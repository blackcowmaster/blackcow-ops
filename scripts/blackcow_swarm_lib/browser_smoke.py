from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "chromium",
    "chromium-browser",
)


@dataclass(frozen=True, slots=True)
class BrowserSmokeResult:
    ok: bool
    dom: str
    error: str


def run_browser_smoke(
    url: str,
    *,
    expect: tuple[str, ...],
    reject: tuple[str, ...],
    chrome_bin: str | None = None,
    screenshot_path: Path | None = None,
    timeout_seconds: int = 30,
) -> BrowserSmokeResult:
    executable = chrome_bin or find_chrome()
    if executable is None:
        return BrowserSmokeResult(ok=False, dom="", error="Chrome executable not found")
    if screenshot_path is not None:
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blackcow-browser-smoke-") as profile_dir:
        command = [
            executable,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-background-networking",
            f"--user-data-dir={profile_dir}",
            "--virtual-time-budget=5000",
            "--dump-dom",
        ]
        if screenshot_path is not None:
            command.append(f"--screenshot={screenshot_path}")
        command.append(url)
        try:
            result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            partial_dom = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
            return BrowserSmokeResult(ok=False, dom=partial_dom, error=f"Chrome timed out after {timeout_seconds}s")
    if result.returncode != 0:
        return BrowserSmokeResult(ok=False, dom=result.stdout, error=result.stderr.strip())
    missing = tuple(value for value in expect if value not in result.stdout)
    rejected = tuple(value for value in reject if value in result.stdout)
    if missing:
        return BrowserSmokeResult(ok=False, dom=result.stdout, error="Missing expected text: " + ", ".join(missing))
    if rejected:
        return BrowserSmokeResult(ok=False, dom=result.stdout, error="Rejected text present: " + ", ".join(rejected))
    if screenshot_path is not None and (not screenshot_path.exists() or screenshot_path.stat().st_size == 0):
        return BrowserSmokeResult(ok=False, dom=result.stdout, error=f"Screenshot missing or empty: {screenshot_path}")
    return BrowserSmokeResult(ok=True, dom=result.stdout, error="")


def find_chrome() -> str | None:
    env_path = os.environ.get("CHROME_BIN")
    if env_path:
        return env_path
    for candidate in DEFAULT_CHROME_PATHS:
        if "/" in candidate:
            if Path(candidate).exists():
                return candidate
        elif _which(candidate) is not None:
            return candidate
    return None


def _which(executable: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        path = Path(directory) / executable
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    return None
