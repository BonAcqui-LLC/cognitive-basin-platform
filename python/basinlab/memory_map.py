"""
Auditable FractalMemoryMap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MemoryNode:
    memory_id: str
    purpose_links: List[str] = field(default_factory=list)
    evidence_links: List[str] = field(default_factory=list)
    contradiction_links: List[str] = field(default_factory=list)
    association_links: List[str] = field(default_factory=list)
    scars: List[str] = field(default_factory=list)
    recovery_routes: List[str] = field(default_factory=list)
    retention_weight: float = 0.5
    survival_reason: str = ""
    pruning_reason: str = ""
    replay_history: List[str] = field(default_factory=list)
    successful_response_memory: List[str] = field(default_factory=list)
    failed_response_memory: List[str] = field(default_factory=list)
    live_attractors: List[str] = field(default_factory=list)
    verified_compression_references: List[str] = field(default_factory=list)


class FractalMemoryMap:
    def __init__(self) -> None:
        self.nodes: Dict[str, MemoryNode] = {}
        self.events: List[Dict[str, str]] = []

    def upsert(self, node: MemoryNode) -> None:
        self.nodes[node.memory_id] = node
        self.events.append({"type": "memory_upserted", "memory_id": node.memory_id})

    def prune(self, memory_id: str, reason: str) -> None:
        if memory_id in self.nodes:
            self.nodes[memory_id].pruning_reason = reason
            self.events.append({"type": "memory_pruned", "memory_id": memory_id, "reason": reason})

