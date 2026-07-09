from __future__ import annotations

from .state import NodeState, SimulationState


def _check_unique_node_ids(nodes: list[NodeState]) -> tuple[bool, int]:
    ids = [node.node_id for node in nodes if node.node_id is not None]
    unique = len(ids) == len(set(ids))
    return unique, len(ids)


def _check_parent_order(nodes: list[NodeState]) -> bool:
    for node in nodes:
        if node.parent_id is None:
            continue
        if node.parent_id < 0 or node.parent_id >= len(nodes):
            return False
        if node.node_id is None:
            return False
        if node.parent_id >= node.node_id:
            return False
    return True


def _check_parent_acyclic(nodes: list[NodeState]) -> bool:
    for node in nodes:
        if node.parent_id is None:
            continue
        seen: set[int] = set()
        current = node
        depth = 0
        while current.parent_id is not None and depth < len(nodes) + 1:
            current_id = current.node_id if current.node_id is not None else -1
            if current_id in seen:
                return False
            seen.add(current_id)
            current = nodes[current.parent_id]
            depth += 1
        if depth >= len(nodes) + 1:
            return False
    return True


def _check_no_active_overlap(nodes: list[NodeState]) -> bool:
    positions: set[tuple[int, int, int]] = set()
    for node in nodes:
        if not node.alive:
            continue
        pos = tuple(node.position)
        if pos in positions:
            return False
        positions.add(pos)
    return True


def _check_nonnegative_energy(nodes: list[NodeState]) -> bool:
    return all(node.energy >= -1e-6 for node in nodes)


def _check_inert_energy_zero(nodes: list[NodeState]) -> bool:
    return all((node.node_type != "inert") or abs(node.energy) <= 1e-6 for node in nodes)


def _check_forest_counter(state: SimulationState) -> bool:
    if not state.nodes:
        return state.forest_counter == 0
    max_forest = max(node.forest_id for node in state.nodes)
    return state.forest_counter >= max_forest + 1


def validate_state(state: SimulationState, energy_log: list[float], closed_system: bool = True) -> dict[str, bool | int]:
    energy_non_increasing = True
    if closed_system and len(energy_log) > 1:
        energy_non_increasing = all((energy_log[i] - energy_log[i - 1]) <= 1e-5 for i in range(1, len(energy_log)))

    unique_ids, counted_ids = _check_unique_node_ids(state.nodes)
    return {
        "energy_non_increasing": energy_non_increasing,
        "unique_node_ids": unique_ids,
        "counted_node_ids": counted_ids,
        "valid_parent_order": _check_parent_order(state.nodes),
        "no_parent_cycles": _check_parent_acyclic(state.nodes),
        "no_active_overlap": _check_no_active_overlap(state.nodes),
        "nonnegative_energy": _check_nonnegative_energy(state.nodes),
        "inert_energy_zero": _check_inert_energy_zero(state.nodes),
        "forest_counter_consistent": _check_forest_counter(state),
        "final_frozen": len([node for node in state.nodes if node.alive]) == 0,
    }
