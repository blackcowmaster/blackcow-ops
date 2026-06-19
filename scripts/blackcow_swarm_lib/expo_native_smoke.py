from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue
from .native_smoke import run_native_smoke
from .visual_review import run_visual_review


@dataclass(frozen=True, slots=True)
class ExpoNativeSmokeResult:
    ok: bool
    message: str


def run_expo_native_smoke(
    *,
    project_root: Path,
    project: str,
    platform: str,
    screenshot_path: Path,
    review_output: Path,
    expect: tuple[str, ...],
    xcrun_bin: str = "xcrun",
    codex_bin: str = "codex",
    startup_wait_seconds: int = 45,
    start_command: tuple[str, ...] | None = None,
) -> ExpoNativeSmokeResult:
    project_path = project_root / project
    package_json = project_path / "package.json"
    if not package_json.exists():
        return ExpoNativeSmokeResult(ok=False, message=f"missing package.json for native smoke: {package_json}")
    if not _is_expo_project(package_json):
        return ExpoNativeSmokeResult(ok=False, message=f"native managed smoke currently requires Expo: {project}")
    command = start_command or ("npm", "run", platform)
    process = subprocess.Popen(
        command,
        cwd=project_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        startup_failure = _wait_for_startup_failure(process, startup_wait_seconds)
        if startup_failure:
            return ExpoNativeSmokeResult(ok=False, message=startup_failure)
        native = run_native_smoke(project, platform, xcrun_bin=xcrun_bin, screenshot_path=screenshot_path)
        if not native.ok:
            return ExpoNativeSmokeResult(ok=False, message=native.message)
        visual = run_visual_review(screenshot_path, review_output, expect=expect, codex_bin=codex_bin)
        if not visual.ok:
            return ExpoNativeSmokeResult(ok=False, message=visual.message)
        return ExpoNativeSmokeResult(ok=True, message=f"Expo native smoke passed for {project}: {screenshot_path}")
    finally:
        _terminate_process_group(process)


def _is_expo_project(package_json: Path) -> bool:
    payload: JsonValue = json.loads(package_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return False
    dependencies = payload.get("dependencies")
    return isinstance(dependencies, dict) and "expo" in dependencies


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
    _communicate_process(process)


def _wait_for_startup_failure(process: subprocess.Popen[str], startup_wait_seconds: int) -> str:
    deadline = time.time() + max(0, startup_wait_seconds)
    while time.time() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            return _startup_exit_message(process, exit_code)
        time.sleep(min(0.2, max(0.0, deadline - time.time())))
    exit_code = process.poll()
    if exit_code is not None:
        return _startup_exit_message(process, exit_code)
    return ""


def _startup_exit_message(process: subprocess.Popen[str], exit_code: int) -> str:
    if exit_code == 0:
        return ""
    stdout, stderr = _communicate_process(process)
    return f"Expo native start command failed with exit code {exit_code}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}".strip()


def _communicate_process(process: subprocess.Popen[str]) -> tuple[str, str]:
    try:
        stdout, stderr = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        return "", ""
    return stdout or "", stderr or ""
