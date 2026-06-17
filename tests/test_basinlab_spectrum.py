"""
Candidate spectrum and claim-reliability tests for BasinLab.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ternary.states import ActionState, EpistemicState
from python.basinlab.providers import CompactReasonerProvider, GeneralistProvider, ScriptedProvider
from python.basinlab.reliability import DecisionClaim, ReliabilityEngine, minority_wins_demo
from python.basinlab.spectrum import (
    CandidateAssumption,
    CandidateGenerator,
    CandidatePrediction,
    CandidateTrajectory,
)


def _deterministic_strategy(_purpose, _context):
    return [
        CandidateTrajectory(
            "det-1",
            "blue route",
            "Follow the river corridor",
            "hydrology-first",
            "deterministic",
            assumptions=[CandidateAssumption("Water access matters", "strategy")],
            predictions=[CandidatePrediction("Expect river adjacency", ["map"])],
        ),
        CandidateTrajectory(
            "det-2",
            "blue route",
            "Follow the ridge line",
            "ridge-first",
            "deterministic",
            assumptions=[CandidateAssumption("Elevation matters", "strategy")],
            predictions=[CandidatePrediction("Expect line-of-sight", ["terrain"])],
        ),
        CandidateTrajectory(
            "det-3",
            "green route",
            "Use the valley floor",
            "valley-first",
            "deterministic",
        ),
    ]


def test_three_different_approaches_remain_distinct():
    spectrum = CandidateGenerator(deterministic_strategies=[_deterministic_strategy]).generate("route", {})
    retained_ids = {candidate.trajectory_id for candidate in spectrum.retained}
    assert retained_ids == {"det-1", "det-2", "det-3"}


def test_paraphrases_deduplicate():
    provider = ScriptedProvider(
        name="scripted",
        scripted_outputs=[
            {
                "trajectory_id": "p1",
                "answer": "Five",
                "reasoning": "The answer is five",
                "approach": "direct arithmetic",
            },
            {
                "trajectory_id": "p2",
                "answer": "5",
                "reasoning": "Answer equals five",
                "approach": "direct arithmetic",
            },
        ],
    )
    spectrum = CandidateGenerator(providers=[provider]).generate("math", {})
    assert len(spectrum.retained) == 1
    assert len(spectrum.merged) == 1
    assert spectrum.merged[0].trajectory_id == "p2"


def test_rejected_candidates_remain_auditable():
    provider = ScriptedProvider(
        name="scripted",
        scripted_outputs=[
            {
                "trajectory_id": "bad",
                "answer": "",
                "reasoning": "No usable answer",
                "approach": "broken",
            }
        ],
    )
    spectrum = CandidateGenerator(providers=[provider]).generate("audit", {})
    assert spectrum.retained == []
    assert len(spectrum.rejected) == 1
    assert "empty" in spectrum.rejected[0].reason.lower()


def test_majority_count_does_not_determine_truth():
    decision = minority_wins_demo()
    assert decision.final_epistemic == EpistemicState.SUPPORTED
    assert decision.final_action == ActionState.EXTEND
    assert decision.winning_answer == "5"
    assert decision.winning_trajectory_id == "minority-1"


def test_candidate_ordering_does_not_change_verified_result():
    candidates_a = [
        CandidateTrajectory("a", "4", "wrong", "fast", "scripted"),
        CandidateTrajectory("b", "5", "right", "checked", "scripted"),
    ]
    candidates_b = list(reversed(candidates_a))
    claims = {
        "a": [
            DecisionClaim(
                "claim-a",
                "2 plus 3 equals 4",
                "a",
                critical=True,
                required_evidence=["math"],
                contradictory_evidence=["eval says 5"],
            )
        ],
        "b": [
            DecisionClaim(
                "claim-b",
                "2 plus 3 equals 5",
                "b",
                critical=True,
                required_evidence=["math"],
                supporting_evidence=["eval says 5"],
            )
        ],
    }
    engine = ReliabilityEngine()
    first = engine.evaluate(candidates_a, claims)
    second = engine.evaluate(candidates_b, claims)
    assert first.winning_trajectory_id == second.winning_trajectory_id == "b"
    assert first.final_epistemic == second.final_epistemic == EpistemicState.SUPPORTED


def test_unresolved_critical_claim_forces_hold():
    engine = ReliabilityEngine()
    candidate = CandidateTrajectory("u1", "pending", "needs proof", "careful", "scripted")
    claims = {
        "u1": [
            DecisionClaim(
                "claim-u1",
                "The bridge is safe",
                "u1",
                critical=True,
                required_evidence=["inspection"],
            )
        ]
    }
    decision = engine.evaluate([candidate], claims)
    assert decision.final_epistemic == EpistemicState.UNRESOLVED
    assert decision.final_action == ActionState.HOLD


def test_supported_noncritical_claim_cannot_rescue_contradicted_conclusion():
    engine = ReliabilityEngine()
    candidate = CandidateTrajectory("mix", "unsafe", "mixed evidence", "inspection", "scripted")
    claims = {
        "mix": [
            DecisionClaim(
                "critical",
                "The support beam is intact",
                "mix",
                critical=True,
                contradictory_evidence=["fracture scan"],
            ),
            DecisionClaim(
                "noncritical",
                "The paint looks new",
                "mix",
                critical=False,
                supporting_evidence=["photo review"],
            ),
        ]
    }
    decision = engine.evaluate([candidate], claims)
    assert decision.final_epistemic == EpistemicState.CONTRADICTED
    assert decision.final_action == ActionState.RETRACT


def test_provider_isolation_flags_are_enforced():
    compact = CompactReasonerProvider(scripted_outputs=[{"answer": "x", "reasoning": "r", "approach": "a"}])
    generalist = GeneralistProvider(scripted_outputs=[{"answer": "y", "reasoning": "r", "approach": "a"}])
    assert compact.can_execute is False
    assert compact.can_commit is False
    assert generalist.can_execute is False
    assert generalist.can_commit is False
