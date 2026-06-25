"""Extension Harness — local run_step adapter.

Wraps nm.run_step through the harness hook lifecycle.
"""

from __future__ import annotations

import sys
from typing import Any

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
import natural_math_v5 as nm

from .registry import ExtensionRegistry
from .context import RunContext
from .protocol import (
    ON_RUN_START,
    BEFORE_STEP,
    AFTER_DECISION_FORMATION,
    AFTER_BIFURCATION_RESERVATION,
    AFTER_MOVEMENT_RESOLUTION,
    AFTER_PRESSURE_UPDATE,
    AFTER_BONDING,
    AFTER_STEP,
    ON_RUN_END,
)
from .snapshots import snapshot_nodes
from .types import HookPhase


def _dispatch(registry, hook_phase, **kwargs):
    """Dispatch a hook to all matching extensions in the registry.

    Uses HookPhase.METHOD_MAP to convert hook phase names to
    the method names expected on extension objects.
    """
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


def run_step_through_harness(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    registry: ExtensionRegistry,
    run_context: RunContext,
    rng: Any = None,
    **kwargs: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute one local step through the harness hook lifecycle."""
    all_events: list[dict[str, Any]] = []

    # 1. ON_RUN_START
    snap = snapshot_nodes(nodes)
    all_events.extend(_dispatch(registry, ON_RUN_START, snapshot=snap))

    # 2. BEFORE_STEP
    snap = snapshot_nodes(nodes)
    all_events.extend(_dispatch(registry, BEFORE_STEP, snapshot=snap, step_index=0))

    # 3. Call baseline run_step
    baseline_kwargs = {}
    for k in ("use_deficit", "use_poc_scream", "allow_bonding",
              "bond_collapse_positions", "bonding_strict"):
        if k in kwargs:
            baseline_kwargs[k] = kwargs[k]
    if rng is not None:
        baseline_kwargs["rng"] = rng

    nm.run_step(nodes, params, **baseline_kwargs)

    # 4. Post-hoc observation hooks
    snap = snapshot_nodes(nodes)
    all_events.extend(_dispatch(registry, AFTER_DECISION_FORMATION, snapshot=snap))
    all_events.extend(_dispatch(registry, AFTER_BIFURCATION_RESERVATION, snapshot=snap))
    all_events.extend(_dispatch(registry, AFTER_MOVEMENT_RESOLUTION, snapshot=snap))
    all_events.extend(_dispatch(registry, AFTER_PRESSURE_UPDATE, snapshot=snap))
    all_events.extend(_dispatch(registry, AFTER_BONDING, snapshot=snap))

    # 5. AFTER_STEP
    snap = snapshot_nodes(nodes)
    all_events.extend(_dispatch(registry, AFTER_STEP, snapshot=snap, step_index=0))

    # 6. ON_RUN_END
    snap = snapshot_nodes(nodes)
    all_events.extend(_dispatch(registry, ON_RUN_END, snapshot=snap))

    return nodes, all_events
