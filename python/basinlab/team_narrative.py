"""
Auditable project continuity records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


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


class TeamNarrative:
    def __init__(self) -> None:
        self.records: Dict[str, NarrativeRecord] = {}
        self.events: List[Dict[str, str]] = []

    def update(self, record: NarrativeRecord) -> None:
        self.records[record.person] = record
        self.events.append({"type": "narrative_updated", "person": record.person})
