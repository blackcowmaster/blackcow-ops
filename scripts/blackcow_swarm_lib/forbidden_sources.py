from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FORBIDDEN_PRIOR_ARTIFACTS = re.compile(r"do\s+not\s+use\s+prior\s+(.+?)\s+artifacts?", re.IGNORECASE)
REFERENCE_WORDS = (
    "reference",
    "surveyed",
    "explored",
    "copied",
    "ported",
    "reused",
    "used",
    "from ",
)
NEGATED_WORDS = (
    "did not use",
    "do not use",
    "not used",
    "without using",
)


@dataclass(frozen=True, slots=True)
class ForbiddenSourceViolation:
    source: str
    evidence_path: str
    evidence: str


def forbidden_sources_from_prompt(prompt: str) -> tuple[str, ...]:
    sources: list[str] = []
    for match in FORBIDDEN_PRIOR_ARTIFACTS.finditer(prompt):
        for raw in re.split(r"\s+(?:or|and)\s+|,", match.group(1)):
            source = raw.strip(" `\"'")
            if source and source not in sources:
                sources.append(source)
    return tuple(sources)


def forbidden_source_violation(prompt: str, result_json: Path) -> ForbiddenSourceViolation | None:
    sources = forbidden_sources_from_prompt(prompt)
    if not sources:
        return None
    try:
        payload = json.loads(result_json.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    for path, value in _walk_strings(payload):
        lowered = value.lower()
        for source in sources:
            if source.lower() not in lowered:
                continue
            if _is_negated(lowered):
                continue
            if any(word in lowered for word in REFERENCE_WORDS) or path.endswith(".artifacts[]"):
                return ForbiddenSourceViolation(source=source, evidence_path=path, evidence=value)
    return None


def write_forbidden_source_report(
    run_dir: Path,
    report_key: str,
    prompt: str,
    result_json: Path,
    violation: ForbiddenSourceViolation,
) -> Path:
    report_path = run_dir / "reports" / f"forbidden-source-{report_key}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "status": "PROTOCOL_VIOLATION",
                "forbidden_source": violation.source,
                "evidence_path": violation.evidence_path,
                "evidence": violation.evidence,
                "result_json": str(result_json),
                "prompt_rule": _first_forbidden_rule(prompt),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def _first_forbidden_rule(prompt: str) -> str:
    match = FORBIDDEN_PRIOR_ARTIFACTS.search(prompt)
    return match.group(0) if match else ""


def _is_negated(text: str) -> bool:
    return any(word in text for word in NEGATED_WORDS)


def _walk_strings(value: Any, path: str = "$") -> tuple[tuple[str, str], ...]:
    results: list[tuple[str, str]] = []
    if isinstance(value, str):
        results.append((path, value))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            results.extend(_walk_strings(item, f"{path}[]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            results.extend(_walk_strings(item, f"{path}.{key}"))
    return tuple(results)
