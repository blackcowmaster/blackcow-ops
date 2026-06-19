from __future__ import annotations

import re
from pathlib import Path


LOCAL_PATH_PATTERN = re.compile(r"/(?:Users|private|tmp|var)/[^\s'\"<>]+")


def build_scratch_worker_prompt(full_prompt: str, *, result_json: Path, task_id: str, replica_id: str) -> str:
    assignment = _extract_section(full_prompt, "## Original Assignment") or full_prompt.splitlines()[0]
    shared_context = _sanitize_external_feedback(
        _extract_section(
            full_prompt,
            "## Shared Swarm Context",
            stop_headings=("## Required Acceptance Checks", "## Active Skill Source"),
        )
    )
    checks = _extract_section(full_prompt, "## Required Acceptance Checks") or "(controller will run acceptance checks)"
    repair_feedback = _sanitize_external_feedback(_extract_section(full_prompt, "## Acceptance Repair Feedback"))
    parts = [
        "# External-Safe Scratch Worker",
        "",
        "You are running in an empty scratch workspace. You cannot inspect the controller repo or prior app artifacts.",
        "Generate fresh implementation files only from the public assignment below.",
        "Do not claim Dribbble, Pinterest, getdesign.kr, or other external visual references unless you actually accessed them in this run.",
        "For React Native/Expo apps, create a native app structure, a concrete DESIGN.md/design.md source, bottom tabs when useful, local persistence when requested, and native QA-ready UI.",
        "For UI apps, write DESIGN.md as the first project file before any TS/TSX code; include tokens, navigation, component states, accessibility, and native QA criteria.",
        "Mandatory Expo/RN file order: create DESIGN.md first, then immediately create swarm-water-test/App.tsx or swarm-water-test/app/_layout.tsx before declarations, storage helpers, or polish files.",
        "Minimum complete candidate for this task is DESIGN.md, package.json, tsconfig.json, App.tsx or app/_layout.tsx, and at least one source/storage file if persistence is requested.",
        "Do not install dependencies, create node_modules, run package managers, or generate build/cache folders; the controller will run checks later.",
        "Because checks run before npm install, Expo/RN scaffolds must be no-install-clean: do not extend expo/tsconfig.base or node_modules-only tsconfig files, avoid deprecated baseUrl/node10 TypeScript options, and make typecheck/lint scripts runnable in the controller.",
        'For scratch Expo/RN package.json, use "typecheck": "tsc --noEmit" and "lint": "tsc --noEmit"; scripts MUST NOT invoke eslint before dependencies are installed.',
        "For Expo/RN apps, create the native entry point before writing result JSON: either App.tsx or app/_layout.tsx must exist. A result without that entry point is incomplete and will be rejected.",
        "If TypeScript source imports React Native, Expo, navigation, storage, or React modules before npm install, include local .d.ts declarations for every imported external module, including react/jsx-runtime when using react-jsx.",
        "Do not shadow React with recursive export= declarations; if stubbing React, declare the default export and every named API you import such as useState, useEffect, useCallback, ReactElement, ComponentType, and ReactNode.",
        "Keep small apps compact. Write the result JSON immediately after creating files instead of continuing to polish.",
        "",
        "## Assignment",
        assignment.strip(),
        "",
        "## Controller Acceptance Checks",
        checks.strip(),
    ]
    if shared_context and shared_context != "(no shared_context.md found)":
        parts.extend(("", "## Controller Shared Context", shared_context))
    if repair_feedback:
        parts.extend(("", "## Acceptance Repair Feedback", repair_feedback))
    parts.extend(
        (
            "",
            "## Output Contract",
            f"Write the final worker result JSON to: {result_json}",
            f"The result must use task_id={task_id!r} and replica_id={replica_id!r}.",
            'Allowed status values are only: "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED", "TIMED_OUT".',
        )
    )
    return "\n".join(parts)


def _extract_section(text: str, heading: str, *, stop_headings: tuple[str, ...] | None = None) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return ""
    end = start
    while end < len(lines):
        if stop_headings is not None:
            if lines[end] in stop_headings:
                break
        elif lines[end].startswith("## "):
            break
        end += 1
    return "\n".join(lines[start:end]).strip()


def _sanitize_external_feedback(text: str) -> str:
    return LOCAL_PATH_PATTERN.sub(_redacted_path, text).strip()


def _redacted_path(match: re.Match[str]) -> str:
    path = Path(match.group(0).rstrip(":,.)"))
    return f"[local path]/{path.name}"
