"""
Calibratable Structural Debt Potential assessment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from .contracts import MeasurementReceipt


class DebtPosture(str, Enum):
    """Specificity-local risk postures, deliberately not action states."""

    OPERATIONAL = "OPERATIONAL"
    CAUTION = "CAUTION"
    CONSTRAINED = "CONSTRAINED"
    CRITICAL = "CRITICAL"
    EXCEEDED = "EXCEEDED"


@dataclass(frozen=True)
class DebtPolicy:
    """Weights and capacity-relative thresholds for one calibrated deployment."""

    discrepancy_weight: float = 1.0
    scar_weight: float = 0.8
    coercivity_weight: float = 0.6
    remanence_weight: float = 0.5
    branching_weight: float = 0.7
    ambiguity_weight: float = 0.4
    sera_waste_weight: float = 0.9
    ngr_weight: float = 1.2
    operational_threshold: float = 0.30
    caution_threshold: float = 0.60
    constrained_threshold: float = 0.85
    critical_threshold: float = 1.20

    def __post_init__(self) -> None:
        weights = (
            self.discrepancy_weight,
            self.scar_weight,
            self.coercivity_weight,
            self.remanence_weight,
            self.branching_weight,
            self.ambiguity_weight,
            self.sera_waste_weight,
            self.ngr_weight,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("debt weights must be non-negative")
        thresholds = (
            self.operational_threshold,
            self.caution_threshold,
            self.constrained_threshold,
            self.critical_threshold,
        )
        if thresholds != tuple(sorted(thresholds)) or len(set(thresholds)) != 4:
            raise ValueError("debt thresholds must be strictly increasing")
        if self.operational_threshold <= 0:
            raise ValueError("debt thresholds must be positive")

    def to_record(self) -> Dict[str, float]:
        return {
            "discrepancy_weight": self.discrepancy_weight,
            "scar_weight": self.scar_weight,
            "coercivity_weight": self.coercivity_weight,
            "remanence_weight": self.remanence_weight,
            "branching_weight": self.branching_weight,
            "ambiguity_weight": self.ambiguity_weight,
            "sera_waste_weight": self.sera_waste_weight,
            "ngr_weight": self.ngr_weight,
            "operational_threshold": self.operational_threshold,
            "caution_threshold": self.caution_threshold,
            "constrained_threshold": self.constrained_threshold,
            "critical_threshold": self.critical_threshold,
        }


@dataclass(frozen=True)
class StructuralDebtInputs:
    discrepancy_debt: float = 0.0
    scar_load: float = 0.0
    coercivity: float = 0.0
    remanence: float = 0.0
    branching_burden: float = 0.0
    ambiguity_load: float = 0.0
    sera_waste_channel: float = 0.0
    ngr_applied: float = 0.0

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.to_record().values()):
            raise ValueError("structural debt inputs must be non-negative")

    @classmethod
    def from_measurement(
        cls,
        receipt: MeasurementReceipt,
        **components: float,
    ) -> "StructuralDebtInputs":
        if "ngr_applied" in components:
            raise ValueError("ngr_applied is supplied by the measurement receipt")
        return cls(ngr_applied=receipt.ngr, **components)

    def to_record(self) -> Dict[str, float]:
        return {
            "discrepancy_debt": self.discrepancy_debt,
            "scar_load": self.scar_load,
            "coercivity": self.coercivity,
            "remanence": self.remanence,
            "branching_burden": self.branching_burden,
            "ambiguity_load": self.ambiguity_load,
            "sera_waste_channel": self.sera_waste_channel,
            "ngr_applied": self.ngr_applied,
        }


@dataclass(frozen=True)
class DebtAssessment:
    receipt_id: str
    policy: DebtPolicy
    inputs: StructuralDebtInputs
    resolution_capacity: float
    total_sdp: float
    debt_ratio: float
    posture: DebtPosture

    def to_record(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "policy": self.policy.to_record(),
            "inputs": self.inputs.to_record(),
            "resolution_capacity": self.resolution_capacity,
            "total_sdp": self.total_sdp,
            "debt_ratio": self.debt_ratio,
            "posture": self.posture.value,
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "DebtAssessment":
        return cls(
            receipt_id=str(payload["receipt_id"]),
            policy=DebtPolicy(**payload["policy"]),
            inputs=StructuralDebtInputs(**payload["inputs"]),
            resolution_capacity=float(payload["resolution_capacity"]),
            total_sdp=float(payload["total_sdp"]),
            debt_ratio=float(payload["debt_ratio"]),
            posture=DebtPosture(str(payload["posture"])),
        )


def assess_structural_debt(
    receipt: MeasurementReceipt,
    inputs: StructuralDebtInputs,
    *,
    resolution_capacity: float,
    policy: DebtPolicy | None = None,
) -> DebtAssessment:
    """Assess structural debt without recomputing or resampling specificity."""

    if resolution_capacity <= 0:
        raise ValueError("resolution_capacity must be positive")
    if inputs.ngr_applied != receipt.ngr:
        raise ValueError("debt inputs must carry NGR from the supplied receipt")
    active_policy = policy or DebtPolicy()
    total = (
        inputs.discrepancy_debt * active_policy.discrepancy_weight
        + inputs.scar_load * active_policy.scar_weight
        + inputs.coercivity * active_policy.coercivity_weight
        + inputs.remanence * active_policy.remanence_weight
        + inputs.branching_burden * active_policy.branching_weight
        + inputs.ambiguity_load * active_policy.ambiguity_weight
        + inputs.sera_waste_channel * active_policy.sera_waste_weight
        + inputs.ngr_applied * active_policy.ngr_weight
    )
    total = round(total, 12)
    ratio = round(total / resolution_capacity, 12)
    if ratio < active_policy.operational_threshold:
        posture = DebtPosture.OPERATIONAL
    elif ratio < active_policy.caution_threshold:
        posture = DebtPosture.CAUTION
    elif ratio < active_policy.constrained_threshold:
        posture = DebtPosture.CONSTRAINED
    elif ratio < active_policy.critical_threshold:
        posture = DebtPosture.CRITICAL
    else:
        posture = DebtPosture.EXCEEDED
    return DebtAssessment(
        receipt_id=receipt.receipt_id,
        policy=active_policy,
        inputs=inputs,
        resolution_capacity=resolution_capacity,
        total_sdp=total,
        debt_ratio=ratio,
        posture=posture,
    )


def verify_debt_assessment(
    receipt: MeasurementReceipt,
    assessment: DebtAssessment,
) -> bool:
    """Recompute a persisted assessment from its declared policy and inputs."""

    if assessment.receipt_id != receipt.receipt_id:
        return False
    try:
        expected = assess_structural_debt(
            receipt,
            assessment.inputs,
            resolution_capacity=assessment.resolution_capacity,
            policy=assessment.policy,
        )
    except ValueError:
        return False
    return expected == assessment
