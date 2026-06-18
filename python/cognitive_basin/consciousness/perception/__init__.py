"""
Typed percept and constant-field contracts plus bounded field logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..common import clamp, now_ts, stable_hash


PerceptID = str
ConstantID = str


class PerceptSource(Enum):
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"
    CONNECTOR = "CONNECTOR"
    PROVIDER = "PROVIDER"
    MEMORY = "MEMORY"
    EXECUTION = "EXECUTION"
    FILESYSTEM = "FILESYSTEM"
    POLICY = "POLICY"
    SIMULATION = "SIMULATION"
    UNKNOWN = "UNKNOWN"


class PerceptModality(Enum):
    TEXT = "text"
    STRUCTURED_DATA = "structured_data"
    CODE = "code"
    FILESYSTEM_STATE = "filesystem_state"
    EXECUTION_OUTPUT = "execution_output"
    CONNECTOR_STATE = "connector_state"
    TEMPORAL_EVENT = "temporal_event"
    NUMERICAL_SIGNAL = "numerical_signal"
    IMAGE_METADATA = "image_metadata"
    HUMAN_INSTRUCTION = "human_instruction"
    SYSTEM_CONSTRAINT = "system_constraint"
    MEMORY_RETRIEVAL = "memory_retrieval"
    MODEL_OUTPUT = "model_output"
    SIMULATED_ENVIRONMENT_STATE = "simulated_environment_state"


class PerceptChannel(Enum):
    USER = "USER"
    SESSION = "SESSION"
    CONNECTOR = "CONNECTOR"
    MEMORY = "MEMORY"
    EVALUATION = "EVALUATION"
    GOVERNANCE = "GOVERNANCE"
    EXECUTION = "EXECUTION"
    SYSTEM = "SYSTEM"


@dataclass
class PerceptFeature:
    key: str
    value: Any
    confidence: float = 1.0

    def to_record(self) -> Dict[str, Any]:
        return {"key": self.key, "value": self.value, "confidence": self.confidence}


@dataclass
class PerceptRelation:
    relation_type: str
    target_percept_id: str
    weight: float = 1.0

    def to_record(self) -> Dict[str, Any]:
        return {"relation_type": self.relation_type, "target_percept_id": self.target_percept_id, "weight": self.weight}


@dataclass
class PerceptReliability:
    current: float
    history: List[float] = field(default_factory=list)
    source_dependence: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {
            "current": self.current,
            "history": list(self.history),
            "source_dependence": self.source_dependence,
        }


@dataclass
class PerceptConflict:
    conflict_id: str
    left_percept_id: str
    right_percept_id: str
    reason: str
    active: bool = True

    def to_record(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "left_percept_id": self.left_percept_id,
            "right_percept_id": self.right_percept_id,
            "reason": self.reason,
            "active": self.active,
        }


@dataclass
class PerceptFusion:
    fused_percept_id: str
    supporting_ids: List[str] = field(default_factory=list)
    minority_ids: List[str] = field(default_factory=list)
    duplicate_ids: List[str] = field(default_factory=list)
    correlated_ids: List[str] = field(default_factory=list)
    disagreements: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {
            "fused_percept_id": self.fused_percept_id,
            "supporting_ids": list(self.supporting_ids),
            "minority_ids": list(self.minority_ids),
            "duplicate_ids": list(self.duplicate_ids),
            "correlated_ids": list(self.correlated_ids),
            "disagreements": list(self.disagreements),
            "confidence": self.confidence,
        }


@dataclass
class PerceptHistory:
    observation_count: int = 0
    last_seen_at: float = 0.0
    content_hashes: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "observation_count": self.observation_count,
            "last_seen_at": self.last_seen_at,
            "content_hashes": list(self.content_hashes),
        }


@dataclass
class PerceptDecay:
    half_life_cycles: int = 3
    max_age_cycles: int = 8
    stale_after_s: float = 900.0
    decay_rate: float = 0.25

    def to_record(self) -> Dict[str, Any]:
        return {
            "half_life_cycles": self.half_life_cycles,
            "max_age_cycles": self.max_age_cycles,
            "stale_after_s": self.stale_after_s,
            "decay_rate": self.decay_rate,
        }


@dataclass
class PerceptPrediction:
    prediction_id: str
    subject: str
    expected_hash: str
    confidence: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "subject": self.subject,
            "expected_hash": self.expected_hash,
            "confidence": self.confidence,
        }


@dataclass
class PerceptResidual:
    residual_id: str
    subject: str
    observed_hash: str
    divergence_reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "residual_id": self.residual_id,
            "subject": self.subject,
            "observed_hash": self.observed_hash,
            "divergence_reason": self.divergence_reason,
        }


@dataclass
class PerceptBoundary:
    boundary_id: str
    boundary_type: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"boundary_id": self.boundary_id, "boundary_type": self.boundary_type, "detail": self.detail}


@dataclass
class PerceptFrame:
    frame_id: str
    percept_ids: List[str]
    created_at: float
    source_count: int

    def to_record(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "percept_ids": list(self.percept_ids),
            "created_at": self.created_at,
            "source_count": self.source_count,
        }


@dataclass
class Percept:
    percept_id: PerceptID
    source: str
    source_type: PerceptSource
    timestamp: float
    observed_content_hash: str
    modality: PerceptModality
    channel: PerceptChannel
    content: Any
    confidence: float
    reliability: PerceptReliability
    privacy_classification: str
    provenance: str
    novelty: float
    salience: float
    purpose_relevance: float
    contradiction_links: List[str] = field(default_factory=list)
    prediction_links: List[str] = field(default_factory=list)
    verification_state: str = "OBSERVATION"
    decay_policy: PerceptDecay = field(default_factory=PerceptDecay)
    retention_policy: str = "SESSION_WORKING"
    features: List[PerceptFeature] = field(default_factory=list)
    relations: List[PerceptRelation] = field(default_factory=list)
    cycle_index: int = 0
    stale: bool = False

    def topic(self) -> str:
        for feature in self.features:
            if feature.key == "topic":
                return str(feature.value)
        return self.percept_id

    def to_record(self) -> Dict[str, Any]:
        return {
            "percept_id": self.percept_id,
            "source": self.source,
            "source_type": self.source_type.value,
            "timestamp": self.timestamp,
            "observed_content_hash": self.observed_content_hash,
            "modality": self.modality.value,
            "channel": self.channel.value,
            "content": self.content,
            "confidence": self.confidence,
            "reliability": self.reliability.to_record(),
            "privacy_classification": self.privacy_classification,
            "provenance": self.provenance,
            "novelty": self.novelty,
            "salience": self.salience,
            "purpose_relevance": self.purpose_relevance,
            "contradiction_links": list(self.contradiction_links),
            "prediction_links": list(self.prediction_links),
            "verification_state": self.verification_state,
            "decay_policy": self.decay_policy.to_record(),
            "retention_policy": self.retention_policy,
            "features": [feature.to_record() for feature in self.features],
            "relations": [relation.to_record() for relation in self.relations],
            "cycle_index": self.cycle_index,
            "stale": self.stale,
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "Percept":
        return cls(
            percept_id=str(payload["percept_id"]),
            source=str(payload["source"]),
            source_type=PerceptSource(payload["source_type"]),
            timestamp=float(payload["timestamp"]),
            observed_content_hash=str(payload["observed_content_hash"]),
            modality=PerceptModality(payload["modality"]),
            channel=PerceptChannel(payload["channel"]),
            content=payload.get("content"),
            confidence=float(payload.get("confidence", 0.5)),
            reliability=PerceptReliability(**payload.get("reliability", {"current": 0.5})),
            privacy_classification=str(payload.get("privacy_classification", "restricted")),
            provenance=str(payload.get("provenance", "")),
            novelty=float(payload.get("novelty", 0.0)),
            salience=float(payload.get("salience", 0.0)),
            purpose_relevance=float(payload.get("purpose_relevance", 0.0)),
            contradiction_links=list(payload.get("contradiction_links", [])),
            prediction_links=list(payload.get("prediction_links", [])),
            verification_state=str(payload.get("verification_state", "OBSERVATION")),
            decay_policy=PerceptDecay(**payload.get("decay_policy", {})),
            retention_policy=str(payload.get("retention_policy", "SESSION_WORKING")),
            features=[PerceptFeature(**item) for item in payload.get("features", [])],
            relations=[PerceptRelation(**item) for item in payload.get("relations", [])],
            cycle_index=int(payload.get("cycle_index", 0)),
            stale=bool(payload.get("stale", False)),
        )


@dataclass
class PerceptReceipt:
    admitted_ids: List[str] = field(default_factory=list)
    duplicate_ids: List[str] = field(default_factory=list)
    stale_ids: List[str] = field(default_factory=list)
    conflict_ids: List[str] = field(default_factory=list)
    frame: Optional[PerceptFrame] = None

    def to_record(self) -> Dict[str, Any]:
        return {
            "admitted_ids": list(self.admitted_ids),
            "duplicate_ids": list(self.duplicate_ids),
            "stale_ids": list(self.stale_ids),
            "conflict_ids": list(self.conflict_ids),
            "frame": self.frame.to_record() if self.frame else None,
        }


class ConstantClass(Enum):
    MATHEMATICAL_INVARIANT = "mathematical_invariant"
    SYSTEM_CONSTRAINT = "system_constraint"
    POLICY_BOUNDARY = "policy_boundary"
    PARTICIPANT_INSTRUCTION = "participant_instruction"
    REPOSITORY_INVARIANT = "repository_invariant"
    ENVIRONMENT_FACT = "environment_fact"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_BOUNDARY = "security_boundary"
    TEMPORAL_CONDITION = "temporal_condition"
    CAPABILITY_BOUNDARY = "capability_boundary"
    PHYSICAL_OR_SIMULATED_RULE = "physical_or_simulated_rule"
    UNCERTAINTY_BOUND = "uncertainty_bound"


@dataclass
class ConstantValue:
    value: Any
    unit: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {"value": self.value, "unit": self.unit}


@dataclass
class ConstantDomain:
    domain_id: str
    domain_type: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"domain_id": self.domain_id, "domain_type": self.domain_type, "detail": self.detail}


@dataclass
class ConstantScope:
    scope_id: str
    scope_type: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"scope_id": self.scope_id, "scope_type": self.scope_type, "detail": self.detail}


@dataclass
class ConstantSource:
    source: str
    source_type: str
    provenance: str

    def to_record(self) -> Dict[str, Any]:
        return {"source": self.source, "source_type": self.source_type, "provenance": self.provenance}


@dataclass
class ConstantEvidence:
    evidence_id: str
    detail: str
    confidence: float = 1.0

    def to_record(self) -> Dict[str, Any]:
        return {"evidence_id": self.evidence_id, "detail": self.detail, "confidence": self.confidence}


@dataclass
class ConstantRevision:
    revision_id: str
    reason: str
    timestamp: float

    def to_record(self) -> Dict[str, Any]:
        return {"revision_id": self.revision_id, "reason": self.reason, "timestamp": self.timestamp}


@dataclass
class ConstantConflict:
    conflict_id: str
    left_constant_id: str
    right_constant_id: str
    reason: str
    unresolved: bool = True

    def to_record(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "left_constant_id": self.left_constant_id,
            "right_constant_id": self.right_constant_id,
            "reason": self.reason,
            "unresolved": self.unresolved,
        }


@dataclass
class ConstantExpiry:
    valid_from: float
    valid_until: float = 0.0

    def is_expired(self, now: float) -> bool:
        return bool(self.valid_until) and now > self.valid_until

    def to_record(self) -> Dict[str, Any]:
        return {"valid_from": self.valid_from, "valid_until": self.valid_until}


@dataclass
class Constant:
    constant_id: ConstantID
    constant_class: ConstantClass
    value: ConstantValue
    domain: ConstantDomain
    scope: ConstantScope
    source: ConstantSource
    evidence: List[ConstantEvidence] = field(default_factory=list)
    confidence: float = 1.0
    validity_interval: ConstantExpiry = field(default_factory=lambda: ConstantExpiry(valid_from=now_ts()))
    revision_history: List[ConstantRevision] = field(default_factory=list)
    contradiction_state: str = "SUPPORTED"
    expiry: Optional[ConstantExpiry] = None
    applicability_conditions: List[str] = field(default_factory=list)
    category: str = "constraint"

    def to_record(self) -> Dict[str, Any]:
        return {
            "constant_id": self.constant_id,
            "constant_class": self.constant_class.value,
            "value": self.value.to_record(),
            "domain": self.domain.to_record(),
            "scope": self.scope.to_record(),
            "source": self.source.to_record(),
            "evidence": [item.to_record() for item in self.evidence],
            "confidence": self.confidence,
            "validity_interval": self.validity_interval.to_record(),
            "revision_history": [item.to_record() for item in self.revision_history],
            "contradiction_state": self.contradiction_state,
            "expiry": self.expiry.to_record() if self.expiry else None,
            "applicability_conditions": list(self.applicability_conditions),
            "category": self.category,
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "Constant":
        return cls(
            constant_id=str(payload["constant_id"]),
            constant_class=ConstantClass(payload["constant_class"]),
            value=ConstantValue(**payload["value"]),
            domain=ConstantDomain(**payload["domain"]),
            scope=ConstantScope(**payload["scope"]),
            source=ConstantSource(**payload["source"]),
            evidence=[ConstantEvidence(**item) for item in payload.get("evidence", [])],
            confidence=float(payload.get("confidence", 1.0)),
            validity_interval=ConstantExpiry(**payload.get("validity_interval", {"valid_from": now_ts()})),
            revision_history=[ConstantRevision(**item) for item in payload.get("revision_history", [])],
            contradiction_state=str(payload.get("contradiction_state", "SUPPORTED")),
            expiry=ConstantExpiry(**payload["expiry"]) if payload.get("expiry") else None,
            applicability_conditions=list(payload.get("applicability_conditions", [])),
            category=str(payload.get("category", "constraint")),
        )


@dataclass
class ConstantSet:
    constants: Dict[ConstantID, Constant] = field(default_factory=dict)
    conflicts: List[ConstantConflict] = field(default_factory=list)
    unresolved_ids: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "constants": {key: value.to_record() for key, value in self.constants.items()},
            "conflicts": [item.to_record() for item in self.conflicts],
            "unresolved_ids": list(self.unresolved_ids),
        }


@dataclass
class ConstantSnapshot:
    snapshot_id: str
    captured_at: float
    constant_ids: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at,
            "constant_ids": list(self.constant_ids),
        }


class ConstantField:
    def __init__(self) -> None:
        self.constants: Dict[str, Constant] = {}
        self.conflicts: List[ConstantConflict] = []

    def apply(self, constants: List[Constant], *, now: float | None = None) -> ConstantSnapshot:
        current = now if now is not None else now_ts()
        for constant in constants:
            if constant.expiry and constant.expiry.is_expired(current):
                constant.contradiction_state = "UNRESOLVED"
            self.constants[constant.constant_id] = constant
        self._refresh_conflicts(current)
        return ConstantSnapshot(
            snapshot_id=f"constant-snapshot-{stable_hash(sorted(self.constants.keys()))[:10]}",
            captured_at=current,
            constant_ids=sorted(self.constants.keys()),
        )

    def _refresh_conflicts(self, current: float) -> None:
        conflicts: List[ConstantConflict] = []
        constants = list(self.constants.values())
        unresolved_ids: set[str] = set()
        for constant in constants:
            if constant.expiry and constant.expiry.is_expired(current):
                constant.contradiction_state = "UNRESOLVED"
                unresolved_ids.add(constant.constant_id)
        for index, left in enumerate(constants):
            for right in constants[index + 1 :]:
                if left.scope.scope_id != right.scope.scope_id:
                    continue
                if left.domain.domain_id != right.domain.domain_id:
                    continue
                if left.value.value != right.value.value:
                    conflict = ConstantConflict(
                        conflict_id=f"constant-conflict-{stable_hash((left.constant_id, right.constant_id))[:10]}",
                        left_constant_id=left.constant_id,
                        right_constant_id=right.constant_id,
                        reason="same scope/domain but different values",
                    )
                    conflicts.append(conflict)
                    unresolved_ids.update({left.constant_id, right.constant_id})
                    left.contradiction_state = "CONTRADICTED"
                    right.contradiction_state = "CONTRADICTED"
        self.conflicts = conflicts

    def export(self) -> ConstantSet:
        unresolved_ids = [
            constant_id
            for constant_id, constant in self.constants.items()
            if constant.contradiction_state != "SUPPORTED"
        ]
        return ConstantSet(constants=dict(self.constants), conflicts=list(self.conflicts), unresolved_ids=unresolved_ids)


class PerceptualField:
    def __init__(self) -> None:
        self.percepts: Dict[str, Percept] = {}
        self.frames: List[PerceptFrame] = []
        self.conflicts: List[PerceptConflict] = []
        self.fusions: List[PerceptFusion] = []
        self.history = PerceptHistory()

    def ingest(self, percepts: List[Percept], *, cycle_index: int, now: float | None = None) -> PerceptReceipt:
        current = now if now is not None else now_ts()
        admitted_ids: List[str] = []
        duplicate_ids: List[str] = []
        stale_ids: List[str] = []
        for percept in percepts:
            percept.cycle_index = cycle_index
            existing = next(
                (
                    item
                    for item in self.percepts.values()
                    if item.observed_content_hash == percept.observed_content_hash and item.source == percept.source
                ),
                None,
            )
            if existing is not None:
                duplicate_ids.append(percept.percept_id)
                percept.novelty = 0.0
            else:
                admitted_ids.append(percept.percept_id)
                self.percepts[percept.percept_id] = percept
            age_s = max(0.0, current - percept.timestamp)
            max_age = percept.decay_policy.stale_after_s
            percept.stale = age_s > max_age or max(0, cycle_index - percept.cycle_index) > percept.decay_policy.max_age_cycles
            if percept.stale:
                stale_ids.append(percept.percept_id)
                percept.salience = clamp(percept.salience * (1.0 - percept.decay_policy.decay_rate))
        self.history.observation_count += len(percepts)
        self.history.last_seen_at = current
        self.history.content_hashes.extend(item.observed_content_hash for item in percepts)
        frame = PerceptFrame(
            frame_id=f"frame-{stable_hash((cycle_index, admitted_ids, duplicate_ids))[:10]}",
            percept_ids=[item.percept_id for item in percepts],
            created_at=current,
            source_count=len({item.source for item in percepts}),
        )
        self.frames.append(frame)
        self._refresh_conflicts_and_fusions()
        return PerceptReceipt(
            admitted_ids=admitted_ids,
            duplicate_ids=duplicate_ids,
            stale_ids=stale_ids,
            conflict_ids=[item.conflict_id for item in self.conflicts],
            frame=frame,
        )

    def _refresh_conflicts_and_fusions(self) -> None:
        self.conflicts = []
        groups: Dict[str, List[Percept]] = {}
        for percept in self.percepts.values():
            groups.setdefault(percept.topic(), []).append(percept)
        fusions: List[PerceptFusion] = []
        for topic, items in groups.items():
            hashes = {item.observed_content_hash for item in items}
            source_names = [item.source for item in items]
            duplicate_ids = [item.percept_id for item in items if source_names.count(item.source) > 1]
            correlated_ids = [item.percept_id for item in items if item.reliability.source_dependence > 0.5]
            minority_ids: List[str] = []
            if len(hashes) > 1:
                majority_hash = max(hashes, key=lambda candidate: sum(1 for item in items if item.observed_content_hash == candidate))
                minority_ids = [item.percept_id for item in items if item.observed_content_hash != majority_hash]
                for left_index, left in enumerate(items):
                    for right in items[left_index + 1 :]:
                        if left.observed_content_hash != right.observed_content_hash:
                            conflict = PerceptConflict(
                                conflict_id=f"percept-conflict-{stable_hash((left.percept_id, right.percept_id))[:10]}",
                                left_percept_id=left.percept_id,
                                right_percept_id=right.percept_id,
                                reason=f"topic {topic} has conflicting observations",
                            )
                            left.contradiction_links.append(conflict.conflict_id)
                            right.contradiction_links.append(conflict.conflict_id)
                            self.conflicts.append(conflict)
            confidence = clamp(sum(item.confidence for item in items) / max(1, len(items)))
            fusions.append(
                PerceptFusion(
                    fused_percept_id=f"fusion-{stable_hash((topic, sorted(item.percept_id for item in items)))[:10]}",
                    supporting_ids=[item.percept_id for item in items],
                    minority_ids=minority_ids,
                    duplicate_ids=sorted(set(duplicate_ids)),
                    correlated_ids=sorted(set(correlated_ids)),
                    disagreements=[conflict.conflict_id for conflict in self.conflicts if topic in conflict.reason],
                    confidence=confidence,
                )
            )
        self.fusions = fusions

    def export(self) -> Dict[str, Any]:
        return {
            "percepts": {key: value.to_record() for key, value in self.percepts.items()},
            "frames": [item.to_record() for item in self.frames],
            "conflicts": [item.to_record() for item in self.conflicts],
            "fusions": [item.to_record() for item in self.fusions],
            "history": self.history.to_record(),
        }


__all__ = [
    "Constant",
    "ConstantClass",
    "ConstantConflict",
    "ConstantDomain",
    "ConstantEvidence",
    "ConstantExpiry",
    "ConstantField",
    "ConstantID",
    "ConstantRevision",
    "ConstantScope",
    "ConstantSet",
    "ConstantSnapshot",
    "ConstantSource",
    "ConstantValue",
    "Percept",
    "PerceptBoundary",
    "PerceptChannel",
    "PerceptConflict",
    "PerceptDecay",
    "PerceptFeature",
    "PerceptFrame",
    "PerceptFusion",
    "PerceptHistory",
    "PerceptID",
    "PerceptModality",
    "PerceptPrediction",
    "PerceptReceipt",
    "PerceptRelation",
    "PerceptReliability",
    "PerceptResidual",
    "PerceptSource",
    "PerceptualField",
]
