from __future__ import annotations

import unittest

from scripts.blackcow_swarm_lib.lifecycle import compute_resume_actions, should_hard_timeout


class TestResume(unittest.TestCase):
    def test_succeeded_task_not_rerun_and_stale_running_retried(self) -> None:
        state = {
            "workers": {
                "D1-r1": {"task_id": "D1", "status": "SUCCEEDED", "attempts": 1, "lease_ts": 100.0},
                "C1-r1": {"task_id": "C1", "status": "RUNNING", "attempts": 1, "lease_ts": 10.0},
            }
        }

        actions = compute_resume_actions(state, now=200.0, stale_after_seconds=60)

        self.assertEqual(actions.skip_workers, ("D1-r1",))
        self.assertEqual(actions.retry_workers, ("C1-r1",))

    def test_live_silent_process_waits_until_hard_timeout(self) -> None:
        self.assertFalse(should_hard_timeout(started_at=100.0, now=150.0, hard_timeout_seconds=60))
        self.assertTrue(should_hard_timeout(started_at=100.0, now=161.0, hard_timeout_seconds=60))


if __name__ == "__main__":
    unittest.main()
