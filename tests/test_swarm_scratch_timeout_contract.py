from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.runner import WorkerTask
from scripts.blackcow_swarm_lib.schema import validate_result
from scripts.blackcow_swarm_lib.scratch_prompt import build_scratch_worker_prompt
from scripts.blackcow_swarm_lib.scratch_runner import (
    SCRATCH_TIMEOUT_SECONDS,
    ScratchReasonixRunner,
    write_salvaged_result_if_needed,
)


class TestScratchTimeoutContract(unittest.TestCase):
    def test_timeout_salvage_is_retryable_not_success(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as scratch_dir:
            workspace = Path(workspace_dir)
            scratch = Path(scratch_dir)
            result_json = workspace / "result.json"
            (scratch / "swarm-water-test" / "src").mkdir(parents=True)
            (scratch / "swarm-water-test" / "src" / "App.tsx").write_text("partial app\n", encoding="utf-8")
            task = self._worker_task(workspace, result_json)

            salvaged = write_salvaged_result_if_needed(
                result_json,
                scratch=scratch,
                task=task,
                started_at=10.0,
                finished_at=100.0,
                status="FAILED_RETRYABLE",
                summary="controller salvaged partial scratch files after worker timeout; retry required",
            )

            payload = json.loads(result_json.read_text(encoding="utf-8"))
            validate_result(payload)
            self.assertTrue(salvaged)
            self.assertEqual(
                payload["status"],
                "FAILED_RETRYABLE",
                "timed-out partial scratch files must not enter tournament as SUCCEEDED",
            )
            self.assertIn("timeout", payload["summary"])

    def test_scratch_worker_command_has_inner_timeout_before_outer_kill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template = ScratchReasonixRunner(Path(temp_dir)).runner.runner_config.command_template

        self.assertIn("--timeout-seconds", template)
        timeout_index = template.index("--timeout-seconds")
        self.assertEqual(template[timeout_index + 1], str(max(1, SCRATCH_TIMEOUT_SECONDS - 5)))

    def test_scratch_prompt_forbids_no_install_eslint_script(self) -> None:
        prompt = build_scratch_worker_prompt(
            "## Original Assignment\nCreate a fresh React Native Expo water app.",
            result_json=Path("/tmp/scratch/.blackcow/result.json"),
            task_id="coder-1",
            replica_id="coder-1-r1",
        )

        self.assertIn('"lint": "tsc --noEmit"', prompt)
        self.assertIn("MUST NOT invoke eslint", prompt)

    def _worker_task(self, workspace: Path, result_json: Path) -> WorkerTask:
        prompt_file = workspace / "prompt.md"
        prompt_file.write_text("Create app", encoding="utf-8")
        return WorkerTask(
            task_id="coder-1",
            replica_id="coder-1-r1",
            skill="blackcow-loop",
            read_only=False,
            prompt_file=prompt_file,
            result_json=result_json,
            workspace=workspace,
            timeout_seconds=90,
            missing_result_fatal=False,
        )


if __name__ == "__main__":
    unittest.main()
