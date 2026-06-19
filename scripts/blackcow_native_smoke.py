#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from blackcow_swarm_lib.native_smoke import run_native_capability_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Require native simulator capability for React Native work.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--platform", choices=("ios",), required=True)
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    if args.screenshot:
        from pathlib import Path

        from blackcow_swarm_lib.native_smoke import run_native_smoke

        result = run_native_smoke(args.project, args.platform, screenshot_path=Path(args.screenshot))
    else:
        result = run_native_capability_gate(args.project, args.platform)
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
