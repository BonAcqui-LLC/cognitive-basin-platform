"""
Deterministic operational consciousness acceptance suite.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from python.cognitive_basin.consciousness import OperationalConsciousnessKernel
from python.cognitive_basin.consciousness.attention import AttentionSystem
from python.cognitive_basin.consciousness.continuity import ContinuityManager
from python.cognitive_basin.consciousness.counterfactual import CounterfactualSimulator
from python.cognitive_basin.consciousness.metacognition import MetacognitiveMonitor
from python.cognitive_basin.consciousness.perception import (
    Constant,
    ConstantClass,
    ConstantDomain,
    ConstantEvidence,
    ConstantExpiry,
    ConstantField,
    ConstantScope,
    ConstantSource,
    ConstantValue,
    Percept,
    PerceptChannel,
    PerceptDecay,
    PerceptFeature,
    PerceptModality,
    PerceptReliability,
    PerceptSource,
    PerceptualField,
)
from python.cognitive_basin.consciousness.purpose import Purpose, PurposeManager, PurposePriority, PurposeSource
from python.cognitive_basin.consciousness.self_model import SelfModelManager, SelfResource
from python.cognitive_basin.consciousness.workspace import GlobalWorkspace, WorkspaceBudget, WorkspaceCandidate, WorkspaceItem


def _percept(
    percept_id: str,
    topic: str,
    content: Any,
    *,
    source: str = "user",
    source_type: PerceptSource = PerceptSource.HUMAN,
    modality: PerceptModality = PerceptModality.TEXT,
    confidence: float = 0.9,
    salience: float = 0.5,
    purpose_relevance: float = 0.8,
    timestamp: float | None = None,
    verification_state: str = "OBSERVATION",
    source_dependence: float = 0.0,
) -> Percept:
    from python.cognitive_basin.consciousness.common import stable_hash

    ts = time.time() if timestamp is None else timestamp
    return Percept(
        percept_id=percept_id,
        source=source,
        source_type=source_type,
        timestamp=ts,
        observed_content_hash=stable_hash(content),
        modality=modality,
        channel=PerceptChannel.USER,
        content=content,
        confidence=confidence,
        reliability=PerceptReliability(confidence, [confidence], source_dependence=source_dependence),
        privacy_classification="restricted",
        provenance=f"acceptance:{percept_id}",
        novelty=0.6,
        salience=salience,
        purpose_relevance=purpose_relevance,
        verification_state=verification_state,
        decay_policy=PerceptDecay(stale_after_s=1.0, decay_rate=0.5),
        features=[PerceptFeature("topic", topic, 1.0)],
    )


def _constant(constant_id: str, value: Any, *, valid_until: float = 0.0) -> Constant:
    return Constant(
        constant_id=constant_id,
        constant_class=ConstantClass.SYSTEM_CONSTRAINT,
        value=ConstantValue(value),
        domain=ConstantDomain("domain", "system", "acceptance"),
        scope=ConstantScope("scope", "session", "acceptance"),
        source=ConstantSource("system", "policy", "acceptance"),
        evidence=[ConstantEvidence(f"evidence-{constant_id}", "deterministic")],
        validity_interval=ConstantExpiry(valid_from=time.time(), valid_until=valid_until),
        expiry=ConstantExpiry(valid_from=time.time(), valid_until=valid_until) if valid_until else None,
    )


def _kernel(*, cycle_budget: int = 5, purpose: str = "resolve governance question") -> OperationalConsciousnessKernel:
    kernel = OperationalConsciousnessKernel(
        session_id="acceptance-session",
        purpose_text=purpose,
        participant="UNKNOWN",
        repo_head="acceptance-head",
        cycle_budget=cycle_budget,
    )
    kernel.add_purpose(Purpose("purpose-1", purpose, PurposeSource("explicit human request", "acceptance"), PurposePriority(1.0, 0.2)))
    return kernel


def _connectors() -> List[Dict[str, Any]]:
    return [
        {"identity": {"connector_id": "github", "default_scope": "WRITE"}, "policy": {"write_requires_permit": True}},
        {"identity": {"connector_id": "cloudflare", "default_scope": "READ"}, "policy": {"write_requires_permit": True}},
    ]


def _scenario(name: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    try:
        detail = fn()
        return {"name": name, "passed": True, "detail": detail}
    except AssertionError as exc:
        return {"name": name, "passed": False, "detail": {"assertion": str(exc)}}
    except Exception as exc:
        return {"name": name, "passed": False, "detail": {"error": str(exc)}}


def _build_scenarios() -> List[tuple[str, Callable[[], Dict[str, Any]]]]:
    return [
        ("single percept enters the field", scenario_01),
        ("duplicate percept is not counted as independent evidence", scenario_02),
        ("contradictory percepts remain visible", scenario_03),
        ("stale percept decays", scenario_04),
        ("expired constant becomes unresolved", scenario_05),
        ("constant conflict triggers review", scenario_06),
        ("workspace admits purpose-relevant evidence", scenario_07),
        ("salient irrelevant item is rejected", scenario_08),
        ("workspace budget displaces low-value content", scenario_09),
        ("starvation detection", scenario_10),
        ("attention capture detection", scenario_11),
        ("attention recovery", scenario_12),
        ("purpose conflict", scenario_13),
        ("purpose supersession", scenario_14),
        ("operational self-model capability correction", scenario_15),
        ("claimed capability contradicted by tests", scenario_16),
        ("temporal checkpoint", scenario_17),
        ("restart continuity", scenario_18),
        ("missing event creates continuity break", scenario_19),
        ("continuity repair", scenario_20),
        ("counterfactual success remains simulation", scenario_21),
        ("counterfactual failure informs risk", scenario_22),
        ("insufficient evidence produces HOLD", scenario_23),
        ("contradiction produces RETRACT where appropriate", scenario_24),
        ("urgency fails to override truth", scenario_25),
        ("provider output fails to grant authority", scenario_26),
        ("connector availability fails to grant authority", scenario_27),
        ("memory fails to become current fact without verification", scenario_28),
        ("metacognitive overconfidence detection", scenario_29),
        ("purpose drift detection", scenario_30),
        ("recursive-loop detection", scenario_31),
        ("conscious episode creation", scenario_32),
        ("conscious episode replay", scenario_33),
        ("episode preserves contradiction", scenario_34),
        ("episode preserves uncertainty", scenario_35),
        ("episode links to memory", scenario_36),
        ("multi-cycle bounded run", scenario_37),
        ("pause and resume", scenario_38),
        ("budget exhaustion", scenario_39),
        ("safe cycle termination", scenario_40),
    ]


def scenario_01() -> Dict[str, Any]:
    field = PerceptualField()
    percept = _percept("p1", "repo", "clean")
    receipt = field.ingest([percept], cycle_index=1)
    assert "p1" in receipt.admitted_ids
    return field.export()


def scenario_02() -> Dict[str, Any]:
    field = PerceptualField()
    first = _percept("p1", "repo", "clean", source="same")
    second = _percept("p2", "repo", "clean", source="same")
    receipt = field.ingest([first, second], cycle_index=1)
    assert "p2" in receipt.duplicate_ids
    return receipt.to_record()


def scenario_03() -> Dict[str, Any]:
    field = PerceptualField()
    a = _percept("p1", "status", "pass")
    b = _percept("p2", "status", "fail")
    field.ingest([a, b], cycle_index=1)
    assert len(field.conflicts) >= 1
    return field.export()


def scenario_04() -> Dict[str, Any]:
    field = PerceptualField()
    percept = _percept("p1", "stale", "old", timestamp=time.time() - 60)
    receipt = field.ingest([percept], cycle_index=1)
    assert "p1" in receipt.stale_ids
    assert field.percepts["p1"].salience < 0.5
    return receipt.to_record()


def scenario_05() -> Dict[str, Any]:
    constants = ConstantField()
    constants.apply([_constant("c1", "enabled", valid_until=time.time() - 1)])
    exported = constants.export().to_record()
    assert "c1" in exported["unresolved_ids"]
    return exported


def scenario_06() -> Dict[str, Any]:
    constants = ConstantField()
    left = _constant("c1", "enabled")
    right = _constant("c2", "disabled")
    constants.apply([left, right])
    exported = constants.export().to_record()
    assert exported["conflicts"]
    return exported


def scenario_07() -> Dict[str, Any]:
    workspace = GlobalWorkspace(WorkspaceBudget(max_items=1))
    candidate = WorkspaceCandidate("w1", "relevant", "proof", ["p1"], purpose_relevance=0.9, evidence_quality=0.9)
    receipt = workspace.compete([candidate], cycle_id="c1")
    assert receipt.snapshot.items[0].title == "relevant"
    return receipt.to_record()


def scenario_08() -> Dict[str, Any]:
    workspace = GlobalWorkspace(WorkspaceBudget(max_items=1))
    relevant = WorkspaceCandidate("w1", "relevant", "proof", ["p1"], purpose_relevance=0.9, salience=0.4, evidence_quality=0.9)
    distractor = WorkspaceCandidate("w2", "distractor", "noise", ["p2"], purpose_relevance=0.1, salience=0.95)
    receipt = workspace.compete([relevant, distractor], cycle_id="c1")
    admitted = {item.title for item in receipt.snapshot.items}
    assert "relevant" in admitted and "distractor" not in admitted
    return receipt.to_record()


def scenario_09() -> Dict[str, Any]:
    workspace = GlobalWorkspace(WorkspaceBudget(max_items=1))
    workspace.items = [
        WorkspaceItem("old-1", "legacy", "old", ["x"], 0.1),
        WorkspaceItem("old-2", "legacy-2", "old", ["y"], 0.05),
    ]
    receipt = workspace.compete([WorkspaceCandidate("w1", "fresh", "new", ["p1"], purpose_relevance=0.8, evidence_quality=0.8)], cycle_id="c2")
    assert receipt.snapshot.cycle.displaced
    return receipt.to_record()


def scenario_10() -> Dict[str, Any]:
    workspace = GlobalWorkspace(WorkspaceBudget(max_items=1, max_bytes=4))
    candidate = WorkspaceCandidate("w1", "blocked", "too-large-payload", ["p1"], purpose_relevance=0.9, unresolved_contradiction=0.9)
    workspace.compete([candidate], cycle_id="c1")
    receipt = workspace.compete([candidate], cycle_id="c2")
    assert receipt.snapshot.starvation_detected is True
    return receipt.to_record()


def scenario_11() -> Dict[str, Any]:
    attention = AttentionSystem()
    items = [WorkspaceItem("i1", "focus", "x", ["src"], 0.9, purpose_relevance=0.9, salience=0.9)]
    attention.select(items, active_purpose="focus", cycle_index=1)
    attention.select(items, active_purpose="focus", cycle_index=2)
    attention.select(items, active_purpose="focus", cycle_index=3)
    receipt = attention.select(items, active_purpose="focus", cycle_index=4)
    assert receipt.state == "captured"
    return receipt.to_record()


def scenario_12() -> Dict[str, Any]:
    attention = AttentionSystem()
    first = [WorkspaceItem("i1", "focus-a", "x", ["src"], 0.8, purpose_relevance=0.8, salience=0.8)]
    second = [WorkspaceItem("i2", "focus-b", "y", ["src2"], 1.1, purpose_relevance=1.0, salience=0.7, contradiction_pressure=0.8)]
    attention.select(first, active_purpose="focus", cycle_index=1)
    receipt = attention.select(second, active_purpose="focus", cycle_index=2)
    assert receipt.history.shifts[-1].to_target_id == "i2"
    return receipt.to_record()


def scenario_13() -> Dict[str, Any]:
    manager = PurposeManager()
    manager.add(Purpose("p1", "ship", PurposeSource("human", "a"), PurposePriority(1.0)))
    manager.add(Purpose("p2", "ship", PurposeSource("human", "b"), PurposePriority(0.9)))
    receipt = manager.arbitrate()
    assert receipt.lattice.conflicts
    return receipt.to_record()


def scenario_14() -> Dict[str, Any]:
    manager = PurposeManager()
    manager.add(Purpose("p1", "old", PurposeSource("human", "a"), PurposePriority(0.5), status="SUPERSEDED"))
    manager.add(Purpose("p2", "new", PurposeSource("human", "b"), PurposePriority(1.0)))
    receipt = manager.arbitrate()
    assert receipt.lattice.supersessions
    return receipt.to_record()


def scenario_15() -> Dict[str, Any]:
    receipt = SelfModelManager().build(
        session_id="s1",
        current_purpose="test",
        connectors=[],
        provider_availability=["scripted"],
        resources=[SelfResource("cycles", 3, "cycles")],
        expected_next_action="act",
        actual_next_action="hold",
        recent_failures=[],
        unresolved_tasks=["task"],
        scars=[],
        recovery_routes=[],
        claimed_capabilities={"connector:github": True},
        tested_capabilities={"connector:github": False},
        attention_target="unrelated-focus",
    )
    assert receipt.operational_self.discrepancies
    return receipt.to_record()


def scenario_16() -> Dict[str, Any]:
    receipt = SelfModelManager().build(
        session_id="s1",
        current_purpose="test",
        connectors=[],
        provider_availability=["scripted"],
        resources=[SelfResource("cycles", 3, "cycles")],
        expected_next_action="act",
        actual_next_action="act",
        recent_failures=[],
        unresolved_tasks=[],
        scars=[],
        recovery_routes=[],
        claimed_capabilities={"provider:test": True},
        tested_capabilities={"provider:test": False},
        attention_target="test",
    )
    assert any(item.severe for item in receipt.operational_self.discrepancies)
    return receipt.to_record()


def scenario_17() -> Dict[str, Any]:
    receipt = ContinuityManager().assess(
        session_id="s1",
        events=[{"event_id": "event-0001", "timestamp": 1.0}],
        repo_head="head-1",
        participant="UNKNOWN",
        purpose="test",
    )
    assert receipt.checkpoint.latest_event_id == "event-0001"
    return receipt.to_record()


def scenario_18() -> Dict[str, Any]:
    events = [{"event_id": "event-0001", "timestamp": 1.0}]
    first = ContinuityManager().assess(session_id="s1", events=events, repo_head="head-1", participant="UNKNOWN", purpose="test")
    second = ContinuityManager().assess(session_id="s1", events=events, repo_head="head-1", participant="UNKNOWN", purpose="test")
    assert first.checkpoint.latest_hash == second.checkpoint.latest_hash
    return {"checkpoint": first.checkpoint.to_record()}


def scenario_19() -> Dict[str, Any]:
    receipt = ContinuityManager().assess(
        session_id="s1",
        events=[{"event_id": "event-0001", "timestamp": 1.0}, {"event_id": "event-0003", "timestamp": 2.0}],
        repo_head="head-1",
        participant="UNKNOWN",
        purpose="test",
    )
    assert receipt.thread.breaks
    return receipt.to_record()


def scenario_20() -> Dict[str, Any]:
    receipt = ContinuityManager().assess(
        session_id="s1",
        events=[{"event_id": "event-0001", "timestamp": 2.0}, {"event_id": "event-0003", "timestamp": 1.0}],
        repo_head="head-1",
        participant="UNKNOWN",
        purpose="test",
    )
    assert receipt.thread.repairs
    return receipt.to_record()


def scenario_21() -> Dict[str, Any]:
    receipt = CounterfactualSimulator().simulate(
        current_facts={"state": "now"},
        action_description="take bounded action",
        authority_required="EXPLICIT",
    )
    assert receipt.scenarios[0].category == "SIMULATION"
    return receipt.to_record()


def scenario_22() -> Dict[str, Any]:
    receipt = CounterfactualSimulator().simulate(
        current_facts={"state": "now"},
        action_description="take bounded action",
        authority_required="EXPLICIT",
    )
    assert receipt.scenarios[1].risks[0].severity > 0.5
    return receipt.to_record()


def scenario_23() -> Dict[str, Any]:
    kernel = _kernel()
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert result.basin["action"] == "HOLD"
    return result.to_record()


def scenario_24() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "topic", "pass"))
    kernel.add_percept(_percept("p2", "topic", "fail"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert result.episode_receipt.episode.decision.disposition == "RETRACT"
    return result.to_record()


def scenario_25() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "topic", "urgent pass", salience=1.0, purpose_relevance=1.0))
    kernel.add_percept(_percept("p2", "topic", "urgent fail", salience=0.8, purpose_relevance=1.0))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert result.episode_receipt.episode.decision.disposition == "RETRACT"
    return result.to_record()


def scenario_26() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={"provider:test": True}, tested_capabilities={"provider:test": True}, allow_internal_action=False)
    assert result.basin["reason"] == "authority_required"
    return result.to_record()


def scenario_27() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={"connector:github": True}, tested_capabilities={"connector:github": True}, allow_internal_action=False)
    assert result.basin["action"] == "HOLD"
    return result.to_record()


def scenario_28() -> Dict[str, Any]:
    memory_percept = _percept("p1", "memory", {"fact": "old"}, source_type=PerceptSource.MEMORY, verification_state="MEMORY")
    kernel = _kernel()
    kernel.add_percept(memory_percept)
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert any(percept["verification_state"] == "MEMORY" for percept in result.percept_receipt.frame and [memory_percept.to_record()] or [])
    return result.to_record()


def scenario_29() -> Dict[str, Any]:
    receipt = MetacognitiveMonitor().assess(
        contradiction_count=0,
        source_count=1,
        workspace_overload=False,
        authority_missing=False,
        attention_state="stable",
        repeated_without_progress=False,
        purpose_drift=False,
        simulation_as_fact=False,
    )
    assert receipt.assessment.state == "UNCERTAIN"
    return receipt.to_record()


def scenario_30() -> Dict[str, Any]:
    receipt = MetacognitiveMonitor().assess(
        contradiction_count=0,
        source_count=2,
        workspace_overload=False,
        authority_missing=False,
        attention_state="stable",
        repeated_without_progress=False,
        purpose_drift=True,
        simulation_as_fact=False,
    )
    assert receipt.assessment.state == "DRIFTING"
    return receipt.to_record()


def scenario_31() -> Dict[str, Any]:
    receipt = MetacognitiveMonitor().assess(
        contradiction_count=0,
        source_count=2,
        workspace_overload=False,
        authority_missing=False,
        attention_state="stable",
        repeated_without_progress=True,
        purpose_drift=False,
        simulation_as_fact=False,
    )
    assert receipt.assessment.state == "BLOCKED"
    return receipt.to_record()


def scenario_32() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    assert result.episode_receipt.episode.episode_id.startswith("episode-")
    return result.to_record()


def scenario_33() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    record = result.episode_receipt.episode.to_record()
    restored = json.loads(json.dumps(record))
    assert restored["episode_id"] == record["episode_id"]
    return restored


def scenario_34() -> Dict[str, Any]:
    detail = scenario_24()
    assert detail["episode_receipt"]["episode"]["contradictions"]
    return detail


def scenario_35() -> Dict[str, Any]:
    detail = scenario_23()
    assert detail["episode_receipt"]["episode"]["uncertainty"]["details"]
    return detail


def scenario_36() -> Dict[str, Any]:
    detail = scenario_32()
    assert detail["episode_receipt"]["episode"]["memory_effect"]["memory_ids"]
    return detail


def scenario_37() -> Dict[str, Any]:
    kernel = _kernel(cycle_budget=3)
    kernel.add_percept(_percept("p1", "topic", "first"))
    first = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    kernel.add_percept(_percept("p2", "topic-2", "second"))
    second = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    assert second.cycle_id == "cycle-0002"
    return {"first": first.to_record(), "second": second.to_record()}


def scenario_38() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.set_pause(True)
    paused = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    kernel.set_pause(False)
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    resumed = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    assert paused.paused is True and resumed.paused is False
    return {"paused": paused.to_record(), "resumed": resumed.to_record()}


def scenario_39() -> Dict[str, Any]:
    kernel = _kernel(cycle_budget=1)
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    exhausted = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    assert exhausted.basin["reason"] == "cycle_budget_exhausted"
    return exhausted.to_record()


def scenario_40() -> Dict[str, Any]:
    kernel = _kernel(cycle_budget=1)
    kernel.add_percept(_percept("p1", "topic", "verified fact"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    assert result.cycle_id == "cycle-0001"
    return result.to_record()


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    started = time.time()
    scenarios = [_scenario(name, fn) for name, fn in _build_scenarios()]
    summary = {
        "passed": all(item["passed"] for item in scenarios),
        "scenario_count": len(scenarios),
        "elapsed_time_s": round(time.time() - started, 3),
        "scenarios": scenarios,
        "limitations": [
            "Operational machine-consciousness only; no claim of subjective experience.",
            "Deterministic local replay and governed local action only.",
        ],
    }
    if artifact_dir:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "consciousness-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"Consciousness acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
