"""Natural Math v5 reference implementation — cluster actions.

Frozen spec: Section 21

Donor: natural_math_cluster_oracle_runner.py
"""

from __future__ import annotations

from typing import Any

from .arithmetic import qdist, sign
from .cluster_initialization import live_degree_bonds, live_bond_pairs
from .cluster_metrics import connected_components
from .randomness import TraceRng


def kill_below_tau(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    for node in nodes:
        if node["alive"] and node["energy"] < params["tau"]:
            node["alive"] = False
            node["type"] = "inert"


def apply_seek(
    nodes: list[dict[str, Any]],
    resource_pos: tuple[int, int, int],
    params: dict[str, Any],
    rng: TraceRng,
) -> None:
    for node in sorted(
        [n for n in nodes if n["alive"]], key=lambda n: n["id"]
    ):
        raw_dx = resource_pos[0] - node["pos"][0]
        raw_dy = resource_pos[1] - node["pos"][1]
        if abs(raw_dx) >= abs(raw_dy):
            dx = sign(raw_dx)
            dy = 0
        else:
            dx = 0
            dy = sign(raw_dy)
        if rng.randrange(0, 1000000) < 120000:
            dx, dy = rng.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        x = min(params["world_size"] - 1, max(0, node["pos"][0] + dx))
        y = min(params["world_size"] - 1, max(0, node["pos"][1] + dy))
        node["pos"] = (x, y, node["pos"][2])
        node["energy"] -= params["move_cost"]


def apply_redistribute(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
) -> None:
    by_id = {node["id"]: node for node in nodes}
    pairs = live_bond_pairs(nodes)
    for low_id, high_id in pairs:
        a = by_id[low_id]
        b = by_id[high_id]
        diff = a["energy"] - b["energy"]
        if abs(diff) <= 1000:
            continue
        amount = (abs(diff) * params["trade_rate_num"]) // params["trade_rate_den"]
        donor_node = a if diff > 0 else b
        recipient = b if diff > 0 else a
        amount = min(amount, donor_node["energy"])
        donor_node["energy"] -= amount
        recipient["energy"] += amount
        donor_node["energy"] = max(0, donor_node["energy"] - params["trade_cost"])


def valid_repair_candidate(
    a: dict[str, Any],
    b: dict[str, Any],
    live_by_id: dict[int, dict[str, Any]],
    params: dict[str, Any],
) -> bool:
    return (
        b["id"] not in a["bonds"]
        and a["id"] not in b["bonds"]
        and live_degree_bonds(a, live_by_id) < params["max_bonds"]
        and live_degree_bonds(b, live_by_id) < params["max_bonds"]
        and (
            params["repair_ignores_distance"]
            or qdist(a["pos"], b["pos"]) <= params["bond_distance_sq"]
        )
    )


def add_bond(a: dict[str, Any], b: dict[str, Any]) -> None:
    a["bonds"].add(b["id"])
    b["bonds"].add(a["id"])


def apply_repair(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    rng: TraceRng,
) -> None:
    # Charge all live nodes repair cost
    for node in sorted(
        [n for n in nodes if n["alive"]], key=lambda n: n["id"]
    ):
        node["energy"] -= params["repair_cost"]
    for node in nodes:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(nodes, params)

    components = connected_components(nodes)
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}

    if len(live_by_id) < 2:
        return

    if len(components) > 1:
        # Try to connect across components
        by_id = {node["id"]: node for node in nodes}
        for i, comp_a in enumerate(components):
            for comp_b in components[i + 1:]:
                candidates = [
                    (by_id[a_id], by_id[b_id])
                    for a_id in comp_a
                    for b_id in comp_b
                    if valid_repair_candidate(by_id[a_id], by_id[b_id], live_by_id, params)
                ]
                candidates.sort(key=lambda pair: (pair[0]["id"], pair[1]["id"]))
                if not candidates:
                    continue
                for a, b in candidates:
                    if rng.randrange(0, 1000000) < params["repair_prob_ppm"]:
                        add_bond(a, b)
                        return
                return
    else:
        # Same component: try random pairs
        live_ids = sorted(live_by_id)
        for _ in range(20):
            first_index = rng.randrange(0, len(live_ids))
            first = live_ids[first_index]
            remaining = live_ids[:first_index] + live_ids[first_index + 1:]
            second = remaining[rng.randrange(0, len(remaining))]
            low_id, high_id = sorted([first, second])
            a = live_by_id[low_id]
            b = live_by_id[high_id]
            if not valid_repair_candidate(a, b, live_by_id, params):
                continue
            if rng.randrange(0, 1000000) < params["repair_prob_ppm"]:
                add_bond(a, b)
                return


def apply_rest(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
) -> None:
    for node in sorted(
        [n for n in nodes if n["alive"]], key=lambda n: n["id"]
    ):
        node["energy"] += params["rest_gain"]


def apply_resource_absorption(
    state: dict[str, Any],
    params: dict[str, Any],
) -> None:
    near = [
        node
        for node in sorted(
            [n for n in state["nodes"] if n["alive"]], key=lambda n: n["id"]
        )
        if qdist(node["pos"], state["resource_pos"]) <= params["resource_radius_sq"]
    ]
    if not near or state["resource_left"] == 0:
        return

    total_absorb = min(
        state["resource_left"], params["resource_absorb_rate"] * len(near)
    )
    base_share = total_absorb // len(near)
    remainder = total_absorb - base_share * len(near)

    for i, node in enumerate(near):
        node["energy"] += base_share
        if i < remainder:
            node["energy"] += 1

    state["resource_left"] -= total_absorb
    state["resource_left"] = max(0, state["resource_left"])
    state["resource_reached"] = True


def apply_damage(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    rng: TraceRng,
) -> None:
    for node in sorted(
        [n for n in nodes if n["alive"]], key=lambda n: n["id"]
    ):
        node["energy"] -= params["damage_energy_loss"]
        node["energy"] = max(0, node["energy"])
    kill_below_tau(nodes, params)

    pairs = live_bond_pairs(nodes)
    by_id = {node["id"]: node for node in nodes}
    for low_id, high_id in pairs:
        if rng.randrange(0, 1000000) < params["damage_bond_break_ppm"]:
            by_id[low_id]["bonds"].discard(high_id)
            by_id[high_id]["bonds"].discard(low_id)


def apply_cluster_action(
    action: str,
    state: dict[str, Any],
    params: dict[str, Any],
    rng: TraceRng | None,
) -> None:
    if action == "SEEK":
        if rng is None:
            raise ValueError("SEEK requires rng")
        apply_seek(state["nodes"], state["resource_pos"], params, rng)
    elif action == "REDISTRIBUTE":
        apply_redistribute(state["nodes"], params)
    elif action == "REPAIR":
        if rng is None:
            raise ValueError("REPAIR requires rng")
        apply_repair(state["nodes"], params, rng)
    elif action == "REST":
        apply_rest(state["nodes"], params)
    else:
        raise ValueError(f"unknown cluster action {action}")

    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)
