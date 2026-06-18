"""
Offline rehearsal with explicit simulation marking.
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
class RehearsalScenario:
    scenario_id: str
    detail: str
    simulation_label: str = "SIMULATED"

    def to_record(self) -> Dict[str, Any]:
        return {"scenario_id": self.scenario_id, "detail": self.detail, "simulation_label": self.simulation_label}


@dataclass
class RehearsalContext:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class RehearsalPolicy:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class RehearsalOutcome:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class RehearsalLesson:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class RehearsalRun:
    run_id: str
    scenario: RehearsalScenario
    context: RehearsalContext
    policy: RehearsalPolicy
    outcome: RehearsalOutcome
    lesson: RehearsalLesson

    def to_record(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario": self.scenario.to_record(),
            "context": self.context.to_record(),
            "policy": self.policy.to_record(),
            "outcome": self.outcome.to_record(),
            "lesson": self.lesson.to_record(),
        }


@dataclass
class RehearsalReceipt:
    runs: List[RehearsalRun]

    def to_record(self) -> Dict[str, Any]:
        return {"runs": _record(self.runs)}


class RehearsalManager:
    def __init__(self) -> None:
        self.runs: List[RehearsalRun] = []

    def rehearse(self, *, detail: str, budget_available: bool) -> RehearsalReceipt:
        if not budget_available:
            return RehearsalReceipt(list(self.runs))
        run = RehearsalRun(
            run_id=f"rehearsal-{len(self.runs) + 1:04d}",
            scenario=RehearsalScenario(f"scenario-{len(self.runs) + 1:04d}", detail),
            context=RehearsalContext("offline deterministic replay"),
            policy=RehearsalPolicy("simulation only"),
            outcome=RehearsalOutcome("no external effects"),
            lesson=RehearsalLesson("simulation cannot approve action"),
        )
        self.runs.append(run)
        return RehearsalReceipt(list(self.runs))


__all__ = [
    "RehearsalContext",
    "RehearsalLesson",
    "RehearsalManager",
    "RehearsalOutcome",
    "RehearsalPolicy",
    "RehearsalReceipt",
    "RehearsalRun",
    "RehearsalScenario",
]
