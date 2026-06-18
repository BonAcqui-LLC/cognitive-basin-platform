"""
Deterministic memory-governance acceptance tests.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.memory_governance.acceptance import run_acceptance_suite


def test_memory_governance_acceptance_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["scenario_count"] == 27
    assert summary["exact_commit"]
    assert (tmp_path / "memory-governance-acceptance-summary.json").exists()


def test_memory_governance_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "memory_governance.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "memory-governance-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
