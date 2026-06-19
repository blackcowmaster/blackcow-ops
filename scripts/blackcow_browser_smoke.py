#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from blackcow_swarm_lib.browser_smoke import run_browser_smoke


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a headless Chrome DOM smoke check.")
    parser.add_argument("url")
    parser.add_argument("--expect", action="append", default=[])
    parser.add_argument("--reject", action="append", default=[])
    parser.add_argument("--screenshot")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    screenshot_path = None
    if args.screenshot:
        from pathlib import Path

        screenshot_path = Path(args.screenshot)
    result = run_browser_smoke(args.url, expect=tuple(args.expect), reject=tuple(args.reject), screenshot_path=screenshot_path)
    if result.ok:
        print("browser-smoke ok")
        return 0
    print("browser-smoke failed: " + result.error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
