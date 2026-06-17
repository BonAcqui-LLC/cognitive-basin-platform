"""
Minimal planner integrating association retrieval into BasinLab context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .associations import AssociationField, AssociationRetrieval


@dataclass
class PlanStep:
    summary: str
    hold_conditions: List[str] = field(default_factory=list)


@dataclass
class PlannerOutput:
    purpose: str
    retrievals: List[AssociationRetrieval]
    steps: List[PlanStep]
    context: Dict[str, List[str]]


class GeneralistPlanner:
    def build_plan(self, purpose: str, association_field: AssociationField) -> PlannerOutput:
        retrievals = association_field.retrieve(purpose)
        context = {"association_ids": [retrieval.association_id for retrieval in retrievals]}
        return PlannerOutput(
            purpose=purpose,
            retrievals=retrievals,
            steps=[
                PlanStep(
                    summary=f"Investigate purpose: {purpose}",
                    hold_conditions=["Missing deterministic evidence", "Critical contradiction unresolved"],
                )
            ],
            context=context,
        )
