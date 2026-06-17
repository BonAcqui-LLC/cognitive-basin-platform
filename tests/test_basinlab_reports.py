"""
Trajectory report tests for BasinLab.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.basinlab.demos import run_all_scenarios
from python.basinlab.reports import build_static_html, write_report_bundle


def test_static_html_escapes_hostile_content(tmp_path):
    report = {
        "scenario": "escape_test",
        "passed": True,
        "execution_output": [{"stdout": "<script>alert(1)</script>", "stderr": ""}],
        "final_basin_state": {"epistemic": "SUPPORTED", "action": "EXTEND", "provisional": False, "reason": "ok"},
    }
    html = build_static_html(report)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_acceptance_writes_sixteen_html_and_json_reports(tmp_path):
    summary = run_all_scenarios(tmp_path)
    reports_dir = tmp_path / "trajectory-reports"
    html_reports = sorted(reports_dir.glob("*.html"))
    json_reports = sorted(reports_dir.glob("*.json"))
    assert summary["scenario_count"] == 16
    assert len(html_reports) == 16
    assert len(json_reports) == 16
    assert (tmp_path / "acceptance-summary.json").exists()
    assert (tmp_path / "capability-registry-snapshot.json").exists()
