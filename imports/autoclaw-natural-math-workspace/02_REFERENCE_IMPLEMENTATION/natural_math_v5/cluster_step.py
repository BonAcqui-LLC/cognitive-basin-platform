"""Natural Math v5 reference implementation — cluster step pipeline.

Frozen spec: Sections 21-22

Donor: natural_math_cluster_oracle_runner.py
"""

from __future__ import annotations

from typing import Any

from .errors import NaturalMathValidationError
from .cluster_actions import (
    apply_damage, apply_resource_absorption, apply_cluster_action, kill_below_tau,
)
from .cluster_initialization import live_degree_bonds
from .cluster_metrics import compute_metrics, select_cluster_action
from .randomness import TraceRng
from .tracing import get_tracer


def check_cluster_invariants(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    ids = [node["id"] for node in nodes]
    if len(ids) != len(set(ids)):
        raise NaturalMathValidationError("Section 6A cluster: duplicate cluster node id")
    by_id = {node["id"]: node for node in nodes}
    live_by_id = {node["id"]: node for node in nodes if node["alive"]}
    for node in nodes:
        for bonded_id in list(node["bonds"]):
            if bonded_id not in by_id:
                raise NaturalMathValidationError("Section 6A cluster: bond points to absent id")
            if node["alive"] and bonded_id in live_by_id and node["id"] not in by_id[bonded_id]["bonds"]:
                raise NaturalMathValidationError("Section 6A cluster: live bond is not symmetric")
        if node["alive"] and live_degree_bonds(node, live_by_id) > params["max_bonds"]:
            raise NaturalMathValidationError("Section 6A cluster: live node exceeds max live bonds")
        if node["alive"] and node["energy"] < params["tau"]:
            raise NaturalMathValidationError("Section 6A cluster: live node below tau")


def cluster_step(
    state: dict[str, Any],
    params: dict[str, Any],
    rng: TraceRng,
    step_index: int,
) -> str:
    """Execute one cluster step. Returns selected action string."""
    tracer = get_tracer()
    # Decay
    for node in sorted(
        [n for n in state["nodes"] if n["alive"]], key=lambda n: n["id"]
    ):
        node["energy"] -= params["decay_cost"]

    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)

    # Damage at step 35
    if step_index == 35:
        apply_damage(state["nodes"], params, rng)
        tracer.record(phase="damage", step=step_index)

    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)

    # Select and apply action
    metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
    action = select_cluster_action(metrics, state["resource_reached"], params)
    apply_cluster_action(action, state, params, rng)
    tracer.record(phase="cluster_action", action=action, step=step_index)

    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)

    # Resource absorption
    apply_resource_absorption(state, params)
    tracer.record(phase="resource_absorption", step=step_index)

    for node in state["nodes"]:
        node["energy"] = max(0, node["energy"])
    kill_below_tau(state["nodes"], params)

    check_cluster_invariants(state["nodes"], params)
    return action
