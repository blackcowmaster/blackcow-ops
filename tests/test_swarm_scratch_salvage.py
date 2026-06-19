from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.scratch_salvage import decide_scratch_salvage


class TestScratchSalvage(unittest.TestCase):
    def test_timeout_salvage_reports_missing_design_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scratch = Path(temp_dir)
            project = scratch / "swarm-water-test"
            self._write_minimal_project(project, design=False)

            decision = decide_scratch_salvage(
                scratch,
                outcome_status="FAILED_RETRYABLE",
                outcome_events=("worker_exit_1", "missing_result_json"),
            )

            self.assertEqual(decision.status, "FAILED_RETRYABLE")
            self.assertIn("missing design source", decision.summary)

    def test_complete_timeout_salvage_can_enter_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scratch = Path(temp_dir)
            project = scratch / "swarm-water-test"
            self._write_minimal_project(project, design=True)

            decision = decide_scratch_salvage(
                scratch,
                outcome_status="FAILED_RETRYABLE",
                outcome_events=("worker_exit_1", "missing_result_json"),
            )

            self.assertEqual(decision.status, "SUCCEEDED")
            self.assertIn("complete scratch candidate", decision.summary)

    def test_successful_worker_keeps_original_success_salvage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scratch = Path(temp_dir)
            project = scratch / "swarm-water-test"
            self._write_minimal_project(project, design=False)

            decision = decide_scratch_salvage(
                scratch,
                outcome_status="SUCCEEDED",
                outcome_events=("worker_exit_0",),
            )

            self.assertEqual(decision.status, "SUCCEEDED")
            self.assertIsNone(decision.summary)

    def _write_minimal_project(self, project: Path, *, design: bool) -> None:
        project.mkdir(parents=True)
        (project / "package.json").write_text(
            '{"scripts":{"typecheck":"tsc --noEmit","lint":"tsc --noEmit"}}\n',
            encoding="utf-8",
        )
        (project / "tsconfig.json").write_text('{"compilerOptions":{"jsx":"react-jsx"}}\n', encoding="utf-8")
        (project / "app.json").write_text('{"expo":{"name":"Water","slug":"swarm-water-test"}}\n', encoding="utf-8")
        (project / "App.tsx").write_text("export default function App() { return null; }\n", encoding="utf-8")
        (project / "types.d.ts").write_text('declare module "react/jsx-runtime";\n', encoding="utf-8")
        if design:
            (project / "DESIGN.md").write_text("# Water Design\n\nTokens and navigation rules.\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
