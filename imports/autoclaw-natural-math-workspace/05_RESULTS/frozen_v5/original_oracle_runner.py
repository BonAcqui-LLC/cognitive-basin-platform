"""
Stage 1.1 Oracle Runner — runs ALL 40 frozen Natural Math v5 oracle fixtures
against the clean package at 02_REFERENCE_IMPLEMENTATION/natural_math_v5.

Uses exec/PowerShell for file writes (no direct write tool).
"""

import copy
import json
import sys
from datetime import datetime

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")

from natural_math_v5.core_step import run_step
from natural_math_v5.randomness import TraceRng
from natural_math_v5.parameters import default_params, DEFAULT_PARAMS
from natural_math_v5.errors import NaturalMathValidationError
from natural_math_v5.cluster_initialization import initialize_cluster, live_bond_pairs
from natural_math_v5.cluster_metrics import compute_metrics, passed_diagnostic, select_cluster_action, connected_components
from natural_math_v5.cluster_actions import (
    kill_below_tau, apply_seek, apply_redistribute, apply_repair, apply_rest,
    apply_resource_absorption, apply_damage, apply_cluster_action,
)
from natural_math_v5.cluster_step import cluster_step
from natural_math_v5.cluster import summarize_cluster_run

# ── Paths ──────────────────────────────────────────────────────────────
INTEGER_FIXTURES_PATH = r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_integer_oracle_fixtures.json"
CLUSTER_FIXTURES_PATH = r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_cluster_oracle_fixtures.json"
OUTPUT_DIR = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5"


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS: Convert between JSON (list) and internal (tuple/set) formats
# ═══════════════════════════════════════════════════════════════════════════

def json_node_to_internal(node):
    """Deep-copy JSON node, convert pos/direction to tuple, bonds to set."""
    n = copy.deepcopy(node)
    n["pos"] = tuple(n["pos"])
    n["direction"] = tuple(n["direction"])
    n["bonds"] = set(n["bonds"])
    return n

def internal_node_to_json(node):
    """Convert internal node back to JSON-comparable format."""
    return {
        "id": node["id"],
        "pos": list(node["pos"]),
        "direction": list(node["direction"]),
        "energy": node["energy"],
        "pressure": node["pressure"],
        "alive": node["alive"],
        "type": node["type"],
        "parent_id": node["parent_id"],
        "bonds": sorted(node["bonds"]),
        "signal_type": node["signal_type"],
    }

def internal_nodes_to_json(nodes):
    return [internal_node_to_json(n) for n in nodes]


# ═══════════════════════════════════════════════════════════════════════════
# PART 1: Integer Fixtures (25 fixtures)
# ═══════════════════════════════════════════════════════════════════════════

def run_integer_fixtures(fixtures_data):
    """Run all 25 integer fixtures. Returns list of case result dicts."""
    results = []
    defaults = DEFAULT_PARAMS
    base_override = fixtures_data.get("defaults_override", {})

    for idx, fixture in enumerate(fixtures_data["fixtures"]):
        name = fixture["name"]
        flags = fixture.get("flags", {})

        # Build params
        params = copy.deepcopy(defaults)
        params.update(base_override)
        if "params" in flags:
            params.update(flags["params"])

        # Convert nodes
        nodes = [json_node_to_internal(n) for n in fixture["nodes"]]

        # Set up flags
        kwargs = {}
        if "use_deficit" in flags:
            kwargs["use_deficit"] = flags["use_deficit"]
        if "use_poc_scream" in flags:
            kwargs["use_poc_scream"] = flags["use_poc_scream"]
        if "allow_bonding" in flags:
            kwargs["allow_bonding"] = flags["allow_bonding"]
        if "bond_collapse_positions" in flags:
            kwargs["bond_collapse_positions"] = flags["bond_collapse_positions"]
        if "bonding_strict" in flags:
            kwargs["bonding_strict"] = flags["bonding_strict"]

        # Create RNG if seeded
        rng = None
        if "rng_seed" in flags:
            rng = TraceRng(flags["rng_seed"])

        # Run fixture
        status = "PASS"
        error_detail = ""
        actual_nodes = None
        actual_draws = []

        try:
            result_nodes = run_step(nodes, params, rng=rng, **kwargs)
            actual_nodes = internal_nodes_to_json(result_nodes)
            actual_draws = rng.draws if rng else []

            # Compare nodes
            expected_nodes = fixture.get("expected_nodes", [])
            if actual_nodes != expected_nodes:
                status = "FAIL"
                error_detail = "node mismatch"

            # Compare draws
            expected_draws = fixture.get("expected_random_draws", [])
            if actual_draws != expected_draws:
                status = "FAIL"
                if error_detail:
                    error_detail += "; draw mismatch"
                else:
                    error_detail = "draw mismatch"

            # Check expected error
            expected_error = fixture.get("expected_error")
            if expected_error:
                status = "FAIL"
                if error_detail:
                    error_detail += "; expected error not raised"
                else:
                    error_detail = "expected error not raised"

        except NaturalMathValidationError as e:
            expected_error = fixture.get("expected_error")
            if expected_error:
                error_type_ok = expected_error["type"] == "NaturalMathValidationError"
                contains_ok = expected_error["contains"] in str(e)
                if error_type_ok and contains_ok:
                    status = "PASS"
                    error_detail = ""
                else:
                    status = "FAIL"
                    error_detail = f"error mismatch: got '{str(e)}', expected contains '{expected_error['contains']}'"
            else:
                status = "FAIL"
                error_detail = f"unexpected NaturalMathValidationError: {str(e)}"
        except Exception as e:
            status = "FAIL"
            error_detail = f"exception: {type(e).__name__}: {str(e)}"

        results.append({
            "category": "integer",
            "fixture_index": idx,
            "fixture_name": name,
            "status": status,
            "error_detail": error_detail,
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# PART 2: Cluster Fixtures (15 fixtures)
# ═══════════════════════════════════════════════════════════════════════════

def summarize_init_state(state, params):
    """Summarize initialization state for fixture comparison."""
    nodes = state["nodes"]
    metrics = compute_metrics(nodes, state["resource_pos"], params)
    return {
        "node_count": len(nodes),
        "alive_count": sum(1 for n in nodes if n["alive"]),
        "first_five_nodes": [
            {"id": n["id"], "pos": list(n["pos"]), "energy": n["energy"], "bonds": sorted(n["bonds"])}
            for n in nodes[:5]
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


def summarize_action_state(state, params, selected_action, rng):
    """Summarize action fixture result for comparison."""
    return {
        "selected_action": selected_action,
        "nodes": [
            {"id": n["id"], "pos": list(n["pos"]), "energy": n["energy"],
             "alive": n["alive"], "type": n["type"], "bonds": sorted(n["bonds"])}
            for n in sorted(state["nodes"], key=lambda x: x["id"])
        ],
        "resource_pos": list(state["resource_pos"]),
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "rng_draws": rng.draws if rng is not None else [],
        "metrics": compute_metrics(state["nodes"], state["resource_pos"], params),
    }


def run_cluster_fixtures(fixtures_data):
    """Run all 15 cluster fixtures. Returns list of case result dicts."""
    results = []
    params_default = DEFAULT_PARAMS

    # ── Initialization fixtures (2) ──
    for idx, fixture in enumerate(fixtures_data.get("initialization_fixtures", [])):
        name = fixture["name"]
        seed = fixture["seed"]
        fparams = copy.deepcopy(params_default)
        fparams.update(fixture.get("params", {}))

        try:
            rng = TraceRng(seed)
            state = initialize_cluster(seed, fparams, rng)
            actual = summarize_init_state(state, fparams)
            expected = fixture["expected_summary"]
            status = "PASS" if actual == expected else "FAIL"
            error_detail = "" if status == "PASS" else "summary mismatch"
        except Exception as e:
            status = "FAIL"
            error_detail = f"{type(e).__name__}: {str(e)}"
            actual = None

        results.append({
            "category": "cluster_initialization",
            "fixture_index": idx,
            "fixture_name": name,
            "status": status,
            "error_detail": error_detail,
            "actual": actual,
        })

    # ── Metrics fixtures (3) ──
    for idx, fixture in enumerate(fixtures_data.get("metrics_fixtures", [])):
        name = fixture["name"]
        fparams = copy.deepcopy(params_default)
        fparams.update(fixture.get("params", {}))
        resource_pos = tuple(fixture["resource_pos"])

        try:
            nodes = [json_node_to_internal(n) for n in fixture["nodes"]]
            actual = compute_metrics(nodes, resource_pos, fparams)
            expected = fixture["expected_metrics"]
            status = "PASS" if actual == expected else "FAIL"
            error_detail = "" if status == "PASS" else "metrics mismatch"
        except Exception as e:
            status = "FAIL"
            error_detail = f"{type(e).__name__}: {str(e)}"
            actual = None

        results.append({
            "category": "cluster_metrics",
            "fixture_index": idx,
            "fixture_name": name,
            "status": status,
            "error_detail": error_detail,
            "actual": actual,
        })

    # ── Action fixtures (5) ──
    for idx, fixture in enumerate(fixtures_data.get("action_fixtures", [])):
        name = fixture["name"]
        fparams = copy.deepcopy(params_default)
        fparams.update(fixture.get("params", {}))

        try:
            state = {
                "nodes": [json_node_to_internal(n) for n in fixture["state"]["nodes"]],
                "resource_pos": tuple(fixture["state"]["resource_pos"]),
                "resource_left": fixture["state"].get("resource_left", 450000),
                "resource_reached": fixture["state"].get("resource_reached", False),
            }

            rng = TraceRng(fixture["rng_seed"]) if "rng_seed" in fixture else None
            selected_action = fixture.get("action")

            if fixture.get("select_action", False):
                metrics = compute_metrics(state["nodes"], state["resource_pos"], fparams)
                selected_action = select_cluster_action(metrics, state["resource_reached"], fparams)

            if selected_action is not None:
                apply_cluster_action(selected_action, state, fparams, rng)

            if fixture.get("apply_resource_absorption", False):
                apply_resource_absorption(state, fparams)
                for n in state["nodes"]:
                    n["energy"] = max(0, n["energy"])
                kill_below_tau(state["nodes"], fparams)

            actual = summarize_action_state(state, fparams, selected_action, rng)
            expected = fixture["expected_summary"]
            status = "PASS" if actual == expected else "FAIL"
            error_detail = "" if status == "PASS" else "summary mismatch"
        except Exception as e:
            status = "FAIL"
            error_detail = f"{type(e).__name__}: {str(e)}"
            actual = None

        results.append({
            "category": "cluster_action",
            "fixture_index": idx,
            "fixture_name": name,
            "status": status,
            "error_detail": error_detail,
            "actual": actual,
        })

    # ── Damage fixtures (1) ──
    for idx, fixture in enumerate(fixtures_data.get("damage_fixtures", [])):
        name = fixture["name"]
        fparams = copy.deepcopy(params_default)
        fparams.update(fixture.get("params", {}))

        try:
            rng = TraceRng(fixture["rng_seed"])
            nodes = [json_node_to_internal(n) for n in fixture["nodes"]]
            apply_damage(nodes, fparams, rng)

            actual = {
                "nodes": [
                    {"id": n["id"], "pos": list(n["pos"]), "energy": n["energy"],
                     "alive": n["alive"], "type": n["type"], "bonds": sorted(n["bonds"])}
                    for n in sorted(nodes, key=lambda x: x["id"])
                ],
                "live_bond_pairs": live_bond_pairs(nodes),
                "rng_draws": rng.draws,
            }
            expected = fixture["expected_summary"]
            status = "PASS" if actual == expected else "FAIL"
            error_detail = "" if status == "PASS" else "summary mismatch"
        except Exception as e:
            status = "FAIL"
            error_detail = f"{type(e).__name__}: {str(e)}"
            actual = None

        results.append({
            "category": "cluster_damage",
            "fixture_index": idx,
            "fixture_name": name,
            "status": status,
            "error_detail": error_detail,
            "actual": actual,
        })

    # ── Cluster run fixtures (4) ──
    for idx, fixture in enumerate(fixtures_data.get("cluster_run_fixtures", [])):
        name = fixture["name"]
        seed = fixture["seed"]
        steps = fixture["steps"]
        fparams = copy.deepcopy(params_default)
        fparams.update(fixture.get("params", {}))

        try:
            rng = TraceRng(seed)
            state = initialize_cluster(seed, fparams, rng)
            actions = []
            for step_index in range(1, steps + 1):
                action = cluster_step(state, fparams, rng, step_index)
                actions.append(action)

            actual = summarize_cluster_run(
                {
                    "nodes": state["nodes"],
                    "resource_pos": state["resource_pos"],
                    "resource_left": state["resource_left"],
                    "resource_reached": state["resource_reached"],
                    "metrics": compute_metrics(state["nodes"], state["resource_pos"], fparams),
                    "passed": passed_diagnostic(
                        compute_metrics(state["nodes"], state["resource_pos"], fparams),
                        state["resource_reached"], fparams,
                    ),
                },
                fparams, rng, actions,
            )
            expected = fixture["expected_summary"]
            status = "PASS" if actual == expected else "FAIL"
            error_detail = "" if status == "PASS" else "summary mismatch"
        except Exception as e:
            status = "FAIL"
            error_detail = f"{type(e).__name__}: {str(e)}"
            actual = None

        results.append({
            "category": "cluster_run",
            "fixture_index": idx,
            "fixture_name": name,
            "status": status,
            "error_detail": error_detail,
            "actual": actual,
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Load fixtures
    with open(INTEGER_FIXTURES_PATH, "r", encoding="utf-8") as f:
        integer_fixtures = json.load(f)
    with open(CLUSTER_FIXTURES_PATH, "r", encoding="utf-8") as f:
        cluster_fixtures = json.load(f)

    # Run all
    int_cases = run_integer_fixtures(integer_fixtures)
    clu_cases = run_cluster_fixtures(cluster_fixtures)

    all_cases = int_cases + clu_cases
    total = len(all_cases)
    passed = sum(1 for c in all_cases if c["status"] == "PASS")
    int_passed = sum(1 for c in int_cases if c["status"] == "PASS")
    clu_passed = sum(1 for c in clu_cases if c["status"] == "PASS")
    overall_passed = (passed == total)

    # Print summary
    print(f"\n{'='*60}")
    print(f"ORIGINAL LOCAL ORACLES: {int_passed}/25")
    print(f"ORIGINAL CLUSTER ORACLES: {clu_passed}/15")
    print(f"ORIGINAL TOTAL: {passed}/40")
    print(f"OVERALL: {'PASS' if overall_passed else 'FAIL'}")
    print(f"{'='*60}\n")

    for case in all_cases:
        marker = "PASS" if case["status"] == "PASS" else "FAIL"
        print(f"  {marker} [{case['category']}] {case['fixture_name']}")
        if case["error_detail"]:
            print(f"       Error: {case['error_detail']}")

    timestamp = datetime.now().strftime("%Y-%m-%d")

    # ── Build results JSON ──
    clu_init_cases = [c for c in clu_cases if c["category"] == "cluster_initialization"]
    clu_metrics_cases = [c for c in clu_cases if c["category"] == "cluster_metrics"]
    clu_action_cases = [c for c in clu_cases if c["category"] == "cluster_action"]
    clu_damage_cases = [c for c in clu_cases if c["category"] == "cluster_damage"]
    clu_run_cases = [c for c in clu_cases if c["category"] == "cluster_run"]

    def case_to_dict(c):
        d = {
            "name": c["fixture_name"],
            "status": c["status"],
        }
        if c["error_detail"]:
            d["error_detail"] = c["error_detail"]
        return d

    results_json = {
        "runner": "stage_1_1_oracle_runner.py",
        "timestamp": timestamp,
        "overall_passed": overall_passed,
        "total_fixtures": total,
        "passed_count": passed,
        "integer_fixtures": {
            "passed": int_passed == 25,
            "count": 25,
            "passed_count": int_passed,
            "cases": [case_to_dict(c) for c in int_cases],
        },
        "cluster_fixtures": {
            "passed": clu_passed == 15,
            "count": 15,
            "passed_count": clu_passed,
            "initialization": {
                "count": len(clu_init_cases),
                "passed": sum(1 for c in clu_init_cases if c["status"] == "PASS"),
                "cases": [case_to_dict(c) for c in clu_init_cases],
            },
            "metrics": {
                "count": len(clu_metrics_cases),
                "passed": sum(1 for c in clu_metrics_cases if c["status"] == "PASS"),
                "cases": [case_to_dict(c) for c in clu_metrics_cases],
            },
            "action": {
                "count": len(clu_action_cases),
                "passed": sum(1 for c in clu_action_cases if c["status"] == "PASS"),
                "cases": [case_to_dict(c) for c in clu_action_cases],
            },
            "damage": {
                "count": len(clu_damage_cases),
                "passed": sum(1 for c in clu_damage_cases if c["status"] == "PASS"),
                "cases": [case_to_dict(c) for c in clu_damage_cases],
            },
            "run": {
                "count": len(clu_run_cases),
                "passed": sum(1 for c in clu_run_cases if c["status"] == "PASS"),
                "cases": [case_to_dict(c) for c in clu_run_cases],
            },
        },
    }

    # Write results JSON
    json_path = OUTPUT_DIR + r"\original_oracle_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2)
    print(f"\nResults JSON written to: {json_path}")

    # ── Build fixture ledger CSV ──
    csv_path = OUTPUT_DIR + r"\original_fixture_ledger.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("category,fixture_index,fixture_name,status,error_detail\n")
        for case in all_cases:
            f.write(f"{case['category']},{case['fixture_index']},{case['fixture_name']},{case['status']},{case['error_detail']}\n")
    print(f"Fixture ledger CSV written to: {csv_path}")

    # ── Build results MD ──
    md_path = OUTPUT_DIR + r"\original_oracle_results.md"
    md_lines = [
        f"# Natural Math v5 — Frozen Original Oracle Results",
        "",
        f"**Runner:** stage_1_1_oracle_runner.py",
        f"**Timestamp:** {timestamp}",
        f"**Overall Result:** {'✅ PASS' if overall_passed else '❌ FAIL'}",
        "",
        "## Summary",
        "",
        "| Category | Passed | Total |",
        "|----------|--------|-------|",
        f"| Integer Fixtures | {int_passed} | 25 |",
        f"| Cluster Fixtures | {clu_passed} | 15 |",
        f"| **Total** | **{passed}** | **{total}** |",
        "",
        "## Integer Fixtures (25)",
        "",
        "| # | Fixture Name | Status | Error |",
        "|---|-------------|--------|-------|",
    ]
    for c in int_cases:
        md_lines.append(f"| {c['fixture_index']} | {c['fixture_name']} | {c['status']} | {c['error_detail']} |")

    md_lines.extend([
        "",
        "## Cluster Fixtures (15)",
        "",
        "### Initialization (2)",
        "",
        "| # | Fixture Name | Status | Error |",
        "|---|-------------|--------|-------|",
    ])
    for c in clu_init_cases:
        md_lines.append(f"| {c['fixture_index']} | {c['fixture_name']} | {c['status']} | {c['error_detail']} |")

    md_lines.extend([
        "",
        "### Metrics (3)",
        "",
        "| # | Fixture Name | Status | Error |",
        "|---|-------------|--------|-------|",
    ])
    for c in clu_metrics_cases:
        md_lines.append(f"| {c['fixture_index']} | {c['fixture_name']} | {c['status']} | {c['error_detail']} |")

    md_lines.extend([
        "",
        "### Action (5)",
        "",
        "| # | Fixture Name | Status | Error |",
        "|---|-------------|--------|-------|",
    ])
    for c in clu_action_cases:
        md_lines.append(f"| {c['fixture_index']} | {c['fixture_name']} | {c['status']} | {c['error_detail']} |")

    md_lines.extend([
        "",
        "### Damage (1)",
        "",
        "| # | Fixture Name | Status | Error |",
        "|---|-------------|--------|-------|",
    ])
    for c in clu_damage_cases:
        md_lines.append(f"| {c['fixture_index']} | {c['fixture_name']} | {c['status']} | {c['error_detail']} |")

    md_lines.extend([
        "",
        "### Run (4)",
        "",
        "| # | Fixture Name | Status | Error |",
        "|---|-------------|--------|-------|",
    ])
    for c in clu_run_cases:
        md_lines.append(f"| {c['fixture_index']} | {c['fixture_name']} | {c['status']} | {c['error_detail']} |")

    md_lines.extend([
        "",
        "## Notes",
        "",
        "- All fixtures are frozen oracle fixtures from the v5 specification.",
        "- Comparisons are exact: energy, position, alive status, bonds, pressure, direction.",
        "- Integer fixtures use `run_step()` from the clean package.",
        "- Cluster fixtures use the clean package's `initialize_cluster()`, `compute_metrics()`, cluster actions, and `cluster_step()`.",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Results MD written to: {md_path}")

    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
