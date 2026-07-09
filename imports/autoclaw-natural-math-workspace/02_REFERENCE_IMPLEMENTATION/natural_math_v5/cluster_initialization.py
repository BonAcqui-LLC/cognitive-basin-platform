"""Natural Math v5 reference implementation — cluster initialization.

Frozen spec: Sections 18-19 (Cluster Initialization)

Donor: natural_math_cluster_oracle_runner.py, initialize_cluster function.
Modifications: extracted live_degree_bonds helper for reuse.
"""

from __future__ import annotations

from typing import Any

from .randomness import TraceRng


def initialize_cluster(
    seed: int,
    params: dict[str, Any],
    rng: TraceRng,
) -> dict[str, Any]:
    """Section 18-19: initialize 30-node cluster in bounded area.

    RNG call order (from donor):
    1. 30x randint(-2,2) for x
    2. 30x randint(-2,2) for y
    3. 30x randint(-5000,5000) for energy
    4. 29 chain bonds: 0-1, 1-2, ..., 28-29
    5. 435x randrange(0,1000000) bond draws, bond if < 80000
    6. 1x choice([2, ws-3]) for resource_x
    7. 1x randint(0, ws-1) for resource_y
    """
    center_x = params["world_size"] // 2
    center_y = params["world_size"] // 2

    nodes: list[dict[str, Any]] = []
    for node_id in range(30):
        x = center_x + rng.randint(-2, 2)
        y = center_y + rng.randint(-2, 2)
        energy = 55000 + rng.randint(-5000, 5000)
        nodes.append({
            "id": node_id,
            "pos": (x, y, 0),
            "direction": (0, 1, 0),
            "energy": energy,
            "pressure": 0,
            "alive": True,
            "type": "seed",
            "parent_id": None,
            "bonds": set(),
            "signal_type": 0,
        })

    live_by_id = {node["id"]: node for node in nodes}

    # Chain bonds: 0-1, 1-2, ..., 28-29
    for node_id in range(29):
        a = live_by_id[node_id]
        b = live_by_id[node_id + 1]
        if (
            live_degree_bonds(a, live_by_id) < params["max_bonds"]
            and live_degree_bonds(b, live_by_id) < params["max_bonds"]
        ):
            a["bonds"].add(b["id"])
            b["bonds"].add(a["id"])

    # 435 random bond draws
    random_bond_draws: list[int] = []
    for low_id in range(30):
        for high_id in range(low_id + 1, 30):
            draw = rng.randrange(0, 1000000)
            random_bond_draws.append(draw)
            a = live_by_id[low_id]
            b = live_by_id[high_id]
            if (
                draw < 80000
                and high_id not in a["bonds"]
                and low_id not in b["bonds"]
                and live_degree_bonds(a, live_by_id) < params["max_bonds"]
                and live_degree_bonds(b, live_by_id) < params["max_bonds"]
            ):
                a["bonds"].add(high_id)
                b["bonds"].add(low_id)

    resource_x = rng.choice([2, params["world_size"] - 3])
    resource_y = rng.randint(0, params["world_size"] - 1)

    return {
        "nodes": nodes,
        "resource_pos": (resource_x, resource_y, 0),
        "resource_left": 450000,
        "resource_reached": False,
        "random_bond_draws": random_bond_draws,
    }


def live_degree_bonds(node: dict[str, Any], live_by_id: dict[int, dict[str, Any]]) -> int:
    """Count live bonds for a node."""
    return sum(1 for bonded_id in node["bonds"] if bonded_id in live_by_id)


def live_bond_pairs(nodes: list[dict[str, Any]]) -> list[list[int]]:
    """Return sorted list of [lo_id, hi_id] for all live bond pairs."""
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    pairs: list[list[int]] = []
    for node in sorted(live_by_id.values(), key=lambda n: n["id"]):
        for bonded_id in sorted(node["bonds"]):
            if bonded_id in live_by_id and node["id"] < bonded_id:
                pairs.append([node["id"], bonded_id])
    return pairs
