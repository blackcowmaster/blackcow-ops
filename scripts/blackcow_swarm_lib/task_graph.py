from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from .acceptance import AcceptancePlan, infer_acceptance_checks
from .config import IntensityProfile, RuntimeOptions, SwarmConfig
from .estimate import Estimate, EstimatePayload, estimate_task
from .schema import validate_estimate, validate_task_graph
from .shared_context import build_shared_context


RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}")


class TaskPayload(TypedDict):
    id: str
    kind: str
    title: str
    skill: str
    prompt: str
    depends_on: list[str]
    read_only: bool
    writes: list[str]
    write_scope: list[str]
    acceptance_checks: list[str]
    replicas: int
    max_replicas: int
    timeout_minutes: int


class TaskGraphPayload(TypedDict):
    run_id: str
    task: str
    mode: str
    intensity: str
    policy: str
    requires_approval: bool
    worker_swarm_allowed: bool
    tasks: list[TaskPayload]


@dataclass(frozen=True, slots=True)
class PlanArtifacts:
    run_id: str
    run_dir: Path
    estimate_path: Path
    task_graph_path: Path
    shared_context_path: Path


def create_dry_run_plan(
    task: str,
    config: SwarmConfig,
    options: RuntimeOptions,
    *,
    run_id: str | None,
    project_root: Path,
    approve_dangerous: bool,
) -> PlanArtifacts:
    safe_run_id = _safe_run_id(run_id)
    run_dir = project_root / ".omo" / "swarm" / "runs" / safe_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    estimate = estimate_task(
        task,
        config,
        requested_intensity=options.intensity,
        requested_policy=options.policy,
        requested_mode=options.mode,
        max_workers=options.max_workers,
    )
    estimate_path = run_dir / "estimate.json"
    task_graph_path = run_dir / "task_graph.json"
    shared_context_path = run_dir / "shared_context.md"
    acceptance = infer_acceptance_checks(task, project_root)
    _write_estimate(estimate_path, estimate.to_json())
    validate_estimate(json.loads(estimate_path.read_text(encoding="utf-8")))
    acceptance_with_run_gates = AcceptancePlan(
        checks=acceptance.checks + _run_level_checks(safe_run_id, acceptance, estimate.expected_speedup),
        project_path=acceptance.project_path,
        native_platform=acceptance.native_platform,
        visual_review_required=acceptance.visual_review_required,
        expected_text=acceptance.expected_text,
    )
    shared_context_path.write_text(build_shared_context(task, estimate, acceptance_with_run_gates), encoding="utf-8")
    graph = _task_graph(safe_run_id, task, estimate, config, options, approve_dangerous, acceptance_with_run_gates)
    validate_task_graph(graph)
    _write_task_graph(task_graph_path, graph)
    return PlanArtifacts(
        run_id=safe_run_id,
        run_dir=run_dir,
        estimate_path=estimate_path,
        task_graph_path=task_graph_path,
        shared_context_path=shared_context_path,
    )


def _task_graph(
    run_id: str,
    task: str,
    estimate: Estimate,
    config: SwarmConfig,
    options: RuntimeOptions,
    approve_dangerous: bool,
    acceptance: AcceptancePlan,
) -> TaskGraphPayload:
    profile = config.intensity[estimate.recommended_intensity]
    timeout_minutes = max(1, profile.timeout_seconds // 60)
    right_sized_small_app = _right_sized_small_app(task, estimate)
    micro_small_app = right_sized_small_app and estimate.estimated_serial_minutes <= 12
    readonly_replicas = 1 if right_sized_small_app else min(profile.max_readonly_workers, max(1, estimate.recommended_workers))
    blocked_writer = estimate.requires_approval and not approve_dangerous
    writer_replicas = _safe_writer_replicas(profile, options, estimate, blocked_writer, right_sized_small_app, micro_small_app)
    tasks = [
        _task("discovery-1", "discovery", "Discover implementation surface", "blackcow-plan", task, [], True, [], min(3, readonly_replicas), timeout_minutes, acceptance.checks),
    ]
    if blocked_writer:
        tasks.extend(
            [
                _task("review-1", "review", "Review dangerous write surface", "blackcow-qa", task, ["discovery-1"], True, [], 1, timeout_minutes, acceptance.checks),
                _task("qa-1", "qa", "Validate approval gate", "blackcow-qa", task, ["discovery-1"], True, [], 1, timeout_minutes, acceptance.checks),
                _task("judge-1", "judge", "Judge blocked swarm plan", "blackcow-qa", task, ["review-1", "qa-1"], True, [], 1, timeout_minutes, acceptance.checks),
            ]
        )
    elif micro_small_app:
        tasks.extend(
            [
                _task("coder-1", "coder", "Implement candidate patch", "blackcow-loop", task, ["discovery-1"], False, ["**/*"], writer_replicas, timeout_minutes, acceptance.checks),
                _task("qa-1", "qa", "Run focused quality checks", "blackcow-qa", task, ["coder-1"], True, [], 1, timeout_minutes, acceptance.checks),
                _task("judge-1", "judge", "Select safest passing candidate", "blackcow-qa", task, ["coder-1", "qa-1"], True, [], 1, timeout_minutes, acceptance.checks),
            ]
        )
    else:
        tasks.extend(
            [
                _task("coder-1", "coder", "Implement candidate patch", "blackcow-loop", task, ["discovery-1"], False, ["**/*"], writer_replicas, timeout_minutes, acceptance.checks),
                _task("review-1", "review", "Review candidate patch", "blackcow-qa", task, ["coder-1"], True, [], min(2, readonly_replicas), timeout_minutes, acceptance.checks),
                _task("qa-1", "qa", "Run focused quality checks", "blackcow-qa", task, ["coder-1"], True, [], min(2, readonly_replicas), timeout_minutes, acceptance.checks),
                _task("judge-1", "judge", "Select safest passing candidate", "blackcow-qa", task, ["coder-1", "review-1", "qa-1"], True, [], 1, timeout_minutes, acceptance.checks),
            ]
        )
    return {
        "run_id": run_id,
        "task": task,
        "mode": estimate.recommended_mode,
        "intensity": estimate.recommended_intensity,
        "policy": options.policy,
        "requires_approval": estimate.requires_approval,
        "worker_swarm_allowed": estimate.writer_swarm_allowed and not blocked_writer,
        "tasks": tasks,
    }


def _task(
    task_id: str,
    kind: str,
    title: str,
    skill: str,
    user_task: str,
    depends_on: list[str],
    read_only: bool,
    writes: list[str],
    replicas: int,
    timeout_minutes: int,
    acceptance_checks: tuple[str, ...],
) -> TaskPayload:
    return {
        "id": task_id,
        "kind": kind,
        "title": title,
        "skill": skill,
        "prompt": f"{title}: {user_task}",
        "depends_on": depends_on,
        "read_only": read_only,
        "writes": writes,
        "write_scope": writes,
        "acceptance_checks": list(acceptance_checks),
        "replicas": replicas,
        "max_replicas": replicas,
        "timeout_minutes": timeout_minutes,
    }


def _safe_writer_replicas(
    profile: IntensityProfile,
    options: RuntimeOptions,
    estimate: Estimate,
    blocked_writer: bool,
    right_sized_small_app: bool = False,
    micro_small_app: bool = False,
) -> int:
    if blocked_writer or not estimate.writer_swarm_allowed:
        return 1
    worker_limit = options.max_workers if options.max_workers is not None else profile.max_total_workers
    if micro_small_app:
        return 1
    if right_sized_small_app:
        return min(profile.max_writer_workers, worker_limit, 2)
    return min(profile.max_writer_workers, worker_limit, max(2, estimate.recommended_workers))


def _right_sized_small_app(task: str, estimate: Estimate) -> bool:
    lower = task.lower()
    if estimate.estimated_serial_minutes > 35:
        return False
    if not ("app" in lower and ("expo" in lower or "react native" in lower or "react-native" in lower)):
        return False
    return not any(word in lower for word in ("backend", "auth", "payment", "billing", "migration", "push notification"))


def _safe_run_id(run_id: str | None) -> str:
    candidate = run_id if run_id is not None else "swarm-" + datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    if candidate in (".", "..") or ".." in candidate or RUN_ID_PATTERN.fullmatch(candidate) is None:
        raise ValueError(f"invalid run-id: {candidate}")
    return candidate


def _run_level_checks(run_id: str, acceptance: AcceptancePlan, expected_speedup: float) -> tuple[str, ...]:
    if acceptance.project_path is None:
        return ()
    checks: list[str] = []
    if acceptance.native_platform is not None and acceptance.runtime_visual_required:
        screenshot_path = f".omo/swarm/runs/{run_id}/screenshots/{acceptance.native_platform}.png"
        checks.append(
            "python3 scripts/blackcow_expo_native_smoke.py "
            f"--project {acceptance.project_path} --platform {acceptance.native_platform} "
            f"--screenshot {screenshot_path} --review-output .omo/swarm/runs/{run_id}/visual-review.md"
            f"{_expect_args(acceptance.expected_text)}"
        )
    elif acceptance.visual_review_required:
        web_check = _web_smoke_check(acceptance.checks)
        if web_check is not None:
            screenshot_path = f".omo/swarm/runs/{run_id}/screenshots/web.png"
            checks.append(f"{web_check} --screenshot {screenshot_path}")
            checks.append(
                "python3 scripts/blackcow_visual_review.py "
                f"--image {screenshot_path} --output .omo/swarm/runs/{run_id}/visual-review.md"
                f"{_expect_args(acceptance.expected_text)}"
            )
    min_speedup = 1.0 if expected_speedup <= 1.0 else 1.1
    checks.append(f"python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/{run_id} --min-speedup {min_speedup:.1f}")
    return tuple(checks)


def _web_smoke_check(checks: tuple[str, ...]) -> str | None:
    for check in checks:
        if "scripts/blackcow_web_smoke.py" in check:
            return check
    return None


def _expect_args(expected_text: tuple[str, ...]) -> str:
    if not expected_text:
        return ""
    return "".join(f" --expect {shlex.quote(value)}" for value in expected_text)


def _write_task_graph(path: Path, payload: TaskGraphPayload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_estimate(path: Path, payload: EstimatePayload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
