"""
Acceptance and CLI tests for BasinLab.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_acceptance_runner_passes(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "basinlab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    summary = json.loads((tmp_path / "acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True
    assert summary["scenario_count"] == 16


def test_cli_run_single_scenario_json():
    result = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "run", "verified_compression", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["scenario"] == "verified_compression"
    assert payload["passed"] is True


def test_cli_capabilities_and_providers_json():
    caps = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "capabilities", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    providers = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "providers", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert caps.returncode == 0
    assert providers.returncode == 0
    assert "persistent_composition" in json.loads(caps.stdout)["scenarios"]
    assert any(item["name"] == "vibethinker" for item in json.loads(providers.stdout))
