from __future__ import annotations

import shlex
from pathlib import Path

from .config import JsonValue
from .scheduler_types import ScheduledTask


def scheduled_tasks(
    graph: dict[str, JsonValue],
    *,
    run_dir: Path | None = None,
    project_root: Path | None = None,
) -> list[ScheduledTask]:
    task_payloads = [_mapping(task, "task") for task in _list(graph["tasks"], "task_graph.tasks")]
    replica_counts = {_string(task["id"], "task.id"): _int(task["replicas"], "task.replicas") for task in task_payloads}
    scheduled: list[ScheduledTask] = []
    for task in task_payloads:
        task_id = _string(task["id"], "task.id")
        for replica_number in range(1, replica_counts[task_id] + 1):
            replica_id = f"{task_id}-r{replica_number}"
            depends_on = _expanded_dependencies(_string_list(task["depends_on"], "task.depends_on"), replica_counts)
            scheduled.append(
                _scheduled_task(
                    task,
                    unique_task_id=replica_id,
                    replica_id=replica_id,
                    depends_on=depends_on,
                    run_dir=run_dir,
                    project_root=project_root,
                )
            )
    return scheduled


def acceptance_checks(
    graph: dict[str, JsonValue],
    *,
    run_dir: Path | None = None,
    project_root: Path | None = None,
) -> tuple[str, ...]:
    checks: list[str] = []
    for task in _list(graph["tasks"], "task_graph.tasks"):
        task_payload = _mapping(task, "task")
        checks.extend(
            _materialize_acceptance_checks(
                _string_list(task_payload["acceptance_checks"], "task.acceptance_checks"),
                run_dir=run_dir,
                project_root=project_root,
            )
        )
    return tuple(dict.fromkeys(checks))


def materialize_run_scoped_text(text: str, *, run_dir: Path, project_root: Path | None = None) -> str:
    lines = []
    for line in text.splitlines():
        lines.append(_materialize_acceptance_check(line, run_dir=run_dir, project_root=project_root))
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _expanded_dependencies(dependencies: tuple[str, ...], replica_counts: dict[str, int]) -> tuple[str, ...]:
    expanded: list[str] = []
    for dependency in dependencies:
        replicas = replica_counts.get(dependency, 1)
        expanded.extend(f"{dependency}-r{replica_number}" for replica_number in range(1, replicas + 1))
    return tuple(expanded)


def _scheduled_task(
    task: dict[str, JsonValue],
    *,
    unique_task_id: str,
    replica_id: str,
    depends_on: tuple[str, ...],
    run_dir: Path | None,
    project_root: Path | None,
) -> ScheduledTask:
    return ScheduledTask(
        task_id=unique_task_id,
        replica_id=replica_id,
        kind=_string(task["kind"], "task.kind"),
        skill=_string(task["skill"], "task.skill"),
        prompt=_string(task["prompt"], "task.prompt"),
        depends_on=depends_on,
        read_only=bool(task["read_only"]),
        writes=_string_list(task["writes"], "task.writes"),
        acceptance_checks=_materialize_acceptance_checks(
            _string_list(task["acceptance_checks"], "task.acceptance_checks"),
            run_dir=run_dir,
            project_root=project_root,
        ),
        timeout_seconds=_int(task["timeout_minutes"], "task.timeout_minutes") * 60,
    )


def _materialize_acceptance_checks(
    checks: tuple[str, ...],
    *,
    run_dir: Path | None,
    project_root: Path | None,
) -> tuple[str, ...]:
    return tuple(_materialize_acceptance_check(check, run_dir=run_dir, project_root=project_root) for check in checks)


def _materialize_acceptance_check(check: str, *, run_dir: Path | None, project_root: Path | None) -> str:
    if run_dir is None or "scripts/blackcow_speed_gate.py" not in check or "--run-dir" not in check:
        return check
    try:
        parts = shlex.split(check)
    except ValueError:
        return check
    try:
        run_dir_index = parts.index("--run-dir") + 1
    except ValueError:
        return check
    if run_dir_index >= len(parts):
        return check
    parts[run_dir_index] = _display_run_dir(run_dir, project_root=project_root)
    return shlex.join(parts)


def _display_run_dir(run_dir: Path, *, project_root: Path | None) -> str:
    if project_root is None:
        return run_dir.as_posix()
    try:
        return run_dir.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return run_dir.as_posix()


def _mapping(value: JsonValue | None, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _list(value: JsonValue | None, field: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _string(value: JsonValue | None, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _string_list(value: JsonValue | None, field: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{field}[]") for item in _list(value, field))


def _int(value: JsonValue | None, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value
