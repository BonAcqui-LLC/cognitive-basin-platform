"""Extension Harness — matched A/B comparison runner.

Runs BASELINE (arm A) vs HARNESS_WITH_EXTENSIONS (arm B) with
identical inputs, then compares results for differences.
"""

from __future__ import annotations

import copy
import sys
from typing import Any

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
import natural_math_v5 as nm
from natural_math_v5.randomness import TraceRng

from .runner import Mode, run_local, run_cluster
from .comparison import deep_equal, structured_diff, hash_result


def run_ab_local(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    extensions: list[Any],
    seed: int = 42,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run BASELINE vs HARNESS_WITH_EXTENSIONS for a local step.

    Args:
        nodes: Input node list (deep-copied for each arm).
        params: Parameter dict (deep-copied for each arm).
        extensions: List of extension instances.
        seed: RNG seed for reproducibility. Each arm gets its own TraceRng(seed).
        **kwargs: Passed to run_local (use_deficit, etc.).
    """
    # Pop rng from kwargs if present (we use seed instead for isolation)
    kwargs.pop("rng", None)

    # Arm A: BASELINE
    nodes_a = copy.deepcopy(nodes)
    params_a = copy.deepcopy(params)
    rng_a = TraceRng(seed)
    result_a = run_local(nodes_a, params_a, mode=Mode.BASELINE, rng=rng_a, **kwargs)

    # Arm B: HARNESS_WITH_EXTENSIONS
    nodes_b = copy.deepcopy(nodes)
    params_b = copy.deepcopy(params)
    rng_b = TraceRng(seed)
    result_b = run_local(
        nodes_b, params_b,
        mode=Mode.HARNESS_WITH_EXTENSIONS,
        extensions=extensions,
        rng=rng_b,
        **kwargs,
    )

    comparison = compare_ab_result(result_a, result_b)
    return {
        "arm_a": {"mode": result_a["mode"], "provenance": result_a["provenance"]},
        "arm_b": {"mode": result_b["mode"], "provenance": result_b["provenance"],
                  "hook_events": result_b.get("hook_events", [])},
        "comparison": comparison,
        "arms_equal": comparison.get("equal", False),
    }


def run_ab_cluster(
    seed: int,
    params: dict[str, Any] | None,
    steps: int,
    extensions: list[Any],
) -> dict[str, Any]:
    """Run BASELINE vs HARNESS_WITH_EXTENSIONS for a cluster run.

    Both arms use the same seed. run_cluster internally creates fresh
    TraceRng instances per call, so no state sharing occurs.
    """
    result_a = run_cluster(seed=seed, params=params, steps=steps, mode=Mode.BASELINE)
    result_b = run_cluster(
        seed=seed, params=params, steps=steps,
        mode=Mode.HARNESS_WITH_EXTENSIONS,
        extensions=extensions,
    )
    comparison = compare_ab_result(result_a, result_b)
    return {
        "arm_a": {"mode": result_a["mode"], "provenance": result_a["provenance"]},
        "arm_b": {"mode": result_b["mode"], "provenance": result_b["provenance"],
                  "hook_events": result_b.get("hook_events", [])},
        "comparison": comparison,
        "arms_equal": comparison.get("equal", False),
    }


def compare_ab_result(
    result_a: dict[str, Any],
    result_b: dict[str, Any],
) -> dict[str, Any]:
    """Deep comparison of two harness run results."""
    sim_a = result_a.get("result", result_a)
    sim_b = result_b.get("result", result_b)

    equal = deep_equal(sim_a, sim_b)
    diffs = structured_diff(sim_a, sim_b) if not equal else []
    hash_a = hash_result(sim_a)
    hash_b = hash_result(sim_b)

    return {
        "equal": equal,
        "diffs": diffs,
        "hash_a": hash_a,
        "hash_b": hash_b,
    }
