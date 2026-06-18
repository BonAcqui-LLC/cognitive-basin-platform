"""
Stabilization, HOLD fog, FractalMemoryMap, and TeamNarrative tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ternary.states import ActionState, EpistemicState
from python.basinlab.hold import HoldFogRecord, HoldFogTracker
from python.basinlab.memory_map import FractalMemoryMap, MemoryNode
from python.cognitive_basin.memory import MemoryEvidenceLink, MemoryFragment, MemoryPurposeLink
from python.cognitive_basin.privacy import RetentionClass, SensitivityLevel, VisibilityScope
from python.basinlab.stabilization import StabilizationEvidence, assess_stabilization
from python.basinlab.team_narrative import NarrativeRecord, TeamNarrative


def test_false_attractor_rejection_and_partial_stabilization():
    result = assess_stabilization(
        converged=True,
        contradictory_signals=["scan mismatch"],
        attractor_strength=0.95,
        evidence=[StabilizationEvidence("e1", "contradiction survives", supports_stability=False)],
    )
    assert result.false_attractor_detected is True
    assert result.partial is True
    assert result.stable is False


def test_hold_fog_persists_until_required_evidence_arrives():
    tracker = HoldFogTracker()
    record = tracker.enter(
        HoldFogRecord(
            reason="contradictory tool output",
            affected_circuit="planning",
            blocked_actions=["commit"],
            permitted_actions=["inspect"],
            required_evidence=["trace-1"],
            review_condition="human or replay review",
            expiry_condition="evidence accepted",
            recovery_path="inspect then replay",
        )
    )
    assert tracker.release(0, []) is False
    assert record.released is False
    assert tracker.release(0, ["trace-1"]) is True
    assert record.released is True


def test_memory_promotion_and_auditable_pruning():
    memory_map = FractalMemoryMap()
    node = MemoryNode(
        memory_id="m1",
        origin_session_id="session-1",
        origin_event_id="event-1",
        participant="UNKNOWN",
        purpose="routing",
        content_hash="hash-m1",
        provenance="local",
        evidence_status="supported",
        epistemic_state=EpistemicState.SUPPORTED,
        action_state=ActionState.EXTEND,
        sensitivity=SensitivityLevel.MODERATE,
        visibility_scope=VisibilityScope.SHARED_PROJECT,
        retention_class=RetentionClass.SHARED_WORKING,
        survival_reason="successful response",
        memory_fragments=[MemoryFragment("fragment-1", "routing detail", "hash-fragment", "local")],
        purpose_links=[MemoryPurposeLink("routing", provenance="test")],
        evidence_links=[MemoryEvidenceLink("report-1", "inspection report", provenance="test")],
        successful_uses=["kept"],
    )
    memory_map.upsert(node)
    memory_map.prune("m1", "low retention weight")
    assert memory_map.nodes["m1"].pruning_history[-1].reason == "low retention weight"
    assert memory_map.events[-1]["type"] == "memory_pruned"


def test_team_narrative_replay_ready_continuity_records():
    narrative = TeamNarrative()
    narrative.update(
        NarrativeRecord(
            person="James Clow",
            contributions=["Basin architecture"],
            decisions=["Preserve contradiction state"],
            superseded_decisions=["Old package ambiguity"],
            unresolved_questions=["How far to automate provider isolation?"],
        )
    )
    narrative.update(
        NarrativeRecord(
            person="Melissa Clow",
            contributions=["Governance framing"],
            conflicts=["Release vs private tranche scope"],
            recovery_history=["Re-centered implementation authority"],
        )
    )
    assert set(narrative.records) == {"James Clow", "Melissa Clow"}
    assert len(narrative.events) == 2
