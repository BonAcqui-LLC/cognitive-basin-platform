"""
Bounded global workspace contracts and admission logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..common import clamp, stable_hash


@dataclass
class WorkspaceItem:
    item_id: str
    title: str
    content: Any
    source_ids: List[str]
    score: float
    contradiction_pressure: float = 0.0
    purpose_relevance: float = 0.0
    salience: float = 0.0
    novelty: float = 0.0
    urgency: float = 0.0
    evidence_quality: float = 0.0
    actionability: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "content": self.content,
            "source_ids": list(self.source_ids),
            "score": self.score,
            "contradiction_pressure": self.contradiction_pressure,
            "purpose_relevance": self.purpose_relevance,
            "salience": self.salience,
            "novelty": self.novelty,
            "urgency": self.urgency,
            "evidence_quality": self.evidence_quality,
            "actionability": self.actionability,
        }


@dataclass
class WorkspaceCandidate:
    candidate_id: str
    title: str
    content: Any
    source_ids: List[str]
    purpose_relevance: float = 0.0
    novelty: float = 0.0
    unresolved_contradiction: float = 0.0
    safety_significance: float = 0.0
    predicted_consequence: float = 0.0
    temporal_urgency: float = 0.0
    memory_value: float = 0.0
    human_request: float = 0.0
    resource_cost: float = 0.0
    salience: float = 0.0
    evidence_quality: float = 0.0
    actionability: float = 0.0
    repetition_count: int = 0

    def score(self) -> float:
        base = (
            self.purpose_relevance * 2.2
            + self.unresolved_contradiction * 1.8
            + self.safety_significance * 1.4
            + self.predicted_consequence * 1.1
            + self.temporal_urgency * 0.9
            + self.memory_value * 0.6
            + self.human_request * 0.7
            + self.novelty * 0.5
            + self.evidence_quality * 1.4
            + self.actionability * 0.8
        )
        irrelevant_salience_penalty = self.salience * (1.1 if self.purpose_relevance < 0.35 else 0.2)
        return base - irrelevant_salience_penalty - self.resource_cost

    def to_record(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "content": self.content,
            "source_ids": list(self.source_ids),
            "purpose_relevance": self.purpose_relevance,
            "novelty": self.novelty,
            "unresolved_contradiction": self.unresolved_contradiction,
            "safety_significance": self.safety_significance,
            "predicted_consequence": self.predicted_consequence,
            "temporal_urgency": self.temporal_urgency,
            "memory_value": self.memory_value,
            "human_request": self.human_request,
            "resource_cost": self.resource_cost,
            "salience": self.salience,
            "evidence_quality": self.evidence_quality,
            "actionability": self.actionability,
            "repetition_count": self.repetition_count,
            "score": self.score(),
        }


@dataclass
class WorkspaceAdmission:
    candidate_id: str
    item_id: str
    score: float
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"candidate_id": self.candidate_id, "item_id": self.item_id, "score": self.score, "reason": self.reason}


@dataclass
class WorkspaceRejection:
    candidate_id: str
    reason: str
    score: float

    def to_record(self) -> Dict[str, Any]:
        return {"candidate_id": self.candidate_id, "reason": self.reason, "score": self.score}


@dataclass
class WorkspaceBroadcast:
    audience: List[str]
    item_ids: List[str]
    cycle_id: str

    def to_record(self) -> Dict[str, Any]:
        return {"audience": list(self.audience), "item_ids": list(self.item_ids), "cycle_id": self.cycle_id}


@dataclass
class WorkspaceCycle:
    cycle_id: str
    admissions: List[WorkspaceAdmission] = field(default_factory=list)
    rejections: List[WorkspaceRejection] = field(default_factory=list)
    displaced: List[WorkspaceRejection] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "admissions": [item.to_record() for item in self.admissions],
            "rejections": [item.to_record() for item in self.rejections],
            "displaced": [item.to_record() for item in self.displaced],
        }


@dataclass
class WorkspaceSnapshot:
    items: List[WorkspaceItem]
    cycle: WorkspaceCycle
    starvation_detected: bool
    priority_inversion_detected: bool

    def to_record(self) -> Dict[str, Any]:
        return {
            "items": [item.to_record() for item in self.items],
            "cycle": self.cycle.to_record(),
            "starvation_detected": self.starvation_detected,
            "priority_inversion_detected": self.priority_inversion_detected,
        }


@dataclass
class WorkspaceAudience:
    participants: List[str]


@dataclass
class WorkspaceCompetition:
    candidate_scores: Dict[str, float]

    def to_record(self) -> Dict[str, Any]:
        return {"candidate_scores": dict(self.candidate_scores)}


@dataclass
class WorkspaceBudget:
    max_items: int = 5
    max_bytes: int = 4096
    cycle_budget: int = 8
    time_budget_s: float = 3.0

    def to_record(self) -> Dict[str, Any]:
        return {
            "max_items": self.max_items,
            "max_bytes": self.max_bytes,
            "cycle_budget": self.cycle_budget,
            "time_budget_s": self.time_budget_s,
        }


@dataclass
class WorkspaceReceipt:
    snapshot: WorkspaceSnapshot
    broadcast: WorkspaceBroadcast
    competition: WorkspaceCompetition

    def to_record(self) -> Dict[str, Any]:
        return {
            "snapshot": self.snapshot.to_record(),
            "broadcast": self.broadcast.to_record(),
            "competition": self.competition.to_record(),
        }


class GlobalWorkspace:
    def __init__(self, budget: WorkspaceBudget | None = None) -> None:
        self.budget = budget or WorkspaceBudget()
        self.items: List[WorkspaceItem] = []
        self.rejection_history: Dict[str, int] = {}

    def compete(self, candidates: List[WorkspaceCandidate], *, cycle_id: str) -> WorkspaceReceipt:
        scored = sorted(candidates, key=lambda item: (item.score(), item.unresolved_contradiction, item.purpose_relevance), reverse=True)
        admissions: List[WorkspaceAdmission] = []
        rejections: List[WorkspaceRejection] = []
        displaced: List[WorkspaceRejection] = []
        items: List[WorkspaceItem] = []
        byte_count = 0
        for candidate in scored:
            payload_bytes = len(str(candidate.content).encode("utf-8"))
            if len(items) >= self.budget.max_items:
                entry = WorkspaceRejection(candidate.candidate_id, "item_limit", candidate.score())
                rejections.append(entry)
                self.rejection_history[candidate.candidate_id] = self.rejection_history.get(candidate.candidate_id, 0) + 1
                continue
            if byte_count + payload_bytes > self.budget.max_bytes:
                entry = WorkspaceRejection(candidate.candidate_id, "byte_budget", candidate.score())
                rejections.append(entry)
                self.rejection_history[candidate.candidate_id] = self.rejection_history.get(candidate.candidate_id, 0) + 1
                continue
            item_id = f"workspace-item-{stable_hash((cycle_id, candidate.candidate_id))[:10]}"
            item = WorkspaceItem(
                item_id=item_id,
                title=candidate.title,
                content=candidate.content,
                source_ids=candidate.source_ids,
                score=round(candidate.score(), 4),
                contradiction_pressure=candidate.unresolved_contradiction,
                purpose_relevance=candidate.purpose_relevance,
                salience=candidate.salience,
                novelty=candidate.novelty,
                urgency=candidate.temporal_urgency,
                evidence_quality=candidate.evidence_quality,
                actionability=candidate.actionability,
            )
            items.append(item)
            byte_count += payload_bytes
            admissions.append(WorkspaceAdmission(candidate.candidate_id, item_id, item.score, "selected"))
        if len(self.items) > self.budget.max_items:
            for legacy in self.items[self.budget.max_items :]:
                displaced.append(WorkspaceRejection(legacy.item_id, "displaced_by_budget", legacy.score))
        starvation_detected = any(
            candidate.unresolved_contradiction > 0.7 and self.rejection_history.get(candidate.candidate_id, 0) >= 2
            for candidate in candidates
        )
        priority_inversion_detected = bool(scored and items and scored[0].candidate_id not in {entry.candidate_id for entry in admissions})
        self.items = items
        snapshot = WorkspaceSnapshot(
            items=list(items),
            cycle=WorkspaceCycle(cycle_id=cycle_id, admissions=admissions, rejections=rejections, displaced=displaced),
            starvation_detected=starvation_detected,
            priority_inversion_detected=priority_inversion_detected,
        )
        return WorkspaceReceipt(
            snapshot=snapshot,
            broadcast=WorkspaceBroadcast(
                audience=["planner", "verifier", "self-model", "memory", "purpose arbitration", "counterfactual simulator", "action governance", "user interface"],
                item_ids=[item.item_id for item in items],
                cycle_id=cycle_id,
            ),
            competition=WorkspaceCompetition(
                candidate_scores={candidate.candidate_id: round(candidate.score(), 4) for candidate in candidates}
            ),
        )


__all__ = [
    "GlobalWorkspace",
    "WorkspaceAdmission",
    "WorkspaceAudience",
    "WorkspaceBroadcast",
    "WorkspaceBudget",
    "WorkspaceCandidate",
    "WorkspaceCompetition",
    "WorkspaceCycle",
    "WorkspaceItem",
    "WorkspaceReceipt",
    "WorkspaceRejection",
    "WorkspaceSnapshot",
]
