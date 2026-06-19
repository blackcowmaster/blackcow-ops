from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.blackcow_swarm_lib.acceptance_runner import AcceptanceResult
from scripts.blackcow_swarm_lib.config import JsonValue
from scripts.blackcow_swarm_lib.lifecycle_scratch import _repair_tasks, execute_reasonix_scratch_run
from scripts.blackcow_swarm_lib.reasonix_health import ReasonixHealthResult
from scripts.blackcow_swarm_lib.runner import ProcessMetadata, RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.scheduler_types import ScheduledTask

import scripts.blackcow_swarm_lib.lifecycle_completion as lifecycle_completion
import scripts.blackcow_swarm_lib.lifecycle_scratch as lifecycle_scratch


class TestLifecycleScratch(unittest.TestCase):
    def test_repair_task_prompt_contains_acceptance_failure_and_full_regeneration_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stdout = root / "stdout.log"
            stderr = root / "stderr.log"
            stdout.write_text("tsconfig.json(2,14): error TS6053: File 'expo/tsconfig.base' not found.\n", encoding="utf-8")
            stderr.write_text("", encoding="utf-8")
            failed = AcceptanceResult(
                command="cd swarm-water-tabs-check && npm run typecheck",
                ok=False,
                exit_code=2,
                stdout_path=stdout,
                stderr_path=stderr,
                duration_seconds=0.5,
            )

            repair_tasks = _repair_tasks([_writer_task()], 1, (failed,))

            self.assertEqual(len(repair_tasks), 1)
            repair = repair_tasks[0]
            self.assertEqual(repair.task_id, "coder-1-repair1-r1")
            self.assertEqual(repair.replica_id, "coder-1-repair1-r1")
            self.assertIn("Acceptance Repair Feedback", repair.prompt)
            self.assertIn("complete replacement candidate", repair.prompt)
            self.assertIn("expo/tsconfig.base", repair.prompt)
            self.assertIn("no-install Expo/React Native scaffold checks", repair.prompt)
            self.assertIn("package.json, tsconfig.json, app.json, and DESIGN.md", repair.prompt)
            self.assertIn("useState", repair.prompt)
            self.assertIn("recursive export=", repair.prompt)
            self.assertEqual(repair.depends_on, ())
            self.assertFalse(repair.read_only)

    def test_repair_task_prompt_preserves_checks_that_already_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            passed_stdout = root / "passed.stdout.log"
            passed_stderr = root / "passed.stderr.log"
            failed_stdout = root / "failed.stdout.log"
            failed_stderr = root / "failed.stderr.log"
            passed_stdout.write_text("typecheck ok\n", encoding="utf-8")
            passed_stderr.write_text("", encoding="utf-8")
            failed_stdout.write_text("", encoding="utf-8")
            failed_stderr.write_text("missing design source\n", encoding="utf-8")
            passed = AcceptanceResult(
                command="cd swarm-water-test && npm run typecheck",
                ok=True,
                exit_code=0,
                stdout_path=passed_stdout,
                stderr_path=passed_stderr,
                duration_seconds=0.5,
            )
            failed = AcceptanceResult(
                command="python3 scripts/blackcow_design_gate.py --project swarm-water-test",
                ok=False,
                exit_code=1,
                stdout_path=failed_stdout,
                stderr_path=failed_stderr,
                duration_seconds=0.5,
            )

            repair_tasks = _repair_tasks([_writer_task()], 2, (passed, failed))

            self.assertEqual(len(repair_tasks), 1)
            prompt = repair_tasks[0].prompt
            self.assertIn("Previously passing acceptance checks to preserve", prompt)
            self.assertIn("cd swarm-water-test && npm run typecheck", prompt)
            self.assertIn("missing design source", prompt)

    def test_scratch_lifecycle_selects_repair_patch_after_acceptance_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = _init_repo(Path(temp_dir))
            graph_path = project_root / "graph.json"
            graph_path.write_text(json.dumps(_writer_graph("scratch-local-repair")), encoding="utf-8")
            acceptance_calls: list[Path] = []

            def acceptance(
                checks: tuple[str, ...],
                *,
                project_root: Path,
                controller_root: Path | None = None,
                run_dir: Path,
            ) -> tuple[AcceptanceResult, ...]:
                acceptance_calls.append(project_root)
                passed = len(acceptance_calls) == 2
                return (
                    AcceptanceResult(
                        command=checks[0],
                        ok=passed,
                        exit_code=0 if passed else 2,
                        stdout_path=run_dir / f"acceptance-{len(acceptance_calls)}.out",
                        stderr_path=run_dir / f"acceptance-{len(acceptance_calls)}.err",
                        duration_seconds=0.01,
                    ),
                )

            with (
                patch.object(lifecycle_scratch, "run_reasonix_health_check", _healthy_health),
                patch.object(lifecycle_scratch, "ScratchReasonixRunner", LocalScratchRunner),
                patch.object(lifecycle_completion, "run_acceptance_checks", acceptance),
            ):
                output = execute_reasonix_scratch_run(graph_path, None, project_root)

            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(len(acceptance_calls), 2)
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))
            self.assertEqual(state["tournament"]["selected_replica_id"], "writer-1-repair1-r1")
            self.assertEqual(state["workers"]["writer-1-repair1-r1"]["status"], "SUCCEEDED")
            judgement = json.loads(Path(output["final_judgement"]).read_text(encoding="utf-8"))
            self.assertEqual(judgement["selected_patches"][0]["replica_id"], "writer-1-repair1-r1")

    def test_scratch_lifecycle_copies_shared_context_from_task_graph_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = _init_repo(Path(temp_dir))
            plan_dir = project_root / ".omo" / "swarm" / "runs" / "planned-run"
            plan_dir.mkdir(parents=True)
            graph_path = plan_dir / "task_graph.json"
            graph_path.write_text(json.dumps(_writer_graph("planned-run")), encoding="utf-8")
            (plan_dir / "shared_context.md").write_text(
                "\n".join(
                    (
                        "## Design Source Gate",
                        "## Native Visual Gate",
                        "## Swarm Speed Gate",
                        "python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/planned-run --min-speedup 1.0",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            with (
                patch.object(lifecycle_scratch, "run_reasonix_health_check", _healthy_health),
                patch.object(lifecycle_scratch, "ScratchReasonixRunner", LocalScratchRunner),
            ):
                output = execute_reasonix_scratch_run(graph_path, "live-run", project_root)

            self.assertEqual(output["run_id"], "live-run")
            copied = project_root / ".omo" / "swarm" / "runs" / "live-run" / "shared_context.md"
            self.assertTrue(copied.exists())
            copied_text = copied.read_text(encoding="utf-8")
            self.assertIn("Design Source Gate", copied_text)
            self.assertIn(".omo/swarm/runs/live-run", copied_text)
            self.assertNotIn(".omo/swarm/runs/planned-run", copied_text)


class LocalScratchRunner:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def run(self, task: WorkerTask) -> RunnerOutcome:
        started_at = time.time()
        task.result_json.parent.mkdir(parents=True, exist_ok=True)
        if not task.read_only:
            value = "repair\n" if "repair1" in task.replica_id else "bad\n"
            (task.workspace / "app.txt").write_text(value, encoding="utf-8")
        task.result_json.write_text(json.dumps(_result(task)), encoding="utf-8")
        finished_at = time.time()
        return RunnerOutcome(
            status="SUCCEEDED",
            result_path=task.result_json,
            command=("local-scratch-runner", task.replica_id),
            started_at=started_at,
            finished_at=finished_at,
            process=ProcessMetadata(pid=0, process_group_id=0),
            events=("local_scratch_result_written",),
        )


def _writer_task() -> ScheduledTask:
    return ScheduledTask(
        task_id="coder-1",
        replica_id="coder-1-r1",
        kind="coder",
        skill="blackcow-loop",
        prompt="Create a fresh React Native Expo water app at swarm-water-tabs-check.",
        depends_on=("discovery-1",),
        read_only=False,
        writes=("**/*",),
        acceptance_checks=("cd swarm-water-tabs-check && npm run typecheck",),
        timeout_seconds=600,
    )


def _writer_graph(run_id: str) -> dict[str, JsonValue]:
    return {
        "run_id": run_id,
        "task": "Local scratch repair",
        "mode": "coder",
        "intensity": "normal",
        "policy": "auto",
        "requires_approval": False,
        "worker_swarm_allowed": True,
        "tasks": [
            {
                "id": "writer-1",
                "kind": "coder",
                "title": "Writer",
                "skill": "blackcow-loop",
                "prompt": "Patch app.txt",
                "depends_on": [],
                "read_only": False,
                "writes": ["app.txt"],
                "write_scope": ["app.txt"],
                "acceptance_checks": ["test app"],
                "replicas": 1,
                "max_replicas": 1,
                "timeout_minutes": 1,
            }
        ],
    }


def _init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / ".gitignore").write_text(".worktrees/\n.omo/swarm/runs/\n", encoding="utf-8")
    (repo / "app.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "app.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


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
        summary="reasonix scratch local health ok",
        started_at=1.0,
        finished_at=1.1,
        transcript_path=transcript_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


def _result(task: WorkerTask) -> dict[str, JsonValue]:
    return {
        "task_id": task.task_id,
        "replica_id": task.replica_id,
        "status": "SUCCEEDED",
        "summary": f"Local scratch result for {task.replica_id}",
        "artifacts": ["app.txt"],
        "changed_files": ["app.txt"],
        "patch_path": None,
        "score": {"overall": 90, "correctness": 90, "safety": 90, "tests": 90},
    }


if __name__ == "__main__":
    unittest.main()
