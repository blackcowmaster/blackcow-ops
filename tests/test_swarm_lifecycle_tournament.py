from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from scripts.blackcow_swarm_lib.acceptance_runner import AcceptanceResult
from scripts.blackcow_swarm_lib.config import JsonValue
from scripts.blackcow_swarm_lib.reasonix_health import ReasonixHealthResult
from scripts.blackcow_swarm_lib.scheduler import ScheduleReport, ScheduledTask, TaskInterval
from scripts.blackcow_swarm_lib.retrying_runner import RetryingRunner
from scripts.blackcow_swarm_lib.tournament import PatchCandidate, TournamentResult
from scripts.blackcow_swarm_lib.worktree import WorktreeError

import scripts.blackcow_swarm_lib.lifecycle as lifecycle
import scripts.blackcow_swarm_lib.lifecycle_completion as lifecycle_completion


@dataclass(frozen=True, slots=True)
class RunnerStub:
    name: str = "stub"


class TestLifecycleTournament(unittest.TestCase):
    def test_writer_patch_runs_acceptance_against_integration_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Given: a successful writer replica leaves a patch for tournament selection.
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_writer_graph("run-writer-applies")), encoding="utf-8")
            acceptance_roots: list[Path] = []

            class SuccessfulScheduler:
                def __init__(self, max_workers: int) -> None:
                    self.max_workers = max_workers

                def run(self, tasks: list[ScheduledTask], runner: RunnerStub, repo_root: Path, run_dir: Path) -> ScheduleReport:
                    patch_dir = run_dir / "patches"
                    patch_dir.mkdir(parents=True, exist_ok=True)
                    (patch_dir / "writer-1-r1.patch").write_text(
                        "diff --git a/app.txt b/app.txt\n"
                        "--- a/app.txt\n"
                        "+++ b/app.txt\n"
                        "@@ -1 +1 @@\n"
                        "-old\n"
                        "+new\n",
                        encoding="utf-8",
                    )
                    return ScheduleReport(
                        states={"writer-1-r1": "SUCCEEDED"},
                        intervals={"writer-1-r1": TaskInterval("writer-1-r1", 1.0, 2.0)},
                        events=[],
                    )

            class SuccessfulTournament:
                def __init__(self, repo_root: Path) -> None:
                    self.repo_root = repo_root

                def run(self, run_id: str, candidates: tuple[PatchCandidate, ...]) -> TournamentResult:
                    integration = self.repo_root / "integration"
                    integration.mkdir()
                    report = self.repo_root / ".omo" / "swarm" / "runs" / run_id / "reports" / "tournament.md"
                    report.parent.mkdir(parents=True, exist_ok=True)
                    report.write_text("# Tournament\n", encoding="utf-8")
                    return TournamentResult(candidates[0], report, integration, "checkpoint", {})

            def acceptance(
                checks: tuple[str, ...],
                *,
                project_root: Path,
                controller_root: Path | None = None,
                run_dir: Path,
            ) -> tuple[AcceptanceResult, ...]:
                acceptance_roots.append(project_root)
                return (
                    AcceptanceResult(
                        command=checks[0],
                        ok=True,
                        exit_code=0,
                        stdout_path=run_dir / "acceptance.out",
                        stderr_path=run_dir / "acceptance.err",
                        duration_seconds=0.01,
                    ),
                )

            # When: the Reasonix lifecycle completes.
            with (
                patch.object(lifecycle, "Scheduler", SuccessfulScheduler),
                patch.object(lifecycle.ReasonixRunner, "default", return_value=RunnerStub()),
                patch.object(lifecycle, "run_reasonix_health_check", _healthy_health),
                patch.object(lifecycle_completion, "PatchTournament", SuccessfulTournament),
                patch.object(lifecycle_completion, "run_acceptance_checks", acceptance),
            ):
                output = lifecycle.execute_reasonix_run(graph_path, None, project_root)

            # Then: acceptance proves the integrated candidate and the final judge records the winner.
            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(acceptance_roots, [project_root / "integration"])
            judgement = json.loads(Path(output["final_judgement"]).read_text(encoding="utf-8"))
            self.assertEqual(judgement["selected_patches"][0]["task_id"], "writer-1")
            self.assertEqual(judgement["selected_patches"][0]["replica_id"], "writer-1-r1")
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))
            self.assertEqual(state["tournament"]["selected_replica_id"], "writer-1-r1")

    def test_writer_success_without_applicable_patch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Given: a writer succeeds, but tournament cannot apply its patch cleanly.
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_writer_graph("run-writer-no-clean-patch")), encoding="utf-8")

            class SuccessfulScheduler:
                def __init__(self, max_workers: int) -> None:
                    self.max_workers = max_workers

                def run(self, tasks: list[ScheduledTask], runner: RunnerStub, repo_root: Path, run_dir: Path) -> ScheduleReport:
                    patch_dir = run_dir / "patches"
                    patch_dir.mkdir(parents=True, exist_ok=True)
                    (patch_dir / "writer-1-r1.patch").write_text("not a clean patch\n", encoding="utf-8")
                    return ScheduleReport(
                        states={"writer-1-r1": "SUCCEEDED"},
                        intervals={"writer-1-r1": TaskInterval("writer-1-r1", 1.0, 2.0)},
                        events=[],
                    )

            class FailingTournament:
                def __init__(self, repo_root: Path) -> None:
                    self.repo_root = repo_root

                def run(self, run_id: str, candidates: tuple[PatchCandidate, ...]) -> TournamentResult:
                    raise WorktreeError("no candidate patch applies cleanly")

            def acceptance(
                checks: tuple[str, ...],
                *,
                project_root: Path,
                controller_root: Path | None = None,
                run_dir: Path,
            ) -> tuple[AcceptanceResult, ...]:
                raise AssertionError("acceptance must not run without an applicable patch")

            # When: lifecycle reaches tournament selection.
            with (
                patch.object(lifecycle, "Scheduler", SuccessfulScheduler),
                patch.object(lifecycle.ReasonixRunner, "default", return_value=RunnerStub()),
                patch.object(lifecycle, "run_reasonix_health_check", _healthy_health),
                patch.object(lifecycle_completion, "PatchTournament", FailingTournament),
                patch.object(lifecycle_completion, "run_acceptance_checks", acceptance),
            ):
                output = lifecycle.execute_reasonix_run(graph_path, None, project_root)

            # Then: the run is failed and no selected patch is claimed.
            self.assertEqual(output["status"], "FAILED")
            judgement = json.loads(Path(output["final_judgement"]).read_text(encoding="utf-8"))
            self.assertEqual(judgement["selected_patches"], [])
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))
            self.assertEqual(state["tournament"]["status"], "FAILED")

    def test_writer_setup_failure_writes_failed_state_and_judgement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Given: a mock lifecycle run has a writer task whose worktree path is occupied.
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)
            (project_root / ".gitignore").write_text(".worktrees/\n.omo/swarm/runs/\n", encoding="utf-8")
            (project_root / "app.txt").write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore", "app.txt"], cwd=project_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
                cwd=project_root,
                check=True,
                capture_output=True,
            )
            occupied_path = project_root / ".worktrees" / "swarm" / "run-setup-lifecycle-failure" / "writer-1-r1"
            occupied_path.parent.mkdir(parents=True)
            occupied_path.write_text("not a worktree\n", encoding="utf-8")
            graph_path = Path(temp_dir) / "graph.json"
            graph_path.write_text(json.dumps(_writer_graph("run-setup-lifecycle-failure")), encoding="utf-8")

            # When: the mock lifecycle executes the graph.
            output = lifecycle.execute_mock_run(graph_path, None, project_root)

            # Then: lifecycle artifacts record a structured failed run.
            self.assertEqual(output["status"], "FAILED")
            state_path = Path(output["state"])
            judgement_path = Path(output["final_judgement"])
            self.assertTrue(state_path.exists())
            self.assertTrue(judgement_path.exists())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "FAILED")
            self.assertEqual(state["workers"]["writer-1-r1"]["status"], "FAILED_RETRYABLE")
            judgement = json.loads(judgement_path.read_text(encoding="utf-8"))
            self.assertEqual(judgement["status"], "FAILED")
            self.assertEqual(judgement["selected_patches"], [])


def _writer_graph(run_id: str) -> dict[str, JsonValue]:
    return {
        "run_id": run_id,
        "task": "Writer lifecycle",
        "mode": "coder",
        "intensity": "high",
        "policy": "auto",
        "requires_approval": False,
        "worker_swarm_allowed": True,
        "tasks": [
            {
                "id": "writer-1",
                "kind": "writer",
                "title": "Writer",
                "skill": "blackcow-loop",
                "prompt": "Patch the app",
                "depends_on": [],
                "read_only": False,
                "writes": ["app.txt"],
                "write_scope": ["app.txt"],
                "acceptance_checks": ["python3 -c 'print(\"ok\")'"],
                "replicas": 1,
                "max_replicas": 1,
                "timeout_minutes": 1,
            }
        ],
    }


def _healthy_health(workspace: Path, run_dir: Path, *, probe_model: bool = False) -> ReasonixHealthResult:
    health_dir = run_dir / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = health_dir / "stdout.log"
    stderr_path = health_dir / "stderr.log"
    transcript_path = health_dir / "transcript.jsonl"
    stdout_path.write_text("ok\n", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")
    transcript_path.write_text("", encoding="utf-8")
    return ReasonixHealthResult(
        ok=True,
        summary="reasonix acp health ok",
        started_at=1.0,
        finished_at=1.1,
        transcript_path=transcript_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


if __name__ == "__main__":
    unittest.main()
