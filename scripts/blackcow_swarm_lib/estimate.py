from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .config import INTENSITIES, MODES, POLICIES, SwarmConfig


class EstimatePayload(TypedDict):
    task: str
    requested_policy: str
    requested_mode: str
    requested_intensity: str
    recommended_mode: str
    recommended_intensity: str
    recommended_workers: int
    estimated_serial_minutes: int
    expected_speedup: float
    requires_approval: bool
    writer_swarm_allowed: bool
    risk_flags: list[str]
    rationale: list[str]


@dataclass(frozen=True, slots=True)
class Estimate:
    task: str
    requested_policy: str
    requested_mode: str
    requested_intensity: str
    recommended_mode: str
    recommended_intensity: str
    recommended_workers: int
    estimated_serial_minutes: int
    expected_speedup: float
    requires_approval: bool
    writer_swarm_allowed: bool
    risk_flags: tuple[str, ...]
    rationale: tuple[str, ...]

    def to_json(self) -> EstimatePayload:
        return {
            "task": self.task,
            "requested_policy": self.requested_policy,
            "requested_mode": self.requested_mode,
            "requested_intensity": self.requested_intensity,
            "recommended_mode": self.recommended_mode,
            "recommended_intensity": self.recommended_intensity,
            "recommended_workers": self.recommended_workers,
            "estimated_serial_minutes": self.estimated_serial_minutes,
            "expected_speedup": self.expected_speedup,
            "requires_approval": self.requires_approval,
            "writer_swarm_allowed": self.writer_swarm_allowed,
            "risk_flags": list(self.risk_flags),
            "rationale": list(self.rationale),
        }


def estimate_task(
    task: str,
    config: SwarmConfig,
    *,
    requested_intensity: str,
    requested_policy: str,
    requested_mode: str,
    max_workers: int | None = None,
) -> Estimate:
    _validate_choice(requested_intensity, INTENSITIES, "intensity")
    _validate_choice(requested_policy, POLICIES, "policy")
    _validate_choice(requested_mode, MODES, "mode")
    text = task.strip()
    if not text:
        raise ValueError("task must not be empty")

    small_mobile_app = _is_small_single_purpose_mobile_app(text.lower())
    serial_minutes = _estimate_serial_minutes(text)
    needs_writer = _needs_writer(text)
    risk_flags = _risk_flags(text, config)
    tiny_task = serial_minutes <= 8
    recommended_mode = _recommended_mode(requested_mode, tiny_task, small_mobile_app, needs_writer, bool(risk_flags))
    recommended_intensity = _recommended_intensity(requested_intensity, serial_minutes, tiny_task, small_mobile_app)
    profile = config.intensity[recommended_intensity]
    worker_limit = max_workers if max_workers is not None else profile.max_total_workers
    recommended_workers = _recommended_workers(serial_minutes, recommended_mode, worker_limit, small_mobile_app)
    requires_approval = requested_policy == "auto" and needs_writer and bool(risk_flags)
    writer_swarm_allowed = (
        needs_writer
        and recommended_mode != "serial"
        and requested_policy in ("auto", "force")
        and not requires_approval
    )
    expected_speedup = _expected_speedup(recommended_workers, recommended_mode, small_mobile_app)
    rationale = _rationale(serial_minutes, tiny_task, small_mobile_app, needs_writer, risk_flags, recommended_mode)
    return Estimate(
        task=text,
        requested_policy=requested_policy,
        requested_mode=requested_mode,
        requested_intensity=requested_intensity,
        recommended_mode=recommended_mode,
        recommended_intensity=recommended_intensity,
        recommended_workers=recommended_workers,
        estimated_serial_minutes=serial_minutes,
        expected_speedup=expected_speedup,
        requires_approval=requires_approval,
        writer_swarm_allowed=writer_swarm_allowed,
        risk_flags=tuple(risk_flags),
        rationale=tuple(rationale),
    )


def _estimate_serial_minutes(task: str) -> int:
    lower = task.lower()
    words = [word for word in lower.replace("/", " ").replace("-", " ").split() if word]
    minutes = max(2, len(words) * 2)
    if _contains_any(lower, ("implement", "build", "create", "add")):
        minutes += 8
    if _contains_any(lower, ("flow", "feature", "integration", "orchestration", "scheduler")):
        minutes += 6
    if _contains_any(lower, ("test", "qa", "review", "schema", "config")):
        minutes += 4
    if _contains_any(lower, ("auth", "permission", "billing", "payment", "migration", "deploy")):
        minutes += 10
    if _contains_any(lower, ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "cargo.lock")):
        minutes += 5
    if _is_small_single_purpose_mobile_app(lower):
        minutes = min(minutes, 12)
    return minutes


def _is_small_single_purpose_mobile_app(text: str) -> bool:
    if not _contains_any(text, ("react native", "react-native", "expo")) or "app" not in text:
        return False
    if _contains_any(text, ("backend", "auth", "payment", "billing", "migration", "cloud sync", "push notification")):
        return False
    if _contains_any(text, ("water", "hydration", "pomodoro", "timer", "check-in", "check app", "tracker")):
        return True
    return False


def _needs_writer(task: str) -> bool:
    return _contains_any(
        task.lower(),
        (
            "implement",
            "change",
            "add",
            "modify",
            "fix",
            "create",
            "update",
            "refactor",
            "delete",
            "write",
            "edit",
            "rename",
        ),
    )


def _risk_flags(task: str, config: SwarmConfig) -> list[str]:
    lower = task.lower()
    flags: list[str] = []
    for pattern in config.risky_writer_patterns:
        if pattern.lower() in lower:
            flags.append(pattern)
    for path in config.single_writer_paths:
        if path.lower() in lower and path not in flags:
            flags.append(path)
    return flags


def _recommended_mode(requested_mode: str, tiny_task: bool, small_mobile_app: bool, needs_writer: bool, risky: bool) -> str:
    if tiny_task:
        return "serial"
    if requested_mode != "adaptive":
        return requested_mode
    if small_mobile_app and needs_writer:
        return "coder"
    if risky:
        return "review"
    if needs_writer:
        return "full"
    return "qa"


def _recommended_intensity(requested_intensity: str, serial_minutes: int, tiny_task: bool, small_mobile_app: bool) -> str:
    if tiny_task or small_mobile_app:
        return "normal"
    if serial_minutes >= 45:
        return "max"
    if requested_intensity in ("high", "max") or serial_minutes >= 18:
        return "high"
    return "normal"


def _recommended_workers(serial_minutes: int, mode: str, worker_limit: int, small_mobile_app: bool) -> int:
    if mode == "serial":
        return 1
    if small_mobile_app:
        return min(worker_limit, 3)
    scaled = max(2, min(worker_limit, serial_minutes // 6 + 2))
    return max(1, scaled)


def _expected_speedup(workers: int, mode: str, small_mobile_app: bool = False) -> float:
    if mode == "serial" or small_mobile_app:
        return 1.0
    return round(min(4.0, 1.0 + workers * 0.18), 2)


def _rationale(
    serial_minutes: int,
    tiny_task: bool,
    small_mobile_app: bool,
    needs_writer: bool,
    risk_flags: list[str],
    recommended_mode: str,
) -> list[str]:
    lines = [f"estimated serial work: {serial_minutes} minutes", f"recommended mode: {recommended_mode}"]
    if tiny_task:
        lines.append("task is small enough that swarm overhead is unlikely to pay off")
    if small_mobile_app:
        lines.append("small single-purpose mobile app: use micro swarm for evidence, not max fanout")
    if needs_writer:
        lines.append("task appears to require file modifications")
    if risk_flags:
        lines.append("risky writer surface detected: " + ", ".join(risk_flags))
    return lines


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _validate_choice(value: str, allowed: tuple[str, ...], field: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(allowed)}")
