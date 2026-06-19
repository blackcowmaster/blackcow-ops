#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blackcow_swarm_lib.speed_gate import run_speed_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Require measured swarm speedup evidence.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--min-speedup", type=float, required=True)
    args = parser.parse_args()
    result = run_speed_gate(Path(args.run_dir), min_speedup=args.min_speedup)
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
