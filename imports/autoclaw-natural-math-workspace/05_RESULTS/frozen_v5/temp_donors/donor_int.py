#!/usr/bin/env python3
"""Integer oracle runner for Natural Math v5.

This is intentionally small and literal. It covers the current run_step fixture
packs: validation basics, contact decisions, sensing, integer gradients,
fallback RNG, movement blocking, target contests, bifurcation, child direction
selection, pressure update, optional bonding, deficit mode, and PoC scream mode.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any


class NaturalMathValidationError(ValueError):
    pass


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

FIELDS = {
    "id",
    "pos",
    "direction",
    "energy",
    "pressure",
    "alive",
    "type",
    "parent_id",
    "bonds",
    "signal_type",
}
DIRS = {
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
}
DIRS_WITH_ZERO = DIRS | {(0, 0, 0)}
LIVE_TYPES = {"seed", "tip"}
DEAD_TYPES = {"branch", "inert", "wall"}


class TraceRng:
    def __init__(self, seed: int):
        self.inner = random.Random(seed)
        self.draws: list[int] = []

    def randrange(self, a: int, b: int) -> int:
        value = self.inner.randrange(a, b)
        if a == 0 and b == 1000000:
            self.draws.append(value)
        return value


def qdist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum((a[i] - b[i]) ** 2 for i in range(3))


def die_inert(node: dict[str, Any]) -> None:
    node["alive"] = False
    node["type"] = "inert"


def validate_params(params: dict[str, Any]) -> None:
    if set(params) != set(DEFAULT_PARAMS):
        raise NaturalMathValidationError("Section 5 params: required parameter set mismatch")
    for key, value in params.items():
        if key == "repair_ignores_distance":
            if type(value) is not bool:
                raise NaturalMathValidationError("Section 5 repair_ignores_distance: must be Boolean")
        elif type(value) is not int:
            raise NaturalMathValidationError(f"Section 5 {key}: must be integer")
    if not (params["tau"] > 0):
        raise NaturalMathValidationError("Section 5 tau: must be > 0")
    if not (params["iota_sq"] > 0 and params["r_sq"] > params["iota_sq"]):
        raise NaturalMathValidationError("Section 5 iota_sq/r_sq: invalid sensing radius")
    if not (params["E0"] > params["tau"]):
        raise NaturalMathValidationError("Section 5 E0: must exceed tau")
    if not (0 <= params["gamma_fallback_ppm"] <= 1000000):
        raise NaturalMathValidationError("Section 5 gamma_fallback_ppm: out of ppm range")


def as_tuple3(value: Any, field: str) -> tuple[int, int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise NaturalMathValidationError(f"Section 6 {field}: must be 3-integer tuple")
    result = tuple(value)
    if any(type(v) is not int for v in result):
        raise NaturalMathValidationError(f"Section 6 {field}: must be 3-integer tuple")
    return result  # type: ignore[return-value]


def validate_nodes(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    if not isinstance(nodes, list):
        raise NaturalMathValidationError("Section 6 nodes: must be mutable list")
    ids: set[int] = set()
    for node in nodes:
        if set(node) != FIELDS:
            raise NaturalMathValidationError("Section 6 node fields: exact field set required")
        if type(node["id"]) is not int or node["id"] < 0:
            raise NaturalMathValidationError("Section 6 id: must be non-negative integer")
        if node["id"] in ids:
            raise NaturalMathValidationError("Section 6 id: duplicate id")
        ids.add(node["id"])
        node["pos"] = as_tuple3(node["pos"], "pos")
        node["direction"] = as_tuple3(node["direction"], "direction")
        if node["direction"] not in DIRS_WITH_ZERO:
            raise NaturalMathValidationError("Section 6 direction: invalid direction")
        if type(node["energy"]) is not int or node["energy"] < 0:
            raise NaturalMathValidationError("Section 6 energy: non-negative integer required")
        if type(node["pressure"]) is not int or node["pressure"] < 0:
            raise NaturalMathValidationError("Section 6 pressure: non-negative integer required")
        if type(node["alive"]) is not bool:
            raise NaturalMathValidationError("Section 6 alive: must be Boolean")
        if node["type"] not in LIVE_TYPES | DEAD_TYPES:
            raise NaturalMathValidationError("Section 6 type: unknown node type")
        if node["alive"] and node["type"] not in LIVE_TYPES:
            raise NaturalMathValidationError("Section 6 type: live node must be seed or tip")
        if node["type"] in DEAD_TYPES and node["alive"]:
            raise NaturalMathValidationError("Section 6 alive: dead type must have alive false")
        if not isinstance(node["bonds"], set) or any(type(v) is not int for v in node["bonds"]):
            raise NaturalMathValidationError("Section 6 bonds: mutable set of integer ids required")
        if type(node["signal_type"]) is not int:
            raise NaturalMathValidationError("Section 6 signal_type: must be integer")
    for node in nodes:
        for bonded_id in node["bonds"]:
            if bonded_id not in ids:
                raise NaturalMathValidationError("Section 6 bonds: bond points to absent id")
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    for node in live_by_id.values():
        for bonded_id in node["bonds"]:
            if bonded_id in live_by_id and node["id"] not in live_by_id[bonded_id]["bonds"]:
                raise NaturalMathValidationError("Section 6 bonds: live-to-live bond must be symmetric")
        if live_degree(node, live_by_id) > params["max_bonds"]:
            raise NaturalMathValidationError("Section 6A bonds: live node exceeds max live bonds")
    validate_params(params)


def live_degree(node: dict[str, Any], live_by_id: dict[int, dict[str, Any]]) -> int:
    return sum(1 for bonded_id in node["bonds"] if bonded_id in live_by_id)


def deficit(energy: int, params: dict[str, Any]) -> int:
    return max(0, params["E0"] - energy)


def gradient_direction(
    node: dict[str, Any],
    live_nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    use_deficit: bool,
    use_poc_scream: bool,
) -> tuple[int, int, int]:
    scores = [[0, 1], [0, 1], [0, 1]]
    for other in live_nodes:
        if other["id"] == node["id"]:
            continue
        dist = qdist(node["pos"], other["pos"])
        if not (1 <= dist <= params["r_sq"]):
            continue
        if use_poc_scream:
            if other["energy"] < 2 * params["tau"]:
                effective = params["suffering_strength"]
            else:
                effective = other["energy"] - node["energy"]
        else:
            effective = other["energy"] - node["energy"]
            if use_deficit:
                effective -= (
                    params["deficit_strength"]
                    * deficit(node["energy"], params)
                    * deficit(other["energy"], params)
                ) // (params["E0"] * params["E0"])
        for axis in range(3):
            c_num = effective * (other["pos"][axis] - node["pos"][axis])
            c_den = dist
            old_num, old_den = scores[axis]
            scores[axis] = [old_num * c_den + c_num * old_den, old_den * c_den]
    if all(score[0] == 0 for score in scores):
        return (0, 0, 0)
    best = 0
    for axis in (1, 2):
        if abs(scores[axis][0]) * scores[best][1] > abs(scores[best][0]) * scores[axis][1]:
            best = axis
    direction = [0, 0, 0]
    direction[best] = 1 if scores[best][0] > 0 else -1
    return tuple(direction)  # type: ignore[return-value]


def fallback_direction(node: dict[str, Any]) -> tuple[int, int, int]:
    direction = node["direction"]
    if direction not in DIRS_WITH_ZERO:
        raise NaturalMathValidationError("Section 13 direction: invalid fallback direction")
    return (0, 1, 0) if direction == (0, 0, 0) else direction


def child_directions(direction: tuple[int, int, int]) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if direction in {(1, 0, 0), (-1, 0, 0)}:
        return (0, 1, 0), (0, 0, 1)
    if direction in {(0, 1, 0), (0, -1, 0)}:
        return (1, 0, 0), (0, 0, 1)
    if direction in {(0, 0, 1), (0, 0, -1)}:
        return (1, 0, 0), (0, 1, 0)
    if direction == (0, 0, 0):
        return (1, 0, 0), (0, 1, 0)
    raise NaturalMathValidationError("Section 15 movement_direction: invalid child direction source")


def add_pos(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(a[i] + b[i] for i in range(3))  # type: ignore[return-value]


def inside_world(pos: tuple[int, int, int]) -> bool:
    return all(-100 <= coord <= 100 for coord in pos)


def can_bifurcate(
    node: dict[str, Any],
    direction: tuple[int, int, int],
    params: dict[str, Any],
    all_occupied: set[tuple[int, int, int]],
    reserved_child_positions: set[tuple[int, int, int]],
    *,
    mode_allows_bifurcation: bool,
) -> tuple[bool, dict[str, Any] | None]:
    first_direction, second_direction = child_directions(direction)
    first_pos = add_pos(node["pos"], first_direction)
    second_pos = add_pos(node["pos"], second_direction)
    if not node["alive"]:
        return False, None
    if not mode_allows_bifurcation:
        return False, None
    if node["pressure"] < params["P_bifurcate"]:
        return False, None
    if node["energy"] <= params["eps_extend"] + params["eps_spawn"] + params["eps_split"] + 2 * params["tau"]:
        return False, None
    if not (inside_world(first_pos) and inside_world(second_pos)):
        return False, None
    if first_pos in all_occupied or second_pos in all_occupied:
        return False, None
    if first_pos in reserved_child_positions or second_pos in reserved_child_positions:
        return False, None
    return True, {
        "parent_id": node["id"],
        "parent_energy_for_split": node["energy"],
        "movement_direction": direction,
        "child_direction_1": first_direction,
        "child_direction_2": second_direction,
        "child_pos_1": first_pos,
        "child_pos_2": second_pos,
    }


def apply_bonding(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    bond_collapse_positions: bool,
    bonding_strict: bool,
) -> None:
    live_nodes = sorted([node for node in nodes if node["alive"]], key=lambda n: n["id"])
    live_by_id = {node["id"]: node for node in live_nodes}
    pairs = [(a, b) for index, a in enumerate(live_nodes) for b in live_nodes[index + 1 :]]
    for a, b in pairs:
        dist_sq = qdist(a["pos"], b["pos"])
        distance_allowed = dist_sq < params["bond_distance_sq"] if bonding_strict else dist_sq <= params["bond_distance_sq"]
        if not distance_allowed:
            continue
        if live_degree(a, live_by_id) >= params["max_bonds"] or live_degree(b, live_by_id) >= params["max_bonds"]:
            continue
        if b["id"] in a["bonds"] or a["id"] in b["bonds"]:
            continue
        a["bonds"].add(b["id"])
        b["bonds"].add(a["id"])
        total = a["energy"] + b["energy"]
        a["energy"] = total // 2
        b["energy"] = total - a["energy"]
        if bond_collapse_positions:
            b["pos"] = a["pos"]


def run_step(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    use_deficit: bool = False,
    use_poc_scream: bool = False,
    allow_bonding: bool = False,
    bond_collapse_positions: bool = False,
    bonding_strict: bool = False,
    rng: TraceRng | None = None,
) -> list[dict[str, Any]]:
    if use_deficit and use_poc_scream:
        raise NaturalMathValidationError("Section 6 runtime flags: use_deficit and use_poc_scream conflict")
    if (bond_collapse_positions or bonding_strict) and not allow_bonding:
        raise NaturalMathValidationError("Section 17 bonding flags: collapse/strict require allow_bonding")
    validate_nodes(nodes, params)
    if not nodes:
        return nodes

    active = sorted([node for node in nodes if node["alive"]], key=lambda n: n["id"])
    for node in active:
        if any(coord < -100 or coord > 100 for coord in node["pos"]):
            die_inert(node)
    for node in active:
        if node["alive"] and node["energy"] < params["tau"]:
            die_inert(node)

    active = sorted([node for node in nodes if node["alive"]], key=lambda n: n["id"])
    all_occupied = {node["pos"] for node in nodes}
    decisions: dict[int, tuple[str, tuple[int, int, int] | None]] = {}
    movement_attempts: dict[tuple[int, int, int], list[int]] = {}
    reserved_child_positions: set[tuple[int, int, int]] = set()
    scheduled_bifurcations: list[dict[str, Any]] = []

    for node in active:
        distances = [
            qdist(node["pos"], other["pos"])
            for other in active
            if other["id"] != node["id"]
            and other["id"] not in node["bonds"]
            and node["id"] not in other["bonds"]
        ]
        min_q = min(distances) if distances else None
        if node["energy"] < params["tau"]:
            decisions[node["id"]] = ("RESTRICT_DIE", None)
        elif min_q is not None and min_q < params["iota_sq"]:
            decisions[node["id"]] = ("RESTRICT_DIE", None)
        elif min_q is not None and min_q == params["iota_sq"]:
            decisions[node["id"]] = ("SENSE", None)
        else:
            direction = gradient_direction(
                node,
                active,
                params,
                use_deficit=use_deficit,
                use_poc_scream=use_poc_scream,
            )
            if direction != (0, 0, 0):
                decisions[node["id"]] = ("EXTEND", direction)
            else:
                if rng is None:
                    raise NaturalMathValidationError("Section 8 rng: required for fallback draw")
                draw = rng.randrange(0, 1000000)
                if draw < params["gamma_fallback_ppm"]:
                    decisions[node["id"]] = ("EXTEND", fallback_direction(node))
                else:
                    decisions[node["id"]] = ("SENSE", None)

    by_id = {node["id"]: node for node in nodes}
    for node_id in sorted(decisions):
        if decisions[node_id][0] == "RESTRICT_DIE":
            die_inert(by_id[node_id])

    for node_id in sorted(decisions):
        if decisions[node_id][0] == "SENSE":
            node = by_id[node_id]
            if node["alive"]:
                node["energy"] = max(0, node["energy"] - params["eps_sense"])
                if node["energy"] < params["tau"]:
                    die_inert(node)

    for node_id in sorted(decisions):
        action, direction = decisions[node_id]
        node = by_id[node_id]
        if action == "EXTEND" and node["alive"]:
            assert direction is not None
            allowed, split_record = can_bifurcate(
                node,
                direction,
                params,
                all_occupied,
                reserved_child_positions,
                mode_allows_bifurcation=not use_poc_scream,
            )
            if allowed:
                assert split_record is not None
                scheduled_bifurcations.append(split_record)
                reserved_child_positions.add(split_record["child_pos_1"])
                reserved_child_positions.add(split_record["child_pos_2"])
                continue
            target = tuple(node["pos"][i] + direction[i] for i in range(3))
            movement_attempts.setdefault(target, []).append(node_id)

    successful_directions: dict[int, tuple[int, int, int]] = {}
    for target in sorted(movement_attempts):
        contenders = movement_attempts[target]
        blocked = target in all_occupied or any(coord < -100 or coord > 100 for coord in target)
        if blocked:
            winners: list[int] = []
            losers = contenders
        elif len(contenders) == 1:
            winners = contenders
            losers = []
        else:
            winners = [min(contenders, key=lambda node_id: (-by_id[node_id]["energy"], node_id))]
            losers = [node_id for node_id in contenders if node_id not in winners]
        for node_id in winners:
            node = by_id[node_id]
            node["pos"] = target
            node["energy"] -= params["eps_extend"]
            successful_directions[node_id] = decisions[node_id][1]  # type: ignore[assignment]
        for node_id in losers:
            node = by_id[node_id]
            node["energy"] = max(0, node["energy"] - params["eps_sense"])
            node["pressure"] += params["delta_P_conflict"]
            if node["energy"] < params["tau"]:
                die_inert(node)

    for node_id in sorted(successful_directions):
        node = by_id[node_id]
        node["direction"] = successful_directions[node_id]
        if node["energy"] < params["tau"]:
            die_inert(node)

    next_id = 1 + max((node["id"] for node in nodes), default=-1)
    for split_record in sorted(scheduled_bifurcations, key=lambda record: record["parent_id"]):
        parent = by_id[split_record["parent_id"]]
        child_energy = (
            split_record["parent_energy_for_split"]
            - params["eps_extend"]
            - params["eps_spawn"]
            - params["eps_split"]
        ) // 2
        parent["alive"] = False
        parent["type"] = "branch"
        parent["energy"] = 0
        child_1 = {
            "id": next_id,
            "pos": split_record["child_pos_1"],
            "direction": split_record["child_direction_1"],
            "energy": child_energy,
            "pressure": 0,
            "alive": True,
            "type": "tip",
            "parent_id": parent["id"],
            "bonds": set(),
            "signal_type": parent["signal_type"],
        }
        child_2 = {
            "id": next_id + 1,
            "pos": split_record["child_pos_2"],
            "direction": split_record["child_direction_2"],
            "energy": child_energy,
            "pressure": 0,
            "alive": True,
            "type": "tip",
            "parent_id": parent["id"],
            "bonds": set(),
            "signal_type": parent["signal_type"],
        }
        nodes.extend([child_1, child_2])
        by_id[child_1["id"]] = child_1
        by_id[child_2["id"]] = child_2
        next_id += 2

    for node in sorted([node for node in nodes if node["alive"]], key=lambda n: n["id"]):
        node["pressure"] = ((node["pressure"] + params["delta_P_baseline"]) * params["beta_num"]) // params["beta_den"]

    if allow_bonding:
        apply_bonding(
            nodes,
            params,
            bond_collapse_positions=bond_collapse_positions,
            bonding_strict=bonding_strict,
        )

    validate_nodes(nodes, params)
    for node in nodes:
        if node["alive"] and node["energy"] < params["tau"]:
            raise NaturalMathValidationError("Section 6A energy: live node below tau")
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    for node in live_by_id.values():
        if live_degree(node, live_by_id) > params["max_bonds"]:
            raise NaturalMathValidationError("Section 6A bonds: live node exceeds max live bonds")
    return nodes


def json_to_nodes(raw_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = copy.deepcopy(raw_nodes)
    for node in nodes:
        node["pos"] = tuple(node["pos"])
        node["direction"] = tuple(node["direction"])
        node["bonds"] = set(node["bonds"])
    return nodes


def nodes_to_json(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for node in sorted(nodes, key=lambda n: n["id"]):
        item = copy.deepcopy(node)
        item["pos"] = list(item["pos"])
        item["direction"] = list(item["direction"])
        item["bonds"] = sorted(item["bonds"])
        result.append(item)
    return result


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
    for fixture in suite["fixtures"]:
        params = copy.deepcopy(DEFAULT_PARAMS)
        params.update(fixture.get("flags", {}).get("params", {}))
        rng_seed = fixture.get("flags", {}).get("rng_seed")
        rng = TraceRng(rng_seed) if rng_seed is not None else None
        nodes = json_to_nodes(fixture["nodes"])
        status = "PASS"
        error = None
        actual_nodes = None
        try:
            flags = fixture.get("flags", {})
            expected_error = fixture.get("expected_error")
            returned = run_step(
                nodes,
                params,
                use_deficit=flags.get("use_deficit", False),
                use_poc_scream=flags.get("use_poc_scream", False),
                allow_bonding=flags.get("allow_bonding", False),
                bond_collapse_positions=flags.get("bond_collapse_positions", False),
                bonding_strict=flags.get("bonding_strict", False),
                rng=rng,
            )
            if expected_error is not None:
                raise AssertionError("expected validation error was not raised")
            if returned is not nodes:
                raise AssertionError("run_step did not return the same nodes list object")
            actual_nodes = nodes_to_json(nodes)
            if actual_nodes != fixture["expected_nodes"]:
                raise AssertionError("final nodes did not match expected_nodes")
            actual_draws = rng.draws if rng is not None else []
            if actual_draws != fixture["expected_random_draws"]:
                raise AssertionError("random draw trace did not match expected_random_draws")
        except Exception as exc:  # noqa: BLE001 - report exact fixture failure
            actual_draws = rng.draws if rng is not None else []
            expected_error = fixture.get("expected_error")
            if expected_error is not None and type(exc).__name__ == expected_error["type"] and expected_error["contains"] in str(exc):
                error = f"{type(exc).__name__}: {exc}"
            else:
                status = "FAIL"
                error = f"{type(exc).__name__}: {exc}"
                all_passed = False
        results["cases"].append(
            {
                "name": fixture["name"],
                "status": status,
                "rng_seed": rng_seed,
                "random_draws": actual_draws,
                "expected_random_draws": fixture["expected_random_draws"],
                "actual_nodes": actual_nodes,
                "error": error,
            }
        )
    results["passed"] = all_passed and all(case["status"] == "PASS" for case in results["cases"])
    return results


def write_report(results: dict[str, Any], report_path: Path) -> None:
    passed_count = sum(1 for case in results["cases"] if case["status"] == "PASS")
    total = len(results["cases"])
    lines = [
        "# Natural Math v5 Integer Oracle Provenance Report",
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
        "- Runner: `natural_math_integer_oracle_runner.py`",
        "",
        "## Covered Sections",
        "",
    ]
    lines.extend(f"- {section}" for section in results["covered_sections"])
    lines.extend(["", "## Case Results", ""])
    for case in results["cases"]:
        lines.append(f"- {case['status']} `{case['name']}`")
        if case["rng_seed"] is not None:
            lines.append(f"  - rng seed: `{case['rng_seed']}`")
            lines.append(f"  - draw_ppm trace: `{case['random_draws']}`")
        if case["error"]:
            lines.append(f"  - error: `{case['error']}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This report proves only that the listed integer fixture packs pass this runner against the named frozen spec hash. It is not a claim that all Natural Math v5 behavior is validated.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default="natural_math_integer_oracle_fixtures.json")
    parser.add_argument("--report", default="natural_math_integer_oracle_results.md")
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    fixtures_path = Path(args.fixtures)
    if not fixtures_path.is_absolute():
        fixtures_path = script_dir / fixtures_path
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = script_dir / report_path
    results = run_suite(fixtures_path)
    write_report(results, report_path)
    print(json.dumps({"passed": results["passed"], "report": str(report_path), "cases": results["cases"]}, indent=2))
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
