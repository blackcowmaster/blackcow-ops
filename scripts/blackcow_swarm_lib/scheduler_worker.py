from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import assert_never

from .runner import WorkerTask
from .scheduler_types import ScheduledTask, ScheduleEvent, TaskInterval, TaskRun
from .skill_contract import build_worker_prompt
from .worktree import WorktreeError


def worker_task(task: ScheduledTask, repo_root: Path, run_dir: Path, workspace: Path) -> WorkerTask:
    worker_dir = writer_artifact_dir(workspace=workspace, run_dir=run_dir, replica_id=task.replica_id) if workspace != repo_root else (
        run_dir / "workers" / task.replica_id
    )
    worker_dir.mkdir(parents=True, exist_ok=True)
    prompt = worker_dir / "prompt.md"
    result = worker_dir / "result.json"
    prompt.write_text(
        build_worker_prompt(
            project_root=repo_root,
            run_dir=run_dir,
            skill=task.skill,
            base_prompt=task.prompt,
            task_id=task.task_id,
            replica_id=task.replica_id,
            result_json=result,
            acceptance_checks=task.acceptance_checks,
        )
        + "\n",
        encoding="utf-8",
    )
    return WorkerTask(
        task_id=task.task_id,
        replica_id=task.replica_id,
        skill=task.skill,
        prompt_file=prompt,
        result_json=result,
        workspace=workspace,
        read_only=task.read_only,
        timeout_seconds=task.timeout_seconds,
        missing_result_fatal=False,
    )


def writer_artifact_dir(*, workspace: Path, run_dir: Path, replica_id: str) -> Path:
    return workspace / ".omo" / "swarm" / "runs" / run_dir.name / "workers" / replica_id


def failed_writer_run(
    report_key: str,
    task: ScheduledTask,
    run_dir: Path,
    started_at: float,
    events: list[ScheduleEvent],
    phase: str,
    error: WorktreeError | subprocess.CalledProcessError,
) -> TaskRun:
    finished_at = time.time()
    _write_writer_failure_report(run_dir, task, phase, error)
    return TaskRun(
        report_key,
        "FAILED_RETRYABLE",
        TaskInterval(report_key, started_at, finished_at),
        tuple([*events, ScheduleEvent(f"WRITER_{phase.upper()}_FAILED", report_key), ScheduleEvent("FAILED_RETRYABLE", report_key)]),
    )


def copy_to_audit_dir(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination, ignore_errors=True)
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)


def _write_writer_failure_report(
    run_dir: Path,
    task: ScheduledTask,
    phase: str,
    error: WorktreeError | subprocess.CalledProcessError,
) -> None:
    report_path = run_dir / "reports" / f"writer-{phase}-failure-{task.replica_id}.json"
    payload = {
        "task_id": task.task_id,
        "replica_id": task.replica_id,
        "phase": phase,
        "status": "FAILED_RETRYABLE",
        "message": str(error),
    }
    match error:
        case subprocess.CalledProcessError() as called:
            payload.update(
                {
                    "cmd": called.cmd,
                    "returncode": called.returncode,
                    "stderr": _process_stream_text(called.stderr),
                    "stdout": _process_stream_text(called.stdout),
                }
            )
        case WorktreeError():
            pass
        case unreachable:
            assert_never(unreachable)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _process_stream_text(stream: bytes | str | None) -> str:
    match stream:
        case None:
            return ""
        case bytes() as data:
            return data.decode("utf-8", errors="replace")
        case str() as text:
            return text
        case unreachable:
            assert_never(unreachable)
