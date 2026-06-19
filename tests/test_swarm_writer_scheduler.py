from __future__ import annotations

import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.runner import MockBehavior, MockRunner, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.scheduler import ScheduledTask, Scheduler


class WorkspaceWritingRunner:
    def __init__(self, expected_entries: int) -> None:
        self.expected_entries = expected_entries
        self.observed_workspaces: dict[str, Path] = {}
        self.delegate = MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.05))
        self.entry_lock = threading.Lock()
        self.all_entered = threading.Event()
        self.entered = 0
        self.timed_out = False

    def run(self, task: WorkerTask) -> RunnerOutcome:
        self.observed_workspaces[task.replica_id] = task.workspace
        target = task.workspace / "src" / task.replica_id / "writer.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{task.replica_id}\n", encoding="utf-8")
        with self.entry_lock:
            self.entered += 1
            if self.entered == self.expected_entries:
                self.all_entered.set()
        if not self.all_entered.wait(2.0):
            self.timed_out = True
        return self.delegate.run(task)


class StatusByReplicaRunner:
    def __init__(self, statuses: dict[str, str]) -> None:
        self.statuses = statuses

    def run(self, task: WorkerTask) -> RunnerOutcome:
        status = self.statuses.get(task.replica_id, "SUCCEEDED")
        return MockRunner(MockBehavior(status=status, delay_seconds=0.01)).run(task)


class TestWriterScheduler(unittest.TestCase):
    def make_task(
        self,
        task_id: str,
        *,
        read_only: bool = True,
        depends_on: tuple[str, ...] = (),
        writes: tuple[str, ...] = (),
    ) -> ScheduledTask:
        return ScheduledTask(
            task_id=task_id,
            replica_id=task_id,
            kind="qa" if read_only else "writer",
            skill="blackcow-qa",
            prompt="Run task",
            depends_on=depends_on,
            read_only=read_only,
            writes=writes,
            acceptance_checks=("python3 -c 'print(\"ok\")'",),
            timeout_seconds=5,
        )

    def test_generated_broad_writer_replicas_overlap_in_isolated_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-broad-writers"
            tasks = [
                self.make_task("coder-1-r1", read_only=False, writes=("**/*",)),
                self.make_task("coder-1-r2", read_only=False, writes=("**/*",)),
            ]
            runner = WorkspaceWritingRunner(expected_entries=2)

            report = Scheduler(max_workers=2).run(tasks, runner, repo_root, run_dir)

            first = report.intervals["coder-1-r1"]
            second = report.intervals["coder-1-r2"]
            self.assertFalse(runner.timed_out)
            self.assertTrue(first.started_at < second.finished_at and second.started_at < first.finished_at)
            self.assertEqual(
                runner.observed_workspaces["coder-1-r1"],
                repo_root / ".worktrees" / "swarm" / "run-broad-writers" / "coder-1-r1",
            )
            self.assertEqual(
                runner.observed_workspaces["coder-1-r2"],
                repo_root / ".worktrees" / "swarm" / "run-broad-writers" / "coder-1-r2",
            )

    def test_dependency_on_writer_race_group_runs_after_any_replica_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-race-dependency"
            tasks = [
                self.make_task("coder-1-r1", read_only=False, writes=("**/*",)),
                self.make_task("coder-1-r2", read_only=False, writes=("**/*",)),
                self.make_task("review-1-r1", depends_on=("coder-1-r1", "coder-1-r2")),
            ]
            runner = StatusByReplicaRunner({"coder-1-r1": "FAILED_RETRYABLE", "coder-1-r2": "SUCCEEDED"})

            report = Scheduler(max_workers=2).run(tasks, runner, repo_root, run_dir)

            events = [(event.event, event.task_id) for event in report.events]
            self.assertEqual(report.states["coder-1-r1"], "FAILED_RETRYABLE")
            self.assertEqual(report.states["coder-1-r2"], "SUCCEEDED")
            self.assertEqual(report.states["review-1-r1"], "SUCCEEDED")
            self.assertLess(events.index(("SUCCEEDED", "coder-1-r2")), events.index(("READY", "review-1-r1")))

    def test_dependency_on_all_failed_race_group_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-race-blocked"
            tasks = [
                self.make_task("coder-1-r1", read_only=False, writes=("**/*",)),
                self.make_task("coder-1-r2", read_only=False, writes=("**/*",)),
                self.make_task("review-1-r1", depends_on=("coder-1-r1", "coder-1-r2")),
            ]
            runner = StatusByReplicaRunner({"coder-1-r1": "FAILED_RETRYABLE", "coder-1-r2": "FAILED_FINAL"})

            report = Scheduler(max_workers=2).run(tasks, runner, repo_root, run_dir)

            self.assertEqual(report.states["review-1-r1"], "BLOCKED")
            self.assertIn(("BLOCKED", "review-1-r1"), [(event.event, event.task_id) for event in report.events])

    def test_parent_risky_writer_scopes_are_serialized(self) -> None:
        for writes in (("pomodoro-app/**",), ("src/**",)):
            with self.subTest(writes=writes), tempfile.TemporaryDirectory() as temp_dir:
                repo_root = Path(temp_dir)
                self.init_git_repo(repo_root)
                run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-parent-risk"
                tasks = [
                    self.make_task("writer-1", read_only=False, writes=writes),
                    self.make_task("writer-2", read_only=False, writes=writes),
                ]

                report = Scheduler(max_workers=2).run(
                    tasks,
                    MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.03)),
                    repo_root,
                    run_dir,
                )

                first = report.intervals["writer-1"]
                second = report.intervals["writer-2"]
                self.assertTrue(first.finished_at <= second.started_at or second.finished_at <= first.started_at)

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
