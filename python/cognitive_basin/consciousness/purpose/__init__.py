"""
Purpose-lattice contracts and arbitration logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


PurposeID = str


@dataclass
class PurposeSource:
    source_type: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"source_type": self.source_type, "detail": self.detail}


@dataclass
class PurposePriority:
    weight: float
    urgency: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {"weight": self.weight, "urgency": self.urgency}


@dataclass
class PurposeConstraint:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PurposeConflict:
    purpose_id: str
    with_purpose_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"purpose_id": self.purpose_id, "with_purpose_id": self.with_purpose_id, "reason": self.reason}


@dataclass
class PurposeDependency:
    purpose_id: str
    depends_on: str

    def to_record(self) -> Dict[str, Any]:
        return {"purpose_id": self.purpose_id, "depends_on": self.depends_on}


@dataclass
class PurposeProgress:
    progress: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {"progress": self.progress}


@dataclass
class PurposeCompletion:
    completed: bool
    detail: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {"completed": self.completed, "detail": self.detail}


@dataclass
class PurposeFailure:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PurposeSuspension:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PurposeSupersession:
    superseded_id: str
    by_purpose_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"superseded_id": self.superseded_id, "by_purpose_id": self.by_purpose_id, "reason": self.reason}


@dataclass
class Purpose:
    purpose_id: PurposeID
    description: str
    source: PurposeSource
    priority: PurposePriority
    constraints: List[PurposeConstraint] = field(default_factory=list)
    dependencies: List[PurposeDependency] = field(default_factory=list)
    status: str = "ACTIVE"
    progress: PurposeProgress = field(default_factory=PurposeProgress)

    def score(self) -> float:
        return self.priority.weight + self.priority.urgency - (0.6 if self.status == "HOLD" else 0.0)

    def to_record(self) -> Dict[str, Any]:
        return {
            "purpose_id": self.purpose_id,
            "description": self.description,
            "source": self.source.to_record(),
            "priority": self.priority.to_record(),
            "constraints": [item.to_record() for item in self.constraints],
            "dependencies": [item.to_record() for item in self.dependencies],
            "status": self.status,
            "progress": self.progress.to_record(),
            "score": self.score(),
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "Purpose":
        return cls(
            purpose_id=str(payload["purpose_id"]),
            description=str(payload["description"]),
            source=PurposeSource(**payload["source"]),
            priority=PurposePriority(**payload["priority"]),
            constraints=[PurposeConstraint(**item) for item in payload.get("constraints", [])],
            dependencies=[PurposeDependency(**item) for item in payload.get("dependencies", [])],
            status=str(payload.get("status", "ACTIVE")),
            progress=PurposeProgress(**payload.get("progress", {"progress": 0.0})),
        )


@dataclass
class PurposeLattice:
    purposes: Dict[PurposeID, Purpose] = field(default_factory=dict)
    conflicts: List[PurposeConflict] = field(default_factory=list)
    supersessions: List[PurposeSupersession] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "purposes": {key: value.to_record() for key, value in self.purposes.items()},
            "conflicts": [item.to_record() for item in self.conflicts],
            "supersessions": [item.to_record() for item in self.supersessions],
        }


@dataclass
class PurposeReceipt:
    active_purpose: Purpose | None
    lattice: PurposeLattice
    suspended: List[PurposeSuspension] = field(default_factory=list)
    completions: List[PurposeCompletion] = field(default_factory=list)
    failures: List[PurposeFailure] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "active_purpose": self.active_purpose.to_record() if self.active_purpose else None,
            "lattice": self.lattice.to_record(),
            "suspended": [item.to_record() for item in self.suspended],
            "completions": [item.to_record() for item in self.completions],
            "failures": [item.to_record() for item in self.failures],
        }


class PurposeManager:
    def __init__(self) -> None:
        self.purposes: Dict[str, Purpose] = {}
        self.supersessions: List[PurposeSupersession] = []

    def add(self, purpose: Purpose) -> None:
        self.purposes[purpose.purpose_id] = purpose

    def arbitrate(self) -> PurposeReceipt:
        purposes = list(self.purposes.values())
        conflicts: List[PurposeConflict] = []
        suspended: List[PurposeSuspension] = []
        for left_index, left in enumerate(purposes):
            for right in purposes[left_index + 1 :]:
                if left.description == right.description:
                    conflicts.append(PurposeConflict(left.purpose_id, right.purpose_id, "duplicate purpose"))
                if left.status == "SUPERSEDED":
                    self.supersessions.append(PurposeSupersession(left.purpose_id, right.purpose_id, "newer purpose selected"))
        active = max((purpose for purpose in purposes if purpose.status not in {"SUPERSEDED", "COMPLETED"}), key=lambda item: item.score(), default=None)
        if active and active.status == "HOLD":
            suspended.append(PurposeSuspension(f"{active.purpose_id} remains on HOLD"))
        return PurposeReceipt(
            active_purpose=active,
            lattice=PurposeLattice(
                purposes={purpose.purpose_id: purpose for purpose in purposes},
                conflicts=conflicts,
                supersessions=list(self.supersessions),
            ),
            suspended=suspended,
        )


__all__ = [
    "Purpose",
    "PurposeCompletion",
    "PurposeConflict",
    "PurposeConstraint",
    "PurposeDependency",
    "PurposeFailure",
    "PurposeID",
    "PurposeLattice",
    "PurposeManager",
    "PurposePriority",
    "PurposeProgress",
    "PurposeReceipt",
    "PurposeSource",
    "PurposeSupersession",
    "PurposeSuspension",
]
