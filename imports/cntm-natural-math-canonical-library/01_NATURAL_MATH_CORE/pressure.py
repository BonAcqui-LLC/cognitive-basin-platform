from __future__ import annotations


def accumulate_pressure(current: float, blocked: bool, delta_contact: float = 5.0, decay: float = 0.25) -> float:
    if blocked:
        return current + delta_contact
    return max(0.0, current - decay)


def apply_conflict_pressure(current: float, delta_conflict: float = 2.0) -> float:
    return current + delta_conflict
