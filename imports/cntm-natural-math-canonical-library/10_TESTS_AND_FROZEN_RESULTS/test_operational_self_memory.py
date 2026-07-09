"""Operational Self + Fractal Attractor Memory v0.1 tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.operational_self.compression import light_compress
from fractalish_ai.operational_self.continuity_spine import OperationalSelfEngine
from fractalish_ai.operational_self.decay import apply_decay
from fractalish_ai.operational_self.models import DEFAULT_NON_CLAIMS, MemoryEvent
from fractalish_ai.operational_self.memory_ingestion import ingest_file

SAMPLES = ROOT / "operational_self" / "samples"


@pytest.fixture
def engine(tmp_path: Path) -> OperationalSelfEngine:
    return OperationalSelfEngine(output_root=tmp_path)


def _ingest_all(eng: OperationalSelfEngine) -> None:
    for p in SAMPLES.rglob("*.json"):
        eng.ingest_bundle(p)


def test_memory_event_ingestion(engine: OperationalSelfEngine) -> None:
    _, events = ingest_file(SAMPLES / "session_events" / "fractalish_build_session.json")
    assert len(events) >= 5
    engine.ingest_session(SAMPLES / "session_events" / "fractalish_build_session.json")
    assert len(engine.events) >= 5


def test_light_compression_preserves_claims() -> None:
    event = MemoryEvent(
        event_id="e1", activation_id="a1", source_type="mock_event", source_id="s1",
        timestamp="2026-01-01", raw_summary="Test. Test.",
        claims=["HOLD remains sacred", "Pressure is not truth"],
    )
    mem = light_compress(event)
    assert "HOLD remains sacred" in mem.retained_claims


def test_light_compression_preserves_holds() -> None:
    event = MemoryEvent(
        event_id="e2", activation_id="a1", source_type="guardian_intake", source_id="g1",
        timestamp="2026-01-01", raw_summary="HOLD unresolved intake.",
        claims=["Unresolved HOLD on prompt injection"], guard_status="HOLD",
    )
    mem = light_compress(event)
    assert mem.retained_open_loops or "HOLD" in " ".join(mem.retained_claims + mem.retained_decisions)


def test_light_compression_preserves_contradiction_scars() -> None:
    event = MemoryEvent(
        event_id="e3", activation_id="a1", source_type="mock_event", source_id="s1",
        timestamp="2026-01-01", raw_summary="Similarity is not identity.",
        claims=["Similarity is not identity", "Similarity means identity"],
    )
    mem = light_compress(event)
    assert mem.retained_scars or any("similarity" in c.lower() for c in mem.retained_claims)


def test_light_compression_preserves_operator_constraints() -> None:
    event = MemoryEvent(
        event_id="e4", activation_id="a1", source_type="operator_note", source_id="op1",
        timestamp="2026-01-01", raw_summary="Operator constraint note.",
        provenance={"operator_constraints": ["operator_sovereignty", "local_only"]},
        operator_notes="operator_sovereignty",
    )
    mem = light_compress(event)
    assert "operator_sovereignty" in mem.retained_constraints


def test_core_doctrine_moves_toward_center(engine: OperationalSelfEngine) -> None:
    engine.ingest_session(SAMPLES / "session_events" / "fractalish_build_session.json")
    doctrine = [a for a in engine.attractors.values() if "doctrine" in a.tags]
    assert doctrine
    assert any(a.basin_region in ("core", "active") for a in doctrine)


def test_low_salience_memory_moves_outward(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    low = [a for a in engine.attractors.values() if a.salience_score < 0.4 and "doctrine" not in a.tags]
    if low:
        before = low[0].distance_from_reasoning_center
        apply_decay({a.attractor_id: a for a in low[:1]}, steps=2)
        assert low[0].distance_from_reasoning_center >= before


def test_contradiction_becomes_scar(engine: OperationalSelfEngine) -> None:
    engine.ingest_session(SAMPLES / "session_events" / "fractalish_build_session.json")
    assert engine.scars


def test_unresolved_claim_becomes_fog_region(engine: OperationalSelfEngine) -> None:
    engine.ingest_guardian(SAMPLES / "guardian_events" / "guardian_intake_summary.json")
    assert engine.fog_regions


def test_replay_route_created_for_resume_product_build(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    route = engine.replay_route("resume product build")
    assert route.get("memory_path")
    assert len(route["memory_path"]) >= 3


def test_pressure_is_not_truth_retrieves_core_doctrine(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    result = engine.retrieve_query("pressure is not truth")
    assert result["results"]
    top = result["results"][0]
    assert top["basin_region"] in ("core", "active", "near", "scar")


def test_similarity_is_not_identity_warns_or_holds(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    result = engine.retrieve_query("similarity means identity")
    assert result["results"]
    assert any(r.get("guard_status") == "HOLD" or r.get("warnings") for r in result["results"])


def test_guardian_intake_memory_preserves_lifecycle(engine: OperationalSelfEngine) -> None:
    engine.ingest_guardian(SAMPLES / "guardian_events" / "guardian_intake_summary.json")
    guardian_events = [e for e in engine.events if e.source_type == "guardian_intake"]
    assert any("lifecycle_state" in e.provenance for e in guardian_events)


def test_authority_memory_preserves_scope_jurisdiction_version(engine: OperationalSelfEngine) -> None:
    engine.ingest_authority(SAMPLES / "authority_events" / "authority_claim_summary.json")
    auth = [e for e in engine.events if e.source_type == "guardian_authority"]
    assert any(all(k in e.provenance for k in ("scope", "jurisdiction", "version")) for e in auth)


def test_session_glyph_update_created(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    engine._persist()
    path = engine.output_root / "session_glyph_update.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("activation_id")
    assert data.get("state_hash")


def test_operational_self_snapshot_created(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    path = engine.output_root / "operational_self_snapshot.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("state_hash")
    assert data.get("memory_counts", {}).get("memories", 0) > 0


def test_non_claims_include_no_consciousness_or_sentience_claim(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    for claim in DEFAULT_NON_CLAIMS:
        assert claim in engine.self_state.non_claims


def test_operational_self_uses_self_term_without_personhood_claim(engine: OperationalSelfEngine) -> None:
    engine.ingest_bundle(SAMPLES / "chat_turns" / "operational_self_discussion.json")
    text = (engine.self_state.active_narrative + (engine.narrative_frame.current_identity_sentence if engine.narrative_frame else "")).lower()
    assert "operational self" in text or "self" in text
    assert "no legal personhood claim" in engine.self_state.non_claims


def test_decay_keeps_core_doctrines_discoverable(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    core_before = [a for a in engine.attractors.values() if "doctrine" in a.tags and a.basin_region in ("core", "active")]
    engine.decay_demo()
    core_after = [a for a in engine.attractors.values() if "doctrine" in a.tags and a.basin_region in ("core", "active", "near")]
    assert len(core_after) >= len(core_before)


def test_decay_keeps_contradiction_scars_discoverable(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    engine.decay_demo()
    assert engine.scars


def test_purge_demo_does_not_purge_core_doctrine(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    core_ids = {a.memory_id for a in engine.attractors.values() if "doctrine" in a.tags}
    engine.purge_demo()
    remaining = {a.memory_id for a in engine.attractors.values() if a.basin_region != "purged"}
    assert core_ids & remaining


def test_dashboard_summary_created(engine: OperationalSelfEngine) -> None:
    engine.run_demo(samples_root=SAMPLES)
    path = engine.output_root / "dashboard_summary.json"
    assert path.exists()
    assert "operational_self_state" in json.loads(path.read_text(encoding="utf-8"))


def test_fractal_memory_map_compatible_snapshot_created(engine: OperationalSelfEngine) -> None:
    _ingest_all(engine)
    path = engine.output_root / "fractal_memory_map_snapshot.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "nodes" in data and "links" in data


def test_existing_guardian_intake_tests_still_pass() -> None:
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_guardian_intake_gateway.py", "-q"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_existing_guardian_authority_tests_still_pass() -> None:
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_guardian_authority_corpus.py", "-q"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_existing_cognitive_basin_sim_tests_still_pass() -> None:
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_cognitive_basin_sim_v1.py", "-q"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr