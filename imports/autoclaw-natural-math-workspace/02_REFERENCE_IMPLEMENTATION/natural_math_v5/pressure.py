"""Natural Math v5 reference implementation — pressure update.

Frozen spec: Section 16 (Pressure)

Donor: natural_math_integer_oracle_runner.py, update_pressure inline in run_step.
"""

from __future__ import annotations

from typing import Any


def update_pressure(nodes: list[dict[str, Any]], params: dict[str, Any]) -> None:
    """Section 16: update pressure for each live node (id-sorted).

    pressure = ((pressure + delta_P_baseline) * beta_num) // beta_den

    IMPORTANT: delta_P_baseline is added HERE, not in the movement phase.
    """
    live_sorted = sorted(
        [node for node in nodes if node["alive"]], key=lambda n: n["id"]
    )
    for node in live_sorted:
        node["pressure"] = (
            (node["pressure"] + params["delta_P_baseline"]) * params["beta_num"]
        ) // params["beta_den"]
