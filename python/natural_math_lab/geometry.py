"""
Exact rational geometry utilities for Natural Math experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class RationalPoint:
    x: Fraction
    y: Fraction


@dataclass(frozen=True)
class RationalLine:
    a: Fraction
    b: Fraction
    c: Fraction


def quadrance(p: RationalPoint, q: RationalPoint) -> Fraction:
    dx = q.x - p.x
    dy = q.y - p.y
    return dx * dx + dy * dy


def spread(line_a: RationalLine, line_b: RationalLine) -> Fraction:
    numerator = (line_a.a * line_b.b - line_b.a * line_a.b) ** 2
    denominator = (line_a.a * line_a.a + line_a.b * line_a.b) * (line_b.a * line_b.a + line_b.b * line_b.b)
    if denominator == 0:
        raise ValueError("Degenerate line has zero length normal")
    return numerator / denominator


def exact_equal(left: Fraction, right: Fraction) -> bool:
    return left == right


def degeneracy_detected(line: RationalLine) -> bool:
    return line.a == 0 and line.b == 0
