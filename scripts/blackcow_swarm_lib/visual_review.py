from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VisualReviewResult:
    ok: bool
    message: str


def run_visual_review(
    image_path: Path,
    output_path: Path,
    *,
    expect: tuple[str, ...] = (),
    codex_bin: str = "codex",
    timeout_seconds: int = 180,
) -> VisualReviewResult:
    if not image_path.exists():
        return VisualReviewResult(ok=False, message=f"missing screenshot for visual review: {image_path}")
    if image_path.stat().st_size == 0:
        return VisualReviewResult(ok=False, message=f"empty screenshot for visual review: {image_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = _visual_review_prompt(expect)
    try:
        result = subprocess.run(
            (
                codex_bin,
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--image",
                str(image_path),
                prompt,
            ),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return VisualReviewResult(ok=False, message=f"codex CLI not found: {codex_bin}")
    except subprocess.TimeoutExpired:
        return VisualReviewResult(ok=False, message=f"codex visual review timed out after {timeout_seconds}s")
    output = _combined_output(result.stdout, result.stderr)
    output_path.write_text(output, encoding="utf-8")
    if result.returncode != 0:
        return VisualReviewResult(ok=False, message=f"codex visual review failed; see {output_path}")
    first_line = _first_non_empty_line(result.stdout)
    verdict = first_line.upper()
    if verdict.startswith("FAIL"):
        return VisualReviewResult(ok=False, message=f"visual review failed; see {output_path}")
    if not verdict.startswith("PASS"):
        return VisualReviewResult(ok=False, message=f"visual review did not return PASS/FAIL; see {output_path}")
    return VisualReviewResult(ok=True, message=f"visual review passed: {output_path}")


def _visual_review_prompt(expect: tuple[str, ...]) -> str:
    expected = "\n".join(f"- {value}" for value in expect) if expect else "- no exact text expectation"
    return "\n".join(
        [
            "You are reviewing a rendered app screenshot as a strict UI acceptance gate.",
            "First line must be exactly PASS or FAIL followed by a short reason.",
            "Return FAIL for unreadable text, poor contrast, clipped or overlapping UI, placeholder/error screens, simulator home screens, web-only renderings for a native app, or missing expected content.",
            "Expected visible content:",
            expected,
        ]
    )


def _combined_output(stdout: str, stderr: str) -> str:
    parts = []
    if stdout.strip():
        parts.append(stdout.strip())
    if stderr.strip():
        parts.append("STDERR:\n" + stderr.strip())
    return "\n\n".join(parts) + "\n"


def _first_non_empty_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
