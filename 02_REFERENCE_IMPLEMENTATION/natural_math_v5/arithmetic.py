"""Natural Math v5 reference implementation — integer arithmetic helpers.

Frozen spec: Section 7 (Helper Rules), Section 2 (Integer Number Rule)
"""

from __future__ import annotations


def integer_div(a: int, b: int) -> int:
    """Section 2: integer_div(a, b) = floor(a / b) where b > 0.

    All calls in the base spec use non-negative numerators.
    """
    return a // b


def qdist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """Section 7: squared grid distance Q(p, q)."""
    return sum((a[i] - b[i]) ** 2 for i in range(3))


def dot(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """Section 7: dot product."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sign(value: int) -> int:
    """Section 7: sign(x). Returns 1, -1, or 0."""
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def clamp_nonnegative(value: int) -> int:
    """Section 7: clamp to non-negative."""
    return max(0, value)


def add_pos(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    """Add two 3d positions."""
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def inside_world(pos: tuple[int, int, int]) -> bool:
    """Section 13: check pos within world boundary (-100 to 100 on all axes)."""
    return all(-100 <= coord <= 100 for coord in pos)


def sort_nodes_by_id(nodes: list[dict]) -> list[dict]:
    """Sort nodes by ascending id for deterministic iteration."""
    return sorted(nodes, key=lambda n: n["id"])
