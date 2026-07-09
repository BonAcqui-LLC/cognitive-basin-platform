#!/usr/bin/env python3
"""Cluster initialization and metrics oracle runner for Natural Math v5."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any


class ClusterTraceRng:
    def __init__(self, seed: int):
        self.inner = random.Random(seed)
        self.draws: list[int] = []

    def randrange(self, a: int, b: int) -> int:
        value = self.inner.randrange(a, b)
        if a == 0 and b == 1000000:
            self.draws.append(value)
        return value

    def randint(self, a: int, b: int) -> int:
        return self.inner.randint(a, b)

    def choice(self, seq: list[Any]) -> Any:
        return self.inner.choice(seq)


DEFAULT_PARAMS = {
    "tau": 5000,
    "iota_sq": 1,
    "r_sq": 625,
    "eps_extend": 500,
    "eps_sense": 1200,
    "eps_spawn": 4000,
    "eps_split": 9000,
    "E0": 1600000,
    "P_bifurcate": 12000,
    "beta_num": 85,
    "beta_den": 100,
    "delta_P_baseline": 2100,
    "delta_P_conflict": 5000,
    "gamma_fallback_ppm": 300000,
    "deficit_strength": 15000,
    "suffering_strength": -50000,
    "bond_distance_sq": 4,
    "max_bonds": 4,
    "decay_cost": 220,
    "move_cost": 300,
    "rest_gain": 220,
    "trade_rate_num": 18,
    "trade_rate_den": 100,
    "trade_cost": 25,
    "repair_cost": 350,
    "repair_prob_ppm": 700000,
    "repair_ignores_distance": False,
    "resource_absorb_rate": 14000,
    "resource_radius_sq": 4,
    "critical_energy": 30000,
    "low_energy_cutoff": 38000,
    "success_max_distance_sq_num": 9,
    "success_max_distance_sq_den": 4,
    "gini_threshold_num": 7,
    "gini_threshold_den": 100,
    "world_size": 25,
    "damage_energy_loss": 14000,
    "damage_bond_break_ppm": 180000,
}


def qdist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum((a[index] - b[index]) ** 2 for index in range(3))


def sign(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def live_degree(node: dict[str, Any], live_by_id: dict[int, dict[str, Any]]) -> int:
    return sum(1 for bonded_id in node["bonds"] if bonded_id in live_by_id)


def live_bond_pairs(nodes: list[dict[str, Any]]) -> list[list[int]]:
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    pairs = []
    for node in sorted(live_by_id.values(), key=lambda item: item["id"]):
        for bonded_id in sorted(node["bonds"]):
            if bonded_id in live_by_id and node["id"] < bonded_id:
                pairs.append([node["id"], bonded_id])
    return pairs


def initialize_cluster(seed: int, params: dict[str, Any], rng: Any | None = None) -> dict[str, Any]:
    if rng is None:
        rng = random.Random(seed)
    center = (params["world_size"] // 2, params["world_size"] // 2, 0)
    nodes = []
    for node_id in range(30):
        x = center[0] + rng.randint(-2, 2)
        y = center[1] + rng.randint(-2, 2)
        nodes.append(
            {
                "id": node_id,
                "pos": (x, y, 0),
                "direction": (0, 1, 0),
                "energy": 55000 + rng.randint(-5000, 5000),
                "pressure": 0,
                "alive": True,
                "type": "seed",
                "parent_id": None,
                "bonds": set(),
                "signal_type": 0,
            }
        )
    live_by_id = {node["id"]: node for node in nodes}
    for node_id in range(29):
        a = live_by_id[node_id]
        b = live_by_id[node_id + 1]
        if live_degree(a, live_by_id) < params["max_bonds"] and live_degree(b, live_by_id) < params["max_bonds"]:
            a["bonds"].add(b["id"])
            b["bonds"].add(a["id"])
    random_bond_draws = []
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
                and live_degree(a, live_by_id) < params["max_bonds"]
                and live_degree(b, live_by_id) < params["max_bonds"]
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


def connected_components(nodes: list[dict[str, Any]]) -> list[list[int]]:
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    assigned: set[int] = set()
    components = []
    for start_id in sorted(live_by_id):
        if start_id in assigned:
            continue
        stack = [start_id]
        component = []
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
    return sorted(components, key=lambda item: item[0])


def compute_metrics(nodes: list[dict[str, Any]], resource_pos: tuple[int, int, int], params: dict[str, Any]) -> dict[str, Any]:
    live_nodes = sorted([node for node in nodes if node["alive"]], key=lambda item: item["id"])
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
    sorted_energies = sorted(energies)
    total = sum(sorted_energies)
    if total == 0:
        gini_num = 0
        gini_den = 1
    else:
        weighted = sum((index + 1) * value for index, value in enumerate(sorted_energies))
        gini_num = 2 * weighted - (alive_count + 1) * total
        gini_den = alive_count * total
    gini_over_threshold = params["gini_threshold_den"] * gini_num > params["gini_threshold_num"] * gini_den
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


def passed_diagnostic(metrics: dict[str, Any], resource_reached: bool, params: dict[str, Any]) -> bool:
    return (
        metrics["alive_count"] >= 24
        and metrics["component_count"] == 1
        and metrics["average_energy"] >= params["low_energy_cutoff"]
        and resource_reached
        and metrics["success_distance_passed"]
    )


def select_cluster_action(metrics: dict[str, Any], resource_reached: bool, params: dict[str, Any]) -> str:
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


def kill_below_tau(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    for node in nodes:
        if node["alive"] and node["energy"] < params["tau"]:
            node["alive"] = False
            node["type"] = "inert"


def apply_seek(nodes: list[dict[str, Any]], resource_pos: tuple[int, int, int], params: dict[str, Any], rng: ClusterTraceRng) -> None:
    for node in sorted([item for item in nodes if item["alive"]], key=lambda item: item["id"]):
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


def apply_redistribute(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    by_id = {node["id"]: node for node in nodes}
    pairs = live_bond_pairs(nodes)
    for low_id, high_id in pairs:
        a = by_id[low_id]
        b = by_id[high_id]
        diff = a["energy"] - b["energy"]
        if abs(diff) <= 1000:
            continue
        amount = (abs(diff) * params["trade_rate_num"]) // params["trade_rate_den"]
        donor = a if diff > 0 else b
        recipient = b if diff > 0 else a
        amount = min(amount, donor["energy"])
        donor["energy"] -= amount
        recipient["energy"] += amount
        donor["energy"] = max(0, donor["energy"] - params["trade_cost"])


def valid_repair_candidate(a: dict[str, Any], b: dict[str, Any], live_by_id: dict[int, dict[str, Any]], params: dict[str, Any]) -> bool:
    return (
        b["id"] not in a["bonds"]
        and a["id"] not in b["bonds"]
        and live_degree(a, live_by_id) < params["max_bonds"]
        and live_degree(b, live_by_id) < params["max_bonds"]
        and (params["repair_ignores_distance"] or qdist(a["pos"], b["pos"]) <= params["bond_distance_sq"])
    )


def add_bond(a: dict[str, Any], b: dict[str, Any]) -> None:
    a["bonds"].add(b["id"])
    b["bonds"].add(a["id"])


def apply_repair(nodes: list[dict[str, Any]], params: dict[str, Any], rng: ClusterTraceRng) -> None:
    for node in sorted([item for item in nodes if item["alive"]], key=lambda item: item["id"]):
        node["energy"] -= params["repair_cost"]
    for node in nodes:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(nodes, params)
    components = connected_components(nodes)
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    if len(live_by_id) < 2:
        return
    if len(components) > 1:
        by_id = {node["id"]: node for node in nodes}
        for index, comp_a in enumerate(components):
            for comp_b in components[index + 1 :]:
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
        live_ids = sorted(live_by_id)
        for _ in range(20):
            first_index = rng.randrange(0, len(live_ids))
            first = live_ids[first_index]
            remaining = live_ids[:first_index] + live_ids[first_index + 1 :]
            second = remaining[rng.randrange(0, len(remaining))]
            low_id, high_id = sorted([first, second])
            a = live_by_id[low_id]
            b = live_by_id[high_id]
            if not valid_repair_candidate(a, b, live_by_id, params):
                continue
            if rng.randrange(0, 1000000) < params["repair_prob_ppm"]:
                add_bond(a, b)
                return


def apply_rest(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    for node in sorted([item for item in nodes if item["alive"]], key=lambda item: item["id"]):
        node["energy"] += params["rest_gain"]


def apply_resource_absorption(state: dict[str, Any], params: dict[str, Any]) -> None:
    near = [
        node
        for node in sorted([item for item in state["nodes"] if item["alive"]], key=lambda item: item["id"])
        if qdist(node["pos"], state["resource_pos"]) <= params["resource_radius_sq"]
    ]
    if not near or state["resource_left"] == 0:
        return
    total_absorb = min(state["resource_left"], params["resource_absorb_rate"] * len(near))
    base_share = total_absorb // len(near)
    remainder = total_absorb - base_share * len(near)
    for index, node in enumerate(near):
        node["energy"] += base_share
        if index < remainder:
            node["energy"] += 1
    state["resource_left"] -= total_absorb
    state["resource_left"] = max(0, state["resource_left"])
    state["resource_reached"] = True


def apply_damage(nodes: list[dict[str, Any]], params: dict[str, Any], rng: ClusterTraceRng) -> None:
    for node in sorted([item for item in nodes if item["alive"]], key=lambda item: item["id"]):
        node["energy"] -= params["damage_energy_loss"]
        node["energy"] = max(0, node["energy"])
    kill_below_tau(nodes, params)
    pairs = live_bond_pairs(nodes)
    by_id = {node["id"]: node for node in nodes}
    for low_id, high_id in pairs:
        if rng.randrange(0, 1000000) < params["damage_bond_break_ppm"]:
            by_id[low_id]["bonds"].discard(high_id)
            by_id[high_id]["bonds"].discard(low_id)


def apply_cluster_action(action: str, state: dict[str, Any], params: dict[str, Any], rng: ClusterTraceRng | None) -> None:
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


def check_cluster_invariants(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    ids = [node["id"] for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate cluster node id")
    by_id = {node["id"]: node for node in nodes}
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    for node in nodes:
        for bonded_id in list(node["bonds"]):
            if bonded_id not in by_id:
                raise ValueError("bond points to absent id")
            if node["alive"] and bonded_id in live_by_id and node["id"] not in by_id[bonded_id]["bonds"]:
                raise ValueError("live bond is not symmetric")
        if node["alive"] and live_degree(node, live_by_id) > params["max_bonds"]:
            raise ValueError("live node exceeds max live bonds")
        if node["alive"] and node["energy"] < params["tau"]:
            raise ValueError("live node below tau")


def cluster_step(state: dict[str, Any], params: dict[str, Any], rng: ClusterTraceRng, step_index: int) -> str:
    for node in sorted([item for item in state["nodes"] if item["alive"]], key=lambda item: item["id"]):
        node["energy"] -= params["decay_cost"]
    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)
    if step_index == 35:
        apply_damage(state["nodes"], params, rng)
    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)
    metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
    action = select_cluster_action(metrics, state["resource_reached"], params)
    apply_cluster_action(action, state, params, rng)
    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)
    apply_resource_absorption(state, params)
    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)
    check_cluster_invariants(state["nodes"], params)
    return action


def summarize_cluster_result(state: dict[str, Any], params: dict[str, Any], rng: ClusterTraceRng, actions: list[str]) -> dict[str, Any]:
    metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
    live_nodes = sorted([node for node in state["nodes"] if node["alive"]], key=lambda item: item["id"])
    return {
        "node_count": len(state["nodes"]),
        "alive_count": metrics["alive_count"],
        "live_node_ids": [node["id"] for node in live_nodes],
        "first_five_nodes": [
            {
                "id": node["id"],
                "pos": list(node["pos"]),
                "energy": node["energy"],
                "alive": node["alive"],
                "type": node["type"],
                "bonds": sorted(node["bonds"]),
            }
            for node in sorted(state["nodes"], key=lambda item: item["id"])[:5]
        ],
        "live_bond_pair_count": len(live_bond_pairs(state["nodes"])),
        "first_ten_live_bond_pairs": live_bond_pairs(state["nodes"])[:10],
        "resource_pos": list(state["resource_pos"]),
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "metrics": metrics,
        "passed": passed_diagnostic(metrics, state["resource_reached"], params),
        "actions": actions,
        "rng_ppm_draw_count": len(rng.draws),
        "first_ten_rng_ppm_draws": rng.draws[:10],
        "last_ten_rng_ppm_draws": rng.draws[-10:],
    }


def run_cluster_summary(seed: int, params: dict[str, Any], steps: int) -> dict[str, Any]:
    rng = ClusterTraceRng(seed)
    state = initialize_cluster(seed, params, rng)
    actions = []
    for step_index in range(1, steps + 1):
        actions.append(cluster_step(state, params, rng, step_index))
    return summarize_cluster_result(state, params, rng, actions)


def summarize_state(state: dict[str, Any], params: dict[str, Any], selected_action: str | None, rng: ClusterTraceRng | None) -> dict[str, Any]:
    return {
        "selected_action": selected_action,
        "nodes": [
            {
                "id": node["id"],
                "pos": list(node["pos"]),
                "energy": node["energy"],
                "alive": node["alive"],
                "type": node["type"],
                "bonds": sorted(node["bonds"]),
            }
            for node in sorted(state["nodes"], key=lambda item: item["id"])
        ],
        "resource_pos": list(state["resource_pos"]),
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "rng_draws": rng.draws if rng is not None else [],
        "metrics": compute_metrics(state["nodes"], state["resource_pos"], params),
    }


def run_action_fixture(fixture: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    state = {
        "nodes": json_to_nodes(fixture["state"]["nodes"]),
        "resource_pos": tuple(fixture["state"]["resource_pos"]),
        "resource_left": fixture["state"].get("resource_left", 450000),
        "resource_reached": fixture["state"].get("resource_reached", False),
    }
    rng = ClusterTraceRng(fixture["rng_seed"]) if "rng_seed" in fixture else None
    selected_action = fixture.get("action")
    if fixture.get("select_action", False):
        metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
        selected_action = select_cluster_action(metrics, state["resource_reached"], params)
    if selected_action is not None:
        apply_cluster_action(selected_action, state, params, rng)
    if fixture.get("apply_resource_absorption", False):
        apply_resource_absorption(state, params)
        for node in state["nodes"]:
            node["energy"] = max(0, node["energy"])
        kill_below_tau(state["nodes"], params)
    return summarize_state(state, params, selected_action, rng)


def json_to_nodes(raw_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = copy.deepcopy(raw_nodes)
    for node in nodes:
        node["pos"] = tuple(node["pos"])
        node["direction"] = tuple(node.get("direction", [0, 1, 0]))
        node["bonds"] = set(node["bonds"])
    return nodes


def summarize_initialization(state: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    nodes = state["nodes"]
    metrics = compute_metrics(nodes, state["resource_pos"], params)
    return {
        "node_count": len(nodes),
        "alive_count": sum(1 for node in nodes if node["alive"]),
        "first_five_nodes": [
            {
                "id": node["id"],
                "pos": list(node["pos"]),
                "energy": node["energy"],
                "bonds": sorted(node["bonds"]),
            }
            for node in nodes[:5]
        ],
        "live_bond_pair_count": len(live_bond_pairs(nodes)),
        "first_ten_live_bond_pairs": live_bond_pairs(nodes)[:10],
        "random_bond_draw_count": len(state["random_bond_draws"]),
        "first_ten_random_bond_draws": state["random_bond_draws"][:10],
        "last_five_random_bond_draws": state["random_bond_draws"][-5:],
        "resource_pos": list(state["resource_pos"]),
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "metrics": metrics,
        "passed": passed_diagnostic(metrics, state["resource_reached"], params),
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def run_suite(fixtures_path: Path) -> dict[str, Any]:
    suite = json.loads(fixtures_path.read_text(encoding="utf-8"))
    spec_path = Path(suite["spec"]["path"])
    spec_hash = sha256(spec_path) if spec_path.exists() else None
    results = {
        "suite": suite["suite"],
        "fixtures_path": str(fixtures_path),
        "fixtures_sha256": sha256(fixtures_path),
        "spec_path": str(spec_path),
        "spec_sha256_expected": suite["spec"]["sha256"],
        "spec_sha256_actual": spec_hash,
        "covered_sections": suite["covered_sections"],
        "cases": [],
    }
    all_passed = spec_hash == suite["spec"]["sha256"]
    for fixture in suite.get("initialization_fixtures", []):
        params = copy.deepcopy(DEFAULT_PARAMS)
        params.update(fixture.get("params", {}))
        actual = summarize_initialization(initialize_cluster(fixture["seed"], params), params)
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        all_passed = all_passed and status == "PASS"
        results["cases"].append({"name": fixture["name"], "kind": "initialization", "status": status, "actual": actual})
    for fixture in suite.get("metrics_fixtures", []):
        params = copy.deepcopy(DEFAULT_PARAMS)
        params.update(fixture.get("params", {}))
        actual = compute_metrics(json_to_nodes(fixture["nodes"]), tuple(fixture["resource_pos"]), params)
        status = "PASS" if actual == fixture["expected_metrics"] else "FAIL"
        all_passed = all_passed and status == "PASS"
        results["cases"].append({"name": fixture["name"], "kind": "metrics", "status": status, "actual": actual})
    for fixture in suite.get("action_fixtures", []):
        params = copy.deepcopy(DEFAULT_PARAMS)
        params.update(fixture.get("params", {}))
        actual = run_action_fixture(fixture, params)
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        all_passed = all_passed and status == "PASS"
        results["cases"].append({"name": fixture["name"], "kind": "action", "status": status, "actual": actual})
    for fixture in suite.get("damage_fixtures", []):
        params = copy.deepcopy(DEFAULT_PARAMS)
        params.update(fixture.get("params", {}))
        rng = ClusterTraceRng(fixture["rng_seed"])
        nodes = json_to_nodes(fixture["nodes"])
        apply_damage(nodes, params, rng)
        actual = {
            "nodes": [
                {
                    "id": node["id"],
                    "pos": list(node["pos"]),
                    "energy": node["energy"],
                    "alive": node["alive"],
                    "type": node["type"],
                    "bonds": sorted(node["bonds"]),
                }
                for node in sorted(nodes, key=lambda item: item["id"])
            ],
            "live_bond_pairs": live_bond_pairs(nodes),
            "rng_draws": rng.draws,
        }
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        all_passed = all_passed and status == "PASS"
        results["cases"].append({"name": fixture["name"], "kind": "damage", "status": status, "actual": actual})
    for fixture in suite.get("cluster_run_fixtures", []):
        params = copy.deepcopy(DEFAULT_PARAMS)
        params.update(fixture.get("params", {}))
        actual = run_cluster_summary(fixture["seed"], params, fixture["steps"])
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        all_passed = all_passed and status == "PASS"
        results["cases"].append({"name": fixture["name"], "kind": "cluster_run", "status": status, "actual": actual})
    results["passed"] = all_passed and all(case["status"] == "PASS" for case in results["cases"])
    return results


def write_report(results: dict[str, Any], report_path: Path) -> None:
    passed_count = sum(1 for case in results["cases"] if case["status"] == "PASS")
    total = len(results["cases"])
    lines = [
        "# Natural Math v5 Cluster Oracle Provenance Report",
        "",
        f"Overall result: {'PASS' if results['passed'] else 'FAIL'}",
        f"Cases passed: {passed_count}/{total}",
        "",
        "## Provenance",
        "",
        f"- Spec path: `{results['spec_path']}`",
        f"- Spec SHA256 expected: `{results['spec_sha256_expected']}`",
        f"- Spec SHA256 actual: `{results['spec_sha256_actual']}`",
        f"- Fixture path: `{results['fixtures_path']}`",
        f"- Fixture SHA256: `{results['fixtures_sha256']}`",
        "- Runner: `natural_math_cluster_oracle_runner.py`",
        "",
        "## Covered Sections",
        "",
    ]
    lines.extend(f"- {section}" for section in results["covered_sections"])
    lines.extend(["", "## Case Results", ""])
    for case in results["cases"]:
        lines.append(f"- {case['status']} `{case['name']}` ({case['kind']})")
        if case["kind"] == "initialization":
            lines.append(f"  - resource_pos: `{case['actual']['resource_pos']}`")
            lines.append(f"  - live_bond_pair_count: `{case['actual']['live_bond_pair_count']}`")
            lines.append(f"  - random_bond_draw_count: `{case['actual']['random_bond_draw_count']}`")
            lines.append(f"  - metrics: `{case['actual']['metrics']}`")
        if case["kind"] == "action":
            lines.append(f"  - selected_action: `{case['actual']['selected_action']}`")
            lines.append(f"  - resource_left: `{case['actual']['resource_left']}`")
            lines.append(f"  - resource_reached: `{case['actual']['resource_reached']}`")
            lines.append(f"  - rng_draws: `{case['actual']['rng_draws']}`")
        if case["kind"] == "damage":
            lines.append(f"  - live_bond_pairs: `{case['actual']['live_bond_pairs']}`")
            lines.append(f"  - rng_draws: `{case['actual']['rng_draws']}`")
        if case["kind"] == "cluster_run":
            lines.append(f"  - alive_count: `{case['actual']['alive_count']}`")
            lines.append(f"  - resource_left: `{case['actual']['resource_left']}`")
            lines.append(f"  - resource_reached: `{case['actual']['resource_reached']}`")
            lines.append(f"  - passed: `{case['actual']['passed']}`")
            lines.append(f"  - rng_ppm_draw_count: `{case['actual']['rng_ppm_draw_count']}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This report validates cluster initialization summaries, standalone metrics fixtures, cluster action/resource micro-fixtures, damage micro-fixtures, and listed seeded cluster runs. A 140-step pass is a validation claim only for an exact listed seed fixture.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default="natural_math_cluster_oracle_fixtures.json")
    parser.add_argument("--report", default="natural_math_cluster_oracle_results.md")
    parser.add_argument("--emit-template", action="store_true")
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    fixtures_path = Path(args.fixtures)
    if not fixtures_path.is_absolute():
        fixtures_path = script_dir / fixtures_path
    if args.emit_template:
        suite = json.loads(fixtures_path.read_text(encoding="utf-8"))
        params = copy.deepcopy(DEFAULT_PARAMS)
        suite["initialization_fixtures"] = [
            {
                "name": "cluster_seed_3_initialization_summary",
                "seed": 3,
                "expected_summary": summarize_initialization(initialize_cluster(3, params), params),
            },
            {
                "name": "cluster_seed_11_initialization_summary",
                "seed": 11,
                "expected_summary": summarize_initialization(initialize_cluster(11, params), params),
            },
        ]
        suite["metrics_fixtures"] = [
            {
                "name": "cluster_metrics_empty_state",
                "resource_pos": [2, 2, 0],
                "nodes": [],
                "expected_metrics": compute_metrics([], (2, 2, 0), params),
            },
            {
                "name": "cluster_metrics_connected_success_low_gini",
                "resource_pos": [1, 0, 0],
                "nodes": [
                    {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 40000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0},
                    {"id": 1, "pos": [1, 0, 0], "direction": [0, 1, 0], "energy": 41000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [0, 2], "signal_type": 0},
                    {"id": 2, "pos": [2, 0, 0], "direction": [0, 1, 0], "energy": 42000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0}
                ],
                "expected_metrics": compute_metrics(json_to_nodes([
                    {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 40000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0},
                    {"id": 1, "pos": [1, 0, 0], "direction": [0, 1, 0], "energy": 41000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [0, 2], "signal_type": 0},
                    {"id": 2, "pos": [2, 0, 0], "direction": [0, 1, 0], "energy": 42000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0}
                ]), (1, 0, 0), params),
            },
            {
                "name": "cluster_metrics_fragmented_high_gini_far_resource",
                "resource_pos": [20, 20, 0],
                "nodes": [
                    {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 10000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                    {"id": 1, "pos": [10, 0, 0], "direction": [0, 1, 0], "energy": 90000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                    {"id": 2, "pos": [0, 10, 0], "direction": [0, 1, 0], "energy": 90000, "pressure": 0, "alive": False, "type": "inert", "parent_id": None, "bonds": [], "signal_type": 0}
                ],
                "expected_metrics": compute_metrics(json_to_nodes([
                    {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 10000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                    {"id": 1, "pos": [10, 0, 0], "direction": [0, 1, 0], "energy": 90000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                    {"id": 2, "pos": [0, 10, 0], "direction": [0, 1, 0], "energy": 90000, "pressure": 0, "alive": False, "type": "inert", "parent_id": None, "bonds": [], "signal_type": 0}
                ]), (20, 20, 0), params),
            },
        ]
        action_cases = [
            {
                "name": "cluster_action_policy_seek_moves_toward_resource",
                "select_action": True,
                "rng_seed": 11,
                "state": {
                    "resource_pos": [4, 0, 0],
                    "resource_left": 450000,
                    "resource_reached": False,
                    "nodes": [
                        {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 36000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0},
                        {"id": 1, "pos": [0, 1, 0], "direction": [0, 1, 0], "energy": 37000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [0], "signal_type": 0}
                    ],
                },
            },
            {
                "name": "cluster_action_policy_rest_adds_rest_gain",
                "select_action": True,
                "state": {
                    "resource_pos": [1, 0, 0],
                    "resource_left": 450000,
                    "resource_reached": True,
                    "nodes": [
                        {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 40000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0},
                        {"id": 1, "pos": [1, 0, 0], "direction": [0, 1, 0], "energy": 41000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [0, 2], "signal_type": 0},
                        {"id": 2, "pos": [2, 0, 0], "direction": [0, 1, 0], "energy": 42000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0}
                    ],
                },
            },
            {
                "name": "cluster_action_redistribute_transfers_energy_over_live_bond",
                "action": "REDISTRIBUTE",
                "state": {
                    "resource_pos": [0, 0, 0],
                    "resource_left": 450000,
                    "resource_reached": False,
                    "nodes": [
                        {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 60000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0},
                        {"id": 1, "pos": [1, 0, 0], "direction": [0, 1, 0], "energy": 40000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [0], "signal_type": 0}
                    ],
                },
            },
            {
                "name": "cluster_action_policy_repair_fragmented_adds_first_valid_bond",
                "select_action": True,
                "rng_seed": 11,
                "params": {"repair_prob_ppm": 1000000},
                "state": {
                    "resource_pos": [0, 0, 0],
                    "resource_left": 450000,
                    "resource_reached": False,
                    "nodes": [
                        {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 10000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                        {"id": 1, "pos": [2, 0, 0], "direction": [0, 1, 0], "energy": 12000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0}
                    ],
                },
            },
            {
                "name": "cluster_resource_absorption_shares_integer_energy",
                "apply_resource_absorption": True,
                "state": {
                    "resource_pos": [0, 0, 0],
                    "resource_left": 28001,
                    "resource_reached": False,
                    "nodes": [
                        {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 10000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                        {"id": 1, "pos": [1, 0, 0], "direction": [0, 1, 0], "energy": 12000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0},
                        {"id": 2, "pos": [5, 5, 0], "direction": [0, 1, 0], "energy": 14000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [], "signal_type": 0}
                    ],
                },
            },
        ]
        for case in action_cases:
            case_params = copy.deepcopy(DEFAULT_PARAMS)
            case_params.update(case.get("params", {}))
            case["expected_summary"] = run_action_fixture(case, case_params)
        suite["action_fixtures"] = action_cases
        damage_cases = [
            {
                "name": "cluster_damage_loses_energy_and_breaks_seeded_bonds",
                "rng_seed": 11,
                "params": {"damage_bond_break_ppm": 500000},
                "nodes": [
                    {"id": 0, "pos": [0, 0, 0], "direction": [0, 1, 0], "energy": 30000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0},
                    {"id": 1, "pos": [1, 0, 0], "direction": [0, 1, 0], "energy": 30000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [0, 2], "signal_type": 0},
                    {"id": 2, "pos": [2, 0, 0], "direction": [0, 1, 0], "energy": 30000, "pressure": 0, "alive": True, "type": "seed", "parent_id": None, "bonds": [1], "signal_type": 0}
                ],
            }
        ]
        for case in damage_cases:
            case_params = copy.deepcopy(DEFAULT_PARAMS)
            case_params.update(case.get("params", {}))
            case_rng = ClusterTraceRng(case["rng_seed"])
            case_nodes = json_to_nodes(case["nodes"])
            apply_damage(case_nodes, case_params, case_rng)
            case["expected_summary"] = {
                "nodes": [
                    {
                        "id": node["id"],
                        "pos": list(node["pos"]),
                        "energy": node["energy"],
                        "alive": node["alive"],
                        "type": node["type"],
                        "bonds": sorted(node["bonds"]),
                    }
                    for node in sorted(case_nodes, key=lambda item: item["id"])
                ],
                "live_bond_pairs": live_bond_pairs(case_nodes),
                "rng_draws": case_rng.draws,
            }
        suite["damage_fixtures"] = damage_cases
        cluster_run_cases = [
            {"name": "cluster_seed_3_steps_0_exact_result", "seed": 3, "steps": 0},
            {"name": "cluster_seed_3_steps_1_exact_result", "seed": 3, "steps": 1},
            {"name": "cluster_seed_3_steps_35_damage_gate_exact_result", "seed": 3, "steps": 35},
            {"name": "cluster_seed_3_steps_140_exact_result", "seed": 3, "steps": 140},
        ]
        for case in cluster_run_cases:
            case_params = copy.deepcopy(DEFAULT_PARAMS)
            case_params.update(case.get("params", {}))
            case["expected_summary"] = run_cluster_summary(case["seed"], case_params, case["steps"])
        suite["cluster_run_fixtures"] = cluster_run_cases
        fixtures_path.write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = script_dir / report_path
    results = run_suite(fixtures_path)
    write_report(results, report_path)
    print(json.dumps({"passed": results["passed"], "report": str(report_path), "cases": results["cases"]}, indent=2))
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
