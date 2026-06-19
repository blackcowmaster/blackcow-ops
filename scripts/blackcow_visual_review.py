#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blackcow_swarm_lib.visual_review import run_visual_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Codex image-based visual acceptance review.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expect", action="append", default=[])
    args = parser.parse_args()
    result = run_visual_review(Path(args.image), Path(args.output), expect=tuple(args.expect))
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
