from __future__ import annotations

import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.lifecycle_graph import acceptance_checks, scheduled_tasks


class TestSwarmLifecycleGraph(unittest.TestCase):
    def test_run_scoped_speed_gate_uses_active_run_dir(self) -> None:
        graph = {
            "run_id": "water-scratch-test-v7",
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
                        "python3 scripts/blackcow_design_gate.py --project swarm-water-test",
                        "python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/water-scratch-test-v7 --min-speedup 1.0",
                    ],
                }
            ],
        }
        project_root = Path("/Users/tester/Project/blackcow-ops")
        active_run_dir = project_root / ".omo" / "swarm" / "runs" / "water-scratch-test-v12-live-a1"

        checks = acceptance_checks(graph, run_dir=active_run_dir, project_root=project_root)
        tasks = scheduled_tasks(graph, run_dir=active_run_dir, project_root=project_root)

        expected_speed_gate = (
            "python3 scripts/blackcow_speed_gate.py --run-dir "
            ".omo/swarm/runs/water-scratch-test-v12-live-a1 --min-speedup 1.0"
        )
        self.assertIn(expected_speed_gate, checks)
        self.assertIn(expected_speed_gate, tasks[0].acceptance_checks)
        self.assertNotIn("water-scratch-test-v7", "\n".join(checks))
        self.assertNotIn("/Users/tester/Project/blackcow-ops", "\n".join(checks))
        self.assertEqual(
            tasks[0].acceptance_checks[0],
            "python3 scripts/blackcow_design_gate.py --project swarm-water-test",
        )

    def test_run_scoped_speed_gate_preserves_absolute_path_outside_project(self) -> None:
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
                        "python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/planned --min-speedup 1.0",
                    ],
                }
            ],
        }

        checks = acceptance_checks(
            graph,
            run_dir=Path("/tmp/external-run"),
            project_root=Path("/Users/tester/Project/blackcow-ops"),
        )

        self.assertEqual(
            checks,
            ("python3 scripts/blackcow_speed_gate.py --run-dir /tmp/external-run --min-speedup 1.0",),
        )

    def test_acceptance_checks_without_run_dir_preserve_graph_commands(self) -> None:
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
                        "python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/planned --min-speedup 1.0",
                    ],
                }
            ],
        }

        self.assertEqual(
            acceptance_checks(graph),
            ("python3 scripts/blackcow_speed_gate.py --run-dir .omo/swarm/runs/planned --min-speedup 1.0",),
        )


if __name__ == "__main__":
    unittest.main()
