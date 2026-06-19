from __future__ import annotations

import subprocess
from pathlib import Path


def registered_branches_outside_run(project_root: Path, run_worktree_dir: Path) -> frozenset[str]:
    result = subprocess.run(["git", "-C", str(project_root), "worktree", "list", "--porcelain"], text=True, capture_output=True, check=True)
    protected: set[str] = set()
    current_path: Path | None = None
    run_root = run_worktree_dir.resolve()
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree "))
            continue
        if current_path is None or not line.startswith("branch refs/heads/"):
            continue
        branch = line.removeprefix("branch refs/heads/")
        try:
            current_path.resolve().relative_to(run_root)
        except ValueError:
            protected.add(branch)
    return frozenset(protected)


def branch_name_from_list_line(line: str) -> str:
    branch = line.strip()
    if branch.startswith("* ") or branch.startswith("+ "):
        return branch[2:].strip()
    return branch
