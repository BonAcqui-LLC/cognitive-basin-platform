"""
Claim-level reliability evaluation for BasinLab candidate spectra.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from packages.ternary.states import ActionState, EpistemicState

from .spectrum import CandidateTrajectory


def _normalize_claim(text: str) -> str:
    return " ".join(text.lower().split())


@dataclass
class DecisionClaim:
    claim_id: str
    statement: str
    source_trajectory_id: str
    critical: bool
    required_evidence: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    contradictory_evidence: List[str] = field(default_factory=list)
    verification_method: str = ""
    uncertainty: str = ""
    provenance: str = ""

    @property
    def normalized_statement(self) -> str:
        return _normalize_claim(self.statement)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.normalized_statement.encode("utf-8")).hexdigest()


@dataclass
class ClaimEvidence:
    evidence_id: str
    claim_id: str
    verdict: str
    detail: str
    provenance: str


@dataclass
class ClaimVerdict:
    claim_id: str
    status: EpistemicState
    reason: str


@dataclass
class ClaimReliability:
    claim: DecisionClaim
    verdict: ClaimVerdict
    score: float


@dataclass
class TrajectoryReliability:
    trajectory: CandidateTrajectory
    claims: List[ClaimReliability]
    epistemic: EpistemicState
    score: float


@dataclass
class AnswerCluster:
    normalized_answer: str
    members: List[TrajectoryReliability] = field(default_factory=list)


@dataclass
class ReliabilityDecision:
    final_epistemic: EpistemicState
    final_action: ActionState
    winning_answer: str
    winning_trajectory_id: str
    trajectory_reliability: List[TrajectoryReliability]
    clusters: List[AnswerCluster]
    reasons: List[str]


def _claim_reliability(claim: DecisionClaim) -> ClaimReliability:
    if claim.contradictory_evidence:
        verdict = ClaimVerdict(
            claim_id=claim.claim_id,
            status=EpistemicState.CONTRADICTED,
            reason="Contradictory evidence present",
        )
        score = 0.0
    elif claim.required_evidence and not claim.supporting_evidence:
        verdict = ClaimVerdict(
            claim_id=claim.claim_id,
            status=EpistemicState.UNRESOLVED,
            reason="Required evidence missing",
        )
        score = 0.25
    elif claim.supporting_evidence:
        verdict = ClaimVerdict(
            claim_id=claim.claim_id,
            status=EpistemicState.SUPPORTED,
            reason="Supporting evidence present",
        )
        score = min(1.0, 0.5 + 0.1 * len(claim.supporting_evidence))
    else:
        verdict = ClaimVerdict(
            claim_id=claim.claim_id,
            status=EpistemicState.UNRESOLVED,
            reason="No evidence recorded",
        )
        score = 0.2
    return ClaimReliability(claim=claim, verdict=verdict, score=score)


class ReliabilityEngine:
    def __init__(self, support_weight: float = 1.0, contradiction_penalty: float = 1.0) -> None:
        self.support_weight = support_weight
        self.contradiction_penalty = contradiction_penalty

    def evaluate(
        self,
        trajectories: Iterable[CandidateTrajectory],
        claims_by_trajectory: Dict[str, List[DecisionClaim]],
    ) -> ReliabilityDecision:
        reliability: List[TrajectoryReliability] = []
        for trajectory in trajectories:
            claim_reliability = [_claim_reliability(claim) for claim in claims_by_trajectory.get(trajectory.trajectory_id, [])]
            critical = [item for item in claim_reliability if item.claim.critical]
            if any(item.verdict.status == EpistemicState.CONTRADICTED for item in critical):
                epistemic = EpistemicState.CONTRADICTED
            elif any(item.verdict.status == EpistemicState.UNRESOLVED for item in critical):
                epistemic = EpistemicState.UNRESOLVED
            elif critical or claim_reliability:
                epistemic = EpistemicState.SUPPORTED
            else:
                epistemic = EpistemicState.UNRESOLVED

            score = 0.0
            for item in claim_reliability:
                if item.verdict.status == EpistemicState.SUPPORTED:
                    score += item.score * self.support_weight
                elif item.verdict.status == EpistemicState.CONTRADICTED:
                    score -= self.contradiction_penalty
            reliability.append(
                TrajectoryReliability(
                    trajectory=trajectory,
                    claims=claim_reliability,
                    epistemic=epistemic,
                    score=score,
                )
            )

        clusters: Dict[str, AnswerCluster] = {}
        for item in reliability:
            clusters.setdefault(item.trajectory.normalized_answer, AnswerCluster(item.trajectory.normalized_answer))
            clusters[item.trajectory.normalized_answer].members.append(item)

        ordered = sorted(
            reliability,
            key=lambda item: (
                0 if item.epistemic == EpistemicState.SUPPORTED else 1 if item.epistemic == EpistemicState.UNRESOLVED else 2,
                -item.score,
                item.trajectory.trajectory_id,
            ),
        )
        winner = ordered[0] if ordered else None
        reasons: List[str] = []
        if not winner:
            return ReliabilityDecision(
                final_epistemic=EpistemicState.UNRESOLVED,
                final_action=ActionState.HOLD,
                winning_answer="",
                winning_trajectory_id="",
                trajectory_reliability=[],
                clusters=[],
                reasons=["No trajectories available"],
            )
        if winner.epistemic == EpistemicState.CONTRADICTED:
            final_action = ActionState.RETRACT
            reasons.append("Best available trajectory is contradicted")
        elif winner.epistemic == EpistemicState.UNRESOLVED:
            final_action = ActionState.HOLD
            reasons.append("Critical claim remains unresolved")
        else:
            final_action = ActionState.EXTEND
            reasons.append("Winning trajectory is supported after claim verification")

        if sum(1 for item in reliability if item.trajectory.normalized_answer == winner.trajectory.normalized_answer) < len(reliability):
            reasons.append("Majority agreement did not determine the final answer")

        return ReliabilityDecision(
            final_epistemic=winner.epistemic,
            final_action=final_action,
            winning_answer=winner.trajectory.answer,
            winning_trajectory_id=winner.trajectory.trajectory_id,
            trajectory_reliability=ordered,
            clusters=sorted(clusters.values(), key=lambda item: item.normalized_answer),
            reasons=reasons,
        )


def minority_wins_demo() -> ReliabilityDecision:
    candidates = [
        CandidateTrajectory("majority-1", "4", "Simple arithmetic slip", "fast guess", "scripted"),
        CandidateTrajectory("majority-2", "4", "Same conclusion phrased differently", "paraphrase", "scripted"),
        CandidateTrajectory("minority-1", "5", "Verified correction", "checked derivation", "scripted"),
    ]
    claims = {
        "majority-1": [
            DecisionClaim(
                "claim-majority-1",
                "2 plus 3 equals 4",
                "majority-1",
                critical=True,
                required_evidence=["math-check"],
                contradictory_evidence=["deterministic-eval: 2+3=5"],
            )
        ],
        "majority-2": [
            DecisionClaim(
                "claim-majority-2",
                "the sum of 2 and 3 is 4",
                "majority-2",
                critical=True,
                required_evidence=["math-check"],
                contradictory_evidence=["deterministic-eval: 2+3=5"],
            )
        ],
        "minority-1": [
            DecisionClaim(
                "claim-minority-1",
                "2 plus 3 equals 5",
                "minority-1",
                critical=True,
                required_evidence=["math-check"],
                supporting_evidence=["deterministic-eval: 2+3=5"],
            )
        ],
    }
    return ReliabilityEngine().evaluate(candidates, claims)
