"""
Stage 2 Extension Harness — Hook Protocol.

Every hook point the harness calls during a run, plus the vocabulary of
valid hook return types that extensions may use.
"""

from __future__ import annotations

# ── Hook-point identifiers ──────────────────────────────────────────────

ON_RUN_START = "ON_RUN_START"
BEFORE_STEP = "BEFORE_STEP"
AFTER_DECISION_FORMATION = "AFTER_DECISION_FORMATION"
AFTER_BIFURCATION_RESERVATION = "AFTER_BIFURCATION_RESERVATION"
AFTER_MOVEMENT_RESOLUTION = "AFTER_MOVEMENT_RESOLUTION"
AFTER_PRESSURE_UPDATE = "AFTER_PRESSURE_UPDATE"
AFTER_BONDING = "AFTER_BONDING"
AFTER_CLUSTER_ACTION_SELECTION = "AFTER_CLUSTER_ACTION_SELECTION"
AFTER_CLUSTER_ACTION = "AFTER_CLUSTER_ACTION"
AFTER_RESOURCE_ABSORPTION = "AFTER_RESOURCE_ABSORPTION"
AFTER_STEP = "AFTER_STEP"
ON_RUN_END = "ON_RUN_END"
PROPOSE_LOCAL_MOVE_PREFERENCE = "PROPOSE_LOCAL_MOVE_PREFERENCE"

# ── Hook classifications ───────────────────────────────────────────────

OBSERVATION_HOOKS = frozenset(
    {
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
    }
)

BEHAVIORAL_HOOKS = frozenset({PROPOSE_LOCAL_MOVE_PREFERENCE})

ALL_HOOKS = OBSERVATION_HOOKS | BEHAVIORAL_HOOKS

# ── Shared enumerations ────────────────────────────────────────────────

VALID_EXTENSION_STATUSES = frozenset(
    {"DRAFT", "EXPERIMENTAL", "VALIDATED_FOR_LISTED_TESTS", "REJECTED", "SUPERSEDED"}
)

VALID_RANDOMNESS_POLICIES = frozenset({"NO_EXTENSION_RANDOMNESS"})


# ── Hook result types ──────────────────────────────────────────────────


class HookResult:
    """Base class for values returned by extension hook callbacks."""

    def is_no_change(self) -> bool:
        return False

    def is_state_update(self) -> bool:
        return False

    def is_proposal(self) -> bool:
        return False


class NoChange(HookResult):
    """Sentinel: the extension observed the state but has nothing to report."""

    def is_no_change(self) -> bool:
        return True


class StateUpdate(HookResult):
    """Extension requests a patch to its own private state store."""

    def __init__(self, state_patch: dict) -> None:
        self.state_patch = state_patch

    def is_state_update(self) -> bool:
        return True


class LocalMovePreferenceProposal(HookResult):
    """
    Extension proposes a directional preference for one specific node's
    next local move step, adjusting the priority with which that direction
    will be considered by the internal resolver.
    """

    def __init__(
        self,
        node_id,
        candidate_direction,
        integer_priority_adjustment: int,
        reason_code: str,
        extension_id: str,
        extension_version: str,
    ) -> None:
        self.node_id = node_id
        self.candidate_direction = candidate_direction
        self.integer_priority_adjustment = integer_priority_adjustment
        self.reason_code = reason_code
        self.extension_id = extension_id
        self.extension_version = extension_version

    def is_proposal(self) -> bool:
        return True


class DiagnosticEvent(HookResult):
    """Extension emits a human-readable diagnostic message (non-actionable)."""

    def __init__(self, message: str) -> None:
        self.message = message
