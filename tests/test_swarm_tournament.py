from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.tournament import PatchCandidate, PatchTournament


class TestTournament(unittest.TestCase):
    def test_clean_patch_beats_non_applying_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            good = self.patch_file(repo, "good.patch", "-base\n+good\n")
            bad = self.patch_file(repo, "bad.patch", "-missing\n+bad\n")

            result = PatchTournament(repo).run(
                "run-1",
                (
                    PatchCandidate("C1-r1", "C1", bad, 99, 1, 1.0),
                    PatchCandidate("C1-r2", "C1", good, 80, 1, 2.0),
                ),
            )

            self.assertEqual(result.winner.replica_id, "C1-r2")
            self.assertEqual((result.integration_worktree / "src" / "app.txt").read_text(encoding="utf-8"), "good\n")
            self.assertEqual((repo / "src" / "app.txt").read_text(encoding="utf-8"), "base\n")
            self.assertIn("C1-r2", result.report_path.read_text(encoding="utf-8"))

    def test_dependent_writer_uses_current_integration_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            good = self.patch_file(repo, "good.patch", "-base\n+good\n")
            tournament = PatchTournament(repo)
            result = tournament.run("run-2", (PatchCandidate("C1-r2", "C1", good, 80, 1, 1.0),))

            dependent = tournament.create_dependent_worktree("run-2", "C2-r1", result.checkpoint_commit)

            self.assertEqual((dependent / "src" / "app.txt").read_text(encoding="utf-8"), "good\n")

    def test_rerun_replaces_existing_integration_worktree_for_repair_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            first = self.patch_file(repo, "first.patch", "-base\n+first\n")
            repair = self.patch_file(repo, "repair.patch", "-base\n+repair\n")
            tournament = PatchTournament(repo)
            tournament.run("run-repair", (PatchCandidate("C1-r1", "C1", first, 80, 1, 1.0),))

            result = tournament.run("run-repair", (PatchCandidate("C1-repair-r1", "C1-repair", repair, 80, 1, 2.0),))

            self.assertEqual(result.winner.replica_id, "C1-repair-r1")
            self.assertEqual((result.integration_worktree / "src" / "app.txt").read_text(encoding="utf-8"), "repair\n")

    def init_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        (repo / ".gitignore").write_text(".worktrees/\n.omo/swarm/runs/\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src" / "app.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        return repo

    def patch_file(self, repo: Path, name: str, hunk: str) -> Path:
        patch = repo / name
        patch.write_text(
            "diff --git a/src/app.txt b/src/app.txt\n"
            "--- a/src/app.txt\n"
            "+++ b/src/app.txt\n"
            "@@ -1 +1 @@\n"
            f"{hunk}",
            encoding="utf-8",
        )
        return patch


if __name__ == "__main__":
    unittest.main()
