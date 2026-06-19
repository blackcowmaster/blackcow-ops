from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .design_gate import run_design_gate
from .expo_clean_gate import run_expo_clean_gate


EXCLUDED_GENERATED_NAMES = frozenset(("node_modules", ".expo", ".next", ".turbo", "dist", "build", "coverage"))


@dataclass(frozen=True, slots=True)
class ScratchSalvageDecision:
    status: str
    summary: str | None


def decide_scratch_salvage(
    scratch: Path,
    *,
    outcome_status: str,
    outcome_events: tuple[str, ...],
) -> ScratchSalvageDecision:
    if outcome_status == "SUCCEEDED" and "timeout" not in outcome_events:
        return ScratchSalvageDecision(status="SUCCEEDED", summary=None)
    gate_message = _salvage_gate_message(scratch)
    if gate_message:
        return ScratchSalvageDecision(
            status="FAILED_RETRYABLE",
            summary=f"controller salvaged incomplete scratch files after worker status {outcome_status}: {gate_message}",
        )
    return ScratchSalvageDecision(
        status="SUCCEEDED",
        summary="controller accepted complete scratch candidate without worker result JSON; controller acceptance gates must decide final status",
    )


def _salvage_gate_message(scratch: Path) -> str:
    project = _project_path(scratch)
    if project is None:
        return "missing package.json in generated project"
    design = run_design_gate(project.parent, project.name)
    if not design.ok:
        return design.message
    clean = run_expo_clean_gate(project.parent, project.name)
    if not clean.ok:
        return clean.message
    if not _has_native_entry(project):
        return "missing native entry point; expected App.tsx or app/_layout.tsx"
    return ""


def _project_path(scratch: Path) -> Path | None:
    packages = sorted(
        path.parent
        for path in scratch.rglob("package.json")
        if not _is_ignored_generated_path(path.relative_to(scratch))
    )
    return packages[0] if packages else None


def _has_native_entry(project: Path) -> bool:
    if (project / "App.tsx").exists() or (project / "app" / "_layout.tsx").exists():
        return True
    return any(path.suffix == ".tsx" for path in (project / "src").rglob("*") if path.is_file())


def _is_ignored_generated_path(path: Path) -> bool:
    if path.parts[0].startswith("."):
        return True
    return any(part in EXCLUDED_GENERATED_NAMES for part in path.parts)
