from __future__ import annotations

import unittest

from scripts.blackcow_swarm_lib.lifecycle import DynamicThrottle


class TestThrottle(unittest.TestCase):
    def test_repeated_rate_limit_cuts_concurrency_by_half(self) -> None:
        throttle = DynamicThrottle(active_workers=10)

        throttle.observe_worker_output("HTTP 429 rate limit")
        throttle.observe_worker_output("timeout while retrying after rate limit")

        self.assertEqual(throttle.active_workers, 5)


if __name__ == "__main__":
    unittest.main()
