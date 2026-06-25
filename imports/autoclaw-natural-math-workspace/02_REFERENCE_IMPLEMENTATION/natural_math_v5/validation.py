"""Natural Math v5 reference implementation — validation.

Frozen spec: Section 6 (Validation Rules), Section 6A (Runtime Invariants)
"""

from __future__ import annotations

from typing import Any

from .errors import NaturalMathValidationError
from .records import (
    NODE_FIELDS, LIVE_TYPES, DEAD_TYPES, DIRECTIONS_WITH_ZERO, is_live, occupancy,
)
from .parameters import DEFAULT_PARAMS, validate_params


def as_tuple3(value: Any, field_name: str) -> tuple[int, int, int]:
    """Validate a 3-integer tuple. Section 6.

    Accepts both lists and tuples for backward compatibility with
    test helpers that convert JSON fixtures before calling run_step.
    """
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple"
        )
    result = tuple(value)
    if any(type(v) is not int for v in result):
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple"
        )
    return result  # type: ignore[return-value]


def as_tuple3_strict(value: Any, field_name: str) -> tuple[int, int, int]:
    """Validate a 3-integer tuple. Section 6. Rejects lists.

    The model requires tuples for pos and direction. JSON fixture
    deserialization must convert lists to tuples BEFORE calling run_step.
    This is a test helper responsibility, not model responsibility.
    """
    if not isinstance(value, tuple) or len(value) != 3:
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: must be 3-integer tuple (got {type(value).__name__})"
        )
    if any(type(v) is not int for v in value):
        raise NaturalMathValidationError(
            f"Section 6 {field_name}: all elements must be int"
        )
    return value


def validate_nodes(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    """Section 6: pre-step validation of all nodes and parameters.

    Checks: field set, id uniqueness and type, pos tuple, direction validity,
    energy/pressure types, alive/type consistency, bonds validity,
    signal_type type, bond symmetry, live max degree, param constraints.

    Raises NaturalMathValidationError on any violation.
    """
    if not isinstance(nodes, list):
        raise NaturalMathValidationError("Section 6 nodes: must be mutable list")

    ids: set[int] = set()
    for node in nodes:
        if set(node) != NODE_FIELDS:
            raise NaturalMathValidationError(
                "Section 6 node fields: exact field set required"
            )
        nid = node["id"]
        if type(nid) is not int or nid < 0:
            raise NaturalMathValidationError("Section 6 id: non-negative integer required")
        if nid in ids:
            raise NaturalMathValidationError("Section 6 id: duplicate id")
        ids.add(nid)

        node["pos"] = as_tuple3_strict(node["pos"], "pos")
        node["direction"] = as_tuple3_strict(node["direction"], "direction")
        if node["direction"] not in DIRECTIONS_WITH_ZERO:
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
            raise NaturalMathValidationError("Section 6 alive: dead type must have alive=false")
        if not isinstance(node["bonds"], set) or any(type(v) is not int for v in node["bonds"]):
            raise NaturalMathValidationError("Section 6 bonds: mutable set of integer ids required")
        if type(node["signal_type"]) is not int:
            raise NaturalMathValidationError("Section 6 signal_type: must be integer")

    # Bond target existence
    for node in nodes:
        for bonded_id in node["bonds"]:
            if bonded_id not in ids:
                raise NaturalMathValidationError("Section 6 bonds: bond points to absent id")

    # Live-to-live bond symmetry
    live_by_id = {node["id"]: node for node in nodes if is_live(node)}
    for node in live_by_id.values():
        for bonded_id in node["bonds"]:
            if bonded_id in live_by_id and node["id"] not in live_by_id[bonded_id]["bonds"]:
                raise NaturalMathValidationError("Section 6 bonds: live-to-live bond must be symmetric")

    # Max live bonds
    for node in live_by_id.values():
        if live_degree(node, live_by_id) > params["max_bonds"]:
            raise NaturalMathValidationError("Section 6A bonds: live node exceeds max live bonds")

    validate_params(params)


def live_degree(node: dict[str, Any], live_by_id: dict[int, dict[str, Any]]) -> int:
    """Section 17: count live bonds. Dead bonds stay in record but don't count."""
    return sum(1 for bonded_id in node["bonds"] if bonded_id in live_by_id)


def check_invariants(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    """Section 6A: post-step runtime invariant checks.

    Checks all Section 6A requirements: unique ids, field types, directions,
    energy/pressure non-negative, type consistency, bond symmetry and max.
    Also checks Section 4: no dead live-types, no live dead-types,
    no live nodes with energy below tau (Section 12 post-step kill guarantee).
    """
    validate_nodes(nodes, params)
    # Post-step: all alive nodes must have energy >= tau
    for node in nodes:
        if is_live(node) and node["energy"] < params["tau"]:
            raise NaturalMathValidationError(
                f"Section 6A: live node {node['id']} has energy {node['energy']} < tau {params['tau']}"
            )
