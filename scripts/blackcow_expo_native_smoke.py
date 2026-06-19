#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blackcow_swarm_lib.expo_native_smoke import run_expo_native_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch an Expo native app, capture simulator screenshot, and run visual review.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--platform", choices=("ios",), required=True)
    parser.add_argument("--screenshot", required=True)
    parser.add_argument("--review-output", required=True)
    parser.add_argument("--expect", action="append", default=[])
    args = parser.parse_args()
    result = run_expo_native_smoke(
        project_root=Path.cwd(),
        project=args.project,
        platform=args.platform,
        screenshot_path=Path(args.screenshot),
        review_output=Path(args.review_output),
        expect=tuple(args.expect),
    )
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
