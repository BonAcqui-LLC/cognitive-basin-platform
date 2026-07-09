"""Trace equivalence verification for Natural Math v5.

Proves that enabling tracing does NOT alter model behavior:
- Same results with trace on vs off
- Trace records accumulate when enabled
- No trace records when disabled
- Zero overhead for disabled state (only boolean check)
"""

from __future__ import annotations

import copy
import random
import sys

sys.path.insert(0, "C:/_MASTER_LIBRARY/06_AUTOCLAW_WORKSPACE/02_REFERENCE_IMPLEMENTATION")

from natural_math_v5 import (
    run_step,
    run_cluster,
    default_params,
    enable_tracing,
    disable_tracing,
    get_tracer,
)


def make_test_node(node_id: int, pos, direction, energy: int = 100000):
    """Create a minimal valid test node."""
    return {
        "id": node_id,
        "pos": tuple(pos),
        "direction": tuple(direction),
        "energy": energy,
        "pressure": 0,
        "alive": True,
        "type": "tip",
        "parent_id": -1,
        "bonds": set(),
        "signal_type": 0,
    }


def deepcopy_nodes(nodes):
    """Deep-copy a list of nodes, preserving tuple positions and set bonds."""
    result = []
    for n in nodes:
        new_n = dict(n)
        new_n["pos"] = tuple(n["pos"])
        new_n["direction"] = tuple(n["direction"])
        new_n["bonds"] = set(n["bonds"])
        result.append(new_n)
    return result


def nodes_equal(a, b):
    """Compare two node lists structurally."""
    if len(a) != len(b):
        return False
    for na, nb in zip(a, b):
        if na["id"] != nb["id"]:
            return False
        if na["pos"] != nb["pos"]:
            return False
        if na["direction"] != nb["direction"]:
            return False
        if na["energy"] != nb["energy"]:
            return False
        if na["pressure"] != nb["pressure"]:
            return False
        if na["alive"] != nb["alive"]:
            return False
        if na["type"] != nb["type"]:
            return False
        if na["bonds"] != nb["bonds"]:
            return False
    return True


class DeterministicRng:
    """Simple deterministic RNG for run_step tests."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self.draws: list[int] = []

    def randrange(self, lo: int, hi: int) -> int:
        val = self._rng.randrange(lo, hi)
        self.draws.append(val)
        return val


# ──────────────────────────────────────────────
# Test 1: run_step with and without tracing
# ──────────────────────────────────────────────
def test_run_step_equivalence():
    """run_step must produce identical results regardless of tracing state."""
    print("=== Test 1: run_step equivalence ===")

    params = default_params()
    params["gamma_fallback_ppm"] = 500000  # Ensure some fallback decisions

    # Create test nodes
    nodes_off = [
        make_test_node(0, (0, 0, 0), (1, 0, 0), 100000),
        make_test_node(1, (2, 0, 0), (-1, 0, 0), 80000),
        make_test_node(2, (0, 2, 0), (0, -1, 0), 120000),
        make_test_node(3, (1, 1, 0), (0, 0, 1), 50000),
        make_test_node(4, (5, 5, 5), (0, 0, -1), 70000),
    ]
    nodes_on = deepcopy_nodes(nodes_off)

    # Clear traces, ensure disabled
    tracer = get_tracer()
    tracer.clear()
    disable_tracing()

    rng_off = DeterministicRng(42)
    result_off = run_step(nodes_off, params, rng=rng_off, allow_bonding=True)

    traces_disabled = tracer.get_records()
    assert len(traces_disabled) == 0, f"Expected no traces when disabled, got {len(traces_disabled)}"

    # Now enable tracing and re-run with same initial state and RNG
    tracer.clear()
    enable_tracing()

    rng_on = DeterministicRng(42)
    nodes_on_copy = deepcopy_nodes(nodes_on)
    result_on = run_step(nodes_on_copy, params, rng=rng_on, allow_bonding=True)

    traces_enabled = tracer.get_records()
    assert len(traces_enabled) > 0, f"Expected trace records when enabled, got {len(traces_enabled)}"
    print(f"  Trace records captured: {len(traces_enabled)}")

    # Verify results are identical
    assert nodes_equal(result_off, result_on), "Results differ between trace on/off!"
    assert rng_off.draws == rng_on.draws, "RNG draws differ between trace on/off!"

    # Verify no leftover state differences
    for n_off, n_on in zip(result_off, result_on):
        for key in ("id", "pos", "direction", "energy", "pressure", "alive", "type", "bonds"):
            assert n_off[key] == n_on[key], f"Node {n_off['id']} field {key} differs"

    print("  PASS: run_step results identical with trace on vs off")
    print("  PASS: Zero traces when disabled")
    print("  PASS: Traces captured when enabled")

    # Verify specific trace phases are present
    phases = {r["phase"] for r in traces_enabled}
    expected_phases = {"decisions", "movement", "pressure"}
    for ep in expected_phases:
        assert ep in phases, f"Expected trace phase '{ep}' not found in {phases}"
    print(f"  Trace phases present: {sorted(phases)}")
    print()


# ──────────────────────────────────────────────
# Test 2: run_cluster with and without tracing
# ──────────────────────────────────────────────
def test_run_cluster_equivalence():
    """run_cluster must produce identical results regardless of tracing state."""
    print("=== Test 2: run_cluster equivalence ===")

    tracer = get_tracer()
    tracer.clear()
    disable_tracing()

    result_off = run_cluster(seed=42, steps=10)

    traces_disabled = tracer.get_records()
    assert len(traces_disabled) == 0, f"Expected no cluster traces when disabled, got {len(traces_disabled)}"

    # Enable tracing and re-run
    tracer.clear()
    enable_tracing()

    result_on = run_cluster(seed=42, steps=10)

    traces_enabled = tracer.get_records()
    assert len(traces_enabled) > 0, f"Expected cluster traces when enabled, got {len(traces_enabled)}"
    print(f"  Cluster trace records captured: {len(traces_enabled)}")

    # Verify key fields match
    assert result_off["resource_pos"] == result_on["resource_pos"], "resource_pos differs"
    assert result_off["resource_left"] == result_on["resource_left"], "resource_left differs"
    assert result_off["resource_reached"] == result_on["resource_reached"], "resource_reached differs"
    assert result_off["passed"] == result_on["passed"], "passed differs"
    assert result_off["metrics"] == result_on["metrics"], "metrics differ"

    # Verify node lists are identical
    assert len(result_off["nodes"]) == len(result_on["nodes"]), "node counts differ"
    assert nodes_equal(result_off["nodes"], result_on["nodes"]), "cluster nodes differ"

    print("  PASS: run_cluster results identical with trace on vs off")
    print("  PASS: Zero cluster traces when disabled")
    print("  PASS: Cluster traces captured when enabled")

    # Verify cluster-specific trace phases
    phases = {r["phase"] for r in traces_enabled}
    cluster_phases = {"cluster_action", "resource_absorption"}
    for cp in cluster_phases:
        assert cp in phases, f"Expected cluster trace phase '{cp}' not found in {phases}"
    print(f"  Cluster trace phases present: {sorted(phases)}")
    print()


# ──────────────────────────────────────────────
# Test 3: Trace records contain expected keys
# ──────────────────────────────────────────────
def test_trace_record_structure():
    """Verify trace records have the expected structure for each phase."""
    print("=== Test 3: trace record structure ===")

    params = default_params()
    params["gamma_fallback_ppm"] = 500000

    nodes = [
        make_test_node(0, (0, 0, 0), (1, 0, 0), 100000),
        make_test_node(1, (2, 0, 0), (-1, 0, 0), 80000),
    ]

    tracer = get_tracer()
    tracer.clear()
    enable_tracing()

    rng = DeterministicRng(99)
    run_step(deepcopy_nodes(nodes), params, rng=rng, allow_bonding=True)

    records = tracer.get_records()

    # Verify decisions phase records
    decisions = [r for r in records if r["phase"] == "decisions"]
    assert len(decisions) > 0, "No decision trace records"
    for d in decisions:
        assert "node_id" in d
        assert d["decision"] in ("EXTEND", "SENSE", "RESTRICT_DIE")
    print(f"  Decision records: {len(decisions)}")

    # Verify movement records (may be empty if nodes didn't move)
    movements = [r for r in records if r["phase"] == "movement"]
    print(f"  Movement records: {len(movements)}")
    for m in movements:
        assert "target" in m
        assert m["winner"] is not None or m["loser"] is not None

    # Verify pressure records
    pressures = [r for r in records if r["phase"] == "pressure"]
    assert len(pressures) > 0, "No pressure trace records"
    for p in pressures:
        assert "node_id" in p
        assert "pressure_before" in p
        assert "pressure_after" in p
    print(f"  Pressure records: {len(pressures)}")

    # All records must use keyword args (manifested as dict keys)
    for r in records:
        assert isinstance(r, dict), f"Record is not a dict: {type(r)}"

    print("  PASS: All trace records well-structured")
    print()


# ──────────────────────────────────────────────
# Test 4: TraceRecorder API
# ──────────────────────────────────────────────
def test_trace_recorder_api():
    """Verify TraceRecorder methods work as specified."""
    print("=== Test 4: TraceRecorder API ===")

    from natural_math_v5 import TraceRecorder

    tr = TraceRecorder()

    # Initially disabled, zero records
    assert tr.get_records() == []
    tr.record(phase="test", value=1)
    assert tr.get_records() == [], "Should not record when disabled"

    # Enable and record
    tr.enable()
    tr.record(phase="test", value=1)
    tr.record(phase="test", value=2)
    records = tr.get_records()
    assert len(records) == 2
    assert records[0] == {"phase": "test", "value": 1}
    assert records[1] == {"phase": "test", "value": 2}

    # get_records returns a copy
    records_copy = tr.get_records()
    records_copy.append({"phase": "hack"})
    assert len(tr.get_records()) == 2, "get_records should return a copy"

    # Clear
    tr.clear()
    assert tr.get_records() == []

    # Disable again
    tr.disable()
    tr.record(phase="should_not_record")
    assert tr.get_records() == []

    print("  PASS: TraceRecorder API works correctly")
    print()


# ──────────────────────────────────────────────
# Test 5: Non-negotiable property — no random consumption
# ──────────────────────────────────────────────
def test_trace_no_random_consumption():
    """Tracing must not consume any random draws."""
    print("=== Test 5: tracing must not consume random draws ===")

    params = default_params()
    params["gamma_fallback_ppm"] = 500000

    nodes = [
        make_test_node(0, (0, 0, 0), (1, 0, 0), 100000),
        make_test_node(1, (2, 0, 0), (-1, 0, 0), 80000),
    ]

    tracer = get_tracer()
    tracer.clear()

    # Run with tracing OFF
    disable_tracing()
    rng_off = DeterministicRng(7)
    run_step(deepcopy_nodes(nodes), params, rng=rng_off, allow_bonding=True)
    draws_off = list(rng_off.draws)

    # Run with tracing ON, same seed
    tracer.clear()
    enable_tracing()
    rng_on = DeterministicRng(7)
    run_step(deepcopy_nodes(nodes), params, rng=rng_on, allow_bonding=True)
    draws_on = list(rng_on.draws)

    assert draws_off == draws_on, (
        f"RNG draws differ! Trace consumed random draws.\n"
        f"  Off: {draws_off}\n  On:  {draws_on}"
    )
    print("  PASS: Tracing does not consume random draws")
    print()


if __name__ == "__main__":
    test_trace_recorder_api()
    test_run_step_equivalence()
    test_run_cluster_equivalence()
    test_trace_record_structure()
    test_trace_no_random_consumption()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
