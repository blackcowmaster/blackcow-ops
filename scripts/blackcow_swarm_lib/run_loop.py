from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue
from .run_diagnostics import RunDiagnosis, diagnose_run
from .task_graph import RUN_ID_PATTERN


RunExecutor = Callable[[Path, str | None, Path], dict[str, JsonValue]]


class RunLoopError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RunLoopAttempt:
    run_id: str
    status: str
    diagnosis: RunDiagnosis

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "diagnosis": self.diagnosis.to_json(),
        }


def execute_run_loop(
    task_graph_path: Path,
    *,
    base_run_id: str | None,
    project_root: Path,
    attempts: int,
    executor: RunExecutor,
) -> dict[str, JsonValue]:
    if attempts < 1:
        raise RunLoopError("attempts must be greater than zero")
    base = _base_run_id(task_graph_path, base_run_id)
    run_attempts: list[RunLoopAttempt] = []
    previous_signature = ""
    stopped_reason = "max_attempts"
    for attempt_index in range(1, attempts + 1):
        run_id = _attempt_run_id(base, attempt_index)
        output = executor(task_graph_path, run_id, project_root)
        status = _status(output)
        diagnosis = diagnose_run(project_root, run_id)
        run_attempts.append(RunLoopAttempt(run_id=run_id, status=status, diagnosis=diagnosis))
        if status == "SUCCEEDED":
            stopped_reason = "succeeded"
            break
        if previous_signature and previous_signature == diagnosis.signature:
            stopped_reason = "repeated_failure_signature"
            break
        if status == "CANCELLED" or (status == "BLOCKED" and not diagnosis.retryable):
            stopped_reason = status.lower()
            break
        previous_signature = diagnosis.signature
    return {
        "run_id": base,
        "status": run_attempts[-1].status,
        "stopped_reason": stopped_reason,
        "attempts": [attempt.to_json() for attempt in run_attempts],
    }


def _base_run_id(task_graph_path: Path, requested: str | None) -> str:
    if requested is not None:
        return _safe_run_id(requested)
    payload: JsonValue = json.loads(task_graph_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("run_id"), str):
        raise RunLoopError("task graph must contain a run_id when --run-id is omitted")
    return _safe_run_id(f"{payload['run_id']}-loop")


def _attempt_run_id(base: str, attempt_index: int) -> str:
    suffix = f"-a{attempt_index}"
    candidate = f"{base[:81 - len(suffix)]}{suffix}"
    return _safe_run_id(candidate)


def _status(output: dict[str, JsonValue]) -> str:
    status = output.get("status")
    if not isinstance(status, str):
        raise RunLoopError("executor output must contain a string status")
    return status


def _safe_run_id(run_id: str) -> str:
    if run_id in (".", "..") or ".." in run_id or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise RunLoopError(f"invalid run-id: {run_id}")
    return run_id
