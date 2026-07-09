"""Natural Math v5 reference implementation — node records.

Frozen spec: Section 3 (Node Record), Section 4 (Node Types And Occupancy)
"""

from __future__ import annotations

from typing import Any

# Section 3: exact field set
NODE_FIELDS: set[str] = {
    "id", "pos", "direction", "energy", "pressure",
    "alive", "type", "parent_id", "bonds", "signal_type",
}

# Section 4: valid types
LIVE_TYPES: set[str] = {"seed", "tip"}
DEAD_TYPES: set[str] = {"branch", "inert", "wall"}
ALL_TYPES: set[str] = LIVE_TYPES | DEAD_TYPES

# Section 3: valid direction set (6 cardinal + zero)
CARDINAL_DIRECTIONS: set[tuple[int, int, int]] = {
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
}
DIRECTIONS_WITH_ZERO: set[tuple[int, int, int]] = CARDINAL_DIRECTIONS | {(0, 0, 0)}

# Section 13: world boundary
WORLD_BOUNDS: tuple[int, int] = (-100, 100)


def make_node(
    node_id: int,
    pos: tuple[int, int, int],
    *,
    direction: tuple[int, int, int] = (0, 1, 0),
    energy: int = 0,
    pressure: int = 0,
    alive: bool = True,
    node_type: str = "seed",
    parent_id: int | None = None,
    bonds: set[int] | None = None,
    signal_type: int = 0,
) -> dict[str, Any]:
    """Create a conforming node dict with all Section 3 fields.

    Section 4: new non-cluster seed nodes use direction=(0,1,0),
    signal_type=0 unless an input fixture provides other values.
    """
    return {
        "id": node_id,
        "pos": pos,
        "direction": direction,
        "energy": energy,
        "pressure": pressure,
        "alive": alive,
        "type": node_type,
        "parent_id": parent_id,
        "bonds": set(bonds) if bonds is not None else set(),
        "signal_type": signal_type,
    }


def die_inert(node: dict[str, Any]) -> None:
    """Section 4: death from energy or boundary changes node to inert.

    Energy is preserved at current value after any applied cost or clamp.
    Pressure, pos, direction, parent_id, bonds, signal_type remain unchanged.
    """
    node["alive"] = False
    node["type"] = "inert"


def die_branch(node: dict[str, Any]) -> None:
    """Section 4: bifurcation parent death — alive=False, type=branch, energy=0."""
    node["alive"] = False
    node["type"] = "branch"
    node["energy"] = 0


def is_live(node: dict[str, Any]) -> bool:
    return node["alive"]


def occupancy(nodes: list[dict[str, Any]]) -> set[tuple[int, int, int]]:
    """All occupied positions (live + dead). Section 12 frozen occupancy."""
    return {node["pos"] for node in nodes}
