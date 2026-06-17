"""
Acceptance runner for deterministic BasinLab demonstrations.
"""

from __future__ import annotations

import argparse
import json

from .demos import run_all_scenarios


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()

    if not args.all:
        parser.error("Only --all is currently supported")

    summary = run_all_scenarios(artifact_dir=args.artifact_dir or None)
    print(f"BasinLab acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
