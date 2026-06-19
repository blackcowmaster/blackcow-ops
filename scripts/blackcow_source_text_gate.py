#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blackcow_swarm_lib.source_text_gate import run_source_text_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Require expected UI text to appear in project source files.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--expect", action="append", default=[])
    args = parser.parse_args()
    result = run_source_text_gate(Path.cwd(), args.project, tuple(args.expect))
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
