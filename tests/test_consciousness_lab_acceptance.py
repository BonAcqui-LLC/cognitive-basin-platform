"""
Acceptance and demo tests for the operational consciousness tranche.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.consciousness_lab.acceptance import run_acceptance_suite
from python.consciousness_lab.demo import run_demo


def test_consciousness_acceptance_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["scenario_count"] == 40
    assert (tmp_path / "consciousness-acceptance-summary.json").exists()


def test_consciousness_acceptance_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "consciousness_lab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "consciousness-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True


def test_consciousness_demo_runs_end_to_end():
    demo = run_demo()
    assert demo["hold_cycle"]["basin"]["action"] == "HOLD"
    assert demo["conflict_cycle"]["episode_receipt"]["episode"]["decision"]["disposition"] == "RETRACT"
    assert demo["recovered_cycle"]["episode_receipt"]["episode"]["action"]["executed"] is True
    assert demo["final_snapshot"]["episodes"]
