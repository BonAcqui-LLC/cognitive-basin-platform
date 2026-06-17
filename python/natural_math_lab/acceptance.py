"""
Deterministic Natural Math lab acceptance runner.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

from .core import generate_visualizations, run_parameter_sweep, run_simulation
from .geometry import RationalLine, RationalPoint, exact_equal, quadrance, spread


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    root = Path(artifact_dir) if artifact_dir else None
    if root:
        root.mkdir(parents=True, exist_ok=True)

    simulation = run_simulation(seed=31, steps=6)
    sweep = run_parameter_sweep()
    visualization_root = root / "visualizations" if root else Path(tempfile.mkdtemp(prefix="natural-math-visualizations-"))
    visualizations = generate_visualizations(simulation, visualization_root)
    exact_quadrance = quadrance(RationalPoint(0, 0), RationalPoint(3, 4))
    right_spread = spread(RationalLine(1, 0, 0), RationalLine(0, 1, 0))
    summary = {
        "passed": simulation["simulation_metrics"]["node_count"] >= 3
        and sweep["run_count"] == 3
        and exact_equal(exact_quadrance, 25)
        and exact_equal(right_spread, 1),
        "simulation": simulation,
        "parameter_sweep": sweep,
        "visualizations": visualizations,
        "exact_geometry": {"quadrance": str(exact_quadrance), "right_spread": str(right_spread)},
    }
    if root:
        (root / "natural-math-lab-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"NaturalMathLab acceptance: passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
