"""
Structured dynamic world model with explicit property-state separation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from python.cognitive_basin.consciousness.common import canonical_json, now_ts, stable_hash


PROPERTY_CATEGORIES = {
    "OBSERVED",
    "INFERRED",
    "PREDICTED",
    "SIMULATED",
    "REMEMBERED",
    "ASSUMED",
    "POLICY_DEFINED",
    "UNKNOWN",
}


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class WorldEntityID:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class WorldProperty:
    name: str
    value: Any
    category: str
    source: str
    provenance: str
    uncertainty: float = 0.0
    temporal_validity: Dict[str, float] = field(default_factory=dict)
    contradiction_links: List[str] = field(default_factory=list)
    revision_history: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.category not in PROPERTY_CATEGORIES:
            raise ValueError(f"Unsupported property category: {self.category}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category,
            "source": self.source,
            "provenance": self.provenance,
            "uncertainty": self.uncertainty,
            "temporal_validity": dict(self.temporal_validity),
            "contradiction_links": list(self.contradiction_links),
            "revision_history": list(self.revision_history),
        }


@dataclass
class WorldRelation:
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def to_record(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "relation_type": self.relation_type,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }


@dataclass
class WorldEvent:
    event_id: str
    event_type: str
    description: str
    entity_ids: List[str]
    timestamp: float
    provenance: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "description": self.description,
            "entity_ids": list(self.entity_ids),
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


@dataclass
class WorldProcess:
    process_id: str
    label: str
    state: str
    entity_ids: List[str] = field(default_factory=list)
    continuity_hash: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "label": self.label,
            "state": self.state,
            "entity_ids": list(self.entity_ids),
            "continuity_hash": self.continuity_hash,
        }


@dataclass
class WorldConstraint:
    constraint_id: str
    detail: str
    scope: str
    category: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "detail": self.detail,
            "scope": self.scope,
            "category": self.category,
        }


@dataclass
class WorldBoundary:
    boundary_id: str
    owner_class: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "owner_class": self.owner_class,
            "detail": self.detail,
        }


@dataclass
class WorldObservation:
    observation_id: str
    entity_type: str
    property_name: str
    value: Any
    category: str
    source: str
    provenance: str
    timestamp: float = field(default_factory=now_ts)
    entity_id: str = ""
    identity_hints: Dict[str, Any] = field(default_factory=dict)
    visibility: str = "SHARED_PROJECT"
    uncertainty: float = 0.0
    contradiction_links: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.category not in PROPERTY_CATEGORIES:
            raise ValueError(f"Unsupported observation category: {self.category}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "entity_type": self.entity_type,
            "property_name": self.property_name,
            "value": self.value,
            "category": self.category,
            "source": self.source,
            "provenance": self.provenance,
            "timestamp": self.timestamp,
            "entity_id": self.entity_id,
            "identity_hints": dict(self.identity_hints),
            "visibility": self.visibility,
            "uncertainty": self.uncertainty,
            "contradiction_links": list(self.contradiction_links),
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "WorldObservation":
        return cls(
            observation_id=str(payload.get("observation_id", "")),
            entity_type=str(payload.get("entity_type", "")),
            property_name=str(payload.get("property_name", "")),
            value=payload.get("value"),
            category=str(payload.get("category", "OBSERVED")),
            source=str(payload.get("source", "")),
            provenance=str(payload.get("provenance", "")),
            timestamp=float(payload.get("timestamp", now_ts())),
            entity_id=str(payload.get("entity_id", "")),
            identity_hints=dict(payload.get("identity_hints", {})),
            visibility=str(payload.get("visibility", "SHARED_PROJECT")),
            uncertainty=float(payload.get("uncertainty", 0.0)),
            contradiction_links=list(payload.get("contradiction_links", [])),
        )


@dataclass
class WorldHypothesis:
    hypothesis_id: str
    detail: str
    evidence: List[str]
    status: str = "UNRESOLVED"

    def to_record(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "detail": self.detail,
            "evidence": list(self.evidence),
            "status": self.status,
        }


@dataclass
class WorldPrediction:
    prediction_id: str
    entity_id: str
    property_name: str
    expected_value: Any
    horizon: str
    source_model: str
    uncertainty: float = 0.25
    status: str = "UNRESOLVED"

    def to_record(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "entity_id": self.entity_id,
            "property_name": self.property_name,
            "expected_value": self.expected_value,
            "horizon": self.horizon,
            "source_model": self.source_model,
            "uncertainty": self.uncertainty,
            "status": self.status,
        }


@dataclass
class WorldTransition:
    transition_id: str
    entity_id: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "entity_id": self.entity_id,
            "before_state": dict(self.before_state),
            "after_state": dict(self.after_state),
            "reason": self.reason,
        }


@dataclass
class WorldRevision:
    revision_id: str
    trigger: str
    reason: str
    evidence: List[str]
    affected_entity_ids: List[str]
    rollback_to: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "trigger": self.trigger,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "affected_entity_ids": list(self.affected_entity_ids),
            "rollback_to": self.rollback_to,
        }


@dataclass
class EntityIdentity:
    entity_id: str
    stable_keys: Dict[str, str]
    entity_type: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "stable_keys": dict(self.stable_keys),
            "entity_type": self.entity_type,
        }


@dataclass
class EntityObservation:
    observation_id: str
    entity_type: str
    stable_keys: Dict[str, str]
    observed_name: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "entity_type": self.entity_type,
            "stable_keys": dict(self.stable_keys),
            "observed_name": self.observed_name,
        }


@dataclass
class EntityMatch:
    entity_id: str
    observation_id: str
    confidence: float
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "observation_id": self.observation_id,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class EntitySplit:
    source_entity_id: str
    new_entity_ids: List[str]
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "source_entity_id": self.source_entity_id,
            "new_entity_ids": list(self.new_entity_ids),
            "reason": self.reason,
        }


@dataclass
class EntityMerge:
    merged_entity_ids: List[str]
    target_entity_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "merged_entity_ids": list(self.merged_entity_ids),
            "target_entity_id": self.target_entity_id,
            "reason": self.reason,
        }


@dataclass
class EntityDisappearance:
    entity_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"entity_id": self.entity_id, "reason": self.reason}


@dataclass
class EntityReappearance:
    entity_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"entity_id": self.entity_id, "reason": self.reason}


@dataclass
class ProcessIdentity:
    process_id: str
    stable_keys: Dict[str, str]
    label: str

    def to_record(self) -> Dict[str, Any]:
        return {"process_id": self.process_id, "stable_keys": dict(self.stable_keys), "label": self.label}


@dataclass
class ProcessContinuation:
    process_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"process_id": self.process_id, "reason": self.reason}


@dataclass
class ProcessTermination:
    process_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"process_id": self.process_id, "reason": self.reason}


@dataclass
class IdentityReceipt:
    matches: List[EntityMatch] = field(default_factory=list)
    splits: List[EntitySplit] = field(default_factory=list)
    merges: List[EntityMerge] = field(default_factory=list)
    disappearances: List[EntityDisappearance] = field(default_factory=list)
    reappearances: List[EntityReappearance] = field(default_factory=list)
    process_continuations: List[ProcessContinuation] = field(default_factory=list)
    process_terminations: List[ProcessTermination] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "matches": _record(self.matches),
            "splits": _record(self.splits),
            "merges": _record(self.merges),
            "disappearances": _record(self.disappearances),
            "reappearances": _record(self.reappearances),
            "process_continuations": _record(self.process_continuations),
            "process_terminations": _record(self.process_terminations),
        }


@dataclass
class WorldEntity:
    entity_id: WorldEntityID
    entity_type: str
    source: str
    provenance: str
    observed_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    inferred_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    predicted_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    simulated_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    remembered_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    assumed_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    policy_defined_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    unknown_properties: Dict[str, WorldProperty] = field(default_factory=dict)
    prediction_state: Dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.0
    temporal_validity: Dict[str, float] = field(default_factory=dict)
    contradiction_links: List[str] = field(default_factory=list)
    participant_visibility: str = "SHARED_PROJECT"
    revision_history: List[str] = field(default_factory=list)

    def set_property(self, prop: WorldProperty) -> None:
        buckets = {
            "OBSERVED": self.observed_properties,
            "INFERRED": self.inferred_properties,
            "PREDICTED": self.predicted_properties,
            "SIMULATED": self.simulated_properties,
            "REMEMBERED": self.remembered_properties,
            "ASSUMED": self.assumed_properties,
            "POLICY_DEFINED": self.policy_defined_properties,
            "UNKNOWN": self.unknown_properties,
        }
        buckets[prop.category][prop.name] = prop
        self.uncertainty = max(self.uncertainty, prop.uncertainty)
        self.temporal_validity[prop.name] = prop.temporal_validity.get("valid_until", 0.0)

    def to_record(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id.to_record(),
            "entity_type": self.entity_type,
            "source": self.source,
            "provenance": self.provenance,
            "observed_properties": _record(self.observed_properties),
            "inferred_properties": _record(self.inferred_properties),
            "predicted_properties": _record(self.predicted_properties),
            "simulated_properties": _record(self.simulated_properties),
            "remembered_properties": _record(self.remembered_properties),
            "assumed_properties": _record(self.assumed_properties),
            "policy_defined_properties": _record(self.policy_defined_properties),
            "unknown_properties": _record(self.unknown_properties),
            "prediction_state": dict(self.prediction_state),
            "uncertainty": self.uncertainty,
            "temporal_validity": dict(self.temporal_validity),
            "contradiction_links": list(self.contradiction_links),
            "participant_visibility": self.participant_visibility,
            "revision_history": list(self.revision_history),
        }


@dataclass
class WorldSnapshot:
    entities: List[WorldEntity]
    relations: List[WorldRelation]
    events: List[WorldEvent]
    processes: List[WorldProcess]
    revisions: List[WorldRevision]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entities": _record(self.entities),
            "relations": _record(self.relations),
            "events": _record(self.events),
            "processes": _record(self.processes),
            "revisions": _record(self.revisions),
        }


@dataclass
class WorldReceipt:
    admitted_entity_ids: List[str]
    observations: List[WorldObservation]
    identity: IdentityReceipt
    revisions: List[WorldRevision]
    snapshot: WorldSnapshot

    def to_record(self) -> Dict[str, Any]:
        return {
            "admitted_entity_ids": list(self.admitted_entity_ids),
            "observations": _record(self.observations),
            "identity": self.identity.to_record(),
            "revisions": _record(self.revisions),
            "snapshot": self.snapshot.to_record(),
        }


class WorldModel:
    def __init__(self) -> None:
        self.entities: Dict[str, WorldEntity] = {}
        self.identity_keys: Dict[str, str] = {}
        self.relations: List[WorldRelation] = []
        self.events: List[WorldEvent] = []
        self.processes: Dict[str, WorldProcess] = {}
        self.revisions: List[WorldRevision] = []
        self.seen_observation_ids: set[str] = set()

    def _identity_key(self, entity_type: str, hints: Dict[str, Any]) -> str:
        stable = {key: str(value) for key, value in sorted(hints.items()) if value not in {"", None}}
        return stable_hash({"entity_type": entity_type, "stable": stable}) if stable else ""

    def _default_entity_id(self, observation: WorldObservation) -> str:
        return f"{observation.entity_type.lower()}-{stable_hash([observation.source, observation.provenance, observation.property_name])[:12]}"

    def _resolve_entity_id(self, observation: WorldObservation, identity: IdentityReceipt) -> str:
        if observation.entity_id:
            return observation.entity_id
        identity_key = self._identity_key(observation.entity_type, observation.identity_hints)
        if identity_key and identity_key in self.identity_keys:
            entity_id = self.identity_keys[identity_key]
            identity.matches.append(EntityMatch(entity_id, observation.observation_id, 1.0, "stable identity hint"))
            return entity_id
        entity_id = self._default_entity_id(observation)
        if identity_key:
            self.identity_keys[identity_key] = entity_id
        return entity_id

    def observe(self, observations: List[WorldObservation]) -> WorldReceipt:
        identity = IdentityReceipt()
        admitted: List[str] = []
        for observation in observations:
            if observation.observation_id in self.seen_observation_ids:
                continue
            self.seen_observation_ids.add(observation.observation_id)
            entity_id = self._resolve_entity_id(observation, identity)
            entity = self.entities.get(entity_id)
            if entity is None:
                entity = WorldEntity(
                    entity_id=WorldEntityID(entity_id),
                    entity_type=observation.entity_type,
                    source=observation.source,
                    provenance=observation.provenance,
                    participant_visibility=observation.visibility,
                )
                self.entities[entity_id] = entity
            prop = WorldProperty(
                name=observation.property_name,
                value=observation.value,
                category=observation.category,
                source=observation.source,
                provenance=observation.provenance,
                uncertainty=observation.uncertainty,
                temporal_validity={"observed_at": observation.timestamp},
                contradiction_links=list(observation.contradiction_links),
                revision_history=list(entity.revision_history),
            )
            entity.set_property(prop)
            if observation.contradiction_links:
                entity.contradiction_links.extend(item for item in observation.contradiction_links if item not in entity.contradiction_links)
            admitted.append(entity_id)
            self.events.append(
                WorldEvent(
                    event_id=f"world-event-{len(self.events) + 1:04d}",
                    event_type="WORLD_OBSERVATION",
                    description=f"{observation.property_name} updated",
                    entity_ids=[entity_id],
                    timestamp=observation.timestamp,
                    provenance=observation.provenance,
                )
            )
        return WorldReceipt(
            admitted_entity_ids=admitted,
            observations=observations,
            identity=identity,
            revisions=[],
            snapshot=self.snapshot(),
        )

    def mark_prediction(self, prediction: WorldPrediction) -> None:
        entity = self.entities.get(prediction.entity_id)
        if entity is None:
            entity = WorldEntity(
                entity_id=WorldEntityID(prediction.entity_id),
                entity_type="ABSTRACT_OBJECT",
                source=prediction.source_model,
                provenance="prediction-engine",
            )
            self.entities[prediction.entity_id] = entity
        entity.set_property(
            WorldProperty(
                name=prediction.property_name,
                value=prediction.expected_value,
                category="PREDICTED",
                source=prediction.source_model,
                provenance="prediction-engine",
                uncertainty=prediction.uncertainty,
            )
        )
        entity.prediction_state[prediction.property_name] = prediction.to_record()

    def revise(self, *, trigger: str, reason: str, evidence: List[str], affected_entity_ids: List[str]) -> WorldRevision:
        revision = WorldRevision(
            revision_id=f"world-revision-{len(self.revisions) + 1:04d}",
            trigger=trigger,
            reason=reason,
            evidence=evidence,
            affected_entity_ids=affected_entity_ids,
            rollback_to=self.revisions[-1].revision_id if self.revisions else "",
        )
        self.revisions.append(revision)
        for entity_id in affected_entity_ids:
            if entity_id in self.entities:
                self.entities[entity_id].revision_history.append(revision.revision_id)
        return revision

    def snapshot(self) -> WorldSnapshot:
        return WorldSnapshot(
            entities=list(self.entities.values()),
            relations=list(self.relations),
            events=list(self.events),
            processes=list(self.processes.values()),
            revisions=list(self.revisions),
        )

    def export(self) -> Dict[str, Any]:
        return self.snapshot().to_record()


__all__ = [
    "EntityDisappearance",
    "EntityIdentity",
    "EntityMatch",
    "EntityMerge",
    "EntityObservation",
    "EntityReappearance",
    "EntitySplit",
    "IdentityReceipt",
    "ProcessContinuation",
    "ProcessIdentity",
    "ProcessTermination",
    "WorldBoundary",
    "WorldConstraint",
    "WorldEntity",
    "WorldEntityID",
    "WorldEvent",
    "WorldHypothesis",
    "WorldModel",
    "WorldObservation",
    "WorldPrediction",
    "WorldProcess",
    "WorldProperty",
    "WorldReceipt",
    "WorldRelation",
    "WorldRevision",
    "WorldSnapshot",
    "WorldTransition",
]
