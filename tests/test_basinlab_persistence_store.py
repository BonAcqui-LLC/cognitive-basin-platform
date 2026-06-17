"""
Persistent-session storage tests for BasinLab.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from packages.ternary.states import ActionState, EpistemicState
from python.basinlab.contracts import ActionProposal, CommitProposal
from python.basinlab.session import BasinLabSession, inspect_persisted_session, replay_persisted_session
from python.basinlab.store import SessionCorruptionError, SessionSchemaMismatchError, SessionStore, SessionStoreError


def test_fresh_process_reopens_persisted_session_and_restores_namespace(tmp_path):
    store = SessionStore(tmp_path / "store")
    with BasinLabSession(store=store, session_metadata={"scenario": "persist-reopen"}) as session:
        first = session.execute_action(ActionProposal("seed", "Create state", "alpha = 10"))
        session.execute_action(
            ActionProposal("compose", "Compose retained state", "beta = alpha + 4", parent_event_id=first.event_id)
        )
        session_id = session.session_id

    reopened = BasinLabSession.resume_from_store(store, str(session_id))
    try:
        namespace = reopened.materialize_namespace()
        assert namespace["alpha"] == 10
        assert namespace["beta"] == 14
    finally:
        reopened.close()


def test_replay_equality_matches_final_governed_state(tmp_path):
    store = SessionStore(tmp_path / "store")
    with BasinLabSession(store=store) as session:
        first = session.execute_action(ActionProposal("seed", "Create state", "counter = 1"))
        session.execute_action(
            ActionProposal("bump", "Advance state", "counter = counter + 6", parent_event_id=first.event_id)
        )
        session_id = str(session.session_id)

    replay = replay_persisted_session(store, session_id)
    assert replay["errors"] == []
    assert replay["basin"].epistemic == EpistemicState.SUPPORTED
    assert replay["basin"].action == ActionState.EXTEND
    assert replay["namespace"]["counter"] == 7
    assert replay["replay_hash"]


def test_corrupt_event_detection_raises(tmp_path):
    store = SessionStore(tmp_path / "store")
    with BasinLabSession(store=store) as session:
        session.execute_action(ActionProposal("seed", "Create state", "alpha = 1"))
        session_id = str(session.session_id)

    store.tamper_event_for_test(session_id, 1, {"type": "session_started", "event_id": "session-9999"})
    with pytest.raises(SessionCorruptionError):
        store.read_events(session_id)


def test_missing_artifact_is_reported_without_losing_audit_row(tmp_path):
    store = SessionStore(tmp_path / "store")
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("evidence", encoding="utf-8")
    with BasinLabSession(store=store) as session:
        action = session.execute_action(ActionProposal("seed", "Create state", "alpha = 1"))
        session.propose_commit(
            CommitProposal(
                "commit",
                artifact_paths=[str(artifact)],
                completion_claim="Unit tests passed.",
                parent_event_id=action.event_id,
            )
        )
        session_id = str(session.session_id)

    artifact.unlink()
    inspection = inspect_persisted_session(store, session_id)
    assert inspection["issues"] == [f"Missing artifact: {artifact}"]
    assert len(inspection["artifacts"]) == 1


def test_schema_mismatch_is_detected_on_reopen(tmp_path):
    store = SessionStore(tmp_path / "store")
    store.set_schema_version_for_test(999)
    with pytest.raises(SessionSchemaMismatchError):
        SessionStore(tmp_path / "store")


def test_interrupted_write_rolls_back_cleanly(tmp_path):
    store = SessionStore(tmp_path / "store")
    session_id = store.create_session({"scenario": "interrupt"})
    with pytest.raises(SessionStoreError):
        store.append_event(
            session_id,
            {"type": "trajectory_report", "event_id": "report-0001", "timestamp": 1.0, "report": {"passed": True}},
            final_basin={"epistemic": "SUPPORTED", "action": "EXTEND", "provisional": False, "reason": "ok"},
            simulate_interrupt=True,
        )
    assert store.inspect_session(session_id)["event_count"] == 0


def test_session_diff_and_concurrent_reads_work(tmp_path):
    left_store = SessionStore(tmp_path / "store")
    right_store = SessionStore(tmp_path / "store")
    with BasinLabSession(store=left_store) as session:
        first = session.execute_action(ActionProposal("seed", "Create state", "value = 1"))
        session.execute_action(ActionProposal("bump", "Advance", "value = value + 1", parent_event_id=first.event_id))
        left_id = str(session.session_id)
    with BasinLabSession(store=left_store) as session:
        session.execute_action(ActionProposal("seed", "Create state", "value = 10"))
        right_id = str(session.session_id)

    diff = right_store.diff_sessions(left_id, right_id)
    inspection = right_store.inspect_session(left_id)
    assert diff["event_count_delta"] > 0
    assert inspection["event_count"] >= 3


def test_pruning_temporary_execution_data_preserves_audit_evidence(tmp_path):
    store = SessionStore(tmp_path / "store")
    artifact = tmp_path / "scratch.log"
    artifact.write_text("temporary execution trace", encoding="utf-8")
    session_id = store.create_session({"scenario": "prune"})
    store.register_artifact(session_id, artifact, artifact_type="execution_temp", temporary=True)
    pruned = store.prune_temporary_artifacts(session_id)
    inspection = store.inspect_session(session_id)
    assert pruned == [str(artifact)]
    assert inspection["artifacts"][0]["pruned"] is True
    assert inspection["artifacts"][0]["exists_on_disk"] is False
