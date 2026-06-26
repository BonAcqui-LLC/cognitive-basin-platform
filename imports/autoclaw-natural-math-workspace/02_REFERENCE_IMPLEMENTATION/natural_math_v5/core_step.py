"""Natural Math v5 reference implementation — core run_step pipeline.

Frozen spec: Sections 2-17, 23. Phase ordering from Section 12 (Simulation Loop).

Donor: natural_math_integer_oracle_runner.py, run_step function.
"""

from __future__ import annotations

from typing import Any

from .bifurcation import can_bifurcate
from .bonding import apply_bonding
from .decisions import fallback_direction
from .errors import NaturalMathValidationError
from .gradient import gradient_direction
from .pressure import update_pressure
from .records import is_live, die_inert
from .arithmetic import qdist, add_pos, inside_world
from .validation import validate_nodes
from .tracing import get_tracer


def run_step(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    use_deficit: bool = False,
    use_poc_scream: bool = False,
    allow_bonding: bool = False,
    bond_collapse_positions: bool = False,
    bonding_strict: bool = False,
    rng: Any = None,
) -> list[dict[str, Any]]:
    """Section 2A: execute one full step of the v5 simulation.

    Returns the SAME nodes list object (mutated in place).
    """
    # Runtime flag conflicts
    if use_deficit and use_poc_scream:
        raise NaturalMathValidationError(
            "Section 6 runtime flags: use_deficit and use_poc_scream conflict"
        )

    validate_nodes(nodes, params)
    tracer = get_tracer()
    if not nodes:
        return nodes

    # Pre-step: kill out-of-bounds nodes, then kill energy-below-tau
    active = sorted(
        [node for node in nodes if node["alive"]], key=lambda n: n["id"]
    )
    for node in active:
        if any(coord < -100 or coord > 100 for coord in node["pos"]):
            die_inert(node)
    for node in active:
        if node["alive"] and node["energy"] < params["tau"]:
            die_inert(node)

    # Recompute active after pre-step kills
    active = sorted(
        [node for node in nodes if node["alive"]], key=lambda n: n["id"]
    )
    all_occupied = {node["pos"] for node in nodes}

    decisions: dict[int, tuple[str, tuple[int, int, int] | None]] = {}
    movement_attempts: dict[tuple[int, int, int], list[int]] = {}
    reserved_child_positions: set[tuple[int, int, int]] = set()
    scheduled_bifurcations: list[dict[str, Any]] = []

    # Phase: compute decisions (Section 11)
    # IMPORTANT: bonded nodes are EXCLUDED from contact computation
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
                node, active, params,
                use_deficit=use_deficit, use_poc_scream=use_poc_scream,
            )
            tracer.record(phase="gradient", node_id=node["id"], direction=direction)
            if direction != (0, 0, 0):
                decisions[node["id"]] = ("EXTEND", direction)
            else:
                if rng is None:
                    raise NaturalMathValidationError(
                        "Section 8 rng: required for fallback draw"
                    )
                draw = rng.randrange(0, 1000000)
                if draw < params["gamma_fallback_ppm"]:
                    decisions[node["id"]] = ("EXTEND", fallback_direction(node))
                else:
                    decisions[node["id"]] = ("SENSE", None)

    for node_id, (decision_type, _direction) in decisions.items():
        tracer.record(phase="decisions", node_id=node_id, decision=decision_type)

    by_id = {node["id"]: node for node in nodes}

    # Phase: kill RESTRICT_DIE nodes immediately
    for node_id in sorted(decisions):
        if decisions[node_id][0] == "RESTRICT_DIE":
            die_inert(by_id[node_id])

    # Phase: apply SENSE costs
    for node_id in sorted(decisions):
        if decisions[node_id][0] == "SENSE":
            node = by_id[node_id]
            if node["alive"]:
                node["energy"] = max(0, node["energy"] - params["eps_sense"])
                if node["energy"] < params["tau"]:
                    die_inert(node)

    # Phase: bifurcation check for EXTEND nodes (before movement)
    for node_id in sorted(decisions):
        action, direction = decisions[node_id]
        node = by_id[node_id]
        if action == "EXTEND" and node["alive"]:
            assert direction is not None
            allowed, split_record = can_bifurcate(
                node, direction, params,
                all_occupied, reserved_child_positions,
                mode_allows_bifurcation=not use_poc_scream,
            )
            tracer.record(phase="bifurcation_check", parent_id=node["id"], can_split=allowed)
            if allowed:
                assert split_record is not None
                scheduled_bifurcations.append(split_record)
                reserved_child_positions.add(split_record["child_pos_1"])
                reserved_child_positions.add(split_record["child_pos_2"])
                continue
            # Not bifurcating: schedule movement attempt
            target = tuple(node["pos"][i] + direction[i] for i in range(3))
            movement_attempts.setdefault(target, []).append(node_id)

    # Phase: movement resolution
    successful_directions: dict[int, tuple[int, int, int]] = {}
    for target in sorted(movement_attempts):
        contenders = movement_attempts[target]
        blocked = (
            target in all_occupied
            or target in reserved_child_positions
            or any(coord < -100 or coord > 100 for coord in target)
        )
        if blocked:
            winners: list[int] = []
            losers = contenders
        elif len(contenders) == 1:
            winners = contenders
            losers = []
        else:
            # Contested: highest energy wins, ties to lower id
            winners = [
                min(contenders, key=lambda nid: (-by_id[nid]["energy"], nid))
            ]
            losers = [nid for nid in contenders if nid not in winners]

        for nid in winners:
            node = by_id[nid]
            node["pos"] = target
            node["energy"] -= params["eps_extend"]
            successful_directions[nid] = decisions[nid][1]  # type: ignore[assignment]
            tracer.record(phase="movement", target=target, winner=nid, loser=None)
        for nid in losers:
            node = by_id[nid]
            node["energy"] = max(0, node["energy"] - params["eps_sense"])
            node["pressure"] += params["delta_P_conflict"]
            tracer.record(phase="movement", target=target, winner=None, loser=nid)
            if node["energy"] < params["tau"]:
                die_inert(node)

    # Update directions for successful movers, kill if energy < tau
    for nid in sorted(successful_directions):
        node = by_id[nid]
        node["direction"] = successful_directions[nid]
        if node["energy"] < params["tau"]:
            die_inert(node)

    # Phase: apply bifurcations
    next_id = 1 + max((node["id"] for node in nodes), default=-1)
    for split_record in sorted(
        scheduled_bifurcations, key=lambda record: record["parent_id"]
    ):
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
        tracer.record(
            phase="bifurcation_apply",
            parent_id=split_record["parent_id"],
            child_1_id=child_1["id"],
            child_2_id=child_2["id"],
        )
        next_id += 2

    # Phase: pressure update (Section 16)
    # IMPORTANT: delta_P_baseline is added HERE, not in movement phase
    pressures_before = {node["id"]: node["pressure"] for node in nodes}
    update_pressure(nodes, params)
    for node in nodes:
        pb = pressures_before.get(node["id"], 0)
        tracer.record(
            phase="pressure",
            node_id=node["id"],
            pressure_before=pb,
            pressure_after=node["pressure"],
        )

    # Phase: bonding (Section 17, optional)
    if allow_bonding:
        apply_bonding(
            nodes, params,
            bond_collapse_positions=bond_collapse_positions,
            bonding_strict=bonding_strict,
        )

    # Phase: post-step validation
    validate_nodes(nodes, params)
    for node in nodes:
        if node["alive"] and node["energy"] < params["tau"]:
            raise NaturalMathValidationError(
                "Section 6A energy: live node below tau"
            )

    return nodes
