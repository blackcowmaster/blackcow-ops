from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.state import RunStore, StateError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "scripts" / "blackcow_swarm.py"


class TestStateStore(unittest.TestCase):
    def test_atomic_state_and_events_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RunStore(Path(temp_dir))

            store.write_state({"run_id": "state-test", "status": "DRY_RUN", "tasks": {}})
            store.append_event("state-test", "dry_run_started", {"tasks": 0})

            state = json.loads((Path(temp_dir) / "state.json").read_text(encoding="utf-8"))
            events = (Path(temp_dir) / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(state["status"], "DRY_RUN")
            self.assertEqual(len(events), 1)
            self.assertEqual(json.loads(events[0])["event"], "dry_run_started")


class TestStateLock(unittest.TestCase):
    def test_second_lock_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RunStore(Path(temp_dir))

            with store.acquire_lock():
                with self.assertRaisesRegex(StateError, "locked"):
                    with store.acquire_lock():
                        pass


class TestDryRunRunCli(unittest.TestCase):
    def setUp(self) -> None:
        shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / "swarm-qa-dry", ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(PROJECT_ROOT / ".omo" / "swarm" / "runs" / "swarm-qa-dry", ignore_errors=True)

    def test_run_dry_run_creates_state_events_and_no_workers(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "run",
                "--task-graph",
                "tests/fixtures/task_graph.simple.json",
                "--dry-run",
                "--run-id",
                "swarm-qa-dry",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        run_dir = PROJECT_ROOT / ".omo" / "swarm" / "runs" / "swarm-qa-dry"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reasonix", result.stdout)
        self.assertTrue((run_dir / "state.json").exists())
        self.assertTrue((run_dir / "events.jsonl").exists())
        self.assertFalse((run_dir / "workers").exists())


if __name__ == "__main__":
    unittest.main()
