from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

from .acceptance_runner import AcceptanceResult, acceptance_passed, run_acceptance_checks
from .config import JsonValue
from .judge import FinalJudge, SelectedPatch
from .scheduler_rules import task_group_id, worker_status as compute_worker_status
from .scheduler_types import ScheduledTask, ScheduleReport
from .state import RunStore
from .tournament import PatchCandidate, PatchTournament
from .worktree import WorktreeError


@dataclass(frozen=True, slots=True)
class RepairSchedule:
    tasks: list[ScheduledTask]
    report: ScheduleReport


class AcceptanceRepair(Protocol):
    def __call__(self, *, attempt: int, acceptance_results: tuple[AcceptanceResult, ...]) -> RepairSchedule | None: ...


MAX_ACCEPTANCE_REPAIR_ATTEMPTS: Final = 2


def complete_run(
    *,
    checks: tuple[str, ...],
    safe_run_id: str,
    run_dir: Path,
    store: RunStore,
    tasks: list[ScheduledTask],
    report: ScheduleReport,
    project_root: Path,
    summary_prefix: str,
    acceptance_repair: AcceptanceRepair | None = None,
) -> dict[str, JsonValue]:
    worker_status = compute_worker_status(report.states)
    has_writers = any(not task.read_only for task in tasks)
    state: dict[str, JsonValue] = {
        "run_id": safe_run_id,
        "status": _active_status(worker_status, has_writers=has_writers),
        "workers": _worker_entries(report),
    }
    store.write_state(state)
    selected_patches: tuple[SelectedPatch, ...] = ()
    acceptance_root = project_root
    tournament_ok = True
    if worker_status == "SUCCEEDED" and has_writers:
        tournament_ok, acceptance_root, selected_patches = _run_tournament(project_root, run_dir, safe_run_id, tasks, report, state)
        store.write_state(state)
    acceptance_results = (
        run_acceptance_checks(checks, project_root=acceptance_root, controller_root=project_root, run_dir=run_dir)
        if worker_status == "SUCCEEDED" and tournament_ok
        else ()
    )
    repair_entries: list[dict[str, JsonValue]] = []
    for attempt in range(1, MAX_ACCEPTANCE_REPAIR_ATTEMPTS + 1):
        if not _acceptance_failed(acceptance_results, checks) or acceptance_repair is None:
            break
        repair_entry: dict[str, JsonValue] = {"attempt": attempt, "worker_status": "RUNNING"}
        repair_entries.append(repair_entry)
        state["status"] = "ACCEPTANCE_REPAIR_RUNNING"
        state["acceptance"] = _acceptance_entries(acceptance_results)
        state["acceptance_repair"] = repair_entries
        store.write_state(state)
        store.append_event(safe_run_id, "acceptance_repair_started", {"attempt": attempt})
        repair = acceptance_repair(attempt=attempt, acceptance_results=acceptance_results)
        if repair is not None:
            _merge_worker_entries(state, repair.report)
            worker_status = compute_worker_status(repair.report.states)
            repair_entry["worker_status"] = worker_status
            state["acceptance_repair"] = repair_entries
            if worker_status == "SUCCEEDED":
                tournament_ok, acceptance_root, selected_patches = _run_tournament(project_root, run_dir, safe_run_id, repair.tasks, repair.report, state)
                store.write_state(state)
                acceptance_results = (
                    run_acceptance_checks(checks, project_root=acceptance_root, controller_root=project_root, run_dir=run_dir)
                    if tournament_ok
                    else ()
                )
            store.append_event(safe_run_id, "acceptance_repair_finished", {"attempt": attempt, "worker_status": worker_status})
            if worker_status != "SUCCEEDED" or not tournament_ok:
                break
            continue
        repair_entry["worker_status"] = "SKIPPED"
        state["acceptance_repair"] = repair_entries
        break
    status = "SUCCEEDED" if worker_status == "SUCCEEDED" and tournament_ok and acceptance_passed(acceptance_results, checks) else "FAILED"
    state["status"] = status
    state["acceptance"] = _acceptance_entries(acceptance_results)
    store.write_state(state)
    store.append_event(safe_run_id, "run_complete", {"status": status})
    final_judgement = FinalJudge(run_dir).write(
        run_id=safe_run_id,
        status=status,
        summary=_final_summary(summary_prefix, status, run_dir, report),
        selected_patches=selected_patches,
        score_overall=90 if status == "SUCCEEDED" else 0,
    )
    return {"run_id": safe_run_id, "status": status, "state": str(store.state_path), "final_judgement": str(final_judgement)}


def _acceptance_entries(acceptance_results: tuple[AcceptanceResult, ...]) -> list[dict[str, JsonValue]]:
    return [
        {
            "command": result.command,
            "status": "PASSED" if result.ok else "FAILED",
            "exit_code": result.exit_code,
            "stdout": str(result.stdout_path),
            "stderr": str(result.stderr_path),
            "duration_seconds": result.duration_seconds,
        }
        for result in acceptance_results
    ]


def _worker_entries(report: ScheduleReport) -> dict[str, dict[str, JsonValue]]:
    return {
        worker_id: {
            "status": status,
            "started_at": report.intervals[worker_id].started_at,
            "finished_at": report.intervals[worker_id].finished_at,
        }
        for worker_id, status in report.states.items()
    }


def _merge_worker_entries(state: dict[str, JsonValue], report: ScheduleReport) -> None:
    workers = state.get("workers")
    if isinstance(workers, dict):
        workers.update(_worker_entries(report))


def _acceptance_failed(results: tuple[AcceptanceResult, ...], checks: tuple[str, ...]) -> bool:
    return bool(results) and not acceptance_passed(results, checks)


def _active_status(worker_status: str, *, has_writers: bool) -> str:
    if worker_status != "SUCCEEDED":
        return worker_status
    return "TOURNAMENT_RUNNING" if has_writers else "ACCEPTANCE_RUNNING"


def _final_summary(summary_prefix: str, status: str, run_dir: Path, report: ScheduleReport) -> str:
    base = f"{summary_prefix} {status}"
    if status == "SUCCEEDED":
        return base
    detail = _first_worker_stderr(run_dir, report)
    return f"{base}: {detail}" if detail else base


def _first_worker_stderr(run_dir: Path, report: ScheduleReport) -> str:
    for worker_id, status in report.states.items():
        if status == "SUCCEEDED":
            continue
        stderr_path = run_dir / "workers" / worker_id / "stderr.log"
        if not stderr_path.exists():
            continue
        line = _first_non_empty_line(stderr_path)
        if line:
            return line[:240]
    return ""


def _first_non_empty_line(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _run_tournament(
    project_root: Path,
    run_dir: Path,
    safe_run_id: str,
    tasks: list[ScheduledTask],
    report: ScheduleReport,
    state: dict[str, JsonValue],
) -> tuple[bool, Path, tuple[SelectedPatch, ...]]:
    candidates = _successful_patch_candidates(run_dir, tasks, report)
    if not candidates:
        state["tournament"] = {"status": "FAILED", "reason": "no successful writer patch candidates"}
        return False, project_root, ()
    try:
        result = PatchTournament(project_root).run(safe_run_id, candidates)
    except (WorktreeError, subprocess.CalledProcessError) as exc:
        state["tournament"] = {"status": "FAILED", "reason": str(exc)}
        return False, project_root, ()
    state["tournament"] = {
        "status": "SUCCEEDED",
        "report": str(result.report_path),
        "integration_worktree": str(result.integration_worktree),
        "checkpoint_commit": result.checkpoint_commit,
        "selected_task_id": result.winner.task_id,
        "selected_replica_id": result.winner.replica_id,
        "selected_patch": str(result.winner.patch_path),
    }
    return True, result.integration_worktree, (_selected_patch(result.winner),)


def _successful_patch_candidates(run_dir: Path, tasks: list[ScheduledTask], report: ScheduleReport) -> tuple[PatchCandidate, ...]:
    candidates: list[PatchCandidate] = []
    for task in tasks:
        if task.read_only or report.states.get(task.replica_id) != "SUCCEEDED":
            continue
        patch_path = run_dir / "patches" / f"{task.replica_id}.patch"
        if not patch_path.exists():
            continue
        candidates.append(
            PatchCandidate(
                replica_id=task.replica_id,
                task_id=task_group_id(task.replica_id),
                patch_path=patch_path,
                score_overall=90,
                changed_lines=_changed_line_count(patch_path),
                completed_at=report.intervals[task.replica_id].finished_at,
            )
        )
    return tuple(candidates)


def _changed_line_count(patch_path: Path) -> int:
    count = 0
    for line in patch_path.read_bytes().splitlines():
        if (line.startswith(b"+") and not line.startswith(b"+++")) or (line.startswith(b"-") and not line.startswith(b"---")):
            count += 1
    return count


def _selected_patch(candidate: PatchCandidate) -> SelectedPatch:
    return SelectedPatch(candidate.task_id, candidate.replica_id, str(candidate.patch_path))
