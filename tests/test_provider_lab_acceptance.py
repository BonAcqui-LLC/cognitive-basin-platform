"""
Provider lab routing, ledger, and acceptance tests.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.provider_lab import ProviderLedger, ProviderPolicy, ProviderRequest, ProviderRouter, ROLE_COMPACT_REASONER, ROLE_GENERALIST, new_invocation_id
from python.provider_lab.acceptance import run_acceptance_suite
from python.basinlab.providers import CompactReasonerProvider, GeneralistProvider, VibeThinkerProvider


def test_provider_lab_acceptance_runner_passes(tmp_path):
    summary = run_acceptance_suite(tmp_path)
    assert summary["passed"] is True
    assert summary["scenario_count"] == 7
    assert len(summary["ledger_entries"]) >= 2
    assert (tmp_path / "provider-lab-acceptance-summary.json").exists()


def test_provider_lab_module_entrypoint(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "provider_lab.acceptance", "--all", "--artifact-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "provider-lab-acceptance-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] is True


def test_provider_router_prefers_role_specific_adapters(tmp_path):
    router = ProviderRouter(
        [
            GeneralistProvider(scripted_outputs=[{"answer": "plan", "reasoning": "r", "approach": "a"}]),
            CompactReasonerProvider(scripted_outputs=[{"answer": "5", "reasoning": "r", "approach": "a"}]),
            VibeThinkerProvider(),
        ]
    )
    ledger = ProviderLedger(tmp_path)
    plan = router.invoke(
        ProviderRequest(
            invocation_id=new_invocation_id(),
            session_id="s1",
            role=ROLE_GENERALIST,
            task_domain="code",
            prompt="plan",
        ),
        ProviderPolicy(),
        ledger,
    )
    compact = router.invoke(
        ProviderRequest(
            invocation_id=new_invocation_id(),
            session_id="s2",
            role=ROLE_COMPACT_REASONER,
            task_domain="arithmetic",
            prompt="2 + 3",
            claims_requested=["2 + 3 = 5"],
        ),
        ProviderPolicy(),
        ledger,
    )
    assert plan.receipt is not None and plan.receipt.provider == "generalist"
    assert compact.receipt is not None and compact.receipt.provider == "compact-reasoner"
    assert compact.outputs[0]["candidate_reasoning_packet"]["no_action_request"] is True
