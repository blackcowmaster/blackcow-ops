from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .acceptance_runner import AcceptanceResult
from .config import JsonValue, load_config
from .judge import FinalJudge
from .lifecycle_completion import RepairSchedule, complete_run
from .lifecycle_graph import acceptance_checks, materialize_run_scoped_text, scheduled_tasks
from .reasonix_health import ReasonixHealthResult, run_reasonix_health_check
from .retrying_runner import RetryingRunner
from .scheduler import Scheduler
from .scheduler_rules import task_group_id
from .scheduler_types import ScheduledTask
from .schema import validate_task_graph
from .scratch_runner import ScratchReasonixRunner
from .state import RunStore
from .task_graph import RUN_ID_PATTERN


class LifecycleScratchInputError(ValueError):
    pass


def execute_reasonix_scratch_run(task_graph_path: Path, run_id: str | None, project_root: Path) -> dict[str, JsonValue]:
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
    store.append_event(safe_run_id, "run_started", {"runner": "reasonix-scratch", "tasks": len(tasks)})
    health = run_reasonix_health_check(_health_workspace(safe_run_id), run_dir, probe_model=True)
    if not health.ok:
        return _blocked_reasonix_preflight(safe_run_id, run_dir, store, health)
    runner = RetryingRunner(ScratchReasonixRunner(project_root), retry_limit=config.intensity[intensity].retry_limit)
    scheduler = Scheduler(max_workers=max(1, min(len(tasks), 4)))
    report = scheduler.run(tasks, runner, project_root, run_dir)

    def repair(*, attempt: int, acceptance_results: tuple[AcceptanceResult, ...]) -> RepairSchedule | None:
        repair_tasks = _repair_tasks(tasks, attempt, acceptance_results)
        if not repair_tasks:
            return None
        repair_report = Scheduler(max_workers=max(1, min(len(repair_tasks), 2))).run(repair_tasks, runner, project_root, run_dir)
        return RepairSchedule(tasks=repair_tasks, report=repair_report)

    return complete_run(
        checks=acceptance_checks(graph, run_dir=run_dir, project_root=project_root),
        safe_run_id=safe_run_id,
        run_dir=run_dir,
        store=store,
        tasks=tasks,
        report=report,
        project_root=project_root,
        summary_prefix="Reasonix scratch run",
        acceptance_repair=repair,
    )


def _repair_tasks(tasks: list[ScheduledTask], attempt: int, acceptance_results: tuple[AcceptanceResult, ...]) -> list[ScheduledTask]:
    failed = tuple(result for result in acceptance_results if not result.ok)
    if not failed:
        return []
    repair_tasks: list[ScheduledTask] = []
    for task in tasks:
        if task.read_only:
            continue
        repair_id = f"{task_group_id(task.replica_id)}-repair{attempt}-r1"
        repair_tasks.append(
            ScheduledTask(
                task_id=repair_id,
                replica_id=repair_id,
                kind=task.kind,
                skill=task.skill,
                prompt=_repair_prompt(task.prompt, attempt, acceptance_results),
                depends_on=(),
                read_only=False,
                writes=task.writes,
                acceptance_checks=task.acceptance_checks,
                timeout_seconds=task.timeout_seconds,
            )
        )
    return repair_tasks


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


def _repair_prompt(base_prompt: str, attempt: int, results: tuple[AcceptanceResult, ...]) -> str:
    passed = tuple(result for result in results if result.ok)
    failed = tuple(result for result in results if not result.ok)
    failures = "\n\n".join(_failure_block(index, result) for index, result in enumerate(failed[:3], start=1))
    parts = [
        base_prompt,
        "",
        "## Acceptance Repair Feedback",
        f"Repair attempt: {attempt}",
        "The previous integrated candidate failed controller acceptance. Generate a complete replacement candidate, not a partial note.",
        "Make the exact acceptance commands pass in the controller environment. Do not rely on missing node_modules or generated cache folders.",
        "Do not regress any acceptance check that already passed in the immediately previous integrated candidate.",
        "For no-install Expo/React Native scaffold checks, do not extend expo/tsconfig.base or other node_modules-only tsconfig files, avoid deprecated baseUrl/node10 TypeScript options, and make typecheck/lint scripts runnable before npm install.",
        'For scratch Expo/RN package.json, use "typecheck": "tsc --noEmit" and "lint": "tsc --noEmit"; scripts MUST NOT invoke eslint before dependencies are installed.',
        "If source imports React Native, Expo, navigation, storage, or React modules before npm install, add local .d.ts declarations for each imported external module and react/jsx-runtime when using react-jsx.",
        "Do not shadow React with recursive export= declarations; if stubbing React, declare the default export and every named API you import such as useState, useEffect, useCallback, ReactElement, ComponentType, and ReactNode.",
        "Keep required project config files such as package.json, tsconfig.json, app.json, and DESIGN.md present in the project root.",
    ]
    if passed:
        parts.extend(("", "### Previously passing acceptance checks to preserve", _passed_checks_block(passed)))
    parts.extend(("", failures))
    return "\n".join(parts)


def _passed_checks_block(passed: tuple[AcceptanceResult, ...]) -> str:
    return "\n".join(
        f"- {result.command}"
        for result in passed[:6]
    )


def _failure_block(index: int, result: AcceptanceResult) -> str:
    parts = [
        f"### Failed check {index}",
        f"Command: {result.command}",
        f"Exit code: {result.exit_code}",
    ]
    stdout = _read_excerpt(result.stdout_path)
    stderr = _read_excerpt(result.stderr_path)
    if stdout:
        parts.extend(("Stdout excerpt:", stdout))
    if stderr:
        parts.extend(("Stderr excerpt:", stderr))
    return "\n".join(parts)


def _read_excerpt(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    return text.strip()[:1600]


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
        summary=f"Reasonix scratch run BLOCKED: {health.summary}",
        selected_patches=(),
        score_overall=0,
    )
    return {"run_id": safe_run_id, "status": "BLOCKED", "state": str(store.state_path), "final_judgement": str(final_judgement)}


def _safe_run_id(run_id: str) -> str:
    if run_id in (".", "..") or ".." in run_id or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise LifecycleScratchInputError(f"invalid run-id: {run_id}")
    return run_id


def _health_workspace(run_id: str) -> Path:
    workspace = Path(tempfile.gettempdir()) / "blackcow-reasonix-scratch-health" / run_id
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _mapping(value: JsonValue | None, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise LifecycleScratchInputError(f"{field} must be an object")
    return value


def _string(value: JsonValue | None, field: str) -> str:
    if not isinstance(value, str):
        raise LifecycleScratchInputError(f"{field} must be a string")
    return value
