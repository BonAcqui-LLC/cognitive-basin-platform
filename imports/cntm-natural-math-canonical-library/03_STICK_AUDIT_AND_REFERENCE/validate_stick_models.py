"""
Validation harness for Melissa's v4 "Stick" program and the hardened v5 model.

Runs seed sweeps and ablations. This is an engineering diagnostic, not a
physical validation and not evidence of crystal formation.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import melissa_crystal_grain_v4_clean as v4
import natural_math_stick_v5_hardened as v5


def run_v4_variant(seed: int, overrides: dict | None = None) -> dict:
    random.seed(seed)
    params = v4.CrystalParams(30)
    for key, value in (overrides or {}).items():
        setattr(params, key, value)

    atoms = []
    for node_id in range(20):
        position = tuple(random.uniform(-8, 8) for _ in range(3))
        energy = params.E0 * random.uniform(0.9, 1.1)
        atoms.append(v4.CrystalNode(node_id, position, energy))

    initial_energy = sum(node.energy for node in atoms)

    for _ in range(params.total_day_steps):
        alive = [node for node in atoms if node.alive]
        if not alive:
            break

        social = {}
        for node in alive:
            neighbors = [
                other
                for other in alive
                if other.id != node.id
                and v4.Q(node.pos, other.pos)
                <= params.r_sq + params.eps_tol
            ]
            social[node.id] = v4.compute_movement_vector(
                node, neighbors, params
            )

        springs = {
            node.id: v4.apply_spring_and_lock(node, atoms, params)
            for node in alive
        }

        for node in alive:
            v4.move_node(
                node, social[node.id], springs[node.id], params
            )

        v4.form_bonds(atoms, params)
        v4.apply_metabolism(atoms, params)

        for node in atoms:
            if node.alive and node.energy < params.tau:
                node.alive = False

    clusters = v4.detect_clusters(atoms)
    sizes = sorted((len(cluster) for cluster in clusters), reverse=True)
    alive = [node for node in atoms if node.alive]

    return {
        "survivors": len(alive),
        "bonded_nodes": sum(1 for node in alive if node.bonds),
        "cluster_count": len(sizes),
        "largest_cluster": max(sizes, default=0),
        "energy_ratio": (
            sum(node.energy for node in alive) / initial_energy
            if initial_energy
            else 0.0
        ),
    }


def run_v5_variant(seed: int, overrides: dict | None = None) -> dict:
    params = v5.StickParams()
    for key, value in (overrides or {}).items():
        setattr(params, key, value)

    result = v5.StickSimulation(params=params, seed=seed).run()
    return {
        "survivors": result.survivors,
        "bonded_nodes": result.bonded_nodes,
        "cluster_count": len(result.cluster_sizes),
        "largest_cluster": max(result.cluster_sizes, default=0),
        "energy_ratio": (
            result.total_final_energy / result.total_initial_energy
            if result.total_initial_energy
            else 0.0
        ),
    }


def aggregate(rows: list[dict]) -> dict:
    return {
        "runs": len(rows),
        "survivors_mean": statistics.mean(r["survivors"] for r in rows),
        "all_survive_fraction": (
            sum(r["survivors"] == 20 for r in rows) / len(rows)
        ),
        "bonded_nodes_mean": statistics.mean(
            r["bonded_nodes"] for r in rows
        ),
        "cluster_count_mean": statistics.mean(
            r["cluster_count"] for r in rows
        ),
        "largest_cluster_mean": statistics.mean(
            r["largest_cluster"] for r in rows
        ),
        "energy_ratio_mean": statistics.mean(
            r["energy_ratio"] for r in rows
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    args = parser.parse_args()

    experiments = {
        "v4_baseline": (
            run_v4_variant,
            {},
        ),
        "v4_no_deficit_coupling": (
            run_v4_variant,
            {"deficit_strength": 0.0},
        ),
        "v4_no_bond_reward": (
            run_v4_variant,
            {"bond_energy_reward": 0.0},
        ),
        "v4_no_bond_benefit_or_reward": (
            run_v4_variant,
            {
                "bonding_benefit": 0.0,
                "bond_energy_reward": 0.0,
            },
        ),
        "v5_closed_resource_baseline": (
            run_v5_variant,
            {},
        ),
        "v5_no_deficit_coupling": (
            run_v5_variant,
            {"deficit_strength": 0.0},
        ),
        "v5_no_bond_saving": (
            run_v5_variant,
            {"saving_per_bond": 0.0},
        ),
    }

    output = {}
    for name, (runner, overrides) in experiments.items():
        rows = [
            runner(seed=seed, overrides=overrides)
            for seed in range(args.seeds)
        ]
        output[name] = aggregate(rows)

    output["interpretation_note"] = (
        "These are software ablations. Similar baseline and no-deficit "
        "results indicate that clustering cannot yet be attributed solely "
        "to the deficit term. Physical and coding claims require separate "
        "experiments."
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
