from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .worktree import WorktreeError, _safe_id


@dataclass(frozen=True, slots=True)
class RaceCandidate:
    replica_id: str
    status: str
    score_overall: int
    changed_lines: int
    completed_at: float


@dataclass(frozen=True, slots=True)
class RaceDecision:
    winner: RaceCandidate
    loser_actions: dict[str, str]


@dataclass(frozen=True, slots=True)
class PatchCandidate:
    replica_id: str
    task_id: str
    patch_path: Path
    score_overall: int
    changed_lines: int
    completed_at: float


@dataclass(frozen=True, slots=True)
class TournamentResult:
    winner: PatchCandidate
    report_path: Path
    integration_worktree: Path
    checkpoint_commit: str
    loser_actions: dict[str, str]


def select_race_winner(candidates: tuple[RaceCandidate, ...], *, discard_running_losers: bool) -> RaceDecision:
    winners = [candidate for candidate in candidates if candidate.status == "SUCCEEDED"]
    if not winners:
        raise ValueError("no successful race candidates")
    winner = sorted(winners, key=lambda item: (-item.score_overall, item.changed_lines, item.completed_at, item.replica_id))[0]
    loser_actions: dict[str, str] = {}
    for candidate in candidates:
        if candidate.replica_id == winner.replica_id:
            continue
        if candidate.status == "RUNNING" and discard_running_losers:
            loser_actions[candidate.replica_id] = "DISCARDED"
        else:
            loser_actions[candidate.replica_id] = "ARCHIVED"
    return RaceDecision(winner=winner, loser_actions=loser_actions)


class PatchTournament:
    def __init__(self, repo_root: Path, *, apply_target: str = "integration-worktree", yes: bool = False) -> None:
        if apply_target == "main" and not yes:
            raise WorktreeError("apply-target=main requires --yes")
        self.repo_root = repo_root
        self.apply_target = apply_target

    def run(self, run_id: str, candidates: tuple[PatchCandidate, ...]) -> TournamentResult:
        safe_run_id = _safe_id(run_id, "run_id")
        integration = self.create_integration_worktree(safe_run_id)
        clean = [candidate for candidate in candidates if candidate.patch_path.exists() and _patch_applies(integration, candidate.patch_path)]
        if not clean:
            raise WorktreeError("no candidate patch applies cleanly")
        winner = sorted(clean, key=lambda item: (-item.score_overall, item.changed_lines, item.completed_at, item.replica_id))[0]
        _git(integration, ("apply", str(winner.patch_path)))
        _git(integration, ("add", "-A"))
        _git(
            integration,
            ("-c", "user.name=Swarm Integrator", "-c", "user.email=swarm@example.invalid", "commit", "-m", f"swarm checkpoint {winner.replica_id}"),
        )
        checkpoint = _git_text(integration, ("rev-parse", "HEAD")).strip()
        report_path = self._write_report(safe_run_id, candidates, clean, winner)
        loser_actions = {candidate.replica_id: "DISCARDED" for candidate in candidates if candidate.replica_id != winner.replica_id}
        return TournamentResult(winner, report_path, integration, checkpoint, loser_actions)

    def create_integration_worktree(self, run_id: str) -> Path:
        safe_run_id = _safe_id(run_id, "run_id")
        if self.apply_target == "main":
            return self.repo_root
        path = self.repo_root / ".worktrees" / "swarm" / safe_run_id / "integration"
        path.parent.mkdir(parents=True, exist_ok=True)
        _remove_existing_worktree(self.repo_root, path)
        _git(self.repo_root, ("worktree", "add", "-B", f"swarm-{safe_run_id}-integration", str(path), "HEAD"))
        return path

    def create_dependent_worktree(self, run_id: str, replica_id: str, checkpoint_commit: str) -> Path:
        safe_run_id = _safe_id(run_id, "run_id")
        safe_replica_id = _safe_id(replica_id, "replica_id")
        path = self.repo_root / ".worktrees" / "swarm" / safe_run_id / safe_replica_id
        path.parent.mkdir(parents=True, exist_ok=True)
        _git(self.repo_root, ("worktree", "add", "-B", f"swarm-{safe_run_id}-{safe_replica_id}", str(path), checkpoint_commit))
        return path

    def _write_report(
        self,
        run_id: str,
        candidates: tuple[PatchCandidate, ...],
        clean: list[PatchCandidate],
        winner: PatchCandidate,
    ) -> Path:
        report_path = self.repo_root / ".omo" / "swarm" / "runs" / run_id / "reports" / "tournament.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        clean_ids = {candidate.replica_id for candidate in clean}
        lines = ["# Tournament", "", f"Winner: {winner.replica_id}", "", "| Replica | Applies | Score |", "|---|---|---|"]
        for candidate in candidates:
            applies = "yes" if candidate.replica_id in clean_ids else "no"
            lines.append(f"| {candidate.replica_id} | {applies} | {candidate.score_overall} |")
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return report_path


def _patch_applies(worktree: Path, patch_path: Path) -> bool:
    result = subprocess.run(["git", "-C", str(worktree), "apply", "--check", str(patch_path)], capture_output=True, check=False)
    return result.returncode == 0


def _remove_existing_worktree(repo: Path, path: Path) -> None:
    if not path.exists():
        return
    result = subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(path)], capture_output=True, check=False)
    if result.returncode != 0 and path.exists():
        shutil.rmtree(path)
    _git(repo, ("worktree", "prune"))


def _git(repo: Path, args: tuple[str, ...]) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _git_text(repo: Path, args: tuple[str, ...]) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return result.stdout
