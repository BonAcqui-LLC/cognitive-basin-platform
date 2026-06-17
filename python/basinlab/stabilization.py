"""
Stabilization primitives for the next Cognitive Basin layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StabilizationEvidence:
    evidence_id: str
    description: str
    supports_stability: bool


@dataclass
class StabilizationResult:
    stable: bool
    partial: bool
    false_attractor_detected: bool
    preserved_contradictions: List[str] = field(default_factory=list)
    recovery_route: str = ""
    replay_reference: str = ""


def assess_stabilization(
    converged: bool,
    contradictory_signals: List[str],
    attractor_strength: float,
    evidence: List[StabilizationEvidence],
) -> StabilizationResult:
    false_attractor = attractor_strength > 0.8 and any(not item.supports_stability for item in evidence)
    stable = converged and not contradictory_signals and not false_attractor
    partial = converged and (bool(contradictory_signals) or false_attractor)
    route = "preserve-contradiction-and-review" if contradictory_signals else "continue-monitoring"
    return StabilizationResult(
        stable=stable,
        partial=partial,
        false_attractor_detected=false_attractor,
        preserved_contradictions=list(contradictory_signals),
        recovery_route=route,
        replay_reference=f"stabilization:{int(stable)}:{int(partial)}:{int(false_attractor)}",
    )
