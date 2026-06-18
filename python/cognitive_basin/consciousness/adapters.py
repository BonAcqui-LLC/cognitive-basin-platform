"""
Adapters that convert existing session artifacts into typed percepts.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .common import stable_hash
from .perception import (
    Percept,
    PerceptChannel,
    PerceptFeature,
    PerceptModality,
    PerceptReliability,
    PerceptSource,
)


def event_to_percepts(events: List[Dict[str, Any]]) -> List[Percept]:
    percepts: List[Percept] = []
    for event in events:
        event_type = str(event.get("type", ""))
        if event_type.startswith("session.consciousness."):
            continue
        if event_type == "session.evidence":
            evidence = event.get("evidence", {})
            detail = evidence.get("detail", "")
            percepts.append(
                _percept(
                    event,
                    source="session.evidence",
                    source_type=PerceptSource.HUMAN,
                    modality=PerceptModality.TEXT,
                    channel=PerceptChannel.USER,
                    content=detail,
                    topic="evidence",
                    verification_state="OBSERVATION",
                )
            )
        elif event_type == "session.claim":
            claim = event.get("claim", {})
            percepts.append(
                _percept(
                    event,
                    source="session.claim",
                    source_type=PerceptSource.PROVIDER,
                    modality=PerceptModality.MODEL_OUTPUT,
                    channel=PerceptChannel.SESSION,
                    content=claim,
                    topic=str(claim.get("claim_id", "claim")),
                    verification_state="INTERPRETATION",
                )
            )
        elif event_type.startswith("session.external_action"):
            percepts.append(
                _percept(
                    event,
                    source=event_type,
                    source_type=PerceptSource.CONNECTOR,
                    modality=PerceptModality.CONNECTOR_STATE,
                    channel=PerceptChannel.CONNECTOR,
                    content={key: value for key, value in event.items() if key not in {"type", "event_id", "timestamp"}},
                    topic="external_action",
                    verification_state="OBSERVATION",
                )
            )
        elif event_type == "action":
            feedback = event.get("result", {}).get("feedback", {})
            percepts.append(
                _percept(
                    event,
                    source="basinlab.action",
                    source_type=PerceptSource.EXECUTION,
                    modality=PerceptModality.EXECUTION_OUTPUT,
                    channel=PerceptChannel.EXECUTION,
                    content=feedback,
                    topic="execution_output",
                    verification_state="OBSERVATION",
                )
            )
        elif event_type == "commit":
            percepts.append(
                _percept(
                    event,
                    source="basinlab.commit",
                    source_type=PerceptSource.SYSTEM,
                    modality=PerceptModality.TEMPORAL_EVENT,
                    channel=PerceptChannel.GOVERNANCE,
                    content=event.get("decision", {}),
                    topic="commit_gate",
                    verification_state="OBSERVATION",
                )
            )
        elif event_type.startswith("session.memory"):
            percepts.append(
                _percept(
                    event,
                    source="session.memory",
                    source_type=PerceptSource.MEMORY,
                    modality=PerceptModality.MEMORY_RETRIEVAL,
                    channel=PerceptChannel.MEMORY,
                    content={key: value for key, value in event.items() if key not in {"type", "event_id", "timestamp"}},
                    topic="memory",
                    verification_state="MEMORY",
                )
            )
        elif event_type == "session.lab.evaluation":
            percepts.append(
                _percept(
                    event,
                    source="evaluation.lab",
                    source_type=PerceptSource.SYSTEM,
                    modality=PerceptModality.STRUCTURED_DATA,
                    channel=PerceptChannel.EVALUATION,
                    content=event.get("lab", {}),
                    topic="evaluation_lab",
                    verification_state="OBSERVATION",
                )
            )
        elif event_type == "session_started":
            percepts.append(
                _percept(
                    event,
                    source="session.started",
                    source_type=PerceptSource.SYSTEM,
                    modality=PerceptModality.TEMPORAL_EVENT,
                    channel=PerceptChannel.SYSTEM,
                    content={"pid": event.get("pid")},
                    topic="session",
                    verification_state="OBSERVATION",
                )
            )
    return percepts


def _percept(
    event: Dict[str, Any],
    *,
    source: str,
    source_type: PerceptSource,
    modality: PerceptModality,
    channel: PerceptChannel,
    content: Any,
    topic: str,
    verification_state: str,
) -> Percept:
    event_id = str(event.get("event_id", source))
    content_hash = stable_hash(content)
    return Percept(
        percept_id=f"adapted-{event_id}",
        source=source,
        source_type=source_type,
        timestamp=float(event.get("timestamp", 0.0)),
        observed_content_hash=content_hash,
        modality=modality,
        channel=channel,
        content=content,
        confidence=0.8,
        reliability=PerceptReliability(0.8, [0.8]),
        privacy_classification="restricted",
        provenance=event_id,
        novelty=0.5,
        salience=0.5,
        purpose_relevance=0.4,
        verification_state=verification_state,
        features=[PerceptFeature("topic", topic, 1.0)],
    )


__all__ = ["event_to_percepts"]
