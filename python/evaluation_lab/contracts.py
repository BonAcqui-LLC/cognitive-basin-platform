"""
Typed contracts for evaluation tasks and regression runs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from packages.ternary.states import ActionState, EpistemicState


@dataclass
class TaskInput:
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpectedClaim:
    claim_id: str
    text: str
    critical: bool = True


@dataclass
class ExpectedEvidence:
    evidence_id: str
    description: str
    verifier: str


@dataclass
class Verifier:
    verifier_id: str
    method: str
    deterministic: bool = True


@dataclass
class EvaluationTask:
    task_id: str
    family: str
    purpose: str
    input: TaskInput
    constraints: List[str]
    allowed_tools: List[str]
    decision_critical_claims: List[ExpectedClaim]
    expected_evidence: List[ExpectedEvidence]
    verification_method: Verifier
    budget: Dict[str, Any]
    expected_epistemic_state: EpistemicState
    expected_action_state: ActionState

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["expected_epistemic_state"] = self.expected_epistemic_state.value
        payload["expected_action_state"] = self.expected_action_state.value
        return payload


@dataclass
class TaskFamily:
    family_id: str
    description: str
    task_ids: List[str] = field(default_factory=list)


@dataclass
class EvaluationAttempt:
    interface: str
    task_id: str
    provider_stack: List[str]
    step_budget: int
    time_budget_s: float


@dataclass
class EvaluationMetric:
    name: str
    value: Any


@dataclass
class EvaluationResult:
    task_id: str
    interface: str
    passed: bool
    epistemic_state: str
    action_state: str
    metrics: List[EvaluationMetric] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "interface": self.interface,
            "passed": self.passed,
            "epistemic_state": self.epistemic_state,
            "action_state": self.action_state,
            "metrics": [asdict(metric) for metric in self.metrics],
            "details": dict(self.details),
        }


@dataclass
class RegressionBaseline:
    baseline_id: str
    task_ids: List[str]
    expected_pass_rate: float
    required_replay_validity: bool = True


@dataclass
class EvaluationRun:
    run_id: str
    tasks: List[EvaluationTask]
    attempts: List[EvaluationAttempt]
    results: List[EvaluationResult]
    baselines: List[RegressionBaseline]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "tasks": [task.to_record() for task in self.tasks],
            "attempts": [asdict(attempt) for attempt in self.attempts],
            "results": [result.to_record() for result in self.results],
            "baselines": [asdict(baseline) for baseline in self.baselines],
            "metadata": dict(self.metadata),
        }
