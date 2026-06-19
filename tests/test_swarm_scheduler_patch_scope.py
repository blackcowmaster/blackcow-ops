from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.runner import MockBehavior, MockRunner, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.scheduler import ScheduledTask, Scheduler


class OutOfScopeWritingRunner:
    def __init__(self) -> None:
        self.delegate = MockRunner(MockBehavior(status="SUCCEEDED"))

    def run(self, task: WorkerTask) -> RunnerOutcome:
        scoped_file = task.workspace / "src" / "allowed.txt"
        scoped_file.parent.mkdir(parents=True, exist_ok=True)
        scoped_file.write_text("inside declared scope\n", encoding="utf-8")
        (task.workspace / "package.json").write_text('{"scripts": {"test": "false"}}\n', encoding="utf-8")
        return self.delegate.run(task)


class TestSchedulerPatchScope(unittest.TestCase):
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

    def test_writer_out_of_scope_patch_fails_and_blocks_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.init_git_repo(repo_root)
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-patch-scope"
            worker_tree = repo_root / ".worktrees" / "swarm" / "run-patch-scope" / "writer-scope-r1"
            tasks = [
                self.make_task("writer-scope", replica_id="writer-scope-r1", read_only=False, writes=("src/**",)),
                self.make_task("review-scope", depends_on=("writer-scope",)),
            ]

            report = Scheduler(max_workers=1).run(tasks, OutOfScopeWritingRunner(), repo_root, run_dir)

            patch_path = run_dir / "patches" / "writer-scope-r1.patch"
            audit_path = run_dir / "reports" / "writer-patch-scope-violation-writer-scope-r1.json"
            patch_text = patch_path.read_text(encoding="utf-8")
            audit_text = audit_path.read_text(encoding="utf-8")
            events = [(event.event, event.task_id) for event in report.events]

            self.assertEqual(report.states["writer-scope"], "FAILED_RETRYABLE")
            self.assertEqual(report.states["review-scope"], "BLOCKED")
            self.assertIn(("PATCH_SCOPE_VIOLATION", "writer-scope"), events)
            self.assertTrue(patch_path.exists())
            self.assertIn("src/allowed.txt", patch_text)
            self.assertIn("package.json", patch_text)
            self.assertIn("writer-scope-r1", audit_text)
            self.assertIn("src/allowed.txt", audit_text)
            self.assertIn("package.json", audit_text)
            self.assertIn("src/**", audit_text)
            self.assertIn(str(patch_path), audit_text)
            self.assertTrue((run_dir / "workers" / "writer-scope-r1" / "result.json").exists())
            self.assertFalse(worker_tree.exists())

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
