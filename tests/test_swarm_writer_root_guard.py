from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.runner import MockBehavior, MockRunner, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.scheduler import ScheduledTask, Scheduler


class RootLeakingWriterRunner:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.delegate = MockRunner(MockBehavior(status="SUCCEEDED"))

    def run(self, task: WorkerTask) -> RunnerOutcome:
        leaked_target = self.repo_root / "swarm-water-check-app" / "package.json"
        leaked_target.parent.mkdir(parents=True, exist_ok=True)
        leaked_target.write_text('{"scripts":{}}\n', encoding="utf-8")
        return self.delegate.run(task)


class TestWriterRootGuard(unittest.TestCase):
    def test_writer_root_mutation_is_protocol_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
            (repo_root / "tracked.txt").write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )
            run_dir = repo_root / ".omo" / "swarm" / "runs" / "run-root-leak"
            task = ScheduledTask(
                task_id="coder-1",
                replica_id="coder-1-r1",
                kind="coder",
                skill="blackcow-loop",
                prompt="Create app",
                depends_on=(),
                read_only=False,
                writes=("**/*",),
                acceptance_checks=("python3 -c 'print(\"ok\")'",),
                timeout_seconds=5,
            )

            report = Scheduler(max_workers=1).run([task], RootLeakingWriterRunner(repo_root), repo_root, run_dir)

            self.assertEqual(report.states["coder-1"], "PROTOCOL_VIOLATION")
            self.assertTrue((run_dir / "reports" / "writer-root-violation-coder-1.diff").exists())


if __name__ == "__main__":
    unittest.main()
