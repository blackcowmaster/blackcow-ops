from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .schema import validate_final_judgement


class SelectedPatchPayload(TypedDict):
    task_id: str
    replica_id: str
    patch_path: str


@dataclass(frozen=True, slots=True)
class SelectedPatch:
    task_id: str
    replica_id: str
    patch_path: str

    def to_json(self) -> SelectedPatchPayload:
        return {"task_id": self.task_id, "replica_id": self.replica_id, "patch_path": self.patch_path}


class FinalJudge:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir

    def write(
        self,
        *,
        run_id: str,
        status: str,
        summary: str,
        selected_patches: tuple[SelectedPatch, ...],
        score_overall: int,
    ) -> Path:
        payload = {
            "run_id": run_id,
            "status": status,
            "summary": summary,
            "selected_patches": [patch.to_json() for patch in selected_patches],
            "score": {
                "overall": score_overall,
                "correctness": score_overall,
                "safety": score_overall,
                "tests": score_overall,
            },
        }
        validate_final_judgement(payload)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / "final_judgement.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path
