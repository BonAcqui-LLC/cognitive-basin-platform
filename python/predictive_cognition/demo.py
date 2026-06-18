"""
Deterministic predictive cognition demo.
"""

from __future__ import annotations

import json

from python.cognitive_basin.causality import (
    CausalClaim,
    CausalEvidence,
    InterventionControl,
    InterventionPrediction,
    InterventionProposal,
    InterventionTarget,
    InterventionValue,
    InterventionVariable,
)
from python.cognitive_basin.consciousness import OperationalConsciousnessKernel
from python.cognitive_basin.consciousness.perception import Percept, PerceptChannel, PerceptFeature, PerceptModality, PerceptReliability, PerceptSource
from python.cognitive_basin.consciousness.purpose import Purpose, PurposePriority, PurposeSource
from python.cognitive_basin.consciousness.common import stable_hash
from python.cognitive_basin.world_model import WorldObservation


def _percept(percept_id: str, topic: str, content: str, *, source: str = "demo", source_type: PerceptSource = PerceptSource.HUMAN, verification_state: str = "OBSERVATION") -> Percept:
    return Percept(
        percept_id=percept_id,
        source=source,
        source_type=source_type,
        timestamp=1.0,
        observed_content_hash=stable_hash(content),
        modality=PerceptModality.TEXT,
        channel=PerceptChannel.USER,
        content=content,
        confidence=0.9,
        reliability=PerceptReliability(0.9, [0.9]),
        privacy_classification="restricted",
        provenance="predictive-demo",
        novelty=0.6,
        salience=0.7,
        purpose_relevance=0.9,
        verification_state=verification_state,
        features=[PerceptFeature("topic", topic, 1.0)],
    )


def _observation(observation_id: str, property_name: str, value: str, *, entity_id: str = "branch-1") -> WorldObservation:
    return WorldObservation(
        observation_id=observation_id,
        entity_type="BRANCH",
        property_name=property_name,
        value=value,
        category="OBSERVED",
        source="demo",
        provenance="predictive-demo",
        entity_id=entity_id,
        identity_hints={"branch": entity_id},
    )


def run_demo() -> dict:
    kernel = OperationalConsciousnessKernel(
        session_id="predictive-demo",
        purpose_text="verify branch readiness",
        participant="UNKNOWN",
        repo_head="demo-head",
        cycle_budget=4,
    )
    kernel.add_purpose(Purpose("purpose-main", "verify branch readiness", PurposeSource("explicit human request", "demo"), PurposePriority(1.0, 0.7)))
    kernel.add_percept(_percept("p1", "branch", "Branch appears ready"))
    kernel.add_world_observation(_observation("o1", "status", "uncertain"))
    kernel.add_prediction_spec(
        {
            "entity_id": "branch-1",
            "property_name": "status",
            "expected_value": "green",
            "confidence": 0.8,
            "assumptions": ["tests stay green"],
            "evidence": ["prior local run"],
            "verification_method": "observe next CI status",
        }
    )
    kernel.add_causal_claim(CausalClaim("claim-1", "ci-green", "branch-ready", "HYPOTHESIZED", [CausalEvidence("local observations")], confounders=["stale cache"]))
    kernel.add_perspective_record(
        {
            "owner_id": "James Clow",
            "owner_class": "PARTICIPANT_JAMES",
            "statement": "Please verify before acting",
            "label": "goal",
            "evidence_category": "EXPLICITLY_STATED",
        }
    )
    first = kernel.run_cycle(events=[], connectors=[{"identity": {"connector_id": "github"}}], claimed_capabilities={"connector:github": True}, tested_capabilities={"connector:github": False}, allow_internal_action=False)

    kernel.add_percept(_percept("p2", "branch", "CI observed red", source_type=PerceptSource.SYSTEM))
    kernel.add_world_observation(_observation("o2", "status", "red"))
    surprising = kernel.run_cycle(events=[{"event_id": "event-0001", "timestamp": 1.0}], connectors=[{"identity": {"connector_id": "github"}}], claimed_capabilities={"connector:github": True}, tested_capabilities={"connector:github": False}, allow_internal_action=False)

    kernel.add_intervention(
        InterventionProposal(
            "proposal-1",
            InterventionTarget("status", "SIMULATION"),
            InterventionVariable("status"),
            InterventionValue("green"),
            InterventionControl("red"),
            InterventionPrediction("green after rerun"),
            "SIMULATION",
        )
    )
    kernel.add_world_observation(_observation("o3", "status", "green"))
    kernel.add_rehearsal_request("simulate rerun and verify again")
    recovered = kernel.run_cycle(
        events=[{"event_id": "event-0001", "timestamp": 1.0}, {"event_id": "event-0002", "timestamp": 2.0}],
        connectors=[{"identity": {"connector_id": "github"}}],
        claimed_capabilities={"connector:github": True},
        tested_capabilities={"connector:github": True},
        allow_internal_action=True,
    )

    return {
        "initial_cycle": first.to_record(),
        "surprising_cycle": surprising.to_record(),
        "recovered_cycle": recovered.to_record(),
        "final_snapshot": kernel.snapshot().to_record(),
    }


def main() -> int:
    print(json.dumps(run_demo(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
