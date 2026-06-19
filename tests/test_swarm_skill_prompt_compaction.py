from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.skill_contract import build_worker_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSmallAppPromptCompaction(unittest.TestCase):
    def test_small_react_native_app_prompt_stays_compact_with_design_contract(self) -> None:
        # Given: a small Expo app task where the swarm should not pay full skill-source latency.
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            base_prompt = (
                "Create a fresh React Native Expo water-drinking check app at swarm-water-tabs-check. "
                "Include daily water check-ins, goal progress, history, settings/reminders, bottom tab "
                "navigation if useful, local persistence, explicit design system/design source, native "
                "visual/design QA, package/typecheck/lint gates, speed evidence, and final judgement."
            )

            # When: the worker prompt is built for the implementation worker.
            prompt = build_worker_prompt(
                project_root=PROJECT_ROOT,
                run_dir=run_dir,
                skill="blackcow-loop",
                base_prompt=base_prompt,
                task_id="coder-1",
                replica_id="coder-1-r1",
                result_json=run_dir / "workers" / "coder-1" / "result.json",
                acceptance_checks=("python3 scripts/blackcow_design_gate.py --project swarm-water-tabs-check",),
            )

            # Then: the prompt remains bounded but still carries the design/native verification contract.
            self.assertLess(len(prompt), 70_000)
            self.assertIn("Small App Fast Path", prompt)
            self.assertIn("Compact excerpt for small single-purpose app", prompt)
            self.assertIn("PDCA Evidence Discipline", prompt)
            self.assertIn("Create or select DESIGN.md", prompt)
            self.assertIn("react-native-design", prompt)
            self.assertIn("ui-ux-pro-max", prompt)
            self.assertIn("bottom tab navigation", prompt)
            self.assertIn("native screenshot criteria", prompt)


if __name__ == "__main__":
    unittest.main()
