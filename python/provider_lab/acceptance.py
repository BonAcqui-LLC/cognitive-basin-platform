"""
Deterministic provider-lab acceptance runner.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from packages.completion_integrity.guard import attempt_transition
from python.basinlab.contracts import ActionProposal, CommitProposal
from python.basinlab.providers import CompactReasonerProvider, GeneralistProvider, ScriptedProvider, VibeThinkerProvider
from python.basinlab.reliability import DecisionClaim, ReliabilityEngine
from python.basinlab.session import BasinLabSession
from python.basinlab.spectrum import CandidateTrajectory
from python.cognitive_basin.pipeline import CommitGate

from . import (
    ProviderLedger,
    ProviderPolicy,
    ProviderRequest,
    ProviderRouter,
    ROLE_COMPACT_REASONER,
    ROLE_GENERALIST,
    ROLE_VERIFIER,
    local_model_inventory,
    new_invocation_id,
    provider_inventory,
)


def _build_router() -> ProviderRouter:
    return ProviderRouter(
        [
            GeneralistProvider(
                scripted_outputs=[
                    {
                        "trajectory_id": "plan-1",
                        "answer": "1. Inspect evidence 2. Execute bounded check 3. Evaluate claims",
                        "reasoning": "Bound the work to one verified step at a time.",
                        "approach": "planning",
                        "decision_claims": ["A bounded plan should be produced before action execution."],
                    }
                ]
            ),
            CompactReasonerProvider(
                scripted_outputs=[
                    {
                        "trajectory_id": "compact-1",
                        "answer": "5",
                        "reasoning": "Add 2 and 3 under the supplied bounded subproblem only.",
                        "approach": "compact-math",
                        "decision_claims": ["2 + 3 = 5"],
                        "predictions": [{"text": "Run deterministic arithmetic check", "required_evidence": ["python-exec"]}],
                    }
                ]
            ),
            ScriptedProvider(
                name="scripted",
                scripted_outputs=[
                    {
                        "trajectory_id": "verify-1",
                        "answer": "verified",
                        "reasoning": "Use the deterministic execution receipt.",
                        "approach": "verification",
                        "decision_claims": ["Execution output matched expected arithmetic result."],
                    }
                ],
            ),
            VibeThinkerProvider(),
        ]
    )


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    artifact_root = Path(artifact_dir) if artifact_dir else None
    if artifact_root:
        artifact_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        ledger = ProviderLedger(Path(td) / "ledger")
        router = _build_router()
        policy = ProviderPolicy(budget_policy="existing-allowance-only", allow_remote=False, allow_live_calls=False)

        plan_request = ProviderRequest(
            invocation_id=new_invocation_id(),
            session_id="provider-acceptance",
            role=ROLE_GENERALIST,
            task_domain="code",
            prompt="Plan a bounded verification flow",
            candidate_count=1,
            claims_requested=["bounded-plan"],
        )
        plan_response = router.invoke(plan_request, policy, ledger)

        compact_request = ProviderRequest(
            invocation_id=new_invocation_id(),
            session_id="provider-acceptance",
            role=ROLE_COMPACT_REASONER,
            task_domain="arithmetic",
            prompt="Solve only the bounded subproblem: 2 + 3",
            candidate_count=1,
            claims_requested=["2 + 3 = 5"],
            prohibited_assumptions=["No tool calls", "No filesystem access"],
        )
        compact_response = router.invoke(compact_request, policy, ledger)

        with BasinLabSession() as session:
            execution = session.execute_action(
                ActionProposal(
                    step_id="verify-arithmetic",
                    summary="Execute arithmetic verification",
                    code="result = 2 + 3\nprint(result)",
                )
            )
            with tempfile.TemporaryDirectory() as commit_td:
                evidence = Path(commit_td) / "tests" / "unit_result.py"
                evidence.parent.mkdir(parents=True, exist_ok=True)
                evidence.write_text("def test_ok():\n    assert 2 + 3 == 5\n", encoding="utf-8")
                allowed_commit = session.propose_commit(
                    CommitProposal(
                        summary="allow commit proposal",
                        artifact_paths=[str(evidence)],
                        completion_claim="Unit tests passed.",
                        parent_event_id=execution.event_id,
                    )
                )
            denied_commit = session.propose_commit(
                CommitProposal(
                    summary="deny unsupported claim",
                    artifact_paths=[],
                    completion_claim="Production operational.",
                    parent_event_id=execution.event_id,
                )
            )

        reliability = ReliabilityEngine().evaluate(
            [
                CandidateTrajectory("majority-a", "4", "wrong arithmetic", "fast", "generalist"),
                CandidateTrajectory("majority-b", "4", "wrong arithmetic repeated", "fast-2", "generalist"),
                CandidateTrajectory("minority", "5", "checked arithmetic", "verified", "compact-reasoner"),
            ],
            {
                "majority-a": [DecisionClaim("c-a", "2 + 3 = 4", "majority-a", critical=True, contradictory_evidence=["python-exec says 5"])],
                "majority-b": [DecisionClaim("c-b", "2 + 3 = 4", "majority-b", critical=True, contradictory_evidence=["python-exec says 5"])],
                "minority": [DecisionClaim("c-c", "2 + 3 = 5", "minority", critical=True, supporting_evidence=["python-exec says 5"])],
            },
        )

        guard_block = attempt_transition(
            capability_name="production.operational",
            artifact_paths=[],
            claimed_status="IMPLEMENTED",
            output_claim="Production operational.",
        )

        summary = {
            "passed": all(
                [
                    plan_response.outputs and plan_response.receipt is not None,
                    compact_response.outputs
                    and "problem_packet" in compact_response.outputs[0]
                    and compact_response.outputs[0]["candidate_reasoning_packet"]["no_action_request"] is True,
                    execution.feedback.stdout.strip() == "5",
                    bool(compact_response.claims),
                    reliability.winning_answer == "5",
                    guard_block.allowed is False,
                    allowed_commit.allowed is True,
                    denied_commit.allowed is False,
                ]
            ),
            "scenario_count": 7,
            "results": [
                {"scenario": "generalist_bounded_plan", "passed": bool(plan_response.outputs), "route": plan_response.receipt.route.to_record() if plan_response.receipt else {}},
                {"scenario": "compact_reasoner_bounded_subproblem", "passed": bool(compact_response.outputs), "packet": compact_response.outputs[0] if compact_response.outputs else {}},
                {"scenario": "candidate_output_executed_or_checked", "passed": execution.feedback.stdout.strip() == "5", "runner_receipt": execution.feedback.runner_receipt},
                {"scenario": "decision_critical_claims_extracted", "passed": bool(compact_response.claims), "claims": compact_response.claims},
                {"scenario": "rigor_evaluates_evidence", "passed": reliability.winning_answer == "5", "winning_trajectory_id": reliability.winning_trajectory_id},
                {"scenario": "guard_blocks_unsupported_capability_language", "passed": guard_block.allowed is False, "reason": guard_block.reason},
                {"scenario": "commit_gate_allows_and_denies", "passed": allowed_commit.allowed and not denied_commit.allowed, "allow": allowed_commit.to_record(), "deny": denied_commit.to_record()},
            ],
            "ledger_entries": ledger.read_all(),
            "provider_inventory": provider_inventory(),
            "local_model_inventory": local_model_inventory(),
            "aggregate_commit_gate": CommitGate().allow({"allowed": allowed_commit.allowed, "provisional": allowed_commit.basin.provisional}),
        }

        if artifact_root:
            (artifact_root / "provider-lab-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"ProviderLab acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
