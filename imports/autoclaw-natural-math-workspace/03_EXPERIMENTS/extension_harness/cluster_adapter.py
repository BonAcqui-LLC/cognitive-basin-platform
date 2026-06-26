"""Extension Harness — cluster run_cluster adapter.

Wraps the cluster pipeline through the harness hook lifecycle.
"""

from __future__ import annotations

import copy
import sys
from typing import Any

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
import natural_math_v5 as nm
from natural_math_v5.randomness import TraceRng
from natural_math_v5.cluster_initialization import initialize_cluster
from natural_math_v5.cluster_metrics import compute_metrics, select_cluster_action, passed_diagnostic
from natural_math_v5.cluster_actions import (
    apply_damage, apply_resource_absorption,
    apply_cluster_action, kill_below_tau,
)
from natural_math_v5.cluster_step import check_cluster_invariants
from natural_math_v5.parameters import validate_params

from .registry import ExtensionRegistry
from .context import RunContext
from .protocol import (
    ON_RUN_START,
    BEFORE_STEP,
    AFTER_CLUSTER_ACTION_SELECTION,
    AFTER_CLUSTER_ACTION,
    AFTER_RESOURCE_ABSORPTION,
    AFTER_STEP,
    ON_RUN_END,
)
from .snapshots import snapshot_nodes
from .types import HookPhase


def _dispatch(registry, hook_phase, **kwargs):
    """Dispatch a hook to matching extensions."""
    method_name = HookPhase.METHOD_MAP.get(hook_phase)
    if method_name is None:
        return []

    events = []
    for ext, manifest in registry.get_hooks(method_name):
        try:
            result = getattr(ext, method_name)(**kwargs)
            events.append({
                "extension_id": manifest.extension_id,
                "hook": hook_phase,
                "result_type": type(result).__name__,
            })
        except Exception as exc:
            events.append({
                "extension_id": manifest.extension_id,
                "hook": hook_phase,
                "result_type": "ERROR",
                "error": str(exc),
            })
    return events


def run_cluster_through_harness(
    seed: int,
    params: dict[str, Any] | None,
    steps: int,
    registry: ExtensionRegistry,
    run_context: RunContext,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute a full cluster run through the harness hook lifecycle."""
    all_events: list[dict[str, Any]] = []

    if params is None:
        params = nm.default_params()
    else:
        validate_params(params)
        params = copy.deepcopy(params)

    rng = TraceRng(seed)
    state = initialize_cluster(seed, params, rng)

    # 1. ON_RUN_START
    snap = snapshot_nodes(state["nodes"])
    all_events.extend(_dispatch(registry, ON_RUN_START, snapshot=snap))

    # 2. Per-step loop
    for step_index in range(1, steps + 1):
        # BEFORE_STEP
        snap = snapshot_nodes(state["nodes"])
        all_events.extend(_dispatch(registry, BEFORE_STEP, snapshot=snap))

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
            for node in state["nodes"]:
                node["energy"] = max(0, node["energy"])
            kill_below_tau(state["nodes"], params)

        # Action selection
        metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
        action = select_cluster_action(metrics, state["resource_reached"], params)

        snap = snapshot_nodes(state["nodes"])
        all_events.extend(_dispatch(
            registry, AFTER_CLUSTER_ACTION_SELECTION,
            snapshot=snap, action=action, step_index=step_index,
        ))

        # Action application
        apply_cluster_action(action, state, params, rng)
        for node in state["nodes"]:
            node["energy"] = max(0, node["energy"])
        kill_below_tau(state["nodes"], params)

        snap = snapshot_nodes(state["nodes"])
        all_events.extend(_dispatch(
            registry, AFTER_CLUSTER_ACTION,
            snapshot=snap, action=action, step_index=step_index,
        ))

        # Resource absorption
        apply_resource_absorption(state, params)
        for node in state["nodes"]:
            node["energy"] = max(0, node["energy"])
        kill_below_tau(state["nodes"], params)

        snap = snapshot_nodes(state["nodes"])
        all_events.extend(_dispatch(
            registry, AFTER_RESOURCE_ABSORPTION,
            snapshot=snap, step_index=step_index,
        ))

        # Invariants
        check_cluster_invariants(state["nodes"], params)

        # AFTER_STEP
        snap = snapshot_nodes(state["nodes"])
        all_events.extend(_dispatch(registry, AFTER_STEP, snapshot=snap))

    # 3. Build result
    final_metrics = compute_metrics(
        state["nodes"], state["resource_pos"], params
    )
    passed = passed_diagnostic(
        final_metrics, state["resource_reached"], params
    )

    result = {
        "nodes": state["nodes"],
        "resource_pos": state["resource_pos"],
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "metrics": final_metrics,
        "passed": passed,
    }

    # 4. ON_RUN_END
    snap = snapshot_nodes(state["nodes"])
    all_events.extend(_dispatch(registry, ON_RUN_END, snapshot=snap))

    return result, all_events
