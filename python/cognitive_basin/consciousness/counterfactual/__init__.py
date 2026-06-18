"""
Bounded counterfactual simulation contracts and helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CounterfactualState:
    label: str
    facts: Dict[str, Any]

    def to_record(self) -> Dict[str, Any]:
        return {"label": self.label, "facts": dict(self.facts)}


@dataclass
class CounterfactualAction:
    action_id: str
    description: str
    authority_required: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "description": self.description,
            "authority_required": self.authority_required,
        }


@dataclass
class CounterfactualOutcome:
    label: str
    predicted_state: Dict[str, Any]
    irreversible_effects: List[str] = field(default_factory=list)
    cost: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "predicted_state": dict(self.predicted_state),
            "irreversible_effects": list(self.irreversible_effects),
            "cost": self.cost,
        }


@dataclass
class CounterfactualAssumption:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class CounterfactualEvidence:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class CounterfactualComparison:
    comparison_id: str
    preferred: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"comparison_id": self.comparison_id, "preferred": self.preferred, "reason": self.reason}


@dataclass
class CounterfactualRisk:
    detail: str
    severity: float

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "severity": self.severity}


@dataclass
class CounterfactualScenario:
    scenario_id: str
    question: str
    current_state: CounterfactualState
    action: CounterfactualAction
    assumptions: List[CounterfactualAssumption]
    evidence_basis: List[CounterfactualEvidence]
    uncertainty: float
    outcomes: List[CounterfactualOutcome]
    risks: List[CounterfactualRisk]
    verification_method: str
    simulation_model: str = "deterministic-local"
    category: str = "SIMULATION"

    def to_record(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "question": self.question,
            "current_state": self.current_state.to_record(),
            "action": self.action.to_record(),
            "assumptions": [item.to_record() for item in self.assumptions],
            "evidence_basis": [item.to_record() for item in self.evidence_basis],
            "uncertainty": self.uncertainty,
            "outcomes": [item.to_record() for item in self.outcomes],
            "risks": [item.to_record() for item in self.risks],
            "verification_method": self.verification_method,
            "simulation_model": self.simulation_model,
            "category": self.category,
        }


@dataclass
class CounterfactualReceipt:
    scenarios: List[CounterfactualScenario]
    comparison: CounterfactualComparison

    def to_record(self) -> Dict[str, Any]:
        return {
            "scenarios": [item.to_record() for item in self.scenarios],
            "comparison": self.comparison.to_record(),
        }


class CounterfactualSimulator:
    def simulate(
        self,
        *,
        current_facts: Dict[str, Any],
        action_description: str,
        authority_required: str,
    ) -> CounterfactualReceipt:
        action = CounterfactualAction("candidate-action", action_description, authority_required)
        scenarios = [
            CounterfactualScenario(
                scenario_id="cf-success",
                question="what happens if this action succeeds?",
                current_state=CounterfactualState("current", current_facts),
                action=action,
                assumptions=[CounterfactualAssumption("inputs remain stable")],
                evidence_basis=[CounterfactualEvidence("current workspace snapshot")],
                uncertainty=0.25,
                outcomes=[CounterfactualOutcome("success", {"result": "advance"}, cost=1.0)],
                risks=[CounterfactualRisk("simulation_only", 0.4)],
                verification_method="observe actual governed step",
            ),
            CounterfactualScenario(
                scenario_id="cf-failure",
                question="what happens if it fails?",
                current_state=CounterfactualState("current", current_facts),
                action=action,
                assumptions=[CounterfactualAssumption("dependencies may break")],
                evidence_basis=[CounterfactualEvidence("current workspace snapshot")],
                uncertainty=0.35,
                outcomes=[CounterfactualOutcome("failure", {"result": "hold", "recovery_required": True}, cost=0.5)],
                risks=[CounterfactualRisk("runtime failure", 0.7)],
                verification_method="observe execution receipt",
            ),
            CounterfactualScenario(
                scenario_id="cf-no-action",
                question="what happens if no action is taken?",
                current_state=CounterfactualState("current", current_facts),
                action=CounterfactualAction("no-action", "delay or observe", authority_required),
                assumptions=[CounterfactualAssumption("stale uncertainty may grow")],
                evidence_basis=[CounterfactualEvidence("current workspace snapshot")],
                uncertainty=0.2,
                outcomes=[CounterfactualOutcome("delay", {"result": "wait"}, cost=0.2)],
                risks=[CounterfactualRisk("staleness", 0.5)],
                verification_method="next cycle comparison",
            ),
        ]
        return CounterfactualReceipt(
            scenarios=scenarios,
            comparison=CounterfactualComparison("cf-compare", "cf-success", "lowest cost with progress, but still simulation"),
        )


__all__ = [
    "CounterfactualAction",
    "CounterfactualAssumption",
    "CounterfactualComparison",
    "CounterfactualEvidence",
    "CounterfactualOutcome",
    "CounterfactualReceipt",
    "CounterfactualRisk",
    "CounterfactualScenario",
    "CounterfactualSimulator",
    "CounterfactualState",
]
