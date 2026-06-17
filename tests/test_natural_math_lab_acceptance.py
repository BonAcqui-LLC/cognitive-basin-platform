"""
Natural Math lab and exact geometry tests.
"""

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.natural_math_lab.acceptance import run_acceptance_suite
from python.natural_math_lab.core import run_parameter_sweep, run_simulation
from python.natural_math_lab.geometry import RationalLine, RationalPoint, exact_equal, quadrance, spread


def test_natural_math_simulation_and_sweep_are_deterministic():
    first = run_simulation(seed=31, steps=4)
    second = run_simulation(seed=31, steps=4)
    assert first["simulation_evidence"]["final_state_hash"] == second["simulation_evidence"]["final_state_hash"]
    sweep = run_parameter_sweep()
    assert sweep["run_count"] == 3
    assert all(run["repository_commit"] != "unknown" for run in sweep["runs"])


def test_exact_geometry_edge_cases():
    assert exact_equal(quadrance(RationalPoint(Fraction(0), Fraction(0)), RationalPoint(Fraction(3), Fraction(4))), Fraction(25))
    assert exact_equal(spread(RationalLine(Fraction(1), Fraction(0), Fraction(0)), RationalLine(Fraction(0), Fraction(1), Fraction(0))), Fraction(1))


def test_natural_math_lab_acceptance_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert Path(summary["visualizations"]["world_state"]).exists()
    assert (tmp_path / "natural-math-lab-acceptance-summary.json").exists()


def test_natural_math_lab_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "natural_math_lab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "natural-math-lab-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
