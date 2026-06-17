"""
Basic Persistent Growth System workload for BasinLab.
"""

from __future__ import annotations

import base64
import pickle
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class LocalProcessState(str, Enum):
    EXTEND = "EXTEND"
    SENSE = "SENSE"
    RESTRICT = "RESTRICT"


@dataclass
class GrowthNode:
    node_id: str
    x: int
    y: int
    energy: float
    parent_id: str = ""
    children: List[str] = field(default_factory=list)
    state: LocalProcessState = LocalProcessState.SENSE
    contact: bool = False


@dataclass
class GrowthWorld:
    seed: int
    width: int = 21
    height: int = 21
    energy_threshold: float = 120.0
    spawn_energy_cost: float = 8.0
    spawn_probability: float = 0.01
    step_count: int = 0
    next_node_index: int = 1
    nodes: Dict[str, GrowthNode] = field(default_factory=dict)
    occupied: Dict[Tuple[int, int], str] = field(default_factory=dict)
    rng: random.Random = field(default_factory=random.Random)


def create_growth_world(seed: int, width: int = 21, height: int = 21) -> GrowthWorld:
    return GrowthWorld(seed=seed, width=width, height=height, rng=random.Random(seed))


def _next_node_id(world: GrowthWorld) -> str:
    node_id = f"node-{world.next_node_index:04d}"
    world.next_node_index += 1
    return node_id


def add_seed(world: GrowthWorld, x: int, y: int, energy: float = 140.0) -> str:
    if (x, y) in world.occupied:
        raise ValueError("Seed position already occupied")
    node_id = _next_node_id(world)
    node = GrowthNode(node_id=node_id, x=x, y=y, energy=energy)
    world.nodes[node_id] = node
    world.occupied[(x, y)] = node_id
    return node_id


def _neighbors(world: GrowthWorld, node: GrowthNode) -> List[Tuple[int, int]]:
    candidates = [
        (node.x + 1, node.y),
        (node.x - 1, node.y),
        (node.x, node.y + 1),
        (node.x, node.y - 1),
    ]
    return [
        (x, y)
        for (x, y) in candidates
        if 0 <= x < world.width and 0 <= y < world.height
    ]


def detect_contact(world: GrowthWorld, node_id: str) -> bool:
    node = world.nodes[node_id]
    contact = any(position in world.occupied for position in _neighbors(world, node))
    node.contact = contact
    return contact


def inspect_node(world: GrowthWorld, node_id: str) -> Dict[str, object]:
    node = world.nodes[node_id]
    return {
        "node_id": node.node_id,
        "position": (node.x, node.y),
        "energy": node.energy,
        "parent_id": node.parent_id,
        "children": list(node.children),
        "state": node.state.value,
        "contact": node.contact,
    }


def inspect_frontier(world: GrowthWorld) -> List[str]:
    frontier = []
    for node_id, node in world.nodes.items():
        if any(position not in world.occupied for position in _neighbors(world, node)):
            frontier.append(node_id)
    return sorted(frontier)


def calculate_energy(world: GrowthWorld) -> float:
    return round(sum(node.energy for node in world.nodes.values()), 6)


def attempt_spawn(world: GrowthWorld, node_id: str) -> bool:
    node = world.nodes[node_id]
    empties = [position for position in _neighbors(world, node) if position not in world.occupied]
    if not empties:
        node.state = LocalProcessState.RESTRICT
        return False
    if node.energy <= world.energy_threshold:
        node.state = LocalProcessState.SENSE
        return False
    if world.rng.random() >= world.spawn_probability:
        node.state = LocalProcessState.SENSE
        return False
    position = empties[world.rng.randrange(len(empties))]
    child_id = add_seed(world, position[0], position[1], energy=world.spawn_energy_cost)
    child = world.nodes[child_id]
    child.parent_id = node.node_id
    node.children.append(child_id)
    node.energy -= world.spawn_energy_cost
    node.state = LocalProcessState.EXTEND
    return True


def advance_steps(world: GrowthWorld, steps: int = 1) -> Dict[str, object]:
    spawned = 0
    for _ in range(steps):
        world.step_count += 1
        for node_id in list(world.nodes):
            node = world.nodes[node_id]
            empties = [position for position in _neighbors(world, node) if position not in world.occupied]
            contact = any(position in world.occupied for position in _neighbors(world, node))
            node.contact = contact
            node.energy += 3.0
            if not empties:
                node.state = LocalProcessState.RESTRICT
                continue
            if len(empties) >= 2 and node.energy > world.energy_threshold:
                node.state = LocalProcessState.EXTEND
                if attempt_spawn(world, node_id):
                    spawned += 1
                    if empties[0] not in world.occupied and len(empties) > 1:
                        # Bifurcation when energy is abundant and space allows.
                        second_position = empties[1]
                        if second_position not in world.occupied and node.energy > world.spawn_energy_cost:
                            child_id = add_seed(world, second_position[0], second_position[1], energy=world.spawn_energy_cost)
                            world.nodes[child_id].parent_id = node.node_id
                            node.children.append(child_id)
                            node.energy -= world.spawn_energy_cost
                            spawned += 1
            elif contact:
                node.state = LocalProcessState.SENSE
            else:
                node.state = LocalProcessState.EXTEND
    return {
        "step_count": world.step_count,
        "node_count": len(world.nodes),
        "frontier": inspect_frontier(world),
        "spawned": spawned,
        "energy": calculate_energy(world),
    }


def extract_growth_graph(world: GrowthWorld) -> Dict[str, object]:
    return {
        "nodes": {
            node_id: {
                "x": node.x,
                "y": node.y,
                "energy": node.energy,
                "parent_id": node.parent_id,
                "children": list(node.children),
                "state": node.state.value,
            }
            for node_id, node in sorted(world.nodes.items())
        },
        "step_count": world.step_count,
    }


def compare_growth_runs(world_a: GrowthWorld, world_b: GrowthWorld) -> Dict[str, object]:
    return {
        "node_delta": len(world_a.nodes) - len(world_b.nodes),
        "energy_delta": calculate_energy(world_a) - calculate_energy(world_b),
        "frontier_delta": len(inspect_frontier(world_a)) - len(inspect_frontier(world_b)),
        "step_delta": world_a.step_count - world_b.step_count,
    }


def snapshot_growth_world(world: GrowthWorld) -> str:
    payload = pickle.dumps(world, protocol=pickle.HIGHEST_PROTOCOL)
    return base64.b64encode(payload).decode("ascii")


def restore_growth_world(snapshot: str) -> GrowthWorld:
    payload = base64.b64decode(snapshot.encode("ascii"))
    return pickle.loads(payload)


def seeded_three_world(seed: int = 7) -> GrowthWorld:
    world = create_growth_world(seed=seed)
    center_x = world.width // 2
    center_y = world.height // 2
    add_seed(world, center_x - 1, center_y, energy=140.0)
    add_seed(world, center_x, center_y, energy=150.0)
    add_seed(world, center_x + 1, center_y, energy=160.0)
    return world
