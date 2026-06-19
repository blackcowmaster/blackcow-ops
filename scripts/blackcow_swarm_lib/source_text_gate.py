from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


TEXT_SUFFIXES: Final = frozenset({".js", ".jsx", ".json", ".md", ".ts", ".tsx"})
TEXT_FILENAMES: Final = frozenset({"App", "app.config"})
SKIP_DIRS: Final = frozenset({".git", ".expo", ".next", "build", "dist", "node_modules"})


@dataclass(frozen=True, slots=True)
class SourceTextGateResult:
    ok: bool
    message: str


def run_source_text_gate(project_root: Path, project: str, expect: tuple[str, ...]) -> SourceTextGateResult:
    project_path = project_root / project
    if not project_path.exists():
        return SourceTextGateResult(ok=False, message=f"missing project for source text gate: {project_path}")
    missing = tuple(value for value in expect if not _project_contains(project_path, value))
    if missing:
        return SourceTextGateResult(ok=False, message=f"missing expected source text for {project}: {', '.join(missing)}")
    return SourceTextGateResult(ok=True, message=f"source text gate passed for {project}")


def _project_contains(project_path: Path, expected: str) -> bool:
    for path in _text_files(project_path):
        if expected in _read_text(path):
            return True
    return False


def _text_files(project_path: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for path in project_path.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.stem in TEXT_FILENAMES:
            paths.append(path)
    return tuple(paths)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
