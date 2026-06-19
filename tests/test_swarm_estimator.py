from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.config import load_config
from scripts.blackcow_swarm_lib.estimate import estimate_task


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "scripts" / "blackcow_swarm.py"


class TestSwarmEstimator(unittest.TestCase):
    def test_high_task_recommends_allowed_intensity(self) -> None:
        estimate = estimate_task(
            "Implement team invite flow",
            load_config(),
            requested_intensity="high",
            requested_policy="auto",
            requested_mode="adaptive",
        )

        self.assertIn(estimate.recommended_intensity, ("normal", "high", "max"))
        self.assertGreaterEqual(estimate.expected_speedup, 1.0)
        self.assertGreater(estimate.recommended_workers, 0)
        self.assertTrue(estimate.writer_swarm_allowed)

    def test_risky_writer_requires_approval_in_auto_policy(self) -> None:
        estimate = estimate_task(
            "Change auth policy and package-lock.json",
            load_config(),
            requested_intensity="high",
            requested_policy="auto",
            requested_mode="adaptive",
        )

        self.assertTrue(estimate.requires_approval)
        self.assertFalse(estimate.writer_swarm_allowed)

    def test_tiny_task_uses_serial_mode(self) -> None:
        estimate = estimate_task(
            "Rename typo",
            load_config(),
            requested_intensity="max",
            requested_policy="auto",
            requested_mode="adaptive",
        )

        self.assertEqual(estimate.recommended_mode, "serial")
        self.assertEqual(estimate.recommended_intensity, "normal")
        self.assertEqual(estimate.recommended_workers, 1)

    def test_small_single_purpose_expo_app_is_not_estimated_from_prompt_length(self) -> None:
        estimate = estimate_task(
            (
                "Create a fresh React Native Expo water-drinking check app at swarm-water-check-app. "
                "Use the blackcow-* skill pipeline and Reasonix worker swarm. Include timer-free hydration "
                "check-ins, daily goal progress, history, native visual/design QA, package/typecheck/lint "
                "gates, speed measurement, and final judgement evidence. Do not use prior water-check-app "
                "or pomodoro-app artifacts."
            ),
            load_config(),
            requested_intensity="max",
            requested_policy="auto",
            requested_mode="adaptive",
        )

        self.assertLessEqual(estimate.estimated_serial_minutes, 12)
        self.assertEqual(estimate.recommended_mode, "coder")
        self.assertEqual(estimate.recommended_intensity, "normal")
        self.assertLessEqual(estimate.recommended_workers, 3)
        self.assertEqual(estimate.expected_speedup, 1.0)

    def test_estimate_cli_outputs_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "estimate",
                "Implement team invite flow",
                "--intensity",
                "high",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(payload["recommended_intensity"], ("normal", "high", "max"))
        self.assertGreaterEqual(payload["expected_speedup"], 1.0)
        self.assertGreater(payload["recommended_workers"], 0)


if __name__ == "__main__":
    unittest.main()
