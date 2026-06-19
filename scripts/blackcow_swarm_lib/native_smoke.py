from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class NativeSmokeResult:
    ok: bool
    message: str


def run_native_capability_gate(project: str, platform: str, *, xcrun_bin: str = "xcrun") -> NativeSmokeResult:
    return run_native_smoke(project, platform, xcrun_bin=xcrun_bin)


def run_native_smoke(
    project: str,
    platform: str,
    *,
    xcrun_bin: str = "xcrun",
    screenshot_path: Path | None = None,
) -> NativeSmokeResult:
    if platform != "ios":
        return NativeSmokeResult(ok=False, message=f"unsupported native platform: {platform}")
    try:
        result = subprocess.run(
            (xcrun_bin, "simctl", "list", "devices", "available"),
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except FileNotFoundError:
        return NativeSmokeResult(ok=False, message=f"xcrun not found: {xcrun_bin}")
    except subprocess.TimeoutExpired:
        return NativeSmokeResult(ok=False, message=f"xcrun simulator check timed out for {project}")
    if result.returncode != 0:
        return NativeSmokeResult(ok=False, message=f"xcrun simulator check failed for {project}: {result.stderr.strip()}")
    if "Booted" not in result.stdout:
        return NativeSmokeResult(ok=False, message=f"no booted iOS simulator for {project}; native visual gate cannot pass")
    if screenshot_path is not None:
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            screenshot = subprocess.run(
                (xcrun_bin, "simctl", "io", "booted", "screenshot", str(screenshot_path)),
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
        except FileNotFoundError:
            return NativeSmokeResult(ok=False, message=f"xcrun not found: {xcrun_bin}")
        except subprocess.TimeoutExpired:
            return NativeSmokeResult(ok=False, message=f"iOS screenshot timed out for {project}")
        if screenshot.returncode != 0:
            return NativeSmokeResult(ok=False, message=f"iOS screenshot failed for {project}: {screenshot.stderr.strip()}")
        if not screenshot_path.exists() or screenshot_path.stat().st_size == 0:
            return NativeSmokeResult(ok=False, message=f"iOS screenshot missing or empty: {screenshot_path}")
        return NativeSmokeResult(ok=True, message=f"iOS screenshot captured for {project}: {screenshot_path}")
    return NativeSmokeResult(ok=True, message=f"booted iOS simulator available for {project}")
