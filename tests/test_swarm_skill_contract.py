from __future__ import annotations

import tempfile
import unittest
import json
import shutil
from pathlib import Path

from scripts.blackcow_swarm_lib.acceptance_runner import acceptance_passed, run_acceptance_checks
from scripts.blackcow_swarm_lib.lifecycle import execute_mock_run
from scripts.blackcow_swarm_lib.skill_contract import build_worker_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSkillContractPrompt(unittest.TestCase):
    def test_react_native_worker_prompt_embeds_rn_skill_context(self) -> None:
        # Given: an Expo/React Native worker task with the normal BlackCow skill source.
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            base_prompt = (
                "Build an Expo React Native water check native app and verify it with an iOS smoke test."
            )

            # When: the swarm builds a worker prompt for that mobile task.
            prompt = build_worker_prompt(
                project_root=PROJECT_ROOT,
                run_dir=run_dir,
                skill="blackcow-loop",
                base_prompt=base_prompt,
                task_id="coder-1",
                replica_id="coder-1-r1",
                result_json=run_dir / "workers" / "coder-1" / "result.json",
                acceptance_checks=("npm test",),
            )

            # Then: the worker gets the active BlackCow source plus every applicable RN/UI skill context.
            self.assertIn("Active Skill Source", prompt)
            self.assertIn("blackcow-loop", prompt)
            self.assertIn("react-native-architecture", prompt)
            self.assertIn("react-native-design", prompt)
            self.assertIn("ui-ux-pro-max", prompt)
            self.assertIn("vercel-react-native-skills", prompt)
            self.assertIn("React Native Architecture", prompt)
            self.assertIn("React Native Design", prompt)
            self.assertIn("Generate Design System (REQUIRED)", prompt)
            self.assertIn("React Native and Expo best practices", prompt)

    def test_small_expo_app_prompt_uses_fast_path_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)

            prompt = build_worker_prompt(
                project_root=PROJECT_ROOT,
                run_dir=run_dir,
                skill="blackcow-plan",
                base_prompt=(
                    "Create a fresh React Native Expo water-drinking check app at swarm-water-check-app. "
                    "Include native visual/design QA. Do not use prior water-check-app or pomodoro-app artifacts."
                ),
                task_id="discovery-1",
                replica_id="discovery-1-r1",
                result_json=run_dir / "workers" / "discovery-1" / "result.json",
                acceptance_checks=("python3 scripts/blackcow_design_gate.py --project swarm-water-check-app",),
            )

            self.assertIn("Small App Fast Path", prompt)
            self.assertIn("Do not call web_search", prompt)
            self.assertIn("Do not call explore", prompt)
            self.assertIn("App.tsx or app/_layout.tsx", prompt)
            self.assertIn("Minimum complete Expo/RN candidate", prompt)
            self.assertIn("Write a compact result JSON", prompt)

    def test_non_react_native_worker_prompt_omits_rn_skill_context(self) -> None:
        # Given: a non-mobile documentation worker task.
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)

            # When: the swarm builds a worker prompt for general repository work.
            prompt = build_worker_prompt(
                project_root=PROJECT_ROOT,
                run_dir=run_dir,
                skill="blackcow-loop",
                base_prompt="Update README copy for the operator workflow.",
                task_id="docs-1",
                replica_id="docs-1-r1",
                result_json=run_dir / "workers" / "docs-1" / "result.json",
                acceptance_checks=(),
            )

            # Then: RN-only source context is not injected.
            self.assertNotIn("react-native-architecture", prompt)
            self.assertNotIn("react-native-design", prompt)
            self.assertNotIn("ui-ux-pro-max", prompt)
            self.assertNotIn("vercel-react-native-skills", prompt)

    def test_loop_worker_prompt_embeds_actual_blackcow_skill_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            (run_dir / "shared_context.md").write_text("Shared context marker\n", encoding="utf-8")

            prompt = build_worker_prompt(
                project_root=PROJECT_ROOT,
                run_dir=run_dir,
                skill="blackcow-loop",
                base_prompt="Implement Pomodoro",
                task_id="coder-1",
                replica_id="coder-1-r1",
                result_json=run_dir / "workers" / "coder-1" / "result.json",
                acceptance_checks=("python3 scripts/blackcow_design_gate.py --project pomodoro-app",),
            )

            self.assertIn("skills/blackcow-loop.md", prompt)
            self.assertIn("PDCA Evidence Discipline", prompt)
            self.assertIn("Cross-Skill Evidence Contract", prompt)
            self.assertIn("blackcow-librarian", prompt)
            self.assertIn("Shared context marker", prompt)
            self.assertIn("schemas/swarm-result.schema.json", prompt)
            self.assertIn("Do not call run_skill", prompt)

    def test_worker_prompt_falls_back_to_controller_shared_context_for_worktree_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_root = root / "repo"
            controller_run_dir = project_root / ".omo" / "swarm" / "runs" / "water-run"
            worktree_run_dir = root / "worktree" / ".omo" / "swarm" / "runs" / "water-run"
            controller_run_dir.mkdir(parents=True)
            worktree_run_dir.mkdir(parents=True)
            (controller_run_dir / "shared_context.md").write_text(
                "Design Source Gate\nNative Visual Gate\nSwarm Speed Gate\n",
                encoding="utf-8",
            )

            prompt = build_worker_prompt(
                project_root=project_root,
                run_dir=worktree_run_dir,
                skill="external-test-skill",
                base_prompt="Create a small Expo water app.",
                task_id="coder-1",
                replica_id="coder-1-r1",
                result_json=worktree_run_dir / "workers" / "coder-1-r1" / "result.json",
                acceptance_checks=("python3 scripts/blackcow_design_gate.py --project swarm-water-test",),
            )

            self.assertIn("Design Source Gate", prompt)
            self.assertIn("Native Visual Gate", prompt)
            self.assertIn("Swarm Speed Gate", prompt)
            self.assertNotIn("(no shared_context.md found)", prompt)

    def test_acceptance_runner_writes_feedback_packet_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            checks = ("python3 -c 'import sys; print(\"bad\"); sys.exit(7)'",)

            results = run_acceptance_checks(checks, project_root=PROJECT_ROOT, run_dir=run_dir)

            self.assertFalse(acceptance_passed(results, checks))
            self.assertEqual(results[0].exit_code, 7)
            self.assertTrue((run_dir / "feedback" / "acceptance-01.json").exists())

    def test_acceptance_runner_removes_stale_attempt_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            first_checks = (
                "python3 -c 'print(\"ok\")'",
                "python3 -c 'import sys; print(\"bad\"); sys.exit(7)'",
            )
            second_checks = ("python3 -c 'import sys; print(\"bad again\"); sys.exit(8)'",)

            run_acceptance_checks(first_checks, project_root=PROJECT_ROOT, run_dir=run_dir)
            results = run_acceptance_checks(second_checks, project_root=PROJECT_ROOT, run_dir=run_dir)

            self.assertEqual(results[0].exit_code, 8)
            self.assertTrue((run_dir / "feedback" / "acceptance-01.json").exists())
            self.assertFalse((run_dir / "feedback" / "acceptance-02.json").exists())
            self.assertFalse((run_dir / "acceptance" / "02.stdout.log").exists())
            self.assertFalse((run_dir / "acceptance" / "02.stderr.log").exists())

    def test_acceptance_runner_executes_controller_checker_against_integration_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            controller_root = root / "controller"
            integration_root = root / "integration"
            run_dir = root / "run"
            script_dir = controller_root / "scripts"
            app_dir = integration_root / "water-app"
            script_dir.mkdir(parents=True)
            app_dir.mkdir(parents=True)
            (app_dir / "package.json").write_text("{}\n", encoding="utf-8")
            (script_dir / "blackcow_probe_gate.py").write_text(
                "from pathlib import Path\n"
                "import argparse\n"
                "parser = argparse.ArgumentParser()\n"
                "parser.add_argument('--project', required=True)\n"
                "args = parser.parse_args()\n"
                "project = Path(args.project)\n"
                "if not (project / 'package.json').exists():\n"
                "    raise SystemExit(5)\n"
                "print(Path.cwd())\n"
                "print(project)\n",
                encoding="utf-8",
            )

            results = run_acceptance_checks(
                ("python3 scripts/blackcow_probe_gate.py --project water-app",),
                project_root=integration_root,
                controller_root=controller_root,
                run_dir=run_dir,
            )

            self.assertTrue(results[0].ok, results[0].stderr_path.read_text(encoding="utf-8"))
            stdout = results[0].stdout_path.read_text(encoding="utf-8")
            self.assertIn(str(controller_root), stdout)
            self.assertIn(str(app_dir), stdout)

    def test_mock_run_cannot_succeed_when_acceptance_fails(self) -> None:
        run_id = "swarm-acceptance-fails"
        graph_path = Path("/tmp/blackcow-missing-graph.json")
        shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
                graph_path = Path(handle.name)
                json.dump(
                    {
                        "run_id": run_id,
                        "task": "Acceptance must fail",
                        "mode": "qa",
                        "intensity": "high",
                        "policy": "auto",
                        "requires_approval": False,
                        "worker_swarm_allowed": True,
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
                                "acceptance_checks": ["python3 -c 'import sys; sys.exit(9)'"],
                                "replicas": 1,
                                "max_replicas": 1,
                                "timeout_minutes": 1,
                            }
                        ],
                    },
                    handle,
                )

            output = execute_mock_run(graph_path, run_id, PROJECT_ROOT)

            self.assertEqual(output["status"], "FAILED")
            self.assertTrue((PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id / "feedback" / "acceptance-01.json").exists())
        finally:
            graph_path.unlink(missing_ok=True)
            shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)

    def test_mock_run_executes_task_replicas(self) -> None:
        run_id = "swarm-replicas-run"
        graph_path = Path("/tmp/blackcow-replicas-graph.json")
        shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)
        try:
            graph_path.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "task": "Replica test",
                        "mode": "qa",
                        "intensity": "high",
                        "policy": "auto",
                        "requires_approval": False,
                        "worker_swarm_allowed": True,
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
                                "acceptance_checks": ["python3 -c 'print(\"ok\")'"],
                                "replicas": 3,
                                "max_replicas": 3,
                                "timeout_minutes": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            output = execute_mock_run(graph_path, run_id, PROJECT_ROOT)
            state = json.loads(Path(output["state"]).read_text(encoding="utf-8"))

            self.assertEqual(output["status"], "SUCCEEDED")
            self.assertEqual(set(state["workers"]), {"qa-1-r1", "qa-1-r2", "qa-1-r3"})
        finally:
            graph_path.unlink(missing_ok=True)
            shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
