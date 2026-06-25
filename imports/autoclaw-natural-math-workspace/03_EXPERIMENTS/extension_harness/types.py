"""Extension Harness — compatibility shim for types.

This module re-exports types from their canonical locations in the
Stage 2 harness package. Module kept for backward compatibility
with adapter/runner code expecting a .types import.
"""

from .manifest import ExtensionManifest
from .protocol import NoChange, HookResult, DiagnosticEvent, StateUpdate
from .protocol import (
    ON_RUN_START,
    BEFORE_STEP,
    AFTER_DECISION_FORMATION,
    AFTER_BIFURCATION_RESERVATION,
    AFTER_MOVEMENT_RESOLUTION,
    AFTER_PRESSURE_UPDATE,
    AFTER_BONDING,
    AFTER_CLUSTER_ACTION_SELECTION,
    AFTER_CLUSTER_ACTION,
    AFTER_RESOURCE_ABSORPTION,
    AFTER_STEP,
    ON_RUN_END,
    PROPOSE_LOCAL_MOVE_PREFERENCE,
    OBSERVATION_HOOKS,
    BEHAVIORAL_HOOKS,
    ALL_HOOKS,
)
from .registry import ExtensionRegistry
from .context import RunContext
from .snapshots import (
    snapshot_nodes,
    snapshot_occupancy,
    snapshot_params,
    snapshot_decisions,
    snapshot_movement_attempts,
    snapshot_bifurcation_reservations,
    snapshot_resource_state,
    snapshot_cluster_metrics,
)

# ── HookPhase compatibility class ──────────────────────────────────────

class HookPhase:
    """Compatibility class mapping canonical hook names to method names."""

    ON_RUN_START = ON_RUN_START
    BEFORE_STEP = BEFORE_STEP
    AFTER_DECISION_FORMATION = AFTER_DECISION_FORMATION
    AFTER_BIFURCATION_RESERVATION = AFTER_BIFURCATION_RESERVATION
    AFTER_MOVEMENT_RESOLUTION = AFTER_MOVEMENT_RESOLUTION
    AFTER_PRESSURE_UPDATE = AFTER_PRESSURE_UPDATE
    AFTER_BONDING = AFTER_BONDING
    AFTER_CLUSTER_ACTION_SELECTION = AFTER_CLUSTER_ACTION_SELECTION
    AFTER_CLUSTER_ACTION = AFTER_CLUSTER_ACTION
    AFTER_RESOURCE_ABSORPTION = AFTER_RESOURCE_ABSORPTION
    AFTER_STEP = AFTER_STEP
    ON_RUN_END = ON_RUN_END
    PROPOSE_LOCAL_MOVE_PREFERENCE = PROPOSE_LOCAL_MOVE_PREFERENCE

    ALL = ALL_HOOKS

    # Hook name -> method name mapping (lowercase)
    METHOD_MAP: dict[str, str] = {
        ON_RUN_START: "on_run_start",
        BEFORE_STEP: "before_step",
        AFTER_DECISION_FORMATION: "on_after_decision_formation",
        AFTER_BIFURCATION_RESERVATION: "on_after_bifurcation_reservation",
        AFTER_MOVEMENT_RESOLUTION: "on_after_movement_resolution",
        AFTER_PRESSURE_UPDATE: "on_after_pressure_update",
        AFTER_BONDING: "on_after_bonding",
        AFTER_CLUSTER_ACTION_SELECTION: "on_after_cluster_action_selection",
        AFTER_CLUSTER_ACTION: "on_after_cluster_action",
        AFTER_RESOURCE_ABSORPTION: "on_after_resource_absorption",
        AFTER_STEP: "after_step",
        ON_RUN_END: "on_run_end",
        PROPOSE_LOCAL_MOVE_PREFERENCE: "propose_local_move_preference",
    }


# Export all
__all__ = [
    "ExtensionManifest",
    "NoChange",
    "HookResult",
    "DiagnosticEvent",
    "StateUpdate",
    "ExtensionRegistry",
    "RunContext",
    "HookPhase",
    "snapshot_nodes",
    "snapshot_occupancy",
    "snapshot_params",
    "snapshot_decisions",
    "snapshot_movement_attempts",
    "snapshot_bifurcation_reservations",
    "snapshot_resource_state",
    "snapshot_cluster_metrics",
]
