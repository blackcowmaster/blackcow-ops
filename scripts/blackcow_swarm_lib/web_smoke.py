from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .browser_smoke import BrowserSmokeResult, run_browser_smoke


@dataclass(frozen=True, slots=True)
class ManagedWebSmokeResult:
    ok: bool
    message: str
    browser: BrowserSmokeResult | None


def run_managed_web_smoke(
    *,
    project_root: Path,
    project: str,
    port: int,
    expect: tuple[str, ...],
    reject: tuple[str, ...],
    screenshot_path: Path | None = None,
    startup_timeout_seconds: int = 45,
) -> ManagedWebSmokeResult:
    project_path = project_root / project
    if not (project_path / "package.json").exists():
        return ManagedWebSmokeResult(ok=False, message=f"missing package.json for web smoke: {project_path}", browser=None)
    url = f"http://localhost:{port}"
    process = subprocess.Popen(
        ("/bin/sh", "-lc", f"npm run web -- --port {port}"),
        cwd=project_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        if not _wait_for_url(url, startup_timeout_seconds):
            stdout, stderr = _communicate(process)
            return ManagedWebSmokeResult(
                ok=False,
                message=f"web app did not become ready at {url}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}",
                browser=None,
            )
        browser = run_browser_smoke(url, expect=expect, reject=reject, screenshot_path=screenshot_path)
        if not browser.ok:
            return ManagedWebSmokeResult(ok=False, message=browser.error, browser=browser)
        return ManagedWebSmokeResult(ok=True, message=f"web smoke passed: {url}", browser=browser)
    finally:
        _terminate_process_group(process)


def _wait_for_url(url: str, timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return True
        except URLError:
            time.sleep(0.5)
    return False


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            return


def _communicate(process: subprocess.Popen[str]) -> tuple[str, str]:
    try:
        stdout, stderr = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        return "", ""
    return stdout or "", stderr or ""
