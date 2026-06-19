from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.blackcow_swarm_lib import cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "scripts" / "blackcow_swarm.py"


class TestCli(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_lists_all_subcommands(self) -> None:
        result = self.run_cli("--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        for subcommand in (
            "estimate",
            "plan",
            "run",
            "run-loop",
            "resume",
            "cancel",
            "status",
            "cleanup",
        ):
            self.assertIn(subcommand, result.stdout)

    def test_run_help_lists_runtime_options(self) -> None:
        result = self.run_cli("run", "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        for option in (
            "--task-graph",
            "--dry-run",
            "--mode",
            "--intensity",
            "--max-workers",
        ):
            self.assertIn(option, result.stdout)

    def test_invalid_subcommand_fails(self) -> None:
        result = self.run_cli("nope")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_blocked_run_prints_json_and_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            graph = Path(temp_dir) / "graph.json"
            graph.write_text("{}", encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(cli, "execute_reasonix_run", return_value={"run_id": "blocked-run", "status": "BLOCKED"}),
                patch("sys.stdout", stdout),
            ):
                return_code = cli.main(["run", "--task-graph", str(graph), "--runner", "reasonix"])

            self.assertEqual(return_code, 1)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "BLOCKED")

    def test_succeeded_run_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            graph = Path(temp_dir) / "graph.json"
            graph.write_text("{}", encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(cli, "execute_mock_run", return_value={"run_id": "ok-run", "status": "SUCCEEDED"}),
                patch("sys.stdout", stdout),
            ):
                return_code = cli.main(["run", "--task-graph", str(graph), "--runner", "mock"])

            self.assertEqual(return_code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
