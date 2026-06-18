"""
Governed memory contracts for BasinLab and EphUX continuity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from packages.ternary.states import ActionState, EpistemicState

from ..privacy import RetentionClass, SensitivityLevel, VisibilityScope


@dataclass
class MemoryFragment:
    fragment_id: str
    text: str
    content_hash: str
    provenance: str

    def to_record(self) -> Dict[str, object]:
        return {
            "fragment_id": self.fragment_id,
            "text": self.text,
            "content_hash": self.content_hash,
            "provenance": self.provenance,
        }


@dataclass
class MemoryPurposeLink:
    purpose: str
    relevance: float = 1.0
    provenance: str = ""

    def to_record(self) -> Dict[str, object]:
        return {"purpose": self.purpose, "relevance": self.relevance, "provenance": self.provenance}


@dataclass
class MemoryEvidenceLink:
    evidence_id: str
    detail: str
    supports: bool = True
    provenance: str = ""

    def to_record(self) -> Dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "detail": self.detail,
            "supports": self.supports,
            "provenance": self.provenance,
        }


@dataclass
class MemoryContradictionLink:
    contradiction_id: str
    detail: str
    provenance: str = ""
    active: bool = True

    def to_record(self) -> Dict[str, object]:
        return {
            "contradiction_id": self.contradiction_id,
            "detail": self.detail,
            "provenance": self.provenance,
            "active": self.active,
        }


@dataclass
class MemoryAssociationLink:
    memory_id: str
    relation: str
    weight: float = 0.0
    provenance: str = ""

    def to_record(self) -> Dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "relation": self.relation,
            "weight": self.weight,
            "provenance": self.provenance,
        }


@dataclass
class MemoryScarLink:
    scar_id: str
    claim_id: str
    provenance: str = ""

    def to_record(self) -> Dict[str, object]:
        return {"scar_id": self.scar_id, "claim_id": self.claim_id, "provenance": self.provenance}


@dataclass
class MemoryRecoveryLink:
    route_id: str
    status: str
    provenance: str = ""

    def to_record(self) -> Dict[str, object]:
        return {"route_id": self.route_id, "status": self.status, "provenance": self.provenance}


@dataclass
class MemoryPromotionEvent:
    reason: str
    evidence: List[str] = field(default_factory=list)
    timestamp: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {"reason": self.reason, "evidence": list(self.evidence), "timestamp": self.timestamp}


@dataclass
class MemoryDemotionEvent:
    reason: str
    evidence: List[str] = field(default_factory=list)
    timestamp: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {"reason": self.reason, "evidence": list(self.evidence), "timestamp": self.timestamp}


@dataclass
class MemoryPruningEvent:
    reason: str
    timestamp: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {"reason": self.reason, "timestamp": self.timestamp}


@dataclass
class MemoryRetentionDecision:
    decision: str
    reason: str
    retention_class: RetentionClass
    visibility_scope: VisibilityScope
    timestamp: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "retention_class": self.retention_class.value,
            "visibility_scope": self.visibility_scope.value,
            "timestamp": self.timestamp,
        }


@dataclass
class MemoryCompressionRecord:
    replay_reference: str
    snapshot_hash: str
    timestamp: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {
            "replay_reference": self.replay_reference,
            "snapshot_hash": self.snapshot_hash,
            "timestamp": self.timestamp,
        }


@dataclass
class MemoryReplayReceipt:
    memory_id: str
    session_id: str
    event_id: str
    replay_hash: str
    verified: bool
    checked_at: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "session_id": self.session_id,
            "event_id": self.event_id,
            "replay_hash": self.replay_hash,
            "verified": self.verified,
            "checked_at": self.checked_at,
        }


@dataclass
class MemoryRetrieval:
    memory_id: str
    score: float
    reasons: List[str] = field(default_factory=list)
    purpose_relevance: float = 0.0
    replay_value: float = 0.0
    verified_usefulness: float = 0.0
    source_quality: float = 0.0
    contradiction_penalty: float = 0.0
    recovery_bonus: float = 0.0
    recency_bonus: float = 0.0

    def to_record(self) -> Dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "score": self.score,
            "reasons": list(self.reasons),
            "purpose_relevance": self.purpose_relevance,
            "replay_value": self.replay_value,
            "verified_usefulness": self.verified_usefulness,
            "source_quality": self.source_quality,
            "contradiction_penalty": self.contradiction_penalty,
            "recovery_bonus": self.recovery_bonus,
            "recency_bonus": self.recency_bonus,
        }


@dataclass
class MemoryItem:
    memory_id: str
    origin_session_id: str
    origin_event_id: str
    participant: str
    purpose: str
    content_hash: str
    provenance: str
    evidence_status: str
    epistemic_state: EpistemicState
    action_state: ActionState
    sensitivity: SensitivityLevel
    visibility_scope: VisibilityScope
    retention_class: RetentionClass
    survival_reason: str
    contradiction_status: str = "none"
    memory_fragments: List[MemoryFragment] = field(default_factory=list)
    purpose_links: List[MemoryPurposeLink] = field(default_factory=list)
    evidence_links: List[MemoryEvidenceLink] = field(default_factory=list)
    contradiction_links: List[MemoryContradictionLink] = field(default_factory=list)
    association_links: List[MemoryAssociationLink] = field(default_factory=list)
    scar_links: List[MemoryScarLink] = field(default_factory=list)
    recovery_links: List[MemoryRecoveryLink] = field(default_factory=list)
    successful_uses: List[str] = field(default_factory=list)
    failed_uses: List[str] = field(default_factory=list)
    replay_references: List[str] = field(default_factory=list)
    promotion_history: List[MemoryPromotionEvent] = field(default_factory=list)
    demotion_history: List[MemoryDemotionEvent] = field(default_factory=list)
    pruning_history: List[MemoryPruningEvent] = field(default_factory=list)
    retention_decisions: List[MemoryRetentionDecision] = field(default_factory=list)
    compression_records: List[MemoryCompressionRecord] = field(default_factory=list)
    created_time: float = 0.0
    last_reviewed_time: float = 0.0
    pruned: bool = False

    def to_record(self) -> Dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "origin_session_id": self.origin_session_id,
            "origin_event_id": self.origin_event_id,
            "participant": self.participant,
            "purpose": self.purpose,
            "content_hash": self.content_hash,
            "provenance": self.provenance,
            "evidence_status": self.evidence_status,
            "epistemic_state": self.epistemic_state.value,
            "action_state": self.action_state.value,
            "sensitivity": self.sensitivity.value,
            "visibility_scope": self.visibility_scope.value,
            "retention_class": self.retention_class.value,
            "survival_reason": self.survival_reason,
            "contradiction_status": self.contradiction_status,
            "memory_fragments": [fragment.to_record() for fragment in self.memory_fragments],
            "purpose_links": [link.to_record() for link in self.purpose_links],
            "evidence_links": [link.to_record() for link in self.evidence_links],
            "contradiction_links": [link.to_record() for link in self.contradiction_links],
            "association_links": [link.to_record() for link in self.association_links],
            "scar_links": [link.to_record() for link in self.scar_links],
            "recovery_links": [link.to_record() for link in self.recovery_links],
            "successful_uses": list(self.successful_uses),
            "failed_uses": list(self.failed_uses),
            "replay_references": list(self.replay_references),
            "promotion_history": [item.to_record() for item in self.promotion_history],
            "demotion_history": [item.to_record() for item in self.demotion_history],
            "pruning_history": [item.to_record() for item in self.pruning_history],
            "retention_decisions": [item.to_record() for item in self.retention_decisions],
            "compression_records": [item.to_record() for item in self.compression_records],
            "created_time": self.created_time,
            "last_reviewed_time": self.last_reviewed_time,
            "pruned": self.pruned,
        }

    @classmethod
    def from_record(cls, payload: Dict[str, object]) -> "MemoryItem":
        return cls(
            memory_id=str(payload["memory_id"]),
            origin_session_id=str(payload.get("origin_session_id", "")),
            origin_event_id=str(payload.get("origin_event_id", "")),
            participant=str(payload.get("participant", "UNKNOWN")),
            purpose=str(payload.get("purpose", "")),
            content_hash=str(payload.get("content_hash", "")),
            provenance=str(payload.get("provenance", "")),
            evidence_status=str(payload.get("evidence_status", "unresolved")),
            epistemic_state=EpistemicState(str(payload.get("epistemic_state", EpistemicState.UNRESOLVED.value))),
            action_state=ActionState(str(payload.get("action_state", ActionState.HOLD.value))),
            sensitivity=SensitivityLevel(str(payload.get("sensitivity", SensitivityLevel.MODERATE.value))),
            visibility_scope=VisibilityScope(str(payload.get("visibility_scope", VisibilityScope.SESSION_ONLY.value))),
            retention_class=RetentionClass(str(payload.get("retention_class", RetentionClass.SESSION_WORKING.value))),
            survival_reason=str(payload.get("survival_reason", "")),
            contradiction_status=str(payload.get("contradiction_status", "none")),
            memory_fragments=[
                MemoryFragment(
                    fragment_id=str(item["fragment_id"]),
                    text=str(item["text"]),
                    content_hash=str(item["content_hash"]),
                    provenance=str(item.get("provenance", "")),
                )
                for item in payload.get("memory_fragments", [])
            ],
            purpose_links=[
                MemoryPurposeLink(
                    purpose=str(item["purpose"]),
                    relevance=float(item.get("relevance", 1.0)),
                    provenance=str(item.get("provenance", "")),
                )
                for item in payload.get("purpose_links", [])
            ],
            evidence_links=[
                MemoryEvidenceLink(
                    evidence_id=str(item["evidence_id"]),
                    detail=str(item.get("detail", "")),
                    supports=bool(item.get("supports", True)),
                    provenance=str(item.get("provenance", "")),
                )
                for item in payload.get("evidence_links", [])
            ],
            contradiction_links=[
                MemoryContradictionLink(
                    contradiction_id=str(item["contradiction_id"]),
                    detail=str(item.get("detail", "")),
                    provenance=str(item.get("provenance", "")),
                    active=bool(item.get("active", True)),
                )
                for item in payload.get("contradiction_links", [])
            ],
            association_links=[
                MemoryAssociationLink(
                    memory_id=str(item["memory_id"]),
                    relation=str(item.get("relation", "")),
                    weight=float(item.get("weight", 0.0)),
                    provenance=str(item.get("provenance", "")),
                )
                for item in payload.get("association_links", [])
            ],
            scar_links=[
                MemoryScarLink(
                    scar_id=str(item["scar_id"]),
                    claim_id=str(item.get("claim_id", "")),
                    provenance=str(item.get("provenance", "")),
                )
                for item in payload.get("scar_links", [])
            ],
            recovery_links=[
                MemoryRecoveryLink(
                    route_id=str(item["route_id"]),
                    status=str(item.get("status", "")),
                    provenance=str(item.get("provenance", "")),
                )
                for item in payload.get("recovery_links", [])
            ],
            successful_uses=list(payload.get("successful_uses", [])),
            failed_uses=list(payload.get("failed_uses", [])),
            replay_references=list(payload.get("replay_references", [])),
            promotion_history=[
                MemoryPromotionEvent(
                    reason=str(item.get("reason", "")),
                    evidence=list(item.get("evidence", [])),
                    timestamp=float(item.get("timestamp", 0.0)),
                )
                for item in payload.get("promotion_history", [])
            ],
            demotion_history=[
                MemoryDemotionEvent(
                    reason=str(item.get("reason", "")),
                    evidence=list(item.get("evidence", [])),
                    timestamp=float(item.get("timestamp", 0.0)),
                )
                for item in payload.get("demotion_history", [])
            ],
            pruning_history=[
                MemoryPruningEvent(reason=str(item.get("reason", "")), timestamp=float(item.get("timestamp", 0.0)))
                for item in payload.get("pruning_history", [])
            ],
            retention_decisions=[
                MemoryRetentionDecision(
                    decision=str(item.get("decision", "retain")),
                    reason=str(item.get("reason", "")),
                    retention_class=RetentionClass(str(item.get("retention_class", RetentionClass.SESSION_WORKING.value))),
                    visibility_scope=VisibilityScope(str(item.get("visibility_scope", VisibilityScope.SESSION_ONLY.value))),
                    timestamp=float(item.get("timestamp", 0.0)),
                )
                for item in payload.get("retention_decisions", [])
            ],
            compression_records=[
                MemoryCompressionRecord(
                    replay_reference=str(item.get("replay_reference", "")),
                    snapshot_hash=str(item.get("snapshot_hash", "")),
                    timestamp=float(item.get("timestamp", 0.0)),
                )
                for item in payload.get("compression_records", [])
            ],
            created_time=float(payload.get("created_time", 0.0)),
            last_reviewed_time=float(payload.get("last_reviewed_time", 0.0)),
            pruned=bool(payload.get("pruned", False)),
        )
