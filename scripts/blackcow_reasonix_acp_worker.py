#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import select
import signal
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from blackcow_swarm_lib.acp_transcript_guard import (
    forbidden_transcript_access,
    small_app_fast_path_violation,
    terminal_transcript_error,
)
from blackcow_swarm_lib.config import JsonValue
from blackcow_swarm_lib.forbidden_sources import forbidden_sources_from_prompt
from blackcow_swarm_lib.acp_worker_contract import build_prompt, repair_prompt, validate_result_file
from blackcow_swarm_lib.reasonix_command import ACP_MCP_ISOLATION_ARGS


@dataclass(frozen=True, slots=True)
class AcpResponse:
    result: dict[str, JsonValue]


class AcpWorkerError(Exception):
    pass


class AcpClient:
    def __init__(
        self,
        process: subprocess.Popen[str],
        *,
        transcript_path: Path | None,
        prompt_contract: str,
        forbidden_sources: tuple[str, ...] = (),
    ) -> None:
        if process.stdin is None or process.stdout is None:
            raise AcpWorkerError("reasonix acp stdio pipes are required")
        self.process = process
        self.stdin = process.stdin
        self.stdout = process.stdout
        self.transcript_path = transcript_path
        self.prompt_contract = prompt_contract
        self.forbidden_sources = forbidden_sources

    def request(
        self,
        request_id: int,
        method: str,
        params: Mapping[str, JsonValue],
        *,
        timeout_seconds: int,
        early_result_json: Path | None = None,
    ) -> AcpResponse:
        self.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
        self.stdin.flush()
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if early_result_json is not None and validate_result_file(early_result_json) is None:
                return AcpResponse(result={"stopReason": "end_turn", "earlyResult": True})
            if self.transcript_path is not None:
                terminal_error = terminal_transcript_error(self.transcript_path)
                if terminal_error is not None:
                    raise AcpWorkerError(terminal_error)
                forbidden_access = forbidden_transcript_access(self.transcript_path, self.forbidden_sources)
                if forbidden_access is not None:
                    raise AcpWorkerError(forbidden_access)
                fast_path_violation = small_app_fast_path_violation(self.transcript_path, self.prompt_contract)
                if fast_path_violation is not None:
                    raise AcpWorkerError(fast_path_violation)
            ready, _, _ = select.select([self.stdout], [], [], 0.5)
            if not ready:
                if self.process.poll() is not None:
                    raise AcpWorkerError("reasonix acp exited before response")
                continue
            line = self.stdout.readline()
            if not line:
                continue
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                if isinstance(error, dict):
                    raise AcpWorkerError(str(error.get("message", error)))
                raise AcpWorkerError(str(error))
            result = message.get("result")
            if not isinstance(result, dict):
                raise AcpWorkerError(f"invalid ACP result for {method}")
            return AcpResponse(result=result)
        raise TimeoutError(f"reasonix acp timed out waiting for {method}")


def run_worker(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    prompt_file = Path(args.prompt_file).resolve()
    result_json = Path(args.result_json).resolve()
    transcript = Path(args.transcript).resolve() if args.transcript else result_json.parent / "reasonix-transcript.jsonl"
    result_json.parent.mkdir(parents=True, exist_ok=True)
    transcript.parent.mkdir(parents=True, exist_ok=True)
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            [
                "reasonix",
                "acp",
                "--yolo",
                "--dir",
                str(workspace),
                "--budget",
                str(args.budget),
                "--effort",
                args.effort,
                *ACP_MCP_ISOLATION_ARGS,
                "--transcript",
                str(transcript),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        print("reasonix acp worker failed: reasonix executable missing", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"reasonix acp worker failed: failed to start reasonix executable: {exc}", file=sys.stderr)
        return 1
    try:
        prompt_contract = prompt_file.read_text(encoding="utf-8")
        forbidden_sources = forbidden_sources_from_prompt(prompt_contract)
        client = AcpClient(
            process,
            transcript_path=transcript,
            prompt_contract=prompt_contract,
            forbidden_sources=forbidden_sources,
        )
        client.request(1, "initialize", {"protocolVersion": 1, "clientInfo": {"name": "blackcow-swarm", "version": "1"}}, timeout_seconds=20)
        session = client.request(2, "session/new", {"cwd": str(workspace)}, timeout_seconds=45)
        session_id = session.result.get("sessionId")
        if not isinstance(session_id, str) or not session_id:
            raise AcpWorkerError("reasonix acp did not return a sessionId")
        prompt = build_prompt(prompt_file, result_json, args.task_id, args.replica_id, args.read_only.lower() == "true")
        for request_id in (3, 4):
            response = client.request(
                request_id,
                "session/prompt",
                {"sessionId": session_id, "prompt": [{"type": "text", "text": prompt}]},
                timeout_seconds=args.timeout_seconds,
                early_result_json=result_json,
            )
            if response.result.get("stopReason") != "end_turn":
                print(f"reasonix acp stopReason={response.result.get('stopReason')}", file=sys.stderr)
                return 1
            validation_error = validate_result_file(result_json)
            if validation_error is None:
                return 0
            prompt = repair_prompt(result_json, validation_error, args.task_id, args.replica_id)
        final_error = validate_result_file(result_json)
        print(f"reasonix acp result_json is invalid after repair: {final_error}", file=sys.stderr)
        return 1
    except (AcpWorkerError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"reasonix acp worker failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if process is not None:
            _terminate(process)


def _terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        process_group_id = os.getpgid(process.pid)
        if process_group_id == os.getpgrp():
            process.terminate()
        else:
            os.killpg(process_group_id, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            process_group_id = os.getpgid(process.pid)
            if process_group_id == os.getpgrp():
                process.kill()
            else:
                os.killpg(process_group_id, signal.SIGKILL)
        except ProcessLookupError:
            return


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a BlackCow worker through Reasonix ACP.")
    parser.add_argument("--skill", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--replica-id", required=True)
    parser.add_argument("--read-only", choices=("true", "false"), default="false")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--budget", type=float, default=0.15)
    parser.add_argument("--effort", choices=("low", "medium", "high", "max"), default="medium")
    parser.add_argument("--transcript")
    return run_worker(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
