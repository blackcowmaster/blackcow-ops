from __future__ import annotations

import unittest

from scripts.blackcow_swarm_lib.scheduler_rules import worker_run_succeeded, worker_status


class TestLifecycleWorkerStatus(unittest.TestCase):
    def test_worker_status_succeeds_when_one_race_group_replica_succeeds(self) -> None:
        states = {
            "coder-1-r1": "FAILED_RETRYABLE",
            "coder-1-r2": "SUCCEEDED",
            "review-1-r1": "SUCCEEDED",
        }

        self.assertTrue(worker_run_succeeded(states))
        self.assertEqual(worker_status(states), "SUCCEEDED")

    def test_worker_status_fails_when_race_group_fails_and_dependents_block(self) -> None:
        states = {
            "coder-1-r1": "FAILED_RETRYABLE",
            "coder-1-r2": "FAILED_FINAL",
            "review-1-r1": "BLOCKED",
        }

        self.assertFalse(worker_run_succeeded(states))
        self.assertEqual(worker_status(states), "FAILED")


if __name__ == "__main__":
    unittest.main()
