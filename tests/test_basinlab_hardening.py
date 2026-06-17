"""
Kernel lifecycle and hardening tests for BasinLab.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ternary.states import ActionState, EpistemicState
from python.basinlab import BasinLabSession
from python.basinlab.contracts import ActionProposal, CommitProposal
from python.basinlab.kernel.subprocess_kernel import KernelProtocolError


def test_worker_crash_recovery_restores_checkpoint():
    with BasinLabSession() as session:
        seeded = session.execute_action(ActionProposal("seed", "Seed value", "value = 11"))
        session.kernel.simulate_crash_for_test()
        repaired = session.execute_action(
            ActionProposal(
                "after-crash",
                "Use restored state after crash",
                "value = value + 1",
                parent_event_id=seeded.event_id,
            )
        )
        namespace = session.materialize_namespace()
        assert repaired.feedback.worker_recovered is True
        assert repaired.basin.epistemic == EpistemicState.SUPPORTED
        assert namespace["value"] == 12


def test_timeout_restores_last_checkpoint():
    with BasinLabSession() as session:
        seeded = session.execute_action(ActionProposal("seed", "Seed state", "value = 3"))
        timed_out = session.execute_action(
            ActionProposal(
                "timeout",
                "Loop forever",
                "while True:\n    pass",
                max_duration_s=0.2,
                parent_event_id=seeded.event_id,
            )
        )
        recovered = session.execute_action(
            ActionProposal(
                "recover",
                "Confirm prior checkpoint remains",
                "value = value + 5",
                parent_event_id=timed_out.event_id,
            )
        )
        assert timed_out.feedback.timed_out is True
        assert timed_out.basin.action == ActionState.HOLD
        assert recovered.feedback.worker_recovered is False
        assert session.materialize_namespace()["value"] == 8


def test_excessive_stdout_is_truncated():
    with BasinLabSession() as session:
        result = session.execute_action(
            ActionProposal(
                "loud",
                "Generate large stdout",
                "print('x' * 12000)",
            )
        )
        assert result.feedback.stdout_truncated is True
        assert "[truncated by BasinLab worker]" in result.feedback.stdout


def test_nonserializable_values_are_summarized_but_not_checkpointed():
    with BasinLabSession() as session:
        result = session.execute_action(
            ActionProposal(
                "lambda",
                "Create a nonserializable function value",
                "helper = lambda x: x + 1",
            )
        )
        assert result.feedback.namespace_summary["helper"].serializable is False
        assert "helper" not in session.materialize_namespace()


def test_namespace_deletion_is_detected():
    with BasinLabSession() as session:
        first = session.execute_action(ActionProposal("seed", "Create vars", "alpha = 1\nbeta = 2"))
        deleted = session.execute_action(
            ActionProposal(
                "delete",
                "Delete one variable",
                "del beta",
                parent_event_id=first.event_id,
            )
        )
        assert deleted.feedback.namespace_diff.deleted == ["beta"]
        assert "beta" not in session.inspect_namespace()


def test_reset_clears_state():
    with BasinLabSession() as session:
        session.execute_action(ActionProposal("seed", "Create vars", "alpha = 1"))
        session.reset()
        assert session.materialize_namespace() == {}


def test_restore_into_fresh_process_rehydrates_state():
    with BasinLabSession() as session:
        session.execute_action(ActionProposal("seed", "Create vars", "alpha = 4\nbeta = 9"))
        old_pid = session.kernel.pid
        restored = session.restore_checkpoint_in_fresh_process()
        assert session.kernel.pid != old_pid
        assert restored["alpha"] == 4
        assert restored["beta"] == 9


def test_malformed_protocol_message_returns_error():
    with BasinLabSession() as session:
        error = session.kernel.send_malformed_message_for_test()
        assert "worker protocol failure" in error


def test_unknown_protocol_operation_raises():
    with BasinLabSession() as session:
        try:
            session.kernel.protocol_request({"op": "unknown-op"}, timeout_s=1.0)
        except KernelProtocolError as exc:
            assert "Unknown op" in str(exc)
        else:
            raise AssertionError("Expected KernelProtocolError for unknown protocol op")


def test_duplicate_action_id_is_rejected():
    with BasinLabSession() as session:
        session.execute_action(ActionProposal("seed", "Create vars", "alpha = 1"))
        duplicate = session.execute_action(ActionProposal("seed", "Reuse ID", "alpha = 2"))
        assert duplicate.feedback.rejected is True
        assert "Duplicate action ID" in duplicate.feedback.rejection_reason


def test_repeated_commit_attempt_is_rejected(tmp_path):
    with BasinLabSession() as session:
        action = session.execute_action(ActionProposal("safe", "Create state", "alpha = 1"))
        evidence = tmp_path / "tests" / "unit.py"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        first = session.propose_commit(
            CommitProposal(
                "commit-once",
                artifact_paths=[str(evidence)],
                completion_claim="Unit tests passed.",
                parent_event_id=action.event_id,
            )
        )
        second = session.propose_commit(
            CommitProposal(
                "commit-twice",
                artifact_paths=[str(evidence)],
                completion_claim="Unit tests passed.",
                parent_event_id=action.event_id,
            )
        )
        assert first.allowed is True
        assert second.allowed is False
        assert any("Repeated commit attempt" in reason for reason in second.reasons)


def test_stale_parent_event_is_rejected():
    with BasinLabSession() as session:
        first = session.execute_action(ActionProposal("a1", "Create vars", "alpha = 1"))
        second = session.execute_action(
            ActionProposal("a2", "Advance", "beta = alpha + 1", parent_event_id=first.event_id)
        )
        stale = session.execute_action(
            ActionProposal("a3", "Use stale parent", "gamma = 3", parent_event_id=first.event_id)
        )
        assert second.basin.epistemic == EpistemicState.SUPPORTED
        assert stale.feedback.rejected is True
        assert "Stale parent event" in stale.feedback.rejection_reason


def test_budget_exhaustion_blocks_more_actions():
    with BasinLabSession(step_budget=1) as session:
        first = session.execute_action(ActionProposal("seed", "Create state", "alpha = 1"))
        second = session.execute_action(
            ActionProposal("overflow", "Exceed budget", "beta = 2", parent_event_id=first.event_id)
        )
        assert first.basin.epistemic == EpistemicState.SUPPORTED
        assert second.feedback.rejected is True
        assert "Step budget exhausted" in second.feedback.rejection_reason
