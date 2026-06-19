from __future__ import annotations

import re
from pathlib import Path

from .skill_source_compaction import compact_active_skill_source_for_small_app


BLACKCOW_SKILLS = frozenset(
    (
        "blackcow-plan",
        "blackcow-loop",
        "blackcow-qa",
        "blackcow-librarian",
        "blackcow-governor",
        "blackcow-skill-review",
        "blackcow-skill-evolver",
        "blackcow-swarm",
    )
)

CROSS_SKILL_SECTION_MARKERS = (
    "Cross-Skill Evidence Contract",
    "Pipeline Log",
    "blackcow-librarian integration",
    "Evidence Compaction Index",
)
REACT_NATIVE_SKILLS = (
    "react-native-architecture",
    "react-native-design",
    "ui-ux-pro-max",
    "vercel-react-native-skills",
)
REACT_NATIVE_TASK_PATTERNS = (
    re.compile(r"\breact[-\s]?native\b", re.IGNORECASE),
    re.compile(r"\bexpo\b", re.IGNORECASE),
    re.compile(r"\brn\b", re.IGNORECASE),
    re.compile(r"\bios\s+smoke\b", re.IGNORECASE),
    re.compile(r"\bnative\s+app\b", re.IGNORECASE),
)
REACT_NATIVE_SKILL_SECTION_MARKERS = (
    "## When to Use This Skill",
    "## When to Apply",
    "## Quick Reference",
    "## How to Use This Skill",
    "## Best Practices",
    "### Step 2: Generate Design System (REQUIRED)",
)
SMALL_APP_FAST_PATH_SKILLS = frozenset(("blackcow-plan", "blackcow-loop", "blackcow-qa"))
SMALL_APP_FEATURE_PATTERNS = (
    re.compile(r"\bwater[-\s]?drinking\b", re.IGNORECASE),
    re.compile(r"\bhydration\b", re.IGNORECASE),
    re.compile(r"\bpomodoro\b", re.IGNORECASE),
    re.compile(r"\btimer\b", re.IGNORECASE),
    re.compile(r"\bcheck[-\s]?in\b", re.IGNORECASE),
    re.compile(r"\btracker\b", re.IGNORECASE),
)
SMALL_APP_COMPLEXITY_BLOCKERS = (
    re.compile(r"\bauth\b", re.IGNORECASE),
    re.compile(r"\bbackend\b", re.IGNORECASE),
    re.compile(r"\bbilling\b", re.IGNORECASE),
    re.compile(r"\bcloud\s+sync\b", re.IGNORECASE),
    re.compile(r"\bmigration\b", re.IGNORECASE),
    re.compile(r"\bpayment\b", re.IGNORECASE),
    re.compile(r"\bpush\s+notification\b", re.IGNORECASE),
)


def build_worker_prompt(
    *,
    project_root: Path,
    run_dir: Path,
    skill: str,
    base_prompt: str,
    task_id: str,
    replica_id: str,
    result_json: Path,
    acceptance_checks: tuple[str, ...],
) -> str:
    shared_context = _format_embedded_context(_shared_context(project_root=project_root, run_dir=run_dir))
    small_app_fast_path = _is_small_single_purpose_mobile_app(skill, base_prompt)
    parts = [
        "# BlackCow Skill-Backed Swarm Worker",
        "",
        f"Task ID: {task_id}",
        f"Replica ID: {replica_id}",
        f"Active skill: {skill}",
        f"Required result JSON: {result_json}",
        "",
        "You are not a generic parallel worker. You must execute the BlackCow skill contract below.",
        "Read the active skill source, follow its phases and evidence rules inline, then write the required result JSON.",
        "Do not call run_skill or spawn another copy of the active BlackCow skill. The embedded source is already the skill invocation.",
        "",
        "## Original Assignment",
        base_prompt,
        "",
        "## Shared Swarm Context",
        shared_context or "(no shared_context.md found)",
        "",
        "## Required Acceptance Checks",
        _acceptance_block(acceptance_checks),
        "",
        "## Active Skill Source",
        _skill_source_block(project_root, skill, compact=small_app_fast_path),
        "",
    ]
    rn_skill_context = _react_native_skill_context_block(base_prompt)
    if rn_skill_context:
        parts.extend(
            [
                "## React Native / UI Skill Sources",
                _react_native_ui_contract(),
                "",
                rn_skill_context,
                "",
            ]
        )
    fast_path = _small_app_fast_path_block(skill, base_prompt)
    if fast_path:
        parts.extend([fast_path, ""])
    parts.extend(
        [
            "## Cross-Skill Evidence Contract",
            _cross_skill_block(project_root),
            "",
            "## Worker Output Contract",
            "Write a valid result.json to the path passed by the runner. The JSON must match schemas/swarm-result.schema.json.",
            "Do not mark SUCCEEDED unless the active skill's artifacts exist and the acceptance checks can pass.",
            "If blocked, write FAILED_RETRYABLE or FAILED_FINAL with artifact paths and the precise blocker.",
            "",
        ]
    )
    return "\n".join(parts)


def _small_app_fast_path_block(skill: str, base_prompt: str) -> str:
    if not _is_small_single_purpose_mobile_app(skill, base_prompt):
        return ""
    return "\n".join(
        (
            "## Small App Fast Path",
            "This overrides broad embedded skill-source discovery instructions for this swarm run.",
            "The assignment is a small single-purpose Expo/React Native app; do not expand it into a full multi-lane product analysis.",
            "Do not call web_search.",
            "Do not call explore.",
            "Do not inspect prior app/project directories or forbidden sources.",
            "Use the embedded skill sources, shared context, task graph, acceptance checks, and current target path status only.",
            "For Expo/React Native apps, create DESIGN.md first, then immediately create App.tsx or app/_layout.tsx before declaration stubs or polish files.",
            "Minimum complete Expo/RN candidate: DESIGN.md, package.json, tsconfig.json, App.tsx or app/_layout.tsx, and requested persistence/source files.",
            "Write a compact result JSON directly: summary <= 1000 words, artifacts limited to required output paths, no giant markdown plan.",
        )
    )


def _shared_context(*, project_root: Path, run_dir: Path) -> str:
    primary = _read_optional(run_dir / "shared_context.md")
    if primary:
        return primary
    controller_run_dir = project_root / ".omo" / "swarm" / "runs" / run_dir.name
    if controller_run_dir != run_dir:
        fallback = _read_optional(controller_run_dir / "shared_context.md")
        if fallback:
            return fallback
    return ""


def _format_embedded_context(text: str) -> str:
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            lines.append(f"###{line.lstrip('#')}")
        else:
            lines.append(line)
    return "\n".join(lines).strip()


def _is_small_single_purpose_mobile_app(skill: str, base_prompt: str) -> bool:
    if skill not in SMALL_APP_FAST_PATH_SKILLS:
        return False
    has_mobile_stack = _is_react_native_task(base_prompt)
    has_small_feature = any(pattern.search(base_prompt) for pattern in SMALL_APP_FEATURE_PATTERNS)
    has_blocker = any(pattern.search(base_prompt) for pattern in SMALL_APP_COMPLEXITY_BLOCKERS)
    return has_mobile_stack and has_small_feature and not has_blocker


def _skill_source_block(project_root: Path, skill: str, *, compact: bool = False) -> str:
    if skill not in BLACKCOW_SKILLS:
        return f"(non-BlackCow skill: {skill})"
    path = project_root / "skills" / f"{skill}.md"
    text = _read_optional(path)
    if not text:
        return f"Missing skill source: {path}"
    if compact:
        text = compact_active_skill_source_for_small_app(text)
    return f"Source path: {path}\n\n```markdown\n{text}\n```"


def _cross_skill_block(project_root: Path) -> str:
    blocks = []
    for skill in ("blackcow-governor", "blackcow-librarian"):
        path = project_root / "skills" / f"{skill}.md"
        text = _read_optional(path)
        if not text:
            blocks.append(f"### {skill}\nMissing source: {path}")
            continue
        excerpt = _extract_relevant_lines(text)
        blocks.append(f"### {skill}\nSource path: {path}\n\n```markdown\n{excerpt}\n```")
    return "\n\n".join(blocks)


def _react_native_skill_context_block(base_prompt: str) -> str:
    if not _is_react_native_task(base_prompt):
        return ""
    return "\n\n".join(_external_skill_source_block(skill) for skill in REACT_NATIVE_SKILLS)


def _react_native_ui_contract() -> str:
    return "\n".join(
        (
            "For React Native/Expo work, apply the embedded React Native architecture, React Native design, ui-ux-pro-max, and Vercel React Native skill sources before implementation.",
            "Create or select DESIGN.md, design.md, getdesign.md, or getdesign.kr with concrete tokens, component rules, accessibility constraints, and native screenshot criteria before UI code.",
            "Use React Native-native components, StyleSheet.create or Nativewind, safe-area handling, Pressable for taps, native icon libraries, and Expo-compatible dependencies.",
            "Do not replace a native app request with a web-only DOM/CSS implementation. Web smoke is compatibility evidence only.",
        )
    )


def _is_react_native_task(base_prompt: str) -> bool:
    return any(pattern.search(base_prompt) for pattern in REACT_NATIVE_TASK_PATTERNS)


def _external_skill_source_block(skill: str) -> str:
    path = Path.home() / ".agents" / "skills" / skill / "SKILL.md"
    text = _read_optional(path)
    if not text:
        return f"### {skill}\nMissing source: {path}"
    excerpt = _extract_external_skill_excerpt(text)
    return f"### {skill}\nSource path: {path}\n\n```markdown\n{excerpt}\n```"


def _extract_external_skill_excerpt(text: str) -> str:
    lines = text.splitlines()
    selected = lines[:12]
    selected.append("")
    for index, line in enumerate(lines):
        if line in REACT_NATIVE_SKILL_SECTION_MARKERS:
            end = index + 1
            while end < len(lines) and not lines[end].startswith("## "):
                end += 1
            selected.extend(lines[index : min(end, index + 40)])
            selected.append("")
    return "\n".join(selected).strip()


def _extract_relevant_lines(text: str) -> str:
    lines = text.splitlines()
    selected: list[str] = []
    for index, line in enumerate(lines):
        if any(marker in line for marker in CROSS_SKILL_SECTION_MARKERS):
            start = max(0, index - 3)
            end = min(len(lines), index + 35)
            selected.extend(lines[start:end])
            selected.append("")
    if not selected:
        return "\n".join(lines[:120])
    return "\n".join(selected)


def _acceptance_block(checks: tuple[str, ...]) -> str:
    if not checks:
        return "(none)"
    return "\n".join(f"- {check}" for check in checks)


def _read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
