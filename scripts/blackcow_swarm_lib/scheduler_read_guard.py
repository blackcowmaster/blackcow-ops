from __future__ import annotations

import subprocess
from pathlib import Path


def git_status(repo_root: Path, run_dir: Path) -> dict[str, str]:
    if not (repo_root / ".git").exists():
        return {}
    result = subprocess.run(["git", "-C", str(repo_root), "status", "--porcelain"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return {}
    ignored_prefix = _relative_prefix(repo_root, run_dir)
    entries: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if _is_ignored_status_line(line, ignored_prefix):
            continue
        entries[line[3:]] = line[:2]
    return entries


def write_dirty_diff(repo_root: Path, run_dir: Path, task_id: str, before: dict[str, str], after: dict[str, str]) -> None:
    reports = run_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    changed_paths = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    tracked_paths = [path for path in changed_paths if not after.get(path, "").startswith("??")]
    diff_text = ""
    if tracked_paths:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--binary", "--", *tracked_paths],
            text=True,
            capture_output=True,
            check=False,
        )
        diff_text = result.stdout if result.returncode == 0 else ""
    status_lines = ["# Read-only worker modified repository state", "", "## Changed status entries"]
    for path in changed_paths:
        status_lines.append(f"- {path}: {before.get(path, '<clean>')} -> {after.get(path, '<clean>')}")
    status_lines.extend(["", "## Diff", diff_text])
    (reports / f"read-only-violation-{task_id}.diff").write_text("\n".join(status_lines), encoding="utf-8")


def write_writer_root_diff(repo_root: Path, run_dir: Path, task_id: str, before: dict[str, str], after: dict[str, str]) -> None:
    reports = run_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    changed_paths = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    status_lines = ["# Writer modified repository root outside its worktree", "", "## Changed status entries"]
    for path in changed_paths:
        status_lines.append(f"- {path}: {before.get(path, '<clean>')} -> {after.get(path, '<clean>')}")
    (reports / f"writer-root-violation-{task_id}.diff").write_text("\n".join(status_lines), encoding="utf-8")


def _relative_prefix(repo_root: Path, run_dir: Path) -> str:
    try:
        return str(run_dir.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return ""


def _is_ignored_status_line(line: str, ignored_prefix: str) -> bool:
    if not ignored_prefix:
        return False
    path = line[3:]
    return path == ignored_prefix or path.startswith(ignored_prefix + "/")
