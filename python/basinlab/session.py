"""
Governed BasinLab session built on the Cognitive Basin truth-state contracts.
"""

from __future__ import annotations

import base64
import hashlib
import json
import pickle
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.completion_integrity.guard import attempt_transition
from packages.ternary.states import ActionState, EpistemicState
from python.cognitive_basin.pipeline import CommitGate

from .contracts import (
    ActionFeedback,
    ActionProposal,
    ActionResult,
    BasinGovernanceState,
    CheckpointRecord,
    CommitDecision,
    CommitProposal,
    NamespaceDiff,
    NamespaceVariableSummary,
    PreExecutionCheck,
)
from .runner import RunnerExecutionError, SubprocessRunner
from .sandbox import inspect_action_code
from .store import SessionStore


def _summary_objects(summary: Dict[str, Dict[str, Any]]) -> Dict[str, NamespaceVariableSummary]:
    return {name: NamespaceVariableSummary(**payload) for name, payload in summary.items()}


def checkpoint_hash(snapshot: Dict[str, Dict[str, Any]]) -> str:
    payload = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def decode_snapshot(snapshot: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    materialized: Dict[str, Any] = {}
    for name, entry in snapshot.items():
        if entry.get("encoding") != "pickle+base64":
            continue
        payload = base64.b64decode(entry["payload"].encode("ascii"))
        materialized[name] = pickle.loads(payload)
    return materialized


def encode_bindings(bindings: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    encoded: Dict[str, Dict[str, Any]] = {}
    for name, value in bindings.items():
        payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        encoded[name] = {
            "encoding": "pickle+base64",
            "payload": base64.b64encode(payload).decode("ascii"),
            "summary": repr(value)[:160],
        }
    return encoded


def default_store_path(root: str | Path | None = None) -> Path:
    base = Path(root) if root else Path.cwd()
    return base / ".basinlab_store"


def _state_from_outcome(feedback: ActionFeedback) -> BasinGovernanceState:
    if feedback.rejected:
        return BasinGovernanceState(
            epistemic=EpistemicState.CONTRADICTED,
            action=ActionState.RETRACT,
            provisional=True,
            reason=feedback.rejection_reason,
        )
    if feedback.timed_out or feedback.exception_type:
        reason = feedback.exception_type or "timed_out"
        return BasinGovernanceState(
            epistemic=EpistemicState.UNRESOLVED,
            action=ActionState.HOLD,
            provisional=True,
            reason=reason,
        )
    return BasinGovernanceState(
        epistemic=EpistemicState.SUPPORTED,
        action=ActionState.EXTEND,
        provisional=False,
        reason="execution_succeeded",
    )


class BasinLabSession:
    def __init__(
        self,
        step_budget: int = 32,
        time_budget_s: float = 120.0,
        *,
        store: SessionStore | None = None,
        session_id: str | None = None,
        session_metadata: Optional[Dict[str, Any]] = None,
        resume_existing: bool = False,
    ) -> None:
        self.runner = SubprocessRunner()
        self.kernel = self.runner
        self.events: List[Dict[str, Any]] = []
        self.last_basin = BasinGovernanceState(
            epistemic=EpistemicState.UNRESOLVED,
            action=ActionState.HOLD,
            provisional=True,
            reason="session_not_started",
        )
        self.step_budget = step_budget
        self.time_budget_s = time_budget_s
        self.started_at: float | None = None
        self._next_event_index = 1
        self._latest_event_id: Optional[str] = None
        self._latest_action_event_id: Optional[str] = None
        self._step_ids: set[str] = set()
        self._committed_parent_ids: set[str] = set()
        self._last_checkpoint = CheckpointRecord()
        self.store = store
        self.session_id = session_id
        self.session_metadata = dict(session_metadata or {})
        self._resume_existing = resume_existing

    @classmethod
    def resume_from_store(cls, store: SessionStore, session_id: str) -> "BasinLabSession":
        session = cls(store=store, session_id=session_id, resume_existing=True)
        session.start()
        return session

    def __enter__(self) -> "BasinLabSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _new_event_id(self, prefix: str) -> str:
        event_id = f"{prefix}-{self._next_event_index:04d}"
        self._next_event_index += 1
        self._latest_event_id = event_id
        return event_id

    def _rebuild_indices(self) -> None:
        highest = 0
        for event in self.events:
            event_id = event.get("event_id", "")
            if "-" in event_id:
                suffix = event_id.rsplit("-", 1)[-1]
                if suffix.isdigit():
                    highest = max(highest, int(suffix))
            if event.get("type") == "action":
                result = event["result"]
                self._step_ids.add(result["proposal"]["step_id"])
                self._latest_action_event_id = event_id
                self.last_basin = BasinGovernanceState(
                    epistemic=EpistemicState(result["basin"]["epistemic"]),
                    action=ActionState(result["basin"]["action"]),
                    provisional=result["basin"]["provisional"],
                    reason=result["basin"]["reason"],
                )
            elif event.get("type") == "commit":
                decision = event["decision"]
                if decision["allowed"]:
                    parent_event_id = event.get("parent_event_id") or ""
                    self._committed_parent_ids.add(parent_event_id)
        self._next_event_index = highest + 1
        if self.events:
            self._latest_event_id = self.events[-1].get("event_id")

    def _steps_remaining(self) -> int:
        return max(0, self.step_budget - len(self._step_ids))

    def _time_remaining(self) -> float:
        if self.started_at is None:
            return self.time_budget_s
        return self.time_budget_s - (time.time() - self.started_at)

    def _persist_event(
        self,
        event: Dict[str, Any],
        *,
        snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
        basin: Optional[BasinGovernanceState] = None,
    ) -> None:
        if self.store is None or self.session_id is None:
            return
        self.store.append_event(
            self.session_id,
            event,
            snapshot=snapshot,
            final_basin=basin.to_record() if basin is not None else None,
        )

    def start(self) -> None:
        if self.store is not None and self._resume_existing:
            if self.session_id is None or not self.store.session_exists(self.session_id):
                raise ValueError("Cannot resume BasinLab session without an existing session ID")
            self.runner.start()
            self.started_at = time.time()
            self.events = self.store.read_events(self.session_id)
            self._rebuild_indices()
            latest_snapshot = self.store.latest_snapshot(self.session_id)
            if latest_snapshot["snapshot"]:
                self.runner.restore(latest_snapshot["snapshot"])
                namespace_summary = _summary_objects(self.runner.inspect_namespace())
                self._last_checkpoint = CheckpointRecord(
                    snapshot=latest_snapshot["snapshot"],
                    namespace_summary=namespace_summary,
                    snapshot_hash=latest_snapshot["snapshot_hash"],
                )
            return

        self.runner.start()
        self.started_at = time.time()
        if self.store is not None and self.session_id is None:
            metadata = {
                "step_budget": self.step_budget,
                "time_budget_s": self.time_budget_s,
                **self.session_metadata,
            }
            self.session_id = self.store.create_session(metadata)
        event_id = self._new_event_id("session")
        event = {
            "type": "session_started",
            "event_id": event_id,
            "timestamp": time.time(),
            "pid": self.kernel.pid,
        }
        self.events.append(event)
        snapshot = self.runner.snapshot_with_summary()
        self._last_checkpoint = CheckpointRecord(
            snapshot=snapshot.get("snapshot", {}),
            namespace_summary=_summary_objects(snapshot.get("namespace_summary", {})),
            snapshot_hash=checkpoint_hash(snapshot.get("snapshot", {})),
        )
        self._persist_event(event, snapshot=self._last_checkpoint.snapshot, basin=self.last_basin)

    def close(self) -> None:
        self.runner.close()

    def reset(self) -> None:
        self.runner.reset()
        self._last_checkpoint = CheckpointRecord()

    def _preflight(self, proposal: ActionProposal) -> PreExecutionCheck:
        reasons: List[str] = []
        if not isinstance(proposal.code, str):
            reasons.append("ActionProposal.code must be a string")
        elif not proposal.code.strip():
            reasons.append("ActionProposal.code is required")
        if not proposal.step_id.strip():
            reasons.append("ActionProposal.step_id is required")
        elif proposal.step_id in self._step_ids:
            reasons.append(f"Duplicate action ID: {proposal.step_id}")
        if not proposal.summary.strip():
            reasons.append("ActionProposal.summary is required")
        nonempty_lines = [line for line in proposal.code.splitlines() if line.strip()] if isinstance(proposal.code, str) else []
        if len(nonempty_lines) > 25:
            reasons.append("ActionProposal exceeds the one-bounded-action line budget")
        if proposal.max_duration_s <= 0 or proposal.max_duration_s > 30:
            reasons.append("ActionProposal.max_duration_s must be in the range (0, 30]")
        if proposal.action_cost <= 0:
            reasons.append("ActionProposal.action_cost must be positive")
        if proposal.parent_event_id and proposal.parent_event_id != self._latest_event_id:
            reasons.append(
                f"Stale parent event: expected {self._latest_event_id or 'none'}, got {proposal.parent_event_id}"
            )
        if self._steps_remaining() < proposal.action_cost:
            reasons.append("Step budget exhausted")
        if self._time_remaining() <= 0:
            reasons.append("Time budget exhausted")

        if reasons:
            return PreExecutionCheck(
                epistemic=EpistemicState.UNRESOLVED,
                action=ActionState.HOLD,
                allowed=False,
                reasons=reasons,
            )

        return PreExecutionCheck(
            epistemic=EpistemicState.SUPPORTED,
            action=ActionState.EXTEND,
            allowed=True,
            reasons=[],
        )

    def _checkpoint_from_execution(self, execution: Dict[str, Any]) -> CheckpointRecord:
        snapshot = execution.get("snapshot", {})
        summary = _summary_objects(execution.get("namespace_summary", {}))
        return CheckpointRecord(
            snapshot=snapshot,
            namespace_summary=summary,
            snapshot_hash=checkpoint_hash(snapshot),
        )

    def _restore_last_checkpoint(self) -> None:
        self.runner.restart()
        if self._last_checkpoint.snapshot:
            self.runner.restore(self._last_checkpoint.snapshot)

    def execute_action(self, proposal: ActionProposal) -> ActionResult:
        preflight = self._preflight(proposal)
        guard = inspect_action_code(proposal.code if isinstance(proposal.code, str) else "").to_record()
        worker_recovered = False
        if preflight.allowed and self.kernel.pid is None and self._last_checkpoint.snapshot:
            self._restore_last_checkpoint()
            worker_recovered = True

        if not preflight.allowed:
            feedback = ActionFeedback(
                rejected=True,
                rejection_reason="; ".join(preflight.reasons),
                namespace_summary=self._last_checkpoint.namespace_summary,
            )
            basin = _state_from_outcome(feedback)
            checkpoint = self._last_checkpoint
        elif not guard["allowed"]:
            feedback = ActionFeedback(
                rejected=True,
                rejection_reason="; ".join(guard["reasons"]),
                namespace_summary=self._last_checkpoint.namespace_summary,
            )
            basin = _state_from_outcome(feedback)
            checkpoint = self._last_checkpoint
            self._step_ids.add(proposal.step_id)
        else:
            try:
                execution = self.runner.execute(proposal.code, timeout_s=proposal.max_duration_s)
            except RunnerExecutionError as exc:
                worker_recovered = True
                self._restore_last_checkpoint()
                feedback = ActionFeedback(
                    rejected=False,
                    timed_out=exc.timed_out,
                    rejection_reason=str(exc),
                    exception_type="" if exc.timed_out else exc.error_class,
                    worker_recovered=True,
                    namespace_summary=self._last_checkpoint.namespace_summary,
                    runner_receipt=exc.receipt.to_record(),
                )
                checkpoint = self._last_checkpoint
            else:
                checkpoint = self._checkpoint_from_execution(execution)
                feedback = ActionFeedback(
                    stdout=execution.get("stdout", ""),
                    stderr=execution.get("stderr", ""),
                    exception_type=execution.get("exception_type", ""),
                    traceback=execution.get("traceback", ""),
                    duration_s=execution.get("duration_s", 0.0),
                    stdout_truncated=execution.get("stdout_truncated", False),
                    stderr_truncated=execution.get("stderr_truncated", False),
                    traceback_truncated=execution.get("traceback_truncated", False),
                    namespace_diff=NamespaceDiff(**execution.get("namespace_diff", {})),
                    namespace_summary=checkpoint.namespace_summary,
                    worker_recovered=worker_recovered,
                    runner_receipt=execution.get("runner_receipt", {}),
                )
                if not feedback.exception_type:
                    self._last_checkpoint = checkpoint
                else:
                    checkpoint = self._last_checkpoint
                    feedback.namespace_summary = checkpoint.namespace_summary
            basin = _state_from_outcome(feedback)
            self._step_ids.add(proposal.step_id)

        sera_event = {
            "type": "sera.action",
            "timestamp": time.time(),
            "step_id": proposal.step_id,
            "epistemic": basin.epistemic.value,
            "action": basin.action.value,
            "provisional": basin.provisional,
            "duration_s": feedback.duration_s,
            "timed_out": feedback.timed_out,
            "rejected": feedback.rejected,
            "exception_type": feedback.exception_type,
            "stdout_chars": len(feedback.stdout),
            "stderr_chars": len(feedback.stderr),
            "created": len(feedback.namespace_diff.created),
            "updated": len(feedback.namespace_diff.updated),
            "deleted": len(feedback.namespace_diff.deleted),
            "worker_recovered": feedback.worker_recovered,
            "steps_remaining": self._steps_remaining(),
        }

        event_id = self._new_event_id("action")
        result = ActionResult(
            event_id=event_id,
            proposal=proposal,
            preflight=preflight,
            guard=guard,
            feedback=feedback,
            basin=basin,
            sera_event=sera_event,
            checkpoint=checkpoint,
        )
        self.last_basin = basin
        self._latest_action_event_id = event_id
        event = {
            "type": "action",
            "event_id": event_id,
            "parent_event_id": proposal.parent_event_id,
            "timestamp": time.time(),
            "result": result.to_record(),
        }
        self.events.append(event)
        self._persist_event(event, snapshot=checkpoint.snapshot, basin=basin)
        return result

    def inspect_namespace(self) -> Dict[str, NamespaceVariableSummary]:
        response = self.runner.inspect_namespace()
        return _summary_objects(response)

    def load_bindings(self, bindings: Dict[str, Any]) -> None:
        self.runner.load_bindings(encode_bindings(bindings))
        snapshot = self.runner.snapshot_with_summary()
        self._last_checkpoint = CheckpointRecord(
            snapshot=snapshot.get("snapshot", {}),
            namespace_summary=_summary_objects(snapshot.get("namespace_summary", {})),
            snapshot_hash=checkpoint_hash(snapshot.get("snapshot", {})),
        )
        event = {
            "type": "bindings_loaded",
            "event_id": self._new_event_id("bindings"),
            "timestamp": time.time(),
            "binding_names": sorted(bindings),
        }
        self.events.append(event)
        self._persist_event(event, snapshot=self._last_checkpoint.snapshot, basin=self.last_basin)

    def materialize_namespace(self) -> Dict[str, Any]:
        return decode_snapshot(self._last_checkpoint.snapshot)

    def restore_checkpoint_in_fresh_process(self) -> Dict[str, Any]:
        self._restore_last_checkpoint()
        return self.materialize_namespace()

    def propose_commit(self, proposal: CommitProposal) -> CommitDecision:
        reasons: List[str] = []
        parent_event_id = proposal.parent_event_id or self._latest_action_event_id or self._latest_event_id
        expected_parent = self._latest_action_event_id or self._latest_event_id
        if parent_event_id != expected_parent:
            reasons.append(
                f"Stale parent event for commit: expected {expected_parent or 'none'}, got {parent_event_id}"
            )
        if parent_event_id in self._committed_parent_ids:
            reasons.append(f"Repeated commit attempt for parent event {parent_event_id}")
        if self.last_basin.epistemic != EpistemicState.SUPPORTED:
            reasons.append("Latest Basin state is not SUPPORTED")
        if self.last_basin.action != ActionState.EXTEND:
            reasons.append("Latest Basin action is not EXTEND")
        if self.last_basin.provisional:
            reasons.append("Latest Basin state remains provisional")

        integrity = attempt_transition(
            capability_name=proposal.capability_name,
            artifact_paths=proposal.artifact_paths,
            claimed_status=proposal.claimed_status,
            output_claim=proposal.completion_claim,
        )
        if not integrity.allowed:
            reasons.append(integrity.reason)

        allowed = CommitGate().allow(
            {
                "allowed": integrity.allowed and not reasons,
                "provisional": bool(reasons),
            }
        )

        if allowed:
            basin = BasinGovernanceState(
                epistemic=EpistemicState.SUPPORTED,
                action=ActionState.EXTEND,
                provisional=False,
                reason="commit_gate_allowed",
            )
            self._committed_parent_ids.add(parent_event_id or "none")
        else:
            basin = BasinGovernanceState(
                epistemic=self.last_basin.epistemic,
                action=ActionState.HOLD,
                provisional=True,
                reason="commit_gate_denied",
            )

        sera_event = {
            "type": "sera.commit",
            "timestamp": time.time(),
            "allowed": allowed,
            "reason_count": len(reasons),
        }
        event_id = self._new_event_id("commit")
        decision = CommitDecision(
            event_id=event_id,
            proposal=proposal,
            allowed=allowed,
            reasons=reasons,
            integrity_reason=integrity.reason,
            basin=basin,
            sera_event=sera_event,
        )
        event = {
            "type": "commit",
            "event_id": event_id,
            "parent_event_id": parent_event_id,
            "timestamp": time.time(),
            "decision": decision.to_record(),
        }
        self.events.append(event)
        self._persist_event(event, basin=basin)
        if self.store is not None and self.session_id is not None:
            for artifact_path in proposal.artifact_paths:
                self.store.register_artifact(
                    self.session_id,
                    artifact_path,
                    event_id=event_id,
                    artifact_type="commit_evidence",
                )
        return decision

    def export_events(self) -> List[Dict[str, Any]]:
        return list(self.events)


def replay_governed_session(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    basin = BasinGovernanceState(
        epistemic=EpistemicState.UNRESOLVED,
        action=ActionState.HOLD,
        provisional=True,
        reason="no_events",
    )
    namespace: Dict[str, Any] = {}
    last_commit: Dict[str, Any] | None = None
    errors: List[str] = []
    report: Dict[str, Any] | None = None

    for event in events:
        if event.get("type") == "action":
            result = event["result"]
            checkpoint = result.get("checkpoint", {})
            snapshot = checkpoint.get("snapshot", {})
            expected_hash = checkpoint.get("snapshot_hash", "")
            actual_hash = checkpoint_hash(snapshot)
            if expected_hash and expected_hash != actual_hash:
                errors.append(f"Checkpoint hash mismatch for {result.get('event_id', 'unknown')}")
            basin = BasinGovernanceState(
                epistemic=EpistemicState(result["basin"]["epistemic"]),
                action=ActionState(result["basin"]["action"]),
                provisional=result["basin"]["provisional"],
                reason=result["basin"]["reason"],
            )
            namespace = decode_snapshot(snapshot)
        elif event.get("type") == "commit":
            last_commit = event["decision"]
            basin = BasinGovernanceState(
                epistemic=EpistemicState(event["decision"]["basin"]["epistemic"]),
                action=ActionState(event["decision"]["basin"]["action"]),
                provisional=event["decision"]["basin"]["provisional"],
                reason=event["decision"]["basin"]["reason"],
            )
        elif event.get("type") == "trajectory_report":
            report = event["report"]
            final_basin = report.get("final_basin_state", {})
            if final_basin:
                basin = BasinGovernanceState(
                    epistemic=EpistemicState(final_basin["epistemic"]),
                    action=ActionState(final_basin["action"]),
                    provisional=final_basin["provisional"],
                    reason=final_basin.get("reason", ""),
                )

    return {
        "basin": basin,
        "namespace": namespace,
        "last_commit": last_commit,
        "events": list(events),
        "errors": errors,
        "report": report,
    }


def replay_persisted_session(store: SessionStore, session_id: str) -> Dict[str, Any]:
    replay = replay_governed_session(store.read_events(session_id))
    replay["replay_hash"] = store.record_replay_hash(
        session_id,
        {
            "basin": replay["basin"].to_record(),
            "namespace_keys": sorted(replay["namespace"]),
            "errors": replay["errors"],
            "last_commit": replay["last_commit"],
        },
    )
    return replay


def inspect_persisted_session(store: SessionStore, session_id: str) -> Dict[str, Any]:
    inspection = store.inspect_session(session_id)
    inspection["snapshot"] = store.latest_snapshot(session_id)
    return inspection


def run_vertical_slice_demo(store_dir: str | Path | None = None) -> Dict[str, Any]:
    store = SessionStore(store_dir or default_store_path()) if store_dir else None
    with BasinLabSession(store=store, session_metadata={"scenario": "vertical_slice"}) as session:
        initial_pid = session.kernel.pid
        first = session.execute_action(
            ActionProposal(
                step_id="seed",
                summary="Create the first retained variable",
                code="alpha = 7\nprint(alpha)",
                expected_variables=["alpha"],
            )
        )
        second = session.execute_action(
            ActionProposal(
                step_id="error",
                summary="Trigger a recoverable runtime failure",
                code="beta = alpha + missing_value",
                expected_variables=["beta"],
                parent_event_id=first.event_id,
            )
        )
        third = session.execute_action(
            ActionProposal(
                step_id="repair",
                summary="Repair the failure without restarting the kernel",
                code="missing_value = 5\nbeta = alpha + missing_value\nprint(beta)",
                expected_variables=["missing_value", "beta"],
                parent_event_id=second.event_id,
            )
        )
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "tests" / "unit_report.py"
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_text("def test_demo():\n    assert True\n", encoding="utf-8")
            commit = session.propose_commit(
                CommitProposal(
                    summary="Governed commit proposal after repaired action",
                    artifact_paths=[str(evidence)],
                    completion_claim="Unit tests passed.",
                    parent_event_id=third.event_id,
                )
            )

        blocked = session.execute_action(
            ActionProposal(
                step_id="blocked",
                summary="Demonstrate pre-execution guard rejection",
                code="import os\nescape_attempt = 1",
                parent_event_id=commit.event_id,
            )
        )

        replay = replay_governed_session(session.export_events())
        return {
            "session_id": session.session_id,
            "initial_pid": initial_pid,
            "final_pid": session.kernel.pid,
            "first": first.to_record(),
            "second": second.to_record(),
            "third": third.to_record(),
            "blocked": blocked.to_record(),
            "commit": commit.to_record(),
            "replay": {
                "basin": replay["basin"].to_record(),
                "namespace": replay["namespace"],
                "last_commit": replay["last_commit"],
                "errors": replay["errors"],
            },
        }
