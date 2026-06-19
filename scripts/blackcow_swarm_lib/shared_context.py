from __future__ import annotations

from .acceptance import AcceptancePlan
from .estimate import Estimate


def build_shared_context(task: str, estimate: Estimate, acceptance: AcceptancePlan) -> str:
    checks = "\n".join(f"- {check}" for check in acceptance.checks)
    return "\n".join(
        [
            "# Shared Swarm Context",
            "",
            f"Task: {task}",
            f"Recommended mode: {estimate.recommended_mode}",
            f"Recommended intensity: {estimate.recommended_intensity}",
            f"Detected project: {acceptance.project_path or 'none'}",
            "",
            "## Required Acceptance Checks",
            checks,
            "",
            "## Failure Feedback Loop",
            "If any acceptance check fails, record the failing command, exit code, stdout, stderr, and artifact path.",
            "Feed that failure packet into the next coder/review worker.",
            "Do not write a successful final judgement while any acceptance check is failing.",
            "",
            "## Design Source Gate",
            "UI work must select or generate an explicit design source before implementation.",
            "Use getdesign.kr for Korean product patterns, getdesign.md for brand systems, or project DESIGN.md/design.md.",
            "Use shadcn/ui only for web React surfaces; React Native uses native component tokens and icon libraries.",
            "",
            "## Native Visual Gate",
            "React Native work targets iOS/Android native first. Web smoke is optional compatibility evidence, not the primary proof.",
            "Capture simulator screenshots with xcrun simctl and run codex exec --image before native UI work can pass.",
            "",
            "## Swarm Speed Gate",
            "Record worker started_at/finished_at timing and compare wall-clock speedup against serial duration.",
            "Do not claim swarm improvement without measured speed evidence.",
            "",
            "## Anti-Gaming Guardrails",
            "- do_not_change_check_commands",
            "- do_not_skip_or_delete_tests",
            "- do_not_weaken_assertions",
            "- do_not_fake_exit_conditions",
            "- do_not_mark_success_without_valid_result_json",
            "- do_not_continue_past_max_iterations_without_reporting_blocker",
            "",
            "Every worker must write a valid result.json before claiming success.",
            "If result.json is missing or invalid, the worker outcome is FAILED_RETRYABLE.",
            "",
        ]
    )
