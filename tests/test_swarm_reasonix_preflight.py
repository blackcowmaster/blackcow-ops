from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.blackcow_swarm_lib.config import JsonValue
from scripts.blackcow_swarm_lib.reasonix_health import ReasonixHealthResult
from scripts.blackcow_swarm_lib.retrying_runner import RetryingRunner
from scripts.blackcow_swarm_lib.scheduler import ScheduleReport, ScheduledTask, TaskInterval

import scripts.blackcow_swarm_lib.lifecycle as lifecycle


class RunnerStub:
    name = "stub"


class TestReasonixPreflight(unittest.TestCase):
    def test_reasonix_lifecycle_wraps_runner_with_retry_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_qa_graph("run-retry-wrapper")), encoding="utf-8")
            observed_retry_limits: list[int] = []

            class InspectingScheduler:
                def __init__(self, max_workers: int) -> None:
                    self.max_workers = max_workers

                def run(self, tasks: list[ScheduledTask], runner: RetryingRunner, repo_root: Path, run_dir: Path) -> ScheduleReport:
                    if not isinstance(runner, RetryingRunner):
                        raise AssertionError(f"runner is not RetryingRunner: {type(runner).__name__}")
                    observed_retry_limits.append(runner.retry_limit)
                    return ScheduleReport(
                        states={"qa-1-r1": "SUCCEEDED"},
                        intervals={"qa-1-r1": TaskInterval("qa-1-r1", 1.0, 2.0)},
                        events=[],
                    )

            with (
                patch.object(lifecycle, "Scheduler", InspectingScheduler),
                patch.object(lifecycle.ReasonixRunner, "default", return_value=RunnerStub()),
                patch.object(lifecycle, "run_reasonix_health_check", _healthy_health),
            ):
                output = lifecycle.execute_reasonix_run(graph_path, None, project_root)

            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(observed_retry_limits, [1])

    def test_reasonix_lifecycle_probes_model_before_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_qa_graph("run-model-preflight")), encoding="utf-8")
            observed_probe_model: list[bool] = []

            class PassingScheduler:
                def __init__(self, max_workers: int) -> None:
                    self.max_workers = max_workers

                def run(self, tasks: list[ScheduledTask], runner: RetryingRunner, repo_root: Path, run_dir: Path) -> ScheduleReport:
                    return ScheduleReport(
                        states={"qa-1-r1": "SUCCEEDED"},
                        intervals={"qa-1-r1": TaskInterval("qa-1-r1", 1.0, 2.0)},
                        events=[],
                    )

            def health_with_probe_observation(
                workspace: Path,
                run_dir: Path,
                *,
                probe_model: bool = False,
            ) -> ReasonixHealthResult:
                observed_probe_model.append(probe_model)
                return _healthy_health(workspace, run_dir)

            with (
                patch.object(lifecycle, "Scheduler", PassingScheduler),
                patch.object(lifecycle.ReasonixRunner, "default", return_value=RunnerStub()),
                patch.object(lifecycle, "run_reasonix_health_check", health_with_probe_observation),
            ):
                output = lifecycle.execute_reasonix_run(graph_path, None, project_root)

            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(observed_probe_model, [True])

    def test_unhealthy_preflight_blocks_before_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_qa_graph("run-health-blocked")), encoding="utf-8")

            class SchedulerMustNotRun:
                def __init__(self, max_workers: int) -> None:
                    self.max_workers = max_workers

                def run(self, tasks: list[ScheduledTask], runner: RetryingRunner, repo_root: Path, run_dir: Path) -> ScheduleReport:
                    raise AssertionError("scheduler must not run when Reasonix preflight fails")

            with (
                patch.object(lifecycle, "Scheduler", SchedulerMustNotRun),
                patch.object(lifecycle, "run_reasonix_health_check", _unhealthy_health),
            ):
                output = lifecycle.execute_reasonix_run(graph_path, None, project_root)

            self.assertEqual(output["status"], "BLOCKED")
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))
            judgement = json.loads(Path(output["final_judgement"]).read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "BLOCKED")
            self.assertEqual(state["workers"], {})
            self.assertIn("session/new", judgement["summary"])
            self.assertFalse((project_root / ".omo" / "swarm" / "runs" / "run-health-blocked" / "workers").exists())

    def test_failed_reasonix_run_summarizes_worker_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_qa_graph("run-stderr-summary")), encoding="utf-8")

            class FailingScheduler:
                def __init__(self, max_workers: int) -> None:
                    self.max_workers = max_workers

                def run(self, tasks: list[ScheduledTask], runner: RetryingRunner, repo_root: Path, run_dir: Path) -> ScheduleReport:
                    worker_dir = run_dir / "workers" / "qa-1-r1"
                    worker_dir.mkdir(parents=True, exist_ok=True)
                    (worker_dir / "stderr.log").write_text(
                        "reasonix acp worker failed: reasonix acp timed out waiting for session/new\n",
                        encoding="utf-8",
                    )
                    return ScheduleReport(
                        states={"qa-1-r1": "FAILED_RETRYABLE"},
                        intervals={"qa-1-r1": TaskInterval("qa-1-r1", 1.0, 2.0)},
                        events=[],
                    )

            with (
                patch.object(lifecycle, "Scheduler", FailingScheduler),
                patch.object(lifecycle.ReasonixRunner, "default", return_value=RunnerStub()),
                patch.object(lifecycle, "run_reasonix_health_check", _healthy_health),
            ):
                output = lifecycle.execute_reasonix_run(graph_path, None, project_root)

            judgement = json.loads(Path(output["final_judgement"]).read_text(encoding="utf-8"))
            self.assertIn("session/new", judgement["summary"])


def _healthy_health(workspace: Path, run_dir: Path, *, probe_model: bool = False) -> ReasonixHealthResult:
    return _health(run_dir, ok=True, summary="reasonix acp health ok", stderr="")


def _unhealthy_health(workspace: Path, run_dir: Path, *, probe_model: bool = False) -> ReasonixHealthResult:
    return _health(
        run_dir,
        ok=False,
        summary="reasonix acp health failed: reasonix acp timed out waiting for session/new",
        stderr="reasonix acp timed out waiting for session/new\n",
    )


def _health(run_dir: Path, *, ok: bool, summary: str, stderr: str) -> ReasonixHealthResult:
    health_dir = run_dir / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = health_dir / "stdout.log"
    stderr_path = health_dir / "stderr.log"
    transcript_path = health_dir / "transcript.jsonl"
    stdout_path.write_text("ok\n" if ok else "", encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    transcript_path.write_text("", encoding="utf-8")
    return ReasonixHealthResult(ok, summary, 1.0, 1.1, transcript_path, stdout_path, stderr_path)


def _qa_graph(run_id: str) -> dict[str, JsonValue]:
    return {
        "run_id": run_id,
        "task": "QA lifecycle",
        "mode": "qa",
        "intensity": "normal",
        "policy": "auto",
        "requires_approval": False,
        "worker_swarm_allowed": False,
        "tasks": [
            {
                "id": "qa-1",
                "kind": "qa",
                "title": "QA",
                "skill": "blackcow-qa",
                "prompt": "Run QA",
                "depends_on": [],
                "read_only": True,
                "writes": [],
                "write_scope": [],
                "acceptance_checks": [],
                "replicas": 1,
                "max_replicas": 1,
                "timeout_minutes": 1,
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
