"""
Association retrieval and maturation for BasinLab planning context.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AssociationBrush:
    source_id: str
    target_id: str
    purpose_relationship: str
    provenance: str


@dataclass
class AssociationBeacon:
    association_id: str
    label: str
    purpose: str
    salience: float = 0.0
    relevance: float = 0.0
    access_count: int = 0
    retrieval_count: int = 0
    survival_duration: float = 0.0
    replay_value: float = 0.0
    successful_use: int = 0
    failed_use: int = 0
    contradiction_count: int = 0
    recovery_history: List[str] = field(default_factory=list)
    provenance: str = ""


@dataclass
class AssociationEdge:
    source_id: str
    target_id: str
    purpose_relationship: str
    provenance: str


@dataclass
class AssociationRetrieval:
    association_id: str
    context_only: bool
    reason: str


@dataclass
class MaturationEvent:
    association_id: str
    delta: float
    timestamp: float


@dataclass
class DecayEvent:
    association_id: str
    delta: float
    timestamp: float


@dataclass
class PromotionEvent:
    association_id: str
    delta: float
    timestamp: float


@dataclass
class DemotionEvent:
    association_id: str
    delta: float
    timestamp: float


class AssociationField:
    def __init__(self) -> None:
        self.beacons: Dict[str, AssociationBeacon] = {}
        self.edges: List[AssociationEdge] = []
        self.events: List[object] = []

    def add_beacon(self, beacon: AssociationBeacon) -> None:
        self.beacons[beacon.association_id] = beacon

    def add_edge(self, brush: AssociationBrush) -> None:
        self.edges.append(
            AssociationEdge(
                source_id=brush.source_id,
                target_id=brush.target_id,
                purpose_relationship=brush.purpose_relationship,
                provenance=brush.provenance,
            )
        )

    def retrieve(self, purpose: str) -> List[AssociationRetrieval]:
        ranked = sorted(
            self.beacons.values(),
            key=lambda beacon: (beacon.purpose != purpose, -beacon.relevance, -beacon.salience, beacon.association_id),
        )
        retrievals: List[AssociationRetrieval] = []
        for beacon in ranked[:5]:
            beacon.access_count += 1
            beacon.retrieval_count += 1
            retrievals.append(
                AssociationRetrieval(
                    association_id=beacon.association_id,
                    context_only=True,
                    reason="Retrieved as planning context, not evidence-qualified truth",
                )
            )
        return retrievals

    def record_use(self, association_id: str, verified_success: bool, contradicted: bool = False) -> None:
        beacon = self.beacons[association_id]
        timestamp = time.time()
        if verified_success:
            beacon.successful_use += 1
            beacon.replay_value += 0.1
            beacon.relevance += 0.1
            self.events.append(PromotionEvent(association_id, 0.1, timestamp))
            self.events.append(MaturationEvent(association_id, 0.1, timestamp))
        else:
            beacon.failed_use += 1
            beacon.relevance -= 0.1
            self.events.append(DemotionEvent(association_id, -0.1, timestamp))
            self.events.append(DecayEvent(association_id, -0.1, timestamp))
        if contradicted:
            beacon.contradiction_count += 1
            beacon.relevance -= 0.2

