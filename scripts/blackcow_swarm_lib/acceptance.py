from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from .config import JsonValue


DEFAULT_ACCEPTANCE_CHECKS = ("python3 -m unittest discover -s tests -p 'test_swarm_*.py'",)
NODE_SCRIPT_ORDER = ("typecheck", "lint", "test", "build")


@dataclass(frozen=True, slots=True)
class AcceptancePlan:
    checks: tuple[str, ...]
    project_path: str | None
    native_platform: str | None = None
    visual_review_required: bool = False
    runtime_visual_required: bool = False
    expected_text: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PackageAcceptance:
    checks: tuple[str, ...]
    native_platform: str | None
    visual_review_required: bool
    expected_text: tuple[str, ...]


def infer_acceptance_checks(task: str, project_root: Path) -> AcceptancePlan:
    new_project_path = _explicit_new_expo_project_path(task)
    if new_project_path is not None:
        expected_text = _expected_ui_text(task)
        return AcceptancePlan(
            checks=_new_expo_project_checks(new_project_path, expected_text),
            project_path=new_project_path,
            native_platform="ios",
            visual_review_required=True,
            runtime_visual_required=False,
            expected_text=expected_text,
        )
    for project_path in _candidate_project_paths(task, project_root):
        package_json = project_root / project_path / "package.json"
        if package_json.exists():
            acceptance = _checks_from_package_json(task, project_path, package_json)
            if acceptance.checks:
                return AcceptancePlan(
                    checks=acceptance.checks,
                    project_path=project_path,
                    native_platform=acceptance.native_platform,
                    visual_review_required=acceptance.visual_review_required,
                    runtime_visual_required=acceptance.native_platform is not None,
                    expected_text=acceptance.expected_text,
                )
    return AcceptancePlan(checks=DEFAULT_ACCEPTANCE_CHECKS, project_path=None)


def _candidate_project_paths(task: str, project_root: Path) -> tuple[str, ...]:
    candidates: list[str] = []
    for token in re.findall(r"[A-Za-z0-9_./-]+", task):
        normalized = token.strip().strip("./")
        if not normalized or normalized in (".", "..") or ".." in normalized:
            continue
        candidate = project_root / normalized
        if candidate.is_dir() and normalized not in candidates:
            candidates.append(normalized)
    return tuple(candidates)


def _explicit_new_expo_project_path(task: str) -> str | None:
    normalized = task.lower()
    if "expo" not in normalized or "react native" not in normalized:
        return None
    if not any(marker in normalized for marker in ("create", "new", "build", "make", "implement")):
        return None
    match = re.search(r"\b(?:in|at|under|called|named)\s+([A-Za-z0-9_.-]+)", task)
    if match is None:
        return None
    candidate = match.group(1).strip().strip("./")
    if not candidate or candidate in (".", "..") or ".." in candidate or "/" in candidate:
        return None
    return candidate


def _new_expo_project_checks(project_path: str, expected_text: tuple[str, ...]) -> tuple[str, ...]:
    checks = [
        f"test -f {shlex.quote(project_path)}/package.json",
        f"python3 scripts/blackcow_expo_clean_gate.py --project {shlex.quote(project_path)}",
        f"cd {shlex.quote(project_path)} && npm run typecheck",
        f"cd {shlex.quote(project_path)} && npm run lint",
        f"python3 scripts/blackcow_design_gate.py --project {shlex.quote(project_path)}",
        f"python3 scripts/blackcow_native_smoke.py --project {shlex.quote(project_path)} --platform ios",
    ]
    if expected_text:
        checks.append(_source_text_gate_check(project_path, expected_text))
    return tuple(checks)


def _checks_from_package_json(task: str, project_path: str, package_json: Path) -> PackageAcceptance:
    payload: JsonValue = json.loads(package_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return PackageAcceptance(checks=(), native_platform=None, visual_review_required=False, expected_text=())
    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return PackageAcceptance(checks=(), native_platform=None, visual_review_required=False, expected_text=())
    checks: list[str] = []
    expected_text = _expected_ui_text(task)
    for script_name in NODE_SCRIPT_ORDER:
        if script_name in scripts:
            checks.append(f"cd {project_path} && npm run {script_name}")
    checks.append(f"python3 scripts/blackcow_design_gate.py --project {project_path}")
    is_native = _is_react_native(payload)
    if is_native:
        checks.append(f"python3 scripts/blackcow_native_smoke.py --project {project_path} --platform ios")
    has_web = "web" in scripts
    if has_web:
        checks.append(_web_smoke_check(project_path, expected_text))
    return PackageAcceptance(
        checks=tuple(checks),
        native_platform="ios" if is_native else None,
        visual_review_required=is_native or has_web,
        expected_text=expected_text,
    )


def _is_react_native(payload: dict[str, JsonValue]) -> bool:
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, dict):
        return False
    return "react-native" in dependencies or "expo" in dependencies


def _expected_ui_text(task: str) -> tuple[str, ...]:
    normalized = task.lower()
    if "water" in normalized or "drink" in normalized or "hydration" in normalized:
        return ("Water",)
    if "pomodoro" in normalized or ("timer" in normalized and "timer-free" not in normalized):
        return ("25:00",)
    return ()


def _web_smoke_check(project_path: str, expected_text: tuple[str, ...]) -> str:
    parts = [f"python3 scripts/blackcow_web_smoke.py --project {shlex.quote(project_path)} --port 8088"]
    for value in expected_text:
        parts.append(f"--expect {shlex.quote(value)}")
    parts.append("--reject 'Something went wrong'")
    return " ".join(parts)


def _source_text_gate_check(project_path: str, expected_text: tuple[str, ...]) -> str:
    parts = [f"python3 scripts/blackcow_source_text_gate.py --project {shlex.quote(project_path)}"]
    for value in expected_text:
        parts.append(f"--expect {shlex.quote(value)}")
    return " ".join(parts)
