from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NodeState:
    position: tuple[int, int, int]
    direction: tuple[int, int, int]
    energy: float
    pressure: float = 0.0
    alive: bool = True
    parent_id: int | None = None
    node_id: int | None = None
    forest_id: int = 0
    node_type: str = "tip"


@dataclass
class SimulationState:
    nodes: list[NodeState] = field(default_factory=list)
    step_count: int = 0
    forest_counter: int = 0
    initial_forest_count: int = 0
    birth_events: int = 0
    trail: dict[tuple[int, int, int], float] = field(default_factory=dict)
    environment: dict[tuple[int, int, int], str] = field(default_factory=dict)
    forest_params: dict[int, dict[str, float]] = field(default_factory=dict)
    history_active: list[int] = field(default_factory=list)
    history_energy: list[float] = field(default_factory=list)
    history_forests: list[int] = field(default_factory=list)
    event_log: list[dict[str, object]] = field(default_factory=list)


# Backward-compatible aliases for the earlier scaffold.
AgentState = NodeState
