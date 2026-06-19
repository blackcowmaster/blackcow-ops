from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypedDict

from .config import RunnerConfig, load_config
from .schema import SchemaError, validate_result


class ScorePayload(TypedDict):
    overall: int
    correctness: int
    safety: int
    tests: int


class ResultPayload(TypedDict):
    task_id: str
    replica_id: str
    status: str
    summary: str
    artifacts: list[str]
    changed_files: list[str]
    patch_path: str | None
    score: ScorePayload


class ProcessTerminator(Protocol):
    def __call__(self, process_group_id: int, signal_number: int) -> None: ...


class RunnerError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WorkerTask:
    task_id: str
    replica_id: str
    skill: str
    read_only: bool
    prompt_file: Path
    result_json: Path
    workspace: Path
    timeout_seconds: int
    missing_result_fatal: bool

    @property
    def key(self) -> str:
        return self.replica_id


@dataclass(frozen=True, slots=True)
class MockBehavior:
    status: str
    delay_seconds: float = 0.0
    malformed_json: bool = False
    omit_result: bool = False


@dataclass(frozen=True, slots=True)
class ProcessMetadata:
    pid: int
    process_group_id: int


@dataclass(frozen=True, slots=True)
class RunnerOutcome:
    status: str
    result_path: Path
    command: tuple[str, ...]
    started_at: float
    finished_at: float
    process: ProcessMetadata | None
    events: tuple[str, ...]


class MockRunner:
    def __init__(self, behavior: MockBehavior) -> None:
        self.behavior = behavior

    def run(self, task: WorkerTask) -> RunnerOutcome:
        _validate_worker_paths(task)
        started_at = time.time()
        if self.behavior.delay_seconds > 0:
            time.sleep(self.behavior.delay_seconds)
        _log_dir(task).mkdir(parents=True, exist_ok=True)
        (_log_dir(task) / "stdout.log").write_text("mock stdout\n", encoding="utf-8")
        (_log_dir(task) / "stderr.log").write_text("", encoding="utf-8")
        events = ["mock_started"]
        if not self.behavior.omit_result:
            if self.behavior.malformed_json:
                task.result_json.write_text("{not valid json", encoding="utf-8")
            else:
                _write_result(task.result_json, _result_payload(task, self.behavior.status))
            events.append("mock_result_written")
        return _verify_result(
            task,
            command=("mock-runner", task.skill),
            started_at=started_at,
            process=None,
            events=tuple(events),
        )


class ReasonixRunner:
    def __init__(self, runner_config: RunnerConfig, process_terminator: ProcessTerminator | None = None) -> None:
        self.runner_config = runner_config
        self.process_terminator = process_terminator if process_terminator is not None else _kill_process_group
        self.active_processes: dict[str, ProcessMetadata] = {}

    @classmethod
    def default(cls, process_terminator: ProcessTerminator | None = None) -> ReasonixRunner:
        return cls(load_config().runner, process_terminator=process_terminator)

    def build_command(self, task: WorkerTask) -> tuple[str, ...]:
        _validate_worker_paths(task)
        values = {
            "skill": task.skill,
            "prompt_file": str(task.prompt_file),
            "result_json": str(task.result_json),
            "workspace": str(task.workspace),
            "run_id": _run_id_from_result_path(task.result_json),
            "task_id": task.task_id,
            "replica_id": task.replica_id,
            "read_only": "true" if task.read_only else "false",
        }
        return tuple(part.format(**values) for part in self.runner_config.command_template)

    def run(self, task: WorkerTask) -> RunnerOutcome:
        started_at = time.time()
        command = self.build_command(task)
        _log_dir(task).mkdir(parents=True, exist_ok=True)
        try:
            process = subprocess.Popen(
                command,
                cwd=task.workspace,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
        )
        except FileNotFoundError:
            return _finish(task, command, started_at, None, ("runner_executable_missing",), "FAILED_FINAL")
        metadata = ProcessMetadata(pid=process.pid, process_group_id=os.getpgid(process.pid))
        self.active_processes[task.key] = metadata
        try:
            stdout, stderr = process.communicate(timeout=task.timeout_seconds)
            events = ("worker_exit_" + str(process.returncode),)
        except subprocess.TimeoutExpired:
            self.cancel(task.key)
            stdout, stderr = process.communicate()
            events = ("timeout",)
        except KeyboardInterrupt:
            self.cancel(task.key)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.process_terminator(metadata.process_group_id, signal.SIGKILL)
                process.communicate()
            self.active_processes.pop(task.key, None)
            raise
        (_log_dir(task) / "stdout.log").write_text(stdout, encoding="utf-8")
        (_log_dir(task) / "stderr.log").write_text(stderr, encoding="utf-8")
        self.active_processes.pop(task.key, None)
        return _verify_result(task, command=command, started_at=started_at, process=metadata, events=events)

    def verify_result(self, task: WorkerTask, events: tuple[str, ...]) -> RunnerOutcome:
        return _verify_result(task, command=self.build_command(task), started_at=time.time(), process=None, events=events)

    def record_process(self, key: str, *, pid: int, process_group_id: int) -> None:
        self.active_processes[key] = ProcessMetadata(pid=pid, process_group_id=process_group_id)

    def cancel(self, key: str) -> tuple[str, ...]:
        metadata = self.active_processes.get(key)
        if metadata is None:
            return ("cancel_missing_process",)
        self.process_terminator(metadata.process_group_id, signal.SIGTERM)
        return ("cancel_sigterm_sent",)


def _verify_result(
    task: WorkerTask,
    *,
    command: tuple[str, ...],
    started_at: float,
    process: ProcessMetadata | None,
    events: tuple[str, ...],
) -> RunnerOutcome:
    try:
        payload = json.loads(task.result_json.read_text(encoding="utf-8"))
        validate_result(payload)
    except FileNotFoundError:
        status = "FAILED_FINAL" if task.missing_result_fatal else "FAILED_RETRYABLE"
        return _finish(task, command, started_at, process, events + ("missing_result_json",), status)
    except json.JSONDecodeError:
        return _finish(task, command, started_at, process, events + ("invalid_result_json",), "FAILED_RETRYABLE")
    except SchemaError:
        return _finish(task, command, started_at, process, events + ("invalid_result_schema",), "FAILED_RETRYABLE")
    return _finish(task, command, started_at, process, events, payload["status"], enrich_result=True)


def _finish(
    task: WorkerTask,
    command: tuple[str, ...],
    started_at: float,
    process: ProcessMetadata | None,
    events: tuple[str, ...],
    status: str,
    *,
    enrich_result: bool = False,
) -> RunnerOutcome:
    finished_at = time.time()
    if enrich_result:
        _enrich_result_timing(task.result_json, started_at, finished_at)
    return RunnerOutcome(
        status=status,
        result_path=task.result_json,
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        process=process,
        events=events,
    )


def _write_result(path: Path, payload: ResultPayload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _enrich_result_timing(path: Path, started_at: float, finished_at: float) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return
    payload["started_at"] = started_at
    payload["finished_at"] = finished_at
    payload["duration_seconds"] = finished_at - started_at
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _result_payload(task: WorkerTask, status: str) -> ResultPayload:
    return {
        "task_id": task.task_id,
        "replica_id": task.replica_id,
        "status": status,
        "summary": f"Mock result for {task.replica_id}",
        "artifacts": [str(task.result_json)],
        "changed_files": [],
        "patch_path": None,
        "score": {"overall": 80, "correctness": 80, "safety": 80, "tests": 80},
    }


def _validate_worker_paths(task: WorkerTask) -> None:
    workspace = task.workspace.resolve()
    if ".." in task.workspace.parts:
        raise RunnerError("workspace path traversal is not allowed")
    for label, path in (("prompt_file", task.prompt_file), ("result_json", task.result_json)):
        if ".." in path.parts:
            raise RunnerError(f"{label} path traversal is not allowed")
        if not path.resolve().is_relative_to(workspace):
            raise RunnerError(f"{label} must be under workspace")


def _log_dir(task: WorkerTask) -> Path:
    return task.result_json.parent


def _run_id_from_result_path(path: Path) -> str:
    parts = path.parts
    for index, part in enumerate(parts):
        if part == "runs" and index + 1 < len(parts):
            return parts[index + 1]
    return path.parent.name


def _kill_process_group(process_group_id: int, signal_number: int) -> None:
    os.killpg(process_group_id, signal_number)
