from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.blackcow_swarm_lib.runner import MockBehavior, MockRunner, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.scheduler import ScheduledTask, Scheduler
from scripts.blackcow_swarm_lib.worktree import PatchCandidate, WorktreeManager

import scripts.blackcow_swarm_lib.scheduler as scheduler_module


class ConcurrentWorkspaceWritingRunner:
    def __init__(self, expected_entries: int) -> None:
        self.expected_entries = expected_entries
        self.observed_workspaces: dict[str, Path] = {}
        self.delegate = MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.05))
        self.entry_lock = threading.Lock()
        self.all_entered = threading.Event()
        self.entered = 0
        self.timed_out = False

    def run(self, task: WorkerTask) -> RunnerOutcome:
        self.observed_workspaces[task.task_id] = task.workspace
        self.observed_workspaces[task.replica_id] = task.workspace
        target = task.workspace / "src" / task.task_id[-1] / "writer.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{task.task_id}\n", encoding="utf-8")
        with self.entry_lock:
            self.entered += 1
            if self.entered == self.expected_entries:
                self.all_entered.set()
        if not self.all_entered.wait(2.0):
            self.timed_out = True
        return self.delegate.run(task)


class TestSchedulerWriters(unittest.TestCase):
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

    def test_single_writer_lockfile_tasks_not_concurrent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run"
            tasks = [
                self.make_task("writer-1", read_only=False, writes=("pnpm-lock.yaml",)),
                self.make_task("writer-2", read_only=False, writes=("pnpm-lock.yaml",)),
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

    def test_non_conflicting_writer_tasks_overlap_in_isolated_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-parallel-writers"
            tasks = [
                self.make_task("writer-a", read_only=False, writes=("src/a/**",)),
                self.make_task("writer-b", read_only=False, writes=("src/b/**",)),
            ]
            runner = ConcurrentWorkspaceWritingRunner(expected_entries=2)

            report = Scheduler(max_workers=2).run(tasks, runner, repo_root, run_dir)

            first = report.intervals["writer-a"]
            second = report.intervals["writer-b"]
            self.assertFalse(runner.timed_out)
            self.assertTrue(first.started_at < second.finished_at and second.started_at < first.finished_at)
            self.assertEqual(
                runner.observed_workspaces["writer-a"],
                repo_root / ".worktrees" / "swarm" / "run-parallel-writers" / "writer-a-r1",
            )
            self.assertEqual(
                runner.observed_workspaces["writer-b"],
                repo_root / ".worktrees" / "swarm" / "run-parallel-writers" / "writer-b-r1",
            )
            self.assertFalse((repo_root / "src" / "a" / "writer.txt").exists())
            self.assertFalse((repo_root / "src" / "b" / "writer.txt").exists())
            self.assertEqual(report.states["writer-a"], "SUCCEEDED")
            self.assertEqual(report.states["writer-b"], "SUCCEEDED")

    def test_writer_worktree_setup_is_serialized_for_parallel_writers(self) -> None:
        class OverlapDetectingWorktreeManager:
            active_creates = 0
            max_active_creates = 0
            create_lock = threading.Lock()

            def __init__(self, repo_root: Path) -> None:
                self.repo_root = repo_root

            def create_writer_worktree(self, run_id: str, replica_id: str, forbidden_paths: tuple[str, ...] = ()) -> Path:
                with self.create_lock:
                    type(self).active_creates += 1
                    type(self).max_active_creates = max(type(self).max_active_creates, type(self).active_creates)
                time.sleep(0.05)
                with self.create_lock:
                    type(self).active_creates -= 1
                worker_tree = self.repo_root / ".worktrees" / "swarm" / run_id / replica_id
                worker_tree.mkdir(parents=True)
                return worker_tree

            def capture_patch(self, worker_tree: Path, run_id: str, replica_id: str, writes: tuple[str, ...]) -> PatchCandidate:
                patch_path = self.repo_root / ".omo" / "swarm" / "runs" / run_id / "patches" / f"{replica_id}.patch"
                patch_path.parent.mkdir(parents=True, exist_ok=True)
                patch_path.write_text("", encoding="utf-8")
                return PatchCandidate("READY", patch_path, (), ())

            def remove_worktree(self, worker_tree: Path) -> None:
                return None

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-setup-serialized"
            tasks = [
                self.make_task("writer-a", read_only=False, writes=("src/a/**",)),
                self.make_task("writer-b", read_only=False, writes=("src/b/**",)),
            ]

            with patch.object(scheduler_module, "WorktreeManager", OverlapDetectingWorktreeManager):
                report = Scheduler(max_workers=2).run(
                    tasks,
                    MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.02)),
                    repo_root,
                    run_dir,
                )

            self.assertEqual(OverlapDetectingWorktreeManager.max_active_creates, 1)
            self.assertEqual(report.states["writer-a"], "SUCCEEDED")
            self.assertEqual(report.states["writer-b"], "SUCCEEDED")

    def test_writer_setup_failure_becomes_failed_retryable_report(self) -> None:
        class FailingWorktreeManager:
            def __init__(self, repo_root: Path) -> None:
                self.repo_root = repo_root

            def create_writer_worktree(self, run_id: str, replica_id: str, forbidden_paths: tuple[str, ...] = ()) -> Path:
                raise subprocess.CalledProcessError(128, ["git", "worktree"], output=b"out", stderr=b"err")

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-setup-failure"
            task = self.make_task("writer-setup-failure", read_only=False, writes=("src/**",))

            with patch.object(scheduler_module, "WorktreeManager", FailingWorktreeManager):
                report = Scheduler(max_workers=1).run(
                    [task],
                    MockRunner(MockBehavior(status="SUCCEEDED")),
                    repo_root,
                    run_dir,
                )

            self.assertEqual(report.states["writer-setup-failure"], "FAILED_RETRYABLE")
            reports = tuple((run_dir / "reports").glob("writer-setup-failure-*.json"))
            self.assertEqual(len(reports), 1)
            payload = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["phase"], "setup")
            self.assertEqual(payload["status"], "FAILED_RETRYABLE")
            self.assertEqual(payload["replica_id"], "writer-setup-failure-r1")
            self.assertEqual(payload["returncode"], 128)
            self.assertEqual(payload["cmd"], ["git", "worktree"])
            self.assertEqual(payload["stdout"], "out")
            self.assertEqual(payload["stderr"], "err")

    def test_writer_tasks_use_isolated_worktree_workspace(self) -> None:
        class RecordingWriterRunner:
            def __init__(self) -> None:
                self.observed_workspace: Path | None = None
                self.delegate = MockRunner(MockBehavior(status="SUCCEEDED"))

            def run(self, task: WorkerTask) -> RunnerOutcome:
                self.observed_workspace = task.workspace
                (task.workspace / "src").mkdir(parents=True, exist_ok=True)
                (task.workspace / "src" / "writer.txt").write_text("from writer\n", encoding="utf-8")
                return self.delegate.run(task)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            (repo_root / "src").mkdir(exist_ok=True)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-writer-iso"
            runner = RecordingWriterRunner()
            manager = WorktreeManager(repo_root)
            worker_tree = repo_root / ".worktrees" / "swarm" / "run-writer-iso" / "writer-iso-r1"

            try:
                report = Scheduler(max_workers=1).run(
                    [self.make_task("writer-iso", read_only=False, writes=("src/**",))],
                    runner,
                    repo_root,
                    run_dir,
                )

                self.assertEqual(runner.observed_workspace, worker_tree)
                self.assertFalse((repo_root / "src" / "writer.txt").exists())
                patch_path = run_dir / "patches" / "writer-iso-r1.patch"
                patch_text = patch_path.read_text(encoding="utf-8")
                self.assertTrue(patch_path.exists())
                self.assertIn("src/writer.txt", patch_text)
                self.assertNotIn("prompt.md", patch_text)
                self.assertNotIn("result.json", patch_text)
                self.assertNotIn("stdout.log", patch_text)
                self.assertNotIn("stderr.log", patch_text)
                self.assertTrue((run_dir / "workers" / "writer-iso-r1" / "result.json").exists())
                self.assertEqual(report.states["writer-iso"], "SUCCEEDED")
            finally:
                if worker_tree.exists():
                    manager.remove_worktree(worker_tree)

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
