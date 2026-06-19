from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.lifecycle import cancel_run, cleanup_run, status_run


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "scripts" / "blackcow_swarm.py"


class TestCancelCleanup(unittest.TestCase):
    def test_cancel_marks_pending_running_and_writes_final_judgement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".omo" / "swarm" / "runs" / "run-cancel"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-cancel",
                        "status": "RUNNING",
                        "workers": {
                            "D1-r1": {"status": "SUCCEEDED"},
                            "C1-r1": {"status": "RUNNING"},
                            "Q1-r1": {"status": "PENDING"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            cancel_run(root, "run-cancel")

            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertTrue((run_dir / "CANCEL_REQUESTED").exists())
            self.assertEqual(state["workers"]["C1-r1"]["status"], "CANCELLED")
            self.assertEqual(state["workers"]["Q1-r1"]["status"], "CANCELLED")
            self.assertTrue((run_dir / "final_judgement.json").exists())
            self.assertIn("cancel_requested", (run_dir / "events.jsonl").read_text(encoding="utf-8"))

    def test_cancel_without_state_writes_cancelled_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".omo" / "swarm" / "runs" / "run-cancel-no-state"
            run_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")

            cancel_run(root, "run-cancel-no-state")

            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "CANCELLED")
            self.assertEqual(state["workers"], {})
            self.assertTrue((run_dir / "CANCEL_REQUESTED").exists())
            self.assertTrue((run_dir / "final_judgement.json").exists())
            self.assertIn("cancel_requested", (run_dir / "events.jsonl").read_text(encoding="utf-8"))

    def test_cleanup_removes_worktrees_and_preserves_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "run-clean"
            run_dir = root / ".omo" / "swarm" / "runs" / run_id
            report_dir = run_dir / "reports"
            worktree_dir = root / ".worktrees" / "swarm" / run_id
            report_dir.mkdir(parents=True)
            worktree_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
            (run_dir / "final_judgement.json").write_text("{}", encoding="utf-8")
            (report_dir / "tournament.md").write_text("# Tournament\n", encoding="utf-8")
            (worktree_dir / "tmp.txt").write_text("tmp\n", encoding="utf-8")

            cleanup_run(root, run_id)

            self.assertFalse(worktree_dir.exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "final_judgement.json").exists())
            self.assertTrue((report_dir / "tournament.md").exists())

    def test_cleanup_purges_writer_worktrees_and_patches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "run-clean"
            run_dir = root / ".omo" / "swarm" / "runs" / run_id
            patch_dir = run_dir / "patches"
            patch = patch_dir / "writer-1-r1.patch"
            worktree_dir = root / ".worktrees" / "swarm" / run_id / "writer-1-r1"

            patch_dir.mkdir(parents=True)
            worktree_dir.mkdir(parents=True)
            (worktree_dir / "file.txt").write_text("tmp\n", encoding="utf-8")
            patch.write_text("diff --git a/file b/file\n", encoding="utf-8")
            (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
            (run_dir / "final_judgement.json").write_text("{}", encoding="utf-8")
            (run_dir / "reports").mkdir(parents=True)
            (run_dir / "reports" / "tournament.md").write_text("# Tournament\n", encoding="utf-8")

            cleanup_run(root, run_id)

            self.assertFalse((root / ".worktrees" / "swarm" / run_id).exists())
            self.assertFalse((run_dir / "patches").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "final_judgement.json").exists())
            self.assertTrue((run_dir / "reports" / "tournament.md").exists())

    def test_cleanup_unregisters_git_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "run-clean-git-worktree"
            run_dir = root / ".omo" / "swarm" / "runs" / run_id
            worktree_dir = root / ".worktrees" / "swarm" / run_id / "integration"
            run_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
            (run_dir / "final_judgement.json").write_text("{}", encoding="utf-8")
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            (root / "app.txt").write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.txt"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "worktree", "add", "-B", f"swarm-{run_id}-integration", str(worktree_dir), "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
            )

            cleanup_run(root, run_id)

            worktrees = subprocess.run(["git", "worktree", "list"], cwd=root, text=True, capture_output=True, check=True)
            branches = subprocess.run(["git", "branch", "--list", f"swarm-{run_id}-*"], cwd=root, text=True, capture_output=True, check=True)
            self.assertNotIn(str(worktree_dir), worktrees.stdout)
            self.assertEqual(branches.stdout, "")
            self.assertFalse((root / ".worktrees" / "swarm" / run_id).exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "final_judgement.json").exists())

    def test_cleanup_does_not_delete_sibling_run_prefix_branches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "run-clean"
            sibling_id = "run-clean-extra"
            run_dir = root / ".omo" / "swarm" / "runs" / run_id
            run_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").write_text("{}\n", encoding="utf-8")
            (run_dir / "final_judgement.json").write_text("{}", encoding="utf-8")
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            (root / "app.txt").write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.txt"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            own_worktree = root / ".worktrees" / "swarm" / run_id / "integration"
            sibling_worktree = root / ".worktrees" / "swarm" / sibling_id / "integration"
            subprocess.run(
                ["git", "worktree", "add", "-B", f"swarm-{run_id}-integration", str(own_worktree), "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "worktree", "add", "-B", f"swarm-{sibling_id}-integration", str(sibling_worktree), "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
            )

            cleanup_run(root, run_id)

            branches = subprocess.run(["git", "branch", "--list", "swarm-run-clean*"], cwd=root, text=True, capture_output=True, check=True)
            worktrees = subprocess.run(["git", "worktree", "list"], cwd=root, text=True, capture_output=True, check=True)
            self.assertNotIn(f"swarm-{run_id}-integration", branches.stdout)
            self.assertIn(f"swarm-{sibling_id}-integration", branches.stdout)
            self.assertNotIn(str(own_worktree), worktrees.stdout)
            self.assertIn(str(sibling_worktree), worktrees.stdout)

    def test_status_summary_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".omo" / "swarm" / "runs" / "run-status"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text(json.dumps({"run_id": "run-status", "status": "DRY_RUN", "workers": {}}), encoding="utf-8")

            self.assertEqual(status_run(root, "run-status")["status"], "DRY_RUN")

    def test_cli_mock_run_status_cancel_cleanup(self) -> None:
        run_id = "swarm-unit-live"
        shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)
        try:
            run = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "run",
                    "--task-graph",
                    "tests/fixtures/task_graph.simple.json",
                    "--runner",
                    "mock",
                    "--run-id",
                    run_id,
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            status = subprocess.run(
                [sys.executable, str(CLI_PATH), "status", "--run-id", run_id],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(json.loads(status.stdout)["status"], "SUCCEEDED")
        finally:
            shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
