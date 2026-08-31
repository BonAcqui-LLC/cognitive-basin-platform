"""
Explicit adapters from specificity-local debt posture to existing namespaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from packages.ternary.states import ActionState, EpistemicState
from python.natural_math_lab.core import NaturalMathProcessState

from .debt import DebtAssessment, DebtPosture


@dataclass(frozen=True)
class BasinSpecificityDecision:
    epistemic: EpistemicState
    action: ActionState
    requested_action: ActionState
    provisional: bool
    reason: str
    receipt_id: str
    debt_posture: DebtPosture

    def to_record(self) -> Dict[str, Any]:
        return {
            "epistemic": self.epistemic.value,
            "action": self.action.value,
            "requested_action": self.requested_action.value,
            "provisional": self.provisional,
            "reason": self.reason,
            "receipt_id": self.receipt_id,
            "debt_posture": self.debt_posture.value,
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "BasinSpecificityDecision":
        return cls(
            epistemic=EpistemicState(str(payload["epistemic"])),
            action=ActionState(str(payload["action"])),
            requested_action=ActionState(
                str(payload.get("requested_action", ActionState.EXTEND.value))
            ),
            provisional=bool(payload["provisional"]),
            reason=str(payload["reason"]),
            receipt_id=str(payload["receipt_id"]),
            debt_posture=DebtPosture(str(payload["debt_posture"])),
        )


def govern_basin_action(
    assessment: DebtAssessment,
    *,
    epistemic: EpistemicState,
    requested_action: ActionState = ActionState.EXTEND,
) -> BasinSpecificityDecision:
    """
    Apply debt pressure to action only.

    The caller-supplied epistemic state is preserved verbatim; specificity
    measurement is not evidence that can promote or demote truth.
    """

    if epistemic == EpistemicState.CONTRADICTED:
        action = ActionState.RETRACT
        reason = "Cognitive Basin evidence is CONTRADICTED"
    elif epistemic == EpistemicState.UNRESOLVED:
        action = ActionState.HOLD
        reason = "Cognitive Basin evidence remains UNRESOLVED"
    elif assessment.posture in (DebtPosture.CRITICAL, DebtPosture.EXCEEDED):
        action = ActionState.RETRACT
        reason = f"specificity debt posture is {assessment.posture.value}"
    elif assessment.posture in (DebtPosture.CAUTION, DebtPosture.CONSTRAINED):
        action = ActionState.HOLD
        reason = f"specificity debt posture is {assessment.posture.value}"
    else:
        action = requested_action
        reason = "specificity debt is within operational policy"
    return BasinSpecificityDecision(
        epistemic=epistemic,
        action=action,
        requested_action=requested_action,
        provisional=action != ActionState.EXTEND,
        reason=reason,
        receipt_id=assessment.receipt_id,
        debt_posture=assessment.posture,
    )


def suggest_natural_math_process(
    assessment: DebtAssessment,
) -> NaturalMathProcessState:
    """Map debt posture into the separate Natural Math process namespace."""

    if assessment.posture == DebtPosture.OPERATIONAL:
        return NaturalMathProcessState.EXTEND
    if assessment.posture in (DebtPosture.CAUTION, DebtPosture.CONSTRAINED):
        return NaturalMathProcessState.SENSE
    return NaturalMathProcessState.RESTRICT
