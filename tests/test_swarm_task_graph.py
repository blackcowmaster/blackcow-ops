from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.config import load_config, merge_cli_overrides
from scripts.blackcow_swarm_lib.schema import validate_task_graph
from scripts.blackcow_swarm_lib.task_graph import create_dry_run_plan


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "scripts" / "blackcow_swarm.py"


class TestSwarmTaskGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.run_ids = ("swarm-unit-plan", "swarm-risky-plan", "swarm-test-plan")
        for run_id in self.run_ids:
            shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)

    def tearDown(self) -> None:
        for run_id in self.run_ids:
            shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / run_id, ignore_errors=True)

    def test_create_dry_run_plan_writes_valid_graph(self) -> None:
        config = load_config()
        options = merge_cli_overrides(
            config,
            mode="adaptive",
            intensity="high",
            policy="auto",
            max_workers=None,
        )

        artifacts = create_dry_run_plan(
            "Implement team invite flow",
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )

        self.assertTrue(artifacts.task_graph_path.exists())
        self.assertTrue(artifacts.estimate_path.exists())
        self.assertTrue(artifacts.shared_context_path.exists())
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        validate_task_graph(payload)
        for task in payload["tasks"]:
            for field in ("id", "kind", "skill", "prompt", "read_only", "depends_on", "writes", "replicas", "timeout_minutes"):
                self.assertIn(field, task)

    def test_plan_cli_creates_run_directory(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "plan",
                "Implement team invite flow",
                "--intensity",
                "high",
                "--dry-run",
                "--run-id",
                "swarm-test-plan",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        graph_path = PROJECT_ROOT / ".omo" / "swarm" / "runs" / "swarm-test-plan" / "task_graph.json"
        self.assertTrue(graph_path.exists())
        validate_task_graph(json.loads(graph_path.read_text(encoding="utf-8")))

    def test_dangerous_prompt_without_yes_has_no_coder_swarm(self) -> None:
        config = load_config()
        options = merge_cli_overrides(
            config,
            mode="adaptive",
            intensity="max",
            policy="auto",
            max_workers=None,
        )

        artifacts = create_dry_run_plan(
            "Change auth policy and package-lock.json",
            config,
            options,
            run_id="swarm-risky-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        coder_swarms = [task for task in payload["tasks"] if task["kind"] in ("coder", "writer") and task["replicas"] > 1]

        self.assertEqual(coder_swarms, [])

    def test_writer_replicas_expand_when_worktree_isolation_enabled(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="adaptive", intensity="max", policy="auto", max_workers=8)

        artifacts = create_dry_run_plan(
            "Implement a team invite flow across UI, API, email template, tests, and documentation",
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        coder_tasks = [task for task in payload["tasks"] if task["kind"] == "coder"]
        profile = config.intensity[options.intensity]
        max_writer_workers = profile.max_writer_workers

        self.assertGreater(len(coder_tasks), 0)
        self.assertGreater(coder_tasks[0]["replicas"], 1)
        self.assertLessEqual(coder_tasks[0]["replicas"], max_writer_workers)
        self.assertLessEqual(coder_tasks[0]["replicas"], options.max_workers)

    def test_small_expo_app_uses_micro_swarm_not_max_fanout(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="adaptive", intensity="max", policy="auto", max_workers=None)

        artifacts = create_dry_run_plan(
            (
                "Create a fresh React Native Expo water-drinking check app at swarm-water-check-app. "
                "Use the blackcow-* skill pipeline and Reasonix worker swarm. Include timer-free hydration "
                "check-ins, daily goal progress, history, native visual/design QA, package/typecheck/lint "
                "gates, speed measurement, and final judgement evidence. Do not use prior water-check-app "
                "or pomodoro-app artifacts."
            ),
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        by_kind = {task["kind"]: task for task in payload["tasks"]}

        self.assertEqual(payload["intensity"], "normal")
        self.assertEqual(payload["mode"], "coder")
        self.assertEqual(by_kind["discovery"]["replicas"], 1)
        self.assertEqual(by_kind["coder"]["replicas"], 1)
        self.assertEqual(by_kind["qa"]["replicas"], 1)
        self.assertNotIn("review", by_kind)
        checks = "\n".join(payload["tasks"][0]["acceptance_checks"])
        self.assertIn("--min-speedup 1.0", checks)
        self.assertNotIn("--min-speedup 1.1", checks)

    def test_shared_context_contains_anti_gaming_guardrails(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="adaptive", intensity="high", policy="auto", max_workers=None)

        artifacts = create_dry_run_plan(
            "Implement team invite flow",
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        context = artifacts.shared_context_path.read_text(encoding="utf-8")

        self.assertIn("do_not_skip_or_delete_tests", context)
        self.assertIn("result.json", context)
        self.assertIn("Failure Feedback Loop", context)
        self.assertIn("failing command", context)
        self.assertIn("Design Source Gate", context)
        self.assertIn("Native Visual Gate", context)
        self.assertIn("xcrun simctl", context)
        self.assertIn("codex exec --image", context)
        self.assertIn("Swarm Speed Gate", context)

    def test_project_task_graph_uses_project_acceptance_checks(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="full", intensity="high", policy="auto", max_workers=None)

        artifacts = create_dry_run_plan(
            "Implement the Pomodoro app in pomodoro-app with timer controls",
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        checks = set(payload["tasks"][0]["acceptance_checks"])

        self.assertIn("cd pomodoro-app && npm run typecheck", checks)
        self.assertIn("cd pomodoro-app && npm run lint", checks)
        self.assertIn(
            "python3 scripts/blackcow_web_smoke.py --project pomodoro-app --port 8088 --expect 25:00 --reject 'Something went wrong'",
            checks,
        )
        self.assertIn("python3 scripts/blackcow_design_gate.py --project pomodoro-app", checks)
        self.assertIn("python3 scripts/blackcow_native_smoke.py --project pomodoro-app --platform ios", checks)
        self.assertIn(
            "python3 scripts/blackcow_expo_native_smoke.py --project pomodoro-app --platform ios "
            "--screenshot .omo/swarm/runs/swarm-unit-plan/screenshots/ios.png "
            "--review-output .omo/swarm/runs/swarm-unit-plan/visual-review.md --expect 25:00",
            checks,
        )
        self.assertIn("python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/swarm-unit-plan --min-speedup 1.1", checks)

    def test_new_expo_project_task_graph_uses_future_project_acceptance_checks(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="full", intensity="high", policy="auto", max_workers=None)

        artifacts = create_dry_run_plan(
            "Create a new React Native Expo water drinking check app in water-check-app",
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        checks = set(payload["tasks"][0]["acceptance_checks"])

        self.assertIn("test -f water-check-app/package.json", checks)
        self.assertIn("python3 scripts/blackcow_expo_clean_gate.py --project water-check-app", checks)
        self.assertIn("cd water-check-app && npm run typecheck", checks)
        self.assertIn("cd water-check-app && npm run lint", checks)
        self.assertIn("python3 scripts/blackcow_design_gate.py --project water-check-app", checks)
        self.assertIn("python3 scripts/blackcow_native_smoke.py --project water-check-app --platform ios", checks)
        self.assertNotIn("scripts/blackcow_web_smoke.py", "\n".join(checks))
        self.assertNotIn("scripts/blackcow_expo_native_smoke.py", "\n".join(checks))
        self.assertIn("python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/swarm-unit-plan --min-speedup 1.0", checks)

    def test_timer_free_hydration_app_does_not_use_pomodoro_expectation(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="full", intensity="max", policy="auto", max_workers=None)

        artifacts = create_dry_run_plan(
            "Create a fresh React Native Expo water-drinking check app at swarm-water-check-app. "
            "Include timer-free hydration check-ins and daily goal progress.",
            config,
            options,
            run_id="swarm-unit-plan",
            project_root=PROJECT_ROOT,
            approve_dangerous=False,
        )
        payload = json.loads(artifacts.task_graph_path.read_text(encoding="utf-8"))
        checks = "\n".join(payload["tasks"][0]["acceptance_checks"])

        self.assertIn("--expect Water", checks)
        self.assertNotIn("--expect 25:00", checks)

    def test_malformed_run_id_is_rejected(self) -> None:
        config = load_config()
        options = merge_cli_overrides(config, mode="adaptive", intensity="high", policy="auto", max_workers=None)

        with self.assertRaisesRegex(ValueError, "invalid run-id"):
            create_dry_run_plan(
                "Implement team invite flow",
                config,
                options,
                run_id="../bad",
                project_root=PROJECT_ROOT,
                approve_dangerous=False,
            )


if __name__ == "__main__":
    unittest.main()
