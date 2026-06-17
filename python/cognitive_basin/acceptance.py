"""
Aggregate deterministic acceptance entrypoint.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from python.basinlab.demos import run_all_scenarios
from python.ephux_local.acceptance import run_acceptance_suite as run_ephux_acceptance
from python.evaluation_lab.acceptance import run_acceptance_suite as run_evaluation_acceptance
from python.natural_math_lab.acceptance import run_acceptance_suite as run_natural_math_acceptance
from python.provider_lab.acceptance import run_acceptance_suite as run_provider_acceptance
from python.sandbox_lab.acceptance import run_acceptance_suite as run_sandbox_acceptance


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> dict:
    root = Path(artifact_dir) if artifact_dir else None
    if root:
        root.mkdir(parents=True, exist_ok=True)
    basinlab = run_all_scenarios((root / "basinlab") if root else None)
    ephux = run_ephux_acceptance((root / "ephux") if root else None)
    provider = run_provider_acceptance((root / "provider_lab") if root else None)
    sandbox = run_sandbox_acceptance((root / "sandbox_lab") if root else None)
    evaluation = run_evaluation_acceptance((root / "evaluation_lab") if root else None)
    natural_math = run_natural_math_acceptance((root / "natural_math_lab") if root else None)
    summary = {
        "passed": all(
            [
                basinlab["passed"],
                ephux["passed"],
                provider["passed"],
                sandbox["passed"],
                evaluation["passed"],
                natural_math["passed"],
            ]
        ),
        "suites": {
            "basinlab": {"passed": basinlab["passed"], "scenario_count": basinlab["scenario_count"]},
            "ephux_local": {"passed": ephux["passed"], "scenario_count": ephux["scenario_count"]},
            "provider_lab": {"passed": provider["passed"], "scenario_count": provider["scenario_count"]},
            "sandbox_lab": {"passed": sandbox["passed"], "scenario_count": sandbox["scenario_count"]},
            "evaluation_lab": {"passed": evaluation["passed"], "task_count": evaluation["task_count"]},
            "natural_math_lab": {"passed": natural_math["passed"], "run_count": natural_math["parameter_sweep"]["run_count"]},
        },
    }
    if root:
        (root / "combined-acceptance-manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
