#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blackcow_swarm_lib.expo_clean_gate import run_expo_clean_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Require no-install-clean Expo/React Native scaffold config.")
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    result = run_expo_clean_gate(Path.cwd(), args.project)
    print(result.message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
