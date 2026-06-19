from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from .config import JsonValue
from .runner import ReasonixRunner, WorkerTask
from .schema import validate_task_graph
from .skill_contract import build_worker_prompt
from .task_graph import RUN_ID_PATTERN


class WorkerCommandPayload(TypedDict):
    replica_id: str
    task_id: str
    command: list[str]


class DryRunOutput(TypedDict):
    dry_run: bool
    run_id: str
    run_dir: str
    state: str
    events: str
    worker_commands: list[WorkerCommandPayload]


class StateError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RunStore:
    run_dir: Path

    @property
    def state_path(self) -> Path:
        return self.run_dir / "state.json"

    @property
    def events_path(self) -> Path:
        return self.run_dir / "events.jsonl"

    @property
    def lock_path(self) -> Path:
        return self.run_dir / "orchestrator.lock"

    def acquire_lock(self) -> StateLock:
        return StateLock(self.lock_path)

    def write_state(self, payload: Mapping[str, JsonValue]) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        temp_path = self.run_dir / f".state.json.{os.getpid()}.tmp"
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp_path.replace(self.state_path)

    def append_event(self, run_id: str, event: str, details: Mapping[str, JsonValue]) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        payload = {"ts": _now(), "run_id": run_id, "event": event, "details": dict(details)}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


@dataclass(frozen=True, slots=True)
class StateLock:
    lock_path: Path

    def __enter__(self) -> StateLock:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise StateError(f"run is locked: {self.lock_path}") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "ts": _now()}) + "\n")
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            return


def execute_dry_run(task_graph_path: Path, run_id: str | None, project_root: Path) -> DryRunOutput:
    graph_payload: JsonValue = json.loads(task_graph_path.read_text(encoding="utf-8"))
    validate_task_graph(graph_payload)
    graph = _mapping(graph_payload, "task_graph")
    safe_run_id = _safe_run_id(run_id, _string(graph["run_id"], "task_graph.run_id"))
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    store = RunStore(run_dir)
    runner = ReasonixRunner.default()
    with store.acquire_lock():
        tasks = _list(graph["tasks"], "task_graph.tasks")
        store.append_event(safe_run_id, "dry_run_started", {"task_graph": str(task_graph_path), "tasks": len(tasks)})
        worker_commands = _render_worker_commands(tasks, run_dir, project_root, runner, store, safe_run_id)
        state = _state_payload(safe_run_id, worker_commands)
        store.write_state(state)
        store.append_event(safe_run_id, "dry_run_complete", {"workers": len(worker_commands)})
    return {
        "dry_run": True,
        "run_id": safe_run_id,
        "run_dir": str(run_dir),
        "state": str(store.state_path),
        "events": str(store.events_path),
        "worker_commands": worker_commands,
    }


def _render_worker_commands(
    tasks: list[JsonValue],
    run_dir: Path,
    project_root: Path,
    runner: ReasonixRunner,
    store: RunStore,
    run_id: str,
) -> list[WorkerCommandPayload]:
    prompt_dir = run_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    commands: list[WorkerCommandPayload] = []
    for task_payload in tasks:
        task = _mapping(task_payload, "task")
        task_id = _string(task["id"], "task.id")
        replicas = _int(task["replicas"], "task.replicas")
        for replica_number in range(1, replicas + 1):
            replica_id = f"{task_id}-r{replica_number}"
            prompt_file = prompt_dir / f"{replica_id}.md"
            result_json = run_dir / "planned-results" / replica_id / "result.json"
            prompt_file.write_text(
                build_worker_prompt(
                    project_root=project_root,
                    run_dir=run_dir,
                    skill=_string(task["skill"], "task.skill"),
                    base_prompt=_string(task["prompt"], "task.prompt"),
                    task_id=task_id,
                    replica_id=replica_id,
                    result_json=result_json,
                    acceptance_checks=_string_list(task["acceptance_checks"], "task.acceptance_checks"),
                )
                + "\n",
                encoding="utf-8",
            )
            worker_task = WorkerTask(
                task_id=task_id,
                replica_id=replica_id,
                skill=_string(task["skill"], "task.skill"),
                read_only=bool(task["read_only"]),
                prompt_file=prompt_file,
                result_json=result_json,
                workspace=project_root,
                timeout_seconds=_int(task["timeout_minutes"], "task.timeout_minutes") * 60,
                missing_result_fatal=False,
            )
            command = list(runner.build_command(worker_task))
            commands.append({"replica_id": replica_id, "task_id": task_id, "command": command})
            store.append_event(run_id, "worker_planned", {"replica_id": replica_id, "task_id": task_id})
    return commands


def _state_payload(run_id: str, worker_commands: list[WorkerCommandPayload]) -> dict[str, JsonValue]:
    return {
        "run_id": run_id,
        "status": "DRY_RUN",
        "workers": {
            command["replica_id"]: {"task_id": command["task_id"], "status": "PLANNED", "command": command["command"]}
            for command in worker_commands
        },
    }


def _safe_run_id(requested: str | None, fallback: str) -> str:
    candidate = requested if requested is not None else fallback
    if candidate in (".", "..") or ".." in candidate or RUN_ID_PATTERN.fullmatch(candidate) is None:
        raise StateError(f"invalid run-id: {candidate}")
    return candidate


def _mapping(value: JsonValue, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise StateError(f"{field} must be an object")
    return value


def _list(value: JsonValue, field: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise StateError(f"{field} must be a list")
    return value


def _string(value: JsonValue, field: str) -> str:
    if not isinstance(value, str):
        raise StateError(f"{field} must be a string")
    return value


def _string_list(value: JsonValue, field: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{field}[]") for item in _list(value, field))


def _int(value: JsonValue, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StateError(f"{field} must be an integer")
    return value


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
