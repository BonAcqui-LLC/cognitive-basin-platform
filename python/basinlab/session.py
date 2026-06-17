"""
Governed BasinLab session built on the Cognitive Basin truth-state contracts.
"""

from __future__ import annotations

import base64
import pickle
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from packages.completion_integrity.guard import attempt_transition
from packages.ternary.states import ActionState, EpistemicState
from python.cognitive_basin.pipeline import CommitGate

from .contracts import (
    ActionFeedback,
    ActionProposal,
    ActionResult,
    BasinGovernanceState,
    CommitDecision,
    CommitProposal,
    NamespaceDiff,
    PreExecutionCheck,
)
from .kernel import SubprocessKernel
from .sandbox import inspect_action_code


def decode_snapshot(snapshot: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    materialized: Dict[str, Any] = {}
    for name, entry in snapshot.items():
        if entry.get("encoding") != "pickle+base64":
            continue
        payload = base64.b64decode(entry["payload"].encode("ascii"))
        materialized[name] = pickle.loads(payload)
    return materialized


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
    def __init__(self) -> None:
        self.kernel = SubprocessKernel()
        self.events: List[Dict[str, Any]] = []
        self.last_basin = BasinGovernanceState(
            epistemic=EpistemicState.UNRESOLVED,
            action=ActionState.HOLD,
            provisional=True,
            reason="session_not_started",
        )

    def __enter__(self) -> "BasinLabSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        self.kernel.start()
        self.events.append(
            {
                "type": "session_started",
                "timestamp": time.time(),
                "pid": self.kernel.pid,
            }
        )

    def close(self) -> None:
        self.kernel.close()

    def _preflight(self, proposal: ActionProposal) -> PreExecutionCheck:
        reasons: List[str] = []
        if not proposal.step_id.strip():
            reasons.append("ActionProposal.step_id is required")
        if not proposal.summary.strip():
            reasons.append("ActionProposal.summary is required")
        if not proposal.code.strip():
            reasons.append("ActionProposal.code is required")
        nonempty_lines = [line for line in proposal.code.splitlines() if line.strip()]
        if len(nonempty_lines) > 25:
            reasons.append("ActionProposal exceeds the one-bounded-action line budget")
        if proposal.max_duration_s <= 0 or proposal.max_duration_s > 30:
            reasons.append("ActionProposal.max_duration_s must be in the range (0, 30]")

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

    def execute_action(self, proposal: ActionProposal) -> ActionResult:
        preflight = self._preflight(proposal)
        guard = inspect_action_code(proposal.code).to_record()

        if not preflight.allowed:
            feedback = ActionFeedback(
                rejected=True,
                rejection_reason="; ".join(preflight.reasons),
            )
            basin = _state_from_outcome(feedback)
            snapshot = self.kernel.snapshot()
        elif not guard["allowed"]:
            feedback = ActionFeedback(
                rejected=True,
                rejection_reason="; ".join(guard["reasons"]),
            )
            basin = _state_from_outcome(feedback)
            snapshot = self.kernel.snapshot()
        else:
            try:
                execution = self.kernel.execute(proposal.code, timeout_s=proposal.max_duration_s)
                feedback = ActionFeedback(
                    stdout=execution.get("stdout", ""),
                    stderr=execution.get("stderr", ""),
                    exception_type=execution.get("exception_type", ""),
                    traceback=execution.get("traceback", ""),
                    duration_s=execution.get("duration_s", 0.0),
                    namespace_diff=NamespaceDiff(**execution.get("namespace_diff", {})),
                )
                snapshot = execution.get("snapshot", {})
            except TimeoutError as exc:
                feedback = ActionFeedback(
                    rejected=False,
                    timed_out=True,
                    rejection_reason=str(exc),
                )
                snapshot = {}
            basin = _state_from_outcome(feedback)

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
        }

        result = ActionResult(
            proposal=proposal,
            preflight=preflight,
            guard=guard,
            feedback=feedback,
            basin=basin,
            sera_event=sera_event,
            snapshot=snapshot,
        )
        self.last_basin = basin
        self.events.append(
            {
                "type": "action",
                "timestamp": time.time(),
                "result": result.to_record(),
            }
        )
        return result

    def inspect_namespace(self) -> Dict[str, str]:
        return self.kernel.inspect_namespace()

    def materialize_namespace(self) -> Dict[str, Any]:
        return decode_snapshot(self.kernel.snapshot())

    def propose_commit(self, proposal: CommitProposal) -> CommitDecision:
        reasons: List[str] = []
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
        decision = CommitDecision(
            proposal=proposal,
            allowed=allowed,
            reasons=reasons,
            integrity_reason=integrity.reason,
            basin=basin,
            sera_event=sera_event,
        )
        self.events.append(
            {
                "type": "commit",
                "timestamp": time.time(),
                "decision": decision.to_record(),
            }
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

    for event in events:
        if event.get("type") == "action":
            result = event["result"]
            basin = BasinGovernanceState(
                epistemic=EpistemicState(result["basin"]["epistemic"]),
                action=ActionState(result["basin"]["action"]),
                provisional=result["basin"]["provisional"],
                reason=result["basin"]["reason"],
            )
            namespace = decode_snapshot(result.get("snapshot", {}))
        elif event.get("type") == "commit":
            last_commit = event["decision"]

    return {
        "basin": basin,
        "namespace": namespace,
        "last_commit": last_commit,
        "events": list(events),
    }


def run_vertical_slice_demo() -> Dict[str, Any]:
    with BasinLabSession() as session:
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
            )
        )
        third = session.execute_action(
            ActionProposal(
                step_id="repair",
                summary="Repair the failure without restarting the kernel",
                code="missing_value = 5\nbeta = alpha + missing_value\nprint(beta)",
                expected_variables=["missing_value", "beta"],
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
                )
            )

        blocked = session.execute_action(
            ActionProposal(
                step_id="blocked",
                summary="Demonstrate pre-execution guard rejection",
                code="import os\nescape_attempt = 1",
            )
        )

        replay = replay_governed_session(session.export_events())
        return {
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
            },
        }
