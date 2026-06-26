"""Natural Math v5 reference implementation — movement resolution.

Frozen spec: Section 13 (Movement And Blocking)
"""

from __future__ import annotations

from typing import Any

from .arithmetic import add_pos, inside_world


def resolve_movement(
    nodes: list[dict[str, Any]],
    movement_attempts: dict[int, tuple[int, int, int]],
    all_occupied: set[tuple[int, int, int]],
    reserved_child_positions: set[tuple[int, int, int]],
    params: dict[str, Any],
) -> int:
    """Section 13: resolve all scheduled EXTEND/FALLBACK movement attempts.

    A target is blocked if: (a) in frozen all_occupied,
    (b) in reserved_child_positions, (c) outside boundary.

    Uncontested unblocked: winner takes target, pays eps_extend.
    Unblocked contested: winner = highest energy (ties to lower id) takes target, 
      pays eps_extend; losers stay, pay eps_sense, gain delta_P_conflict.
    Blocked (any case): all contenders stay, pay eps_sense, gain delta_P_conflict.

    Returns conflict count.
    """
    by_id: dict[int, dict[str, Any]] = {n["id"]: n for n in nodes}

    # Group contenders by target
    target_contenders: dict[tuple[int, int, int], list[int]] = {}
    for nid, target in movement_attempts.items():
        target_contenders.setdefault(target, []).append(nid)

    conflict_count = 0

    for target, contender_ids in target_contenders.items():
        blocked = (
            target in all_occupied
            or target in reserved_child_positions
            or not inside_world(target)
        )

        if blocked:
            # All contenders are losers
            for cid in contender_ids:
                loser = by_id[cid]
                loser["energy"] = max(0, loser["energy"] - params["eps_sense"])
                if loser["energy"] < params["tau"]:
                    loser["alive"] = False
                    loser["type"] = "inert"
                loser["pressure"] += params["delta_P_conflict"]
        elif len(contender_ids) > 1:
            # Contested unblocked: winner by energy, ties to lower id
            conflict_count += 1
            winner_id = min(contender_ids, key=lambda cid: (-by_id[cid]["energy"], cid))
            for cid in contender_ids:
                if cid == winner_id:
                    w = by_id[cid]
                    w["energy"] -= params["eps_extend"]
                    if w["energy"] < 0:
                        w["energy"] = 0
                        w["alive"] = False
                        w["type"] = "inert"
                    else:
                        w["pos"] = target
                    w["pressure"] += params["delta_P_baseline"]
                else:
                    loser = by_id[cid]
                    loser["energy"] = max(0, loser["energy"] - params["eps_sense"])
                    if loser["energy"] < params["tau"]:
                        loser["alive"] = False
                        loser["type"] = "inert"
                    loser["pressure"] += params["delta_P_conflict"]
        else:
            # Uncontested unblocked: winner takes target
            winner = by_id[contender_ids[0]]
            winner["energy"] -= params["eps_extend"]
            if winner["energy"] < 0:
                winner["energy"] = 0
                winner["alive"] = False
                winner["type"] = "inert"
            else:
                winner["pos"] = target
            winner["pressure"] += params["delta_P_baseline"]

    return conflict_count
