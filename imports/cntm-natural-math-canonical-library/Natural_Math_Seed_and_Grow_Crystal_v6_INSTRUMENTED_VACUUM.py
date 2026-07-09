#!/usr/bin/env python3
"""
Natural Math Seed-and-Grow Crystal v6 — INSTRUMENTED with VACUUM MEMORY
=======================================================================
Extends Melissa's v6 clean with upstream decision instrumentation AND a
vacuum_memory layer: a coarse scalar field that accumulates energy-transport
residue (harvest, flow, movement, spawn, death) and decays slowly.

The void is treated as stored energy — a ghost landscape of prior flows that
conditions future admissible futures.

Run:
    python Natural_Math_Seed_and_Grow_Crystal_v6_INSTRUMENTED_VACUUM.py
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

Vec3 = Tuple[float, float, float]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Node:
    def __init__(
        self,
        node_id: int,
        pos: Vec3,
        energy: float,
        parent_id: Optional[int],
        node_type: str,
        alive: bool,
        role: Optional[str] = None,
    ) -> None:
        self.id = node_id
        self.pos = pos
        self.energy = energy
        self.pressure = 0.0
        self.parent_id = parent_id
        self.type = node_type
        self.alive = alive
        self.role = role

        self.bonds: List[int] = []
        self.bond_dirs: Dict[int, Vec3] = {}
        self.identity = [0.0, 0.0, 0.0]
        self.bond_history: List[int] = []

        self.age = 0
        self.total_harvested = 0.0
        self.cluster_size_history: List[int] = []
        self.tumble_count = 0
        self.run_count = 0

        self.last_field = 0.0
        self.best_field_seen = 0.0
        self.best_field_pos = pos
        self.current_dir: Vec3 = (0.0, 0.0, 1.0)

        self.bifurcation_count = 0
        self.generation = 0
        self.anchored = False

        # --- Energy-flow instrumentation (lightweight) ---
        self.acc_harvest = 0.0
        self.acc_transport = 0.0
        self.acc_metabolism = 0.0
        self.acc_movement = 0.0


@dataclass
class AdmissibleFuture:
    direction: List[float]
    score: float
    energy_cost: float
    field_projection: float
    angular_gap_deg: float
    constraint_type: str


@dataclass
class InstrumentedDecisionRecord:
    # === Core identification (no defaults) ===
    step: int
    node_id: int
    generation: int
    role: str
    bond_count: int
    energy: float
    pressure: float
    surface_score: float
    local_field: float
    incoming_energy_flow: float
    eligible: bool
    selected_action: str
    rejection_reasons: List[str]

    # === Admissible futures manifold ===
    admissible_futures: List[Dict]
    futures_count: int
    futures_entropy: float
    selected_future_index: int
    selection_surprisal: float
    constraint_curvature: float

    # === Pre-bifurcation snapshot ===
    snapshot_bond_topology: List[int]
    snapshot_neighbor_count: int
    snapshot_local_density: float
    snapshot_incoming_flux: float
    snapshot_stem_curvature: float

    # === Energy flow accounting ===
    energy_source_harvest: float
    energy_source_transport: float
    energy_source_reserve: float
    energy_sink_metabolism: float
    energy_sink_movement: float
    energy_sink_spawn: float
    energy_child_gift: float
    energy_parent_retained: float
    energy_balance: float

    # === Structural inheritance ===
    lineage_depth: int
    ancestral_motif: str
    generational_pressure_avg: float
    structural_divergence: float

    # === Phase-space diagnostics ===
    phase_energy: float
    phase_pressure: float
    phase_surface: float
    phase_field: float
    manifold_distance: float
    survival_probability: float
    basin_curvature: float

    # === Counterfactual ===
    counterfactual_hold_energy: float
    counterfactual_hold_pressure: float
    counterfactual_projected_children: int
    counterfactual_opportunity_cost: float
    counterfactual_regret: float

    # === Vacuum memory ===
    local_vacuum: float
    vacuum_gradient: List[float]
    vacuum_influence: float
    vacuum_inherited_trace: float

    # === Outcome (defaults at END to avoid dataclass ordering issues) ===
    child_role: Optional[str] = None
    child_id: Optional[int] = None
    child_direction: Optional[List[float]] = None
    energy_partition: Optional[Tuple[float, float]] = None


class Params:
    def __init__(self) -> None:
        self.tau = 5.0
        self.iota = 1.0
        self.r = 25.0
        self.eps_extend = 0.3
        self.eps_sense = 0.01
        self.E0 = 800.0
        self.eta_sq = 0.01
        self.gamma_fallback = 0.0
        self.eps_tol = 1e-9
        self.r_sq = self.r**2
        self.iota_sq = self.iota**2
        self.deficit_strength = 10.0

        self.max_bonds = 6
        self.D = 0.15
        self.kappa_transport = 0.03
        self.max_move_dist_sq = 2.0

        self.identity_learning_rate = 0.3
        self.compatibility_threshold = 0.3
        self.hello_strength = 5.0
        self.identity_noise = 0.05

        self.base_consumption = 2.0

        self.patch_count = 25
        self.patch_radius = 5.0
        self.patch_max = 30.0
        self.patch_recovery = 0.08
        self.patch_decay = 0.002
        self.patch_sharpness = 3.0
        self.background_level = 0.3

        self.harvest_base_rate = 0.7
        self.size_penalty = 0.08
        self.transport_reward = 0.5
        self.consumer_penalty = 1.0

        self.shell_base_radius = 3.0
        self.shell_coupling = 0.3
        self.shell_energy_cost = 0.05

        self.mutation_prob = 0.002
        self.mutation_strength = 0.3

        self.sense_radius = 3.0
        self.chemotaxis_strength = 80.0
        self.min_gradient_threshold = 0.5
        self.move_speed = 2.0
        self.move_cost_per_unit = 0.15

        self.bonding_benefit = 0.2
        self.bond_distance = 2.0
        self.directional_bonding = True
        self.max_bond_angle = 45.0
        self.role_bond_bonus = 0.3

        self.bifurcation_enabled = True
        self.bifurcation_start_step = 100
        self.min_bonds_to_bifurcate = 1
        self.bifurcation_energy_min = 250.0
        self.bifurcation_energy_max = 780.0
        self.bifurcation_pressure_threshold = 4.0
        self.pressure_baseline = 1.2
        self.pressure_decay = 0.95
        self.eps_spawn = 15.0
        self.eps_split = 5.0
        self.max_nodes = 200
        self.child_push_distance = 1.6

        self.role_mutation_prob = 0.2
        self.role_cycle = {"P": "I", "I": "C", "C": "P"}

        self.surface_neighbor_radius = 4.0
        self.surface_score_min = 0.35
        self.freeze_anchored_structure = True

        # --- Instrumentation parameters ---
        self.future_samples = 8
        self.manifold_softness = 20.0

        # --- Vacuum memory parameters ---
        self.vacuum_resolution = 10          # 10x10x10 grid over bounds
        self.vacuum_bounds = 15.0
        self.vacuum_decay = 0.995            # 0.5% loss per step
        self.vacuum_deposit_rate = 0.08
        self.vacuum_sense_radius = 4.0
        self.vacuum_producer_repulsion = 12.0   # P repelled by high vacuum
        self.vacuum_consumer_attraction = 10.0  # C attracted to high vacuum
        self.vacuum_intermediate_neutral = 0.0


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------

def Q(p1: Vec3, p2: Vec3) -> float:
    return sum((a - b) ** 2 for a, b in zip(p1, p2))


def dist(p1: Vec3, p2: Vec3) -> float:
    return math.sqrt(Q(p1, p2))


def norm(v: Iterable[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def normalize_vec(v: Iterable[float], eps_tol: float = 1e-9) -> List[float]:
    vals = list(v)
    n = norm(vals)
    if n < eps_tol:
        return [0.0] * len(vals)
    return [x / n for x in vals]


def dot(v1: Iterable[float], v2: Iterable[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))


def angle_between(v1: Iterable[float], v2: Iterable[float]) -> float:
    n1 = norm(v1)
    n2 = norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 180.0
    cosine = max(-1.0, min(1.0, dot(v1, v2) / (n1 * n2)))
    return math.degrees(math.acos(cosine))


# ---------------------------------------------------------------------------
# Roles and identity
# ---------------------------------------------------------------------------

def get_role(node: Node) -> str:
    if node.role is not None:
        return node.role
    idx = max(range(3), key=lambda i: node.identity[i])
    return ["P", "I", "C"][idx]


def role_complementarity(role_a: str, role_b: str) -> float:
    pairs = {
        ("P", "I"): 1.0, ("I", "P"): 1.0,
        ("I", "C"): 1.0, ("C", "I"): 1.0,
        ("P", "P"): 0.3, ("C", "C"): 0.3,
        ("P", "C"): 0.0, ("C", "P"): 0.0,
    }
    return pairs.get((role_a, role_b), 0.0)


def identity_for_role(role: str) -> List[float]:
    if role == "P":
        return [1.0, 0.0, 0.0]
    if role == "I":
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class DiffuseField:
    def __init__(self, params: Params, bounds: float = 15.0, seed: int = 42) -> None:
        self.params = params
        self.bounds = bounds
        rng = random.Random(seed)
        self.patches = []
        for _ in range(params.patch_count):
            center = (
                rng.uniform(-bounds, bounds),
                rng.uniform(-bounds, bounds),
                rng.uniform(-bounds, bounds),
            )
            self.patches.append({
                "center": center,
                "energy": params.patch_max * rng.uniform(0.8, 1.0),
                "radius": params.patch_radius,
            })

    def get(self, pos: Vec3) -> float:
        total = self.params.background_level
        for patch in self.patches:
            d = dist(pos, patch["center"])
            if d < patch["radius"]:
                falloff = math.exp(-self.params.patch_sharpness * d / patch["radius"])
                total += patch["energy"] * falloff
        return total

    def gradient(self, pos: Vec3, sample_radius: float = 2.0) -> Vec3:
        g = [0.0, 0.0, 0.0]
        for dx, dy, dz in ((1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)):
            sample_pos = (
                pos[0] + dx * sample_radius,
                pos[1] + dy * sample_radius,
                pos[2] + dz * sample_radius,
            )
            value = self.get(sample_pos)
            g[0] += dx * value
            g[1] += dy * value
            g[2] += dz * value
        ng = norm(g)
        if ng < 1e-9:
            return (0.0, 0.0, 0.0)
        return (g[0] / ng, g[1] / ng, g[2] / ng)

    def harvest(self, pos: Vec3, cluster_size: int, producer_strength: float) -> float:
        field_value = self.get(pos)
        if field_value < self.params.eps_tol:
            return 0.0
        efficiency = max(0.3, 1.0 - self.params.size_penalty * (cluster_size - 1))
        amount = self.params.harvest_base_rate * field_value * max(0.0, producer_strength) * efficiency
        amount = min(amount, field_value * 0.12)
        for patch in self.patches:
            if dist(pos, patch["center"]) < patch["radius"]:
                patch["energy"] = max(patch["energy"] - amount * 0.02, 0.0)
        return amount

    def update(self) -> None:
        for patch in self.patches:
            patch["energy"] = min(patch["energy"] + self.params.patch_recovery, self.params.patch_max)
            patch["energy"] = max(patch["energy"] - self.params.patch_decay, 0.0)

    def find_nearest_patch(self, pos: Vec3):
        return min(((patch, dist(pos, patch["center"])) for patch in self.patches), key=lambda item: item[1])


# ---------------------------------------------------------------------------
# VACUUM MEMORY — the void as stored energy
# ---------------------------------------------------------------------------

class VacuumMemory:
    """
    A coarse scalar field that accumulates energy-transport residue.
    The void remembers where energy has passed, decaying slowly.
    """
    def __init__(self, params: Params):
        self.params = params
        self.res = params.vacuum_resolution
        self.bounds = params.vacuum_bounds
        self.cell_size = 2.0 * self.bounds / self.res
        # 3D grid: grid[x][y][z]
        self.grid = [[[0.0 for _ in range(self.res)] for _ in range(self.res)] for _ in range(self.res)]

    def _idx(self, coord: float) -> int:
        i = int((coord + self.bounds) / self.cell_size)
        return max(0, min(i, self.res - 1))

    def deposit(self, pos: Vec3, amount: float) -> None:
        """Energy passed through here; leave a trace in the void."""
        if amount <= 0:
            return
        ix, iy, iz = self._idx(pos[0]), self._idx(pos[1]), self._idx(pos[2])
        self.grid[ix][iy][iz] += amount * self.params.vacuum_deposit_rate

    def get(self, pos: Vec3) -> float:
        ix, iy, iz = self._idx(pos[0]), self._idx(pos[1]), self._idx(pos[2])
        return self.grid[ix][iy][iz]

    def gradient(self, pos: Vec3) -> Vec3:
        ix, iy, iz = self._idx(pos[0]), self._idx(pos[1]), self._idx(pos[2])
        g = [0.0, 0.0, 0.0]
        for dx, dy, dz in ((1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)):
            nx, ny, nz = ix + dx, iy + dy, iz + dz
            if 0 <= nx < self.res and 0 <= ny < self.res and 0 <= nz < self.res:
                g[0] += dx * self.grid[nx][ny][nz]
                g[1] += dy * self.grid[nx][ny][nz]
                g[2] += dz * self.grid[nx][ny][nz]
        ng = norm(g)
        if ng < 1e-9:
            return (0.0, 0.0, 0.0)
        return (g[0] / ng, g[1] / ng, g[2] / ng)

    def update(self) -> None:
        for i in range(self.res):
            for j in range(self.res):
                for k in range(self.res):
                    self.grid[i][j][k] *= self.params.vacuum_decay

    def to_list(self) -> List:
        """Flatten for JSON export."""
        return self.grid


# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------

def node_map(nodes: List[Node]) -> Dict[int, Node]:
    return {n.id: n for n in nodes}


def connect_nodes(a: Node, b: Node) -> None:
    if a.id == b.id:
        return
    direction = tuple(normalize_vec((b.pos[0] - a.pos[0], b.pos[1] - a.pos[1], b.pos[2] - a.pos[2])))
    opposite = (-direction[0], -direction[1], -direction[2])
    if b.id not in a.bonds:
        a.bonds.append(b.id)
        a.bond_history.append(b.id)
    if a.id not in b.bonds:
        b.bonds.append(a.id)
        b.bond_history.append(a.id)
    a.bond_dirs[b.id] = direction
    b.bond_dirs[a.id] = opposite
    a.anchored = True
    b.anchored = True


def connected_components(nodes: List[Node]) -> List[List[Node]]:
    alive = [n for n in nodes if n.alive]
    by_id = node_map(alive)
    visited = set()
    components: List[List[Node]] = []
    for node in alive:
        if node.id in visited:
            continue
        queue = [node.id]
        comp: List[Node] = []
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            current = by_id.get(current_id)
            if current is None:
                continue
            comp.append(current)
            for neighbor_id in current.bonds:
                if neighbor_id not in visited and neighbor_id in by_id:
                    queue.append(neighbor_id)
        if comp:
            components.append(comp)
    return components


# ---------------------------------------------------------------------------
# Shells and movement
# ---------------------------------------------------------------------------

def compute_shells(nodes: List[Node], params: Params):
    shells = {}
    for cluster in connected_components(nodes):
        center = tuple(sum(n.pos[i] for n in cluster) / len(cluster) for i in range(3))
        avg_identity = normalize_vec([sum(n.identity[i] for n in cluster) / len(cluster) for i in range(3)])
        shells[cluster[0].id] = {
            "center": center,
            "radius": params.shell_base_radius * math.sqrt(len(cluster)),
            "polarity": avg_identity,
            "strength": sum(n.energy for n in cluster) / len(cluster),
            "nodes": [n.id for n in cluster],
            "size": len(cluster),
        }
    return shells


def shell_effect_on_node(node: Node, shells, params: Params):
    fx = fy = fz = 0.0
    energy_xfer = 0.0
    for shell in shells.values():
        if node.id in shell["nodes"]:
            energy_xfer -= params.shell_energy_cost * shell["size"] * 0.1
            continue
        dx = node.pos[0] - shell["center"][0]
        dy = node.pos[1] - shell["center"][1]
        dz = node.pos[2] - shell["center"][2]
        d = math.sqrt(dx*dx + dy*dy + dz*dz)
        if d < params.eps_tol or d > shell["radius"] * 2:
            continue
        sim = dot(node.identity, shell["polarity"]) / (norm(node.identity) * norm(shell["polarity"]) + 1e-9)
        force_mag = shell["strength"] * params.shell_coupling / (d + 1.0)
        if sim > 0.3:
            fx -= force_mag * dx / d
            fy -= force_mag * dy / d
            fz -= force_mag * dz / d
        elif sim < -0.2:
            fx += force_mag * dx / d
            fy += force_mag * dy / d
            fz += force_mag * dz / d
    return fx, fy, fz, energy_xfer


def compute_movement_vector(p: Node, active_snapshot: List[Node], field: DiffuseField, shells, vacuum: VacuumMemory, params: Params) -> Vec3:
    social_g = [0.0, 0.0, 0.0]
    social_weight = 0.0
    for q in active_snapshot:
        if q.id == p.id:
            continue
        q_dist = Q(p.pos, q.pos)
        if q_dist > params.r_sq + params.eps_tol or q_dist < params.eps_tol:
            continue
        sim = dot(p.identity, q.identity) / (norm(p.identity) * norm(q.identity) + 1e-9)
        loneliness_p = 1.0 if not p.bonds else 0.0
        loneliness_q = 1.0 if not q.bonds else 0.0
        hello_signal = loneliness_p * loneliness_q * params.hello_strength
        role_bonus = params.role_bond_bonus * role_complementarity(get_role(p), get_role(q)) if params.directional_bonding else 0.0
        compat = sim + hello_signal * 0.1 + role_bonus
        if compat < params.compatibility_threshold and not (loneliness_p and loneliness_q):
            continue
        w = compat / q_dist
        social_weight += w
        energy_diff = q.energy - p.energy
        deficit_p = max(0.0, (params.E0 - p.energy) / params.E0)
        deficit_q = max(0.0, (params.E0 - q.energy) / params.E0)
        effective_diff = energy_diff - params.deficit_strength * deficit_p * deficit_q
        dx = q.pos[0] - p.pos[0]
        dy = q.pos[1] - p.pos[1]
        dz = q.pos[2] - p.pos[2]
        social_g[0] += w * effective_diff * dx
        social_g[1] += w * effective_diff * dy
        social_g[2] += w * effective_diff * dz
    if social_weight > params.eps_tol:
        social_g = [x / social_weight for x in social_g]

    chemo_g = [0.0, 0.0, 0.0]
    chemo_weight = 0.0
    id_norm = norm(p.identity)
    if id_norm > params.eps_tol:
        producer_strength = p.identity[0] / id_norm
        if producer_strength > 0.15:
            field_here = field.get(p.pos)
            field_grad = field.gradient(p.pos, sample_radius=params.sense_radius)
            grad_norm = norm(field_grad)
            if field_here > p.best_field_seen:
                p.best_field_seen = field_here
                p.best_field_pos = p.pos
            if grad_norm > 0.1 and field_here > params.min_gradient_threshold:
                chemo_g = list(field_grad)
                chemo_weight = producer_strength * 2.0
                p.run_count += 1
                p.current_dir = field_grad
            elif field_here > params.background_level * 2:
                if random.random() < 0.3:
                    chemo_g = [x * 0.3 for x in normalize_vec([random.gauss(0, 1) for _ in range(3)])]
                    chemo_weight = 0.3
                    p.tumble_count += 1
            else:
                p.tumble_count += 1
                if p.best_field_seen > field_here * 1.5:
                    memory_vector = [p.best_field_pos[i] - p.pos[i] for i in range(3)]
                    memory_distance = norm(memory_vector)
                    if 1 < memory_distance < 100:
                        memory_dir = normalize_vec(memory_vector)
                        chemo_g = [x * 0.3 for x in memory_dir]
                        chemo_weight = 0.3
                        p.current_dir = tuple(memory_dir)
                else:
                    p.current_dir = tuple(normalize_vec([random.gauss(0, 1) for _ in range(3)]))

    shell_fx, shell_fy, shell_fz, shell_energy = shell_effect_on_node(p, shells, params)
    shell_g = [shell_fx, shell_fy, shell_fz]
    shell_weight = 1.0 if norm(shell_g) > 0.01 else 0.0
    p.energy = min(max(p.energy + shell_energy, 0.0), params.E0)

    # === VACUUM MEMORY influence ===
    vacuum_g = [0.0, 0.0, 0.0]
    vacuum_weight = 0.0
    vacuum_val = vacuum.get(p.pos)
    vacuum_grad = vacuum.gradient(p.pos)
    vg_norm = norm(vacuum_grad)
    if vg_norm > 1e-9:
        role = get_role(p)
        if role == "P":
            # Producers repelled by high vacuum (avoid depleted ghosts)
            vacuum_g = [-x * params.vacuum_producer_repulsion for x in vacuum_grad]
            vacuum_weight = min(1.0, vacuum_val / 5.0) * params.vacuum_producer_repulsion
        elif role == "C":
            # Consumers attracted to high vacuum (follow prior flow residue)
            vacuum_g = [x * params.vacuum_consumer_attraction for x in vacuum_grad]
            vacuum_weight = min(1.0, vacuum_val / 5.0) * params.vacuum_consumer_attraction
        else:
            # Intermediates sense weakly for routing
            vacuum_g = [x * params.vacuum_intermediate_neutral for x in vacuum_grad]
            vacuum_weight = 0.0

    total_g = [0.0, 0.0, 0.0]
    total_weight = 0.0
    if social_weight > params.eps_tol:
        for i in range(3):
            total_g[i] += social_g[i] * social_weight
        total_weight += social_weight
    if chemo_weight > 0:
        for i in range(3):
            total_g[i] += chemo_g[i] * chemo_weight * params.chemotaxis_strength
        total_weight += chemo_weight * params.chemotaxis_strength
    if shell_weight > 0:
        for i in range(3):
            total_g[i] += shell_g[i]
        total_weight += shell_weight
    if vacuum_weight > 0:
        for i in range(3):
            total_g[i] += vacuum_g[i]
        total_weight += vacuum_weight
    if total_weight < params.eps_tol:
        if norm(p.current_dir) > params.eps_tol:
            return tuple(normalize_vec(p.current_dir))
        return (0.0, 0.0, 1.0)
    total_g = [x / total_weight for x in total_g]
    if norm(total_g) < params.eps_tol:
        return (0.0, 0.0, 0.0)
    return tuple(normalize_vec(total_g))


# ---------------------------------------------------------------------------
# Persistent bonding and transport
# ---------------------------------------------------------------------------

def form_bonds(nodes: List[Node], params: Params) -> None:
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if not a.alive or not b.alive:
                continue
            if b.id in a.bonds:
                continue
            if len(a.bonds) >= params.max_bonds or len(b.bonds) >= params.max_bonds:
                continue
            d = dist(a.pos, b.pos)
            if d > params.bond_distance or d < 0.01:
                continue
            sim = dot(a.identity, b.identity) / (norm(a.identity) * norm(b.identity) + 1e-9)
            lonely_a = not a.bonds
            lonely_b = not b.bonds
            role_bonus = params.role_bond_bonus * role_complementarity(get_role(a), get_role(b)) if params.directional_bonding else 0.0
            compat = sim + (params.hello_strength if lonely_a and lonely_b else 0.0) * 0.1 + role_bonus
            if not (compat >= params.compatibility_threshold or (lonely_a and lonely_b)):
                continue
            bond_dir = tuple(normalize_vec((b.pos[0] - a.pos[0], b.pos[1] - a.pos[1], b.pos[2] - a.pos[2])))
            opposite = (-bond_dir[0], -bond_dir[1], -bond_dir[2])
            can_bond_a = all(angle_between(bond_dir, a.bond_dirs[existing_id]) >= params.max_bond_angle for existing_id in a.bonds if existing_id in a.bond_dirs)
            can_bond_b = all(angle_between(opposite, b.bond_dirs[existing_id]) >= params.max_bond_angle for existing_id in b.bonds if existing_id in b.bond_dirs)
            if can_bond_a and can_bond_b:
                connect_nodes(a, b)


def transport_energy(nodes: List[Node], vacuum: VacuumMemory, params: Params) -> Dict[int, float]:
    by_id = node_map(nodes)
    flows = []
    incoming: Dict[int, float] = {n.id: 0.0 for n in nodes}
    seen = set()
    for p in nodes:
        if not p.alive:
            continue
        for bond_id in p.bonds:
            edge = tuple(sorted((p.id, bond_id)))
            if edge in seen:
                continue
            seen.add(edge)
            q = by_id.get(bond_id)
            if q is None or not q.alive:
                continue
            energy_diff = p.energy - q.energy
            if abs(energy_diff) < params.eps_tol:
                continue
            flow = params.D * energy_diff
            transport_skill = (p.identity[1] + q.identity[1]) / 2
            cost = params.kappa_transport * abs(flow) * (1.0 - 0.5 * transport_skill)
            flows.append((p, q, flow, cost))
    for p, q, flow, cost in flows:
        if flow > 0:
            actual = min(flow, p.energy)
            p.energy = max(p.energy - actual - cost / 2, 0.0)
            q.energy = max(q.energy + actual - cost / 2, 0.0)
            incoming[q.id] += actual
            q.acc_transport += actual
            p.acc_transport -= actual
            # Vacuum remembers the transport event
            vacuum.deposit(p.pos, actual)
            vacuum.deposit(q.pos, actual)
        else:
            actual = min(-flow, q.energy)
            q.energy = max(q.energy - actual - cost / 2, 0.0)
            p.energy = max(p.energy + actual - cost / 2, 0.0)
            incoming[p.id] += actual
            p.acc_transport += actual
            q.acc_transport -= actual
            vacuum.deposit(p.pos, actual)
            vacuum.deposit(q.pos, actual)
    return incoming


# ---------------------------------------------------------------------------
# Metabolism, identity, pressure
# ---------------------------------------------------------------------------

def apply_metabolism(nodes: List[Node], field: DiffuseField, vacuum: VacuumMemory, params: Params) -> None:
    cluster_sizes: Dict[int, int] = {}
    for comp in connected_components(nodes):
        for n in comp:
            cluster_sizes[n.id] = len(comp)
    by_id = node_map(nodes)
    for node in nodes:
        if not node.alive:
            continue
        id_norm = norm(node.identity)
        if id_norm < params.eps_tol:
            node.energy = max(node.energy - params.base_consumption * 0.5, 0.0)
            node.acc_metabolism += params.base_consumption * 0.5
            continue
        cluster_size = cluster_sizes.get(node.id, 1)
        node.cluster_size_history.append(cluster_size)
        producer_strength = node.identity[0] / id_norm
        harvested = field.harvest(node.pos, cluster_size, producer_strength)
        node.energy = min(node.energy + harvested, params.E0)
        node.total_harvested += harvested
        node.acc_harvest += harvested
        # Vacuum remembers harvest (energy drawn from field into node)
        vacuum.deposit(node.pos, harvested)
        bond_bonus = params.bonding_benefit * len(node.bonds)
        consumer_strength = node.identity[2] / id_norm
        receiving_transport = any(by_id[bid].alive and by_id[bid].energy > node.energy for bid in node.bonds if bid in by_id)
        consumer_penalty = params.consumer_penalty * consumer_strength if not receiving_transport else 0.0
        consumption = consumer_strength * params.base_consumption + params.base_consumption * 0.2
        shell_cost = params.shell_energy_cost * len(node.bonds)
        net_consumption = max(0.0, consumption + shell_cost + consumer_penalty - bond_bonus)
        node.energy = max(node.energy - net_consumption, 0.0)
        node.acc_metabolism += net_consumption


def update_identities(nodes: List[Node], params: Params) -> None:
    by_id = node_map(nodes)
    for p in nodes:
        if not p.alive:
            continue
        if random.random() < params.mutation_prob:
            mutation = [random.gauss(0, params.mutation_strength) for _ in range(3)]
            p.identity = normalize_vec([p.identity[i] + mutation[i] for i in range(3)])
            p.age += 1
            continue
        neighbors = [by_id[bid] for bid in p.bonds if bid in by_id and by_id[bid].alive]
        if neighbors:
            avg_identity = [sum(n.identity[i] for n in neighbors) / len(neighbors) for i in range(3)]
            p.identity = normalize_vec([p.identity[i] + params.identity_learning_rate * (avg_identity[i] - p.identity[i]) for i in range(3)])
        else:
            drift = [random.gauss(0, params.identity_noise) for _ in range(3)]
            p.identity = normalize_vec([p.identity[i] + drift[i] for i in range(3)])
        p.age += 1


def update_pressure(nodes: List[Node], params: Params) -> None:
    for node in nodes:
        if not node.alive:
            continue
        bond_pressure = len(node.bonds) * params.pressure_baseline
        energy_pressure = max(0.0, node.energy - params.E0 * 0.5) / params.E0 * 10.0
        node.pressure = (node.pressure + bond_pressure + energy_pressure) * params.pressure_decay


# ---------------------------------------------------------------------------
# Frontier and bifurcation logic  (INSTRUMENTED)
# ---------------------------------------------------------------------------

def surface_score(node: Node, nodes: List[Node], params: Params) -> float:
    neighbors = [other for other in nodes if other.alive and other.id != node.id and dist(node.pos, other.pos) <= params.surface_neighbor_radius]
    density_score = 1.0 - min(1.0, len(neighbors) / max(1.0, params.max_bonds * 1.5))
    if not node.bond_dirs:
        directional_score = 1.0
    else:
        resultant = [sum(direction[i] for direction in node.bond_dirs.values()) for i in range(3)]
        directional_score = min(1.0, norm(resultant) / len(node.bond_dirs))
    return max(0.0, min(1.0, 0.5 * density_score + 0.5 * directional_score))


def outward_direction(node: Node) -> Vec3:
    if node.bond_dirs:
        average = [sum(direction[i] for direction in node.bond_dirs.values()) for i in range(3)]
        direction = normalize_vec([-x for x in average])
        if norm(direction) > 1e-9:
            return tuple(direction)
    fallback = normalize_vec([random.gauss(0, 1) for _ in range(3)])
    return tuple(fallback)


# ---------------------------------------------------------------------------
# UPSTREAM INSTRUMENTATION FUNCTIONS
# ---------------------------------------------------------------------------

def compute_admissible_futures(node, nodes, field, params, surface_score_val):
    futures: List[AdmissibleFuture] = []
    base = outward_direction(node)
    candidates = [base]
    for _ in range(params.future_samples - 1):
        cand = normalize_vec([random.gauss(0, 1) for _ in range(3)])
        if dot(cand, base) < -0.3:
            cand = [-x for x in cand]
        candidates.append(tuple(cand))
    field_vec = field.gradient(node.pos, sample_radius=params.sense_radius)
    field_norm = norm(field_vec)
    spawn_cost = params.eps_spawn + params.eps_split
    for cand in candidates:
        min_angle = 180.0
        for bdir in node.bond_dirs.values():
            a = angle_between(cand, bdir)
            if a < min_angle:
                min_angle = a
        field_proj = dot(cand, field_vec) if field_norm > 0 else 0.0
        energy_cost = spawn_cost + params.move_cost_per_unit * params.child_push_distance
        score = (
            field_proj * 2.0
            + min_angle / 180.0 * 1.0
            + (node.energy - energy_cost) / params.E0 * 1.5
            + surface_score_val * 0.5
        )
        constraint = "free"
        if min_angle < params.max_bond_angle:
            constraint = "bond_blocked"
        if energy_cost > node.energy:
            constraint = "energy_blocked"
        futures.append(AdmissibleFuture(
            direction=list(cand), score=score, energy_cost=energy_cost,
            field_projection=field_proj, angular_gap_deg=min_angle, constraint_type=constraint,
        ))
    scores = [f.score for f in futures]
    max_score = max(scores) if scores else 0.0
    exp_scores = [math.exp(s - max_score) for s in scores]
    sum_exp = sum(exp_scores)
    probs = [e / sum_exp for e in exp_scores] if sum_exp > 0 else [1.0 / len(futures)] * len(futures)
    entropy = -sum(p * math.log(p + 1e-12) for p in probs)
    selected_idx = 0
    surprisal = -math.log(probs[selected_idx] + 1e-12)
    mean_score = sum(scores) / len(scores)
    var_score = sum((s - mean_score) ** 2 for s in scores) / len(scores)
    curvature = var_score / (abs(max_score) + 1e-9)
    return futures, entropy, selected_idx, surprisal, curvature


def capture_pre_bifurcation_snapshot(node, nodes, incoming_energy, params):
    neighbors = [other for other in nodes if other.alive and other.id != node.id and dist(node.pos, other.pos) <= params.surface_neighbor_radius]
    topology = sorted(node.bonds)
    if neighbors:
        mean_dist = sum(dist(node.pos, n.pos) for n in neighbors) / len(neighbors)
        density = 1.0 / (mean_dist + 0.1)
    else:
        density = 0.0
    flux = incoming_energy.get(node.id, 0.0)
    if len(node.bond_dirs) >= 2:
        dirs = list(node.bond_dirs.values())
        mean_dir = normalize_vec([sum(d[i] for d in dirs) for i in range(3)])
        deviations = [angle_between(d, mean_dir) for d in dirs]
        curvature = sum(deviations) / len(deviations)
    else:
        curvature = 0.0
    return topology, len(neighbors), density, flux, curvature


def compute_structural_inheritance(node, nodes, params):
    lineage_depth = node.generation
    motif = f"G{node.generation}_B{len(node.bonds)}_H{hash(tuple(sorted(node.bond_history))) % 10000}"
    by_id = node_map(nodes)
    if node.parent_id is not None and node.parent_id in by_id:
        parent = by_id[node.parent_id]
        gen_pressure = (parent.pressure + node.pressure) / 2.0
        parent_to_self = normalize_vec([node.pos[i] - parent.pos[i] for i in range(3)])
        parent_outward = outward_direction(parent)
        divergence = angle_between(parent_to_self, parent_outward)
    else:
        gen_pressure = node.pressure
        divergence = 0.0
    return lineage_depth, motif, gen_pressure, divergence


def probe_phase_space(node, nodes, field, params, futures_curvature):
    alive = [n for n in nodes if n.alive]
    if len(alive) > 5:
        centroid = [
            sum(n.energy for n in alive) / len(alive),
            sum(n.pressure for n in alive) / len(alive),
            sum(surface_score(n, nodes, params) for n in alive) / len(alive),
            sum(field.get(n.pos) for n in alive) / len(alive),
        ]
    else:
        centroid = [params.E0 * 0.5, params.pressure_baseline, 0.5, params.background_level]
    s = surface_score(node, nodes, params)
    point = [node.energy, node.pressure, s, field.get(node.pos)]
    d_manifold = math.sqrt(sum((a - b) ** 2 for a, b in zip(point, centroid)))
    sp = 1.0 / (1.0 + math.exp((d_manifold - 50.0) / params.manifold_softness))
    return point, d_manifold, sp, futures_curvature


def compute_counterfactual(node, actual_bifurcated, child_energy, params, best_future_score, hold_future_score):
    spawn_cost = params.eps_spawn + params.eps_split
    if actual_bifurcated:
        hold_energy = node.energy + child_energy + spawn_cost
        hold_pressure = node.pressure * 1.2
        projected_children = 0
        opportunity_cost = child_energy
        regret = max(0.0, hold_future_score - best_future_score) if hold_future_score is not None else 0.0
    else:
        hold_energy = node.energy
        hold_pressure = node.pressure
        projected_children = 1 if node.energy > params.bifurcation_energy_min else 0
        opportunity_cost = 0.0
        regret = 0.0
    return hold_energy, hold_pressure, projected_children, opportunity_cost, regret


# ---------------------------------------------------------------------------
# Bifurcation with full instrumentation + vacuum memory
# ---------------------------------------------------------------------------

def bifurcate(nodes, next_id, params, field, vacuum, step, incoming_energy):
    records: List[InstrumentedDecisionRecord] = []
    if not params.bifurcation_enabled or step < params.bifurcation_start_step:
        return [], next_id, records
    if len(nodes) >= params.max_nodes:
        return [], next_id, records
    new_nodes: List[Node] = []

    for node in list(nodes):
        if not node.alive:
            continue
        if len(nodes) + len(new_nodes) >= params.max_nodes:
            break
        reasons: List[str] = []
        s_score = surface_score(node, nodes + new_nodes, params)
        local_field = field.get(node.pos)

        if len(node.bonds) < params.min_bonds_to_bifurcate:
            reasons.append("insufficient_structural_integration")
        if node.energy < params.bifurcation_energy_min:
            reasons.append("energy_below_minimum")
        if node.energy > params.bifurcation_energy_max:
            reasons.append("energy_above_window")
        if node.pressure < params.bifurcation_pressure_threshold:
            reasons.append("pressure_below_threshold")
        if s_score < params.surface_score_min:
            reasons.append("not_surface_exposed")
        spawn_cost = params.eps_spawn + params.eps_split
        if node.energy < spawn_cost * 2:
            reasons.append("insufficient_spawn_budget")

        eligible = not reasons

        # === UPSTREAM INSTRUMENTATION ===
        futures, futures_entropy, selected_idx, surprisal, constraint_curvature = compute_admissible_futures(
            node, nodes, field, params, s_score
        )
        snapshot_topo, snapshot_nbrs, snapshot_density, snapshot_flux, snapshot_curvature = capture_pre_bifurcation_snapshot(
            node, nodes, incoming_energy, params
        )
        lineage_depth, motif, gen_pressure, divergence = compute_structural_inheritance(node, nodes, params)
        phase_point, manifold_dist, survival_prob, basin_curve = probe_phase_space(
            node, nodes, field, params, constraint_curvature
        )

        # Vacuum memory at decision point
        local_vacuum = vacuum.get(node.pos)
        vacuum_grad = vacuum.gradient(node.pos)
        vacuum_influence = 0.0
        role = get_role(node)
        if role == "P":
            vacuum_influence = -local_vacuum * params.vacuum_producer_repulsion / 100.0
        elif role == "C":
            vacuum_influence = local_vacuum * params.vacuum_consumer_attraction / 100.0
        # Inherit parent's vacuum trace
        by_id = node_map(nodes)
        vacuum_inherited = 0.0
        if node.parent_id is not None and node.parent_id in by_id:
            vacuum_inherited = vacuum.get(by_id[node.parent_id].pos)

        # Energy flow at decision moment
        reserve = max(0.0, node.energy - incoming_energy.get(node.id, 0.0))
        source_harvest = node.acc_harvest
        source_transport = node.acc_transport
        source_reserve = reserve
        sink_metabolism = node.acc_metabolism
        sink_movement = node.acc_movement
        sink_spawn = spawn_cost if eligible else 0.0
        child_gift = 0.0
        parent_retained = node.energy
        e_balance = (source_harvest + source_transport + source_reserve) - (sink_metabolism + sink_movement + sink_spawn + child_gift)

        best_future_score = max((f.score for f in futures), default=0.0)
        hold_future_score = next((f.score for f in futures if f.constraint_type == "free"), None)

        if not eligible:
            cf_hold_e, cf_hold_p, cf_proj_children, cf_opp_cost, cf_regret = compute_counterfactual(
                node, False, 0.0, params, best_future_score, hold_future_score
            )
            record = InstrumentedDecisionRecord(
                step=step, node_id=node.id, generation=node.generation, role=get_role(node),
                bond_count=len(node.bonds), energy=node.energy, pressure=node.pressure,
                surface_score=s_score, local_field=local_field,
                incoming_energy_flow=incoming_energy.get(node.id, 0.0),
                eligible=False, selected_action="HOLD", rejection_reasons=reasons.copy(),
                admissible_futures=[asdict(f) for f in futures],
                futures_count=len(futures), futures_entropy=futures_entropy,
                selected_future_index=-1, selection_surprisal=0.0,
                constraint_curvature=constraint_curvature,
                snapshot_bond_topology=snapshot_topo, snapshot_neighbor_count=snapshot_nbrs,
                snapshot_local_density=snapshot_density, snapshot_incoming_flux=snapshot_flux,
                snapshot_stem_curvature=snapshot_curvature,
                energy_source_harvest=source_harvest, energy_source_transport=source_transport,
                energy_source_reserve=source_reserve, energy_sink_metabolism=sink_metabolism,
                energy_sink_movement=sink_movement, energy_sink_spawn=sink_spawn,
                energy_child_gift=child_gift, energy_parent_retained=parent_retained,
                energy_balance=e_balance,
                lineage_depth=lineage_depth, ancestral_motif=motif,
                generational_pressure_avg=gen_pressure, structural_divergence=divergence,
                phase_energy=phase_point[0], phase_pressure=phase_point[1],
                phase_surface=phase_point[2], phase_field=phase_point[3],
                manifold_distance=manifold_dist, survival_probability=survival_prob,
                basin_curvature=basin_curve,
                counterfactual_hold_energy=cf_hold_e, counterfactual_hold_pressure=cf_hold_p,
                counterfactual_projected_children=cf_proj_children,
                counterfactual_opportunity_cost=cf_opp_cost, counterfactual_regret=cf_regret,
                local_vacuum=local_vacuum, vacuum_gradient=list(vacuum_grad),
                vacuum_influence=vacuum_influence, vacuum_inherited_trace=vacuum_inherited,
            )
            records.append(record)
            continue

        parent_role = get_role(node)
        child_role = params.role_cycle.get(parent_role, parent_role) if random.random() < params.role_mutation_prob else parent_role
        child_energy = (node.energy - spawn_cost) / 2.0
        node.energy = child_energy
        push_dir = outward_direction(node)
        child_pos = (
            node.pos[0] + push_dir[0] * params.child_push_distance,
            node.pos[1] + push_dir[1] * params.child_push_distance,
            node.pos[2] + push_dir[2] * params.child_push_distance,
        )
        child = Node(next_id, child_pos, child_energy, node.id, "child", True, child_role)
        child.generation = node.generation + 1
        child.identity = identity_for_role(child_role)
        child.last_field = field.get(child_pos)
        child.best_field_seen = child.last_field
        child.best_field_pos = child_pos
        child.current_dir = push_dir
        connect_nodes(node, child)
        new_nodes.append(child)
        node.bifurcation_count += 1
        node.pressure = 0.0

        # Vacuum remembers the spawn event
        vacuum.deposit(node.pos, spawn_cost)
        vacuum.deposit(child_pos, child_energy)

        selected_idx = 0
        best_match = -1.0
        for idx, f in enumerate(futures):
            sim = dot(push_dir, f.direction) / (norm(push_dir) * norm(f.direction) + 1e-9)
            if sim > best_match:
                best_match = sim
                selected_idx = idx
        max_score = max(f.score for f in futures)
        exp_scores = [math.exp(f.score - max_score) for f in futures]
        sum_exp = sum(exp_scores)
        prob_sel = exp_scores[selected_idx] / sum_exp if sum_exp > 0 else 1.0 / len(futures)
        surprisal = -math.log(prob_sel + 1e-12)

        child_gift = child_energy
        parent_retained = node.energy
        sink_spawn = spawn_cost
        e_balance = (source_harvest + source_transport + source_reserve) - (sink_metabolism + sink_movement + sink_spawn + child_gift)

        cf_hold_e, cf_hold_p, cf_proj_children, cf_opp_cost, cf_regret = compute_counterfactual(
            node, True, child_energy, params, best_future_score, hold_future_score
        )

        record = InstrumentedDecisionRecord(
            step=step, node_id=node.id, generation=node.generation, role=get_role(node),
            bond_count=len(node.bonds), energy=node.energy, pressure=node.pressure,
            surface_score=s_score, local_field=local_field,
            incoming_energy_flow=incoming_energy.get(node.id, 0.0),
            eligible=True, selected_action="BIFURCATE", rejection_reasons=[],
            admissible_futures=[asdict(f) for f in futures],
            futures_count=len(futures), futures_entropy=futures_entropy,
            selected_future_index=selected_idx, selection_surprisal=surprisal,
            constraint_curvature=constraint_curvature,
            snapshot_bond_topology=snapshot_topo, snapshot_neighbor_count=snapshot_nbrs,
            snapshot_local_density=snapshot_density, snapshot_incoming_flux=snapshot_flux,
            snapshot_stem_curvature=snapshot_curvature,
            energy_source_harvest=source_harvest, energy_source_transport=source_transport,
            energy_source_reserve=source_reserve, energy_sink_metabolism=sink_metabolism,
            energy_sink_movement=sink_movement, energy_sink_spawn=sink_spawn,
            energy_child_gift=child_gift, energy_parent_retained=parent_retained,
            energy_balance=e_balance,
            lineage_depth=lineage_depth, ancestral_motif=motif,
            generational_pressure_avg=gen_pressure, structural_divergence=divergence,
            phase_energy=phase_point[0], phase_pressure=phase_point[1],
            phase_surface=phase_point[2], phase_field=phase_point[3],
            manifold_distance=manifold_dist, survival_probability=survival_prob,
            basin_curvature=basin_curve,
            counterfactual_hold_energy=cf_hold_e, counterfactual_hold_pressure=cf_hold_p,
            counterfactual_projected_children=cf_proj_children,
            counterfactual_opportunity_cost=cf_opp_cost, counterfactual_regret=cf_regret,
            local_vacuum=local_vacuum, vacuum_gradient=list(vacuum_grad),
            vacuum_influence=vacuum_influence, vacuum_inherited_trace=vacuum_inherited,
            child_role=child_role, child_id=child.id, child_direction=list(push_dir),
            energy_partition=(node.energy, child_energy),
        )
        records.append(record)
        next_id += 1

    return new_nodes, next_id, records


# ---------------------------------------------------------------------------
# Motion and shape analysis
# ---------------------------------------------------------------------------

def move_node(node, move_vec, all_nodes, vacuum, params):
    if norm(move_vec) < params.eps_tol:
        return
    if params.freeze_anchored_structure and node.anchored:
        return
    energy_factor = min(1.0, node.energy / params.E0 + 0.3)
    speed = params.move_speed * energy_factor
    id_norm = norm(node.identity)
    if id_norm > params.eps_tol:
        speed *= 0.5 + node.identity[0] / id_norm
    new_pos = tuple(node.pos[i] + move_vec[i] * speed for i in range(3))
    distance_moved = dist(new_pos, node.pos)
    move_cost = distance_moved * params.move_cost_per_unit
    if node.energy >= move_cost:
        node.pos = new_pos
        node.energy -= move_cost
        node.acc_movement += move_cost
        node.current_dir = move_vec
        # Vacuum remembers movement (energy spent to change position)
        vacuum.deposit(new_pos, move_cost)
    elif distance_moved > params.eps_tol:
        max_distance = node.energy / params.move_cost_per_unit
        if max_distance > 0.1:
            scale = max_distance / distance_moved
            node.pos = tuple(node.pos[i] + move_vec[i] * speed * scale for i in range(3))
            actual_cost = node.energy
            node.acc_movement += actual_cost
            node.energy = 0.0
            node.current_dir = move_vec
            vacuum.deposit(node.pos, actual_cost)


def analyze_cluster_shape(cluster: List[Node]):
    if len(cluster) <= 1:
        return "SINGLE", 0.0
    angles = []
    for node in cluster:
        directions = [node.bond_dirs[bid] for bid in node.bonds if bid in node.bond_dirs]
        for i in range(len(directions)):
            for j in range(i + 1, len(directions)):
                angles.append(angle_between(directions[i], directions[j]))
    avg_angle = sum(angles) / len(angles) if angles else 0.0
    extents = [max(n.pos[i] for n in cluster) - min(n.pos[i] for n in cluster) for i in range(3)]
    dims = sorted(extents, reverse=True)
    if len(cluster) <= 3:
        shape = "CHAIN" if dims[0] > max(dims[1], dims[2]) * 3 else "CLUSTER"
    elif dims[0] > max(dims[1], dims[2]) * 3:
        shape = "CHAIN"
    elif dims[2] < dims[0] * 0.3 and dims[2] < dims[1] * 0.3:
        shape = "SHEET"
    else:
        shape = "VOLUME"
    return shape, avg_angle


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_seed_and_grow(steps: int = 500, num_nodes: int = 12, seed: int = 42, output_dir: Optional[Path] = None):
    params = Params()
    random.seed(seed)
    field = DiffuseField(params, bounds=15, seed=seed)
    vacuum = VacuumMemory(params)

    nodes: List[Node] = []
    next_id = num_nodes
    for i in range(num_nodes):
        pos = (random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))
        node = Node(i, pos, params.E0 * 0.5, None, "seed", True)
        node.identity = normalize_vec([random.random(), random.random(), random.random()])
        node.last_field = field.get(pos)
        node.best_field_seen = node.last_field
        node.best_field_pos = pos
        nodes.append(node)

    print("=== NATURAL MATH SEED-AND-GROW CRYSTAL v6 INSTRUMENTED + VACUUM MEMORY ===")
    print(f"Seed nodes: {num_nodes}")
    print(f"Steps: {steps}")
    print("Vacuum memory: coarse grid, slow decay, role-conditional sensing")
    print("  Producers repelled by high vacuum (avoid depleted ghosts)")
    print("  Consumers attracted to high vacuum (follow prior flow residue)")
    print()

    history = []
    instrumented_records: List[InstrumentedDecisionRecord] = []

    for step in range(steps):
        active = [n for n in nodes if n.alive]
        if not active:
            print(f"*** EXTINCTION at step {step + 1} ***")
            break
        shells = compute_shells(nodes, params)
        active_snapshot = active[:]
        form_bonds(nodes, params)
        incoming_energy = transport_energy(nodes, vacuum, params)
        apply_metabolism(nodes, field, vacuum, params)
        field.update()
        vacuum.update()
        update_identities(nodes, params)
        update_pressure(nodes, params)
        new_nodes, next_id, records = bifurcate(nodes, next_id, params, field, vacuum, step, incoming_energy)
        instrumented_records.extend(records)
        if new_nodes:
            nodes.extend(new_nodes)
        for node in active:
            if node.energy < params.tau:
                continue
            move_vec = compute_movement_vector(node, active_snapshot, field, shells, vacuum, params)
            if norm(move_vec) > params.eps_tol:
                move_node(node, move_vec, nodes, vacuum, params)
                if not node.anchored:
                    node.type = "tip"
        deaths = []
        for node in nodes:
            if node.alive and node.energy < params.tau - params.eps_tol:
                node.alive = False
                node.type = "inert"
                deaths.append(node.id)
                # Vacuum remembers death (energy released back to void)
                vacuum.deposit(node.pos, params.tau)
        if step < 10 or step % 50 == 49 or new_nodes:
            alive = [n for n in nodes if n.alive]
            clusters = connected_components(nodes)
            max_size = max((len(c) for c in clusters), default=0)
            total_bonds = sum(len(n.bonds) for n in alive) // 2
            roles = {}
            for n in alive:
                roles[get_role(n)] = roles.get(get_role(n), 0) + 1
            history.append({
                "step": step + 1,
                "alive": len(alive),
                "total_nodes": len(nodes),
                "clusters": len(clusters),
                "max_size": max_size,
                "bonds": total_bonds,
                "new_nodes": len(new_nodes),
                "deaths": len(deaths),
                "roles": roles,
            })
            phase = "SEED" if step < params.bifurcation_start_step else "GROWTH"
            print(f"[{phase}] S{step + 1:3d}: {len(alive)} alive / {len(nodes)} total | {len(clusters)} clusters | max={max_size} | bonds={total_bonds} | +{len(new_nodes)} / -{len(deaths)}")

    alive = [n for n in nodes if n.alive]
    clusters = connected_components(nodes)
    print()
    print("=" * 72)
    print("FINAL STRUCTURE")
    print("=" * 72)
    print(f"Survivors: {len(alive)}/{len(nodes)}")
    print(f"Clusters: {len(clusters)}")
    print(f"Persistent bonds: {sum(len(n.bonds) for n in alive) // 2}")
    print(f"Bifurcations: {sum(n.bifurcation_count for n in nodes)}")
    print(f"Instrumented decision records: {len(instrumented_records)}")

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        nodes_payload = []
        for n in nodes:
            nodes_payload.append({
                "id": n.id, "pos": n.pos, "energy": n.energy, "pressure": n.pressure,
                "parent_id": n.parent_id, "type": n.type, "alive": n.alive,
                "role": get_role(n), "bonds": n.bonds, "generation": n.generation,
                "anchored": n.anchored, "bifurcation_count": n.bifurcation_count,
                "acc_harvest": n.acc_harvest, "acc_transport": n.acc_transport,
                "acc_metabolism": n.acc_metabolism, "acc_movement": n.acc_movement,
            })
        (output_dir / "nodes.json").write_text(json.dumps(nodes_payload, indent=2), encoding="utf-8")
        (output_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        (output_dir / "instrumented_decisions.json").write_text(
            json.dumps([asdict(r) for r in instrumented_records], indent=2), encoding="utf-8"
        )
        (output_dir / "vacuum_memory.json").write_text(
            json.dumps(vacuum.to_list(), indent=2), encoding="utf-8"
        )
        summary = {
            "steps_requested": steps, "seed": seed, "initial_nodes": num_nodes,
            "total_nodes": len(nodes), "survivors": len(alive), "clusters": len(clusters),
            "persistent_bonds": sum(len(n.bonds) for n in alive) // 2,
            "bifurcations": sum(n.bifurcation_count for n in nodes),
            "instrumented_records": len(instrumented_records),
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return nodes, field, history, instrumented_records, vacuum


def parse_args():
    parser = argparse.ArgumentParser(description="Natural Math Seed-and-Grow Crystal v6 INSTRUMENTED + VACUUM")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--nodes", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("seed_and_grow_v6_instrumented_vacuum_output"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_seed_and_grow(steps=args.steps, num_nodes=args.nodes, seed=args.seed, output_dir=args.out)


if __name__ == "__main__":
    main()
