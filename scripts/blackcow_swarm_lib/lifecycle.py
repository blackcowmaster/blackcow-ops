from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue, load_config
from .judge import FinalJudge
from .lifecycle_cleanup import branch_name_from_list_line, registered_branches_outside_run
from .lifecycle_completion import complete_run
from .lifecycle_graph import acceptance_checks, materialize_run_scoped_text, scheduled_tasks
from .reasonix_health import ReasonixHealthResult, run_reasonix_health_check
from .runner import MockBehavior, MockRunner, ReasonixRunner
from .retrying_runner import RetryingRunner
from .scheduler import Scheduler
from .schema import validate_task_graph
from .state import RunStore
from .task_graph import RUN_ID_PATTERN


@dataclass(frozen=True, slots=True)
class ResumeActions:
    skip_workers: tuple[str, ...]
    retry_workers: tuple[str, ...]


class LifecycleInputError(ValueError):
    pass


class DynamicThrottle:
    def __init__(self, active_workers: int) -> None:
        self.active_workers = max(1, active_workers)
        self.rate_limit_hits = 0

    def observe_worker_output(self, output: str) -> None:
        text = output.lower()
        if "rate limit" in text or "http 429" in text or "timeout" in text:
            self.rate_limit_hits += 1
        if self.rate_limit_hits >= 2:
            self.active_workers = max(1, self.active_workers // 2)
            self.rate_limit_hits = 0


def compute_resume_actions(state: Mapping[str, JsonValue], *, now: float, stale_after_seconds: int) -> ResumeActions:
    workers = _mapping(state["workers"], "workers")
    skip: list[str] = []
    retry: list[str] = []
    for worker_id, value in workers.items():
        worker = _mapping(value, worker_id)
        status = _string(worker.get("status"), f"{worker_id}.status")
        if status == "SUCCEEDED":
            skip.append(worker_id)
        elif status == "RUNNING" and now - _number(worker.get("lease_ts"), f"{worker_id}.lease_ts") > stale_after_seconds:
            retry.append(worker_id)
    return ResumeActions(skip_workers=tuple(skip), retry_workers=tuple(retry))


def should_hard_timeout(*, started_at: float, now: float, hard_timeout_seconds: int) -> bool:
    return now - started_at > hard_timeout_seconds


def cancel_run(project_root: Path, run_id: str) -> Path:
    safe_run_id = _safe_run_id(run_id)
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    store = RunStore(run_dir)
    state = (
        _mapping(json.loads(store.state_path.read_text(encoding="utf-8")), "state")
        if store.state_path.exists()
        else {"run_id": safe_run_id, "status": "CANCELLED", "workers": {}}
    )
    workers = _mapping(state["workers"], "workers")
    for worker in workers.values():
        worker_state = _mapping(worker, "worker")
        status = _string(worker_state.get("status"), "worker.status")
        if status in ("PENDING", "READY", "LEASED", "RUNNING", "PLANNED"):
            worker_state["status"] = "CANCELLED"
    state["status"] = "CANCELLED"
    (run_dir / "CANCEL_REQUESTED").write_text("cancel_requested\n", encoding="utf-8")
    store.write_state(state)
    store.append_event(safe_run_id, "cancel_requested", {"run_id": safe_run_id})
    return FinalJudge(run_dir).write(
        run_id=safe_run_id,
        status="CANCELLED",
        summary="Run cancelled by request",
        selected_patches=(),
        score_overall=0,
    )


def status_run(project_root: Path, run_id: str) -> dict[str, JsonValue]:
    safe_run_id = _safe_run_id(run_id)
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    state = _mapping(json.loads((run_dir / "state.json").read_text(encoding="utf-8")), "state")
    return {"run_id": safe_run_id, "status": state["status"], "workers": state.get("workers", {})}


def cleanup_run(project_root: Path, run_id: str) -> dict[str, JsonValue]:
    safe_run_id = _safe_run_id(run_id)
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    worktree_dir = project_root / ".worktrees" / "swarm" / safe_run_id
    removed: list[str] = []
    _remove_registered_worktrees(project_root, worktree_dir, removed)
    _delete_run_branches(project_root, safe_run_id, removed)
    if worktree_dir.exists():
        shutil.rmtree(worktree_dir)
        removed.append(str(worktree_dir))
    _prune_worktrees(project_root)
    for name in ("workers", "planned-results", "prompts", "patches"):
        path = run_dir / name
        if path.exists():
            shutil.rmtree(path)
            removed.append(str(path))
    return {"run_id": safe_run_id, "removed": removed}


def _remove_registered_worktrees(project_root: Path, worktree_dir: Path, removed: list[str]) -> None:
    if not (project_root / ".git").exists():
        return
    for path in _registered_worktrees_under(project_root, worktree_dir):
        subprocess.run(["git", "-C", str(project_root), "worktree", "remove", "--force", str(path)], check=True, capture_output=True)
        removed.append(str(path))


def _registered_worktrees_under(project_root: Path, worktree_dir: Path) -> tuple[Path, ...]:
    result = subprocess.run(["git", "-C", str(project_root), "worktree", "list", "--porcelain"], text=True, capture_output=True, check=True)
    worktree_root = worktree_dir.resolve()
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if not line.startswith("worktree "):
            continue
        path = Path(line.removeprefix("worktree "))
        try:
            path.resolve().relative_to(worktree_root)
        except ValueError:
            continue
        paths.append(path)
    return tuple(paths)


def _prune_worktrees(project_root: Path) -> None:
    if not (project_root / ".git").exists():
        return
    subprocess.run(["git", "-C", str(project_root), "worktree", "prune"], check=True, capture_output=True)


def _delete_run_branches(project_root: Path, run_id: str, removed: list[str]) -> None:
    if not (project_root / ".git").exists():
        return
    protected = registered_branches_outside_run(project_root, project_root / ".worktrees" / "swarm" / run_id)
    result = subprocess.run(
        ["git", "-C", str(project_root), "branch", "--list", f"swarm-{run_id}-*"],
        text=True,
        capture_output=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        branch = branch_name_from_list_line(line)
        if not branch or branch in protected:
            continue
        subprocess.run(["git", "-C", str(project_root), "branch", "-D", branch], check=True, capture_output=True)
        removed.append(branch)


def execute_mock_run(task_graph_path: Path, run_id: str | None, project_root: Path) -> dict[str, JsonValue]:
    graph_payload: JsonValue = json.loads(task_graph_path.read_text(encoding="utf-8"))
    validate_task_graph(graph_payload)
    graph = _mapping(graph_payload, "task_graph")
    safe_run_id = _safe_run_id(run_id if run_id is not None else _string(graph["run_id"], "task_graph.run_id"))
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    _copy_plan_shared_context(task_graph_path, run_dir, project_root=project_root)
    store = RunStore(run_dir)
    tasks = scheduled_tasks(graph, run_dir=run_dir, project_root=project_root)
    store.append_event(safe_run_id, "run_started", {"runner": "mock", "tasks": len(tasks)})
    report = Scheduler(max_workers=max(1, len(tasks))).run(tasks, MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.01)), project_root, run_dir)
    return complete_run(
        checks=acceptance_checks(graph, run_dir=run_dir, project_root=project_root),
        safe_run_id=safe_run_id,
        run_dir=run_dir,
        store=store,
        tasks=tasks,
        report=report,
        project_root=project_root,
        summary_prefix="Mock run",
    )


def execute_reasonix_run(task_graph_path: Path, run_id: str | None, project_root: Path) -> dict[str, JsonValue]:
    graph_payload: JsonValue = json.loads(task_graph_path.read_text(encoding="utf-8"))
    validate_task_graph(graph_payload)
    graph = _mapping(graph_payload, "task_graph")
    safe_run_id = _safe_run_id(run_id if run_id is not None else _string(graph["run_id"], "task_graph.run_id"))
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    _copy_plan_shared_context(task_graph_path, run_dir, project_root=project_root)
    store = RunStore(run_dir)
    tasks = scheduled_tasks(graph, run_dir=run_dir, project_root=project_root)
    config = load_config()
    intensity = _string(graph["intensity"], "task_graph.intensity")
    store.append_event(safe_run_id, "run_started", {"runner": "reasonix-acp", "tasks": len(tasks)})
    health = run_reasonix_health_check(project_root, run_dir, probe_model=True)
    if not health.ok:
        return _blocked_reasonix_preflight(safe_run_id, run_dir, store, health)
    runner = RetryingRunner(ReasonixRunner.default(), retry_limit=config.intensity[intensity].retry_limit)
    report = Scheduler(max_workers=max(1, min(len(tasks), 4))).run(tasks, runner, project_root, run_dir)
    return complete_run(
        checks=acceptance_checks(graph, run_dir=run_dir, project_root=project_root),
        safe_run_id=safe_run_id,
        run_dir=run_dir,
        store=store,
        tasks=tasks,
        report=report,
        project_root=project_root,
        summary_prefix="Reasonix ACP run",
    )


def _blocked_reasonix_preflight(
    safe_run_id: str,
    run_dir: Path,
    store: RunStore,
    health: ReasonixHealthResult,
) -> dict[str, JsonValue]:
    state: dict[str, JsonValue] = {
        "run_id": safe_run_id,
        "status": "BLOCKED",
        "workers": {},
        "reasonix_health": {
            "ok": health.ok,
            "summary": health.summary,
            "started_at": health.started_at,
            "finished_at": health.finished_at,
            "duration_seconds": health.finished_at - health.started_at,
            "transcript": str(health.transcript_path),
            "stdout": str(health.stdout_path),
            "stderr": str(health.stderr_path),
        },
    }
    store.write_state(state)
    store.append_event(safe_run_id, "reasonix_health_blocked", {"summary": health.summary})
    store.append_event(safe_run_id, "run_complete", {"status": "BLOCKED"})
    final_judgement = FinalJudge(run_dir).write(
        run_id=safe_run_id,
        status="BLOCKED",
        summary=f"Reasonix ACP run BLOCKED: {health.summary}",
        selected_patches=(),
        score_overall=0,
    )
    return {"run_id": safe_run_id, "status": "BLOCKED", "state": str(store.state_path), "final_judgement": str(final_judgement)}


def _copy_plan_shared_context(task_graph_path: Path, run_dir: Path, *, project_root: Path) -> None:
    source = task_graph_path.parent / "shared_context.md"
    if not source.exists():
        return
    destination = run_dir / "shared_context.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        materialize_run_scoped_text(source.read_text(encoding="utf-8"), run_dir=run_dir, project_root=project_root),
        encoding="utf-8",
    )


def _safe_run_id(run_id: str) -> str:
    if run_id in (".", "..") or ".." in run_id or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise LifecycleInputError(f"invalid run-id: {run_id}")
    return run_id


def _mapping(value: JsonValue | None, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise LifecycleInputError(f"{field} must be an object")
    return value


def _string(value: JsonValue | None, field: str) -> str:
    if not isinstance(value, str):
        raise LifecycleInputError(f"{field} must be a string")
    return value


def _number(value: JsonValue | None, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LifecycleInputError(f"{field} must be a number")
    return float(value)
