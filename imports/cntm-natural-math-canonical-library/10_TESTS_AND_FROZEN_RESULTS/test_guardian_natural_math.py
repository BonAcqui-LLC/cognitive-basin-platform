"""Tests for Guardian/HOLD Natural Math integration."""

from __future__ import annotations

import json
from pathlib import Path

from fractalish_ai.mcva.gate import MCVAGate
from fractalish_ai.natural_math.experimental_guardian_hold import (
    GuardianNaturalMath,
    maze_to_setup,
    run_vanilla,
)
from fractalish_ai.natural_math.v3_6_core import CoreParams

REPO = Path(__file__).resolve().parents[1]


def test_mcva_gate_evaluate_returns_status() -> None:
    gate = MCVAGate()
    result = gate.evaluate({"name": "irregular_boundary", "grid": [[0, 1], [0, 1]]})
    assert result["status"] in {"MCVA", "HOLD", "AMCVA"}
    assert "uncertainty" in result
    assert gate.evaluation_count == 1


def test_guardian_reduces_collisions_on_ambiguous_maze() -> None:
    maze_path = REPO / "mazes" / "ambiguous" / "conflicting_paths.json"
    maze = json.loads(maze_path.read_text(encoding="utf-8"))
    params = CoreParams(seed=42, gamma_fallback=0.35)

    nodes_v, next_v, walls, target = maze_to_setup(maze, params)
    _, vanilla = run_vanilla(nodes_v, next_v, params, max_steps=80, walls=walls, target=target)

    nodes_g, next_g, _, _ = maze_to_setup(maze, params)
    engine = GuardianNaturalMath(
        params, MCVAGate(), hold_threshold=0.5, walls=walls, maze_name=maze["name"]
    )
    _, guarded = engine.run_with_guardian(nodes_g, next_g, max_steps=80, target=target)

    assert vanilla["conflict_count"] > guarded["conflict_count"]
    assert guarded["hold_overrides"] > 0
    assert guarded["mcva_evaluations"] > 0


def test_simple_maze_unaffected_by_guardian() -> None:
    maze_path = REPO / "mazes" / "simple.json"
    maze = json.loads(maze_path.read_text(encoding="utf-8"))
    params = CoreParams(seed=42, gamma_fallback=0.35)

    nodes_v, next_v, walls, target = maze_to_setup(maze, params)
    _, vanilla = run_vanilla(nodes_v, next_v, params, max_steps=50, walls=walls, target=target)

    nodes_g, next_g, _, _ = maze_to_setup(maze, params)
    engine = GuardianNaturalMath(
        params, MCVAGate(), hold_threshold=0.5, walls=walls, maze_name=maze["name"]
    )
    _, guarded = engine.run_with_guardian(nodes_g, next_g, max_steps=50, target=target)

    assert vanilla["reached_target"] is True
    assert guarded["reached_target"] is True
    assert guarded["hold_overrides"] == 0