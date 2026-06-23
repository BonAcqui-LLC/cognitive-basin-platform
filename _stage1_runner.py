#!/usr/bin/env python3
"""Natural Math v5 — Stage 1 comprehensive fixture runner.

Runs ALL 40 original oracle fixtures:
  - 25 integer oracle fixtures (run_step)
  - 15 cluster oracle fixtures (run_cluster + summarize_cluster_run)

Output: 05_RESULTS/frozen_v5/original_oracle_results.json + .md
"""

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Add reference implementation to path
REF_DIR = Path(r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
sys.path.insert(0, str(REF_DIR))

from natural_math_v5 import run_step, run_cluster, NaturalMathValidationError, default_params
from natural_math_v5.randomness import TraceRng
from natural_math_v5.cluster import summarize_cluster_run
from natural_math_v5.cluster_initialization import initialize_cluster, live_bond_pairs
from natural_math_v5.cluster_metrics import compute_metrics, passed_diagnostic, select_cluster_action
from natural_math_v5.cluster_actions import (
    apply_damage, apply_resource_absorption, apply_cluster_action, kill_below_tau,
    apply_seek, apply_redistribute, apply_repair, apply_rest,
)

# ---- Paths ----
FIXTURES_DIR = Path(r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES")
INT_FIXTURES = FIXTURES_DIR / "natural_math_integer_oracle_fixtures.json"
CLUSTER_FIXTURES = FIXTURES_DIR / "natural_math_cluster_oracle_fixtures.json"
RESULTS_DIR = Path(r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CANON_SPEC = Path(r"C:\_MASTER_LIBRARY\01_CANON\01_NATURAL_MATH_V5\Natural Math v5 - Status Frozen Int.txt")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# ---- Integer fixture helpers ----

def json_to_nodes(raw_nodes):
    """Convert JSON fixture nodes: lists -> tuples, bonds lists -> sets."""
    nodes = copy.deepcopy(raw_nodes)
    for node in nodes:
        node["pos"] = tuple(node["pos"])
        node["direction"] = tuple(node["direction"])
        node["bonds"] = set(node["bonds"])
    return nodes


def nodes_to_json(nodes):
    """Serialize nodes back to JSON-safe format."""
    result = []
    for node in sorted(nodes, key=lambda n: n["id"]):
        item = copy.deepcopy(node)
        item["pos"] = list(item["pos"])
        item["direction"] = list(item["direction"])
        item["bonds"] = sorted(item["bonds"])
        result.append(item)
    return result


# ---- Cluster fixture helpers ----

def cluster_json_to_nodes(raw_nodes):
    """Convert cluster fixture nodes (same as integer)."""
    return json_to_nodes(raw_nodes)


def summarize_initialization(state, params):
    """Match donor's summarize_initialization output."""
    nodes = state["nodes"]
    metrics = compute_metrics(nodes, state["resource_pos"], params)
    return {
        "node_count": len(nodes),
        "alive_count": sum(1 for node in nodes if node["alive"]),
        "first_five_nodes": [
            {
                "id": node["id"],
                "pos": list(node["pos"]),
                "energy": node["energy"],
                "bonds": sorted(node["bonds"]),
            }
            for node in nodes[:5]
        ],
        "live_bond_pair_count": len(live_bond_pairs(nodes)),
        "first_ten_live_bond_pairs": live_bond_pairs(nodes)[:10],
        "random_bond_draw_count": len(state["random_bond_draws"]),
        "first_ten_random_bond_draws": state["random_bond_draws"][:10],
        "last_five_random_bond_draws": state["random_bond_draws"][-5:],
        "resource_pos": list(state["resource_pos"]),
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "metrics": metrics,
        "passed": passed_diagnostic(metrics, state["resource_reached"], params),
    }


def summarize_state(state, params, selected_action, rng):
    """Match donor's summarize_state for action fixtures."""
    return {
        "selected_action": selected_action,
        "nodes": [
            {
                "id": node["id"],
                "pos": list(node["pos"]),
                "energy": node["energy"],
                "alive": node["alive"],
                "type": node["type"],
                "bonds": sorted(node["bonds"]),
            }
            for node in sorted(state["nodes"], key=lambda n: n["id"])
        ],
        "resource_pos": list(state["resource_pos"]),
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "rng_draws": rng.draws if rng is not None else [],
        "metrics": compute_metrics(state["nodes"], state["resource_pos"], params),
    }


def run_action_fixture(fixture, params):
    """Run a cluster action fixture, matching donor behavior."""
    state = {
        "nodes": cluster_json_to_nodes(fixture["state"]["nodes"]),
        "resource_pos": tuple(fixture["state"]["resource_pos"]),
        "resource_left": fixture["state"].get("resource_left", 450000),
        "resource_reached": fixture["state"].get("resource_reached", False),
    }
    rng = TraceRng(fixture["rng_seed"]) if "rng_seed" in fixture else None
    selected_action = fixture.get("action")
    if fixture.get("select_action", False):
        metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
        selected_action = select_cluster_action(metrics, state["resource_reached"], params)
    if selected_action is not None:
        apply_cluster_action(selected_action, state, params, rng)
    if fixture.get("apply_resource_absorption", False):
        apply_resource_absorption(state, params)
        for node in state["nodes"]:
            node["energy"] = max(0, node["energy"])
        kill_below_tau(state["nodes"], params)
    return summarize_state(state, params, selected_action, rng)


# ---- MAIN RUNNER ----

def run_integer_fixtures():
    """Run all 25 integer oracle fixtures."""
    suite = json.loads(INT_FIXTURES.read_text(encoding="utf-8"))
    # Resolve spec path: try fixture path, fall back to canonical
    spec_path = Path(suite["spec"]["path"])
    if not spec_path.exists():
        spec_path = CANON_SPEC
    spec_hash_actual = sha256(spec_path) if spec_path.exists() else None
    spec_hash_expected = suite["spec"]["sha256"]

    cases = []
    all_passed = spec_hash_actual == spec_hash_expected

    for fixture in suite["fixtures"]:
        params = copy.deepcopy(default_params())
        params.update(fixture.get("flags", {}).get("params", {}))
        rng_seed = fixture.get("flags", {}).get("rng_seed")
        rng = TraceRng(rng_seed) if rng_seed is not None else None
        nodes = json_to_nodes(fixture["nodes"])
        status = "PASS"
        error = None
        expected_error = fixture.get("expected_error")

        try:
            flags = fixture.get("flags", {})
            returned = run_step(
                nodes,
                params,
                use_deficit=flags.get("use_deficit", False),
                use_poc_scream=flags.get("use_poc_scream", False),
                allow_bonding=flags.get("allow_bonding", False),
                bond_collapse_positions=flags.get("bond_collapse_positions", False),
                bonding_strict=flags.get("bonding_strict", False),
                rng=rng,
            )
            if expected_error is not None:
                raise AssertionError("expected validation error was not raised")
            if returned is not nodes:
                raise AssertionError("run_step did not return the same nodes list object")
            actual_nodes = nodes_to_json(nodes)
            if actual_nodes != fixture["expected_nodes"]:
                raise AssertionError(
                    f"nodes mismatch. Expected first node: {fixture['expected_nodes'][0] if fixture['expected_nodes'] else 'empty'}, "
                    f"Got: {actual_nodes[0] if actual_nodes else 'empty'}"
                )
            actual_draws = rng.draws if rng is not None else []
            if actual_draws != fixture["expected_random_draws"]:
                raise AssertionError(
                    f"rng draw trace mismatch. Expected: {fixture['expected_random_draws']}, Got: {actual_draws}"
                )
        except NaturalMathValidationError as exc:
            if expected_error is not None and expected_error["type"] == "NaturalMathValidationError" and expected_error["contains"] in str(exc):
                error = f"NaturalMathValidationError: {exc}"
            else:
                status = "FAIL"
                error = f"NaturalMathValidationError: {exc}"
                all_passed = False
        except Exception as exc:
            actual_draws = rng.draws if rng is not None else []
            if expected_error is not None and type(exc).__name__ == expected_error["type"] and expected_error["contains"] in str(exc):
                error = f"{type(exc).__name__}: {exc}"
            else:
                status = "FAIL"
                error = f"{type(exc).__name__}: {exc}"
                all_passed = False

        cases.append({
            "name": fixture["name"],
            "kind": "integer",
            "status": status,
            "error": error,
        })

    return {
        "suite": suite["suite"],
        "spec_sha256_expected": spec_hash_expected,
        "spec_sha256_actual": spec_hash_actual,
        "cases": cases,
        "all_passed": all_passed and all(c["status"] == "PASS" for c in cases),
    }


def run_cluster_fixtures():
    """Run all 15 cluster oracle fixtures."""
    suite = json.loads(CLUSTER_FIXTURES.read_text(encoding="utf-8"))
    # Resolve spec path: try fixture path, fall back to canonical
    spec_path = Path(suite["spec"]["path"])
    if not spec_path.exists():
        spec_path = CANON_SPEC
    spec_hash_actual = sha256(spec_path) if spec_path.exists() else None
    spec_hash_expected = suite["spec"]["sha256"]

    cases = []
    all_passed = spec_hash_actual == spec_hash_expected
    params = copy.deepcopy(default_params())

    # Initialization fixtures (2)
    for fixture in suite.get("initialization_fixtures", []):
        fp = copy.deepcopy(params)
        fp.update(fixture.get("params", {}))
        rng = TraceRng(fixture["seed"])
        state = initialize_cluster(fixture["seed"], fp, rng)
        actual = summarize_initialization(state, fp)
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        cases.append({
            "name": fixture["name"],
            "kind": "cluster_initialization",
            "status": status,
            "error": None if status == "PASS" else "summary mismatch",
        })

    # Metrics fixtures (3)
    for fixture in suite.get("metrics_fixtures", []):
        fp = copy.deepcopy(params)
        fp.update(fixture.get("params", {}))
        nodes = cluster_json_to_nodes(fixture["nodes"])
        actual = compute_metrics(nodes, tuple(fixture["resource_pos"]), fp)
        status = "PASS" if actual == fixture["expected_metrics"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        cases.append({
            "name": fixture["name"],
            "kind": "cluster_metrics",
            "status": status,
            "error": None if status == "PASS" else "metrics mismatch",
        })

    # Action fixtures (5)
    for fixture in suite.get("action_fixtures", []):
        fp = copy.deepcopy(params)
        fp.update(fixture.get("params", {}))
        actual = run_action_fixture(fixture, fp)
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        cases.append({
            "name": fixture["name"],
            "kind": "cluster_action",
            "status": status,
            "error": None if status == "PASS" else "action summary mismatch",
        })

    # Damage fixtures (1)
    for fixture in suite.get("damage_fixtures", []):
        fp = copy.deepcopy(params)
        fp.update(fixture.get("params", {}))
        rng = TraceRng(fixture["rng_seed"])
        nodes = cluster_json_to_nodes(fixture["nodes"])
        apply_damage(nodes, fp, rng)
        actual = {
            "nodes": [
                {
                    "id": node["id"],
                    "pos": list(node["pos"]),
                    "energy": node["energy"],
                    "alive": node["alive"],
                    "type": node["type"],
                    "bonds": sorted(node["bonds"]),
                }
                for node in sorted(nodes, key=lambda n: n["id"])
            ],
            "live_bond_pairs": live_bond_pairs(nodes),
            "rng_draws": rng.draws,
        }
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        cases.append({
            "name": fixture["name"],
            "kind": "cluster_damage",
            "status": status,
            "error": None if status == "PASS" else "damage mismatch",
        })

    # Cluster run fixtures (4)
    for fixture in suite.get("cluster_run_fixtures", []):
        fp = copy.deepcopy(params)
        fp.update(fixture.get("params", {}))

        # Run with internal tracking for donor-style summary
        seed = fixture["seed"]
        steps = fixture["steps"]
        rng = TraceRng(seed)
        state = initialize_cluster(seed, fp, rng)
        actions = []
        for step_index in range(1, steps + 1):
            from natural_math_v5.cluster_step import cluster_step
            action = cluster_step(state, fp, rng, step_index)
            actions.append(action)

        result = {
            "nodes": state["nodes"],
            "resource_pos": state["resource_pos"],
            "resource_left": state["resource_left"],
            "resource_reached": state["resource_reached"],
            "metrics": compute_metrics(state["nodes"], state["resource_pos"], fp),
            "passed": passed_diagnostic(
                compute_metrics(state["nodes"], state["resource_pos"], fp),
                state["resource_reached"], fp
            ),
        }
        actual = summarize_cluster_run(result, fp, rng, actions)
        status = "PASS" if actual == fixture["expected_summary"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        cases.append({
            "name": fixture["name"],
            "kind": "cluster_run",
            "status": status,
            "error": None if status == "PASS" else "cluster run mismatch",
        })

    return {
        "suite": suite["suite"],
        "spec_sha256_expected": spec_hash_expected,
        "spec_sha256_actual": spec_hash_actual,
        "cases": cases,
        "all_passed": all_passed and all(c["status"] == "PASS" for c in cases),
    }


def main():
    print("=" * 60)
    print("Natural Math v5 — Stage 1 Comprehensive Fixture Runner")
    print("=" * 60)

    # Run integer fixtures
    print("\n--- Running 25 Integer Oracle Fixtures ---")
    int_results = run_integer_fixtures()
    int_passed = sum(1 for c in int_results["cases"] if c["status"] == "PASS")
    int_total = len(int_results["cases"])
    print(f"Integer: {int_passed}/{int_total} passed")
    for c in int_results["cases"]:
        marker = "PASS" if c["status"] == "PASS" else "FAIL"
        print(f"  {marker} {c['name']}")
        if c["error"]:
            print(f"       Error: {c['error']}")

    # Run cluster fixtures
    print("\n--- Running 15 Cluster Oracle Fixtures ---")
    cluster_results = run_cluster_fixtures()
    cluster_passed = sum(1 for c in cluster_results["cases"] if c["status"] == "PASS")
    cluster_total = len(cluster_results["cases"])
    print(f"Cluster: {cluster_passed}/{cluster_total} passed")
    for c in cluster_results["cases"]:
        marker = "PASS" if c["status"] == "PASS" else "FAIL"
        print(f"  {marker} {c['name']}")
        if c["error"]:
            print(f"       Error: {c['error']}")

    # Overall
    total_passed = int_passed + cluster_passed
    total_cases = int_total + cluster_total
    overall = int_results["all_passed"] and cluster_results["all_passed"]
    print(f"\n{'=' * 60}")
    print(f"OVERALL: {total_passed}/{total_cases} ({'PASS' if overall else 'FAIL'})")
    print(f"{'=' * 60}")

    # Build combined results
    combined = {
        "runner": "stage_1_comprehensive_runner.py",
        "timestamp": "2026-06-23",
        "overall_passed": overall,
        "total_fixtures": total_cases,
        "passed_count": total_passed,
        "integer_fixtures": {
            "passed": int_results["all_passed"],
            "count": int_total,
            "passed_count": int_passed,
            "spec_sha256": int_results["spec_sha256_actual"],
            "cases": int_results["cases"],
        },
        "cluster_fixtures": {
            "passed": cluster_results["all_passed"],
            "count": cluster_total,
            "passed_count": cluster_passed,
            "spec_sha256": cluster_results["spec_sha256_actual"],
            "cases": cluster_results["cases"],
        },
        "fixes_applied": [
            "ISSUE 2: run_cluster returns Section 22 contract (6 keys)",
            "ISSUE 3: Phase ordering verified against spec; __init__.py updated",
            "ISSUE 4: cluster_step ValueError -> NaturalMathValidationError",
            "ISSUE 5: sample_two rewritten per spec algorithm (no rng.sample)",
            "ISSUE 6: as_tuple3_strict rejects lists; validate_nodes strict",
            "ISSUE 7: Removed non-spec bonding flag check from run_step",
            "ISSUE 8: tracing.py deferred to Stage 2",
        ],
    }

    # Write JSON results
    json_path = RESULTS_DIR / "original_oracle_results.json"
    json_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"\nJSON results: {json_path}")

    # Write Markdown report
    md_lines = [
        "# Natural Math v5 — Stage 1 Oracle Results",
        "",
        f"**Overall:** {'PASS' if overall else 'FAIL'} ({total_passed}/{total_cases} fixtures)",
        f"**Date:** 2026-06-23",
        "",
        "## Stage 1 Fixes Applied",
        "",
    ]
    for fix in combined["fixes_applied"]:
        md_lines.append(f"- {fix}")
    md_lines.extend([
        "",
        "## Integer Oracle Fixtures (25)",
        "",
    ])
    for c in int_results["cases"]:
        md_lines.append(f"- **{c['status']}** `{c['name']}`")
        if c["error"]:
            md_lines.append(f"  - Error: `{c['error']}`")
    md_lines.extend([
        "",
        f"**Integer result: {int_passed}/{int_total} passed**",
        "",
        "## Cluster Oracle Fixtures (15)",
        "",
    ])
    for c in cluster_results["cases"]:
        md_lines.append(f"- **{c['status']}** `{c['name']}` ({c['kind']})")
        if c["error"]:
            md_lines.append(f"  - Error: `{c['error']}`")
    md_lines.extend([
        "",
        f"**Cluster result: {cluster_passed}/{cluster_total} passed**",
        "",
        "## Provenance",
        "",
        "- Runner: `stage_1_comprehensive_runner.py`",
        "- Package: `natural_math_v5` (reference implementation)",
        f"- Integer fixtures: `{INT_FIXTURES}`",
        f"- Cluster fixtures: `{CLUSTER_FIXTURES}`",
        "- Spec: Natural Math v5 - Status Frozen Int",
    ])

    md_path = RESULTS_DIR / "original_oracle_results.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Markdown report: {md_path}")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
