"""
Natural Math "Stick" Mechanism — Hardened Reference Implementation v5.0

Purpose
-------
Preserve Melissa Clow's core idea:
    shared depletion can increase attraction;
    contact can create bounded-degree persistent bonds;
    bonded structure changes future movement and resource use.

This version is a software agent model, not an atomic crystal simulator.
It corrects several auditability problems in v4:
- bonds persist until an explicit break condition;
- formation, rest, and break distances are consistent;
- energy-difference and depletion terms are dimensionless;
- inverse-distance weighting matches the written Natural Math equation;
- spring magnitude is not erased by normalizing the combined vector;
- bonded nodes repel when compressed and attract when stretched;
- energy sharing is simultaneous and globally conservative;
- bond benefits reduce consumption but do not create energy by default;
- every optional external inflow is explicitly accounted;
- update order is snapshot-based and deterministic for a fixed seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Iterable, List, Sequence, Set, Tuple
import argparse
import json
import math
import random

Vec3 = Tuple[float, float, float]


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(v: Vec3, s: float) -> Vec3:
    return (v[0] * s, v[1] * s, v[2] * s)


def dot(v: Vec3, w: Vec3) -> float:
    return v[0] * w[0] + v[1] * w[1] + v[2] * w[2]


def norm_sq(v: Vec3) -> float:
    return dot(v, v)


def norm(v: Vec3) -> float:
    return math.sqrt(norm_sq(v))


def unit(v: Vec3, eps: float = 1e-12) -> Vec3:
    n = norm(v)
    if n <= eps:
        return (0.0, 0.0, 0.0)
    return scale(v, 1.0 / n)


def clamp_magnitude(v: Vec3, maximum: float) -> Vec3:
    n = norm(v)
    if n <= maximum or n <= 1e-12:
        return v
    return scale(v, maximum / n)


def quadrance(a: Vec3, b: Vec3) -> float:
    return norm_sq(sub(a, b))


@dataclass
class StickParams:
    steps: int = 720
    initial_energy: float = 800.0
    death_threshold: float = 5.0

    sensing_radius: float = 25.0
    movement_speed: float = 0.5
    bonded_speed_factor: float = 0.6
    movement_cost_per_unit: float = 0.15

    # Dimensionless differential:
    # alpha * ((E_q-E_p)/E0) + sigma * delta_p * delta_q
    energy_difference_strength: float = 1.0
    deficit_strength: float = 1.0

    max_bonds: int = 3
    bond_form_distance: float = 2.0
    bond_rest_distance: float = 1.5
    bond_break_distance: float = 3.0
    spring_stiffness: float = 0.25

    base_consumption: float = 0.5
    saving_per_bond: float = 0.15
    minimum_consumption: float = 0.05

    # Zero means a closed resource model.
    # A positive value is explicit environmental inflow, not "free energy."
    external_inflow_per_bond: float = 0.0

    boundary_radius: float = 50.0
    boundary_strength: float = 0.05
    epsilon: float = 1e-9


@dataclass
class Node:
    id: int
    position: Vec3
    energy: float
    bonds: Set[int] = field(default_factory=set)
    alive: bool = True
    age: int = 0


@dataclass
class StepLedger:
    movement_cost: float = 0.0
    metabolic_cost: float = 0.0
    external_inflow: float = 0.0


@dataclass
class RunSummary:
    seed: int
    steps_completed: int
    survivors: int
    cluster_sizes: List[int]
    bonded_nodes: int
    total_initial_energy: float
    total_final_energy: float
    total_movement_cost: float
    total_metabolic_cost: float
    total_external_inflow: float
    maximum_degree: int
    deterministic_signature: str


class StickSimulation:
    def __init__(
        self,
        params: StickParams | None = None,
        num_nodes: int = 20,
        seed: int = 42,
    ):
        self.params = params or StickParams()
        self.seed = seed
        self.rng = random.Random(seed)
        self.nodes: List[Node] = []

        for node_id in range(num_nodes):
            position = tuple(
                self.rng.uniform(-8.0, 8.0) for _ in range(3)
            )
            energy = self.params.initial_energy * self.rng.uniform(0.9, 1.1)
            energy = min(energy, self.params.initial_energy)
            self.nodes.append(Node(node_id, position, energy))

        self.initial_energy = self.total_energy()
        self.total_ledger = StepLedger()
        self.steps_completed = 0

    def total_energy(self) -> float:
        return sum(node.energy for node in self.nodes if node.alive)

    def depletion(self, energy: float) -> float:
        p = self.params
        return min(1.0, max(0.0, (p.initial_energy - energy) / p.initial_energy))

    def snapshot(self):
        return {
            node.id: {
                "position": node.position,
                "energy": node.energy,
                "bonds": frozenset(node.bonds),
                "alive": node.alive,
            }
            for node in self.nodes
        }

    def social_vector(self, node_id: int, snap) -> Vec3:
        p = self.params
        current = snap[node_id]
        pos_p = current["position"]
        energy_p = current["energy"]
        depletion_p = self.depletion(energy_p)
        result: Vec3 = (0.0, 0.0, 0.0)
        found = False

        for other_id, other in snap.items():
            if other_id == node_id or not other["alive"]:
                continue

            displacement = sub(other["position"], pos_p)
            d2 = norm_sq(displacement)
            if d2 <= p.epsilon or d2 > p.sensing_radius ** 2:
                continue

            found = True
            energy_difference = (
                other["energy"] - energy_p
            ) / p.initial_energy
            mutual_depletion = (
                depletion_p * self.depletion(other["energy"])
            )
            effective_difference = (
                p.energy_difference_strength * energy_difference
                + p.deficit_strength * mutual_depletion
            )

            # Matches (1/Q) * differential * displacement.
            contribution = scale(
                displacement,
                effective_difference / max(d2, p.epsilon),
            )
            result = add(result, contribution)

        if not found:
            random_direction = (
                self.rng.gauss(0.0, 1.0),
                self.rng.gauss(0.0, 1.0),
                self.rng.gauss(0.0, 1.0),
            )
            return unit(random_direction)

        return result

    def spring_vector(self, node_id: int, snap) -> Vec3:
        p = self.params
        current = snap[node_id]
        pos_p = current["position"]
        result: Vec3 = (0.0, 0.0, 0.0)

        for other_id in current["bonds"]:
            other = snap[other_id]
            if not other["alive"]:
                continue

            displacement = sub(other["position"], pos_p)
            distance = norm(displacement)
            if distance <= p.epsilon:
                # Deterministic tiny separating direction for overlap.
                sign = -1.0 if node_id < other_id else 1.0
                displacement = (sign, 0.0, 0.0)
                distance = 1.0

            stretch = distance - p.bond_rest_distance
            # Positive stretch attracts; negative stretch repels.
            result = add(
                result,
                scale(unit(displacement), p.spring_stiffness * stretch),
            )

        return result

    def planned_motion(self, node_id: int, snap) -> Vec3:
        p = self.params
        node = snap[node_id]
        social = self.social_vector(node_id, snap)
        spring = self.spring_vector(node_id, snap)

        energy_factor = min(
            1.0,
            node["energy"] / p.initial_energy + 0.3,
        )
        social_speed = p.movement_speed * energy_factor
        if node["bonds"]:
            social_speed *= p.bonded_speed_factor

        velocity = add(scale(unit(social), social_speed), spring)
        return clamp_magnitude(velocity, p.movement_speed)

    def apply_boundary(self, position: Vec3) -> Vec3:
        p = self.params
        distance = norm(position)
        if distance <= p.boundary_radius or distance <= p.epsilon:
            return position

        excess = distance - p.boundary_radius
        correction = min(excess, p.boundary_strength * excess)
        return sub(position, scale(unit(position), correction))

    def move_from_snapshot(self, snap, ledger: StepLedger):
        p = self.params
        motions = {
            node.id: self.planned_motion(node.id, snap)
            for node in self.nodes
            if node.alive
        }

        for node in self.nodes:
            if not node.alive:
                continue

            displacement = motions[node.id]
            requested_distance = norm(displacement)
            affordable_distance = (
                node.energy / p.movement_cost_per_unit
                if p.movement_cost_per_unit > 0
                else requested_distance
            )
            actual_distance = min(requested_distance, affordable_distance)

            if requested_distance > p.epsilon:
                actual_displacement = scale(
                    displacement,
                    actual_distance / requested_distance,
                )
            else:
                actual_displacement = (0.0, 0.0, 0.0)

            node.position = self.apply_boundary(
                add(node.position, actual_displacement)
            )
            cost = actual_distance * p.movement_cost_per_unit
            node.energy = max(0.0, node.energy - cost)
            ledger.movement_cost += cost

    def update_bonds(self):
        p = self.params

        # Break only by explicit hysteresis threshold.
        for node in self.nodes:
            for other_id in list(node.bonds):
                other = self.nodes[other_id]
                if (
                    not node.alive
                    or not other.alive
                    or quadrance(node.position, other.position)
                    > p.bond_break_distance ** 2
                ):
                    node.bonds.discard(other_id)
                    other.bonds.discard(node.id)

        # Candidate bonds are deterministic: nearest first, then IDs.
        candidates = []
        for i, a in enumerate(self.nodes):
            if not a.alive:
                continue
            for j in range(i + 1, len(self.nodes)):
                b = self.nodes[j]
                if not b.alive or j in a.bonds:
                    continue
                d2 = quadrance(a.position, b.position)
                if p.epsilon < d2 <= p.bond_form_distance ** 2:
                    candidates.append((d2, i, j))

        candidates.sort()
        new_edges: List[Tuple[int, int]] = []

        for _, i, j in candidates:
            a = self.nodes[i]
            b = self.nodes[j]
            if len(a.bonds) >= p.max_bonds:
                continue
            if len(b.bonds) >= p.max_bonds:
                continue
            a.bonds.add(j)
            b.bonds.add(i)
            new_edges.append((i, j))

        self.equalize_new_bond_components(new_edges)

    def equalize_new_bond_components(
        self, new_edges: Sequence[Tuple[int, int]]
    ):
        """
        Order-independent, energy-conserving equalization among nodes joined
        by edges created in this step.
        """
        adjacency: Dict[int, Set[int]] = {}
        for i, j in new_edges:
            adjacency.setdefault(i, set()).add(j)
            adjacency.setdefault(j, set()).add(i)

        visited: Set[int] = set()
        for start in adjacency:
            if start in visited:
                continue

            stack = [start]
            component = []
            while stack:
                node_id = stack.pop()
                if node_id in visited:
                    continue
                visited.add(node_id)
                component.append(node_id)
                stack.extend(adjacency.get(node_id, ()))

            mean_energy = sum(
                self.nodes[node_id].energy for node_id in component
            ) / len(component)
            for node_id in component:
                self.nodes[node_id].energy = mean_energy

    def apply_metabolism(self, ledger: StepLedger):
        p = self.params
        for node in self.nodes:
            if not node.alive:
                continue

            degree = len(node.bonds)
            consumption = max(
                p.minimum_consumption,
                p.base_consumption - p.saving_per_bond * degree,
            )
            actual = min(node.energy, consumption)
            node.energy -= actual
            ledger.metabolic_cost += actual

            inflow = p.external_inflow_per_bond * degree
            node.energy = min(p.initial_energy, node.energy + inflow)
            ledger.external_inflow += inflow

            node.age += 1
            if node.energy < p.death_threshold:
                node.alive = False

    def validate_invariants(self):
        p = self.params
        for node in self.nodes:
            if len(node.bonds) > p.max_bonds:
                raise AssertionError("maximum degree exceeded")
            for other_id in node.bonds:
                other = self.nodes[other_id]
                if node.id not in other.bonds:
                    raise AssertionError("asymmetric bond")
                if not node.alive or not other.alive:
                    raise AssertionError("bond to dead node")

    def step(self):
        if not any(node.alive for node in self.nodes):
            return False

        ledger = StepLedger()
        snap = self.snapshot()
        self.move_from_snapshot(snap, ledger)
        self.update_bonds()
        self.apply_metabolism(ledger)
        self.validate_invariants()

        self.total_ledger.movement_cost += ledger.movement_cost
        self.total_ledger.metabolic_cost += ledger.metabolic_cost
        self.total_ledger.external_inflow += ledger.external_inflow
        self.steps_completed += 1
        return True

    def cluster_sizes(self) -> List[int]:
        visited: Set[int] = set()
        sizes = []

        for node in self.nodes:
            if not node.alive or node.id in visited:
                continue

            stack = [node.id]
            size = 0
            while stack:
                node_id = stack.pop()
                if node_id in visited:
                    continue
                visited.add(node_id)
                size += 1
                stack.extend(
                    other_id
                    for other_id in self.nodes[node_id].bonds
                    if self.nodes[other_id].alive
                )
            sizes.append(size)

        return sorted(sizes, reverse=True)

    def signature(self) -> str:
        state = []
        for node in self.nodes:
            state.append(
                (
                    node.id,
                    tuple(round(x, 9) for x in node.position),
                    round(node.energy, 9),
                    tuple(sorted(node.bonds)),
                    node.alive,
                )
            )
        return json.dumps(state, separators=(",", ":"))

    def run(self) -> RunSummary:
        for _ in range(self.params.steps):
            if not self.step():
                break

        final_energy = self.total_energy()
        expected = (
            self.initial_energy
            - self.total_ledger.movement_cost
            - self.total_ledger.metabolic_cost
            + self.total_ledger.external_inflow
        )
        if abs(final_energy - expected) > 1e-6:
            raise AssertionError(
                f"energy ledger mismatch: final={final_energy}, "
                f"expected={expected}"
            )

        return RunSummary(
            seed=self.seed,
            steps_completed=self.steps_completed,
            survivors=sum(1 for n in self.nodes if n.alive),
            cluster_sizes=self.cluster_sizes(),
            bonded_nodes=sum(
                1 for n in self.nodes if n.alive and n.bonds
            ),
            total_initial_energy=self.initial_energy,
            total_final_energy=final_energy,
            total_movement_cost=self.total_ledger.movement_cost,
            total_metabolic_cost=self.total_ledger.metabolic_cost,
            total_external_inflow=self.total_ledger.external_inflow,
            maximum_degree=max(
                (len(n.bonds) for n in self.nodes), default=0
            ),
            deterministic_signature=self.signature(),
        )


def determinism_check(seed: int = 42) -> bool:
    first = StickSimulation(seed=seed).run()
    second = StickSimulation(seed=seed).run()
    return first.deterministic_signature == second.deterministic_signature


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--nodes", type=int, default=20)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument(
        "--external-inflow-per-bond", type=float, default=0.0
    )
    args = parser.parse_args()

    params = StickParams(
        steps=args.steps,
        external_inflow_per_bond=args.external_inflow_per_bond,
    )
    simulation = StickSimulation(
        params=params,
        num_nodes=args.nodes,
        seed=args.seed,
    )
    summary = simulation.run()
    output = asdict(summary)
    output.pop("deterministic_signature")
    output["determinism_check"] = determinism_check(args.seed)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
