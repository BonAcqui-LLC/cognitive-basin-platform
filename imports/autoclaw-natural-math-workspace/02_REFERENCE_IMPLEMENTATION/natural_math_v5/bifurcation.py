"""Natural Math v5 reference implementation — bifurcation.

Frozen spec: Section 14 (Bifurcation), Section 15 (Child Direction Table)

Donor: natural_math_integer_oracle_runner.py
"""

from __future__ import annotations

from typing import Any

from .arithmetic import add_pos, inside_world
from .records import DIRECTIONS_WITH_ZERO
from .errors import NaturalMathValidationError


def child_directions(direction: tuple[int, int, int]) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Section 15: fixed child direction table based on movement direction axis."""
    if direction in {(1, 0, 0), (-1, 0, 0)}:
        return (0, 1, 0), (0, 0, 1)
    if direction in {(0, 1, 0), (0, -1, 0)}:
        return (1, 0, 0), (0, 0, 1)
    if direction in {(0, 0, 1), (0, 0, -1)}:
        return (1, 0, 0), (0, 1, 0)
    if direction == (0, 0, 0):
        return (1, 0, 0), (0, 1, 0)
    raise NaturalMathValidationError(
        "Section 15 movement_direction: invalid child direction source"
    )


def can_bifurcate(
    node: dict[str, Any],
    direction: tuple[int, int, int],
    params: dict[str, Any],
    all_occupied: set[tuple[int, int, int]],
    reserved_child_positions: set[tuple[int, int, int]],
    *,
    mode_allows_bifurcation: bool,
) -> tuple[bool, dict[str, Any] | None]:
    """Section 14: check if node can bifurcate.

    Returns (can_split, split_record).
    Record keys match donor: parent_id, parent_energy_for_split,
    movement_direction, child_direction_1, child_direction_2,
    child_pos_1, child_pos_2.
    """
    first_direction, second_direction = child_directions(direction)
    first_pos = add_pos(node["pos"], first_direction)
    second_pos = add_pos(node["pos"], second_direction)

    if not node["alive"]:
        return False, None
    if not mode_allows_bifurcation:
        return False, None
    if node["pressure"] < params["P_bifurcate"]:
        return False, None
    required = params["eps_extend"] + params["eps_spawn"] + params["eps_split"] + 2 * params["tau"]
    if node["energy"] <= required:
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
