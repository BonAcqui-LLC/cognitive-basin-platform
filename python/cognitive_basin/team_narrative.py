"""
Explicit multi-user continuity records for Cognitive Basin sessions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .privacy import VisibilityScope, explicit_participant


def _merge_unique(left: Iterable[str], right: Iterable[str]) -> List[str]:
    merged: List[str] = []
    for value in list(left) + list(right):
        if value and value not in merged:
            merged.append(value)
    return merged


@dataclass
class NarrativeRecord:
    person: str
    contributions: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    superseded_decisions: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    current_purposes: List[str] = field(default_factory=list)
    commitments: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    recovery_history: List[str] = field(default_factory=list)
    visibility_scope: VisibilityScope = VisibilityScope.SHARED_PROJECT
    explicit_identity: bool = True

    @property
    def participant_id(self) -> str:
        return explicit_participant(self.person)

    def normalized(self) -> "NarrativeRecord":
        return NarrativeRecord(
            person=self.participant_id,
            contributions=list(self.contributions),
            decisions=list(self.decisions),
            conflicts=list(self.conflicts),
            superseded_decisions=list(self.superseded_decisions),
            unresolved_questions=list(self.unresolved_questions),
            current_purposes=list(self.current_purposes),
            commitments=list(self.commitments),
            failures=list(self.failures),
            recovery_history=list(self.recovery_history),
            visibility_scope=self.visibility_scope,
            explicit_identity=self.explicit_identity and self.participant_id != "UNKNOWN",
        )

    def merged(self, other: "NarrativeRecord") -> "NarrativeRecord":
        left = self.normalized()
        right = other.normalized()
        return NarrativeRecord(
            person=left.participant_id,
            contributions=_merge_unique(left.contributions, right.contributions),
            decisions=_merge_unique(left.decisions, right.decisions),
            conflicts=_merge_unique(left.conflicts, right.conflicts),
            superseded_decisions=_merge_unique(left.superseded_decisions, right.superseded_decisions),
            unresolved_questions=_merge_unique(left.unresolved_questions, right.unresolved_questions),
            current_purposes=_merge_unique(left.current_purposes, right.current_purposes),
            commitments=_merge_unique(left.commitments, right.commitments),
            failures=_merge_unique(left.failures, right.failures),
            recovery_history=_merge_unique(left.recovery_history, right.recovery_history),
            visibility_scope=left.visibility_scope,
            explicit_identity=left.explicit_identity and right.explicit_identity,
        )

    def to_record(self) -> Dict[str, object]:
        normalized = self.normalized()
        return {
            "participant_id": normalized.participant_id,
            "display_name": normalized.person,
            "explicit_identity": normalized.explicit_identity,
            "visibility_scope": normalized.visibility_scope.value,
            "contributions": list(normalized.contributions),
            "decisions": list(normalized.decisions),
            "conflicts": list(normalized.conflicts),
            "superseded_decisions": list(normalized.superseded_decisions),
            "unresolved_questions": list(normalized.unresolved_questions),
            "current_purposes": list(normalized.current_purposes),
            "commitments": list(normalized.commitments),
            "failures": list(normalized.failures),
            "recovery_history": list(normalized.recovery_history),
        }

    @classmethod
    def from_record(cls, payload: Dict[str, object]) -> "NarrativeRecord":
        return cls(
            person=str(payload.get("participant_id") or payload.get("display_name") or ""),
            contributions=list(payload.get("contributions", [])),
            decisions=list(payload.get("decisions", [])),
            conflicts=list(payload.get("conflicts", [])),
            superseded_decisions=list(payload.get("superseded_decisions", [])),
            unresolved_questions=list(payload.get("unresolved_questions", [])),
            current_purposes=list(payload.get("current_purposes", [])),
            commitments=list(payload.get("commitments", [])),
            failures=list(payload.get("failures", [])),
            recovery_history=list(payload.get("recovery_history", [])),
            visibility_scope=VisibilityScope(str(payload.get("visibility_scope", VisibilityScope.SHARED_PROJECT.value))),
            explicit_identity=bool(payload.get("explicit_identity", True)),
        )


class TeamNarrative:
    def __init__(self) -> None:
        self.records: Dict[str, NarrativeRecord] = {}
        self.events: List[Dict[str, str]] = []

    def update(self, record: NarrativeRecord) -> NarrativeRecord:
        normalized = record.normalized()
        existing = self.records.get(normalized.participant_id)
        merged = existing.merged(normalized) if existing else normalized
        self.records[normalized.participant_id] = merged
        self.events.append({"type": "narrative_updated", "participant_id": normalized.participant_id})
        return merged

    def to_records(self) -> List[Dict[str, object]]:
        return [record.to_record() for _, record in sorted(self.records.items())]

    @classmethod
    def from_events(cls, events: Iterable[Dict[str, object]]) -> "TeamNarrative":
        narrative = cls()
        for event in events:
            if not str(event.get("type", "")).startswith("session.narrative"):
                continue
            record = event.get("narrative")
            if isinstance(record, dict):
                narrative.update(NarrativeRecord.from_record(record))
        return narrative
