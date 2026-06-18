"""
Real multi-cycle operational consciousness demo.
"""

from __future__ import annotations

import json

from python.cognitive_basin.consciousness import OperationalConsciousnessKernel
from python.cognitive_basin.consciousness.purpose import Purpose, PurposePriority, PurposeSource
from python.cognitive_basin.consciousness.perception import (
    Percept,
    PerceptChannel,
    PerceptFeature,
    PerceptModality,
    PerceptReliability,
    PerceptSource,
)
from python.cognitive_basin.consciousness.common import stable_hash


def _percept(
    percept_id: str,
    topic: str,
    content: str,
    *,
    source_type: PerceptSource = PerceptSource.HUMAN,
    purpose_relevance: float = 0.8,
    verification_state: str = "OBSERVATION",
) -> Percept:
    return Percept(
        percept_id=percept_id,
        source="demo",
        source_type=source_type,
        timestamp=1.0,
        observed_content_hash=stable_hash(content),
        modality=PerceptModality.TEXT,
        channel=PerceptChannel.USER,
        content=content,
        confidence=0.9,
        reliability=PerceptReliability(0.9, [0.9]),
        privacy_classification="restricted",
        provenance="demo",
        novelty=0.6,
        salience=0.7,
        purpose_relevance=purpose_relevance,
        verification_state=verification_state if source_type != PerceptSource.MEMORY else "MEMORY",
        features=[PerceptFeature("topic", topic, 1.0)],
    )


def run_demo() -> dict:
    kernel = OperationalConsciousnessKernel(
        session_id="demo-session",
        purpose_text="verify branch readiness",
        participant="UNKNOWN",
        repo_head="demo-head",
        cycle_budget=4,
    )
    kernel.add_purpose(Purpose("purpose-main", "verify branch readiness", PurposeSource("explicit human request", "demo"), PurposePriority(1.0, 0.7)))
    kernel.add_purpose(Purpose("purpose-side", "prepare a release note", PurposeSource("project commitment", "demo"), PurposePriority(0.5, 0.2)))

    kernel.add_percept(_percept("p1", "branch", "The branch may be ready"))
    hold_cycle = kernel.run_cycle(
        events=[],
        connectors=[{"identity": {"connector_id": "github", "default_scope": "WRITE"}, "policy": {"write_requires_permit": True}}],
        claimed_capabilities={"connector:github": True},
        tested_capabilities={"connector:github": False},
        allow_internal_action=False,
    )

    kernel.add_percept(_percept("p2", "tests", "Tests passed on one machine"))
    kernel.add_percept(_percept("p3", "tests", "Tests failed on CI", source_type=PerceptSource.SYSTEM))
    conflict_cycle = kernel.run_cycle(
        events=[{"event_id": "event-0001", "timestamp": 1.0}],
        connectors=[{"identity": {"connector_id": "github", "default_scope": "WRITE"}, "policy": {"write_requires_permit": True}}],
        claimed_capabilities={"connector:github": True},
        tested_capabilities={"connector:github": False},
        allow_internal_action=False,
    )

    kernel.add_percept(
        _percept(
            "p4",
            "tests",
            "Two independent green runs verified",
            source_type=PerceptSource.SYSTEM,
            purpose_relevance=1.0,
            verification_state="VERIFIED_FACT",
        )
    )
    recovered_cycle = kernel.run_cycle(
        events=[{"event_id": "event-0001", "timestamp": 1.0}, {"event_id": "event-0002", "timestamp": 2.0}],
        connectors=[{"identity": {"connector_id": "github", "default_scope": "WRITE"}, "policy": {"write_requires_permit": True}}],
        claimed_capabilities={"connector:github": True},
        tested_capabilities={"connector:github": True},
        allow_internal_action=True,
    )

    return {
        "hold_cycle": hold_cycle.to_record(),
        "conflict_cycle": conflict_cycle.to_record(),
        "recovered_cycle": recovered_cycle.to_record(),
        "final_snapshot": kernel.snapshot().to_record(),
    }


def main() -> int:
    demo = run_demo()
    print(json.dumps(demo, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
