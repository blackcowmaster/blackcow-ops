from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.judge import FinalJudge, SelectedPatch
from scripts.blackcow_swarm_lib.schema import validate_final_judgement


class TestFinalJudge(unittest.TestCase):
    def test_final_judgement_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = FinalJudge(Path(temp_dir)).write(
                run_id="run-judge",
                status="SUCCEEDED",
                summary="Selected clean patch",
                selected_patches=(SelectedPatch("C1", "C1-r2", ".omo/swarm/runs/run-judge/patches/C1-r2.patch"),),
                score_overall=91,
            )

            payload = json.loads(path.read_text(encoding="utf-8"))
            validate_final_judgement(payload)
            self.assertEqual(payload["selected_patches"][0]["replica_id"], "C1-r2")


if __name__ == "__main__":
    unittest.main()
