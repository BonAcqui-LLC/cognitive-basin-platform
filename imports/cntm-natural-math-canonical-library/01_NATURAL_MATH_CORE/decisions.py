from __future__ import annotations

from typing import Iterable

import numpy as np

from .lattice import quadrance
from .state import NodeState

EXTEND = "EXTEND"
SENSE = "SENSE"
RESTRICT = "RESTRICT"
CONSERVE = "CONSERVE"
REPRODUCE = "REPRODUCE"

DECISIONS = [EXTEND, SENSE, RESTRICT, CONSERVE, REPRODUCE]


def compute_gradient(
    node: NodeState,
    active_nodes: Iterable[NodeState],
    trail_map: dict[tuple[int, int, int], float],
    gamma: float,
    radius: float,
) -> np.ndarray:
    grad_energy = np.zeros(3, dtype=float)
    grad_trail = np.zeros(3, dtype=float)
    pos_p = np.array(node.position, dtype=int)
    energy_p = node.energy
    for other in active_nodes:
        if other.node_id == node.node_id:
            continue
        pos_q = np.array(other.position, dtype=int)
        q_dist_sq = quadrance(pos_p, pos_q)
        if q_dist_sq > radius:
            continue
        denom = max(q_dist_sq, 1)
        weight = 1.0 / denom
        q_vec = pos_q - pos_p
        grad_energy += (other.energy - energy_p) * weight * q_vec
        trail_p = trail_map.get(tuple(pos_p), 0.0)
        trail_q = trail_map.get(tuple(pos_q), 0.0)
        grad_trail += (trail_q - trail_p) * weight * q_vec
    return grad_energy - gamma * grad_trail


def gradient_magnitude_sq(grad: np.ndarray) -> float:
    return float(quadrance(grad.astype(int), (0, 0, 0)))


def decide(
    node: NodeState,
    active_nodes: list[NodeState],
    trail_map: dict[tuple[int, int, int], float],
    params: dict[str, float | int],
    expansion_efficiency: float = 1.0,
) -> int:
    tau = float(params["tau"])
    iota = float(params["iota"])
    eta_sq = float(params["eta_sq"])
    gamma = float(params["gamma"])
    p_hibernate = float(params["P_hibernate"])
    p_bifurcate = float(params["P_bifurcate"])
    radius = float(params["R"])
    eps_sense = float(params["eps_sense"])
    eps_split = float(params["eps_split"])

    if node.parent_id is not None and node.pressure > p_hibernate:
        return -2

    min_q = float("inf")
    for other in active_nodes:
        if other.node_id == node.node_id:
            continue
        d2 = quadrance(node.position, other.position)
        if d2 < min_q:
            min_q = d2

    if node.energy < tau or min_q < iota**2:
        if (node.energy - eps_sense < tau) and (node.parent_id is not None):
            return -2
        return -1

    if (
        node.parent_id is not None
        and node.energy >= float(params["E_reproduce"])
        and node.node_type == "tip"
        and node.energy > tau * 10
        and expansion_efficiency < float(params["eta_reproduce"])
    ):
        return -3

    grad = compute_gradient(node, active_nodes, trail_map, gamma, radius)
    grad_mag_sq = gradient_magnitude_sq(grad)
    if node.energy >= tau and min_q > iota**2 and grad_mag_sq > eta_sq:
        if node.pressure >= p_bifurcate:
            if node.energy >= eps_split + 2 * tau:
                return +1
        else:
            return +1

    return 0
