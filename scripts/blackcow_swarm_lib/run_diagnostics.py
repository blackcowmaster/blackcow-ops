from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue
from .task_graph import RUN_ID_PATTERN


class RunDiagnosisError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RunDiagnosis:
    summary: str
    signature: str
    retryable: bool
    source: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "summary": self.summary,
            "signature": self.signature,
            "retryable": self.retryable,
            "source": self.source,
        }


def diagnose_run(project_root: Path, run_id: str) -> RunDiagnosis:
    safe_run_id = _safe_run_id(run_id)
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    state = _mapping(json.loads((run_dir / "state.json").read_text(encoding="utf-8")), "state")
    status = _string(state.get("status"), "state.status")
    if status == "SUCCEEDED":
        return RunDiagnosis("run succeeded", "run:SUCCEEDED", retryable=False, source="state")
    retryable_worker = _first_failed_worker(state, run_dir, retryable_only=True)
    if retryable_worker is not None:
        return retryable_worker
    acceptance = _first_failed_acceptance(state, run_dir)
    if acceptance is not None:
        return acceptance
    worker = _first_failed_worker(state, run_dir)
    if worker is not None:
        return worker
    final_summary = _final_summary(run_dir)
    if final_summary:
        return RunDiagnosis(final_summary, _signature("final", final_summary), retryable=_health_retryable(run_dir), source="final_judgement")
    return RunDiagnosis(f"run ended with status {status}", f"run:{status}", retryable=False, source="state")


def _first_failed_acceptance(state: dict[str, JsonValue], run_dir: Path) -> RunDiagnosis | None:
    acceptance = state.get("acceptance")
    if not isinstance(acceptance, list):
        return None
    for item in acceptance:
        if not isinstance(item, dict) or item.get("status") != "FAILED":
            continue
        command = _string(item.get("command"), "acceptance.command")
        stderr = _read_log_excerpt(item.get("stderr"))
        stdout = _read_log_excerpt(item.get("stdout"))
        detail = stderr or stdout or f"acceptance command failed: {command}"
        return RunDiagnosis(detail, _signature("acceptance", command, detail), retryable=False, source=str(run_dir / "acceptance"))
    return None


def _first_failed_worker(state: dict[str, JsonValue], run_dir: Path, *, retryable_only: bool = False) -> RunDiagnosis | None:
    workers = _mapping(state.get("workers"), "state.workers")
    for worker_id, value in workers.items():
        worker = _mapping(value, f"workers.{worker_id}")
        status = _string(worker.get("status"), f"workers.{worker_id}.status")
        if status == "SUCCEEDED":
            continue
        result = _worker_result(run_dir, worker_id)
        if result is not None:
            result_status = _string(result.get("status"), "result.status")
            summary = _string(result.get("summary"), "result.summary")
            retryable = result_status == "FAILED_RETRYABLE"
            if retryable_only and not retryable:
                continue
            return RunDiagnosis(
                f"{worker_id} {result_status}: {summary}",
                _signature("worker", worker_id, result_status, summary),
                retryable=retryable,
                source=str(run_dir / "workers" / worker_id / "result.json"),
            )
        stderr = _first_non_empty_line(run_dir / "workers" / worker_id / "stderr.log")
        detail = stderr or f"{worker_id} ended with status {status}"
        retryable = status == "FAILED_RETRYABLE"
        if retryable_only and not retryable:
            continue
        return RunDiagnosis(detail, _signature("worker", worker_id, status, detail), retryable=retryable, source="worker")
    return None


def _worker_result(run_dir: Path, worker_id: str) -> dict[str, JsonValue] | None:
    try:
        return _mapping(json.loads((run_dir / "workers" / worker_id / "result.json").read_text(encoding="utf-8")), "result")
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _final_summary(run_dir: Path) -> str:
    try:
        payload = _mapping(json.loads((run_dir / "final_judgement.json").read_text(encoding="utf-8")), "final")
    except FileNotFoundError:
        return ""
    except json.JSONDecodeError:
        return ""
    return _string(payload.get("summary"), "final.summary") if "summary" in payload else ""


def _health_retryable(run_dir: Path) -> bool:
    try:
        lines = (run_dir / "health" / "stdout.log").read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return False
    for line in lines:
        try:
            payload: JsonValue = json.loads(line)
        except json.JSONDecodeError:
            continue
        if _contains_retryable_true(payload):
            return True
    return False


def _contains_retryable_true(value: JsonValue) -> bool:
    match value:
        case {"retryable": True, **rest}:
            return True
        case dict() as mapping:
            return any(_contains_retryable_true(item) for item in mapping.values())
        case list() as items:
            return any(_contains_retryable_true(item) for item in items)
        case _:
            return False


def _read_log_excerpt(value: JsonValue | None) -> str:
    if not isinstance(value, str):
        return ""
    return _most_relevant_log_line(Path(value))


def _most_relevant_log_line(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return ""
    for line in lines:
        stripped = line.strip()
        if _looks_actionable(stripped):
            return stripped[:500]
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith(">"):
            return stripped[:500]
    return _first_non_empty_line(path)


def _looks_actionable(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in ("error", "failed", "missing", "not found", "exception", "traceback"))


def _first_non_empty_line(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return ""
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped[:500]
    return ""


def _signature(*parts: str) -> str:
    normalized = " ".join(_normalize(part) for part in parts if part)
    return normalized[:240]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _safe_run_id(run_id: str) -> str:
    if run_id in (".", "..") or ".." in run_id or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise RunDiagnosisError(f"invalid run-id: {run_id}")
    return run_id


def _mapping(value: JsonValue | None, field: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise RunDiagnosisError(f"{field} must be an object")
    return value


def _string(value: JsonValue | None, field: str) -> str:
    if not isinstance(value, str):
        raise RunDiagnosisError(f"{field} must be a string")
    return value
