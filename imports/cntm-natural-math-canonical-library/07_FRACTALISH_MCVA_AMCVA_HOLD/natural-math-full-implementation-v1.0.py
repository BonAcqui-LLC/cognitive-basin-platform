from __future__ import annotations

import argparse
import csv
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import random

import numpy as np


@dataclass
class NodeState:
    position: tuple[int, int, int]
    direction: tuple[int, int, int]
    energy: float
    pressure: float = 0.0
    alive: bool = True
    parent_id: int | None = None
    node_id: int | None = None
    forest_id: int = 0
    node_type: str = "tip"


@dataclass
class SimulationState:
    nodes: list[NodeState] = field(default_factory=list)
    step_count: int = 0
    forest_counter: int = 0
    initial_forest_count: int = 0
    birth_events: int = 0
    trail: dict[tuple[int, int, int], float] = field(default_factory=dict)
    environment: dict[tuple[int, int, int], str] = field(default_factory=dict)
    forest_params: dict[int, dict[str, float]] = field(default_factory=dict)
    history_active: list[int] = field(default_factory=list)
    history_energy: list[float] = field(default_factory=list)
    history_forests: list[int] = field(default_factory=list)
    event_log: list[dict[str, object]] = field(default_factory=list)


def quadrance(u: tuple[int, int, int] | np.ndarray, v: tuple[int, int, int] | np.ndarray) -> int:
    return int(sum((int(u[i]) - int(v[i])) ** 2 for i in range(3)))


def spread(u: tuple[int, int, int] | np.ndarray, v: tuple[int, int, int] | np.ndarray) -> float:
    q_u = quadrance(u, (0, 0, 0))
    q_v = quadrance(v, (0, 0, 0))
    if q_u == 0 or q_v == 0:
        return 0.0
    cross = np.cross(u, v)
    q_cross = quadrance(cross, (0, 0, 0))
    return q_cross / (q_u * q_v)


def perpendicular_vector(v: tuple[int, int, int] | np.ndarray) -> np.ndarray:
    vec = np.array(v, dtype=int)
    for i in range(3):
        if vec[i] != 0:
            w = np.zeros(3, dtype=int)
            w[(i + 1) % 3] = vec[i]
            w[(i + 2) % 3] = -vec[(i + 1) % 3]
            if quadrance(vec, w) > 0:
                return w
    return np.array([1, 0, 0], dtype=int)


def rational_sqrt_approx(x: float, max_iter: int = 50) -> float:
    if x < 0:
        return 0.0
    a, b = 1, 1
    for _ in range(max_iter):
        a_new = (a + x * b) // 2
        b_new = a
        a, b = a_new, b_new
        if b == 0:
            break
        if a * a == x * b * b:
            return a / b
    return math.sqrt(x)


def bifurcation_children(v0: tuple[int, int, int] | np.ndarray, s: float) -> tuple[np.ndarray, np.ndarray]:
    parent = np.array(v0, dtype=int)
    w = perpendicular_vector(parent)
    q_v0 = quadrance(parent, (0, 0, 0))
    q_w = quadrance(w, (0, 0, 0))
    if q_v0 == 0 or q_w == 0:
        return parent.copy(), parent.copy()
    k_sq = (s / (1 - s)) * (q_v0 / q_w)
    k = rational_sqrt_approx(k_sq)
    if k == 0:
        return parent.copy(), parent.copy()
    v1 = parent + int(round(k)) * w
    v2 = parent - int(round(k)) * w
    return v1, v2


EXTEND = "EXTEND"
SENSE = "SENSE"
RESTRICT = "RESTRICT"
CONSERVE = "CONSERVE"
REPRODUCE = "REPRODUCE"


def compute_gradient(
    node: NodeState,
    active_nodes: list[NodeState],
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


def total_active_energy(nodes: list[NodeState]) -> float:
    return float(sum(node.energy for node in nodes if node.alive))


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


def default_params() -> dict[str, float | int]:
    return {
        "tau": 8.0,
        "iota": 2,
        "eta_sq": 1.0,
        "gamma": 1.0,
        "P_hibernate": 40,
        "P_bifurcate": 20,
        "P_erode": 50,
        "Delta_P_contact": 5,
        "Delta_P_conflict": 2,
        "eps_extend": 10,
        "eps_sense": 2,
        "eps_conserve": 1,
        "eps_split": 14,
        "eps_spawn": 7,
        "beta": 0.8,
        "s": 0.25,
        "s_min": 1 / 16,
        "s_max": 1 / 2,
        "R": 25,
        "delta": 2,
        "trail_deposit": 0.5,
        "trail_decay": 0.01,
        "E_reproduce": 50,
        "eps_reproduce": 10,
        "eta_reproduce": 0.1,
        "E_max_seed": 100,
        "sigma_mutate": 1.0,
        "seed": 7,
    }


def smoke_profile() -> dict[str, object]:
    return {
        "params": {},
        "seed_layout": [
            ((0, 0, 0), (0, 1, 0), 400.0, 0),
            ((10, 0, 0), (0, 1, 0), 400.0, 1),
            ((-10, 0, 0), (0, 1, 0), 400.0, 2),
        ],
        "add_test_obstacles": False,
    }


def growth_demo_profile() -> dict[str, object]:
    return {
        "params": {
            "iota": 1,
            "eta_sq": 0.0,
            "P_bifurcate": 10.0,
        },
        "seed_layout": [
            ((0, 0, 0), (1, 0, 0), 100.0, 0),
            ((3, 0, 0), (-1, 0, 0), 1000.0, 1),
        ],
        "add_test_obstacles": False,
    }


def obstacle_growth_profile() -> dict[str, object]:
    return {
        "params": {
            "iota": 1,
            "eta_sq": 0.0,
            "P_bifurcate": 5.0,
        },
        "seed_layout": [
            ((0, 0, 0), (1, 0, 0), 400.0, 0),
            ((3, 0, 0), (-1, 0, 0), 1000.0, 1),
        ],
        "add_test_obstacles": True,
    }


def bifurcation_demo_profile() -> dict[str, object]:
    return {
        "params": {
            "iota": 1,
            "eta_sq": 0.0,
            "P_bifurcate": 1.0,
        },
        "seed_layout": [
            ((0, 0, 0), (1, 0, 0), 600.0, 0),
            ((4, 0, 0), (-1, 0, 0), 1000.0, 1),
        ],
        "add_test_obstacles": False,
        "manual_obstacles": [(1, 0, 0)],
    }


def get_profile(name: str) -> dict[str, object]:
    profiles = {
        "smoke": smoke_profile,
        "growth-demo": growth_demo_profile,
        "obstacle-growth": obstacle_growth_profile,
        "bifurcation-demo": bifurcation_demo_profile,
    }
    if name not in profiles:
        raise ValueError(f"Unknown Natural Math profile: {name}")
    return profiles[name]()


def export_state(path: Path, state: dict[str, object]) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def export_history_csv(path: Path, simulator: "NaturalMathSimulator") -> None:
    validation = simulator.validate()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "step",
                "active_sites",
                "active_energy",
                "active_forests",
                "energy_non_increasing",
                "no_parent_cycles",
                "no_active_overlap",
            ]
        )
        for idx, (active, energy, forests) in enumerate(
            zip(simulator.state.history_active, simulator.state.history_energy, simulator.state.history_forests),
            start=1,
        ):
            writer.writerow(
                [
                    idx,
                    active,
                    energy,
                    forests,
                    validation["energy_non_increasing"],
                    validation["no_parent_cycles"],
                    validation["no_active_overlap"],
                ]
            )


def export_event_csv(path: Path, simulator: "NaturalMathSimulator") -> None:
    if not simulator.state.event_log:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(simulator.state.event_log[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(simulator.state.event_log)


class NaturalMathSimulator:
    """Full Implementation v1.0 consolidated into one source file."""

    def __init__(self, params: dict[str, float | int] | None = None) -> None:
        merged = default_params()
        if params:
            merged.update(params)
        self.params = merged
        seed = int(self.params.get("seed", 7))
        np.random.seed(seed)
        random.seed(seed)
        self.state = SimulationState()
        self.forest_recent_novel: dict[int, deque[int]] = defaultdict(lambda: deque(maxlen=20))
        self.forest_recent_energy: dict[int, deque[float]] = defaultdict(lambda: deque(maxlen=20))
        self.forest_seen_positions: dict[int, set[tuple[int, int, int]]] = defaultdict(set)
        self.energy_log: list[float] = []

    def add_obstacle(self, pos: tuple[int, int, int]) -> None:
        self.state.environment[tuple(pos)] = "obstacle"

    def add_test_obstacles(self) -> None:
        for x in range(-5, 6):
            self.add_obstacle((x, 15, 0))
            self.add_obstacle((x, -15, 0))

    def add_seed(
        self,
        pos: tuple[int, int, int],
        direction: tuple[int, int, int],
        energy: float,
        forest_id: int | None = None,
    ) -> NodeState:
        if forest_id is None:
            forest_id = self.state.forest_counter
            self.state.forest_counter += 1
        else:
            self.state.forest_counter = max(self.state.forest_counter, forest_id + 1)
        node = NodeState(
            position=pos,
            direction=direction,
            energy=float(energy),
            parent_id=None,
            node_id=len(self.state.nodes),
            forest_id=forest_id,
            node_type="tip",
        )
        self.state.nodes.append(node)
        self.forest_seen_positions[forest_id].add(tuple(node.position))
        if forest_id not in self.state.forest_params:
            self.state.forest_params[forest_id] = {}
        return node

    def get_active_nodes(self) -> list[NodeState]:
        return [node for node in self.state.nodes if node.alive]

    def _depth(self, node: NodeState) -> int:
        if node.parent_id is None:
            return 0
        return 1 + self._depth(self.state.nodes[node.parent_id])

    def expansion_efficiency_by_forest(self) -> dict[int, float]:
        lookup: dict[int, float] = {}
        for forest_id in {node.forest_id for node in self.state.nodes}:
            novel_series = self.forest_recent_novel[forest_id]
            energy_series = self.forest_recent_energy[forest_id]
            total_novel = float(sum(novel_series))
            total_energy = float(sum(energy_series))
            lookup[forest_id] = total_novel / total_energy if total_energy > 0 else 1.0
        return lookup

    def _params_for_forest(self, forest_id: int) -> dict[str, float | int]:
        merged = dict(self.params)
        merged.update(self.state.forest_params.get(forest_id, {}))
        return merged

    def phase1_decisions(self) -> dict[int, int]:
        active = self.get_active_nodes()
        decisions: dict[int, int] = {}
        efficiency_lookup = self.expansion_efficiency_by_forest()
        for node in active:
            decisions[node.node_id or 0] = decide(
                node,
                active,
                self.state.trail,
                self._params_for_forest(node.forest_id),
                expansion_efficiency=efficiency_lookup.get(node.forest_id, 1.0),
            )
        return decisions

    def phase2_conserve(self, decisions: dict[int, int], step_energy_spent: dict[int, float]) -> int:
        active = self.get_active_nodes()
        conservers = [node for node in active if decisions[node.node_id or 0] == -2]
        conservers.sort(key=lambda node: self._depth(node), reverse=True)

        buffer_energy: dict[int, float] = defaultdict(float)
        buffer_pressure: dict[int, float] = defaultdict(float)
        for node in conservers:
            if node.parent_id is None:
                continue
            step_energy_spent[node.forest_id] += float(self.params["eps_conserve"])
            recovered = float(self.params["beta"]) * (node.energy - float(self.params["eps_conserve"]))
            buffer_energy[node.parent_id] += recovered
            buffer_pressure[node.parent_id] += float(self.params["beta"]) * node.pressure
            node.alive = False
            node.energy = 0.0
            node.node_type = "inert"

        for parent_id, energy in buffer_energy.items():
            self.state.nodes[parent_id].energy += energy
        for parent_id, pressure in buffer_pressure.items():
            self.state.nodes[parent_id].pressure += pressure
        return len(conservers)

    def phase3_candidates(self, decisions: dict[int, int]) -> list[tuple[int, np.ndarray, np.ndarray, bool]]:
        candidates: list[tuple[int, np.ndarray, np.ndarray, bool]] = []
        for node in self.get_active_nodes():
            if decisions[node.node_id or 0] != +1:
                continue
            forest_params = self._params_for_forest(node.forest_id)
            if node.pressure >= float(forest_params["P_bifurcate"]):
                if node.energy >= float(forest_params["eps_split"]) + 2 * float(forest_params["tau"]):
                    v1, v2 = bifurcation_children(node.direction, float(forest_params["s"]))
                    new_pos_1 = np.array(node.position, dtype=int) + np.array(v1, dtype=int)
                    new_pos_2 = np.array(node.position, dtype=int) + np.array(v2, dtype=int)
                    candidates.append((node.node_id or 0, new_pos_1, v1, True))
                    candidates.append((node.node_id or 0, new_pos_2, v2, True))
                else:
                    new_pos = np.array(node.position, dtype=int) + np.array(node.direction, dtype=int)
                    candidates.append((node.node_id or 0, new_pos, np.array(node.direction, dtype=int), False))
            else:
                new_pos = np.array(node.position, dtype=int) + np.array(node.direction, dtype=int)
                candidates.append((node.node_id or 0, new_pos, np.array(node.direction, dtype=int), False))
        return candidates

    def phase4a_obstacles(
        self,
        candidates: list[tuple[int, np.ndarray, np.ndarray, bool]],
        step_energy_spent: dict[int, float],
    ) -> tuple[list[tuple[int, np.ndarray, np.ndarray, bool]], set[int]]:
        occupied = {tuple(node.position) for node in self.get_active_nodes()}
        valid: list[tuple[int, np.ndarray, np.ndarray, bool]] = []
        rejected_parents: set[int] = set()
        for node_id, pos, direction, is_bifurcation in candidates:
            if tuple(pos) in occupied or self.state.environment.get(tuple(map(int, pos))) == "obstacle":
                node = self.state.nodes[node_id]
                node.pressure += float(self.params["Delta_P_contact"])
                node.energy -= float(self.params["eps_extend"])
                step_energy_spent[node.forest_id] += float(self.params["eps_extend"])
                rejected_parents.add(node_id)
            else:
                valid.append((node_id, pos, direction, is_bifurcation))
        return valid, rejected_parents

    def phase4b_conflicts(
        self,
        candidates: list[tuple[int, np.ndarray, np.ndarray, bool]],
    ) -> tuple[list[tuple[int, np.ndarray, np.ndarray, bool]], list[tuple[int, np.ndarray, np.ndarray, bool]]]:
        buckets: dict[tuple[int, int, int], list[tuple[int, np.ndarray, np.ndarray, bool]]] = defaultdict(list)
        iota_sq = float(self.params["iota"]) ** 2
        for node_id, pos, direction, is_bifurcation in candidates:
            key = (
                int(pos[0] // int(self.params["iota"])),
                int(pos[1] // int(self.params["iota"])),
                int(pos[2] // int(self.params["iota"])),
            )
            buckets[key].append((node_id, pos, direction, is_bifurcation))

        winners: list[tuple[int, np.ndarray, np.ndarray, bool]] = []
        losers: list[tuple[int, np.ndarray, np.ndarray, bool]] = []
        for bucket in buckets.values():
            for i, (id1, p1, d1, b1) in enumerate(bucket):
                conflicts: list[tuple[int, np.ndarray, np.ndarray, bool]] = []
                for j, (id2, p2, d2, b2) in enumerate(bucket):
                    if i >= j:
                        continue
                    if quadrance(tuple(map(int, p1)), tuple(map(int, p2))) <= iota_sq:
                        conflicts.append((id2, p2, d2, b2))
                if not conflicts:
                    winners.append((id1, p1, d1, b1))
                else:
                    loser_candidate = min(conflicts, key=lambda item: self.state.nodes[item[0]].energy)
                    if self.state.nodes[loser_candidate[0]].energy < self.state.nodes[id1].energy:
                        losers.append((id1, p1, d1, b1))
                        winners.append(loser_candidate)
                    else:
                        winners.append((id1, p1, d1, b1))
                        losers.extend(conflicts)
        return winners, losers

    def phase5_apply(
        self,
        decisions: dict[int, int],
        winners: list[tuple[int, np.ndarray, np.ndarray, bool]],
        losers: list[tuple[int, np.ndarray, np.ndarray, bool]],
        step_energy_spent: dict[int, float],
    ) -> dict[str, int]:
        active = self.get_active_nodes()
        step_novel_positions: dict[int, int] = defaultdict(int)
        event_counts = {
            "sense_actions": 0,
            "conflict_losses": 0,
            "restrict_deaths": 0,
            "bifurcations": 0,
            "single_child_extensions": 0,
            "new_children": 0,
            "reproduction_births": 0,
        }

        for node in active:
            node_id = node.node_id or 0
            if decisions[node_id] == 0:
                node.energy -= float(self.params["eps_sense"])
                step_energy_spent[node.forest_id] += float(self.params["eps_sense"])
                event_counts["sense_actions"] += 1

        for node_id, _, _, _ in losers:
            node = self.state.nodes[node_id]
            node.energy -= float(self.params["eps_sense"])
            node.pressure += float(self.params["Delta_P_conflict"])
            step_energy_spent[node.forest_id] += float(self.params["eps_sense"])
            event_counts["conflict_losses"] += 1

        for node in active:
            if decisions[node.node_id or 0] == -1:
                node.alive = False
                node.energy = 0.0
                node.node_type = "inert"
                event_counts["restrict_deaths"] += 1

        for node_id, new_pos, direction, is_bifurcation in winners:
            node = self.state.nodes[node_id]
            if is_bifurcation:
                child_energy = (node.energy - float(self.params["eps_split"])) / 2.0
                v1, v2 = bifurcation_children(node.direction, float(self.params["s"]))
                step_energy_spent[node.forest_id] += float(self.params["eps_split"])
                child_1 = NodeState(
                    position=tuple(map(int, new_pos)),
                    direction=tuple(map(int, v1)),
                    energy=child_energy,
                    parent_id=node_id,
                    node_id=len(self.state.nodes),
                    forest_id=node.forest_id,
                    node_type="tip",
                )
                child_2 = NodeState(
                    position=tuple(map(int, new_pos)),
                    direction=tuple(map(int, v2)),
                    energy=child_energy,
                    parent_id=node_id,
                    node_id=len(self.state.nodes) + 1,
                    forest_id=node.forest_id,
                    node_type="tip",
                )
                self.state.nodes.extend([child_1, child_2])
                event_counts["bifurcations"] += 1
                event_counts["new_children"] += 2
                for child in (child_1, child_2):
                    pos_key = tuple(child.position)
                    if pos_key not in self.forest_seen_positions[child.forest_id]:
                        self.forest_seen_positions[child.forest_id].add(pos_key)
                        step_novel_positions[child.forest_id] += 1
                node.node_type = "branch"
                node.energy = 0.0
            else:
                child_energy = node.energy - float(self.params["eps_extend"]) - float(self.params["eps_spawn"])
                step_energy_spent[node.forest_id] += float(self.params["eps_extend"]) + float(self.params["eps_spawn"])
                child = NodeState(
                    position=tuple(map(int, new_pos)),
                    direction=tuple(map(int, direction)),
                    energy=child_energy,
                    parent_id=node_id,
                    node_id=len(self.state.nodes),
                    forest_id=node.forest_id,
                    node_type="tip",
                )
                self.state.nodes.append(child)
                event_counts["single_child_extensions"] += 1
                event_counts["new_children"] += 1
                pos_key = tuple(child.position)
                if pos_key not in self.forest_seen_positions[child.forest_id]:
                    self.forest_seen_positions[child.forest_id].add(pos_key)
                    step_novel_positions[child.forest_id] += 1
                node.node_type = "branch"
                node.energy = 0.0
                node.direction = tuple(map(int, direction))

        for node in active:
            if decisions[node.node_id or 0] == -3:
                disp_vec = np.random.randint(-20, 21, size=3)
                disp_pos = np.array(node.position, dtype=int) + disp_vec
                seed_energy = min(node.energy - float(self.params["eps_reproduce"]), float(self.params["E_max_seed"]))
                if seed_energy > 0:
                    new_forest_id = self.state.forest_counter
                    self.state.forest_counter += 1
                    self.state.birth_events += 1
                    event_counts["reproduction_births"] += 1
                    step_energy_spent[node.forest_id] += float(self.params["eps_reproduce"])
                    parent_pb = self.state.forest_params.get(node.forest_id, {}).get(
                        "P_bifurcate", float(self.params["P_bifurcate"])
                    )
                    sigma = float(self.params["sigma_mutate"])
                    new_pb = max(5.0, min(100.0, parent_pb + float(np.random.normal(0, sigma))))
                    self.state.forest_params[new_forest_id] = {"P_bifurcate": new_pb}
                    offspring = NodeState(
                        position=tuple(map(int, disp_pos)),
                        direction=node.direction,
                        energy=seed_energy,
                        parent_id=None,
                        node_id=len(self.state.nodes),
                        forest_id=new_forest_id,
                        node_type="tip",
                    )
                    self.state.nodes.append(offspring)
                    self.forest_seen_positions[new_forest_id].add(tuple(offspring.position))
                    step_novel_positions[new_forest_id] += 1
                    node.alive = False
                    node.energy = 0.0
                    node.node_type = "inert"

        for node in self.get_active_nodes():
            if node.node_type != "inert":
                self.state.trail[tuple(node.position)] = self.state.trail.get(tuple(node.position), 0.0) + float(
                    self.params["trail_deposit"]
                )

        for key in list(self.state.trail.keys()):
            self.state.trail[key] -= float(self.params["trail_decay"])
            if self.state.trail[key] <= 0:
                del self.state.trail[key]

        for node in self.state.nodes:
            if not node.alive:
                node.pressure = 0.0

        for forest_id in {node.forest_id for node in self.state.nodes}:
            self.forest_recent_novel[forest_id].append(step_novel_positions.get(forest_id, 0))
            self.forest_recent_energy[forest_id].append(step_energy_spent.get(forest_id, 0.0))
        return event_counts

    def apply_external_input(self) -> None:
        external_input = float(self.params.get("external_input", 0.0))
        if external_input <= 0:
            return
        for node in self.get_active_nodes():
            node.energy += external_input

    def step(self) -> bool:
        self.apply_external_input()
        active_start = len(self.get_active_nodes())
        step_energy_spent: dict[int, float] = defaultdict(float)
        decisions = self.phase1_decisions()
        decision_counts = {
            "extend_decisions": sum(1 for value in decisions.values() if value == +1),
            "sense_decisions": sum(1 for value in decisions.values() if value == 0),
            "restrict_decisions": sum(1 for value in decisions.values() if value == -1),
            "conserve_decisions": sum(1 for value in decisions.values() if value == -2),
            "reproduce_decisions": sum(1 for value in decisions.values() if value == -3),
        }
        conserves_applied = self.phase2_conserve(decisions, step_energy_spent)
        candidates = self.phase3_candidates(decisions)
        valid, _ = self.phase4a_obstacles(candidates, step_energy_spent)
        winners, losers = self.phase4b_conflicts(valid)
        event_counts = self.phase5_apply(decisions, winners, losers, step_energy_spent)
        self.state.step_count += 1

        active = self.get_active_nodes()
        active_end = len(active)
        active_energy = total_active_energy(active)
        active_forests = len({node.forest_id for node in active})
        self.state.history_active.append(active_end)
        self.state.history_energy.append(active_energy)
        forests = {node.forest_id for node in active}
        self.state.history_forests.append(len(forests))
        self.energy_log.append(active_energy)
        self.state.event_log.append(
            {
                "step": self.state.step_count,
                "active_start": active_start,
                "active_end": active_end,
                "active_energy_end": active_energy,
                "active_forests_end": active_forests,
                "candidate_count": len(candidates),
                "valid_candidate_count": len(valid),
                "winner_count": len(winners),
                "loser_count": len(losers),
                "conserves_applied": conserves_applied,
                **decision_counts,
                **event_counts,
            }
        )
        return len(active) > 0

    def run(
        self,
        max_steps: int = 10_000,
        seed_layout: list[tuple[tuple[int, int, int], tuple[int, int, int], float, int]] | None = None,
        add_test_obstacles: bool = False,
    ) -> tuple[list[int], list[float], list[int], bool]:
        if self.state.nodes or self.state.history_active or self.state.step_count != 0:
            raise RuntimeError("run() expects a fresh NaturalMathSimulator instance.")

        layout = seed_layout or [
            ((0, 0, 0), (0, 1, 0), 400.0, 0),
            ((10, 0, 0), (0, 1, 0), 400.0, 1),
            ((-10, 0, 0), (0, 1, 0), 400.0, 2),
        ]
        for pos, direction, energy, forest_id in layout:
            self.add_seed(pos, direction, energy, forest_id=forest_id)
        if add_test_obstacles:
            self.add_test_obstacles()
        self.state.initial_forest_count = self.state.forest_counter

        froze = False
        for _ in range(max_steps):
            alive = self.step()
            if not alive:
                froze = True
                break
        return self.state.history_active, self.state.history_energy, self.state.history_forests, froze

    def validate(self) -> dict[str, bool]:
        return validate_state(
            self.state,
            self.energy_log,
            closed_system=float(self.params.get("external_input", 0.0)) <= 0,
        )

    def snapshot(self) -> dict[str, object]:
        active = self.get_active_nodes()
        event_totals: dict[str, int] = defaultdict(int)
        for event in self.state.event_log:
            for key, value in event.items():
                if key == "step":
                    continue
                if isinstance(value, int):
                    event_totals[key] += value
        return {
            "step_count": self.state.step_count,
            "initial_forest_count": self.state.initial_forest_count,
            "birth_events": self.state.birth_events,
            "active_sites": len(active),
            "active_energy": total_active_energy(active),
            "active_forests": len({node.forest_id for node in active}),
            "trail_sites": len(self.state.trail),
            "environment_sites": len(self.state.environment),
            "validation": self.validate(),
            "nodes": [asdict(node) for node in self.state.nodes],
            "history_active": self.state.history_active,
            "history_energy": self.state.history_energy,
            "history_forests": self.state.history_forests,
            "event_log": self.state.event_log,
            "event_totals": dict(event_totals),
            "params": self.params,
            "forest_params": self.state.forest_params,
            "todos": [
                "TODO: exact subtree-local ExpansionEfficiency(p,t)",
                "TODO: obstacle erosion and target hooks",
                "TODO: add theorem-specific validation harness on top of invariant checks",
                "TODO: event-level evidence export aligned with Fractalish analyzer",
                "TODO: eventual inactivity theorem validation harness",
            ],
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Natural Math Full Implementation v1.0 consolidated single-source runner."
    )
    parser.add_argument(
        "--profile",
        choices=["smoke", "growth-demo", "obstacle-growth", "bifurcation-demo"],
        default="bifurcation-demo",
        help="Named run profile. Use 'smoke' for the closed-system inactive-state baseline.",
    )
    parser.add_argument("--max-steps", type=int, default=10_000, help="Maximum timesteps to run.")
    parser.add_argument("--seed", type=int, default=7, help="Deterministic PRNG seed.")
    parser.add_argument("--initial-energy", type=float, default=400.0, help="Starting energy per seed.")
    parser.add_argument("--p-bifurcate", type=float, default=None, help="Override base bifurcation threshold.")
    parser.add_argument("--e-reproduce", type=float, default=None, help="Override minimum energy for reproduction.")
    parser.add_argument(
        "--eta-reproduce",
        type=float,
        default=None,
        help="Override efficiency threshold for reproduction.",
    )
    parser.add_argument(
        "--sigma-mutate",
        type=float,
        default=None,
        help="Override mutation stddev for offspring P_bifurcate.",
    )
    parser.add_argument(
        "--external-input",
        type=float,
        default=None,
        help="Override per-step energy input for open-system experiments.",
    )
    parser.add_argument("--obstacles", action="store_true", help="Add simple test walls to exercise pressure and branching.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output directory for JSON/CSV exports.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile = get_profile(args.profile)
    profile_params = dict(profile["params"])
    profile_params["seed"] = args.seed
    if args.p_bifurcate is not None:
        profile_params["P_bifurcate"] = args.p_bifurcate
    if args.e_reproduce is not None:
        profile_params["E_reproduce"] = args.e_reproduce
    if args.eta_reproduce is not None:
        profile_params["eta_reproduce"] = args.eta_reproduce
    if args.sigma_mutate is not None:
        profile_params["sigma_mutate"] = args.sigma_mutate
    if args.external_input is not None:
        profile_params["external_input"] = args.external_input

    simulator = NaturalMathSimulator(params=profile_params)
    for obstacle in profile.get("manual_obstacles", []):
        simulator.add_obstacle(obstacle)
    seed_layout = [
        (pos, direction, args.initial_energy if energy == 400.0 else energy, forest_id)
        for pos, direction, energy, forest_id in profile["seed_layout"]
    ]
    history_active, _, history_forests, froze = simulator.run(
        max_steps=args.max_steps,
        seed_layout=seed_layout,
        add_test_obstacles=bool(profile["add_test_obstacles"]) or args.obstacles,
    )
    validation = simulator.validate()

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        export_state(args.out / "natural_math_summary.json", simulator.snapshot())
        export_history_csv(args.out / "natural_math_history.csv", simulator)
        export_event_csv(args.out / "natural_math_events.csv", simulator)

    print("Natural Math Full Implementation v1.0")
    print(f"Profile: {args.profile}")
    print(f"Starting Simulation. Forests: {simulator.state.initial_forest_count}")
    if bool(profile["add_test_obstacles"]) or args.obstacles:
        print("Test obstacles enabled.")
    if froze:
        print(f"Simulation froze (Eventuality Theorem) at step {simulator.state.step_count}")
    else:
        print(f"Simulation hit max_steps={args.max_steps} with {history_active[-1]} active sites remaining")
    print()
    print("--- FINAL REPORT ---")
    print(f"Total Steps: {simulator.state.step_count}")
    print(f"Final Active Sites: {history_active[-1]}")
    print(f"Peak Forests: {max(history_forests)}")
    print(f"Initial Forests: {simulator.state.initial_forest_count}")
    print(f"Final Active Forests: {history_forests[-1]}")
    print(f"New Forests Created: {simulator.state.birth_events}")
    print(f"Energy non-increasing (closed-system check): {validation['energy_non_increasing']}")
    print(f"Unique node ids: {validation['unique_node_ids']}")
    print(f"Valid parent order: {validation['valid_parent_order']}")
    print(f"No parent cycles: {validation['no_parent_cycles']}")
    print(f"No active overlap: {validation['no_active_overlap']}")
    print(f"Nonnegative energy: {validation['nonnegative_energy']}")
    print(f"Inert energy zero: {validation['inert_energy_zero']}")
    print(f"Forest counter consistent: {validation['forest_counter_consistent']}")
    if simulator.state.event_log:
        totals = simulator.snapshot()["event_totals"]
        print(f"Total extend decisions: {totals.get('extend_decisions', 0)}")
        print(f"Total bifurcations: {totals.get('bifurcations', 0)}")
        print(f"Total single-child extensions: {totals.get('single_child_extensions', 0)}")
        print(f"Total conflict losses: {totals.get('conflict_losses', 0)}")
        print(f"Total restrict deaths: {totals.get('restrict_deaths', 0)}")
        print(f"Total reproduction births: {totals.get('reproduction_births', 0)}")
    if froze:
        print()
        print("Smoke test reached an inactive state in this run.")
    else:
        print()
        print("Run stopped at max_steps before inactivity; do not claim theorem verification from this run alone.")
    if args.out is not None:
        print()
        print(f"Exports written to: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
