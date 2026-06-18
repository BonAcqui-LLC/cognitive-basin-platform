"""
Predictive cognition acceptance and demo tests.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.predictive_cognition import run_acceptance_suite


def test_predictive_cognition_acceptance_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["scenario_count"] == 55


def test_predictive_cognition_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "predictive_cognition.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "predictive-cognition-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True


def test_predictive_cognition_demo_runs():
    result = subprocess.run(
        [sys.executable, "-m", "predictive_cognition.demo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["final_snapshot"]["world"]
    assert payload["final_snapshot"]["prediction"]
