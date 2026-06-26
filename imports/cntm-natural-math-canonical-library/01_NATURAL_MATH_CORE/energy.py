from __future__ import annotations

from .state import NodeState


def spend_energy(current: float, amount: float) -> float:
    return max(0.0, current - max(0.0, amount))


def total_active_energy(nodes: list[NodeState]) -> float:
    return float(sum(node.energy for node in nodes if node.alive))
