from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.config import JsonValue
from scripts.blackcow_swarm_lib.run_diagnostics import diagnose_run
from scripts.blackcow_swarm_lib.run_loop import execute_run_loop


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "scripts" / "blackcow_swarm.py"


class TestSwarmRunLoop(unittest.TestCase):
    def test_run_loop_stops_when_failure_signature_repeats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph = _task_graph(root, "loop-repeat")
            calls: list[str | None] = []

            def executor(task_graph_path: Path, run_id: str | None, project_root: Path) -> dict[str, JsonValue]:
                calls.append(run_id)
                if run_id is None:
                    raise AssertionError("run-loop must assign a concrete run id")
                _write_failed_retryable_run(project_root, run_id)
                return {"run_id": run_id, "status": "FAILED"}

            output = execute_run_loop(
                graph,
                base_run_id="loop-repeat",
                project_root=root,
                attempts=3,
                executor=executor,
            )

            self.assertEqual(len(calls), 2)
            self.assertEqual(output["status"], "FAILED")
            self.assertEqual(output["stopped_reason"], "repeated_failure_signature")
            self.assertEqual(len(output["attempts"]), 2)

    def test_run_loop_stops_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph = _task_graph(root, "loop-success")
            calls: list[str | None] = []

            def executor(task_graph_path: Path, run_id: str | None, project_root: Path) -> dict[str, JsonValue]:
                calls.append(run_id)
                if run_id is None:
                    raise AssertionError("run-loop must assign a concrete run id")
                if len(calls) == 1:
                    _write_failed_retryable_run(project_root, run_id)
                    return {"run_id": run_id, "status": "FAILED"}
                _write_success_run(project_root, run_id)
                return {"run_id": run_id, "status": "SUCCEEDED"}

            output = execute_run_loop(
                graph,
                base_run_id="loop-success",
                project_root=root,
                attempts=3,
                executor=executor,
            )

            self.assertEqual(len(calls), 2)
            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(output["stopped_reason"], "succeeded")

    def test_run_loop_retries_retryable_blocked_preflight_until_repeated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph = _task_graph(root, "loop-blocked")
            calls: list[str | None] = []

            def executor(task_graph_path: Path, run_id: str | None, project_root: Path) -> dict[str, JsonValue]:
                calls.append(run_id)
                if run_id is None:
                    raise AssertionError("run-loop must assign a concrete run id")
                _write_retryable_blocked_run(project_root, run_id)
                return {"run_id": run_id, "status": "BLOCKED"}

            output = execute_run_loop(
                graph,
                base_run_id="loop-blocked",
                project_root=root,
                attempts=3,
                executor=executor,
            )

            self.assertEqual(len(calls), 2)
            self.assertEqual(output["status"], "BLOCKED")
            self.assertEqual(output["stopped_reason"], "repeated_failure_signature")

    def test_diagnose_run_reports_failed_retryable_worker_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_failed_retryable_run(root, "diag-worker")

            diagnosis = diagnose_run(root, "diag-worker").to_json()

            self.assertTrue(diagnosis["retryable"])
            self.assertIn("coder-1-r1", str(diagnosis["summary"]))
            self.assertIn("FAILED_RETRYABLE", str(diagnosis["summary"]))
            self.assertIn("timeout", str(diagnosis["signature"]))

    def test_diagnose_run_marks_health_retryable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_retryable_blocked_run(root, "diag-blocked")

            diagnosis = diagnose_run(root, "diag-blocked").to_json()

            self.assertTrue(diagnosis["retryable"])
            self.assertIn("fetch failed", str(diagnosis["summary"]))

    def test_diagnose_run_reports_actionable_acceptance_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".omo" / "swarm" / "runs" / "diag-acceptance"
            acceptance_dir = run_dir / "acceptance"
            acceptance_dir.mkdir(parents=True)
            stdout = acceptance_dir / "03.stdout.log"
            stderr = acceptance_dir / "03.stderr.log"
            stdout.write_text(
                "\n".join(
                    (
                        "> swarm-water-test@1.0.0 typecheck",
                        "> tsc --noEmit",
                        "",
                        "src/screens/HomeScreen.tsx(1,17): error TS2305: Module 'react' has no exported member 'useState'.",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            stderr.write_text("", encoding="utf-8")
            state = {
                "run_id": "diag-acceptance",
                "status": "FAILED",
                "workers": {},
                "acceptance": [
                    {
                        "command": "cd swarm-water-test && npm run typecheck",
                        "status": "FAILED",
                        "exit_code": 2,
                        "stdout": str(stdout),
                        "stderr": str(stderr),
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            diagnosis = diagnose_run(root, "diag-acceptance").to_json()

            self.assertIn("TS2305", str(diagnosis["summary"]))
            self.assertNotIn("swarm-water-test@1.0.0", str(diagnosis["summary"]))

    def test_diagnose_run_prefers_retryable_repair_worker_over_stale_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / ".omo" / "swarm" / "runs" / "diag-repair-retry"
            worker_dir = run_dir / "workers" / "coder-1-repair1-r1"
            acceptance_dir = run_dir / "acceptance"
            worker_dir.mkdir(parents=True)
            acceptance_dir.mkdir()
            stdout = acceptance_dir / "03.stdout.log"
            stderr = acceptance_dir / "03.stderr.log"
            stdout.write_text("src/App.tsx(1,1): error TS2305: stale initial candidate error\n", encoding="utf-8")
            stderr.write_text("", encoding="utf-8")
            state = {
                "run_id": "diag-repair-retry",
                "status": "FAILED",
                "workers": {
                    "coder-1-r1": {"status": "SUCCEEDED", "started_at": 1.0, "finished_at": 2.0},
                    "coder-1-repair1-r1": {"status": "FAILED_RETRYABLE", "started_at": 3.0, "finished_at": 4.0},
                },
                "acceptance": [
                    {
                        "command": "cd swarm-water-test && npm run typecheck",
                        "status": "FAILED",
                        "exit_code": 2,
                        "stdout": str(stdout),
                        "stderr": str(stderr),
                    }
                ],
            }
            result = {
                "task_id": "coder-1-repair1-r1",
                "replica_id": "coder-1-repair1-r1",
                "status": "FAILED_RETRYABLE",
                "summary": "controller salvaged incomplete scratch files: missing native entry point",
                "artifacts": ["swarm-water-test/package.json"],
                "changed_files": ["swarm-water-test/package.json"],
                "patch_path": None,
                "score": {"overall": 50, "correctness": 50, "safety": 70, "tests": 0},
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
            (worker_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")

            diagnosis = diagnose_run(root, "diag-repair-retry").to_json()

            self.assertTrue(diagnosis["retryable"])
            self.assertIn("coder-1-repair1-r1", str(diagnosis["summary"]))
            self.assertIn("missing native entry point", str(diagnosis["summary"]))

    def test_cli_run_loop_succeeds_with_mock_runner(self) -> None:
        run_id = "swarm-unit-loop"
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "run-loop",
                    "--task-graph",
                    "tests/fixtures/task_graph.simple.json",
                    "--runner",
                    "mock",
                    "--run-id",
                    run_id,
                    "--attempts",
                    "2",
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "SUCCEEDED")
            self.assertEqual(payload["stopped_reason"], "succeeded")
            self.assertEqual(payload["attempts"][0]["run_id"], f"{run_id}-a1")
        finally:
            shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / f"{run_id}-a1", ignore_errors=True)


def _task_graph(root: Path, run_id: str) -> Path:
    path = root / "task_graph.json"
    path.write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    return path


def _write_failed_retryable_run(project_root: Path, run_id: str) -> None:
    run_dir = project_root / ".omo" / "swarm" / "runs" / run_id
    worker_dir = run_dir / "workers" / "coder-1-r1"
    worker_dir.mkdir(parents=True)
    state = {
        "run_id": run_id,
        "status": "FAILED",
        "workers": {
            "coder-1-r1": {"status": "FAILED_RETRYABLE", "started_at": 1.0, "finished_at": 86.0},
            "qa-1-r1": {"status": "BLOCKED", "started_at": 86.0, "finished_at": 86.0},
        },
        "acceptance": [],
    }
    result = {
        "task_id": "coder-1-r1",
        "replica_id": "coder-1-r1",
        "status": "FAILED_RETRYABLE",
        "summary": "controller salvaged partial scratch files after worker timeout; retry required",
        "artifacts": ["swarm-water-test/App.tsx"],
        "changed_files": ["swarm-water-test/App.tsx"],
        "patch_path": None,
        "score": {"overall": 50, "correctness": 50, "safety": 70, "tests": 0},
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (worker_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")


def _write_success_run(project_root: Path, run_id: str) -> None:
    run_dir = project_root / ".omo" / "swarm" / "runs" / run_id
    run_dir.mkdir(parents=True)
    state = {"run_id": run_id, "status": "SUCCEEDED", "workers": {}, "acceptance": []}
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")


def _write_retryable_blocked_run(project_root: Path, run_id: str) -> None:
    run_dir = project_root / ".omo" / "swarm" / "runs" / run_id
    health_dir = run_dir / "health"
    health_dir.mkdir(parents=True)
    state = {"run_id": run_id, "status": "BLOCKED", "workers": {}}
    final = {
        "run_id": run_id,
        "status": "BLOCKED",
        "summary": "Reasonix scratch run BLOCKED: reasonix acp health failed: model preflight failed: fetch failed",
        "selected_patches": [],
        "score": {"overall": 0, "correctness": 0, "safety": 0, "tests": 0},
    }
    update = {
        "jsonrpc": "2.0",
        "method": "session/update",
        "params": {
            "update": {
                "content": {
                    "metadata": {
                        "error": {
                            "message": "fetch failed",
                            "retryable": True,
                        }
                    }
                }
            }
        },
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (run_dir / "final_judgement.json").write_text(json.dumps(final), encoding="utf-8")
    (health_dir / "stdout.log").write_text(json.dumps(update) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
