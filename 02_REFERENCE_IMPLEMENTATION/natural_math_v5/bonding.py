"""Natural Math v5 reference implementation — bonding.

Frozen spec: Section 17 (Bonding)

Donor: natural_math_integer_oracle_runner.py, apply_bonding function.
"""

from __future__ import annotations

from typing import Any

from .arithmetic import qdist
from .validation import live_degree


def apply_bonding(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    bond_collapse_positions: bool = False,
    bonding_strict: bool = False,
) -> None:
    """Section 17: form bonds between eligible live node pairs.

    Iterates ALL pairs (a.id < b.id). For each:
    - Distance must be < bond_distance_sq (strict) or <= (non-strict).
    - Both must have live_degree < max_bonds.
    - No existing bond between them.
    - Energy equalization: total // 2 and total - half.
    """
    live_nodes = sorted(
        [node for node in nodes if node["alive"]], key=lambda n: n["id"]
    )
    live_by_id = {node["id"]: node for node in live_nodes}
    pairs = [
        (a, b)
        for index, a in enumerate(live_nodes)
        for b in live_nodes[index + 1:]
    ]

    for a, b in pairs:
        dist_sq = qdist(a["pos"], b["pos"])
        distance_allowed = (
            dist_sq < params["bond_distance_sq"]
            if bonding_strict
            else dist_sq <= params["bond_distance_sq"]
        )
        if not distance_allowed:
            continue
        if (
            live_degree(a, live_by_id) >= params["max_bonds"]
            or live_degree(b, live_by_id) >= params["max_bonds"]
        ):
            continue
        if b["id"] in a["bonds"] or a["id"] in b["bonds"]:
            continue

        a["bonds"].add(b["id"])
        b["bonds"].add(a["id"])
        total = a["energy"] + b["energy"]
        a["energy"] = total // 2
        b["energy"] = total - a["energy"]
        if bond_collapse_positions:
            b["pos"] = a["pos"]
