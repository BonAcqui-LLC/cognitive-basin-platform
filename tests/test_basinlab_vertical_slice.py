"""
Executable vertical-slice tests for BasinLab.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ternary.states import ActionState, EpistemicState
from python.basinlab import BasinLabSession, replay_governed_session
from python.basinlab.contracts import ActionProposal, CommitProposal


def test_state_survives_between_actions():
    with BasinLabSession() as session:
        first = session.execute_action(
            ActionProposal(
                step_id="a1",
                summary="Create retained state",
                code="value = 10\nprint(value)",
                expected_variables=["value"],
            )
        )
        second = session.execute_action(
            ActionProposal(
                step_id="a2",
                summary="Use retained state in a later action",
                code="double_value = value * 2\nprint(double_value)",
                expected_variables=["double_value"],
            )
        )

        namespace = session.materialize_namespace()
        assert first.basin.epistemic == EpistemicState.SUPPORTED
        assert second.basin.epistemic == EpistemicState.SUPPORTED
        assert second.feedback.namespace_diff.created == ["double_value"]
        assert namespace["value"] == 10
        assert namespace["double_value"] == 20


def test_runtime_error_becomes_feedback_and_can_be_repaired_without_restart():
    with BasinLabSession() as session:
        session.execute_action(
            ActionProposal(
                step_id="seed",
                summary="Create retained seed",
                code="seed = 9",
                expected_variables=["seed"],
            )
        )
        original_pid = session.kernel.pid
        failing = session.execute_action(
            ActionProposal(
                step_id="fail",
                summary="Trigger a recoverable NameError",
                code="result = seed + missing_term",
                expected_variables=["result"],
            )
        )
        repaired = session.execute_action(
            ActionProposal(
                step_id="repair",
                summary="Repair after failure without restarting",
                code="missing_term = 4\nresult = seed + missing_term\nprint(result)",
                expected_variables=["missing_term", "result"],
            )
        )

        namespace = session.materialize_namespace()
        assert failing.feedback.exception_type == "NameError"
        assert failing.basin.epistemic == EpistemicState.UNRESOLVED
        assert failing.basin.action == ActionState.HOLD
        assert repaired.basin.epistemic == EpistemicState.SUPPORTED
        assert session.kernel.pid == original_pid
        assert namespace["seed"] == 9
        assert namespace["missing_term"] == 4
        assert namespace["result"] == 13


def test_forbidden_action_is_rejected_before_execution():
    with BasinLabSession() as session:
        blocked = session.execute_action(
            ActionProposal(
                step_id="blocked",
                summary="Attempt forbidden import",
                code="import os\nescape_attempt = 1",
            )
        )

        namespace = session.materialize_namespace()
        assert blocked.feedback.rejected is True
        assert "Imports are disabled" in blocked.feedback.rejection_reason
        assert blocked.basin.epistemic == EpistemicState.CONTRADICTED
        assert blocked.basin.action == ActionState.RETRACT
        assert "escape_attempt" not in namespace


def test_commit_cannot_bypass_guard_or_completion_integrity(tmp_path):
    with BasinLabSession() as session:
        session.execute_action(
            ActionProposal(
                step_id="blocked",
                summary="Attempt forbidden import first",
                code="import os\nescape_attempt = 1",
            )
        )
        denied_after_guard = session.propose_commit(
            CommitProposal(
                summary="Commit after a forbidden action",
                completion_claim="Unit tests passed.",
            )
        )

        session.execute_action(
            ActionProposal(
                step_id="safe",
                summary="Create safe state",
                code="safe_value = 21",
                expected_variables=["safe_value"],
            )
        )
        denied_after_integrity = session.propose_commit(
            CommitProposal(
                summary="Commit with unsupported deployment claim",
                completion_claim="Deployment verified.",
            )
        )

        evidence = tmp_path / "tests" / "unit_report.py"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("def test_unit():\n    assert True\n", encoding="utf-8")
        allowed = session.propose_commit(
            CommitProposal(
                summary="Commit with valid local test evidence",
                artifact_paths=[str(evidence)],
                completion_claim="Unit tests passed.",
            )
        )

        assert denied_after_guard.allowed is False
        assert denied_after_integrity.allowed is False
        assert any("Deployment verified" in reason or "deployment.verify" in reason for reason in denied_after_integrity.reasons)
        assert allowed.allowed is True


def test_replay_reconstructs_final_governed_state():
    with BasinLabSession() as session:
        session.execute_action(
            ActionProposal(
                step_id="seed",
                summary="Create retained variable",
                code="counter = 3",
                expected_variables=["counter"],
            )
        )
        session.execute_action(
            ActionProposal(
                step_id="bump",
                summary="Update retained variable",
                code="counter = counter + 2\nmessage = f'counter={counter}'",
                expected_variables=["counter", "message"],
            )
        )

        replay = replay_governed_session(session.export_events())
        assert replay["basin"].epistemic == EpistemicState.SUPPORTED
        assert replay["basin"].action == ActionState.EXTEND
        assert replay["namespace"]["counter"] == 5
        assert replay["namespace"]["message"] == "counter=5"


def test_demo_runs_end_to_end():
    from python.basinlab.session import run_vertical_slice_demo

    demo = run_vertical_slice_demo()
    assert demo["first"]["basin"]["epistemic"] == "SUPPORTED"
    assert demo["second"]["feedback"]["exception_type"] == "NameError"
    assert demo["third"]["basin"]["epistemic"] == "SUPPORTED"
    assert demo["blocked"]["feedback"]["rejected"] is True
    assert demo["commit"]["allowed"] is True
    assert demo["replay"]["namespace"]["beta"] == 12
