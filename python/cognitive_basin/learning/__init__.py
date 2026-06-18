"""
Bounded adaptive policy learning with rollback.
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


IMMUTABLE_LEARNING_TARGETS = {
    "truth_definitions",
    "authority_boundaries",
    "audit_requirements",
    "participant_identity",
    "security_rules",
    "commit_gate_requirements",
}


@dataclass
class LearningSignal:
    detail: str
    strength: float

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail, "strength": self.strength}


@dataclass
class LearningExample:
    example_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"example_id": self.example_id, "detail": self.detail}


@dataclass
class LearningObjective:
    objective_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"objective_id": self.objective_id, "detail": self.detail}


@dataclass
class PolicyCandidate:
    candidate_id: str
    domain: str
    parameter: str
    prior_value: float
    proposed_value: float
    rationale: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "domain": self.domain,
            "parameter": self.parameter,
            "prior_value": self.prior_value,
            "proposed_value": self.proposed_value,
            "rationale": self.rationale,
        }


@dataclass
class PolicyEvaluation:
    candidate_id: str
    accepted: bool
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"candidate_id": self.candidate_id, "accepted": self.accepted, "detail": self.detail}


@dataclass
class PolicyUpdate:
    version: int
    domain: str
    parameter: str
    value: float
    evidence: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "domain": self.domain,
            "parameter": self.parameter,
            "value": self.value,
            "evidence": list(self.evidence),
        }


@dataclass
class PolicyRollback:
    version: int
    domain: str
    parameter: str
    restored_value: float
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "domain": self.domain,
            "parameter": self.parameter,
            "restored_value": self.restored_value,
            "reason": self.reason,
        }


@dataclass
class LearningReceipt:
    candidates: List[PolicyCandidate]
    evaluations: List[PolicyEvaluation]
    updates: List[PolicyUpdate]
    rollbacks: List[PolicyRollback]

    def to_record(self) -> Dict[str, Any]:
        return {
            "candidates": _record(self.candidates),
            "evaluations": _record(self.evaluations),
            "updates": _record(self.updates),
            "rollbacks": _record(self.rollbacks),
        }


class LearningManager:
    def __init__(self) -> None:
        self.policy_state: Dict[str, Dict[str, float]] = {}
        self.version = 0
        self.updates: List[PolicyUpdate] = []
        self.rollbacks: List[PolicyRollback] = []

    def candidate(self, *, domain: str, parameter: str, prior_value: float, proposed_value: float, rationale: str) -> PolicyCandidate:
        return PolicyCandidate(
            candidate_id=f"policy-candidate-{self.version + 1:04d}",
            domain=domain,
            parameter=parameter,
            prior_value=prior_value,
            proposed_value=proposed_value,
            rationale=rationale,
        )

    def evaluate(self, candidate: PolicyCandidate, *, evidence: List[str]) -> PolicyEvaluation:
        if candidate.domain in IMMUTABLE_LEARNING_TARGETS or candidate.parameter in IMMUTABLE_LEARNING_TARGETS:
            return PolicyEvaluation(candidate.candidate_id, False, "immutable learning target")
        if not evidence:
            return PolicyEvaluation(candidate.candidate_id, False, "missing evidence")
        return PolicyEvaluation(candidate.candidate_id, True, "bounded update accepted")

    def apply(self, candidate: PolicyCandidate, *, evidence: List[str]) -> PolicyUpdate:
        evaluation = self.evaluate(candidate, evidence=evidence)
        if not evaluation.accepted:
            raise ValueError(evaluation.detail)
        self.version += 1
        self.policy_state.setdefault(candidate.domain, {})[candidate.parameter] = candidate.proposed_value
        update = PolicyUpdate(self.version, candidate.domain, candidate.parameter, candidate.proposed_value, evidence)
        self.updates.append(update)
        return update

    def rollback(self, domain: str, parameter: str, restored_value: float, reason: str) -> PolicyRollback:
        self.policy_state.setdefault(domain, {})[parameter] = restored_value
        rollback = PolicyRollback(self.version, domain, parameter, restored_value, reason)
        self.rollbacks.append(rollback)
        return rollback

    def receipt(self, candidates: List[PolicyCandidate], evaluations: List[PolicyEvaluation]) -> LearningReceipt:
        return LearningReceipt(candidates, evaluations, list(self.updates), list(self.rollbacks))


__all__ = [
    "IMMUTABLE_LEARNING_TARGETS",
    "LearningExample",
    "LearningManager",
    "LearningObjective",
    "LearningReceipt",
    "LearningSignal",
    "PolicyCandidate",
    "PolicyEvaluation",
    "PolicyRollback",
    "PolicyUpdate",
]
