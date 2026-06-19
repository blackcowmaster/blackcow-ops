from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scripts import blackcow_reasonix_acp_worker as acp_worker
from scripts.blackcow_reasonix_acp_worker import build_prompt, forbidden_transcript_access, terminal_transcript_error


class TestReasonixAcpWorker(unittest.TestCase):
    def test_missing_reasonix_executable_reports_worker_failure_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_file = root / "prompt.md"
            result_json = root / "result.json"
            prompt_file.write_text("Run QA\n", encoding="utf-8")
            env = os.environ.copy()
            env["PATH"] = "/usr/bin:/bin"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "blackcow_reasonix_acp_worker.py"),
                    "--skill",
                    "blackcow-qa",
                    "--prompt-file",
                    str(prompt_file),
                    "--result-json",
                    str(result_json),
                    "--workspace",
                    str(root),
                    "--run-id",
                    "missing-reasonix",
                    "--task-id",
                    "qa-1",
                    "--replica-id",
                    "qa-1-r1",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("reasonix acp worker failed", result.stderr)
            self.assertIn("reasonix executable missing", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_missing_prompt_file_is_not_reported_as_missing_reasonix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake_reasonix = bin_dir / "reasonix"
            fake_reasonix.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(30)\n", encoding="utf-8")
            fake_reasonix.chmod(0o755)
            result_json = root / "result.json"
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:/usr/bin:/bin"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "blackcow_reasonix_acp_worker.py"),
                    "--skill",
                    "blackcow-qa",
                    "--prompt-file",
                    str(root / "missing-prompt.md"),
                    "--result-json",
                    str(result_json),
                    "--workspace",
                    str(root),
                    "--run-id",
                    "missing-prompt",
                    "--task-id",
                    "qa-1",
                    "--replica-id",
                    "qa-1-r1",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=5,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("reasonix acp worker failed", result.stderr)
            self.assertIn("missing-prompt.md", result.stderr)
            self.assertNotIn("reasonix executable missing", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_non_executable_reasonix_reports_start_failure_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake_reasonix = bin_dir / "reasonix"
            fake_reasonix.write_text("not executable\n", encoding="utf-8")
            fake_reasonix.chmod(0o644)
            prompt_file = root / "prompt.md"
            prompt_file.write_text("Run QA\n", encoding="utf-8")
            result_json = root / "result.json"
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:/usr/bin:/bin"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "blackcow_reasonix_acp_worker.py"),
                    "--skill",
                    "blackcow-qa",
                    "--prompt-file",
                    str(prompt_file),
                    "--result-json",
                    str(result_json),
                    "--workspace",
                    str(root),
                    "--run-id",
                    "bad-reasonix",
                    "--task-id",
                    "qa-1",
                    "--replica-id",
                    "qa-1-r1",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("reasonix acp worker failed: failed to start reasonix executable", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_worker_command_disables_user_mcp_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            argv_log = root / "argv.json"
            fake_reasonix = bin_dir / "reasonix"
            fake_reasonix.write_text(
                f"#!{sys.executable}\n"
                "import json\n"
                "import pathlib\n"
                "import sys\n"
                f"pathlib.Path({str(argv_log)!r}).write_text(json.dumps(sys.argv), encoding='utf-8')\n"
                "for line in sys.stdin:\n"
                "    msg = json.loads(line)\n"
                "    method = msg.get('method')\n"
                "    if method == 'initialize':\n"
                "        print(json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'result': {'ok': True}}), flush=True)\n"
                "    elif method == 'session/new':\n"
                "        print(json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'result': {'sessionId': 's1'}}), flush=True)\n"
                "    elif method == 'session/prompt':\n"
                "        print(json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'result': {'stopReason': 'end_turn'}}), flush=True)\n"
                "        if msg.get('id') == 4:\n"
                "            break\n",
                encoding="utf-8",
            )
            fake_reasonix.chmod(0o755)
            prompt_file = root / "prompt.md"
            prompt_file.write_text("Run QA\n", encoding="utf-8")
            result_json = root / "result.json"
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:/usr/bin:/bin"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "blackcow_reasonix_acp_worker.py"),
                    "--skill",
                    "blackcow-qa",
                    "--prompt-file",
                    str(prompt_file),
                    "--result-json",
                    str(result_json),
                    "--workspace",
                    str(root),
                    "--run-id",
                    "mcp-isolated",
                    "--task-id",
                    "qa-1",
                    "--replica-id",
                    "qa-1-r1",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )

            argv = json.loads(argv_log.read_text(encoding="utf-8"))
            self.assertEqual(result.returncode, 1)
            self.assertIn("--mcp", argv)
            self.assertEqual(argv[argv.index("--mcp") + 1], "")

    def test_writer_prompt_forbids_original_repo_absolute_path_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_file = root / "prompt.md"
            result_json = root / "result.json"
            prompt_file.write_text("Implement app\n", encoding="utf-8")

            prompt = build_prompt(prompt_file, result_json, "coder-1", "coder-1-r1", read_only=False)

            self.assertIn("current workspace", prompt)
            self.assertIn("Do not use absolute paths to the original repository root", prompt)

    def test_terminal_transcript_error_detects_unrecoverable_sse_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "reasonix-transcript.jsonl"
            transcript.write_text(
                '{"role":"error","error":"SSE body read failed: terminated",'
                '"errorDetail":{"recoverable":false,"retryable":true}}\n',
                encoding="utf-8",
            )

            message = terminal_transcript_error(transcript)

            self.assertEqual(message, "SSE body read failed: terminated")

    def test_forbidden_transcript_access_detects_tool_start_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "reasonix-transcript.jsonl"
            transcript.write_text(
                '{"role":"tool_start","tool":"list_directory","args":"{\\"path\\": \\"water-check-app\\"}"}\n'
                '{"role":"tool_start","tool":"list_directory","args":"{\\"path\\": \\"swarm-water-check-app\\"}"}\n',
                encoding="utf-8",
            )

            message = forbidden_transcript_access(transcript, ("water-check-app", "pomodoro-app"))

            self.assertEqual(message, "forbidden source access attempted: water-check-app")

    def test_forbidden_transcript_access_allows_target_with_source_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "reasonix-transcript.jsonl"
            transcript.write_text(
                '{"role":"tool_start","tool":"list_directory","args":"{\\"path\\": \\"swarm-water-check-app\\"}"}\n',
                encoding="utf-8",
            )

            message = forbidden_transcript_access(transcript, ("water-check-app",))

            self.assertIsNone(message)

    def test_small_app_fast_path_detects_forbidden_discovery_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "reasonix-transcript.jsonl"
            transcript.write_text(
                '{"role":"tool_start","tool":"web_search","args":"{\\"query\\": \\"Expo hydration app design\\"}"}\n',
                encoding="utf-8",
            )

            message = acp_worker.small_app_fast_path_violation(
                transcript,
                "## Small App Fast Path\nDo not call web_search.\nDo not call explore.\n",
            )

            self.assertEqual(message, "small app fast path violation: web_search")


if __name__ == "__main__":
    unittest.main()
