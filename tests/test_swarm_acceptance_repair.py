from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.blackcow_swarm_lib.acceptance_runner import AcceptanceResult
from scripts.blackcow_swarm_lib.lifecycle_completion import RepairSchedule, complete_run
from scripts.blackcow_swarm_lib.scheduler_types import ScheduledTask, ScheduleReport, TaskInterval
from scripts.blackcow_swarm_lib.state import RunStore
from scripts.blackcow_swarm_lib.tournament import PatchCandidate, TournamentResult

import scripts.blackcow_swarm_lib.lifecycle_completion as lifecycle_completion


class TestAcceptanceRepair(unittest.TestCase):
    def test_acceptance_failure_can_run_repair_schedule_before_final_judgement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            run_dir = project_root / ".omo" / "swarm" / "runs" / "run-repair"
            initial_task = _writer_task("writer-1", "writer-1-r1", "Patch the app")
            initial_report = _report("writer-1-r1")
            _write_patch(run_dir, "writer-1-r1")
            acceptance_roots: list[Path] = []

            class RecordingTournament:
                calls: list[tuple[str, ...]] = []

                def __init__(self, repo_root: Path) -> None:
                    self.repo_root = repo_root

                def run(self, run_id: str, candidates: tuple[PatchCandidate, ...]) -> TournamentResult:
                    self.calls.append(tuple(candidate.replica_id for candidate in candidates))
                    winner = candidates[-1]
                    integration = self.repo_root / f"integration-{len(self.calls)}"
                    integration.mkdir()
                    report = run_dir / "reports" / f"tournament-{len(self.calls)}.md"
                    report.parent.mkdir(parents=True, exist_ok=True)
                    report.write_text("# Tournament\n", encoding="utf-8")
                    return TournamentResult(winner, report, integration, f"checkpoint-{len(self.calls)}", {})

            def acceptance(
                checks: tuple[str, ...],
                *,
                project_root: Path,
                controller_root: Path | None = None,
                run_dir: Path,
            ) -> tuple[AcceptanceResult, ...]:
                acceptance_roots.append(project_root)
                passed = len(acceptance_roots) == 2
                return (
                    AcceptanceResult(
                        command=checks[0],
                        ok=passed,
                        exit_code=0 if passed else 2,
                        stdout_path=run_dir / f"acceptance-{len(acceptance_roots)}.out",
                        stderr_path=run_dir / f"acceptance-{len(acceptance_roots)}.err",
                        duration_seconds=0.01,
                    ),
                )

            def repair(*, attempt: int, acceptance_results: tuple[AcceptanceResult, ...]) -> RepairSchedule | None:
                self.assertEqual(attempt, 1)
                self.assertFalse(acceptance_results[0].ok)
                repair_task = _writer_task("writer-1-repair1", "writer-1-repair1-r1", "Patch the app with feedback")
                _write_patch(run_dir, "writer-1-repair1-r1")
                return RepairSchedule(tasks=[repair_task], report=_report("writer-1-repair1-r1"))

            with (
                patch.object(lifecycle_completion, "PatchTournament", RecordingTournament),
                patch.object(lifecycle_completion, "run_acceptance_checks", acceptance),
            ):
                output = complete_run(
                    checks=("npm run typecheck",),
                    safe_run_id="run-repair",
                    run_dir=run_dir,
                    store=RunStore(run_dir),
                    tasks=[initial_task],
                    report=initial_report,
                    project_root=project_root,
                    summary_prefix="Reasonix scratch run",
                    acceptance_repair=repair,
                )

            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(RecordingTournament.calls, [("writer-1-r1",), ("writer-1-repair1-r1",)])
            self.assertEqual(acceptance_roots, [project_root / "integration-1", project_root / "integration-2"])
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))
            self.assertEqual(state["workers"]["writer-1-repair1-r1"]["status"], "SUCCEEDED")
            judgement = json.loads(Path(output["final_judgement"]).read_text(encoding="utf-8"))
            self.assertEqual(judgement["selected_patches"][0]["replica_id"], "writer-1-repair1-r1")

    def test_acceptance_repair_can_use_latest_failure_for_second_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            run_dir = project_root / ".omo" / "swarm" / "runs" / "run-repair-again"
            initial_task = _writer_task("writer-1", "writer-1-r1", "Patch the app")
            initial_report = _report("writer-1-r1")
            _write_patch(run_dir, "writer-1-r1")
            acceptance_roots: list[Path] = []
            repair_attempts: list[int] = []

            class RecordingTournament:
                calls: list[tuple[str, ...]] = []

                def __init__(self, repo_root: Path) -> None:
                    self.repo_root = repo_root

                def run(self, run_id: str, candidates: tuple[PatchCandidate, ...]) -> TournamentResult:
                    self.calls.append(tuple(candidate.replica_id for candidate in candidates))
                    winner = candidates[-1]
                    integration = self.repo_root / f"integration-{len(self.calls)}"
                    integration.mkdir()
                    report = run_dir / "reports" / f"tournament-{len(self.calls)}.md"
                    report.parent.mkdir(parents=True, exist_ok=True)
                    report.write_text("# Tournament\n", encoding="utf-8")
                    return TournamentResult(winner, report, integration, f"checkpoint-{len(self.calls)}", {})

            def acceptance(
                checks: tuple[str, ...],
                *,
                project_root: Path,
                controller_root: Path | None = None,
                run_dir: Path,
            ) -> tuple[AcceptanceResult, ...]:
                acceptance_roots.append(project_root)
                passed = len(acceptance_roots) == 3
                return (
                    AcceptanceResult(
                        command=checks[0],
                        ok=passed,
                        exit_code=0 if passed else 2,
                        stdout_path=run_dir / f"acceptance-{len(acceptance_roots)}.out",
                        stderr_path=run_dir / f"acceptance-{len(acceptance_roots)}.err",
                        duration_seconds=0.01,
                    ),
                )

            def repair(*, attempt: int, acceptance_results: tuple[AcceptanceResult, ...]) -> RepairSchedule | None:
                self.assertFalse(acceptance_results[0].ok)
                repair_attempts.append(attempt)
                repair_task = _writer_task(
                    f"writer-1-repair{attempt}",
                    f"writer-1-repair{attempt}-r1",
                    f"Patch the app with feedback attempt {attempt}",
                )
                _write_patch(run_dir, f"writer-1-repair{attempt}-r1")
                return RepairSchedule(tasks=[repair_task], report=_report(f"writer-1-repair{attempt}-r1"))

            with (
                patch.object(lifecycle_completion, "PatchTournament", RecordingTournament),
                patch.object(lifecycle_completion, "run_acceptance_checks", acceptance),
            ):
                output = complete_run(
                    checks=("npm run typecheck",),
                    safe_run_id="run-repair-again",
                    run_dir=run_dir,
                    store=RunStore(run_dir),
                    tasks=[initial_task],
                    report=initial_report,
                    project_root=project_root,
                    summary_prefix="Reasonix scratch run",
                    acceptance_repair=repair,
                )

            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(repair_attempts, [1, 2])
            self.assertEqual(
                RecordingTournament.calls,
                [("writer-1-r1",), ("writer-1-repair1-r1",), ("writer-1-repair2-r1",)],
            )
            self.assertEqual(
                acceptance_roots,
                [project_root / "integration-1", project_root / "integration-2", project_root / "integration-3"],
            )
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))
            self.assertEqual(
                state["acceptance_repair"],
                [{"attempt": 1, "worker_status": "SUCCEEDED"}, {"attempt": 2, "worker_status": "SUCCEEDED"}],
            )

    def test_acceptance_repair_writes_running_state_before_worker_executes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            project_root.mkdir()
            run_dir = project_root / ".omo" / "swarm" / "runs" / "run-repair-running"
            initial_task = _writer_task("writer-1", "writer-1-r1", "Patch the app")
            initial_report = _report("writer-1-r1")
            _write_patch(run_dir, "writer-1-r1")

            class RecordingTournament:
                def __init__(self, repo_root: Path) -> None:
                    self.repo_root = repo_root

                def run(self, run_id: str, candidates: tuple[PatchCandidate, ...]) -> TournamentResult:
                    winner = candidates[-1]
                    integration = self.repo_root / "integration"
                    integration.mkdir()
                    report = run_dir / "reports" / "tournament.md"
                    report.parent.mkdir(parents=True, exist_ok=True)
                    report.write_text("# Tournament\n", encoding="utf-8")
                    return TournamentResult(winner, report, integration, "checkpoint", {})

            def acceptance(
                checks: tuple[str, ...],
                *,
                project_root: Path,
                controller_root: Path | None = None,
                run_dir: Path,
            ) -> tuple[AcceptanceResult, ...]:
                return (
                    AcceptanceResult(
                        command=checks[0],
                        ok=False,
                        exit_code=2,
                        stdout_path=run_dir / "acceptance.out",
                        stderr_path=run_dir / "acceptance.err",
                        duration_seconds=0.01,
                    ),
                )

            def repair(*, attempt: int, acceptance_results: tuple[AcceptanceResult, ...]) -> RepairSchedule | None:
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "ACCEPTANCE_REPAIR_RUNNING")
                self.assertEqual(state["acceptance_repair"], [{"attempt": 1, "worker_status": "RUNNING"}])
                self.assertEqual(state["acceptance"][0]["status"], "FAILED")
                return None

            with (
                patch.object(lifecycle_completion, "PatchTournament", RecordingTournament),
                patch.object(lifecycle_completion, "run_acceptance_checks", acceptance),
            ):
                output = complete_run(
                    checks=("npm run typecheck",),
                    safe_run_id="run-repair-running",
                    run_dir=run_dir,
                    store=RunStore(run_dir),
                    tasks=[initial_task],
                    report=initial_report,
                    project_root=project_root,
                    summary_prefix="Reasonix scratch run",
                    acceptance_repair=repair,
                )

            self.assertEqual(output["status"], "FAILED")


def _writer_task(task_id: str, replica_id: str, prompt: str) -> ScheduledTask:
    return ScheduledTask(
        task_id=task_id,
        replica_id=replica_id,
        kind="writer",
        skill="blackcow-loop",
        prompt=prompt,
        depends_on=(),
        read_only=False,
        writes=("app.txt",),
        acceptance_checks=("npm run typecheck",),
        timeout_seconds=60,
    )


def _report(replica_id: str) -> ScheduleReport:
    return ScheduleReport(
        states={replica_id: "SUCCEEDED"},
        intervals={replica_id: TaskInterval(replica_id, 1.0, 2.0)},
        events=[],
    )


def _write_patch(run_dir: Path, replica_id: str) -> None:
    patch_dir = run_dir / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    (patch_dir / f"{replica_id}.patch").write_text(
        "diff --git a/app.txt b/app.txt\n"
        "--- a/app.txt\n"
        "+++ b/app.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
