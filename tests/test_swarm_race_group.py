from __future__ import annotations

import unittest

from scripts.blackcow_swarm_lib.tournament import RaceCandidate, select_race_winner


class TestRaceGroup(unittest.TestCase):
    def test_failed_fast_pass_slow_selects_passing_candidate(self) -> None:
        decision = select_race_winner(
            (
                RaceCandidate("C1-r1", "FAILED_RETRYABLE", 40, 10, 1.0),
                RaceCandidate("C1-r2", "SUCCEEDED", 90, 12, 2.0),
                RaceCandidate("C1-r3", "RUNNING", 0, 0, 9.0),
            ),
            discard_running_losers=True,
        )

        self.assertEqual(decision.winner.replica_id, "C1-r2")
        self.assertEqual(decision.loser_actions["C1-r3"], "DISCARDED")


if __name__ == "__main__":
    unittest.main()
