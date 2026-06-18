"""
Deterministic connector acceptance tests.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.connector_lab.acceptance import run_acceptance_suite


def test_connector_lab_acceptance_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["scenario_count"] == 28
    assert (tmp_path / "connector-lab-acceptance-summary.json").exists()


def test_connector_lab_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "connector_lab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "connector-lab-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
