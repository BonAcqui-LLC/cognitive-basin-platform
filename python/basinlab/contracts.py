"""
Typed BasinLab contracts for the first executable vertical slice.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

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


@dataclass
class CommitProposal:
    summary: str
    artifact_paths: List[str] = field(default_factory=list)
    completion_claim: str = ""
    claimed_status: str = "IMPLEMENTED"
    capability_name: str = "basinlab.commit.proposal"


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
    namespace_diff: NamespaceDiff = field(default_factory=NamespaceDiff)

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
            "namespace_diff": self.namespace_diff.to_record(),
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
class ActionResult:
    proposal: ActionProposal
    preflight: PreExecutionCheck
    guard: Dict[str, Any]
    feedback: ActionFeedback
    basin: BasinGovernanceState
    sera_event: Dict[str, Any]
    snapshot: Dict[str, Dict[str, str]]

    def to_record(self) -> Dict[str, Any]:
        return {
            "proposal": {
                "step_id": self.proposal.step_id,
                "summary": self.proposal.summary,
                "code": self.proposal.code,
                "expected_variables": list(self.proposal.expected_variables),
                "completion_claim": self.proposal.completion_claim,
                "max_duration_s": self.proposal.max_duration_s,
                "capability_name": self.proposal.capability_name,
            },
            "preflight": self.preflight.to_record(),
            "guard": dict(self.guard),
            "feedback": self.feedback.to_record(),
            "basin": self.basin.to_record(),
            "sera_event": dict(self.sera_event),
            "snapshot": dict(self.snapshot),
        }


@dataclass
class CommitDecision:
    proposal: CommitProposal
    allowed: bool
    reasons: List[str]
    integrity_reason: str
    basin: BasinGovernanceState
    sera_event: Dict[str, Any]

    def to_record(self) -> Dict[str, Any]:
        return {
            "proposal": {
                "summary": self.proposal.summary,
                "artifact_paths": list(self.proposal.artifact_paths),
                "completion_claim": self.proposal.completion_claim,
                "claimed_status": self.proposal.claimed_status,
                "capability_name": self.proposal.capability_name,
            },
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "integrity_reason": self.integrity_reason,
            "basin": self.basin.to_record(),
            "sera_event": dict(self.sera_event),
        }
