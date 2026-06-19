from __future__ import annotations

import json
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    command: str
    ok: bool
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    duration_seconds: float


def run_acceptance_checks(
    checks: tuple[str, ...],
    *,
    project_root: Path,
    controller_root: Path | None = None,
    run_dir: Path,
    timeout_seconds: int = 120,
) -> tuple[AcceptanceResult, ...]:
    unique_checks = tuple(dict.fromkeys(checks))
    results: list[AcceptanceResult] = []
    reports_dir = run_dir / "acceptance"
    feedback_dir = run_dir / "feedback"
    reports_dir.mkdir(parents=True, exist_ok=True)
    feedback_dir.mkdir(parents=True, exist_ok=True)
    _clear_previous_acceptance_outputs(reports_dir, feedback_dir)
    command_root = controller_root if controller_root is not None else project_root
    for index, command in enumerate(unique_checks, start=1):
        started = time.time()
        stdout_path = reports_dir / f"{index:02d}.stdout.log"
        stderr_path = reports_dir / f"{index:02d}.stderr.log"
        try:
            controller_args = _controller_checker_args(command, project_root=project_root, controller_root=command_root)
            if controller_args is None:
                process = subprocess.run(
                    ("/bin/sh", "-lc", command),
                    cwd=project_root,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=timeout_seconds,
                )
            else:
                process = subprocess.run(
                    controller_args,
                    cwd=command_root,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=timeout_seconds,
                )
            stdout = process.stdout
            stderr = process.stderr
            exit_code = process.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = _decode_timeout_output(exc.stdout)
            stderr = _decode_timeout_output(exc.stderr) + f"\nTimed out after {timeout_seconds}s"
            exit_code = 124
        duration = time.time() - started
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        result = AcceptanceResult(
            command=command,
            ok=exit_code == 0,
            exit_code=exit_code,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            duration_seconds=duration,
        )
        results.append(result)
        if not result.ok:
            _write_feedback(feedback_dir, index, result)
            break
    return tuple(results)


def acceptance_passed(results: tuple[AcceptanceResult, ...], expected_checks: tuple[str, ...]) -> bool:
    return len(results) == len(tuple(dict.fromkeys(expected_checks))) and all(result.ok for result in results)


def _controller_checker_args(command: str, *, project_root: Path, controller_root: Path) -> tuple[str, ...] | None:
    try:
        args = shlex.split(command)
    except ValueError:
        return None
    if len(args) < 2 or Path(args[1]).parent.as_posix() != "scripts":
        return None
    script_name = Path(args[1]).name
    if not script_name.startswith("blackcow_") or not script_name.endswith(".py"):
        return None
    rewritten = list(args)
    rewritten[1] = str(controller_root / args[1])
    for index, arg in enumerate(rewritten[:-1]):
        if arg != "--project":
            continue
        project_arg = Path(rewritten[index + 1])
        if not project_arg.is_absolute():
            rewritten[index + 1] = str(project_root / project_arg)
    return tuple(rewritten)


def _write_feedback(feedback_dir: Path, index: int, result: AcceptanceResult) -> None:
    payload = {
        "command": result.command,
        "exit_code": result.exit_code,
        "stdout": str(result.stdout_path),
        "stderr": str(result.stderr_path),
        "duration_seconds": result.duration_seconds,
    }
    (feedback_dir / f"acceptance-{index:02d}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _clear_previous_acceptance_outputs(reports_dir: Path, feedback_dir: Path) -> None:
    for pattern in ("*.stdout.log", "*.stderr.log"):
        for path in reports_dir.glob(pattern):
            path.unlink()
    for path in feedback_dir.glob("acceptance-*.json"):
        path.unlink()


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
