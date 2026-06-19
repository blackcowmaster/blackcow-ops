from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DESIGN_SOURCE_NAMES = ("DESIGN.md", "design.md", "getdesign.md", "getdesign.kr")


@dataclass(frozen=True, slots=True)
class GateResult:
    ok: bool
    message: str


def run_design_gate(project_root: Path, project: str) -> GateResult:
    project_path = project_root / project
    candidates = tuple(project_path / name for name in DESIGN_SOURCE_NAMES) + tuple(
        project_root / name for name in DESIGN_SOURCE_NAMES
    )
    for candidate in candidates:
        if candidate.exists() and candidate.read_text(encoding="utf-8").strip():
            return GateResult(ok=True, message=f"design source found: {candidate}")
    expected = ", ".join(DESIGN_SOURCE_NAMES)
    return GateResult(ok=False, message=f"missing design source; expected one of: {expected}")
