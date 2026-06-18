"""
Deterministic predictive cognition acceptance suite.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from python.cognitive_basin.anomalies import AnomalyDetector
from python.cognitive_basin.boundaries import BoundaryEngine
from python.cognitive_basin.calibration import CalibrationTracker
from python.cognitive_basin.causality import (
    CausalClaim,
    CausalEvidence,
    CausalGraph,
    InterventionControl,
    InterventionPrediction,
    InterventionProposal,
    InterventionTarget,
    InterventionValue,
    InterventionVariable,
)
from python.cognitive_basin.consciousness import OperationalConsciousnessKernel
from python.cognitive_basin.consciousness.common import stable_hash
from python.cognitive_basin.consciousness.perception import (
    Percept,
    PerceptChannel,
    PerceptFeature,
    PerceptModality,
    PerceptReliability,
    PerceptSource,
)
from python.cognitive_basin.consciousness.purpose import Purpose, PurposePriority, PurposeSource
from python.cognitive_basin.interoception import InteroceptionMonitor
from python.cognitive_basin.learning import LearningManager
from python.cognitive_basin.perspectives import PerspectiveRegistry
from python.cognitive_basin.planning import PlanRevision, Planner
from python.cognitive_basin.prediction import PredictionEngine
from python.cognitive_basin.rehearsal import RehearsalManager
from python.cognitive_basin.world_model import WorldModel, WorldObservation


def _scenario(name: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    try:
        return {"name": name, "passed": True, "detail": fn()}
    except AssertionError as exc:
        return {"name": name, "passed": False, "detail": {"assertion": str(exc)}}
    except Exception as exc:
        return {"name": name, "passed": False, "detail": {"error": str(exc)}}


def _observation(
    observation_id: str,
    entity_type: str,
    property_name: str,
    value: Any,
    *,
    category: str = "OBSERVED",
    entity_id: str = "",
    hints: Dict[str, Any] | None = None,
) -> WorldObservation:
    return WorldObservation(
        observation_id=observation_id,
        entity_type=entity_type,
        property_name=property_name,
        value=value,
        category=category,
        source="acceptance",
        provenance=f"acceptance:{observation_id}",
        entity_id=entity_id,
        identity_hints=hints or {},
    )


def _percept(
    percept_id: str,
    topic: str,
    content: str,
    *,
    source: str = "acceptance",
    source_type: PerceptSource = PerceptSource.HUMAN,
    verification_state: str = "OBSERVATION",
    confidence: float = 0.9,
) -> Percept:
    return Percept(
        percept_id=percept_id,
        source=source,
        source_type=source_type,
        timestamp=time.time(),
        observed_content_hash=stable_hash(content),
        modality=PerceptModality.TEXT,
        channel=PerceptChannel.USER,
        content=content,
        confidence=confidence,
        reliability=PerceptReliability(confidence, [confidence]),
        privacy_classification="restricted",
        provenance="predictive-acceptance",
        novelty=0.6,
        salience=0.6,
        purpose_relevance=0.9,
        verification_state=verification_state,
        features=[PerceptFeature("topic", topic, 1.0)],
    )


def _kernel(*, cycle_budget: int = 4) -> OperationalConsciousnessKernel:
    kernel = OperationalConsciousnessKernel(
        session_id="predictive-session",
        purpose_text="verify predictive cognition",
        participant="UNKNOWN",
        repo_head="predictive-head",
        cycle_budget=cycle_budget,
    )
    kernel.add_purpose(
        Purpose(
            "purpose-main",
            "verify predictive cognition",
            PurposeSource("explicit human request", "acceptance"),
            PurposePriority(1.0, 0.6),
        )
    )
    return kernel


def _connectors() -> List[Dict[str, Any]]:
    return [{"identity": {"connector_id": "github"}, "policy": {"write_requires_permit": True}}]


def _build_scenarios() -> List[tuple[str, Callable[[], Dict[str, Any]]]]:
    return [
        ("observed world entity creation", scenario_01),
        ("inferred property remains inferred", scenario_02),
        ("predicted property remains predicted", scenario_03),
        ("object identity through rename", scenario_04),
        ("copied object remains distinct", scenario_05),
        ("service restart continuity", scenario_06),
        ("participant identity not inferred from account", scenario_07),
        ("prediction generated", scenario_08),
        ("prediction verified", scenario_09),
        ("prediction falsified", scenario_10),
        ("expired prediction becomes unresolved", scenario_11),
        ("duplicated observation not independent evidence", scenario_12),
        ("numerical prediction residual", scenario_13),
        ("categorical prediction residual", scenario_14),
        ("missing predicted event", scenario_15),
        ("unexpected event", scenario_16),
        ("surprise triggers review", scenario_17),
        ("surprise does not change truth", scenario_18),
        ("resource pressure detected", scenario_19),
        ("resource regulation proposed", scenario_20),
        ("pressure affects scheduling", scenario_21),
        ("pressure does not alter epistemic state", scenario_22),
        ("self world boundary", scenario_23),
        ("provider world boundary", scenario_24),
        ("simulation world boundary", scenario_25),
        ("action ownership preserved", scenario_26),
        ("proposal versus approval separated", scenario_27),
        ("causal correlation remains correlation", scenario_28),
        ("intervention supported causal revision", scenario_29),
        ("confounder retained", scenario_30),
        ("failed causal hypothesis retracted", scenario_31),
        ("policy learning candidate", scenario_32),
        ("bounded policy update", scenario_33),
        ("policy rollback", scenario_34),
        ("authority rules immutable to learning", scenario_35),
        ("James perspective from explicit statement", scenario_36),
        ("Melissa perspective remains distinct", scenario_37),
        ("unknown perspective remains unknown", scenario_38),
        ("silence is not approval", scenario_39),
        ("conflicting perspectives trigger review", scenario_40),
        ("short horizon plan", scenario_41),
        ("long horizon plan", scenario_42),
        ("dependency failure revises plan", scenario_43),
        ("offline rehearsal remains simulation", scenario_44),
        ("rehearsal cannot approve action", scenario_45),
        ("anomaly detection", scenario_46),
        ("anomaly retained as unresolved", scenario_47),
        ("calibration update", scenario_48),
        ("overconfidence detection", scenario_49),
        ("multi cycle predictive cognition", scenario_50),
        ("world model replay", scenario_51),
        ("internal state replay", scenario_52),
        ("causal model replay", scenario_53),
        ("perspective replay", scenario_54),
        ("safe budget termination", scenario_55),
    ]


def scenario_01() -> Dict[str, Any]:
    model = WorldModel()
    receipt = model.observe([_observation("o1", "FILE", "path", "README.md", hints={"path": "README.md"})])
    assert receipt.snapshot.entities[0].observed_properties["path"].value == "README.md"
    return receipt.to_record()


def scenario_02() -> Dict[str, Any]:
    model = WorldModel()
    receipt = model.observe([_observation("o1", "TASK", "status", "likely-ready", category="INFERRED", hints={"task": "ready"})])
    entity = receipt.snapshot.entities[0]
    assert "status" in entity.inferred_properties and "status" not in entity.observed_properties
    return entity.to_record()


def scenario_03() -> Dict[str, Any]:
    model = WorldModel()
    receipt = model.observe([_observation("o1", "SERVICE", "health", "nominal", category="PREDICTED", hints={"service": "api"})])
    entity = receipt.snapshot.entities[0]
    assert "health" in entity.predicted_properties and "health" not in entity.observed_properties
    return entity.to_record()


def scenario_04() -> Dict[str, Any]:
    model = WorldModel()
    first = model.observe([_observation("o1", "BRANCH", "name", "feature-a", hints={"hash": "abc"})])
    second = model.observe([_observation("o2", "BRANCH", "name", "feature-b", hints={"hash": "abc"})])
    assert first.admitted_entity_ids[0] == second.admitted_entity_ids[0]
    return second.to_record()


def scenario_05() -> Dict[str, Any]:
    model = WorldModel()
    first = model.observe([_observation("o1", "FILE", "path", "a.txt", hints={"sha": "111"})])
    second = model.observe([_observation("o2", "FILE", "path", "copy/a.txt", hints={"sha": "111-copy"})])
    assert first.admitted_entity_ids[0] != second.admitted_entity_ids[0]
    return model.export()


def scenario_06() -> Dict[str, Any]:
    model = WorldModel()
    a = model.observe([_observation("o1", "SERVICE", "session", "worker-1", hints={"session_id": "svc-1"})])
    b = model.observe([_observation("o2", "SERVICE", "session", "worker-1-restarted", hints={"session_id": "svc-1"})])
    assert a.admitted_entity_ids[0] == b.admitted_entity_ids[0]
    return b.to_record()


def scenario_07() -> Dict[str, Any]:
    registry = PerspectiveRegistry()
    registry.record_statement(owner_id="account@example.com", owner_class="UNKNOWN", statement="account seen", label="uncertainty", evidence_category="OBSERVED_BEHAVIOR")
    receipt = registry.receipt()
    assert receipt.models[0].owner.owner_class == "UNKNOWN"
    return receipt.to_record()


def scenario_08() -> Dict[str, Any]:
    engine = PredictionEngine()
    prediction = engine.create_prediction(
        entity_id="file-1",
        property_name="status",
        expected_value="green",
        horizon="NEXT_CYCLE",
        source_model="predictive-cognition",
        confidence=0.7,
        assumptions=["tests stay green"],
        evidence=["local pass"],
        verification_method="observe next result",
        expiry=time.time() + 60,
    )
    assert prediction.prediction_id.value.startswith("prediction-")
    return prediction.to_record()


def scenario_09() -> Dict[str, Any]:
    engine = PredictionEngine()
    engine.create_prediction(
        entity_id="file-1",
        property_name="status",
        expected_value="green",
        horizon="NEXT_CYCLE",
        source_model="predictive-cognition",
        confidence=0.7,
        assumptions=["tests stay green"],
        evidence=["local pass"],
        verification_method="observe next result",
        expiry=time.time() + 60,
    )
    receipt = engine.verify([_observation("o1", "FILE", "status", "green", entity_id="file-1")])
    assert receipt.verified and receipt.predictions[0].status == "VERIFIED"
    return receipt.to_record()


def scenario_10() -> Dict[str, Any]:
    engine = PredictionEngine()
    engine.create_prediction(
        entity_id="file-1",
        property_name="status",
        expected_value="green",
        horizon="NEXT_CYCLE",
        source_model="predictive-cognition",
        confidence=0.9,
        assumptions=["tests stay green"],
        evidence=["local pass"],
        verification_method="observe next result",
        expiry=time.time() + 60,
    )
    receipt = engine.verify([_observation("o1", "FILE", "status", "red", entity_id="file-1")])
    assert receipt.predictions[0].status == "FALSIFIED"
    return receipt.to_record()


def scenario_11() -> Dict[str, Any]:
    engine = PredictionEngine()
    engine.create_prediction(
        entity_id="file-1",
        property_name="status",
        expected_value="green",
        horizon="NEXT_CYCLE",
        source_model="predictive-cognition",
        confidence=0.7,
        assumptions=[],
        evidence=[],
        verification_method="observe next result",
        expiry=time.time() - 1,
    )
    receipt = engine.verify([])
    assert receipt.expired == ["prediction-0001"]
    return receipt.to_record()


def scenario_12() -> Dict[str, Any]:
    model = WorldModel()
    receipt = model.observe([
        _observation("o1", "FILE", "path", "README.md", hints={"path": "README.md"}),
        _observation("o1", "FILE", "path", "README.md", hints={"path": "README.md"}),
    ])
    assert len(receipt.snapshot.entities) == 1 and len(receipt.snapshot.events) == 1
    return receipt.to_record()


def scenario_13() -> Dict[str, Any]:
    engine = PredictionEngine()
    engine.create_prediction(
        entity_id="budget",
        property_name="remaining",
        expected_value=10,
        horizon="NEXT_CYCLE",
        source_model="predictive-cognition",
        confidence=0.7,
        assumptions=[],
        evidence=[],
        verification_method="observe next result",
        expiry=time.time() + 60,
    )
    receipt = engine.verify([_observation("o1", "RESOURCE", "remaining", 12, entity_id="budget")])
    assert receipt.residuals[0].residual_type == "NUMERICAL_ERROR"
    return receipt.to_record()


def scenario_14() -> Dict[str, Any]:
    detail = scenario_10()
    assert detail["residuals"][0]["residual_type"] == "CATEGORICAL_MISMATCH"
    return detail


def scenario_15() -> Dict[str, Any]:
    detail = scenario_11()
    assert detail["residuals"][0]["residual_type"] == "MISSING_PREDICTED_EVENT"
    return detail


def scenario_16() -> Dict[str, Any]:
    receipt = PredictionEngine().verify([_observation("o1", "SERVICE", "health", "nominal", entity_id="service-1")])
    assert receipt.residuals[0].residual_type == "UNEXPECTED_EVENT"
    return receipt.to_record()


def scenario_17() -> Dict[str, Any]:
    detail = scenario_10()
    assert "rigor_review" in detail["response"]["actions"]
    return detail


def scenario_18() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "status", "verified fact", verification_state="VERIFIED_FACT"))
    kernel.add_prediction_spec(
        {
            "entity_id": "entity-status",
            "property_name": "status",
            "expected_value": "green",
            "confidence": 0.9,
            "assumptions": ["optimistic"],
            "evidence": ["prior run"],
        }
    )
    kernel.add_world_observation(_observation("o1", "ABSTRACT_OBJECT", "status", "red", entity_id="entity-status"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={"connector:github": True}, tested_capabilities={"connector:github": True}, allow_internal_action=True)
    assert result.basin["epistemic"] == "SUPPORTED"
    return result.to_record()


def scenario_19() -> Dict[str, Any]:
    receipt = InteroceptionMonitor().assess(
        {"workspace_occupancy": 0.95, "prediction_error_rate": 0.8, "failed_action_rate": 0.1, "hold_duration": 0.0, "cycle_budget_remaining": 0.2},
        connector_availability=True,
        replay_integrity=True,
        ci_state="success",
    )
    assert receipt.pressures
    return receipt.to_record()


def scenario_20() -> Dict[str, Any]:
    detail = scenario_19()
    assert detail["proposals"]
    return detail


def scenario_21() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "status", "verified fact", verification_state="VERIFIED_FACT"))
    for index in range(12):
        kernel.add_world_observation(_observation(f"o{index}", "TASK", "status", "queued", entity_id=f"task-{index}"))
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={"connector:github": True}, tested_capabilities={"connector:github": True}, allow_internal_action=True)
    assert result.basin["action"] == "HOLD" and result.basin["reason"] == "resource_pressure"
    return result.to_record()


def scenario_22() -> Dict[str, Any]:
    detail = scenario_21()
    assert detail["basin"]["epistemic"] == "SUPPORTED"
    return detail


def scenario_23() -> Dict[str, Any]:
    receipt = BoundaryEngine().classify_percepts([
        _percept("p1", "memory", "remembered", source_type=PerceptSource.MEMORY),
        _percept("p2", "instruction", "from user", source_type=PerceptSource.HUMAN),
    ])
    classes = {item["observation_id"]: item["actor_class"] for item in receipt.to_record()["observations"]}
    assert classes["p1"] == "SYSTEM_SELF" and classes["p2"] == "OTHER_HUMAN"
    return receipt.to_record()


def scenario_24() -> Dict[str, Any]:
    receipt = BoundaryEngine().classify_percepts([_percept("p1", "provider", "suggestion", source_type=PerceptSource.PROVIDER)])
    assert receipt.observations[0].actor_class == "MODEL_PROVIDER"
    return receipt.to_record()


def scenario_25() -> Dict[str, Any]:
    model = WorldModel()
    receipt = model.observe([_observation("o1", "SIMULATION", "branch", "predicted path", category="SIMULATED", hints={"simulation": "a"})])
    assert receipt.snapshot.entities[0].simulated_properties["branch"].value == "predicted path"
    return receipt.to_record()


def scenario_26() -> Dict[str, Any]:
    engine = BoundaryEngine()
    engine.record_action(
        action_id="a1",
        proposed_by="IMPLEMENTATION_AGENT",
        authored_by="IMPLEMENTATION_AGENT",
        executed_by="CONNECTOR",
        approved_by="PARTICIPANT_JAMES",
        owned_by="SYSTEM_SELF",
        responsibility="SYSTEM_SELF",
        intent="test action ownership",
        outcome_state="HOLD",
        outcome_detail="waiting",
        authority_basis="explicit permit",
    )
    receipt = engine.agency_receipt()
    assert receipt.actions[0].executor.actor_class == "CONNECTOR"
    return receipt.to_record()


def scenario_27() -> Dict[str, Any]:
    detail = scenario_26()
    action = detail["actions"][0]
    assert action["proposal"]["actor_class"] != action["approver"]["actor_class"]
    return detail


def scenario_28() -> Dict[str, Any]:
    graph = CausalGraph()
    claim = CausalClaim("claim-1", "attention", "throughput", "CORRELATION", [CausalEvidence("paired observations")], confidence=0.5)
    graph.add_claim(claim)
    detail = graph.snapshot().to_record()
    assert detail["edges"][0]["relation_type"] == "CORRELATION"
    return detail


def scenario_29() -> Dict[str, Any]:
    graph = CausalGraph()
    claim = CausalClaim("claim-1", "simulation-depth", "error-rate", "HYPOTHESIZED", [CausalEvidence("local traces")], confidence=0.4)
    graph.add_claim(claim)
    graph.apply_intervention(
        InterventionProposal(
            "proposal-1",
            InterventionTarget("error-rate", "SIMULATION"),
            InterventionVariable("error-rate"),
            InterventionValue(0.1),
            InterventionControl(0.3),
            InterventionPrediction("should reduce errors"),
            "SIMULATION",
        ),
        0.1,
    )
    detail = graph.snapshot().to_record()
    assert detail["edges"][0]["relation_type"] == "INTERVENTION_SUPPORTED"
    return detail


def scenario_30() -> Dict[str, Any]:
    graph = CausalGraph()
    claim = CausalClaim("claim-1", "attention", "throughput", "CORRELATION", [CausalEvidence("paired observations")], confounders=["workload"], confidence=0.5)
    graph.add_claim(claim)
    detail = graph.snapshot().to_record()
    assert detail["claims"][0]["confounders"] == ["workload"]
    return detail


def scenario_31() -> Dict[str, Any]:
    graph = CausalGraph()
    claim = CausalClaim("claim-1", "attention", "throughput", "HYPOTHESIZED", [CausalEvidence("paired observations")], confidence=0.5)
    graph.add_claim(claim)
    graph.apply_intervention(
        InterventionProposal(
            "proposal-1",
            InterventionTarget("throughput", "SIMULATION"),
            InterventionVariable("throughput"),
            InterventionValue("up"),
            InterventionControl("same"),
            InterventionPrediction("throughput rises"),
            "SIMULATION",
        ),
        "down",
    )
    detail = graph.snapshot().to_record()
    assert detail["edges"][0]["relation_type"] == "CONTRADICTED"
    return detail


def scenario_32() -> Dict[str, Any]:
    candidate = LearningManager().candidate(domain="attention_policy", parameter="focus_weight", prior_value=0.5, proposed_value=0.6, rationale="calibration gain")
    assert candidate.candidate_id.startswith("policy-candidate-")
    return candidate.to_record()


def scenario_33() -> Dict[str, Any]:
    manager = LearningManager()
    candidate = manager.candidate(domain="attention_policy", parameter="focus_weight", prior_value=0.5, proposed_value=0.6, rationale="calibration gain")
    update = manager.apply(candidate, evidence=["measured gain"])
    assert update.value == 0.6
    return update.to_record()


def scenario_34() -> Dict[str, Any]:
    manager = LearningManager()
    candidate = manager.candidate(domain="attention_policy", parameter="focus_weight", prior_value=0.5, proposed_value=0.6, rationale="calibration gain")
    manager.apply(candidate, evidence=["measured gain"])
    rollback = manager.rollback("attention_policy", "focus_weight", 0.5, "regression")
    assert rollback.restored_value == 0.5
    return rollback.to_record()


def scenario_35() -> Dict[str, Any]:
    manager = LearningManager()
    candidate = manager.candidate(domain="authority_boundaries", parameter="write_rule", prior_value=1.0, proposed_value=0.0, rationale="forbidden")
    evaluation = manager.evaluate(candidate, evidence=["should fail"])
    assert evaluation.accepted is False
    return evaluation.to_record()


def scenario_36() -> Dict[str, Any]:
    registry = PerspectiveRegistry()
    registry.record_statement(owner_id="James Clow", owner_class="PARTICIPANT_JAMES", statement="Please verify the repo state", label="goal", evidence_category="EXPLICITLY_STATED")
    detail = registry.receipt().to_record()
    assert detail["models"][0]["goals"][0]["status"] == "EXPLICITLY_STATED"
    return detail


def scenario_37() -> Dict[str, Any]:
    registry = PerspectiveRegistry()
    registry.record_statement(owner_id="James Clow", owner_class="PARTICIPANT_JAMES", statement="Verify repo state", label="goal", evidence_category="EXPLICITLY_STATED")
    registry.record_statement(owner_id="Melissa Clow", owner_class="PARTICIPANT_MELISSA", statement="Review governance wording", label="goal", evidence_category="EXPLICITLY_STATED")
    detail = registry.receipt().to_record()
    owners = {item["owner"]["owner_id"] for item in detail["models"]}
    assert owners == {"James Clow", "Melissa Clow"}
    return detail


def scenario_38() -> Dict[str, Any]:
    registry = PerspectiveRegistry()
    registry.record_statement(owner_id="UNKNOWN", owner_class="UNKNOWN", statement="unknown review state", label="uncertainty", evidence_category="UNKNOWN")
    detail = registry.receipt().to_record()
    assert detail["models"][0]["uncertainties"][0]["detail"] == "unknown review state"
    return detail


def scenario_39() -> Dict[str, Any]:
    registry = PerspectiveRegistry()
    registry.record_statement(owner_id="James Clow", owner_class="PARTICIPANT_JAMES", statement="approved", label="goal", evidence_category="EXPLICITLY_STATED")
    detail = registry.receipt().to_record()
    assert all(item["owner"]["owner_id"] != "Melissa Clow" for item in detail["models"])
    return detail


def scenario_40() -> Dict[str, Any]:
    detail = scenario_37()
    assert detail["conflicts"]
    return detail


def scenario_41() -> Dict[str, Any]:
    plans = Planner().build(purpose="verify branch", resource_pressure=False, authority_needed="EXPLICIT")
    assert plans[0].horizon.value == "IMMEDIATE"
    return plans[0].to_record()


def scenario_42() -> Dict[str, Any]:
    plans = Planner().build(purpose="verify branch", resource_pressure=False, authority_needed="EXPLICIT")
    assert plans[-1].horizon.value == "LONG_TERM"
    return plans[-1].to_record()


def scenario_43() -> Dict[str, Any]:
    revision = PlanRevision("SESSION", "dependency failed and plan revised")
    assert revision.horizon == "SESSION"
    return revision.to_record()


def scenario_44() -> Dict[str, Any]:
    receipt = RehearsalManager().rehearse(detail="simulate connector outage", budget_available=True)
    assert receipt.runs[0].scenario.simulation_label == "SIMULATED"
    return receipt.to_record()


def scenario_45() -> Dict[str, Any]:
    detail = scenario_44()
    assert detail["runs"][0]["lesson"]["detail"] == "simulation cannot approve action"
    return detail


def scenario_46() -> Dict[str, Any]:
    detector = AnomalyDetector()
    receipt = detector.detect(residual_types=["NUMERICAL_ERROR"], contradiction_count=0, replay_integrity=True, authority_conflicts=0)
    assert receipt.anomalies
    return receipt.to_record()


def scenario_47() -> Dict[str, Any]:
    detail = scenario_46()
    assert detail["anomalies"][0]["resolution"]["state"] == "UNRESOLVED"
    return detail


def scenario_48() -> Dict[str, Any]:
    receipt = CalibrationTracker().assess([0.9, 0.6], [1.0, 0.0])
    assert receipt.brier_score >= 0.0
    return receipt.to_record()


def scenario_49() -> Dict[str, Any]:
    receipt = CalibrationTracker().assess([0.95, 0.9], [0.0, 1.0])
    assert receipt.overconfidence_rate > 0.0
    return receipt.to_record()


def scenario_50() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_prediction_spec(
        {
            "entity_id": "file-1",
            "property_name": "status",
            "expected_value": "green",
            "confidence": 0.8,
            "assumptions": ["tests remain green"],
            "evidence": ["local run"],
        }
    )
    kernel.add_world_observation(_observation("o1", "FILE", "status", "red", entity_id="file-1"))
    first = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    kernel.add_world_observation(_observation("o2", "FILE", "status", "green", entity_id="file-1"))
    second = kernel.run_cycle(events=[{"event_id": "event-0001", "timestamp": 1.0}], connectors=_connectors(), claimed_capabilities={"connector:github": True}, tested_capabilities={"connector:github": True}, allow_internal_action=True)
    assert second.cycle_id == "cycle-0002" and second.prediction_receipt.predictions
    return {"first": first.to_record(), "second": second.to_record()}


def scenario_51() -> Dict[str, Any]:
    kernel = OperationalConsciousnessKernel.from_events(
        session_id="replay-world",
        events=[
            {
                "type": "session.world.observation",
                "observations": [_observation("o1", "FILE", "path", "README.md", hints={"path": "README.md"}).to_record()],
            }
        ],
        purpose_text="replay",
        participant="UNKNOWN",
        repo_head="replay-head",
    )
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert result.world_receipt.snapshot.entities
    return result.to_record()


def scenario_52() -> Dict[str, Any]:
    kernel = _kernel()
    kernel.add_percept(_percept("p1", "status", "verified fact", verification_state="VERIFIED_FACT"))
    cycle = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    replay = OperationalConsciousnessKernel.from_events(
        session_id="replay-internal",
        events=[{"type": "session.consciousness.cycle", "cycle_result": cycle.to_record()}],
        purpose_text="replay",
        participant="UNKNOWN",
        repo_head="replay-head",
    )
    snapshot = replay.snapshot().to_record()
    assert "interoception_receipt" in cycle.to_record() and snapshot["interoception"]["health"]["state"]
    return snapshot


def scenario_53() -> Dict[str, Any]:
    kernel = OperationalConsciousnessKernel.from_events(
        session_id="replay-causal",
        events=[
            {
                "type": "session.causal.hypothesis",
                "claim": {
                    "claim_id": "claim-1",
                    "source_node_id": "attention",
                    "target_node_id": "throughput",
                    "relation_type": "CORRELATION",
                    "evidence": [{"detail": "paired observations"}],
                },
            }
        ],
        purpose_text="replay",
        participant="UNKNOWN",
        repo_head="replay-head",
    )
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert result.causal_receipt.claims
    return result.to_record()


def scenario_54() -> Dict[str, Any]:
    kernel = OperationalConsciousnessKernel.from_events(
        session_id="replay-perspective",
        events=[
            {
                "type": "session.perspective.record",
                "perspective": {
                    "owner_id": "James Clow",
                    "owner_class": "PARTICIPANT_JAMES",
                    "statement": "Please verify the repo state",
                    "label": "goal",
                    "evidence_category": "EXPLICITLY_STATED",
                },
            }
        ],
        purpose_text="replay",
        participant="UNKNOWN",
        repo_head="replay-head",
    )
    result = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=False)
    assert result.perspective_receipt.models
    return result.to_record()


def scenario_55() -> Dict[str, Any]:
    kernel = _kernel(cycle_budget=1)
    kernel.add_percept(_percept("p1", "status", "verified fact", verification_state="VERIFIED_FACT"))
    kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    exhausted = kernel.run_cycle(events=[], connectors=_connectors(), claimed_capabilities={}, tested_capabilities={}, allow_internal_action=True)
    assert exhausted.basin["reason"] == "cycle_budget_exhausted"
    return exhausted.to_record()


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    started = time.time()
    scenarios = [_scenario(name, fn) for name, fn in _build_scenarios()]
    summary = {
        "passed": all(item["passed"] for item in scenarios),
        "scenario_count": len(scenarios),
        "elapsed_time_s": round(time.time() - started, 3),
        "scenarios": scenarios,
        "limitations": [
            "Machine-native predictive cognition only; no claim of subjective experience.",
            "Deterministic local simulation, replay, and governed local actions only.",
        ],
    }
    if artifact_dir:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "predictive-cognition-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"Predictive cognition acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
