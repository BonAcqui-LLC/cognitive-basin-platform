"""
Typed BasinLab contracts for the hardened runtime and spectrum layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from packages.ternary.states import ActionState, EpistemicState


@dataclass
class ActionProposal:
    step_id: str
    summary: str
    code: str
    expected_variables: List[str] = field(default_factory=list)
    completion_claim: str = ""
    max_duration_s: float = 5.0
    capability_name: str = "basinlab.session.execute"
    parent_event_id: Optional[str] = None
    action_cost: int = 1


@dataclass
class CommitProposal:
    summary: str
    artifact_paths: List[str] = field(default_factory=list)
    completion_claim: str = ""
    claimed_status: str = "IMPLEMENTED"
    capability_name: str = "basinlab.commit.proposal"
    parent_event_id: Optional[str] = None


@dataclass
class PreExecutionCheck:
    epistemic: EpistemicState
    action: ActionState
    allowed: bool
    reasons: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "epistemic": self.epistemic.value,
            "action": self.action.value,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
        }


@dataclass
class NamespaceVariableSummary:
    type_name: str
    repr_text: str
    serializable: bool
    serialized_bytes: int = 0

    def to_record(self) -> Dict[str, Any]:
        return {
            "type_name": self.type_name,
            "repr_text": self.repr_text,
            "serializable": self.serializable,
            "serialized_bytes": self.serialized_bytes,
        }


@dataclass
class NamespaceDiff:
    created: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "created": list(self.created),
            "updated": list(self.updated),
            "deleted": list(self.deleted),
        }


@dataclass
class ActionFeedback:
    stdout: str = ""
    stderr: str = ""
    exception_type: str = ""
    traceback: str = ""
    duration_s: float = 0.0
    timed_out: bool = False
    rejected: bool = False
    rejection_reason: str = ""
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    traceback_truncated: bool = False
    namespace_diff: NamespaceDiff = field(default_factory=NamespaceDiff)
    namespace_summary: Dict[str, NamespaceVariableSummary] = field(default_factory=dict)
    worker_recovered: bool = False
    runner_receipt: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exception_type": self.exception_type,
            "traceback": self.traceback,
            "duration_s": self.duration_s,
            "timed_out": self.timed_out,
            "rejected": self.rejected,
            "rejection_reason": self.rejection_reason,
            "stdout_truncated": self.stdout_truncated,
            "stderr_truncated": self.stderr_truncated,
            "traceback_truncated": self.traceback_truncated,
            "namespace_diff": self.namespace_diff.to_record(),
            "namespace_summary": {
                name: summary.to_record() for name, summary in self.namespace_summary.items()
            },
            "worker_recovered": self.worker_recovered,
            "runner_receipt": dict(self.runner_receipt),
        }


@dataclass
class BasinGovernanceState:
    epistemic: EpistemicState
    action: ActionState
    provisional: bool
    reason: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {
            "epistemic": self.epistemic.value,
            "action": self.action.value,
            "provisional": self.provisional,
            "reason": self.reason,
        }


@dataclass
class CheckpointRecord:
    snapshot: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    namespace_summary: Dict[str, NamespaceVariableSummary] = field(default_factory=dict)
    snapshot_hash: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {
            "snapshot": dict(self.snapshot),
            "namespace_summary": {
                name: summary.to_record() for name, summary in self.namespace_summary.items()
            },
            "snapshot_hash": self.snapshot_hash,
        }


@dataclass
class ActionResult:
    event_id: str
    proposal: ActionProposal
    preflight: PreExecutionCheck
    guard: Dict[str, Any]
    feedback: ActionFeedback
    basin: BasinGovernanceState
    sera_event: Dict[str, Any]
    checkpoint: CheckpointRecord

    def to_record(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "proposal": {
                "step_id": self.proposal.step_id,
                "summary": self.proposal.summary,
                "code": self.proposal.code,
                "expected_variables": list(self.proposal.expected_variables),
                "completion_claim": self.proposal.completion_claim,
                "max_duration_s": self.proposal.max_duration_s,
                "capability_name": self.proposal.capability_name,
                "parent_event_id": self.proposal.parent_event_id,
                "action_cost": self.proposal.action_cost,
            },
            "preflight": self.preflight.to_record(),
            "guard": dict(self.guard),
            "feedback": self.feedback.to_record(),
            "basin": self.basin.to_record(),
            "sera_event": dict(self.sera_event),
            "checkpoint": self.checkpoint.to_record(),
        }


@dataclass
class CommitDecision:
    event_id: str
    proposal: CommitProposal
    allowed: bool
    reasons: List[str]
    integrity_reason: str
    basin: BasinGovernanceState
    sera_event: Dict[str, Any]

    def to_record(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "proposal": {
                "summary": self.proposal.summary,
                "artifact_paths": list(self.proposal.artifact_paths),
                "completion_claim": self.proposal.completion_claim,
                "claimed_status": self.proposal.claimed_status,
                "capability_name": self.proposal.capability_name,
                "parent_event_id": self.proposal.parent_event_id,
            },
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "integrity_reason": self.integrity_reason,
            "basin": self.basin.to_record(),
            "sera_event": dict(self.sera_event),
        }
