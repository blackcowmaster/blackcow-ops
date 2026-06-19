from __future__ import annotations

from typing import Final


_HEAD_LINE_COUNT: Final = 56
_MARKER_CONTEXT_BEFORE: Final = 3
_MARKER_CONTEXT_AFTER: Final = 18
_MAX_EXCERPT_LINES: Final = 280
_ACTIVE_SKILL_MARKERS: Final = (
    "Explicit Swarm Activation",
    "PDCA Evidence Discipline",
    "Observable Verification Ladder",
    "Visual Verification",
    "Evidence Compaction Index",
    "Stop Rules",
    "Completion Criteria",
    "blackcow-librarian integration",
    "Design",
    "DESIGN.md",
    "getdesign",
    "React Native",
    "Expo",
    "screenshot",
    "visual",
    "Evidence",
    "result.json",
    "Do not",
    "speed",
)


def compact_active_skill_source_for_small_app(text: str) -> str:
    lines = text.splitlines()
    selected = _selected_line_indexes(lines)
    excerpt = _join_compacted_lines(lines, selected)
    return "\n".join(
        (
            "Compact excerpt for small single-purpose app; full active skill source omitted to reduce worker latency.",
            excerpt,
            "End compact excerpt. Preserve the active skill contract, but do not expand into broad discovery unless acceptance checks require it.",
        )
    )


def _selected_line_indexes(lines: list[str]) -> set[int]:
    selected = set(range(min(_HEAD_LINE_COUNT, len(lines))))
    for index, line in enumerate(lines):
        if any(marker in line for marker in _ACTIVE_SKILL_MARKERS):
            start = max(0, index - _MARKER_CONTEXT_BEFORE)
            end = min(len(lines), index + _MARKER_CONTEXT_AFTER)
            selected.update(range(start, end))
    return set(sorted(selected)[:_MAX_EXCERPT_LINES])


def _join_compacted_lines(lines: list[str], selected: set[int]) -> str:
    output: list[str] = []
    previous = -2
    for index in sorted(selected):
        if index != previous + 1 and output:
            output.append("...")
        output.append(lines[index])
        previous = index
    return "\n".join(output).strip()
