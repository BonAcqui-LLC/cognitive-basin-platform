"""
Governed attention contracts and bounded selection logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..common import stable_hash
from ..workspace import WorkspaceItem


@dataclass
class AttentionTarget:
    target_id: str
    label: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"target_id": self.target_id, "label": self.label, "reason": self.reason}


@dataclass
class AttentionWeight:
    target_id: str
    salience: float
    relevance: float
    urgency: float
    evidence_quality: float
    contradiction_pressure: float
    purpose_alignment: float
    actionability: float
    novelty: float
    total: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "salience": self.salience,
            "relevance": self.relevance,
            "urgency": self.urgency,
            "evidence_quality": self.evidence_quality,
            "contradiction_pressure": self.contradiction_pressure,
            "purpose_alignment": self.purpose_alignment,
            "actionability": self.actionability,
            "novelty": self.novelty,
            "total": self.total,
        }


@dataclass
class AttentionPolicy:
    max_targets: int = 2
    allow_lock: bool = True
    stale_fixation_cycles: int = 3

    def to_record(self) -> Dict[str, Any]:
        return {
            "max_targets": self.max_targets,
            "allow_lock": self.allow_lock,
            "stale_fixation_cycles": self.stale_fixation_cycles,
        }


@dataclass
class AttentionShift:
    from_target_id: str
    to_target_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"from_target_id": self.from_target_id, "to_target_id": self.to_target_id, "reason": self.reason}


@dataclass
class AttentionLock:
    target_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"target_id": self.target_id, "reason": self.reason}


@dataclass
class AttentionRelease:
    target_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"target_id": self.target_id, "reason": self.reason}


@dataclass
class AttentionConflict:
    conflict_type: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"conflict_type": self.conflict_type, "detail": self.detail}


@dataclass
class AttentionBudget:
    max_focus_items: int = 2
    max_switches_per_cycle_window: int = 3

    def to_record(self) -> Dict[str, Any]:
        return {
            "max_focus_items": self.max_focus_items,
            "max_switches_per_cycle_window": self.max_switches_per_cycle_window,
        }


@dataclass
class AttentionHistory:
    focus_ids: List[str] = field(default_factory=list)
    shifts: List[AttentionShift] = field(default_factory=list)
    states: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "focus_ids": list(self.focus_ids),
            "shifts": [item.to_record() for item in self.shifts],
            "states": list(self.states),
        }


@dataclass
class AttentionReceipt:
    focus: List[AttentionTarget]
    weights: List[AttentionWeight]
    conflicts: List[AttentionConflict]
    locks: List[AttentionLock]
    releases: List[AttentionRelease]
    state: str
    history: AttentionHistory

    def to_record(self) -> Dict[str, Any]:
        return {
            "focus": [item.to_record() for item in self.focus],
            "weights": [item.to_record() for item in self.weights],
            "conflicts": [item.to_record() for item in self.conflicts],
            "locks": [item.to_record() for item in self.locks],
            "releases": [item.to_record() for item in self.releases],
            "state": self.state,
            "history": self.history.to_record(),
        }


class AttentionSystem:
    def __init__(self, policy: AttentionPolicy | None = None, budget: AttentionBudget | None = None) -> None:
        self.policy = policy or AttentionPolicy()
        self.budget = budget or AttentionBudget()
        self.history = AttentionHistory()
        self._lock_target_id = ""

    def set_lock(self, target_id: str, reason: str = "manual") -> None:
        self._lock_target_id = target_id
        self.history.states.append(f"lock:{target_id}:{reason}")

    def select(self, items: List[WorkspaceItem], *, active_purpose: str, cycle_index: int) -> AttentionReceipt:
        weights: List[AttentionWeight] = []
        conflicts: List[AttentionConflict] = []
        locks: List[AttentionLock] = []
        releases: List[AttentionRelease] = []
        for item in items:
            purpose_alignment = item.purpose_relevance
            total = (
                item.salience * 0.7
                + item.purpose_relevance * 1.5
                + item.urgency * 1.0
                + item.evidence_quality * 1.2
                + item.contradiction_pressure * 1.1
                + purpose_alignment * 1.2
                + item.actionability * 0.8
                + item.novelty * 0.4
            )
            weights.append(
                AttentionWeight(
                    target_id=item.item_id,
                    salience=item.salience,
                    relevance=item.purpose_relevance,
                    urgency=item.urgency,
                    evidence_quality=item.evidence_quality,
                    contradiction_pressure=item.contradiction_pressure,
                    purpose_alignment=purpose_alignment,
                    actionability=item.actionability,
                    novelty=item.novelty,
                    total=round(total, 4),
                )
            )
        ordered = sorted(weights, key=lambda item: item.total, reverse=True)
        selected = ordered[: self.budget.max_focus_items]
        if self._lock_target_id and any(item.target_id == self._lock_target_id for item in ordered):
            selected = [item for item in ordered if item.target_id == self._lock_target_id][:1] + [
                item for item in selected if item.target_id != self._lock_target_id
            ]
            locks.append(AttentionLock(self._lock_target_id, "retained lock"))
        if ordered:
            highest_salience = max(items, key=lambda item: item.salience)
            if highest_salience.item_id != selected[0].target_id and highest_salience.salience > 0.8:
                conflicts.append(AttentionConflict("salient_distractor", f"{highest_salience.item_id} lost to relevance"))
        focus = [
            AttentionTarget(item.target_id, next((workspace.title for workspace in items if workspace.item_id == item.target_id), item.target_id), active_purpose)
            for item in selected
        ]
        previous_focus = self.history.focus_ids[-1] if self.history.focus_ids else ""
        state = "stable"
        if len(set(self.history.focus_ids[-3:] + [focus[0].target_id] if focus else self.history.focus_ids[-3:])) >= self.budget.max_switches_per_cycle_window:
            conflicts.append(AttentionConflict("excessive_context_switching", "Focus changed too frequently"))
            state = "unstable"
        if previous_focus and focus and previous_focus == focus[0].target_id:
            recent_repeat = self.history.focus_ids[-self.policy.stale_fixation_cycles :]
            if len(recent_repeat) >= self.policy.stale_fixation_cycles and all(item == previous_focus for item in recent_repeat):
                conflicts.append(AttentionConflict("stale_fixation", f"{previous_focus} repeated without shift"))
                state = "captured"
        if len({next((workspace.source_ids[0] for workspace in items if workspace.item_id == item.target_id), "") for item in selected}) == 1 and len(selected) > 1:
            conflicts.append(AttentionConflict("source_monopolization", "All focus comes from one source"))
        if any(item.contradiction_pressure > 0.7 for item in items) and not any(
            item.target_id in {focus_item.target_id for focus_item in focus} and item.contradiction_pressure > 0.7 for item in weights
        ):
            conflicts.append(AttentionConflict("contradiction_avoidance", "Contradictory item not selected"))
            state = "captured"
        if previous_focus and focus and previous_focus != focus[0].target_id:
            self.history.shifts.append(AttentionShift(previous_focus, focus[0].target_id, "competition"))
        self.history.focus_ids.extend(item.target_id for item in focus)
        self.history.states.append(state)
        return AttentionReceipt(
            focus=focus,
            weights=weights,
            conflicts=conflicts,
            locks=locks,
            releases=releases,
            state=state,
            history=self.history,
        )


__all__ = [
    "AttentionBudget",
    "AttentionConflict",
    "AttentionHistory",
    "AttentionLock",
    "AttentionPolicy",
    "AttentionReceipt",
    "AttentionRelease",
    "AttentionShift",
    "AttentionSystem",
    "AttentionTarget",
    "AttentionWeight",
]
