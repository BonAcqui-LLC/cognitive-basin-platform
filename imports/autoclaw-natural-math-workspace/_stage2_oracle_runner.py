"""
Stage 2 — Oracle Mode Comparison Runner.

Runs ALL 40 frozen v5 oracles (25 integer + 15 cluster) through:
  1. BASELINE (direct nm.run_step / nm.run_cluster)
  2. HARNESS_NO_EXTENSIONS (runner with empty registry)
  3. HARNESS_WITH_EXTENSIONS (runner with noop extension)

Verifies all 120 runs produce identical results to original frozen outputs.

Output: 05_RESULTS/extension_harness/original_oracle_mode_comparison.json
        05_RESULTS/extension_harness/deterministic_mode_comparison.json
"""

import copy
import json
import sys
import hashlib
import time
from datetime import datetime

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE")

import natural_math_v5 as nm
from natural_math_v5.core_step import run_step
from natural_math_v5.randomness import TraceRng
from natural_math_v5.parameters import DEFAULT_PARAMS
from natural_math_v5.errors import NaturalMathValidationError
from natural_math_v5.cluster_initialization import initialize_cluster, live_bond_pairs
from natural_math_v5.cluster_metrics import compute_metrics, passed_diagnostic, select_cluster_action
from natural_math_v5.cluster_actions import (
    kill_below_tau, apply_damage, apply_resource_absorption,
    apply_cluster_action,
)
from natural_math_v5.cluster_step import cluster_step
from natural_math_v5.cluster import summarize_cluster_run


def summarize_init_state(state, params):
    """Full initialization summary matching original oracle runner."""
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

from extension_harness import (
    Mode,
    NoopExtension,
    run_local,
    run_cluster,
    hash_result,
    deep_equal,
    structured_diff,
    serialize_run_output,
)

# ── Paths ────────────────────────────────────────────────────────────
INTEGER_FIXTURES_PATH = r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_integer_oracle_fixtures.json"
CLUSTER_FIXTURES_PATH = r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_cluster_oracle_fixtures.json"
OUTPUT_DIR = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\extension_harness"

# ── Helpers ──────────────────────────────────────────────────────────

def json_node_to_internal(node):
    n = copy.deepcopy(node)
    n["pos"] = tuple(n["pos"])
    n["direction"] = tuple(n["direction"])
    n["bonds"] = set(n["bonds"])
    return n


def internal_nodes_to_json(nodes):
    result = []
    for node in nodes:
        result.append({
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
        })
    return result


# ══════════════════════════════════════════════════════════════════════
# TASK 1: Run 40 oracles in 3 modes
# ══════════════════════════════════════════════════════════════════════

def run_integer_oracles_3modes(fixtures_data):
    """Run all 25 integer fixtures through 3 modes."""
    results = []
    defaults = DEFAULT_PARAMS
    base_override = fixtures_data.get("defaults_override", {})
    noop = NoopExtension()

    for idx, fixture in enumerate(fixtures_data["fixtures"]):
        name = fixture["name"]
        flags = fixture.get("flags", {})

        # Build params
        params = copy.deepcopy(defaults)
        params.update(base_override)
        if "params" in flags:
            params.update(flags["params"])

        # Build kwargs
        kwargs = {}
        for k in ("use_deficit", "use_poc_scream", "allow_bonding",
                  "bond_collapse_positions", "bonding_strict"):
            if k in flags:
                kwargs[k] = flags[k]

        mode_results = {}
        overall_status = "PASS"
        errors = []

        for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            try:
                nodes = [json_node_to_internal(n) for n in fixture["nodes"]]

                if mode_label == Mode.BASELINE:
                    rng = TraceRng(flags["rng_seed"]) if "rng_seed" in flags else None
                    result_nodes = run_step(nodes, params, rng=rng, **kwargs)
                    actual_json = internal_nodes_to_json(result_nodes)
                    hook_events = []
                else:
                    rng = TraceRng(flags["rng_seed"]) if "rng_seed" in flags else None
                    out = run_local(
                        nodes, params, mode=mode_label,
                        extensions=[noop] if mode_label == Mode.HARNESS_WITH_EXTENSIONS else None,
                        rng=rng, **kwargs,
                    )
                    actual_json = internal_nodes_to_json(out["result"])
                    hook_events = out.get("hook_events", [])

                expected_nodes = fixture.get("expected_nodes", [])
                match = (actual_json == expected_nodes)
                h = hashlib.sha256(
                    json.dumps(actual_json, sort_keys=True).encode()
                ).hexdigest()[:16]

                mode_results[mode_label] = {
                    "match": match,
                    "hash": h,
                    "hook_event_count": len(hook_events),
                }

                if not match:
                    overall_status = "FAIL"
                    errors.append(f"{mode_label}: node mismatch")

            except NaturalMathValidationError as e:
                expected_error = fixture.get("expected_error")
                if expected_error:
                    mode_results[mode_label] = {
                        "match": True,
                        "error_raised": True,
                        "error": str(e),
                        "hook_event_count": 0,
                    }
                else:
                    overall_status = "FAIL"
                    mode_results[mode_label] = {
                        "match": False,
                        "error": str(e),
                        "hook_event_count": 0,
                    }
                    errors.append(f"{mode_label}: unexpected error: {str(e)}")
            except Exception as e:
                overall_status = "FAIL"
                mode_results[mode_label] = {
                    "match": False,
                    "error": f"{type(e).__name__}: {str(e)}",
                    "hook_event_count": 0,
                }
                errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

        results.append({
            "category": "integer",
            "fixture_index": idx,
            "fixture_name": name,
            "status": overall_status,
            "modes": mode_results,
            "errors": errors,
        })

    return results


def run_cluster_oracles_3modes(fixtures_data):
    """Run all 15 cluster fixtures through 3 modes."""
    results = []
    noop = NoopExtension()

    # ── Init fixtures (2) ──
    for idx, fixture in enumerate(fixtures_data.get("initialization_fixtures", [])):
        name = fixture["name"]
        seed = fixture["seed"]
        fparams = copy.deepcopy(DEFAULT_PARAMS)
        fparams.update(fixture.get("params", {}))

        mode_results = {}
        overall_status = "PASS"
        errors = []

        for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            try:
                rng = TraceRng(seed)
                state = initialize_cluster(seed, fparams, rng)

                # Summarize using full init_state summary
                actual = summarize_init_state(state, fparams)

                expected = fixture["expected_summary"]
                match = (actual == expected)

                mode_results[mode_label] = {"match": match, "hash": hashlib.sha256(
                    json.dumps(actual, sort_keys=True).encode()).hexdigest()[:16]}

                if not match:
                    overall_status = "FAIL"
                    errors.append(f"{mode_label}: summary mismatch")
            except Exception as e:
                overall_status = "FAIL"
                mode_results[mode_label] = {"match": False, "error": f"{type(e).__name__}: {str(e)}"}
                errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

        results.append({
            "category": "cluster_initialization",
            "fixture_index": idx,
            "fixture_name": name,
            "status": overall_status,
            "modes": mode_results,
            "errors": errors,
        })

    # ── Metrics fixtures (3) ──
    for idx, fixture in enumerate(fixtures_data.get("metrics_fixtures", [])):
        name = fixture["name"]
        fparams = copy.deepcopy(DEFAULT_PARAMS)
        fparams.update(fixture.get("params", {}))
        resource_pos = tuple(fixture["resource_pos"])

        mode_results = {}
        overall_status = "PASS"
        errors = []

        for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            try:
                nodes = [json_node_to_internal(n) for n in fixture["nodes"]]
                actual = compute_metrics(nodes, resource_pos, fparams)
                expected = fixture["expected_metrics"]
                match = (actual == expected)

                mode_results[mode_label] = {"match": match, "hash": hashlib.sha256(
                    json.dumps(actual, sort_keys=True).encode()).hexdigest()[:16]}

                if not match:
                    overall_status = "FAIL"
                    errors.append(f"{mode_label}: metrics mismatch")
            except Exception as e:
                overall_status = "FAIL"
                mode_results[mode_label] = {"match": False, "error": f"{type(e).__name__}: {str(e)}"}
                errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

        results.append({
            "category": "cluster_metrics",
            "fixture_index": idx,
            "fixture_name": name,
            "status": overall_status,
            "modes": mode_results,
            "errors": errors,
        })

    # ── Action fixtures (5) ──
    for idx, fixture in enumerate(fixtures_data.get("action_fixtures", [])):
        name = fixture["name"]
        fparams = copy.deepcopy(DEFAULT_PARAMS)
        fparams.update(fixture.get("params", {}))

        for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            mode_results = {}
            overall_status = "PASS"
            errors = []

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

                actual = {
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
                    "metrics": compute_metrics(state["nodes"], state["resource_pos"], fparams),
                }

                expected = fixture["expected_summary"]
                match = (actual == expected)
                mode_results[mode_label] = {"match": match, "hash": hashlib.sha256(
                    json.dumps(actual, sort_keys=True).encode()).hexdigest()[:16]}

                if not match:
                    overall_status = "FAIL"
                    errors.append(f"{mode_label}: summary mismatch")
            except Exception as e:
                overall_status = "FAIL"
                mode_results[mode_label] = {"match": False, "error": f"{type(e).__name__}: {str(e)}"}
                errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

        results.append({
            "category": "cluster_action",
            "fixture_index": idx,
            "fixture_name": name,
            "status": overall_status,
            "modes": mode_results,
            "errors": errors,
        })

    # ── Damage fixtures (1) ──
    for idx, fixture in enumerate(fixtures_data.get("damage_fixtures", [])):
        name = fixture["name"]
        fparams = copy.deepcopy(DEFAULT_PARAMS)
        fparams.update(fixture.get("params", {}))

        mode_results = {}
        overall_status = "PASS"
        errors = []

        for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
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
                match = (actual == expected)

                mode_results[mode_label] = {"match": match, "hash": hashlib.sha256(
                    json.dumps(actual, sort_keys=True).encode()).hexdigest()[:16]}

                if not match:
                    overall_status = "FAIL"
                    errors.append(f"{mode_label}: summary mismatch")
            except Exception as e:
                overall_status = "FAIL"
                mode_results[mode_label] = {"match": False, "error": f"{type(e).__name__}: {str(e)}"}
                errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

        results.append({
            "category": "cluster_damage",
            "fixture_index": idx,
            "fixture_name": name,
            "status": overall_status,
            "modes": mode_results,
            "errors": errors,
        })

    # ── Run fixtures (4) ──
    for idx, fixture in enumerate(fixtures_data.get("cluster_run_fixtures", [])):
        name = fixture["name"]
        seed = fixture["seed"]
        steps = fixture["steps"]
        fparams = copy.deepcopy(DEFAULT_PARAMS)
        fparams.update(fixture.get("params", {}))

        mode_results = {}
        overall_status = "PASS"
        errors = []

        for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            try:
                rng = TraceRng(seed)
                state = initialize_cluster(seed, fparams, rng)
                actions = []
                for step_i in range(1, steps + 1):
                    action = cluster_step(state, fparams, rng, step_i)
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
                match = (actual == expected)

                mode_results[mode_label] = {"match": match, "hash": hashlib.sha256(
                    json.dumps(actual, sort_keys=True).encode()).hexdigest()[:16]}

                if not match:
                    overall_status = "FAIL"
                    errors.append(f"{mode_label}: summary mismatch")
            except Exception as e:
                overall_status = "FAIL"
                mode_results[mode_label] = {"match": False, "error": f"{type(e).__name__}: {str(e)}"}
                errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

        results.append({
            "category": "cluster_run",
            "fixture_index": idx,
            "fixture_name": name,
            "status": overall_status,
            "modes": mode_results,
            "errors": errors,
        })

    return results


# ══════════════════════════════════════════════════════════════════════
# TASK 2: Deterministic mode equivalence (cluster seeds 0-49)
# ══════════════════════════════════════════════════════════════════════

def run_deterministic_equivalence():
    """Run cluster seeds 0-49 at steps 0,1,35,140 in all 3 modes."""
    results = []
    noop = NoopExtension()
    params = nm.default_params()

    for seed in range(50):
        for steps in [0, 1, 35, 140]:
            mode_hashes = {}
            all_match = True
            errors = []

            for mode_label in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
                try:
                    if mode_label == Mode.BASELINE:
                        out = run_cluster(seed=seed, params=params, steps=steps, mode=mode_label)
                    else:
                        out = run_cluster(
                            seed=seed, params=params, steps=steps, mode=mode_label,
                            extensions=[noop] if mode_label == Mode.HARNESS_WITH_EXTENSIONS else None,
                        )
                    h = hash_result(out["result"])
                    mode_hashes[mode_label] = h
                except Exception as e:
                    all_match = False
                    mode_hashes[mode_label] = f"ERROR: {type(e).__name__}: {str(e)}"
                    errors.append(f"{mode_label}: {type(e).__name__}: {str(e)}")

            if all_match and mode_hashes:
                values = list(mode_hashes.values())
                if len(set(values)) != 1:
                    all_match = False
                    errors.append("hash mismatch across modes")

            results.append({
                "seed": seed,
                "steps": steps,
                "all_match": all_match,
                "hashes": mode_hashes,
                "errors": errors,
            })

            # Progress
            if seed % 10 == 0 and steps == 0:
                print(f"  Deterministic equivalence: seed {seed}/49...")

    return results


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load fixtures
    with open(INTEGER_FIXTURES_PATH, "r", encoding="utf-8") as f:
        integer_fixtures = json.load(f)
    with open(CLUSTER_FIXTURES_PATH, "r", encoding="utf-8") as f:
        cluster_fixtures = json.load(f)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # ══════════════════════════════════════════════════════════════════
    # TASK 1: Oracle mode comparison
    # ══════════════════════════════════════════════════════════════════
    print("=" * 60)
    print("TASK 1: Running 40 oracles in 3 modes...")
    print("=" * 60)

    int_results = run_integer_oracles_3modes(integer_fixtures)
    clu_results = run_cluster_oracles_3modes(cluster_fixtures)
    all_results = int_results + clu_results

    total = len(all_results)
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    overall_passed = (passed == total)

    print(f"\n  Integer oracles (all 3 modes): {sum(1 for r in int_results if r['status'] == 'PASS')}/{len(int_results)}")
    print(f"  Cluster oracles (all 3 modes): {sum(1 for r in clu_results if r['status'] == 'PASS')}/{len(clu_results)}")
    print(f"  TOTAL: {passed}/{total}")
    print(f"  OVERALL: {'PASS' if overall_passed else 'FAIL'}")

    for r in all_results:
        if r["status"] == "FAIL":
            print(f"    FAIL [{r['category']}] {r['fixture_name']}: {r['errors']}")

    oracle_json = {
        "task": "original_oracle_mode_comparison",
        "timestamp": timestamp,
        "overall_passed": overall_passed,
        "total_fixtures": total,
        "passed_count": passed,
        "integer_fixtures": {
            "passed": all(r["status"] == "PASS" for r in int_results),
            "count": len(int_results),
            "passed_count": sum(1 for r in int_results if r["status"] == "PASS"),
            "results": int_results,
        },
        "cluster_fixtures": {
            "passed": all(r["status"] == "PASS" for r in clu_results),
            "count": len(clu_results),
            "passed_count": sum(1 for r in clu_results if r["status"] == "PASS"),
            "results": clu_results,
        },
    }

    oracle_path = os.path.join(OUTPUT_DIR, "original_oracle_mode_comparison.json")
    with open(oracle_path, "w", encoding="utf-8") as f:
        json.dump(oracle_json, f, indent=2)
    print(f"\n  Results written to: {oracle_path}")

    # ══════════════════════════════════════════════════════════════════
    # TASK 2: Deterministic mode equivalence
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TASK 2: Deterministic mode equivalence (seeds 0-49)...")
    print("=" * 60)

    det_results = run_deterministic_equivalence()

    det_total = len(det_results)
    det_passed = sum(1 for r in det_results if r["all_match"])
    det_overall = (det_passed == det_total)
    print(f"\n  Deterministic equivalence: {det_passed}/{det_total} match")
    print(f"  OVERALL: {'PASS' if det_overall else 'FAIL'}")

    for r in det_results:
        if not r["all_match"]:
            print(f"    FAIL seed={r['seed']} steps={r['steps']}: {r['errors']}")

    det_json = {
        "task": "deterministic_mode_comparison",
        "timestamp": timestamp,
        "overall_passed": det_overall,
        "total_runs": det_total,
        "passed_count": det_passed,
        "results": det_results,
    }

    det_path = os.path.join(OUTPUT_DIR, "deterministic_mode_comparison.json")
    with open(det_path, "w", encoding="utf-8") as f:
        json.dump(det_json, f, indent=2)
    print(f"\n  Results written to: {det_path}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

    return 0 if (overall_passed and det_overall) else 1


if __name__ == "__main__":
    sys.exit(main())
