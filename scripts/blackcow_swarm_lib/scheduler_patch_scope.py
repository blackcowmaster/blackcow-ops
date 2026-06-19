from __future__ import annotations

import json
from pathlib import Path

from .scheduler_types import ScheduledTask
from .worktree import PatchCandidate


def patch_scope_violation(candidate: PatchCandidate) -> bool:
    return candidate.status != "READY" or bool(candidate.out_of_scope_files)


def write_patch_scope_violation_report(run_dir: Path, task: ScheduledTask, candidate: PatchCandidate) -> None:
    report_path = run_dir / "reports" / f"writer-patch-scope-violation-{task.replica_id}.json"
    payload = {
        "task_id": task.task_id,
        "replica_id": task.replica_id,
        "patch_status": candidate.status,
        "patch_path": str(candidate.patch_path),
        "declared_writes": list(task.writes),
        "changed_files": list(candidate.changed_files),
        "out_of_scope_files": list(candidate.out_of_scope_files),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
