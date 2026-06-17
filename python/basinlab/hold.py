"""
Measurable HOLD fog tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class HoldFogRecord:
    reason: str
    affected_circuit: str
    blocked_actions: List[str]
    permitted_actions: List[str]
    required_evidence: List[str]
    review_condition: str
    expiry_condition: str
    recovery_path: str
    released: bool = False


class HoldFogTracker:
    def __init__(self) -> None:
        self.records: List[HoldFogRecord] = []

    def enter(self, record: HoldFogRecord) -> HoldFogRecord:
        self.records.append(record)
        return record

    def release(self, index: int, evidence: List[str]) -> bool:
        record = self.records[index]
        if not set(record.required_evidence).issubset(set(evidence)):
            return False
        record.released = True
        return True
