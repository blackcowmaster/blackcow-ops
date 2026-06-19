from __future__ import annotations

import json
from pathlib import Path

from blackcow_swarm_lib.forbidden_sources import forbidden_sources_from_prompt
from blackcow_swarm_lib.schema import SchemaError, validate_result


def build_prompt(prompt_file: Path, result_json: Path, task_id: str, replica_id: str, read_only: bool) -> str:
    base_prompt = prompt_file.read_text(encoding="utf-8")
    forbidden_sources = forbidden_sources_from_prompt(base_prompt)
    write_policy = [
        "## Filesystem Policy",
        "This worker is a WRITER worker. You may edit files required by the assigned implementation task.",
        "All repository file writes and shell commands must stay inside the current workspace.",
        "Do not use absolute paths to the original repository root for project files; use relative paths from the current workspace.",
        "Do not install system tools, browsers, global npm packages, Codex binaries, or OS packages.",
        "Do not run brew, apt, softwareupdate, npm -g, sudo, npx playwright install, or similar host-mutating commands.",
        "Do not replace required acceptance checks with weaker checks. Run only short local checks needed to support your result.",
        "If a required external checker is missing, slow, or broken, record FAILED_RETRYABLE with exact evidence instead of trying to repair the host.",
        "Once you have written a valid result JSON, stop. The swarm controller owns final acceptance.",
    ]
    if read_only:
        write_policy = [
            "## Filesystem Policy",
            "This worker is READ-ONLY.",
            f"The only file you may create or modify is the required result JSON: {result_json}",
            "Do not call write_file, edit_file, multi_edit, or shell commands that mutate repository files for any other path.",
            "Do not update .omo/pipeline.log, plans, source files, docs, evidence files, lockfiles, or configuration files.",
            "Put notes, evidence, and recommendations in the result JSON summary/artifacts instead of writing side files.",
        ]
    return "\n".join(
        [
            base_prompt,
            "",
            *_forbidden_source_policy(forbidden_sources),
            "",
            *write_policy,
            "",
            "## Reasonix ACP Worker Requirement",
            f"Write the final worker result JSON to: {result_json}",
            f"The result must use task_id={task_id!r} and replica_id={replica_id!r}.",
            "The JSON must match this exact shape:",
            "{",
            f'  "task_id": "{task_id}",',
            f'  "replica_id": "{replica_id}",',
            '  "status": "SUCCEEDED",',
            '  "summary": "short summary",',
            '  "artifacts": ["path/to/artifact"],',
            '  "changed_files": [],',
            '  "patch_path": null,',
            '  "score": {"overall": 80, "correctness": 80, "safety": 80, "tests": 80}',
            "}",
            'Allowed status values are only: "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED", "TIMED_OUT".',
            "Do not finish until the result JSON exists.",
            "",
        ]
    )


def repair_prompt(result_json: Path, error: str, task_id: str, replica_id: str) -> str:
    return "\n".join(
        [
            "The result JSON you wrote is invalid for BlackCow swarm.",
            f"Validation error: {error}",
            f"Rewrite {result_json} now using this exact schema shape:",
            "{",
            f'  "task_id": "{task_id}",',
            f'  "replica_id": "{replica_id}",',
            '  "status": "SUCCEEDED",',
            '  "summary": "short summary",',
            '  "artifacts": ["path/to/artifact"],',
            '  "changed_files": [],',
            '  "patch_path": null,',
            '  "score": {"overall": 80, "correctness": 80, "safety": 80, "tests": 80}',
            "}",
            'Use only these status values: "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED", "TIMED_OUT".',
            "Do not add verdict/mode/gates fields instead of the required fields.",
        ]
    )


def validate_result_file(path: Path) -> str | None:
    if not path.exists():
        return f"missing result_json: {path}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validate_result(payload)
    except json.JSONDecodeError as exc:
        return f"invalid JSON: {exc.msg}"
    except SchemaError as exc:
        return str(exc)
    return None


def _forbidden_source_policy(forbidden_sources: tuple[str, ...]) -> list[str]:
    if not forbidden_sources:
        return []
    return [
        "## Forbidden Source Policy",
        "The assignment forbids these prior artifacts: " + ", ".join(forbidden_sources),
        "Do not read, list, explore, reference, copy, port, summarize, or structurally inspect those paths.",
        "Do not call tools against those paths. If you need a pattern, derive it from the embedded skill sources and current assignment only.",
        "The ACP controller will abort the worker immediately if transcript evidence shows access to any forbidden source path.",
    ]
