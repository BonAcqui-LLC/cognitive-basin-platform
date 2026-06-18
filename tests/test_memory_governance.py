"""
Governed memory and multi-user continuity tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ternary.states import ActionState, EpistemicState
from python.cognitive_basin.memory import (
    FractalMemoryMap,
    MemoryEvidenceLink,
    MemoryFragment,
    MemoryItem,
    MemoryPurposeLink,
)
from python.cognitive_basin.privacy import RetentionClass, SensitivityLevel, VisibilityScope
from python.cognitive_basin.team_narrative import NarrativeRecord, TeamNarrative


def _memory(memory_id: str, purpose: str, *, participant: str = "UNKNOWN", contradiction_status: str = "none") -> MemoryItem:
    return MemoryItem(
        memory_id=memory_id,
        origin_session_id="s-1",
        origin_event_id=f"e-{memory_id}",
        participant=participant,
        purpose=purpose,
        content_hash=f"hash-{memory_id}",
        provenance="human-local-review",
        evidence_status="supported",
        epistemic_state=EpistemicState.SUPPORTED,
        action_state=ActionState.EXTEND,
        sensitivity=SensitivityLevel.MODERATE,
        visibility_scope=VisibilityScope.SHARED_PROJECT,
        retention_class=RetentionClass.SHARED_WORKING,
        survival_reason="useful in prior verified work",
        contradiction_status=contradiction_status,
        memory_fragments=[MemoryFragment(f"fragment-{memory_id}", f"text-{memory_id}", f"hash-fragment-{memory_id}", "local")],
        purpose_links=[MemoryPurposeLink(purpose, relevance=1.0, provenance="test")],
        evidence_links=[MemoryEvidenceLink(f"evidence-{memory_id}", f"detail-{memory_id}", provenance="test")],
        replay_references=["replay-s-1"],
    )


def test_memory_retrieval_prefers_verified_replay_relevant_items():
    memory_map = FractalMemoryMap()
    strong = memory_map.upsert(_memory("m-strong", "routing"))
    weak = memory_map.upsert(_memory("m-weak", "routing", contradiction_status="contradicted"))
    memory_map.record_use(strong.memory_id, successful=True, note="verified-route")
    memory_map.record_use(strong.memory_id, successful=True, note="replayed-route")
    memory_map.record_use(weak.memory_id, successful=False, note="contradicted-route")

    retrievals = memory_map.retrieve("routing")
    assert retrievals[0].memory_id == "m-strong"
    assert retrievals[0].verified_usefulness > retrievals[1].verified_usefulness
    assert retrievals[1].contradiction_penalty > 0


def test_memory_replay_and_pruning_stay_auditable():
    memory_map = FractalMemoryMap()
    stored = memory_map.upsert(_memory("m-prune", "audit"))
    memory_map.prune(stored.memory_id, "retention window expired")

    replayed = FractalMemoryMap.from_records(memory_map.export_records())
    assert replayed.items["m-prune"].pruned is True
    assert replayed.items["m-prune"].pruning_history[-1].reason == "retention window expired"


def test_team_narrative_keeps_people_separate_and_unknown_explicit():
    narrative = TeamNarrative()
    narrative.update(NarrativeRecord(person="James Clow", contributions=["Architecture"]))
    narrative.update(NarrativeRecord(person="Melissa Clow", contributions=["Governance"]))
    narrative.update(NarrativeRecord(person="", conflicts=["Actor unspecified"]))

    records = narrative.to_records()
    participants = {record["participant_id"] for record in records}
    assert participants == {"James Clow", "Melissa Clow", "UNKNOWN"}
    assert next(record for record in records if record["participant_id"] == "UNKNOWN")["explicit_identity"] is False
