"""Stage 2 Extension Harness — Hook Result Validation."""

from .errors import HookContractError, ProposalValidationError
from .protocol import (
    BEHAVIORAL_HOOKS,
    DiagnosticEvent,
    HookResult,
    LocalMovePreferenceProposal,
    NoChange,
    OBSERVATION_HOOKS,
    StateUpdate,
)

# Valid cardinal directions for local moves (4-connected grid).
_CARDINAL_DIRECTIONS = frozenset({(0, 1), (0, -1), (1, 0), (-1, 0)})


def validate_hook_result(result, hook_name, extension_id):
    """Validate that *result* is acceptable for *hook_name*.

    Returns the result unchanged on success.

    Raises HookContractError if the result violates the hook contract.
    """
    if not isinstance(result, HookResult):
        raise HookContractError(
            f"Extension {extension_id!r} returned non-HookResult "
            f"from hook {hook_name!r}: {type(result).__name__}"
        )

    # Observation hooks: NoChange, DiagnosticEvent, or StateUpdate only
    if hook_name in OBSERVATION_HOOKS:
        if isinstance(result, LocalMovePreferenceProposal):
            raise HookContractError(
                f"Extension {extension_id!r} returned a proposal from "
                f"observation hook {hook_name!r}"
            )
        # NoChange, DiagnosticEvent, StateUpdate are all acceptable
        return result

    # Behavioral hooks: may return proposals
    if hook_name in BEHAVIORAL_HOOKS:
        if isinstance(result, LocalMovePreferenceProposal):
            # Self-consistency check
            if result.extension_id != extension_id:
                raise HookContractError(
                    f"Proposal extension_id {result.extension_id!r} "
                    f"does not match hook owner {extension_id!r}"
                )
        return result

    raise HookContractError(f"Unknown hook name: {hook_name!r}")


def validate_move_proposal(proposal, nodes, params, occupancy, reserved_positions):
    """Validate a LocalMovePreferenceProposal against current model state.

    Args:
        proposal: The LocalMovePreferenceProposal to validate.
        nodes: List of node objects (must have .id, .position/.pos, .alive).
        params: Parameter dictionary (must include width, height).
        occupancy: Frozenset of occupied positions as (x, y) tuples.
        reserved_positions: Frozenset of reserved positions as (x, y) tuples.

    Returns:
        (True, None) if valid.
        (False, reason_string) if rejected.
    """
    # Reject non-cardinal direction
    direction = tuple(proposal.candidate_direction)
    if direction not in _CARDINAL_DIRECTIONS:
        return False, f"non-cardinal direction: {direction}"

    # Find the node
    target_node = None
    for node in nodes:
        if node.id == proposal.node_id:
            target_node = node
            break

    if target_node is None:
        return False, f"node not found: {proposal.node_id!r}"

    # Reject dead node
    if hasattr(target_node, "alive") and not target_node.alive:
        return False, f"node is dead: {proposal.node_id!r}"

    # Compute current position
    pos = None
    for attr in ("position", "pos"):
        if hasattr(target_node, attr):
            p = getattr(target_node, attr)
            if isinstance(p, (tuple, list)) and len(p) == 2:
                pos = (p[0], p[1])
                break

    if pos is None:
        return False, f"cannot determine position for node {proposal.node_id!r}"

    target_pos = (pos[0] + direction[0], pos[1] + direction[1])

    # Out-of-bounds
    width = params.get("width", params.get("grid_width"))
    height = params.get("height", params.get("grid_height"))
    if width is None or height is None:
        return False, "params missing width/height"

    x, y = target_pos
    if x < 0 or x >= width or y < 0 or y >= height:
        return False, f"target {target_pos} out of bounds ({width}x{height})"

    # Occupied target
    if target_pos in occupancy:
        return False, f"target {target_pos} already occupied"

    # Reserved target
    if target_pos in reserved_positions:
        return False, f"target {target_pos} is reserved"

    # Invalid priority adjustment (must be finite integer)
    adj = proposal.integer_priority_adjustment
    if not isinstance(adj, int):
        return False, f"priority adjustment must be int, got {type(adj).__name__}"

    return True, None
