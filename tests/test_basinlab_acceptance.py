"""
Acceptance and CLI tests for BasinLab.
"""

import json
import subprocess
import sys
import tempfile
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
    assert summary["trajectory_report_count"] == 16


def test_cli_run_single_scenario_json():
    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, "-m", "basinlab.cli.main", "--store-dir", td, "run", "verified_compression", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["scenario"] == "verified_compression"
        assert payload["passed"] is True
        assert payload["session_id"]


def test_cli_persisted_inspect_replay_and_diff_json(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "--store-dir", str(tmp_path), "run-all", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    first, second = payload["session_ids"][:2]
    inspect = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "--store-dir", str(tmp_path), "inspect", first, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    replay = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "--store-dir", str(tmp_path), "replay", first, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    diff = subprocess.run(
        [sys.executable, "-m", "basinlab.cli.main", "--store-dir", str(tmp_path), "diff", first, second, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert inspect.returncode == 0
    assert replay.returncode == 0
    assert diff.returncode == 0
    assert json.loads(inspect.stdout)["session_id"] == first
    assert json.loads(replay.stdout)["replay_hash"]
    assert "event_count_delta" in json.loads(diff.stdout)


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
    assert "completion_integrity.guard" in json.loads(caps.stdout)["registry_entries"]
    provider_payload = json.loads(providers.stdout)
    assert any(item["name"] == "vibethinker" for item in provider_payload["providers"])
    assert "local_model_inventory" in provider_payload
