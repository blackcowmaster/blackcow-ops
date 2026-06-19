from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

from blackcow_swarm_lib.config import JsonValue


FORBIDDEN_FAST_PATH_TOOLS = frozenset(("web_search", "explore"))


def terminal_transcript_error(transcript: Path) -> str | None:
    if not transcript.exists():
        return None
    for payload in _recent_json_payloads(transcript, line_limit=20):
        if payload.get("role") != "error":
            continue
        error_detail = payload.get("errorDetail")
        recoverable = error_detail.get("recoverable") if isinstance(error_detail, dict) else None
        error = payload.get("error")
        if recoverable is False and isinstance(error, str):
            return error
    return None


def forbidden_transcript_access(transcript: Path, forbidden_sources: tuple[str, ...]) -> str | None:
    if not forbidden_sources or not transcript.exists():
        return None
    for payload in _recent_json_payloads(transcript, line_limit=200):
        if payload.get("role") != "tool_start":
            continue
        haystack = json.dumps(payload.get("args", ""), ensure_ascii=False)
        for source in forbidden_sources:
            if _contains_path_token(haystack, source):
                return f"forbidden source access attempted: {source}"
    return None


def small_app_fast_path_violation(transcript: Path, prompt: str) -> str | None:
    if "Small App Fast Path" not in prompt or not transcript.exists():
        return None
    for payload in _recent_json_payloads(transcript, line_limit=200):
        if payload.get("role") != "tool_start":
            continue
        tool = _tool_name(payload)
        if tool in FORBIDDEN_FAST_PATH_TOOLS:
            return f"small app fast path violation: {tool}"
    return None


def _recent_json_payloads(transcript: Path, *, line_limit: int) -> Iterator[dict[str, JsonValue]]:
    try:
        lines = transcript.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in reversed(lines[-line_limit:]):
        try:
            payload: JsonValue = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _tool_name(payload: dict[str, JsonValue]) -> str | None:
    tool = payload.get("tool")
    if isinstance(tool, str):
        return tool
    name = payload.get("name")
    if isinstance(name, str):
        return name
    return None


def _contains_path_token(text: str, source: str) -> bool:
    pattern = re.compile(rf"(?<![\w-]){re.escape(source.strip('/'))}(?![\w-])")
    return bool(pattern.search(text))
