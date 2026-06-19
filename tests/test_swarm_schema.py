from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.config import JsonValue
from scripts.blackcow_swarm_lib.schema import (
    SchemaError,
    validate_estimate,
    validate_final_judgement,
    validate_result,
    validate_task_graph,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"
SCHEMAS = PROJECT_ROOT / "schemas"


class TestSchemas(unittest.TestCase):
    def load_fixture(self, name: str) -> JsonValue:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_schema_files_are_valid_json(self) -> None:
        for name in (
            "swarm-task.schema.json",
            "swarm-result.schema.json",
            "swarm-estimate.schema.json",
            "swarm-final-judgement.schema.json",
        ):
            with self.subTest(schema=name):
                json.loads((SCHEMAS / name).read_text(encoding="utf-8"))

    def test_valid_fixtures(self) -> None:
        validate_task_graph(self.load_fixture("task_graph.simple.json"))
        validate_result(self.load_fixture("result.success.json"))
        validate_estimate(self.load_fixture("estimate.high.json"))
        validate_final_judgement(self.load_fixture("final_judgement.success.json"))

    def test_invalid_task_missing_kind(self) -> None:
        with self.assertRaisesRegex(SchemaError, "kind"):
            validate_task_graph(self.load_fixture("task_graph.invalid-missing-kind.json"))

    def test_invalid_task_kind(self) -> None:
        payload = self.load_fixture("task_graph.simple.json")
        payload["tasks"][0]["kind"] = "unknown"

        with self.assertRaisesRegex(SchemaError, "kind"):
            validate_task_graph(payload)

    def test_invalid_result_status(self) -> None:
        payload = self.load_fixture("result.success.json")
        payload["status"] = "WIN"

        with self.assertRaisesRegex(SchemaError, "status"):
            validate_result(payload)

    def test_invalid_score_range(self) -> None:
        payload = self.load_fixture("result.success.json")
        payload["score"]["overall"] = 101

        with self.assertRaisesRegex(SchemaError, "score.overall"):
            validate_result(payload)


if __name__ == "__main__":
    unittest.main()
