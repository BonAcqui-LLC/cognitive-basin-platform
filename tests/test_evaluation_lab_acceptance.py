"""
Evaluation lab registry and acceptance tests.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.evaluation_lab import build_task_registry, run_evaluation_suite


def test_evaluation_registry_covers_expected_families():
    tasks, families = build_task_registry()
    family_ids = {family.family_id for family in families}
    assert len(tasks) >= 19
    assert "natural_math" in family_ids
    assert "capability_boundary_sampling" in family_ids


def test_evaluation_lab_acceptance_passes(tmp_path):
    summary = run_evaluation_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["task_count"] >= 19
    assert summary["comparison_result_count"] >= 40
    assert summary["majority_wrong_cases"][0]["winner"] == "m3"


def test_evaluation_lab_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "evaluation_lab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "evaluation-lab-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
