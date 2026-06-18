"""
Self/world/other boundaries and action ownership accounting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from python.cognitive_basin.consciousness.perception import Percept, PerceptSource


ACTOR_CLASSES = {
    "SYSTEM_SELF",
    "PARTICIPANT_JAMES",
    "PARTICIPANT_MELISSA",
    "OTHER_HUMAN",
    "IMPLEMENTATION_AGENT",
    "MODEL_PROVIDER",
    "CONNECTOR",
    "EXTERNAL_SYSTEM",
    "SIMULATED_AGENT",
    "UNKNOWN",
}


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class SelfStateReference:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class WorldStateReference:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class OtherAgentReference:
    actor_class: str
    detail: str

    def __post_init__(self) -> None:
        if self.actor_class not in ACTOR_CLASSES:
            raise ValueError(f"Unsupported actor class: {self.actor_class}")

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ObservationOwnership:
    observation_id: str
    actor_class: str
    basis: str

    def to_record(self) -> Dict[str, Any]:
        return {"observation_id": self.observation_id, "actor_class": self.actor_class, "basis": self.basis}


@dataclass
class MemoryOwnership:
    memory_id: str
    actor_class: str
    basis: str

    def to_record(self) -> Dict[str, Any]:
        return {"memory_id": self.memory_id, "actor_class": self.actor_class, "basis": self.basis}


@dataclass
class AuthorityOwnership:
    authority_id: str
    actor_class: str
    basis: str

    def to_record(self) -> Dict[str, Any]:
        return {"authority_id": self.authority_id, "actor_class": self.actor_class, "basis": self.basis}


@dataclass
class AgencyBoundary:
    boundary_id: str
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"boundary_id": self.boundary_id, "actor_class": self.actor_class, "detail": self.detail}


@dataclass
class BoundaryConflict:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class ActionOrigin:
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ActionAuthor:
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ActionExecutor:
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ActionApprover:
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ActionOwner:
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ActionResponsibility:
    actor_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"actor_class": self.actor_class, "detail": self.detail}


@dataclass
class ActionIntent:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class ActionOutcome:
    state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "detail": self.detail}


@dataclass
class ActionOwnership:
    action_id: str
    proposal: ActionOrigin
    author: ActionAuthor
    executor: ActionExecutor
    approver: ActionApprover
    owner: ActionOwner
    responsibility: ActionResponsibility
    intent: ActionIntent
    outcome: ActionOutcome
    authority_basis: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "proposal": self.proposal.to_record(),
            "author": self.author.to_record(),
            "executor": self.executor.to_record(),
            "approver": self.approver.to_record(),
            "owner": self.owner.to_record(),
            "responsibility": self.responsibility.to_record(),
            "intent": self.intent.to_record(),
            "outcome": self.outcome.to_record(),
            "authority_basis": self.authority_basis,
        }


@dataclass
class BoundaryReceipt:
    observations: List[ObservationOwnership]
    boundaries: List[AgencyBoundary]
    conflicts: List[BoundaryConflict]

    def to_record(self) -> Dict[str, Any]:
        return {
            "observations": _record(self.observations),
            "boundaries": _record(self.boundaries),
            "conflicts": _record(self.conflicts),
        }


@dataclass
class AgencyReceipt:
    actions: List[ActionOwnership] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {"actions": _record(self.actions)}


class BoundaryEngine:
    def __init__(self) -> None:
        self.action_history: List[ActionOwnership] = []

    def classify_percepts(self, percepts: List[Percept]) -> BoundaryReceipt:
        observations: List[ObservationOwnership] = []
        conflicts: List[BoundaryConflict] = []
        boundaries = [
            AgencyBoundary("boundary-self", "SYSTEM_SELF", "system-generated state remains separate from world and other agents"),
            AgencyBoundary("boundary-sim", "SIMULATED_AGENT", "simulated outputs remain marked as simulated"),
        ]
        for percept in percepts:
            actor_class = self._actor_for_percept(percept)
            observations.append(ObservationOwnership(percept.percept_id, actor_class, percept.source_type.value))
            if actor_class == "MODEL_PROVIDER" and "James" in str(percept.content):
                conflicts.append(BoundaryConflict("provider output cannot be attributed to James without explicit evidence"))
        return BoundaryReceipt(observations, boundaries, conflicts)

    def record_action(
        self,
        *,
        action_id: str,
        proposed_by: str,
        authored_by: str,
        executed_by: str,
        approved_by: str,
        owned_by: str,
        responsibility: str,
        intent: str,
        outcome_state: str,
        outcome_detail: str,
        authority_basis: str,
    ) -> ActionOwnership:
        ownership = ActionOwnership(
            action_id=action_id,
            proposal=ActionOrigin(proposed_by, "who proposed it"),
            author=ActionAuthor(authored_by, "who authored it"),
            executor=ActionExecutor(executed_by, "who executed it"),
            approver=ActionApprover(approved_by, "who approved it"),
            owner=ActionOwner(owned_by, "who owns the decision"),
            responsibility=ActionResponsibility(responsibility, "responsibility boundary"),
            intent=ActionIntent(intent),
            outcome=ActionOutcome(outcome_state, outcome_detail),
            authority_basis=authority_basis,
        )
        self.action_history.append(ownership)
        return ownership

    def agency_receipt(self) -> AgencyReceipt:
        return AgencyReceipt(list(self.action_history))

    def _actor_for_percept(self, percept: Percept) -> str:
        if percept.source == "James Clow":
            return "PARTICIPANT_JAMES"
        if percept.source == "Melissa Clow":
            return "PARTICIPANT_MELISSA"
        if percept.source_type == PerceptSource.PROVIDER:
            return "MODEL_PROVIDER"
        if percept.source_type == PerceptSource.CONNECTOR:
            return "CONNECTOR"
        if percept.source_type == PerceptSource.SYSTEM:
            return "EXTERNAL_SYSTEM"
        if percept.source_type == PerceptSource.MEMORY:
            return "SYSTEM_SELF"
        if percept.source_type == PerceptSource.HUMAN:
            return "OTHER_HUMAN" if percept.source not in {"James Clow", "Melissa Clow"} else ("PARTICIPANT_JAMES" if percept.source == "James Clow" else "PARTICIPANT_MELISSA")
        return "UNKNOWN"


__all__ = [
    "ACTOR_CLASSES",
    "ActionApprover",
    "ActionAuthor",
    "ActionExecutor",
    "ActionIntent",
    "ActionOrigin",
    "ActionOutcome",
    "ActionOwner",
    "ActionOwnership",
    "ActionResponsibility",
    "AgencyBoundary",
    "AgencyReceipt",
    "AuthorityOwnership",
    "BoundaryConflict",
    "BoundaryEngine",
    "BoundaryReceipt",
    "MemoryOwnership",
    "ObservationOwnership",
    "OtherAgentReference",
    "SelfStateReference",
    "WorldStateReference",
]
