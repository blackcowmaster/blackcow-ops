from __future__ import annotations

from pathlib import Path


FORBIDDEN_PROMPT_MARKERS = (
    "# BlackCow Skill-Backed Swarm Worker",
    "## Active Skill Source",
    "## Embedded Skill Source",
    "PRIVATE BLACKCOW",
    ".codex/attachments",
    ".codex/plugins/cache",
    ".agents/skills",
)


class ScratchExportSafetyError(ValueError):
    pass


def assert_external_safe_scratch_payload(
    prompt: str,
    *,
    scratch: Path,
    result_json: Path,
    project_root: Path,
) -> None:
    resolved_project = _resolve(project_root)
    resolved_scratch = _resolve(scratch)
    resolved_result = _resolve(result_json)
    if _is_relative_to(resolved_scratch, resolved_project):
        raise ScratchExportSafetyError("scratch workspace must be outside project root")
    if not _is_relative_to(resolved_result, resolved_scratch):
        raise ScratchExportSafetyError("scratch result JSON must stay inside scratch workspace")
    for marker in _private_prompt_markers(resolved_project):
        if marker and marker in prompt:
            raise ScratchExportSafetyError(f"scratch prompt contains private marker: {marker}")


def _private_prompt_markers(project_root: Path) -> tuple[str, ...]:
    home = Path.home()
    return (
        str(project_root),
        project_root.as_posix(),
        str(home / ".codex"),
        str(home / ".agents"),
        "/.codex/",
        "/.agents/",
        *FORBIDDEN_PROMPT_MARKERS,
    )


def _resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
