"""
Recovery routes for contradiction scars.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class RecoveryRequirement:
    description: str
    required_evidence: List[str] = field(default_factory=list)


@dataclass
class RecoveryRoute:
    route_id: str
    originating_scar_id: str
    evidence_required: List[RecoveryRequirement]
    prohibited_shortcuts: List[str]
    permitted_transitions: List[str]
    review_requirement: str
    success_condition: str
    failure_condition: str
    retained_uncertainty: str


@dataclass
class RecoveryAttempt:
    route_id: str
    provided_evidence: List[str]
    shortcut_attempts: List[str]
    pressure: float = 0.0
    confidence: float = 0.0
    repetition_count: int = 0


@dataclass
class RecoveryResult:
    route_id: str
    succeeded: bool
    reasons: List[str]
    timestamp: float


class RecoveryManager:
    def __init__(self) -> None:
        self.attempts: List[RecoveryAttempt] = []
        self.results: List[RecoveryResult] = []

    def attempt_recovery(self, route: RecoveryRoute, attempt: RecoveryAttempt) -> RecoveryResult:
        reasons: List[str] = []
        self.attempts.append(attempt)
        for shortcut in attempt.shortcut_attempts:
            if shortcut in route.prohibited_shortcuts:
                reasons.append(f"Prohibited shortcut attempted: {shortcut}")
        for requirement in route.evidence_required:
            for required_item in requirement.required_evidence:
                if required_item not in attempt.provided_evidence:
                    reasons.append(f"Missing required evidence: {required_item}")
        succeeded = not reasons
        result = RecoveryResult(
            route_id=route.route_id,
            succeeded=succeeded,
            reasons=reasons,
            timestamp=time.time(),
        )
        self.results.append(result)
        return result
