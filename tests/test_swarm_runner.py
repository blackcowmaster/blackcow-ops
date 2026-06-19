from __future__ import annotations

import json
import signal
import tempfile
import unittest
import sys
from pathlib import Path

from scripts.blackcow_swarm_lib.config import validate_command_template
from scripts.blackcow_swarm_lib.reasonix_health import _default_command, run_reasonix_health_check
from scripts.blackcow_swarm_lib.retrying_runner import RetryingRunner
from scripts.blackcow_swarm_lib.runner import MockBehavior, MockRunner, ReasonixRunner, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.schema import validate_result


class TestMockRunner(unittest.TestCase):
    def make_task(self, workspace: Path, task_id: str = "qa-1") -> WorkerTask:
        prompt_file = workspace / "prompt.md"
        result_json = workspace / "result.json"
        prompt_file.write_text("Run QA", encoding="utf-8")
        return WorkerTask(
            task_id=task_id,
            replica_id=f"{task_id}-r1",
            skill="blackcow-qa",
            read_only=True,
            prompt_file=prompt_file,
            result_json=result_json,
            workspace=workspace,
            timeout_seconds=5,
            missing_result_fatal=False,
        )

    def test_success_result_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = MockRunner(MockBehavior(status="SUCCEEDED")).run(task)

            self.assertEqual(outcome.status, "SUCCEEDED")
            self.assertTrue(task.result_json.exists())
            validate_result(json.loads(task.result_json.read_text(encoding="utf-8")))

    def test_success_result_records_controller_timing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = MockRunner(MockBehavior(status="SUCCEEDED", delay_seconds=0.01)).run(task)

            payload = json.loads(task.result_json.read_text(encoding="utf-8"))

            self.assertEqual(payload["started_at"], outcome.started_at)
            self.assertEqual(payload["finished_at"], outcome.finished_at)
            self.assertLess(payload["started_at"], payload["finished_at"])

    def test_retryable_failure_result_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = MockRunner(MockBehavior(status="FAILED_RETRYABLE")).run(task)

            self.assertEqual(outcome.status, "FAILED_RETRYABLE")
            self.assertIn("mock_result_written", outcome.events)

    def test_timeout_and_slow_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = MockRunner(MockBehavior(status="TIMED_OUT", delay_seconds=0.01)).run(task)

            self.assertEqual(outcome.status, "TIMED_OUT")
            self.assertLess(outcome.started_at, outcome.finished_at)

    def test_malformed_json_becomes_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = MockRunner(MockBehavior(status="SUCCEEDED", malformed_json=True)).run(task)

            self.assertEqual(outcome.status, "FAILED_RETRYABLE")
            self.assertIn("invalid_result_json", outcome.events)

    def test_missing_result_json_becomes_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = MockRunner(MockBehavior(status="SUCCEEDED", omit_result=True)).run(task)

            self.assertEqual(outcome.status, "FAILED_RETRYABLE")
            self.assertIn("missing_result_json", outcome.events)


class TestReasonixRunner(unittest.TestCase):
    def make_task(self, workspace: Path) -> WorkerTask:
        prompt_file = workspace / "prompt.md"
        result_json = workspace / "result.json"
        prompt_file.write_text("Run QA", encoding="utf-8")
        return WorkerTask(
            task_id="qa-1",
            replica_id="qa-1-r1",
            skill="blackcow-qa",
            read_only=True,
            prompt_file=prompt_file,
            result_json=result_json,
            workspace=workspace,
            timeout_seconds=5,
            missing_result_fatal=False,
        )

    def test_command_substitution_is_argument_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            command = ReasonixRunner.default().build_command(task)

            self.assertIsInstance(command, tuple)
            self.assertEqual(command[0], "python3")
            self.assertIn("scripts/blackcow_reasonix_acp_worker.py", command)
            self.assertIn("blackcow-qa", command)
            self.assertIn(str(task.prompt_file), command)
            self.assertIn(str(task.result_json), command)
            self.assertIn("--read-only", command)
            self.assertIn("true", command)

    def test_rejects_unknown_placeholder(self) -> None:
        with self.assertRaisesRegex(ValueError, "mystery"):
            validate_command_template(("reasonix", "{skill}", "{prompt_file}", "{result_json}", "{mystery}"))

    def test_missing_result_json_records_retryable_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task = self.make_task(Path(temp_dir))
            outcome = ReasonixRunner.default().verify_result(task, events=("worker_exit_0",))

            self.assertEqual(outcome.status, "FAILED_RETRYABLE")
            self.assertIn("missing_result_json", outcome.events)

    def test_cancel_uses_process_group_termination(self) -> None:
        calls: list[tuple[int, int]] = []

        def fake_terminator(process_group_id: int, signal_number: int) -> None:
            calls.append((process_group_id, signal_number))

        runner = ReasonixRunner.default(process_terminator=fake_terminator)
        runner.record_process("qa-1-r1", pid=123, process_group_id=456)
        runner.cancel("qa-1-r1")

        self.assertEqual(calls, [(456, signal.SIGTERM)])

    def test_health_check_reports_session_new_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_acp = root / "fake_acp.py"
            fake_acp.write_text(
                "import json, sys, time\n"
                "for line in sys.stdin:\n"
                "    msg = json.loads(line)\n"
                "    if msg.get('method') == 'initialize':\n"
                "        expected = {'protocolVersion': 1, 'clientInfo': {'name': 'blackcow-swarm', 'version': '1'}}\n"
                "        if msg.get('params') != expected:\n"
                "            print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'error':{'message':'bad initialize params'}}), flush=True)\n"
                "        else:\n"
                "            print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':{'ok': True}}), flush=True)\n"
                "    elif msg.get('method') == 'session/new':\n"
                "        time.sleep(5)\n",
                encoding="utf-8",
            )

            result = run_reasonix_health_check(
                workspace=root,
                run_dir=root / "run",
                command=(sys.executable, str(fake_acp)),
                timeout_seconds=0.2,
            )

            self.assertFalse(result.ok)
            self.assertIn("session/new", result.summary)
            self.assertTrue(result.stderr_path.exists())
            self.assertLess(result.finished_at - result.started_at, 2.0)

    def test_health_check_default_disables_user_mcp_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            command = _default_command(root, root / "transcript.jsonl")

            self.assertIn("--mcp", command)
            self.assertEqual(command[command.index("--mcp") + 1], "")

    def test_health_check_can_probe_model_connectivity_without_task_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_log = root / "prompt.txt"
            fake_acp = root / "fake_acp.py"
            fake_acp.write_text(
                "import json, pathlib, sys\n"
                f"prompt_log = pathlib.Path({str(prompt_log)!r})\n"
                "for line in sys.stdin:\n"
                "    msg = json.loads(line)\n"
                "    method = msg.get('method')\n"
                "    if method == 'initialize':\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':{'ok': True}}), flush=True)\n"
                "    elif method == 'session/new':\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':{'sessionId':'s1'}}), flush=True)\n"
                "    elif method == 'session/prompt':\n"
                "        prompt_log.write_text(msg['params']['prompt'][0]['text'], encoding='utf-8')\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'error':{'message':'fetch failed'}}), flush=True)\n",
                encoding="utf-8",
            )

            result = run_reasonix_health_check(
                workspace=root,
                run_dir=root / "run",
                command=(sys.executable, str(fake_acp)),
                timeout_seconds=2.0,
                probe_model=True,
            )

            self.assertFalse(result.ok)
            self.assertIn("model preflight", result.summary)
            self.assertIn("fetch failed", result.summary)
            prompt = prompt_log.read_text(encoding="utf-8")
            self.assertIn("BlackCow Reasonix model connectivity preflight", prompt)
            self.assertNotIn(str(root), prompt)

    def test_health_check_reports_model_error_from_session_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_acp = root / "fake_acp.py"
            fake_acp.write_text(
                "import json, sys\n"
                "for line in sys.stdin:\n"
                "    msg = json.loads(line)\n"
                "    method = msg.get('method')\n"
                "    if method == 'initialize':\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':{'ok': True}}), flush=True)\n"
                "    elif method == 'session/new':\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':{'sessionId':'s1'}}), flush=True)\n"
                "    elif method == 'session/prompt':\n"
                "        print(json.dumps({'jsonrpc':'2.0','method':'session/update','params':{'update':{'metadata':{'error':{'message':'fetch failed'}}}}}), flush=True)\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':{'stopReason':'error'}}), flush=True)\n",
                encoding="utf-8",
            )

            result = run_reasonix_health_check(
                workspace=root,
                run_dir=root / "run",
                command=(sys.executable, str(fake_acp)),
                timeout_seconds=2.0,
                probe_model=True,
            )

            self.assertFalse(result.ok)
            self.assertIn("fetch failed", result.summary)


class SequenceRunner:
    def __init__(self, statuses: tuple[str, ...]) -> None:
        self.statuses = statuses
        self.calls = 0

    def run(self, task: WorkerTask) -> RunnerOutcome:
        status = self.statuses[min(self.calls, len(self.statuses) - 1)]
        self.calls += 1
        return RunnerOutcome(
            status=status,
            result_path=task.result_json,
            command=("sequence-runner",),
            started_at=float(self.calls),
            finished_at=float(self.calls),
            process=None,
            events=(f"status={status}",),
        )


class TestRetryingRunner(unittest.TestCase):
    def make_task(self, workspace: Path) -> WorkerTask:
        return WorkerTask(
            task_id="discovery-1",
            replica_id="discovery-1-r1",
            skill="blackcow-plan",
            read_only=True,
            prompt_file=workspace / "prompt.md",
            result_json=workspace / "result.json",
            workspace=workspace,
            timeout_seconds=5,
            missing_result_fatal=False,
        )

    def test_retries_retryable_worker_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = SequenceRunner(("FAILED_RETRYABLE", "SUCCEEDED"))

            outcome = RetryingRunner(runner, retry_limit=1).run(self.make_task(Path(temp_dir)))

            self.assertEqual(outcome.status, "SUCCEEDED")
            self.assertEqual(runner.calls, 2)
            self.assertIn("retry_attempts=1", outcome.events)

    def test_does_not_retry_final_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = SequenceRunner(("FAILED_FINAL", "SUCCEEDED"))

            outcome = RetryingRunner(runner, retry_limit=1).run(self.make_task(Path(temp_dir)))

            self.assertEqual(outcome.status, "FAILED_FINAL")
            self.assertEqual(runner.calls, 1)


if __name__ == "__main__":
    unittest.main()
