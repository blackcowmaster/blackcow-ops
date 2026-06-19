from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

from .config import RunnerConfig
from .runner import MockBehavior, MockRunner, ReasonixRunner, RunnerOutcome, WorkerTask
from .schema import SchemaError, validate_result
from .scratch_prompt import build_scratch_worker_prompt
from .scratch_salvage import ScratchSalvageDecision, decide_scratch_salvage
from .scratch_safety import assert_external_safe_scratch_payload


EXCLUDED_GENERATED_NAMES = frozenset(("node_modules", ".expo", ".next", ".turbo", "dist", "build", "coverage"))
SCRATCH_TIMEOUT_SECONDS = 90
INNER_REASONIX_TIMEOUT_SECONDS = max(1, SCRATCH_TIMEOUT_SECONDS - 5)
ENTRYPOINT_REPAIR_TIMEOUT_SECONDS = 45
MISSING_NATIVE_ENTRYPOINT = "missing native entry point"
TSCONFIG_DEPRECATION = "tsconfig compilerOptions.baseUrl triggers TypeScript 6 deprecation errors"
FOCUSED_REPAIR_LIMIT = 3


class ScratchReasonixRunner:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.runner = ReasonixRunner(
            RunnerConfig(
                runner_type="reasonix",
                command_template=(
                    sys.executable,
                    str(project_root / "scripts" / "blackcow_reasonix_acp_worker.py"),
                    "--skill",
                    "{skill}",
                    "--prompt-file",
                    "{prompt_file}",
                    "--result-json",
                    "{result_json}",
                    "--workspace",
                    "{workspace}",
                    "--run-id",
                    "{run_id}",
                    "--task-id",
                    "{task_id}",
                    "--replica-id",
                    "{replica_id}",
                    "--read-only",
                    "{read_only}",
                    "--timeout-seconds",
                    str(INNER_REASONIX_TIMEOUT_SECONDS),
                ),
                cwd_mode="task_workspace",
                require_json_result=True,
            )
        )

    def run(self, task: WorkerTask) -> RunnerOutcome:
        if task.read_only:
            return MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.01)).run(task)
        _clear_previous_result(task.result_json)
        scratch = _scratch_workspace(task)
        if scratch.exists():
            shutil.rmtree(scratch)
        control_dir = scratch / ".blackcow"
        control_dir.mkdir(parents=True)
        scratch_prompt = control_dir / "prompt.md"
        scratch_result = control_dir / "result.json"
        prompt_text = build_scratch_worker_prompt(
            task.prompt_file.read_text(encoding="utf-8"),
            result_json=scratch_result,
            task_id=task.task_id,
            replica_id=task.replica_id,
        )
        assert_external_safe_scratch_payload(
            prompt_text,
            scratch=scratch,
            result_json=scratch_result,
            project_root=self.project_root,
        )
        scratch_prompt.write_text(prompt_text + "\n", encoding="utf-8")
        scratch_task = WorkerTask(
            task_id=task.task_id,
            replica_id=task.replica_id,
            skill=task.skill,
            read_only=False,
            prompt_file=scratch_prompt,
            result_json=scratch_result,
            workspace=scratch,
            timeout_seconds=min(task.timeout_seconds, SCRATCH_TIMEOUT_SECONDS),
            missing_result_fatal=task.missing_result_fatal,
        )
        outcome = self.runner.run(scratch_task)
        outcome = self._run_focused_repairs(
            original_task=task,
            scratch=scratch,
            control_dir=control_dir,
            scratch_result=scratch_result,
            outcome=outcome,
        )
        copy_generated_files(scratch, task.workspace)
        _copy_result(scratch_result, task.result_json, outcome.started_at, outcome.finished_at)
        salvage_decision = decide_scratch_salvage(
            scratch,
            outcome_status=outcome.status,
            outcome_events=outcome.events,
        )
        salvaged = write_salvaged_result_if_needed(
            task.result_json,
            scratch=scratch,
            task=task,
            started_at=outcome.started_at,
            finished_at=outcome.finished_at,
            status=salvage_decision.status,
            summary=salvage_decision.summary,
        )
        status = _result_status(task.result_json, fallback=outcome.status)
        return RunnerOutcome(
            status=status,
            result_path=task.result_json,
            command=outcome.command,
            started_at=outcome.started_at,
            finished_at=outcome.finished_at,
            process=outcome.process,
            events=(*outcome.events, "scratch_workspace", *(("scratch_salvaged_missing_result",) if salvaged else ())),
        )

    def _run_focused_repairs(
        self,
        *,
        original_task: WorkerTask,
        scratch: Path,
        control_dir: Path,
        scratch_result: Path,
        outcome: RunnerOutcome,
    ) -> RunnerOutcome:
        attempted: set[str] = set()
        current = outcome
        for _ in range(FOCUSED_REPAIR_LIMIT):
            decision = decide_scratch_salvage(
                scratch,
                outcome_status=current.status,
                outcome_events=current.events,
            )
            repair_kind = _focused_repair_kind(decision)
            if repair_kind is None or repair_kind in attempted:
                return current
            attempted.add(repair_kind)
            current = self._run_focused_repair(
                original_task=original_task,
                scratch=scratch,
                control_dir=control_dir,
                scratch_result=scratch_result,
                started_at=outcome.started_at,
                prior_events=current.events,
                repair_kind=repair_kind,
            )
        return current

    def _run_focused_repair(
        self,
        *,
        original_task: WorkerTask,
        scratch: Path,
        control_dir: Path,
        scratch_result: Path,
        started_at: float,
        prior_events: tuple[str, ...],
        repair_kind: str,
    ) -> RunnerOutcome:
        _clear_previous_result(scratch_result)
        prompt_file = control_dir / f"{repair_kind}-repair-prompt.md"
        prompt_text = _focused_repair_prompt(
            repair_kind=repair_kind,
            result_json=scratch_result,
            task_id=original_task.task_id,
            replica_id=original_task.replica_id,
        )
        assert_external_safe_scratch_payload(
            prompt_text,
            scratch=scratch,
            result_json=scratch_result,
            project_root=self.project_root,
        )
        prompt_file.write_text(prompt_text + "\n", encoding="utf-8")
        repair_task = WorkerTask(
            task_id=original_task.task_id,
            replica_id=original_task.replica_id,
            skill=original_task.skill,
            read_only=False,
            prompt_file=prompt_file,
            result_json=scratch_result,
            workspace=scratch,
            timeout_seconds=min(original_task.timeout_seconds, ENTRYPOINT_REPAIR_TIMEOUT_SECONDS),
            missing_result_fatal=original_task.missing_result_fatal,
        )
        repair_outcome = self.runner.run(repair_task)
        return RunnerOutcome(
            status=repair_outcome.status,
            result_path=repair_outcome.result_path,
            command=repair_outcome.command,
            started_at=started_at,
            finished_at=repair_outcome.finished_at,
            process=repair_outcome.process,
            events=(*prior_events, f"{repair_kind}_repair_started", *repair_outcome.events),
        )


def _scratch_workspace(task: WorkerTask) -> Path:
    return Path(tempfile.gettempdir()) / "blackcow-reasonix-scratch" / _run_id(task.result_json) / task.replica_id


def _focused_repair_kind(decision: ScratchSalvageDecision) -> str | None:
    if decision.status != "FAILED_RETRYABLE" or not decision.summary:
        return None
    if TSCONFIG_DEPRECATION in decision.summary:
        return "tsconfig"
    if MISSING_NATIVE_ENTRYPOINT in decision.summary:
        return "entrypoint"
    return None


def _focused_repair_prompt(*, repair_kind: str, result_json: Path, task_id: str, replica_id: str) -> str:
    if repair_kind == "tsconfig":
        return _tsconfig_repair_prompt(result_json=result_json, task_id=task_id, replica_id=replica_id)
    return _entrypoint_repair_prompt(result_json=result_json, task_id=task_id, replica_id=replica_id)


def _tsconfig_repair_prompt(*, result_json: Path, task_id: str, replica_id: str) -> str:
    return "\n".join(
        (
            "# External-Safe Scratch Tsconfig Repair",
            "",
            "You are in the same scratch workspace as the partial Expo/React Native app.",
            "The controller found exactly one blocking clean-scaffold issue: tsconfig compilerOptions.baseUrl triggers TypeScript 6 deprecation errors.",
            "Do not restart the project, do not remove existing source files, and do not install dependencies.",
            "Edit swarm-water-test/tsconfig.json to be no-install-clean.",
            "Remove compilerOptions.baseUrl. Remove compilerOptions.paths if it only mapped '*' to declaration stubs.",
            "Keep jsx, strict, noEmit, moduleResolution=bundler, include, and exclude usable for local typecheck/lint.",
            "Do not add ignoreDeprecations unless removing baseUrl is impossible.",
            "",
            "## Output Contract",
            f"Write the final worker result JSON to: {result_json}",
            f"The result must use task_id={task_id!r} and replica_id={replica_id!r}.",
            'Allowed status values are only: "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED", "TIMED_OUT".',
            "If you cannot complete the repair, still write FAILED_RETRYABLE result JSON with the exact blocker.",
        )
    )


def _entrypoint_repair_prompt(*, result_json: Path, task_id: str, replica_id: str) -> str:
    return "\n".join(
        (
            "# External-Safe Scratch Entrypoint Repair",
            "",
            "You are in the same scratch workspace as the partial Expo/React Native app.",
            "The controller found exactly one blocking structural issue: missing native entry point.",
            "Do not restart the project, do not remove existing files, and do not install dependencies.",
            "Create swarm-water-test/App.tsx unless swarm-water-test/app/_layout.tsx already exists.",
            "Use the existing DESIGN.md, package.json, tsconfig.json, declarations, and src/storage.ts when present.",
            "Keep the repair compact: a functional water check UI with bottom-tab-like native sections, daily progress, and storage wiring is enough.",
            "If imports need no-install TypeScript declarations, update the existing declarations file minimally.",
            "",
            "## Required Files Before Result",
            "- swarm-water-test/App.tsx or swarm-water-test/app/_layout.tsx",
            "- keep swarm-water-test/DESIGN.md",
            "- keep swarm-water-test/package.json",
            "- keep swarm-water-test/tsconfig.json",
            "",
            "## Output Contract",
            f"Write the final worker result JSON to: {result_json}",
            f"The result must use task_id={task_id!r} and replica_id={replica_id!r}.",
            'Allowed status values are only: "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED", "TIMED_OUT".',
            "If you cannot complete the repair, still write FAILED_RETRYABLE result JSON with the exact blocker.",
        )
    )


def _run_id(path: Path) -> str:
    parts = path.parts
    for index, part in enumerate(parts):
        if part == "runs" and index + 1 < len(parts):
            return parts[index + 1]
    return path.parent.name


def _clear_previous_result(result_json: Path) -> None:
    try:
        result_json.unlink()
    except FileNotFoundError:
        return


def copy_generated_files(source: Path, destination: Path) -> None:
    for child in source.iterdir():
        if child.name.startswith("."):
            continue
        target = destination / child.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if child.is_dir():
            shutil.copytree(child, target, ignore=_ignore_generated_artifacts)
        else:
            shutil.copy2(child, target)


def _ignore_generated_artifacts(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDED_GENERATED_NAMES}


def write_salvaged_result_if_needed(
    result_json: Path,
    *,
    scratch: Path,
    task: WorkerTask,
    started_at: float,
    finished_at: float,
    status: str = "SUCCEEDED",
    summary: str | None = None,
) -> bool:
    if result_json.exists():
        return False
    generated_files = _generated_files(scratch)
    if not generated_files:
        return False
    result_json.parent.mkdir(parents=True, exist_ok=True)
    duration = finished_at - started_at
    payload = {
        "task_id": task.task_id,
        "replica_id": task.replica_id,
        "status": status,
        "summary": summary or "controller salvaged generated scratch files because Reasonix omitted result JSON; local acceptance gates must decide final status",
        "artifacts": generated_files,
        "changed_files": generated_files,
        "patch_path": None,
        "score": {"overall": 50, "correctness": 50, "safety": 70, "tests": 0},
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
    }
    result_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def _generated_files(scratch: Path) -> list[str]:
    paths: list[str] = []
    for path in sorted(scratch.rglob("*")):
        if not path.is_file() or _is_ignored_generated_path(path.relative_to(scratch)):
            continue
        paths.append(path.relative_to(scratch).as_posix())
    return paths


def _is_ignored_generated_path(path: Path) -> bool:
    if path.parts[0].startswith("."):
        return True
    return any(part in EXCLUDED_GENERATED_NAMES for part in path.parts)


def _copy_result(source: Path, destination: Path, started_at: float, finished_at: float) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload["started_at"] = started_at
        payload["finished_at"] = finished_at
        payload["duration_seconds"] = finished_at - started_at
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _result_status(path: Path, *, fallback: str) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validate_result(payload)
    except (FileNotFoundError, json.JSONDecodeError, SchemaError):
        return fallback if fallback != "SUCCEEDED" else "FAILED_RETRYABLE"
    status = payload["status"]
    return status if isinstance(status, str) else "FAILED_RETRYABLE"
