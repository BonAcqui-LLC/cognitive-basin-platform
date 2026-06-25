"""Natural Math v5 reference implementation — cluster metrics.

Frozen spec: Section 20 (Cluster Metrics)

Donor: natural_math_cluster_oracle_runner.py
"""

from __future__ import annotations

from typing import Any

from .arithmetic import qdist
from .cluster_initialization import live_degree_bonds, live_bond_pairs


def connected_components(nodes: list[dict[str, Any]]) -> list[list[int]]:
    """Return components as sorted lists of node ids, sorted by first id."""
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    assigned: set[int] = set()
    components: list[list[int]] = []

    for start_id in sorted(live_by_id):
        if start_id in assigned:
            continue
        stack = [start_id]
        component: list[int] = []
        assigned.add(start_id)
        while stack:
            node_id = stack.pop()
            component.append(node_id)
            node = live_by_id[node_id]
            for bonded_id in sorted(node["bonds"]):
                if bonded_id in live_by_id and bonded_id not in assigned:
                    assigned.add(bonded_id)
                    stack.append(bonded_id)
        components.append(sorted(component))

    return sorted(components, key=lambda c: c[0])


def compute_metrics(
    nodes: list[dict[str, Any]],
    resource_pos: tuple[int, int, int],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Section 20: compute full cluster metrics dictionary."""
    live_nodes = sorted(
        [node for node in nodes if node["alive"]], key=lambda n: n["id"]
    )

    if not live_nodes:
        return {
            "alive_count": 0,
            "component_count": 0,
            "average_energy": 0,
            "min_energy": 0,
            "center_sum": None,
            "center_denominator": 0,
            "success_distance_passed": False,
            "gini_num": 0,
            "gini_den": 1,
            "gini_over_threshold": False,
        }

    alive_count = len(live_nodes)
    energies = [node["energy"] for node in live_nodes]
    energy_total = sum(energies)

    # Center of mass relative to resource
    center_sum_tuple = (
        sum(node["pos"][0] for node in live_nodes),
        sum(node["pos"][1] for node in live_nodes),
        sum(node["pos"][2] for node in live_nodes),
    )
    dx_num = center_sum_tuple[0] - resource_pos[0] * alive_count
    dy_num = center_sum_tuple[1] - resource_pos[1] * alive_count
    dz_num = center_sum_tuple[2] - resource_pos[2] * alive_count
    dist_num = dx_num * dx_num + dy_num * dy_num + dz_num * dz_num

    success_distance_passed = (
        params["success_max_distance_sq_den"] * dist_num
        <= params["success_max_distance_sq_num"] * alive_count * alive_count
    )

    # Integer Gini coefficient
    sorted_energies = sorted(energies)
    total = sum(sorted_energies)
    if total == 0:
        gini_num = 0
        gini_den = 1
    else:
        weighted = sum((i + 1) * v for i, v in enumerate(sorted_energies))
        gini_num = 2 * weighted - (alive_count + 1) * total
        gini_den = alive_count * total

    gini_over_threshold = (
        params["gini_threshold_den"] * gini_num
        > params["gini_threshold_num"] * gini_den
    )

    return {
        "alive_count": alive_count,
        "component_count": len(connected_components(nodes)),
        "average_energy": energy_total // alive_count,
        "min_energy": min(energies),
        "center_sum": list(center_sum_tuple),
        "center_denominator": alive_count,
        "success_distance_passed": success_distance_passed,
        "gini_num": gini_num,
        "gini_den": gini_den,
        "gini_over_threshold": gini_over_threshold,
    }


def passed_diagnostic(
    metrics: dict[str, Any],
    resource_reached: bool,
    params: dict[str, Any],
) -> bool:
    """Section 22: overall cluster passed diagnostic."""
    return (
        metrics["alive_count"] >= 24
        and metrics["component_count"] == 1
        and metrics["average_energy"] >= params["low_energy_cutoff"]
        and resource_reached
        and metrics["success_distance_passed"]
    )


def select_cluster_action(
    metrics: dict[str, Any],
    resource_reached: bool,
    params: dict[str, Any],
) -> str:
    """Section 21: policy-based action selection."""
    if metrics["component_count"] > 1:
        return "REPAIR"
    if metrics["min_energy"] < params["critical_energy"]:
        return "REST" if resource_reached else "REDISTRIBUTE"
    if metrics["average_energy"] < params["low_energy_cutoff"] and not resource_reached:
        return "SEEK"
    if metrics["average_energy"] < params["low_energy_cutoff"] and resource_reached:
        return "SEEK" if not metrics["success_distance_passed"] else "REST"
    if metrics["gini_over_threshold"]:
        return "REDISTRIBUTE"
    if not metrics["success_distance_passed"]:
        return "SEEK"
    return "REST"
