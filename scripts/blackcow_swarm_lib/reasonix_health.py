from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue
from .reasonix_command import ACP_MCP_ISOLATION_ARGS, ACP_MODEL_PREFLIGHT_PROMPT


@dataclass(frozen=True, slots=True)
class ReasonixHealthResult:
    ok: bool
    summary: str
    started_at: float
    finished_at: float
    transcript_path: Path
    stdout_path: Path
    stderr_path: Path


class ReasonixHealthError(Exception):
    pass


def run_reasonix_health_check(
    workspace: Path,
    run_dir: Path,
    command: tuple[str, ...] | None = None,
    timeout_seconds: float = 6.0,
    probe_model: bool = False,
    model_timeout_seconds: float = 20.0,
) -> ReasonixHealthResult:
    started_at = time.time()
    health_dir = run_dir / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = health_dir / "reasonix-health-transcript.jsonl"
    stdout_path = health_dir / "stdout.log"
    stderr_path = health_dir / "stderr.log"
    transcript_path.touch(exist_ok=True)
    stdout_lines: list[str] = []
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command if command is not None else _default_command(workspace, transcript_path),
            cwd=workspace,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        _request(
            process,
            1,
            "initialize",
            {"protocolVersion": 1, "clientInfo": {"name": "blackcow-swarm", "version": "1"}},
            min(2.0, timeout_seconds),
            stdout_lines,
        )
        remaining_seconds = max(0.1, timeout_seconds - (time.time() - started_at))
        session = _request(process, 2, "session/new", {"cwd": str(workspace)}, remaining_seconds, stdout_lines)
        session_id = session.get("sessionId")
        if not isinstance(session_id, str) or not session_id:
            raise ReasonixHealthError("missing sessionId")
        if probe_model:
            _probe_model(process, session_id, model_timeout_seconds, stdout_lines)
        return _finish(process, started_at, "reasonix acp health ok", True, transcript_path, stdout_path, stderr_path, stdout_lines)
    except FileNotFoundError:
        return _finish(None, started_at, "reasonix acp health failed: reasonix executable missing", False, transcript_path, stdout_path, stderr_path, stdout_lines)
    except (TimeoutError, ReasonixHealthError, json.JSONDecodeError, OSError) as exc:
        return _finish(process, started_at, f"reasonix acp health failed: {exc}", False, transcript_path, stdout_path, stderr_path, stdout_lines)


def _default_command(workspace: Path, transcript_path: Path) -> tuple[str, ...]:
    return (
        "reasonix",
        "acp",
        "--yolo",
        "--dir",
        str(workspace),
        "--budget",
        "0.01",
        "--effort",
        "low",
        *ACP_MCP_ISOLATION_ARGS,
        "--transcript",
        str(transcript_path),
    )


def _request(
    process: subprocess.Popen[str],
    request_id: int,
    method: str,
    params: Mapping[str, JsonValue],
    timeout_seconds: float,
    stdout_lines: list[str],
) -> dict[str, JsonValue]:
    if process.stdin is None or process.stdout is None:
        raise ReasonixHealthError("stdio pipes unavailable")
    stdout_fd = process.stdout.fileno()
    pending = b""
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
    process.stdin.flush()
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        while b"\n" not in pending:
            ready, _, _ = select.select([stdout_fd], [], [], 0.05)
            if not ready:
                if process.poll() is not None:
                    raise ReasonixHealthError(f"reasonix acp exited before {method}")
                if time.time() >= deadline:
                    break
                continue
            chunk = os.read(stdout_fd, 4096)
            if not chunk:
                raise ReasonixHealthError(f"reasonix acp exited before {method}")
            pending += chunk
        if b"\n" not in pending:
            continue
        raw_line, _, pending = pending.partition(b"\n")
        line = raw_line.decode("utf-8", errors="replace") + "\n"
        stdout_lines.append(line)
        payload: JsonValue = json.loads(line)
        if not isinstance(payload, dict) or payload.get("id") != request_id:
            continue
        if "error" in payload:
            raise ReasonixHealthError(_acp_error_text(payload["error"]))
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ReasonixHealthError(f"invalid ACP health result for {method}")
        return result
    raise TimeoutError(f"reasonix acp timed out waiting for {method}")


def _probe_model(
    process: subprocess.Popen[str],
    session_id: str,
    timeout_seconds: float,
    stdout_lines: list[str],
) -> None:
    try:
        result = _request(
            process,
            3,
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": ACP_MODEL_PREFLIGHT_PROMPT}]},
            timeout_seconds,
            stdout_lines,
        )
    except (ReasonixHealthError, TimeoutError) as exc:
        raise ReasonixHealthError(f"model preflight failed: {exc}") from exc
    stop_reason = result.get("stopReason")
    if stop_reason != "end_turn":
        detail = _last_session_update_error(stdout_lines)
        reason = detail if detail is not None else f"stopReason={stop_reason}"
        raise ReasonixHealthError(f"model preflight failed: {reason}")


def _last_session_update_error(stdout_lines: list[str]) -> str | None:
    for line in reversed(stdout_lines):
        try:
            payload: JsonValue = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or payload.get("method") != "session/update":
            continue
        params = payload.get("params")
        if not isinstance(params, dict):
            continue
        update = params.get("update")
        if not isinstance(update, dict):
            continue
        metadata = update.get("metadata")
        if not isinstance(metadata, dict):
            continue
        error = metadata.get("error")
        if isinstance(error, str):
            return error
        if not isinstance(error, dict):
            continue
        message = error.get("message")
        if isinstance(message, str):
            return message
    return None


def _finish(
    process: subprocess.Popen[str] | None,
    started_at: float,
    summary: str,
    ok: bool,
    transcript_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    stdout_lines: list[str],
) -> ReasonixHealthResult:
    stdout_tail = ""
    stderr_tail = ""
    if process is not None:
        _terminate(process)
        stdout_tail, stderr_tail = _collect_output(process)
    stdout_path.write_text("".join(stdout_lines) + stdout_tail, encoding="utf-8")
    stderr_path.write_text(stderr_tail, encoding="utf-8")
    return ReasonixHealthResult(
        ok=ok,
        summary=summary,
        started_at=started_at,
        finished_at=time.time(),
        transcript_path=transcript_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


def _terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=1)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait(timeout=1)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            return


def _collect_output(process: subprocess.Popen[str]) -> tuple[str, str]:
    try:
        return process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        return "", "reasonix acp process did not exit after forced termination\n"


def _acp_error_text(error: JsonValue) -> str:
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str):
            return message
    return str(error)
