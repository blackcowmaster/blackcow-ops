from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.config import ConfigError, load_config, merge_cli_overrides


class TestSwarmConfig(unittest.TestCase):
    def test_default_config_has_required_profiles(self) -> None:
        config = load_config()

        self.assertEqual(config.default_policy, "auto")
        self.assertEqual(config.default_intensity, "high")
        self.assertEqual(config.intensity["normal"].max_total_workers, 8)
        self.assertEqual(config.intensity["high"].max_total_workers, 24)
        self.assertEqual(config.intensity["max"].max_total_workers, 64)
        self.assertTrue(config.runner.require_json_result)

    def test_runner_template_requires_result_json(self) -> None:
        payload = {
            "swarm": {
                "default_policy": "auto",
                "default_mode": "adaptive",
                "default_intensity": "high",
                "runner": {
                    "type": "reasonix",
                    "command_template": [
                        "reasonix",
                        "run_skill",
                        "{skill}",
                        "--prompt-file",
                        "{prompt_file}",
                    ],
                    "cwd_mode": "task_workspace",
                    "require_json_result": True,
                },
                "intensity": {
                    "normal": {"max_total_workers": 8, "max_writer_workers": 1, "timeout_seconds": 600},
                    "high": {"max_total_workers": 24, "max_writer_workers": 3, "timeout_seconds": 900},
                    "max": {"max_total_workers": 64, "max_writer_workers": 6, "timeout_seconds": 1200},
                },
                "single_writer_paths": [],
                "risky_writer_patterns": [],
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "bad.swarm.json"
            config_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ConfigError, "result_json"):
                load_config(config_path)

    def test_runner_template_rejects_unknown_placeholder(self) -> None:
        payload = {
            "swarm": {
                "default_policy": "auto",
                "default_mode": "adaptive",
                "default_intensity": "high",
                "runner": {
                    "type": "reasonix",
                    "command_template": [
                        "reasonix",
                        "run_skill",
                        "{skill}",
                        "--prompt-file",
                        "{prompt_file}",
                        "--output",
                        "{result_json}",
                        "--bad",
                        "{mystery}",
                    ],
                    "cwd_mode": "task_workspace",
                    "require_json_result": True,
                },
                "intensity": {
                    "normal": {"max_total_workers": 8, "max_writer_workers": 1, "timeout_seconds": 600},
                    "high": {"max_total_workers": 24, "max_writer_workers": 3, "timeout_seconds": 900},
                    "max": {"max_total_workers": 64, "max_writer_workers": 6, "timeout_seconds": 1200},
                },
                "single_writer_paths": [],
                "risky_writer_patterns": [],
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "bad.swarm.json"
            config_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ConfigError, "mystery"):
                load_config(config_path)

    def test_cli_overrides_replace_config_defaults(self) -> None:
        options = merge_cli_overrides(
            load_config(),
            mode="qa",
            intensity="normal",
            policy="suggest",
            max_workers=3,
        )

        self.assertEqual(options.mode, "qa")
        self.assertEqual(options.intensity, "normal")
        self.assertEqual(options.policy, "suggest")
        self.assertEqual(options.max_workers, 3)


if __name__ == "__main__":
    unittest.main()
