"""
Aggregate deterministic acceptance tests.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.cognitive_basin.acceptance import run_acceptance_suite


def test_aggregate_acceptance_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert "evaluation_lab" in summary["suites"]
    assert (tmp_path / "combined-acceptance-manifest.json").exists()


def test_aggregate_acceptance_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "cognitive_basin.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "combined-acceptance-manifest.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
