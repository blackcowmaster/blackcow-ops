from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.worktree import WorktreeManager


class TestWorktree(unittest.TestCase):
    def test_writer_patch_created_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            manager = WorktreeManager(repo)

            worker_tree = manager.create_writer_worktree("run-1", "writer-1-r1")
            self.assertEqual(worker_tree, repo / ".worktrees" / "swarm" / "run-1" / "writer-1-r1")
            (worker_tree / "src" / "app.txt").write_text("changed\n", encoding="utf-8")
            (worker_tree / "src" / "new.txt").write_text("new\n", encoding="utf-8")
            (worker_tree / "src" / "obsolete.txt").unlink()
            (worker_tree / "src" / "image.bin").write_bytes(b"\x00\x02binary-change")

            candidate = manager.capture_patch(worker_tree, "run-1", "writer-1-r1", writes=("src/**",))
            patch = candidate.patch_path.read_bytes()

            self.assertEqual(candidate.status, "READY")
            self.assertTrue(candidate.patch_path.exists())
            self.assertIn("src/new.txt", candidate.changed_files)
            self.assertIn("src/obsolete.txt", candidate.changed_files)
            self.assertIn(b"new file mode", patch)
            self.assertIn(b"deleted file mode", patch)
            self.assertIn(b"GIT binary patch", patch)
            self.assertEqual((repo / "src" / "app.txt").read_text(encoding="utf-8"), "clean\n")
            self.assertFalse((repo / "src" / "new.txt").exists())
            self.assertTrue((repo / "src" / "obsolete.txt").exists())

    def test_out_of_scope_patch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            manager = WorktreeManager(repo)

            worker_tree = manager.create_writer_worktree("run-2", "writer-2-r1")
            (worker_tree / "docs").mkdir()
            (worker_tree / "docs" / "out.txt").write_text("out\n", encoding="utf-8")
            candidate = manager.capture_patch(worker_tree, "run-2", "writer-2-r1", writes=("src/**",))

            self.assertEqual(candidate.status, "NEEDS_REVIEW")
            self.assertEqual(candidate.out_of_scope_files, ("docs/out.txt",))

    def test_rejects_path_traversal_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            manager = WorktreeManager(repo)

            with self.assertRaisesRegex(ValueError, "invalid"):
                manager.create_writer_worktree("../bad", "writer-1-r1")
            with self.assertRaisesRegex(ValueError, "invalid"):
                manager.create_writer_worktree("run-1", "../../x")
            with self.assertRaisesRegex(ValueError, "invalid"):
                manager.create_writer_worktree("", "writer-1-r1")

    def test_create_writer_worktree_allows_ignored_dirty_swarm_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            manager = WorktreeManager(repo)

            (repo / ".omo" / "swarm" / "runs" / "stale" / "leftover.txt").parent.mkdir(parents=True, exist_ok=True)
            (repo / ".omo" / "swarm" / "runs" / "stale" / "leftover.txt").write_text("stale run\n", encoding="utf-8")
            (repo / ".worktrees" / "swarm" / "stale" / "leftover.txt").parent.mkdir(parents=True, exist_ok=True)
            (repo / ".worktrees" / "swarm" / "stale" / "leftover.txt").write_text("stale worktree\n", encoding="utf-8")

            status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True, check=True)
            self.assertEqual(status.stdout, "")

            worker_tree = manager.create_writer_worktree("run-ignored", "writer-ignored-r1")
            self.assertEqual(worker_tree, repo / ".worktrees" / "swarm" / "run-ignored" / "writer-ignored-r1")

    def test_create_writer_worktree_replaces_existing_same_run_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            manager = WorktreeManager(repo)
            worker_tree = manager.create_writer_worktree("run-repeat", "writer-repeat-r1")
            (worker_tree / "stale.txt").write_text("stale worker output\n", encoding="utf-8")

            recreated = manager.create_writer_worktree("run-repeat", "writer-repeat-r1")

            self.assertEqual(recreated, worker_tree)
            self.assertFalse((recreated / "stale.txt").exists())
            status = subprocess.run(["git", "status", "--porcelain"], cwd=recreated, text=True, capture_output=True, check=True)
            self.assertEqual(status.stdout, "")

    def test_dirty_root_is_materialized_as_worker_baseline_without_polluting_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            manager = WorktreeManager(repo)

            (repo / "tracked.txt").write_text("dirty tracked\n", encoding="utf-8")
            (repo / "scripts").mkdir()
            (repo / "scripts" / "tool.py").write_text("print('tool')\n", encoding="utf-8")
            (repo / "water-check-app").mkdir()
            (repo / "water-check-app" / "package.json").write_text('{"name":"water-check-app"}\n', encoding="utf-8")

            worker_tree = manager.create_writer_worktree("run-dirty", "writer-dirty-r1")

            self.assertEqual((worker_tree / "tracked.txt").read_text(encoding="utf-8"), "dirty tracked\n")
            self.assertEqual((worker_tree / "scripts" / "tool.py").read_text(encoding="utf-8"), "print('tool')\n")
            self.assertEqual(
                (worker_tree / "water-check-app" / "package.json").read_text(encoding="utf-8"),
                '{"name":"water-check-app"}\n',
            )
            status = subprocess.run(["git", "status", "--porcelain"], cwd=worker_tree, text=True, capture_output=True, check=True)
            self.assertEqual(status.stdout, "")

            (worker_tree / "src" / "new.txt").write_text("new\n", encoding="utf-8")
            candidate = manager.capture_patch(worker_tree, "run-dirty", "writer-dirty-r1", writes=("src/**",))
            patch = candidate.patch_path.read_text(encoding="utf-8")

            self.assertEqual(candidate.status, "READY")
            self.assertEqual(candidate.changed_files, ("src/new.txt",))
            self.assertIn("src/new.txt", patch)
            self.assertNotIn("tracked.txt", patch)
            self.assertNotIn("scripts/tool.py", patch)

    def test_forbidden_prior_artifact_dirs_are_quarantined_from_writer_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            (repo / "water-check-app").mkdir()
            (repo / "water-check-app" / "package.json").write_text('{"name":"water-check-app"}\n', encoding="utf-8")
            (repo / "pomodoro-app").mkdir()
            (repo / "pomodoro-app" / "package.json").write_text('{"name":"pomodoro-app"}\n', encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "apps"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            manager = WorktreeManager(repo)

            worker_tree = manager.create_writer_worktree(
                "run-forbidden",
                "writer-forbidden-r1",
                forbidden_paths=("water-check-app", "pomodoro-app"),
            )

            self.assertFalse((worker_tree / "water-check-app").exists())
            self.assertFalse((worker_tree / "pomodoro-app").exists())
            status = subprocess.run(["git", "status", "--porcelain"], cwd=worker_tree, text=True, capture_output=True, check=True)
            self.assertEqual(status.stdout, "")

            (worker_tree / "swarm-water-check-app").mkdir()
            (worker_tree / "swarm-water-check-app" / "package.json").write_text('{"name":"swarm-water-check-app"}\n', encoding="utf-8")
            candidate = manager.capture_patch(worker_tree, "run-forbidden", "writer-forbidden-r1", writes=("swarm-water-check-app/**",))
            patch = candidate.patch_path.read_text(encoding="utf-8")

            self.assertEqual(candidate.status, "READY")
            self.assertEqual(candidate.changed_files, ("swarm-water-check-app/package.json",))
            self.assertIn("swarm-water-check-app/package.json", patch)
            self.assertNotIn("a/water-check-app/package.json", patch)
            self.assertNotIn("b/water-check-app/package.json", patch)
            self.assertNotIn("a/pomodoro-app/package.json", patch)
            self.assertNotIn("b/pomodoro-app/package.json", patch)

    def test_forbidden_prior_artifact_dirty_baseline_is_not_applied_after_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            (repo / "pomodoro-app").mkdir()
            (repo / "pomodoro-app" / "package.json").write_text('{"name":"pomodoro-app"}\n', encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "pomodoro"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            manager = WorktreeManager(repo)
            (repo / "tracked.txt").write_text("dirty tracked\n", encoding="utf-8")
            (repo / "pomodoro-app" / "package.json").write_text('{"name":"dirty-pomodoro"}\n', encoding="utf-8")
            (repo / "pomodoro-app" / "local.txt").write_text("local prior artifact\n", encoding="utf-8")

            worker_tree = manager.create_writer_worktree(
                "run-forbidden-dirty",
                "writer-forbidden-dirty-r1",
                forbidden_paths=("pomodoro-app",),
            )

            self.assertFalse((worker_tree / "pomodoro-app").exists())
            self.assertEqual((worker_tree / "tracked.txt").read_text(encoding="utf-8"), "dirty tracked\n")
            status = subprocess.run(["git", "status", "--porcelain"], cwd=worker_tree, text=True, capture_output=True, check=True)
            self.assertEqual(status.stdout, "")
            report = (
                repo
                / ".omo"
                / "swarm"
                / "runs"
                / "run-forbidden-dirty"
                / "reports"
                / "writer-baseline-writer-forbidden-dirty-r1.json"
            ).read_text(encoding="utf-8")
            self.assertIn("tracked.txt", report)
            self.assertNotIn("pomodoro-app", report)

    def test_ignored_project_config_files_are_forced_into_writer_patch_without_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.init_repo(Path(temp_dir))
            (repo / ".gitignore").write_text(
                ".worktrees/\n.omo/swarm/runs/\nnode_modules/\npackage.json\ntsconfig.json\n.prettierrc\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "ignore configs"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            manager = WorktreeManager(repo)
            worker_tree = manager.create_writer_worktree("run-ignored-configs", "writer-ignored-configs-r1")
            app = worker_tree / "swarm-water-tabs-check"
            (app / "node_modules").mkdir(parents=True)
            (app / "package.json").write_text('{"name":"swarm-water-tabs-check"}\n', encoding="utf-8")
            (app / "tsconfig.json").write_text('{"compilerOptions":{"strict":true}}\n', encoding="utf-8")
            (app / ".prettierrc").write_text("{}\n", encoding="utf-8")
            (app / "App.tsx").write_text("export default function App() { return null }\n", encoding="utf-8")
            (app / "node_modules" / "dep.js").write_text("module.exports = {}\n", encoding="utf-8")

            candidate = manager.capture_patch(
                worker_tree,
                "run-ignored-configs",
                "writer-ignored-configs-r1",
                writes=("swarm-water-tabs-check/**",),
            )
            patch = candidate.patch_path.read_text(encoding="utf-8")

            self.assertEqual(candidate.status, "READY")
            self.assertIn("swarm-water-tabs-check/package.json", candidate.changed_files)
            self.assertIn("swarm-water-tabs-check/tsconfig.json", candidate.changed_files)
            self.assertIn("swarm-water-tabs-check/.prettierrc", candidate.changed_files)
            self.assertIn("swarm-water-tabs-check/App.tsx", candidate.changed_files)
            self.assertNotIn("swarm-water-tabs-check/node_modules/dep.js", candidate.changed_files)
            self.assertIn("swarm-water-tabs-check/package.json", patch)
            self.assertIn("swarm-water-tabs-check/tsconfig.json", patch)
            self.assertIn("swarm-water-tabs-check/.prettierrc", patch)
            self.assertNotIn("node_modules/dep.js", patch)

    def init_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        (repo / ".gitignore").write_text(".worktrees/\n.omo/swarm/runs/\n", encoding="utf-8")
        (repo / "tracked.txt").write_text("clean tracked\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src" / "app.txt").write_text("clean\n", encoding="utf-8")
        (repo / "src" / "obsolete.txt").write_text("old\n", encoding="utf-8")
        (repo / "src" / "image.bin").write_bytes(b"\x00\x01binary")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        return repo


if __name__ == "__main__":
    unittest.main()
