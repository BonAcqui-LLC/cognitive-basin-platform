"""
Bounded participant and system perspective models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class PerspectiveOwner:
    owner_id: str
    owner_class: str

    def to_record(self) -> Dict[str, Any]:
        return {"owner_id": self.owner_id, "owner_class": self.owner_class}


@dataclass
class PerspectiveEvidence:
    detail: str
    category: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "category": self.category}


@dataclass
class AttributedBelief:
    detail: str
    status: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "status": self.status}


@dataclass
class AttributedKnowledge:
    detail: str
    status: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "status": self.status}


@dataclass
class AttributedUncertainty:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class AttributedGoal:
    detail: str
    status: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "status": self.status}


@dataclass
class AttributedConstraint:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class AttributedPreference:
    detail: str
    status: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "status": self.status}


@dataclass
class PerspectiveConflict:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PerspectiveRevision:
    owner_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"owner_id": self.owner_id, "detail": self.detail}


@dataclass
class PerspectiveModel:
    owner: PerspectiveOwner
    beliefs: List[AttributedBelief] = field(default_factory=list)
    knowledge: List[AttributedKnowledge] = field(default_factory=list)
    uncertainties: List[AttributedUncertainty] = field(default_factory=list)
    goals: List[AttributedGoal] = field(default_factory=list)
    constraints: List[AttributedConstraint] = field(default_factory=list)
    preferences: List[AttributedPreference] = field(default_factory=list)
    evidence: List[PerspectiveEvidence] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "owner": self.owner.to_record(),
            "beliefs": _record(self.beliefs),
            "knowledge": _record(self.knowledge),
            "uncertainties": _record(self.uncertainties),
            "goals": _record(self.goals),
            "constraints": _record(self.constraints),
            "preferences": _record(self.preferences),
            "evidence": _record(self.evidence),
        }


@dataclass
class PerspectiveReceipt:
    models: List[PerspectiveModel]
    conflicts: List[PerspectiveConflict]
    revisions: List[PerspectiveRevision]

    def to_record(self) -> Dict[str, Any]:
        return {
            "models": _record(self.models),
            "conflicts": _record(self.conflicts),
            "revisions": _record(self.revisions),
        }


class PerspectiveRegistry:
    def __init__(self) -> None:
        self.models: Dict[str, PerspectiveModel] = {}
        self.revisions: List[PerspectiveRevision] = []

    def record_statement(
        self,
        *,
        owner_id: str,
        owner_class: str,
        statement: str,
        label: str,
        evidence_category: str,
    ) -> PerspectiveModel:
        model = self.models.setdefault(owner_id, PerspectiveModel(PerspectiveOwner(owner_id, owner_class)))
        evidence = PerspectiveEvidence(statement, evidence_category)
        model.evidence.append(evidence)
        if label == "belief":
            model.beliefs.append(AttributedBelief(statement, evidence_category))
        elif label == "knowledge":
            model.knowledge.append(AttributedKnowledge(statement, evidence_category))
        elif label == "goal":
            model.goals.append(AttributedGoal(statement, evidence_category))
        elif label == "constraint":
            model.constraints.append(AttributedConstraint(statement))
        elif label == "preference":
            model.preferences.append(AttributedPreference(statement, evidence_category))
        else:
            model.uncertainties.append(AttributedUncertainty(statement))
        self.revisions.append(PerspectiveRevision(owner_id, f"recorded {label}"))
        return model

    def receipt(self) -> PerspectiveReceipt:
        conflicts: List[PerspectiveConflict] = []
        james = self.models.get("James Clow")
        melissa = self.models.get("Melissa Clow")
        if james and melissa:
            james_goals = {item.detail for item in james.goals}
            melissa_goals = {item.detail for item in melissa.goals}
            if james_goals.symmetric_difference(melissa_goals):
                conflicts.append(PerspectiveConflict("participants hold distinct explicit goals or evidence"))
        return PerspectiveReceipt(list(self.models.values()), conflicts, list(self.revisions))


__all__ = [
    "AttributedBelief",
    "AttributedConstraint",
    "AttributedGoal",
    "AttributedKnowledge",
    "AttributedPreference",
    "AttributedUncertainty",
    "PerspectiveConflict",
    "PerspectiveEvidence",
    "PerspectiveModel",
    "PerspectiveOwner",
    "PerspectiveReceipt",
    "PerspectiveRegistry",
    "PerspectiveRevision",
]
