"""Natural Math v5 reference implementation — cluster runner.

Frozen spec: Section 2A, Sections 18-22

Donor: natural_math_cluster_oracle_runner.py, run_cluster_summary function.
"""

from __future__ import annotations

import copy
from typing import Any

from .cluster_initialization import initialize_cluster, live_bond_pairs
from .cluster_metrics import compute_metrics, passed_diagnostic
from .cluster_step import cluster_step
from .errors import NaturalMathValidationError
from .parameters import default_params, validate_params
from .randomness import TraceRng


def run_cluster(
    seed: int,
    params: dict[str, Any] | None = None,
    steps: int = 140,
) -> dict[str, Any]:
    """Section 2A: run full cluster benchmark.

    Args:
        seed: integer RNG seed
        params: parameter dict (None = fresh defaults)
        steps: number of steps (non-negative integer)

    Returns summary dict matching donor's summarize_cluster_result shape.
    """
    if type(seed) is not int:
        raise NaturalMathValidationError("Section 2A seed: must be integer")
    if type(steps) is not int or steps < 0:
        raise NaturalMathValidationError("Section 2A steps: must be non-negative integer")

    if params is None:
        params = default_params()
    else:
        validate_params(params)
        params = copy.deepcopy(params)

    rng = TraceRng(seed)
    state = initialize_cluster(seed, params, rng)

    actions: list[str] = []
    for step_index in range(1, steps + 1):
        action = cluster_step(state, params, rng, step_index)
        actions.append(action)

    metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
    live_nodes = sorted(
        [node for node in state["nodes"] if node["alive"]], key=lambda n: n["id"]
    )

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
            for node in sorted(state["nodes"], key=lambda n: n["id"])[:5]
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
