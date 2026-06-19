from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.runner import MockBehavior, MockRunner, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.scheduler import ScheduledTask, Scheduler


class DirtyReadOnlyRunner:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.delegate = MockRunner(MockBehavior(status="SUCCEEDED"))

    def run(self, task: WorkerTask) -> RunnerOutcome:
        (self.repo_root / "product.txt").write_text("dirty\n", encoding="utf-8")
        return self.delegate.run(task)


class ForbiddenSourceReferencingRunner:
    def run(self, task: WorkerTask) -> RunnerOutcome:
        started_at = time.time()
        task.result_json.parent.mkdir(parents=True, exist_ok=True)
        task.result_json.write_text(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "replica_id": task.replica_id,
                    "status": "SUCCEEDED",
                    "summary": "Surveyed water-check-app as a reference implementation.",
                    "artifacts": ["water-check-app/"],
                    "changed_files": [],
                    "patch_path": None,
                    "score": {"overall": 80, "correctness": 80, "safety": 80, "tests": 80},
                }
            ),
            encoding="utf-8",
        )
        return RunnerOutcome(
            status="SUCCEEDED",
            result_path=task.result_json,
            command=("forbidden-source-runner",),
            started_at=started_at,
            finished_at=time.time(),
            process=None,
            events=("result_written",),
        )


class TestScheduler(unittest.TestCase):
    def make_task(
        self,
        task_id: str,
        *,
        replica_id: str | None = None,
        read_only: bool = True,
        depends_on: tuple[str, ...] = (),
        writes: tuple[str, ...] = (),
    ) -> ScheduledTask:
        return ScheduledTask(
            task_id=task_id,
            replica_id=replica_id if replica_id is not None else f"{task_id}-r1",
            kind="qa" if read_only else "writer",
            skill="blackcow-qa",
            prompt="Run task",
            depends_on=depends_on,
            read_only=read_only,
            writes=writes,
            acceptance_checks=("python3 -c 'print(\"ok\")'",),
            timeout_seconds=5,
        )

    def test_read_only_tasks_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            tasks = [self.make_task(f"qa-{index}") for index in range(3)]
            scheduler = Scheduler(max_workers=3)
            started = time.time()

            report = scheduler.run(tasks, MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.05)), Path(temp_dir), run_dir)

            elapsed = time.time() - started
            intervals = [report.intervals[task.task_id] for task in tasks]
            self.assertLess(elapsed, 0.14)
            self.assertTrue(any(a.started_at < b.finished_at and b.started_at < a.finished_at for a in intervals for b in intervals if a.task_id != b.task_id))

    def test_read_only_dirty_repo_is_protocol_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / "run"

            report = Scheduler(max_workers=1).run(
                [self.make_task("qa-dirty")],
                DirtyReadOnlyRunner(repo_root),
                repo_root,
                run_dir,
            )

            self.assertEqual(report.states["qa-dirty"], "PROTOCOL_VIOLATION")
            self.assertTrue((run_dir / "reports" / "read-only-violation-qa-dirty.diff").exists())

    def test_forbidden_prior_app_reference_is_protocol_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / "run-forbidden-source"
            task = self.make_task("discovery-prior-app")
            task = ScheduledTask(
                task_id=task.task_id,
                replica_id=task.replica_id,
                kind=task.kind,
                skill=task.skill,
                prompt="Create fresh app. Do not use prior water-check-app or pomodoro-app artifacts.",
                depends_on=task.depends_on,
                read_only=task.read_only,
                writes=task.writes,
                acceptance_checks=task.acceptance_checks,
                timeout_seconds=task.timeout_seconds,
            )

            report = Scheduler(max_workers=1).run([task], ForbiddenSourceReferencingRunner(), repo_root, run_dir)

            self.assertEqual(report.states["discovery-prior-app"], "PROTOCOL_VIOLATION")
            self.assertTrue((run_dir / "reports" / "forbidden-source-discovery-prior-app.json").exists())

    def test_read_only_allows_preexisting_dirty_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            (repo_root / "product.txt").write_text("already dirty\n", encoding="utf-8")
            run_dir = repo_root / "run"

            report = Scheduler(max_workers=1).run(
                [self.make_task("qa-clean")],
                MockRunner(MockBehavior(status="SUCCEEDED")),
                repo_root,
                run_dir,
            )

            self.assertEqual(report.states["qa-clean"], "SUCCEEDED")
            self.assertFalse((run_dir / "reports" / "read-only-violation-qa-clean.diff").exists())

    def test_dependency_waits_for_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            tasks = [
                self.make_task("discovery-1"),
                self.make_task("qa-1", depends_on=("discovery-1",)),
            ]

            report = Scheduler(max_workers=2).run(tasks, MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.01)), Path(temp_dir), run_dir)
            events = [(event.event, event.task_id) for event in report.events]

            self.assertLess(events.index(("SUCCEEDED", "discovery-1")), events.index(("READY", "qa-1")))

    def init_git_repo(self, repo_root: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
        (repo_root / ".gitignore").write_text(".worktrees/\n.omo/swarm/runs/\n", encoding="utf-8")
        (repo_root / "product.txt").write_text("clean\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore", "product.txt"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )


if __name__ == "__main__":
    unittest.main()
