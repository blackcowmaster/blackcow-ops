from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue


@dataclass(frozen=True, slots=True)
class SpeedGateResult:
    ok: bool
    message: str


def run_speed_gate(run_dir: Path, *, min_speedup: float) -> SpeedGateResult:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return SpeedGateResult(ok=False, message=f"missing state.json: {state_path}")
    payload: JsonValue = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return SpeedGateResult(ok=False, message="state.json must be an object")
    workers = payload.get("workers")
    if not isinstance(workers, dict) or not workers:
        return SpeedGateResult(ok=False, message="missing worker timing evidence")
    durations: list[float] = []
    starts: list[float] = []
    finishes: list[float] = []
    for worker in workers.values():
        if not isinstance(worker, dict):
            return SpeedGateResult(ok=False, message="worker timing evidence is malformed")
        started_at = worker.get("started_at")
        finished_at = worker.get("finished_at")
        if not isinstance(started_at, int | float) or not isinstance(finished_at, int | float):
            return SpeedGateResult(ok=False, message="missing worker timing evidence")
        durations.append(float(finished_at) - float(started_at))
        starts.append(float(started_at))
        finishes.append(float(finished_at))
    serial_seconds = sum(durations)
    wall_seconds = max(finishes) - min(starts)
    if wall_seconds <= 0:
        return SpeedGateResult(ok=False, message="invalid worker timing evidence")
    speedup = serial_seconds / wall_seconds
    if speedup < min_speedup:
        return SpeedGateResult(ok=False, message=f"swarm speedup {speedup:.2f} below required {min_speedup:.2f}")
    return SpeedGateResult(ok=True, message=f"swarm speedup {speedup:.2f}")
