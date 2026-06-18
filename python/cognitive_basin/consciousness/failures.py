"""
Explicit operational machine-consciousness failure records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ConsciousnessFailure:
    failure_type: str
    detection: str
    evidence: List[str]
    affected_episode: str
    affected_purpose: str
    severity: float
    hold_required: bool
    recovery_route: str
    replay_references: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "detection": self.detection,
            "evidence": list(self.evidence),
            "affected_episode": self.affected_episode,
            "affected_purpose": self.affected_purpose,
            "severity": self.severity,
            "hold_required": self.hold_required,
            "recovery_route": self.recovery_route,
            "replay_references": list(self.replay_references),
        }


def _failure(name: str, detection: str, evidence: List[str], purpose: str, hold_required: bool) -> ConsciousnessFailure:
    return ConsciousnessFailure(name, detection, evidence, "", purpose, 0.7 if hold_required else 0.4, hold_required, "review and replay", [])


class PerceptualBlindness(ConsciousnessFailure):
    pass


class PerceptualFlood(ConsciousnessFailure):
    pass


class SourceMonopoly(ConsciousnessFailure):
    pass


class AttentionCapture(ConsciousnessFailure):
    pass


class PurposeDrift(ConsciousnessFailure):
    pass


class SelfModelError(ConsciousnessFailure):
    pass


class ContinuityBreak(ConsciousnessFailure):
    pass


class CounterfactualConfusion(ConsciousnessFailure):
    pass


class AuthorityConfusion(ConsciousnessFailure):
    pass


class MemoryRealityConfusion(ConsciousnessFailure):
    pass


class SimulationRealityConfusion(ConsciousnessFailure):
    pass


class ConfidenceEvidenceMismatch(ConsciousnessFailure):
    pass


class GlobalWorkspaceStarvation(ConsciousnessFailure):
    pass


class RecursiveMetacognition(ConsciousnessFailure):
    pass


class ActionWithoutAwareness(ConsciousnessFailure):
    pass


class AwarenessWithoutAction(ConsciousnessFailure):
    pass


class ContradictionSuppression(ConsciousnessFailure):
    pass


__all__ = [
    "ActionWithoutAwareness",
    "AttentionCapture",
    "AuthorityConfusion",
    "AwarenessWithoutAction",
    "ConfidenceEvidenceMismatch",
    "ConsciousnessFailure",
    "ContinuityBreak",
    "ContradictionSuppression",
    "CounterfactualConfusion",
    "GlobalWorkspaceStarvation",
    "MemoryRealityConfusion",
    "PerceptualBlindness",
    "PerceptualFlood",
    "PurposeDrift",
    "RecursiveMetacognition",
    "SelfModelError",
    "SimulationRealityConfusion",
    "SourceMonopoly",
]
