#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# --- How to run ---
# 1. Install uv (optional for this stdlib-only script):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run with the system Python:
#      python3 scripts/blackcow_swarm.py [ARGS]
# 3. Or run through uv:
#      uv run scripts/blackcow_swarm.py [ARGS]
# ------------------

from __future__ import annotations

from blackcow_swarm_lib.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
