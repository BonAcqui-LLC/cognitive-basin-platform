"""
Machine interoception and bounded operational regulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class InteroceptiveSignal:
    signal_id: str
    resource_id: str
    state: str
    reading: float
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "resource_id": self.resource_id,
            "state": self.state,
            "reading": self.reading,
            "detail": self.detail,
        }


@dataclass
class InternalResource:
    resource_id: str
    label: str
    unit: str

    def to_record(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "label": self.label, "unit": self.unit}


@dataclass
class ResourceBudget:
    resource_id: str
    maximum: float
    remaining: float
    unit: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "maximum": self.maximum,
            "remaining": self.remaining,
            "unit": self.unit,
        }


@dataclass
class ResourceUse:
    resource_id: str
    amount: float
    unit: str

    def to_record(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "amount": self.amount, "unit": self.unit}


@dataclass
class ResourcePressure:
    resource_id: str
    state: str
    severity: float
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "state": self.state,
            "severity": self.severity,
            "detail": self.detail,
        }


@dataclass
class ResourceFailure:
    resource_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "detail": self.detail}


@dataclass
class InternalConstraint:
    constraint_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"constraint_id": self.constraint_id, "detail": self.detail}


@dataclass
class SubsystemHealth:
    subsystem_id: str
    state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"subsystem_id": self.subsystem_id, "state": self.state, "detail": self.detail}


@dataclass
class SystemHealth:
    state: str
    subsystems: List[SubsystemHealth]

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "subsystems": _record(self.subsystems)}


@dataclass
class InternalPrediction:
    resource_id: str
    expected_state: str
    horizon: str

    def to_record(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "expected_state": self.expected_state, "horizon": self.horizon}


@dataclass
class InternalResidual:
    resource_id: str
    expected_state: str
    observed_state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "expected_state": self.expected_state,
            "observed_state": self.observed_state,
            "detail": self.detail,
        }


@dataclass
class RegulationTarget:
    resource_id: str
    target_state: str

    def to_record(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "target_state": self.target_state}


@dataclass
class RegulationRange:
    minimum: float
    maximum: float

    def to_record(self) -> Dict[str, Any]:
        return {"minimum": self.minimum, "maximum": self.maximum}


@dataclass
class RegulationPolicy:
    policy_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "detail": self.detail}


@dataclass
class RegulationAction:
    action_id: str
    detail: str
    preserves_provenance: bool = True

    def to_record(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "detail": self.detail,
            "preserves_provenance": self.preserves_provenance,
        }


@dataclass
class RegulationConflict:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class RegulationOutcome:
    state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "detail": self.detail}


@dataclass
class RegulationFailure:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class RegulationHistory:
    actions: List[RegulationAction] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {"actions": _record(self.actions)}


@dataclass
class RegulationProposal:
    proposal_id: str
    target: RegulationTarget
    policy: RegulationPolicy
    action: RegulationAction
    rationale: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target": self.target.to_record(),
            "policy": self.policy.to_record(),
            "action": self.action.to_record(),
            "rationale": self.rationale,
        }


@dataclass
class RegulationReceipt:
    signals: List[InteroceptiveSignal]
    pressures: List[ResourcePressure]
    proposals: List[RegulationProposal]
    health: SystemHealth
    history: RegulationHistory
    failures: List[RegulationFailure]

    def to_record(self) -> Dict[str, Any]:
        return {
            "signals": _record(self.signals),
            "pressures": _record(self.pressures),
            "proposals": _record(self.proposals),
            "health": self.health.to_record(),
            "history": self.history.to_record(),
            "failures": _record(self.failures),
        }


class InteroceptionMonitor:
    def __init__(self) -> None:
        self.history = RegulationHistory()

    def assess(self, metrics: Dict[str, float], *, connector_availability: bool, replay_integrity: bool, ci_state: str) -> RegulationReceipt:
        signals: List[InteroceptiveSignal] = []
        pressures: List[ResourcePressure] = []
        proposals: List[RegulationProposal] = []
        subsystem_states = [
            SubsystemHealth("connectors", "NOMINAL" if connector_availability else "DEGRADATION", "connector availability"),
            SubsystemHealth("replay", "NOMINAL" if replay_integrity else "CONFLICT", "replay integrity"),
            SubsystemHealth("ci", "NOMINAL" if ci_state == "success" else "INSTABILITY", "ci state"),
        ]
        for resource_id, reading in metrics.items():
            if reading >= 0.9:
                state = "DEPLETION" if "remaining" in resource_id else "SATURATION"
                severity = 1.0
            elif reading >= 0.75:
                state = "PRESSURE"
                severity = 0.8
            elif reading <= 0.15:
                state = "RECOVERY"
                severity = 0.2
            else:
                state = "NOMINAL"
                severity = 0.0
            signals.append(InteroceptiveSignal(f"signal-{resource_id}", resource_id, state, reading, f"{resource_id}={reading:.2f}"))
            if state in {"PRESSURE", "DEPLETION", "SATURATION"}:
                pressure = ResourcePressure(resource_id, state, severity, f"{resource_id} requires regulation")
                pressures.append(pressure)
                action_detail = {
                    "workspace_occupancy": "reduce workspace load",
                    "prediction_error_rate": "request evidence and lower rehearsal depth",
                    "failed_action_rate": "enter HOLD and review failures",
                    "hold_duration": "request human review",
                }.get(resource_id, "defer low-priority work")
                proposal = RegulationProposal(
                    proposal_id=f"regulation-{len(proposals) + 1:04d}",
                    target=RegulationTarget(resource_id, "NOMINAL"),
                    policy=RegulationPolicy("preserve-truth", "resource pressure may affect scheduling but not truth"),
                    action=RegulationAction(f"regulation-action-{len(proposals) + 1:04d}", action_detail),
                    rationale=pressure.detail,
                )
                proposals.append(proposal)
                self.history.actions.append(proposal.action)
        overall_state = "NOMINAL" if not pressures and connector_availability and replay_integrity and ci_state == "success" else "INSTABILITY"
        return RegulationReceipt(
            signals=signals,
            pressures=pressures,
            proposals=proposals,
            health=SystemHealth(overall_state, subsystem_states),
            history=self.history,
            failures=[],
        )


__all__ = [
    "InternalConstraint",
    "InternalPrediction",
    "InternalResidual",
    "InternalResource",
    "InteroceptionMonitor",
    "InteroceptiveSignal",
    "RegulationAction",
    "RegulationConflict",
    "RegulationFailure",
    "RegulationHistory",
    "RegulationOutcome",
    "RegulationPolicy",
    "RegulationProposal",
    "RegulationRange",
    "RegulationReceipt",
    "RegulationTarget",
    "ResourceBudget",
    "ResourceFailure",
    "ResourcePressure",
    "ResourceUse",
    "SubsystemHealth",
    "SystemHealth",
]
