from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict
import random

import numpy as np

from .decisions import decide
from .energy import total_active_energy
from .invariants import validate_state
from .lattice import bifurcation_children, quadrance
from .presets import default_params
from .state import NodeState, SimulationState


class NaturalMathSimulator:
    """Canonical local-first Natural Math simulator for the workspace."""

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


# Backward-compatible alias matching earlier external scripts.
NaturalMathPopSim = NaturalMathSimulator
