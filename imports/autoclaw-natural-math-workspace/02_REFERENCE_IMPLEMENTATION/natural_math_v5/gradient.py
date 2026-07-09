"""Natural Math v5 reference implementation — exact rational gradient.

Frozen spec: Section 10 (Integer Gradient Choice)
"""

from __future__ import annotations

from typing import Any

from .arithmetic import qdist
from .parameters import DEFAULT_PARAMS


def deficit(energy: int, params: dict[str, Any]) -> int:
    """Section 9: deficit(E) = max(0, E0 - E)."""
    return max(0, params["E0"] - energy)


def gradient_direction(
    node: dict[str, Any],
    live_nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    use_deficit: bool = False,
    use_poc_scream: bool = False,
) -> tuple[int, int, int]:
    """Section 10: exact rational integer gradient.

    Only live neighbors within 1 ≤ qdist ≤ r_sq are considered.
    Each neighbor contributes (num, den) = (effective * delta_pos[axis], qdist).
    Rational scores are accumulated as (total_num, total_den) per axis.
    Axis with largest absolute rational score wins, ties to x before y before z.
    Returns a cardinal direction (one of the 6 valid directions) plus (0,0,0).

    Section 9 deficit: effective_energy = other.energy - node.energy
      minus deficit_strength * deficit(node) * deficit(other) // (E0 * E0).
    Section 9 PoC scream: if other.energy < 2*tau, effective = suffering_strength.
    """
    # scores[axis] = [numerator, denominator] as rational numbers
    scores: list[list[int]] = [[0, 1], [0, 1], [0, 1]]

    for other in live_nodes:
        if other["id"] == node["id"]:
            continue
        dist = qdist(node["pos"], other["pos"])
        if not (1 <= dist <= params["r_sq"]):
            continue

        # Section 9: effective energy difference
        if use_poc_scream:
            if other["energy"] < 2 * params["tau"]:
                effective = params["suffering_strength"]
            else:
                effective = other["energy"] - node["energy"]
        else:
            effective = other["energy"] - node["energy"]
            if use_deficit:
                effective -= (
                    params["deficit_strength"]
                    * deficit(node["energy"], params)
                    * deficit(other["energy"], params)
                ) // (params["E0"] * params["E0"])

        for axis in range(3):
            c_num = effective * (other["pos"][axis] - node["pos"][axis])
            c_den = dist
            old_num, old_den = scores[axis]
            # Rational addition: a/b + c/d = (a*d + c*b) / (b*d)
            scores[axis] = [old_num * c_den + c_num * old_den, old_den * c_den]

    # Zero gradient → (0,0,0)
    if all(score[0] == 0 for score in scores):
        return (0, 0, 0)

    # Section 10: axis with largest absolute rational score
    # Cross-multiply to compare: |a/b| > |c/d|  ⇔  |a|*d > |c|*b
    best = 0
    for axis in (1, 2):
        if abs(scores[axis][0]) * scores[best][1] > abs(scores[best][0]) * scores[axis][1]:
            best = axis

    direction = [0, 0, 0]
    direction[best] = 1 if scores[best][0] > 0 else -1
    return (direction[0], direction[1], direction[2])
