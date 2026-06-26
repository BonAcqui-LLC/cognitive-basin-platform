"""Natural Math v5 reference implementation — fallback direction.

Frozen spec: Section 13 (Fallback Direction)

Donor: natural_math_integer_oracle_runner.py, fallback_direction function.
"""

from __future__ import annotations

from typing import Any

from .errors import NaturalMathValidationError
from .records import DIRECTIONS_WITH_ZERO


def fallback_direction(node: dict[str, Any]) -> tuple[int, int, int]:
    """Section 13: fallback direction uses stored direction field.

    If stored direction is (0,0,0), default to (0,1,0).
    """
    direction = node["direction"]
    if direction not in DIRECTIONS_WITH_ZERO:
        raise NaturalMathValidationError(
            "Section 13 direction: invalid fallback direction"
        )
    return (0, 1, 0) if direction == (0, 0, 0) else direction
