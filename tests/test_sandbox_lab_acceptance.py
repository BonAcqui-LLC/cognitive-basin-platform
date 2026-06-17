"""
Sandbox runner and adversarial acceptance tests.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.basinlab import BasinLabSession
from python.basinlab.contracts import ActionProposal
from python.sandbox_lab.acceptance import run_acceptance_suite


def test_sandbox_lab_acceptance_runner_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["scenario_count"] >= 19
    assert (tmp_path / "sandbox-lab-acceptance-summary.json").exists()


def test_sandbox_lab_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "sandbox_lab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "sandbox-lab-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True


def test_runner_receipt_is_recorded_on_success_and_timeout():
    with BasinLabSession() as session:
        safe = session.execute_action(ActionProposal("safe", "simple arithmetic", "value = 1 + 1"))
        timeout = session.execute_action(
            ActionProposal(
                "timeout",
                "hang",
                "while True:\n    pass",
                max_duration_s=0.2,
                parent_event_id=safe.event_id,
            )
        )
        assert safe.feedback.runner_receipt["runner_type"] == "subprocess"
        assert safe.feedback.runner_receipt["restriction_classification"]["timeout"] == "BEST_EFFORT"
        assert timeout.feedback.runner_receipt["runner_type"] == "subprocess"
        assert timeout.feedback.timed_out is True
