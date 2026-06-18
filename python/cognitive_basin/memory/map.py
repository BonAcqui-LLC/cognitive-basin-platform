"""
Queryable FractalMemoryMap with auditable replay and retrieval.
"""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Dict, Iterable, List

from ..privacy import content_hash
from ..retention import decide_retention
from .contracts import (
    MemoryCompressionRecord,
    MemoryDemotionEvent,
    MemoryItem,
    MemoryPromotionEvent,
    MemoryPruningEvent,
    MemoryReplayReceipt,
    MemoryRetrieval,
)


def _merge_unique(left: Iterable[str], right: Iterable[str]) -> List[str]:
    merged: List[str] = []
    for value in list(left) + list(right):
        if value and value not in merged:
            merged.append(value)
    return merged


def _item_source_quality(item: MemoryItem) -> float:
    provenance = item.provenance.lower()
    if "human" in provenance or "local" in provenance:
        return 0.25
    if "import" in provenance or "api" in provenance:
        return 0.15
    return 0.05


class FractalMemoryMap:
    def __init__(self) -> None:
        self.items: Dict[str, MemoryItem] = {}
        self.events: List[Dict[str, object]] = []

    @property
    def nodes(self) -> Dict[str, MemoryItem]:
        return self.items

    def upsert(self, item: MemoryItem) -> MemoryItem:
        now = time.time()
        if not item.created_time:
            item.created_time = now
        item.last_reviewed_time = now
        if not item.content_hash and item.memory_fragments:
            item.content_hash = content_hash(" ".join(fragment.text for fragment in item.memory_fragments))

        existing = self.items.get(item.memory_id)
        if existing:
            item = replace(
                item,
                successful_uses=_merge_unique(existing.successful_uses, item.successful_uses),
                failed_uses=_merge_unique(existing.failed_uses, item.failed_uses),
                replay_references=_merge_unique(existing.replay_references, item.replay_references),
                created_time=existing.created_time,
                promotion_history=list(existing.promotion_history) + list(item.promotion_history),
                demotion_history=list(existing.demotion_history) + list(item.demotion_history),
                pruning_history=list(existing.pruning_history) + list(item.pruning_history),
                retention_decisions=list(existing.retention_decisions),
                compression_records=list(existing.compression_records) + list(item.compression_records),
            )

        decision = decide_retention(item)
        item.retention_decisions.append(decision)
        item.retention_class = decision.retention_class
        if decision.decision == "promote":
            item.promotion_history.append(
                MemoryPromotionEvent(reason=decision.reason, evidence=list(item.successful_uses), timestamp=decision.timestamp)
            )
        elif decision.decision == "demote":
            item.demotion_history.append(
                MemoryDemotionEvent(reason=decision.reason, evidence=list(item.failed_uses), timestamp=decision.timestamp)
            )
        self.items[item.memory_id] = item
        self.events.append({"type": "memory_upserted", "memory_id": item.memory_id, "decision": decision.decision})
        return item

    def record_use(self, memory_id: str, *, successful: bool, note: str) -> None:
        item = self.items[memory_id]
        if successful:
            item.successful_uses = _merge_unique(item.successful_uses, [note])
        else:
            item.failed_uses = _merge_unique(item.failed_uses, [note])
        item.last_reviewed_time = time.time()
        item.retention_decisions.append(decide_retention(item))
        self.events.append({"type": "memory_use_recorded", "memory_id": memory_id, "successful": successful})

    def prune(self, memory_id: str, reason: str) -> None:
        if memory_id not in self.items:
            return
        item = self.items[memory_id]
        item.pruned = True
        item.pruning_history.append(MemoryPruningEvent(reason=reason, timestamp=time.time()))
        self.events.append({"type": "memory_pruned", "memory_id": memory_id, "reason": reason})

    def attach_replay_reference(self, memory_id: str, reference: str, snapshot_hash: str = "") -> None:
        item = self.items[memory_id]
        item.replay_references = _merge_unique(item.replay_references, [reference])
        if snapshot_hash:
            item.compression_records.append(
                MemoryCompressionRecord(replay_reference=reference, snapshot_hash=snapshot_hash, timestamp=time.time())
            )
        self.events.append({"type": "memory_replay_attached", "memory_id": memory_id, "reference": reference})

    def retrieve(self, purpose: str, limit: int = 5) -> List[MemoryRetrieval]:
        normalized_purpose = purpose.lower().strip()
        scored: List[MemoryRetrieval] = []
        for item in self.items.values():
            purpose_relevance = max(
                [link.relevance for link in item.purpose_links if normalized_purpose and normalized_purpose in link.purpose.lower()]
                or ([1.0] if normalized_purpose and normalized_purpose in item.purpose.lower() else [0.0])
            )
            verified_usefulness = min(1.0, 0.35 * len(item.successful_uses))
            replay_value = min(1.0, 0.2 * len(item.replay_references))
            source_quality = _item_source_quality(item)
            contradiction_penalty = 0.4 if item.contradiction_status == "contradicted" else 0.15 * len(item.contradiction_links)
            recovery_bonus = 0.1 if item.recovery_links and item.contradiction_status != "contradicted" else 0.0
            age_s = max(0.0, time.time() - (item.last_reviewed_time or item.created_time or time.time()))
            recency_bonus = max(0.0, 0.15 - min(0.15, age_s / 86_400.0 * 0.05))
            score = (
                purpose_relevance
                + verified_usefulness
                + replay_value
                + source_quality
                + recovery_bonus
                + recency_bonus
                - contradiction_penalty
            )
            reasons = []
            if purpose_relevance:
                reasons.append("purpose relevance")
            if verified_usefulness:
                reasons.append("verified usefulness")
            if replay_value:
                reasons.append("replay value")
            if contradiction_penalty:
                reasons.append("contradiction penalty applied")
            scored.append(
                MemoryRetrieval(
                    memory_id=item.memory_id,
                    score=score,
                    reasons=reasons,
                    purpose_relevance=purpose_relevance,
                    replay_value=replay_value,
                    verified_usefulness=verified_usefulness,
                    source_quality=source_quality,
                    contradiction_penalty=contradiction_penalty,
                    recovery_bonus=recovery_bonus,
                    recency_bonus=recency_bonus,
                )
            )
        scored.sort(key=lambda item: (-item.score, item.memory_id))
        return scored[:limit]

    def replay_receipts(self, session_id: str, replay_hash: str) -> List[MemoryReplayReceipt]:
        receipts: List[MemoryReplayReceipt] = []
        checked_at = time.time()
        for item in self.items.values():
            receipts.append(
                MemoryReplayReceipt(
                    memory_id=item.memory_id,
                    session_id=session_id,
                    event_id=item.origin_event_id,
                    replay_hash=replay_hash,
                    verified=True,
                    checked_at=checked_at,
                )
            )
        return receipts

    def export_records(self) -> List[Dict[str, object]]:
        return [item.to_record() for _, item in sorted(self.items.items())]

    @classmethod
    def from_records(cls, records: Iterable[Dict[str, object]]) -> "FractalMemoryMap":
        memory_map = cls()
        for record in records:
            item = MemoryItem.from_record(record)
            memory_map.items[item.memory_id] = item
        return memory_map

    @classmethod
    def from_events(cls, events: Iterable[Dict[str, object]]) -> "FractalMemoryMap":
        memory_map = cls()
        for event in events:
            kind = str(event.get("type", ""))
            if kind == "session.memory.upsert":
                payload = event.get("memory_item")
                if isinstance(payload, dict):
                    memory_map.items[str(payload["memory_id"])] = MemoryItem.from_record(payload)
            elif kind == "session.memory.prune":
                memory_id = str(event.get("memory_id", ""))
                if memory_id in memory_map.items:
                    memory_map.prune(memory_id, str(event.get("reason", "")))
            elif kind == "session.memory.use":
                memory_id = str(event.get("memory_id", ""))
                if memory_id in memory_map.items:
                    memory_map.record_use(
                        memory_id,
                        successful=bool(event.get("successful", False)),
                        note=str(event.get("note", "")),
                    )
        return memory_map
