from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}")
EXCLUDED_PATCH_ARTIFACT_NAMES = frozenset(("node_modules", ".expo", ".next", ".turbo", "dist", "build", "coverage", ".git"))


@dataclass(frozen=True, slots=True)
class PatchCandidate:
    status: str
    patch_path: Path
    changed_files: tuple[str, ...]
    out_of_scope_files: tuple[str, ...]


class WorktreeError(ValueError):
    pass


class WorktreeManager:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def create_writer_worktree(self, run_id: str, replica_id: str, forbidden_paths: tuple[str, ...] = ()) -> Path:
        safe_run_id = _safe_id(run_id, "run_id")
        safe_replica_id = _safe_id(replica_id, "replica_id")
        worker_tree = self.repo_root / ".worktrees" / "swarm" / safe_run_id / safe_replica_id
        worker_tree.parent.mkdir(parents=True, exist_ok=True)
        branch = f"swarm-{safe_run_id}-{safe_replica_id}"
        _remove_existing_worktree(self.repo_root, worker_tree)
        _git(self.repo_root, ("worktree", "add", "-B", branch, str(worker_tree), "HEAD"))
        self._quarantine_forbidden_paths(worker_tree, forbidden_paths)
        self._materialize_dirty_baseline(worker_tree, safe_run_id, safe_replica_id, forbidden_paths)
        return worker_tree

    def capture_patch(self, worker_tree: Path, run_id: str, replica_id: str, writes: tuple[str, ...]) -> PatchCandidate:
        safe_run_id = _safe_id(run_id, "run_id")
        safe_replica_id = _safe_id(replica_id, "replica_id")
        patch_path = self.repo_root / ".omo" / "swarm" / "runs" / safe_run_id / "patches" / f"{safe_replica_id}.patch"
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        _git(worker_tree, ("add", "-A"))
        _force_add_ignored_source_files(worker_tree, writes)
        changed_files = _changed_files(worker_tree)
        patch_path.write_bytes(_git_bytes(worker_tree, ("diff", "--cached", "--binary")))
        out_of_scope = tuple(path for path in changed_files if not _matches_scope(path, writes))
        status = "READY" if not out_of_scope else "NEEDS_REVIEW"
        return PatchCandidate(
            status=status,
            patch_path=patch_path,
            changed_files=changed_files,
            out_of_scope_files=out_of_scope,
        )

    def remove_worktree(self, worker_tree: Path) -> None:
        _git(self.repo_root, ("worktree", "remove", "--force", str(worker_tree)))

    def _materialize_dirty_baseline(
        self,
        worker_tree: Path,
        run_id: str,
        replica_id: str,
        forbidden_paths: tuple[str, ...],
    ) -> None:
        pathspec = _dirty_baseline_pathspec(forbidden_paths)
        tracked_patch = _git_bytes(self.repo_root, ("diff", "--binary", "HEAD", *pathspec))
        tracked_files = _git_names(self.repo_root, ("diff", "--name-only", "HEAD", "-z", *pathspec))
        untracked_files = tuple(
            relative_path
            for relative_path in _git_names(self.repo_root, ("ls-files", "--others", "--exclude-standard", "-z"))
            if not _is_forbidden_path(relative_path, forbidden_paths)
        )
        if tracked_patch:
            _git_input(worker_tree, ("apply", "--binary"), tracked_patch)
        for relative_path in untracked_files:
            if relative_path.startswith(".worktrees/"):
                continue
            source = self.repo_root / relative_path
            if source.is_dir():
                continue
            destination = worker_tree / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                if destination.exists() or destination.is_symlink():
                    destination.unlink()
                os.symlink(os.readlink(source), destination)
            else:
                shutil.copy2(source, destination)
        _git(worker_tree, ("add", "-A"))
        baseline_commit = None
        if _has_staged_changes(worker_tree):
            _git(
                worker_tree,
                (
                    "-c",
                    "user.name=BlackCow Swarm",
                    "-c",
                    "user.email=blackcow-swarm@example.invalid",
                    "commit",
                    "-m",
                    f"swarm dirty baseline {replica_id}",
                ),
            )
            baseline_commit = _git_text(worker_tree, ("rev-parse", "HEAD")).strip()
        if tracked_files or untracked_files:
            self._write_baseline_report(run_id, replica_id, tracked_files, untracked_files, baseline_commit)

    def _write_baseline_report(
        self,
        run_id: str,
        replica_id: str,
        tracked_files: tuple[str, ...],
        untracked_files: tuple[str, ...],
        baseline_commit: str | None,
    ) -> None:
        report_path = self.repo_root / ".omo" / "swarm" / "runs" / run_id / "reports" / f"writer-baseline-{replica_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "baseline_commit": baseline_commit,
            "replica_id": replica_id,
            "run_id": run_id,
            "tracked_files": list(tracked_files),
            "untracked_files": list(untracked_files),
        }
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _quarantine_forbidden_paths(self, worker_tree: Path, forbidden_paths: tuple[str, ...]) -> None:
        for relative_path in forbidden_paths:
            target = worker_tree / relative_path
            if not target.exists() and not target.is_symlink():
                continue
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        if forbidden_paths:
            _git(worker_tree, ("add", "-A"))
            if _has_staged_changes(worker_tree):
                _git(
                    worker_tree,
                    (
                        "-c",
                        "user.name=BlackCow Swarm",
                        "-c",
                        "user.email=blackcow-swarm@example.invalid",
                        "commit",
                        "-m",
                        "swarm quarantine forbidden sources",
                    ),
                )


def _safe_id(value: str, field: str) -> str:
    if value in (".", "..") or ".." in value or SAFE_ID.fullmatch(value) is None:
        raise WorktreeError(f"invalid {field}: {value}")
    return value


def _changed_files(worker_tree: Path) -> tuple[str, ...]:
    return _git_names(worker_tree, ("diff", "--cached", "--name-only", "-z"))


def _force_add_ignored_source_files(worker_tree: Path, writes: tuple[str, ...]) -> None:
    ignored_files = tuple(
        path
        for path in _git_names(worker_tree, ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"))
        if _matches_scope(path, writes) and not _is_excluded_patch_artifact(path)
    )
    if ignored_files:
        _git(worker_tree, ("add", "-f", "--", *ignored_files))


def _is_excluded_patch_artifact(path: str) -> bool:
    return any(part in EXCLUDED_PATCH_ARTIFACT_NAMES for part in Path(path).parts)


def _matches_scope(path: str, writes: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or path == pattern for pattern in writes)


def _dirty_baseline_pathspec(forbidden_paths: tuple[str, ...]) -> tuple[str, ...]:
    if not forbidden_paths:
        return ()
    excludes = tuple(f":(exclude){path.rstrip('/')}/**" for path in forbidden_paths)
    return ("--", ".", *excludes)


def _is_forbidden_path(path: str, forbidden_paths: tuple[str, ...]) -> bool:
    return any(path == forbidden.rstrip("/") or path.startswith(f"{forbidden.rstrip('/')}/") for forbidden in forbidden_paths)


def _git(repo: Path, args: tuple[str, ...]) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _git_text(repo: Path, args: tuple[str, ...]) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True)
    return result.stdout


def _git_bytes(repo: Path, args: tuple[str, ...]) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return result.stdout


def _git_input(repo: Path, args: tuple[str, ...], payload: bytes) -> None:
    subprocess.run(["git", "-C", str(repo), *args], input=payload, check=True, capture_output=True)


def _git_names(repo: Path, args: tuple[str, ...]) -> tuple[str, ...]:
    output = _git_bytes(repo, args)
    names = [name.decode("utf-8") for name in output.split(b"\x00") if name]
    return tuple(names)


def _has_staged_changes(repo: Path) -> bool:
    result = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True
    raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)


def _remove_existing_worktree(repo: Path, path: Path) -> None:
    if path.exists() and not path.is_dir():
        _git(repo, ("worktree", "prune"))
        return
    if path.exists():
        result = subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(path)], capture_output=True, check=False)
        if result.returncode != 0 and path.exists():
            shutil.rmtree(path)
    _git(repo, ("worktree", "prune"))
