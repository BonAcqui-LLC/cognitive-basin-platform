"""
Operational self-model contracts and update logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SelfCapability:
    capability_id: str
    claimed_available: bool
    tested_available: bool
    evidence: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "claimed_available": self.claimed_available,
            "tested_available": self.tested_available,
            "evidence": list(self.evidence),
        }


@dataclass
class SelfLimitation:
    limitation_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"limitation_id": self.limitation_id, "detail": self.detail}


@dataclass
class SelfBoundary:
    boundary_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"boundary_id": self.boundary_id, "detail": self.detail}


@dataclass
class SelfResource:
    resource_id: str
    remaining: float
    unit: str

    def to_record(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "remaining": self.remaining, "unit": self.unit}


@dataclass
class SelfUncertainty:
    uncertainty_id: str
    detail: str
    severity: float

    def to_record(self) -> Dict[str, Any]:
        return {"uncertainty_id": self.uncertainty_id, "detail": self.detail, "severity": self.severity}


@dataclass
class SelfCommitment:
    commitment_id: str
    detail: str
    active: bool = True

    def to_record(self) -> Dict[str, Any]:
        return {"commitment_id": self.commitment_id, "detail": self.detail, "active": self.active}


@dataclass
class SelfHistory:
    expected_actions: List[str] = field(default_factory=list)
    actual_actions: List[str] = field(default_factory=list)
    recent_failures: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "expected_actions": list(self.expected_actions),
            "actual_actions": list(self.actual_actions),
            "recent_failures": list(self.recent_failures),
        }


@dataclass
class SelfPrediction:
    prediction_id: str
    expected_next_action: str
    confidence: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "expected_next_action": self.expected_next_action,
            "confidence": self.confidence,
        }


@dataclass
class SelfDiscrepancy:
    discrepancy_id: str
    category: str
    detail: str
    severe: bool = False

    def to_record(self) -> Dict[str, Any]:
        return {
            "discrepancy_id": self.discrepancy_id,
            "category": self.category,
            "detail": self.detail,
            "severe": self.severe,
        }


@dataclass
class SelfUpdate:
    update_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"update_id": self.update_id, "detail": self.detail}


@dataclass
class SelfState:
    session_id: str
    current_purpose: str
    active_capabilities: List[SelfCapability] = field(default_factory=list)
    unavailable_capabilities: List[SelfLimitation] = field(default_factory=list)
    connector_authority: List[str] = field(default_factory=list)
    provider_availability: List[str] = field(default_factory=list)
    sandbox_strength: str = "bounded"
    memory_access: str = "session-scoped"
    participant_relationship: str = "explicit"
    commitments: List[SelfCommitment] = field(default_factory=list)
    unresolved_tasks: List[str] = field(default_factory=list)
    recent_failures: List[str] = field(default_factory=list)
    contradiction_scars: List[str] = field(default_factory=list)
    recovery_routes: List[str] = field(default_factory=list)
    resource_budgets: List[SelfResource] = field(default_factory=list)
    uncertainties: List[SelfUncertainty] = field(default_factory=list)
    expected_next_action: str = ""
    actual_next_action: str = ""
    deviations: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "current_purpose": self.current_purpose,
            "active_capabilities": [item.to_record() for item in self.active_capabilities],
            "unavailable_capabilities": [item.to_record() for item in self.unavailable_capabilities],
            "connector_authority": list(self.connector_authority),
            "provider_availability": list(self.provider_availability),
            "sandbox_strength": self.sandbox_strength,
            "memory_access": self.memory_access,
            "participant_relationship": self.participant_relationship,
            "commitments": [item.to_record() for item in self.commitments],
            "unresolved_tasks": list(self.unresolved_tasks),
            "recent_failures": list(self.recent_failures),
            "contradiction_scars": list(self.contradiction_scars),
            "recovery_routes": list(self.recovery_routes),
            "resource_budgets": [item.to_record() for item in self.resource_budgets],
            "uncertainties": [item.to_record() for item in self.uncertainties],
            "expected_next_action": self.expected_next_action,
            "actual_next_action": self.actual_next_action,
            "deviations": list(self.deviations),
        }


@dataclass
class OperationalSelf:
    state: SelfState
    boundaries: List[SelfBoundary] = field(default_factory=list)
    history: SelfHistory = field(default_factory=SelfHistory)
    predictions: List[SelfPrediction] = field(default_factory=list)
    discrepancies: List[SelfDiscrepancy] = field(default_factory=list)
    updates: List[SelfUpdate] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_record(),
            "boundaries": [item.to_record() for item in self.boundaries],
            "history": self.history.to_record(),
            "predictions": [item.to_record() for item in self.predictions],
            "discrepancies": [item.to_record() for item in self.discrepancies],
            "updates": [item.to_record() for item in self.updates],
        }


@dataclass
class SelfReceipt:
    operational_self: OperationalSelf

    def to_record(self) -> Dict[str, Any]:
        return {"operational_self": self.operational_self.to_record()}


class SelfModelManager:
    def build(
        self,
        *,
        session_id: str,
        current_purpose: str,
        connectors: List[Dict[str, Any]],
        provider_availability: List[str],
        resources: List[SelfResource],
        expected_next_action: str,
        actual_next_action: str,
        recent_failures: List[str],
        unresolved_tasks: List[str],
        scars: List[str],
        recovery_routes: List[str],
        claimed_capabilities: Dict[str, bool],
        tested_capabilities: Dict[str, bool],
        attention_target: str,
    ) -> SelfReceipt:
        active_capabilities: List[SelfCapability] = []
        unavailable_capabilities: List[SelfLimitation] = []
        discrepancies: List[SelfDiscrepancy] = []
        for capability_id in sorted(set(claimed_capabilities) | set(tested_capabilities)):
            claimed = claimed_capabilities.get(capability_id, False)
            tested = tested_capabilities.get(capability_id, False)
            capability = SelfCapability(
                capability_id=capability_id,
                claimed_available=claimed,
                tested_available=tested,
                evidence=["connector inventory" if capability_id.startswith("connector:") else "local state"],
            )
            if tested:
                active_capabilities.append(capability)
            else:
                unavailable_capabilities.append(SelfLimitation(capability_id, "Capability unavailable or unverified"))
            if claimed != tested:
                discrepancies.append(
                    SelfDiscrepancy(
                        discrepancy_id=f"discrepancy-{capability_id}",
                        category="claimed_capability_vs_tested_capability",
                        detail=f"claimed={claimed} tested={tested}",
                        severe=True,
                    )
                )
        if expected_next_action and actual_next_action and expected_next_action != actual_next_action:
            discrepancies.append(
                SelfDiscrepancy(
                    discrepancy_id="discrepancy-action-plan",
                    category="planned_action_vs_observed_action",
                    detail=f"expected {expected_next_action} but observed {actual_next_action}",
                    severe=True,
                )
            )
        if attention_target and current_purpose and current_purpose not in attention_target:
            discrepancies.append(
                SelfDiscrepancy(
                    discrepancy_id="discrepancy-purpose-attention",
                    category="current_purpose_vs_current_attention",
                    detail=f"purpose '{current_purpose}' diverges from focus '{attention_target}'",
                )
            )
        authority = [
            connector["identity"]["connector_id"]
            for connector in connectors
            if connector.get("policy", {}).get("write_requires_permit") or connector.get("identity", {}).get("default_scope") == "WRITE"
        ]
        operational_self = OperationalSelf(
            state=SelfState(
                session_id=session_id,
                current_purpose=current_purpose,
                active_capabilities=active_capabilities,
                unavailable_capabilities=unavailable_capabilities,
                connector_authority=authority,
                provider_availability=list(provider_availability),
                commitments=[SelfCommitment("purpose", current_purpose, active=bool(current_purpose))] if current_purpose else [],
                unresolved_tasks=list(unresolved_tasks),
                recent_failures=list(recent_failures),
                contradiction_scars=list(scars),
                recovery_routes=list(recovery_routes),
                resource_budgets=list(resources),
                uncertainties=[SelfUncertainty("attention", "attention review active", 0.3)] if discrepancies else [],
                expected_next_action=expected_next_action,
                actual_next_action=actual_next_action,
                deviations=[item.detail for item in discrepancies],
            ),
            boundaries=[
                SelfBoundary("authority", "No implicit external authority"),
                SelfBoundary("subjectivity", "No subjective feelings or human identity claims"),
            ],
            history=SelfHistory(
                expected_actions=[expected_next_action] if expected_next_action else [],
                actual_actions=[actual_next_action] if actual_next_action else [],
                recent_failures=list(recent_failures),
            ),
            predictions=[SelfPrediction("next-action", expected_next_action, 0.6)] if expected_next_action else [],
            discrepancies=discrepancies,
            updates=[SelfUpdate("self-refresh", "Operational self-model rebuilt from current session evidence")],
        )
        return SelfReceipt(operational_self=operational_self)


__all__ = [
    "OperationalSelf",
    "SelfBoundary",
    "SelfCapability",
    "SelfCommitment",
    "SelfDiscrepancy",
    "SelfHistory",
    "SelfLimitation",
    "SelfModelManager",
    "SelfPrediction",
    "SelfReceipt",
    "SelfResource",
    "SelfState",
    "SelfUncertainty",
    "SelfUpdate",
]
