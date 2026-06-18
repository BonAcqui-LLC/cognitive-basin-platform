"""
Multi-horizon planning.
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
class PlanningHorizon:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class PlanDependency:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PlanRisk:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PlanResource:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PlanCheckpoint:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PlanStep:
    step_id: str
    detail: str
    authority_needed: str
    evidence_needed: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "detail": self.detail,
            "authority_needed": self.authority_needed,
            "evidence_needed": list(self.evidence_needed),
        }


@dataclass
class PlanBranch:
    branch_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"branch_id": self.branch_id, "detail": self.detail}


@dataclass
class PlanState:
    state_id: str
    purpose: str
    predicted_state: str

    def to_record(self) -> Dict[str, Any]:
        return {"state_id": self.state_id, "purpose": self.purpose, "predicted_state": self.predicted_state}


@dataclass
class PlanRevision:
    horizon: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"horizon": self.horizon, "detail": self.detail}


@dataclass
class PlanReceipt:
    horizon: PlanningHorizon
    state: PlanState
    steps: List[PlanStep]
    branches: List[PlanBranch]
    dependencies: List[PlanDependency]
    risks: List[PlanRisk]
    resources: List[PlanResource]
    checkpoint: PlanCheckpoint
    abandonment_condition: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "horizon": self.horizon.to_record(),
            "state": self.state.to_record(),
            "steps": _record(self.steps),
            "branches": _record(self.branches),
            "dependencies": _record(self.dependencies),
            "risks": _record(self.risks),
            "resources": _record(self.resources),
            "checkpoint": self.checkpoint.to_record(),
            "abandonment_condition": self.abandonment_condition,
        }


class Planner:
    def build(self, *, purpose: str, resource_pressure: bool, authority_needed: str) -> List[PlanReceipt]:
        horizons = [
            "IMMEDIATE",
            "NEXT_CYCLE",
            "SESSION",
            "TRANCHE",
            "PROJECT",
            "DEPLOYMENT",
            "LONG_TERM",
        ]
        plans: List[PlanReceipt] = []
        for index, horizon in enumerate(horizons, start=1):
            plans.append(
                PlanReceipt(
                    horizon=PlanningHorizon(horizon),
                    state=PlanState(f"plan-state-{index:04d}", purpose, "HOLD" if resource_pressure and horizon == "IMMEDIATE" else "ADVANCE"),
                    steps=[PlanStep(f"plan-step-{index:04d}", f"{horizon.lower()} step for {purpose}", authority_needed, ["current evidence"])],
                    branches=[PlanBranch(f"plan-branch-{index:04d}", "fallback if dependency fails")],
                    dependencies=[PlanDependency("verified evidence"), PlanDependency("authority remains explicit")],
                    risks=[PlanRisk("resource pressure")] if resource_pressure else [PlanRisk("stale evidence")],
                    resources=[PlanResource("cycles"), PlanResource("workspace budget")],
                    checkpoint=PlanCheckpoint(f"{horizon.lower()} checkpoint"),
                    abandonment_condition="authority denied or contradiction unresolved",
                )
            )
        return plans


__all__ = [
    "PlanBranch",
    "PlanCheckpoint",
    "PlanDependency",
    "PlanReceipt",
    "PlanResource",
    "PlanRevision",
    "PlanRisk",
    "PlanState",
    "PlanStep",
    "Planner",
    "PlanningHorizon",
]
