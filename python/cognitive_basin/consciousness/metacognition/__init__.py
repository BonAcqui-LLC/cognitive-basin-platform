"""
Metacognitive monitoring contracts and operational review logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MetaObservation:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class MetaAssessment:
    state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "detail": self.detail}


@dataclass
class MetaUncertainty:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class MetaConflict:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class MetaFailure:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class MetaCorrection:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class MetaQuestion:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class MetaReceipt:
    observations: List[MetaObservation]
    assessment: MetaAssessment
    uncertainties: List[MetaUncertainty] = field(default_factory=list)
    conflicts: List[MetaConflict] = field(default_factory=list)
    failures: List[MetaFailure] = field(default_factory=list)
    corrections: List[MetaCorrection] = field(default_factory=list)
    questions: List[MetaQuestion] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "observations": [item.to_record() for item in self.observations],
            "assessment": self.assessment.to_record(),
            "uncertainties": [item.to_record() for item in self.uncertainties],
            "conflicts": [item.to_record() for item in self.conflicts],
            "failures": [item.to_record() for item in self.failures],
            "corrections": [item.to_record() for item in self.corrections],
            "questions": [item.to_record() for item in self.questions],
        }


class MetacognitiveMonitor:
    STATES = {"CLEAR", "UNCERTAIN", "CONFLICTED", "OVERLOADED", "CAPTURED", "DRIFTING", "BLOCKED", "RECOVERING"}

    def assess(
        self,
        *,
        contradiction_count: int,
        source_count: int,
        workspace_overload: bool,
        authority_missing: bool,
        attention_state: str,
        repeated_without_progress: bool,
        purpose_drift: bool,
        simulation_as_fact: bool,
    ) -> MetaReceipt:
        observations = [
            MetaObservation(f"contradictions={contradiction_count}"),
            MetaObservation(f"sources={source_count}"),
            MetaObservation(f"attention={attention_state}"),
        ]
        uncertainties: List[MetaUncertainty] = []
        conflicts: List[MetaConflict] = []
        failures: List[MetaFailure] = []
        corrections: List[MetaCorrection] = []
        questions: List[MetaQuestion] = [
            MetaQuestion("do I have enough evidence?"),
            MetaQuestion("am I confusing simulation with observation?"),
        ]
        state = "CLEAR"
        detail = "evidence and attention remain within bounds"
        if source_count <= 1:
            uncertainties.append(MetaUncertainty("single-source dependence"))
            state = "UNCERTAIN"
            detail = "single source dependence detected"
        if contradiction_count > 0:
            conflicts.append(MetaConflict("contradictions remain visible"))
            state = "CONFLICTED"
            detail = "contradictions remain active"
        if workspace_overload:
            failures.append(MetaFailure("workspace overload"))
            state = "OVERLOADED"
            detail = "workspace budget pressure detected"
        if attention_state in {"captured", "unstable"}:
            failures.append(MetaFailure("attention captured or unstable"))
            state = "CAPTURED"
            detail = "attention requires correction"
        if purpose_drift:
            conflicts.append(MetaConflict("purpose drift"))
            corrections.append(MetaCorrection("realign focus with current purpose"))
            state = "DRIFTING"
            detail = "purpose drift detected"
        if repeated_without_progress:
            failures.append(MetaFailure("recursive review"))
            state = "BLOCKED"
            detail = "repeating without progress"
        if authority_missing:
            failures.append(MetaFailure("authority missing"))
            questions.append(MetaQuestion("am I exceeding authority?"))
            state = "BLOCKED"
            detail = "authority required before action"
        if simulation_as_fact:
            failures.append(MetaFailure("simulation reality confusion"))
            corrections.append(MetaCorrection("downgrade simulated output to SIMULATION"))
            state = "CONFLICTED"
            detail = "simulation treated like observation"
        return MetaReceipt(
            observations=observations,
            assessment=MetaAssessment(state, detail),
            uncertainties=uncertainties,
            conflicts=conflicts,
            failures=failures,
            corrections=corrections,
            questions=questions,
        )


__all__ = [
    "MetaAssessment",
    "MetaConflict",
    "MetaCorrection",
    "MetaFailure",
    "MetaObservation",
    "MetaQuestion",
    "MetaReceipt",
    "MetaUncertainty",
    "MetacognitiveMonitor",
]
