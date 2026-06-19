from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.runner import RunnerOutcome, WorkerTask
from scripts.blackcow_swarm_lib.schema import validate_result
from scripts.blackcow_swarm_lib.lifecycle_graph import acceptance_checks
from scripts.blackcow_swarm_lib.scratch_runner import (
    ENTRYPOINT_REPAIR_TIMEOUT_SECONDS,
    SCRATCH_TIMEOUT_SECONDS,
    ScratchReasonixRunner,
    build_scratch_worker_prompt,
    copy_generated_files,
    write_salvaged_result_if_needed,
)
from scripts.blackcow_swarm_lib.scratch_safety import (
    ScratchExportSafetyError,
    assert_external_safe_scratch_payload,
)


class TestScratchRunner(unittest.TestCase):
    def test_scratch_prompt_excludes_private_skill_source_and_keeps_app_contract(self) -> None:
        # Given: the normal worker prompt contains private embedded skill context.
        full_prompt = "\n".join(
            (
                "# BlackCow Skill-Backed Swarm Worker",
                "## Original Assignment",
                "Create a fresh React Native Expo water-drinking check app at swarm-water-tabs-check.",
                "Include bottom tab navigation, DESIGN.md, native visual QA, and speed evidence.",
                "",
                "## Shared Swarm Context",
                "## Design Source Gate",
                "Use getdesign.kr or a concrete DESIGN.md source before implementation.",
                "## Native Visual Gate",
                "Capture native simulator screenshots before accepting UI work.",
                "",
                "## Active Skill Source",
                "PRIVATE BLACKCOW LOOP SOURCE SECRET",
                "",
                "## Required Acceptance Checks",
                "- cd swarm-water-tabs-check && npm run typecheck",
                "- python3 scripts/blackcow_design_gate.py --project swarm-water-tabs-check",
            )
        )

        # When: an external-safe scratch prompt is built for Reasonix.
        prompt = build_scratch_worker_prompt(
            full_prompt,
            result_json=Path("/tmp/scratch/.blackcow/result.json"),
            task_id="coder-1",
            replica_id="coder-1-r1",
        )

        # Then: only public task requirements and output schema instructions remain.
        self.assertIn("React Native Expo water-drinking check app", prompt)
        self.assertIn("bottom tab navigation", prompt)
        self.assertIn("DESIGN.md", prompt)
        self.assertIn("native visual QA", prompt)
        self.assertIn("cd swarm-water-tabs-check && npm run typecheck", prompt)
        self.assertIn("/tmp/scratch/.blackcow/result.json", prompt)
        self.assertIn("Do not install dependencies", prompt)
        self.assertIn("Mandatory Expo/RN file order", prompt)
        self.assertIn("Minimum complete candidate", prompt)
        self.assertIn("no-install-clean", prompt)
        self.assertIn("expo/tsconfig.base", prompt)
        self.assertIn("App.tsx or app/_layout.tsx must exist", prompt)
        self.assertIn("useState", prompt)
        self.assertIn("recursive export=", prompt)
        self.assertIn("Controller Shared Context", prompt)
        self.assertIn("Design Source Gate", prompt)
        self.assertIn("Native Visual Gate", prompt)
        self.assertIn("Write the result JSON immediately after creating files", prompt)
        self.assertNotIn("PRIVATE BLACKCOW LOOP SOURCE SECRET", prompt)
        self.assertNotIn("Active Skill Source", prompt)

    def test_scratch_prompt_keeps_sanitized_acceptance_repair_feedback(self) -> None:
        full_prompt = "\n".join(
            (
                "# BlackCow Skill-Backed Swarm Worker",
                "## Original Assignment",
                "Create a fresh React Native Expo water app at swarm-water-tabs-check.",
                "",
                "## Required Acceptance Checks",
                "- python3 scripts/blackcow_expo_clean_gate.py --project swarm-water-tabs-check",
                "",
                "## Acceptance Repair Feedback",
                "Repair attempt: 1",
                "Command: python3 scripts/blackcow_expo_clean_gate.py --project swarm-water-tabs-check",
                "Stderr excerpt:",
                "/Users/alice/Project/blackcow-ops/.worktrees/swarm/run/integration/scripts/blackcow_expo_clean_gate.py: missing",
            )
        )

        prompt = build_scratch_worker_prompt(
            full_prompt,
            result_json=Path("/tmp/scratch/.blackcow/result.json"),
            task_id="coder-1-repair1",
            replica_id="coder-1-repair1-r1",
        )

        self.assertIn("Acceptance Repair Feedback", prompt)
        self.assertIn("blackcow_expo_clean_gate.py", prompt)
        self.assertNotIn("/Users/alice", prompt)
        self.assertNotIn(".worktrees/swarm", prompt)

    def test_scratch_prompt_keeps_repair_failures_after_passed_checks(self) -> None:
        full_prompt = "\n".join(
            (
                "# BlackCow Skill-Backed Swarm Worker",
                "## Original Assignment",
                "Create a fresh React Native Expo water app at swarm-water-tabs-check.",
                "",
                "## Required Acceptance Checks",
                "- cd swarm-water-tabs-check && npm run typecheck",
                "",
                "## Acceptance Repair Feedback",
                "Repair attempt: 1",
                "### Previously passing acceptance checks to preserve",
                "- python3 scripts/blackcow_expo_clean_gate.py --project swarm-water-tabs-check",
                "### Failed check 1",
                "Command: cd swarm-water-tabs-check && npm run typecheck",
                "Stdout excerpt:",
                "src/App.tsx(1,17): error TS2305: Module 'react' has no exported member 'useState'.",
            )
        )

        prompt = build_scratch_worker_prompt(
            full_prompt,
            result_json=Path("/tmp/scratch/.blackcow/result.json"),
            task_id="coder-1-repair1",
            replica_id="coder-1-repair1-r1",
        )

        self.assertIn("Previously passing acceptance checks", prompt)
        self.assertIn("Failed check 1", prompt)
        self.assertIn("TS2305", prompt)

    def test_scratch_timeout_cap_matches_small_app_worker_budget(self) -> None:
        self.assertLessEqual(SCRATCH_TIMEOUT_SECONDS, 90)

    def test_scratch_safety_accepts_sanitized_prompt_and_external_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "repo"
            scratch = root / "scratch" / "coder-1-r1"
            result_json = scratch / ".blackcow" / "result.json"
            project_root.mkdir()
            scratch.mkdir(parents=True)
            prompt = build_scratch_worker_prompt(
                "## Original Assignment\nCreate a compact Expo water tracker.",
                result_json=result_json,
                task_id="coder-1",
                replica_id="coder-1-r1",
            )

            assert_external_safe_scratch_payload(
                prompt,
                scratch=scratch,
                result_json=result_json,
                project_root=project_root,
            )

    def test_scratch_prompt_acceptance_checks_do_not_expose_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "repo"
            scratch = root / "scratch" / "coder-1-r1"
            result_json = scratch / ".blackcow" / "result.json"
            project_root.mkdir()
            scratch.mkdir(parents=True)
            graph = {
                "tasks": [
                    {
                        "id": "coder-1",
                        "kind": "coder",
                        "skill": "blackcow-coder",
                        "prompt": "Create the app.",
                        "read_only": False,
                        "depends_on": [],
                        "writes": ["swarm-water-test/**"],
                        "replicas": 1,
                        "timeout_minutes": 10,
                        "acceptance_checks": [
                            "python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/water-scratch-test-v7 --min-speedup 1.0",
                        ],
                    }
                ],
            }
            checks = acceptance_checks(
                graph,
                run_dir=project_root / ".omo" / "swarm" / "runs" / "water-scratch-test-v13-live-a1",
                project_root=project_root,
            )
            full_prompt = "\n".join(
                (
                    "# BlackCow Skill-Backed Swarm Worker",
                    "## Original Assignment",
                    "Create a fresh React Native Expo water app at swarm-water-test.",
                    "",
                    "## Required Acceptance Checks",
                    *checks,
                )
            )

            prompt = build_scratch_worker_prompt(
                full_prompt,
                result_json=result_json,
                task_id="coder-1",
                replica_id="coder-1-r1",
            )

            self.assertIn(".omo/swarm/runs/water-scratch-test-v13-live-a1", prompt)
            self.assertNotIn(str(project_root), prompt)
            assert_external_safe_scratch_payload(
                prompt,
                scratch=scratch,
                result_json=result_json,
                project_root=project_root,
            )

    def test_scratch_safety_rejects_private_prompt_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "repo"
            scratch = root / "scratch"
            result_json = scratch / ".blackcow" / "result.json"
            project_root.mkdir()
            scratch.mkdir(parents=True)
            prompt = "\n".join(("## Active Skill Source", str(project_root), "PRIVATE BLACKCOW LOOP SOURCE SECRET"))

            with self.assertRaisesRegex(ScratchExportSafetyError, "private marker"):
                assert_external_safe_scratch_payload(
                    prompt,
                    scratch=scratch,
                    result_json=result_json,
                    project_root=project_root,
                )

    def test_scratch_safety_rejects_workspace_inside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            scratch = project_root / ".omo" / "scratch"
            result_json = scratch / ".blackcow" / "result.json"
            scratch.mkdir(parents=True)

            with self.assertRaisesRegex(ScratchExportSafetyError, "outside project root"):
                assert_external_safe_scratch_payload(
                    "safe prompt",
                    scratch=scratch,
                    result_json=result_json,
                    project_root=project_root,
                )

    def test_scratch_safety_rejects_result_path_outside_scratch_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "repo"
            scratch = root / "scratch"
            result_json = root / "elsewhere" / "result.json"
            project_root.mkdir()
            scratch.mkdir()

            with self.assertRaisesRegex(ScratchExportSafetyError, "result JSON"):
                assert_external_safe_scratch_payload(
                    "safe prompt",
                    scratch=scratch,
                    result_json=result_json,
                    project_root=project_root,
                )

    def test_scratch_copy_excludes_dependency_and_build_artifacts(self) -> None:
        # Given: a scratch workspace contains source files plus generated dependency/build output.
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as destination_dir:
            source_root = Path(source_dir)
            destination = Path(destination_dir)
            (source_root / "swarm-water-tabs-check" / "src").mkdir(parents=True)
            (source_root / "swarm-water-tabs-check" / "src" / "App.tsx").write_text("app\n", encoding="utf-8")
            (source_root / "swarm-water-tabs-check" / "node_modules").mkdir()
            (source_root / "swarm-water-tabs-check" / "node_modules" / "dep.js").write_text("dep\n", encoding="utf-8")
            (source_root / "swarm-water-tabs-check" / ".expo").mkdir()
            (source_root / "swarm-water-tabs-check" / ".expo" / "state.json").write_text("{}\n", encoding="utf-8")

            # When: generated files are copied back into the integration worktree.
            copy_generated_files(source_root, destination)

            # Then: source files are preserved while heavy generated artifacts are dropped.
            self.assertTrue((destination / "swarm-water-tabs-check" / "src" / "App.tsx").exists())
            self.assertFalse((destination / "swarm-water-tabs-check" / "node_modules").exists())
            self.assertFalse((destination / "swarm-water-tabs-check" / ".expo").exists())

    def test_scratch_salvages_generated_files_when_reasonix_omits_result_json(self) -> None:
        # Given: Reasonix created app source files but did not write the required result JSON.
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as scratch_dir:
            workspace = Path(workspace_dir)
            scratch = Path(scratch_dir)
            result_json = workspace / "result.json"
            (scratch / "swarm-water-tabs-check" / "src").mkdir(parents=True)
            (scratch / "swarm-water-tabs-check" / "src" / "App.tsx").write_text("app\n", encoding="utf-8")
            task = self._worker_task(workspace, result_json)

            # When: the controller salvages the partial scratch output.
            salvaged = write_salvaged_result_if_needed(
                result_json,
                scratch=scratch,
                task=task,
                started_at=10.0,
                finished_at=12.5,
            )

            # Then: a valid result exists so local tournament and acceptance gates can decide final status.
            payload = json.loads(result_json.read_text(encoding="utf-8"))
            validate_result(payload)
            self.assertTrue(salvaged)
            self.assertEqual(payload["status"], "SUCCEEDED")
            self.assertIn("controller salvaged", payload["summary"])
            self.assertEqual(payload["duration_seconds"], 2.5)
            self.assertIn("swarm-water-tabs-check/src/App.tsx", payload["changed_files"])

    def test_scratch_runner_runs_focused_entrypoint_repair_for_partial_expo_app(self) -> None:
        run_id = "scratch-entrypoint-repair-test"
        scratch_run = Path(tempfile.gettempdir()) / "blackcow-reasonix-scratch" / run_id
        shutil.rmtree(scratch_run, ignore_errors=True)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                project_root = root / "repo"
                workspace = root / "workspace"
                project_root.mkdir()
                workspace.mkdir()
                result_json = workspace / ".omo" / "swarm" / "runs" / run_id / "workers" / "coder-1-r1" / "result.json"
                task = self._worker_task(workspace, result_json)
                runner = ScratchReasonixRunner(project_root)
                fake_runner = EntrypointRepairRunner()
                runner.runner = fake_runner

                outcome = runner.run(task)

                payload = json.loads(result_json.read_text(encoding="utf-8"))
                self.assertEqual(outcome.status, "SUCCEEDED")
                self.assertEqual(payload["status"], "SUCCEEDED")
                self.assertIn("complete scratch candidate", payload["summary"])
                self.assertIn("swarm-water-test/App.tsx", payload["changed_files"])
                self.assertEqual(fake_runner.calls, 2)
                self.assertIn("entrypoint_repair_started", outcome.events)
                self.assertIn("External-Safe Scratch Entrypoint Repair", fake_runner.prompts[-1])
                self.assertLessEqual(fake_runner.timeouts[-1], ENTRYPOINT_REPAIR_TIMEOUT_SECONDS)
        finally:
            shutil.rmtree(scratch_run, ignore_errors=True)

    def test_scratch_runner_chains_tsconfig_then_entrypoint_repairs(self) -> None:
        run_id = "scratch-tsconfig-entrypoint-repair-test"
        scratch_run = Path(tempfile.gettempdir()) / "blackcow-reasonix-scratch" / run_id
        shutil.rmtree(scratch_run, ignore_errors=True)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                project_root = root / "repo"
                workspace = root / "workspace"
                project_root.mkdir()
                workspace.mkdir()
                result_json = workspace / ".omo" / "swarm" / "runs" / run_id / "workers" / "coder-1-r1" / "result.json"
                task = self._worker_task(workspace, result_json)
                runner = ScratchReasonixRunner(project_root)
                fake_runner = TsconfigThenEntrypointRepairRunner()
                runner.runner = fake_runner

                outcome = runner.run(task)

                payload = json.loads(result_json.read_text(encoding="utf-8"))
                tsconfig = json.loads((workspace / "swarm-water-test" / "tsconfig.json").read_text(encoding="utf-8"))
                self.assertEqual(outcome.status, "SUCCEEDED")
                self.assertEqual(payload["status"], "SUCCEEDED")
                self.assertEqual(fake_runner.calls, 3)
                self.assertIn("tsconfig_repair_started", outcome.events)
                self.assertIn("entrypoint_repair_started", outcome.events)
                self.assertIn("External-Safe Scratch Tsconfig Repair", fake_runner.prompts[1])
                self.assertIn("External-Safe Scratch Entrypoint Repair", fake_runner.prompts[2])
                self.assertNotIn("baseUrl", tsconfig["compilerOptions"])
                self.assertNotIn("paths", tsconfig["compilerOptions"])
                self.assertTrue((workspace / "swarm-water-test" / "App.tsx").exists())
        finally:
            shutil.rmtree(scratch_run, ignore_errors=True)

    def test_scratch_does_not_salvage_empty_output(self) -> None:
        # Given: Reasonix omitted result JSON and produced no app files.
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as scratch_dir:
            workspace = Path(workspace_dir)
            result_json = workspace / "result.json"
            task = self._worker_task(workspace, result_json)

            # When: salvage runs against an empty scratch workspace.
            salvaged = write_salvaged_result_if_needed(
                result_json,
                scratch=Path(scratch_dir),
                task=task,
                started_at=10.0,
                finished_at=12.5,
            )

            # Then: no success result is fabricated.
            self.assertFalse(salvaged)
            self.assertFalse(result_json.exists())

    def test_scratch_retry_clears_stale_failed_salvage_result(self) -> None:
        # Given: the first scratch attempt times out with an incomplete app and writes a failed salvage result.
        run_id = "scratch-stale-result-test"
        scratch_run = Path(tempfile.gettempdir()) / "blackcow-reasonix-scratch" / run_id
        shutil.rmtree(scratch_run, ignore_errors=True)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                project_root = root / "repo"
                workspace = root / "workspace"
                project_root.mkdir()
                workspace.mkdir()
                result_json = workspace / ".omo" / "swarm" / "runs" / run_id / "workers" / "coder-1-r1" / "result.json"
                task = self._worker_task(workspace, result_json)
                runner = ScratchReasonixRunner(project_root)
                runner.runner = TwoAttemptMissingResultRunner()

                first = runner.run(task)
                self.assertEqual(first.status, "FAILED_RETRYABLE")
                self.assertIn("missing native entry point", json.loads(result_json.read_text(encoding="utf-8"))["summary"])

                # When: retrying the same worker produces a complete no-result app.
                second = runner.run(task)

                # Then: the stale failed result is replaced by the second attempt's successful salvage.
                payload = json.loads(result_json.read_text(encoding="utf-8"))
                self.assertEqual(second.status, "SUCCEEDED")
                self.assertEqual(payload["status"], "SUCCEEDED")
                self.assertIn("complete scratch candidate", payload["summary"])
                self.assertIn("swarm-water-test/App.tsx", payload["changed_files"])
        finally:
            shutil.rmtree(scratch_run, ignore_errors=True)

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
            timeout_seconds=180,
            missing_result_fatal=False,
        )


class TwoAttemptMissingResultRunner:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, task: WorkerTask) -> RunnerOutcome:
        self.calls += 1
        _write_no_install_project(task.workspace / "swarm-water-test", with_entry=self.calls >= 3)
        started_at = float(self.calls)
        return RunnerOutcome(
            status="FAILED_RETRYABLE",
            result_path=task.result_json,
            command=("fake-scratch",),
            started_at=started_at,
            finished_at=started_at + 0.5,
            process=None,
            events=("missing_result_json",),
        )


class EntrypointRepairRunner:
    def __init__(self) -> None:
        self.calls = 0
        self.prompts: list[str] = []
        self.timeouts: list[int] = []

    def run(self, task: WorkerTask) -> RunnerOutcome:
        self.calls += 1
        self.prompts.append(task.prompt_file.read_text(encoding="utf-8"))
        self.timeouts.append(task.timeout_seconds)
        _write_no_install_project(task.workspace / "swarm-water-test", with_entry=self.calls == 2)
        started_at = float(self.calls)
        return RunnerOutcome(
            status="FAILED_RETRYABLE",
            result_path=task.result_json,
            command=("fake-scratch",),
            started_at=started_at,
            finished_at=started_at + 0.5,
            process=None,
            events=("timeout", "missing_result_json"),
        )


class TsconfigThenEntrypointRepairRunner:
    def __init__(self) -> None:
        self.calls = 0
        self.prompts: list[str] = []

    def run(self, task: WorkerTask) -> RunnerOutcome:
        self.calls += 1
        self.prompts.append(task.prompt_file.read_text(encoding="utf-8"))
        project = task.workspace / "swarm-water-test"
        if self.calls == 1:
            _write_no_install_project(project, with_entry=False, with_base_url=True)
        elif self.calls == 2:
            _write_no_install_project(project, with_entry=False, with_base_url=False)
        else:
            _write_no_install_project(project, with_entry=True, with_base_url=False)
        started_at = float(self.calls)
        return RunnerOutcome(
            status="FAILED_RETRYABLE",
            result_path=task.result_json,
            command=("fake-scratch",),
            started_at=started_at,
            finished_at=started_at + 0.5,
            process=None,
            events=("timeout", "missing_result_json"),
        )


def _write_no_install_project(project: Path, *, with_entry: bool, with_base_url: bool = False) -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc --noEmit","lint":"tsc --noEmit"}}\n',
        encoding="utf-8",
    )
    compiler_options = '{"jsx":"react-jsx","baseUrl":".","paths":{"*":["./src/declarations.d.ts"]}}' if with_base_url else '{"jsx":"react-jsx"}'
    (project / "tsconfig.json").write_text(f'{{"compilerOptions":{compiler_options}}}\n', encoding="utf-8")
    (project / "app.json").write_text('{"expo":{"name":"Water","slug":"swarm-water-test"}}\n', encoding="utf-8")
    (project / "DESIGN.md").write_text("# Water Design\n\nTokens, tabs, states, and native QA criteria.\n", encoding="utf-8")
    if with_entry:
        (project / "App.tsx").write_text("export default function App() { return null; }\n", encoding="utf-8")
        (project / "types.d.ts").write_text('declare module "react/jsx-runtime";\n', encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
