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
    assert "memory_governance" in summary["suites"]
    assert "action_permit" in summary["suites"]
    assert "connector_lab" in summary["suites"]
    assert "consciousness_lab" in summary["suites"]
    assert "predictive_cognition" in summary["suites"]
    assert len(summary["suites"]) == 11
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


def test_aggregate_acceptance_fails_when_memory_governance_fails(monkeypatch, tmp_path):
    from python import cognitive_basin as pkg  # noqa: F401
    import python.cognitive_basin.acceptance as acceptance

    def fake_memory_suite(_artifact_dir=None):
        return {
            "passed": False,
            "scenario_count": 20,
            "limitations": ["forced failure"],
        }

    monkeypatch.setattr(acceptance, "run_action_permit_acceptance", fake_memory_suite)
    summary = acceptance.run_acceptance_suite(tmp_path)
    assert summary["passed"] is False
    assert summary["suites"]["action_permit"]["result"] == "FAIL"
