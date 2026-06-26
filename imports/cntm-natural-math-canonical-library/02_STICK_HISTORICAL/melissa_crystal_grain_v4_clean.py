import random
import math
from typing import List, Tuple


class CrystalParams:
    def __init__(self, steps_per_hour=30):
        self.steps_per_hour = steps_per_hour
        self.total_day_steps = 24 * steps_per_hour

        # Energy & movement
        self.E0 = 800.0
        self.tau = 5.0
        self.move_speed = 0.5
        self.move_cost_per_unit = 0.15
        self.base_consumption = 0.5
        self.bonding_benefit = 0.6
        self.bond_energy_reward = 0.1

        # Social gradient
        self.r_sq = 50.0 ** 2
        self.deficit_strength = 20.0

        # Bonding mechanics
        self.max_bonds = 3
        self.bond_range_sq = 16.0

        # Spring + soft position lock
        self.spring_stiffness = 0.5
        self.bond_keep_distance_sq = 2.25
        self.bond_break_distance_sq = 9.0

        # Boundary
        self.boundary_radius = 50.0
        self.boundary_strength = 0.05

        # Bonded movement damping
        self.bonded_speed_factor = 0.6

        self.eps_tol = 1e-9


class CrystalNode:
    def __init__(self, nid: int, pos: Tuple[float, float, float], energy: float):
        self.id = nid
        self.pos = pos
        self.energy = energy
        self.bonds: List[int] = []
        self.alive = True
        self.age = 0


def Q(p1, p2) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    dz = p1[2] - p2[2]
    return dx * dx + dy * dy + dz * dz


def norm(v) -> float:
    return math.sqrt(sum(x * x for x in v))


def normalize(v):
    n = norm(v)
    if n < 1e-12:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def compute_movement_vector(
    p: CrystalNode, neighbors: List[CrystalNode], params: CrystalParams
):
    g = [0.0, 0.0, 0.0]
    weight_sum = 0.0

    for q in neighbors:
        d2 = Q(p.pos, q.pos)
        if d2 > params.r_sq + params.eps_tol or d2 < params.eps_tol:
            continue

        w = 1.0 / math.sqrt(d2)
        weight_sum += w

        deficit_p = max(0.0, (params.E0 - p.energy) / params.E0)
        deficit_q = max(0.0, (params.E0 - q.energy) / params.E0)
        deficit_factor = params.deficit_strength * deficit_p * deficit_q

        raw_diff = q.energy - p.energy
        effective_diff = raw_diff + deficit_factor

        dx = q.pos[0] - p.pos[0]
        dy = q.pos[1] - p.pos[1]
        dz = q.pos[2] - p.pos[2]

        g[0] += w * effective_diff * dx
        g[1] += w * effective_diff * dy
        g[2] += w * effective_diff * dz

    if weight_sum < params.eps_tol:
        rdir = [random.gauss(0, 0.1) for _ in range(3)]
        return normalize(rdir)

    g = [g[0] / weight_sum, g[1] / weight_sum, g[2] / weight_sum]
    return normalize(g)


def apply_spring_and_lock(
    p: CrystalNode, all_nodes: List[CrystalNode], params: CrystalParams
):
    force = [0.0, 0.0, 0.0]

    for bid in p.bonds:
        q = all_nodes[bid]
        if not q.alive:
            continue

        d2 = Q(p.pos, q.pos)
        if d2 > params.bond_break_distance_sq:
            continue

        if d2 > params.bond_keep_distance_sq:
            dx = q.pos[0] - p.pos[0]
            dy = q.pos[1] - p.pos[1]
            dz = q.pos[2] - p.pos[2]
            d = math.sqrt(d2)
            rest = math.sqrt(params.bond_keep_distance_sq)
            stretch = d - rest
            mag = params.spring_stiffness * stretch

            if d > 1e-9:
                force[0] += mag * dx / d
                force[1] += mag * dy / d
                force[2] += mag * dz / d

        if d2 > 4.0:
            mx = (p.pos[0] + q.pos[0]) / 2.0
            my = (p.pos[1] + q.pos[1]) / 2.0
            mz = (p.pos[2] + q.pos[2]) / 2.0
            force[0] += 0.2 * (mx - p.pos[0])
            force[1] += 0.2 * (my - p.pos[1])
            force[2] += 0.2 * (mz - p.pos[2])

    return force


def form_bonds(nodes: List[CrystalNode], params: CrystalParams):
    for node in nodes:
        if node.alive:
            node.bonds = []

    count = len(nodes)
    for i in range(count):
        a = nodes[i]
        if not a.alive:
            continue

        for j in range(i + 1, count):
            b = nodes[j]
            if not b.alive:
                continue

            if len(a.bonds) >= params.max_bonds or len(b.bonds) >= params.max_bonds:
                continue

            d2 = Q(a.pos, b.pos)
            if d2 > params.bond_range_sq + params.eps_tol or d2 < params.eps_tol:
                continue

            avg_e = (a.energy + b.energy) / 2.0
            a.energy = avg_e
            b.energy = avg_e
            a.bonds.append(b.id)
            b.bonds.append(a.id)


def apply_metabolism(nodes: List[CrystalNode], params: CrystalParams):
    for node in nodes:
        if not node.alive:
            continue

        bond_bonus = params.bonding_benefit * len(node.bonds)
        consumption = max(0.0, params.base_consumption - bond_bonus)
        node.energy = max(node.energy - consumption, 0.0)
        node.energy += len(node.bonds) * params.bond_energy_reward
        node.energy = min(node.energy, params.E0)
        node.age += 1


def enforce_boundary(
    node, center=(0.0, 0.0, 0.0), radius=50.0, strength=0.05
):
    dx = node.pos[0] - center[0]
    dy = node.pos[1] - center[1]
    dz = node.pos[2] - center[2]
    d = math.sqrt(dx * dx + dy * dy + dz * dz)

    if d > radius:
        factor = 1.0 - strength * (d - radius) / d
        node.pos = (
            center[0] + dx * factor,
            center[1] + dy * factor,
            center[2] + dz * factor,
        )


def move_node(p: CrystalNode, social_dir, spring_force, params):
    total_dir = [
        social_dir[0] + spring_force[0],
        social_dir[1] + spring_force[1],
        social_dir[2] + spring_force[2],
    ]
    total_dir = normalize(total_dir)

    if norm(total_dir) < params.eps_tol:
        return

    energy_factor = min(1.0, p.energy / params.E0 + 0.3)
    speed = params.move_speed * energy_factor
    if len(p.bonds) > 0:
        speed *= params.bonded_speed_factor

    new_pos = (
        p.pos[0] + total_dir[0] * speed,
        p.pos[1] + total_dir[1] * speed,
        p.pos[2] + total_dir[2] * speed,
    )

    dist_moved = math.sqrt(Q(p.pos, new_pos))
    move_cost = dist_moved * params.move_cost_per_unit

    if p.energy >= move_cost:
        p.pos = new_pos
        p.energy -= move_cost
    else:
        max_dist = p.energy / params.move_cost_per_unit
        if max_dist > 0.01:
            scale = max_dist / dist_moved
            p.pos = (
                p.pos[0] + total_dir[0] * speed * scale,
                p.pos[1] + total_dir[1] * speed * scale,
                p.pos[2] + total_dir[2] * speed * scale,
            )
        p.energy = 0.0

    enforce_boundary(
        p,
        radius=params.boundary_radius,
        strength=params.boundary_strength,
    )


def detect_clusters(atoms: List[CrystalNode]):
    alive = [a for a in atoms if a.alive]
    visited = set()
    clusters = []

    for atom in alive:
        if atom.id in visited:
            continue

        queue = [atom.id]
        cluster = []

        while queue:
            nid = queue.pop()
            if nid in visited:
                continue

            visited.add(nid)
            node = atoms[nid]
            cluster.append(node)

            for bid in node.bonds:
                if bid not in visited and atoms[bid].alive:
                    queue.append(bid)

        clusters.append(cluster)

    return clusters


def run_crystal_simulation(
    steps_per_hour=30, num_atoms=20, seed=42, verbose=True
):
    random.seed(seed)
    params = CrystalParams(steps_per_hour)
    total_steps = params.total_day_steps

    atoms = []
    for i in range(num_atoms):
        x = random.uniform(-8, 8)
        y = random.uniform(-8, 8)
        z = random.uniform(-8, 8)
        energy = params.E0 * random.uniform(0.9, 1.1)
        atoms.append(CrystalNode(i, (x, y, z), energy))

    if verbose:
        print("=== CRYSTAL GRAIN v4: STRONG SPRING + SOFT LOCK ===")
        print(f"24h, {steps_per_hour} steps/hour, {num_atoms} atoms")
        print(
            f"Bond range <=4, spring stiffness={params.spring_stiffness}, "
            f"sensing radius={math.sqrt(params.r_sq):.0f}"
        )
        print()

    for step in range(total_steps):
        alive = [a for a in atoms if a.alive]
        if not alive:
            if verbose:
                print(f"Extinction at step {step + 1}")
            break

        social_dir = {}
        for atom in alive:
            neighbors = [
                q
                for q in alive
                if Q(atom.pos, q.pos) <= params.r_sq + params.eps_tol
                and q.id != atom.id
            ]
            social_dir[atom.id] = compute_movement_vector(
                atom, neighbors, params
            )

        spring_force = {
            atom.id: apply_spring_and_lock(atom, atoms, params)
            for atom in alive
        }

        for atom in alive:
            move_node(
                atom,
                social_dir[atom.id],
                spring_force[atom.id],
                params,
            )

        form_bonds(atoms, params)
        apply_metabolism(atoms, params)

        for atom in atoms:
            if atom.alive and atom.energy < params.tau:
                atom.alive = False

        if verbose and (
            step % steps_per_hour == 0 or step == total_steps - 1
        ):
            hour = step // steps_per_hour
            minute = (step % steps_per_hour) * 60 // steps_per_hour
            alive_now = [a for a in atoms if a.alive]
            clusters = detect_clusters(atoms)
            avg_size = (
                sum(len(c) for c in clusters) / len(clusters)
                if clusters
                else 0
            )
            max_size = max((len(c) for c in clusters), default=0)
            bonded = sum(1 for a in alive_now if a.bonds)

            print(
                f"Time {hour:02d}:{minute:02d} | "
                f"alive={len(alive_now):3d} | "
                f"clusters={len(clusters):3d} | "
                f"avg={avg_size:.2f} | max={max_size:2d} | "
                f"bonded={bonded:3d}"
            )

    return atoms


if __name__ == "__main__":
    result = run_crystal_simulation(
        steps_per_hour=30, num_atoms=20, seed=42
    )
    clusters = detect_clusters(result)
    sizes = sorted((len(c) for c in clusters), reverse=True)
    print(f"\nFinal cluster sizes: {sizes}")
