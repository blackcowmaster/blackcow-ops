#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blackcow_swarm_lib.web_smoke import run_managed_web_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a web app, run browser smoke, then stop it.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--expect", action="append", default=[])
    parser.add_argument("--reject", action="append", default=[])
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    result = run_managed_web_smoke(
        project_root=Path.cwd(),
        project=args.project,
        port=args.port,
        expect=tuple(args.expect),
        reject=tuple(args.reject),
        screenshot_path=Path(args.screenshot) if args.screenshot else None,
    )
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
