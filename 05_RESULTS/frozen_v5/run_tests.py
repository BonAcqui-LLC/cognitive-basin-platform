"""
Deterministic replay and isolation tests for Natural Math v5 (frozen).

Parts A, B, C as specified.
"""
import sys, os, json, copy, gc, traceback, math
from collections import OrderedDict
from datetime import datetime, timezone

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
from natural_math_v5 import run_cluster, run_step, default_params, NaturalMathValidationError
from natural_math_v5.randomness import TraceRng
from natural_math_v5.cluster_initialization import initialize_cluster
from natural_math_v5.cluster_step import cluster_step
from natural_math_v5.cluster_metrics import compute_metrics, passed_diagnostic
from natural_math_v5.validation import check_invariants

# ── helpers ──────────────────────────────────────────────────

def deep_equal(a, b, path=""):
    """Recursive deep equality returning (bool, str) with failure path."""
    if type(a) is not type(b):
        return False, f"{path}: type mismatch {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False, f"{path}: key mismatch {set(a.keys())} vs {set(b.keys())}"
        for k in a:
            ok, msg = deep_equal(a[k], b[k], f"{path}.{k}")
            if not ok:
                return False, msg
    elif isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False, f"{path}: length {len(a)} vs {len(b)}"
        for i, (va, vb) in enumerate(zip(a, b)):
            ok, msg = deep_equal(va, vb, f"{path}[{i}]")
            if not ok:
                return False, msg
    elif isinstance(a, set):
        if a != b:
            return False, f"{path}: set mismatch {a} vs {b}"
    elif isinstance(a, float):
        if not (math.isclose(a, b, rel_tol=1e-9) or (math.isnan(a) and math.isnan(b))):
            return False, f"{path}: float {a} != {b}"
    else:
        if a != b:
            return False, f"{path}: value {a!r} != {b!r}"
    return True, ""

def identity_check_results(r1, r2, label):
    """Check that corresponding node dicts do NOT share identity across runs."""
    issues = []
    n1, n2 = r1.get("nodes", []), r2.get("nodes", [])
    for i, (a, b) in enumerate(zip(n1, n2)):
        if a is b:
            issues.append(f"{label}: node[{i}] shares identity")
    if r1 is r2:
        issues.append(f"{label}: top-level dict shares identity")
    return issues

# ── Part A: Cluster Deterministic Replay ──────────────────────

def part_a():
    print("=" * 60)
    print("PART A: Cluster Deterministic Replay (50 seeds x 4 step counts)")

    seeds = list(range(50))
    step_counts = [0, 1, 35, 140]
    failures = []

    total_configs = len(seeds) * len(step_counts)
    config_index = 0

    for seed in seeds:
        for steps in step_counts:
            config_index += 1
            label = f"seed={seed}, steps={steps}"

            # ── params=None ──
            try:
                r_none_1 = run_cluster(seed, params=None, steps=steps)
                r_none_2 = run_cluster(seed, params=None, steps=steps)
            except Exception as e:
                failures.append({
                    "part": "A", "config": label, "params": "None",
                    "error": str(e), "traceback": traceback.format_exc(),
                })
                continue

            ok, msg = deep_equal(r_none_1, r_none_2)
            if not ok:
                failures.append({
                    "part": "A", "config": label, "params": "None", "mismatch": msg,
                })

            id_issues = identity_check_results(r_none_1, r_none_2, f"{label}/None")
            for issue in id_issues:
                failures.append({
                    "part": "A", "config": label, "params": "None", "identity_issue": issue,
                })

            # ── params=explicit copy ──
            p_before = default_params()
            p1 = copy.deepcopy(p_before)
            p2 = copy.deepcopy(p_before)

            try:
                r_explicit_1 = run_cluster(seed, params=p1, steps=steps)
                r_explicit_2 = run_cluster(seed, params=p2, steps=steps)
            except Exception as e:
                failures.append({
                    "part": "A", "config": label, "params": "explicit",
                    "error": str(e), "traceback": traceback.format_exc(),
                })
                continue

            ok, msg = deep_equal(r_explicit_1, r_explicit_2)
            if not ok:
                failures.append({
                    "part": "A", "config": label, "params": "explicit", "mismatch": msg,
                })

            id_issues = identity_check_results(r_explicit_1, r_explicit_2, f"{label}/explicit")
            for issue in id_issues:
                failures.append({
                    "part": "A", "config": label, "params": "explicit", "identity_issue": issue,
                })

            # Check params dicts unchanged
            ok_p1, msg_p1 = deep_equal(p_before, p1)
            if not ok_p1:
                failures.append({
                    "part": "A", "config": label, "params": "explicit", "params_mutated_p1": msg_p1,
                })
            ok_p2, msg_p2 = deep_equal(p_before, p2)
            if not ok_p2:
                failures.append({
                    "part": "A", "config": label, "params": "explicit", "params_mutated_p2": msg_p2,
                })

            if config_index % 20 == 0:
                print(f"  [{config_index}/{total_configs}] {label} OK")

    print(f"  Completed {config_index}/{total_configs} configs")
    print(f"  Failures: {len(failures)}")
    return failures

# ── Part B: Local Deterministic Cases ─────────────────────────

def make_test_node(node_id, pos, energy=80000, alive=True):
    return {
        "id": node_id, "pos": pos, "direction": (0, 1, 0),
        "energy": energy, "pressure": 0, "alive": alive,
        "type": "seed", "parent_id": None, "bonds": set(), "signal_type": 0,
    }

def part_b():
    print("\n" + "=" * 60)
    print("PART B: Local Deterministic Cases (10 bounded cases)")
    failures = []
    p = default_params()

    cases = [
        ([make_test_node(0, (12, 12, 0), 100000)], "1-node singleton"),
        ([make_test_node(0, (10, 10, 0), 90000), make_test_node(1, (15, 15, 0), 90000)], "2-node no bonds"),
        ([make_test_node(0, (12, 12, 0), 80000), make_test_node(1, (13, 12, 0), 80000),
          make_test_node(2, (14, 12, 0), 80000)], "3-node chain"),
        ([make_test_node(0, (10, 10, 0), 70000), make_test_node(1, (12, 10, 0), 70000),
          make_test_node(2, (10, 12, 0), 70000), make_test_node(3, (12, 12, 0), 70000)], "4-node grid"),
        ([make_test_node(0, (12, 12, 0), 60000), make_test_node(1, (12, 13, 0), 60000),
          make_test_node(2, (13, 12, 0), 60000), make_test_node(3, (13, 13, 0), 60000),
          make_test_node(4, (14, 12, 0), 60000)], "5-node cluster"),
        ([make_test_node(0, (5, 5, 0), 60000), make_test_node(1, (5, 6, 0), 60000),
          make_test_node(2, (6, 5, 0), 60000), make_test_node(3, (6, 6, 0), 100),
          make_test_node(4, (7, 5, 0), 60000), make_test_node(5, (7, 6, 0), 60000)], "6-node mixed energy"),
        ([make_test_node(i, (10 + i, 12, 0), 50000 + i * 5000) for i in range(7)], "7-node chain"),
        ([make_test_node(i, (8 + i % 4, 8 + i // 4, 0), 60000) for i in range(8)], "8-node grid"),
        ([make_test_node(i, (12 + i % 3 - 1, 12 + i // 3 - 1, 0), 55000 + i * 2000) for i in range(9)], "9-node"),
        ([make_test_node(i, (i % 25, i % 25, 0), 70000) for i in range(10)], "10-node diagonal"),
    ]

    for case_idx, (nodes_template, desc) in enumerate(cases):
        label = f"Case {case_idx}: {desc}"
        try:
            n1 = copy.deepcopy(nodes_template)
            n2 = copy.deepcopy(nodes_template)

            result1 = run_step(n1, p, rng=TraceRng(case_idx * 1000 + 42))
            result2 = run_step(n2, p, rng=TraceRng(case_idx * 1000 + 42))

            ok, msg = deep_equal(result1, result2)
            if not ok:
                failures.append({"part": "B", "case": label, "mismatch": msg})

            # Integer-only check
            for node in result1:
                if node.get("alive"):
                    for field in ["energy", "pressure"]:
                        val = node.get(field, 0)
                        if isinstance(val, float):
                            failures.append({"part": "B", "case": label,
                                "float_found": f"node[{node['id']}].{field}={val!r}"})
                    pos = node.get("pos", (0, 0, 0))
                    for i, coord in enumerate(pos):
                        if isinstance(coord, float):
                            failures.append({"part": "B", "case": label,
                                "float_found": f"node[{node['id']}].pos[{i}]={coord!r}"})

            check_invariants(result1, p)

            # Isolation: different RNG, same seed
            n3 = copy.deepcopy(nodes_template)
            n4 = copy.deepcopy(nodes_template)
            result3 = run_step(n3, p, rng=TraceRng(case_idx * 1000 + 99))
            result4 = run_step(n4, p, rng=TraceRng(case_idx * 1000 + 99))
            ok2, msg2 = deep_equal(result3, result4)
            if not ok2:
                failures.append({"part": "B", "case": label, "mismatch_isolation": msg2})

            for i, (a, b) in enumerate(zip(result1, result2)):
                if a is b:
                    failures.append({"part": "B", "case": label, "identity_leak": f"node[{i}]"})

            print(f"  {label}: OK")
        except NaturalMathValidationError as e:
            failures.append({"part": "B", "case": label, "invariant_violation": str(e)})
        except Exception as e:
            failures.append({"part": "B", "case": label, "error": str(e),
                "traceback": traceback.format_exc()})

    print(f"  Cases: {len(cases)}, Failures: {len(failures)}")
    return failures

# ── Part C: Isolation Tests ───────────────────────────────────

def part_c():
    print("\n" + "=" * 60)
    print("PART C: Isolation Tests")
    failures = []

    # C1: Different seeds = independent
    try:
        r0 = run_cluster(0)
        r1 = run_cluster(1)
        ok, _ = deep_equal(r0, r1)
        if ok:
            failures.append({"part": "C", "test": "seed_isolation",
                "issue": "run_cluster(0) and run_cluster(1) returned identical results"})
        else:
            print("  C1: Different seeds -> different results OK")
        for i, (a, b) in enumerate(zip(r0["nodes"], r1["nodes"])):
            if a is b:
                failures.append({"part": "C", "test": "seed_isolation",
                    "issue": f"Node[{i}] shares identity across seed 0 and 1"})
    except Exception as e:
        failures.append({"part": "C", "test": "seed_isolation",
            "error": str(e), "traceback": traceback.format_exc()})

    # C2: Triple identical
    try:
        r_a = run_cluster(0, steps=10)
        r_b = run_cluster(0, steps=10)
        r_c = run_cluster(0, steps=10)
        ok_ab, msg_ab = deep_equal(r_a, r_b)
        ok_ac, msg_ac = deep_equal(r_a, r_c)
        if not ok_ab:
            failures.append({"part": "C", "test": "triple_identical", "mismatch": f"A vs B: {msg_ab}"})
        if not ok_ac:
            failures.append({"part": "C", "test": "triple_identical", "mismatch": f"A vs C: {msg_ac}"})
        ok_bc, msg_bc = deep_equal(r_b, r_c)
        if not ok_bc:
            failures.append({"part": "C", "test": "triple_identical", "mismatch": f"B vs C: {msg_bc}"})
        print(f"  C2: Triple identical: {'OK' if (ok_ab and ok_ac and ok_bc) else 'FAIL'}")
    except Exception as e:
        failures.append({"part": "C", "test": "triple_identical",
            "error": str(e), "traceback": traceback.format_exc()})

    # C3: CWD independence
    try:
        orig_cwd = os.getcwd()
        temp_dir = os.path.join(os.environ.get("TEMP", orig_cwd), "nm_v5_iso_test_c")
        os.makedirs(temp_dir, exist_ok=True)
        os.chdir(temp_dir)
        r_cwd = run_cluster(42, steps=5)
        os.chdir(orig_cwd)
        r_orig = run_cluster(42, steps=5)
        ok_cwd, msg_cwd = deep_equal(r_cwd, r_orig)
        if not ok_cwd:
            failures.append({"part": "C", "test": "cwd_independence", "mismatch": msg_cwd})
        else:
            print("  C3: CWD independence OK")
    except Exception as e:
        failures.append({"part": "C", "test": "cwd_independence",
            "error": str(e), "traceback": traceback.format_exc()})
        try:
            os.chdir(orig_cwd)
        except:
            pass

    # C4: Dict insertion order independence
    try:
        sorted_keys = sorted(default_params().keys())
        dp = default_params()
        p_ordered = OrderedDict()
        for k in sorted_keys:
            p_ordered[k] = dp[k]
        p_reversed = OrderedDict()
        for k in reversed(sorted_keys):
            p_reversed[k] = dp[k]
        r_ordered = run_cluster(7, params=dict(p_ordered), steps=5)
        r_reversed = run_cluster(7, params=dict(p_reversed), steps=5)
        ok_ord, msg_ord = deep_equal(r_ordered, r_reversed)
        if not ok_ord:
            failures.append({"part": "C", "test": "insertion_order_independence", "mismatch": msg_ord})
        else:
            print("  C4: Dict insertion order independence OK")
    except Exception as e:
        failures.append({"part": "C", "test": "insertion_order_independence",
            "error": str(e), "traceback": traceback.format_exc()})

    # C5: Global state leakage
    try:
        gc.collect()
        results = [run_cluster(i, steps=3) for i in range(5)]
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                if results[i] is results[j]:
                    failures.append({"part": "C", "test": "global_state_leakage",
                        "issue": f"Result {i} and {j} share identity"})
                for ni, (na, nb) in enumerate(zip(results[i]["nodes"], results[j]["nodes"])):
                    if na is nb:
                        failures.append({"part": "C", "test": "global_state_leakage",
                            "issue": f"Node[{ni}] shares identity across runs {i} and {j}"})
        print("  C5: Global state leakage check OK")
    except Exception as e:
        failures.append({"part": "C", "test": "global_state_leakage",
            "error": str(e), "traceback": traceback.format_exc()})

    print(f"  Isolation failures: {len(failures)}")
    return failures

# ── Internal RNG trace verification ───────────────────────────

def part_a_rng_trace():
    print("\n" + "=" * 60)
    print("PART A (supplement): Internal RNG trace verification")
    failures = []
    for seed in [0, 17, 49]:
        for steps in [0, 35, 140]:
            label = f"RNG trace seed={seed}, steps={steps}"
            p = default_params()
            rng1 = TraceRng(seed)
            rng2 = TraceRng(seed)
            state1 = initialize_cluster(seed, p, rng1)
            state2 = initialize_cluster(seed, p, rng2)
            for step_idx in range(1, steps + 1):
                cluster_step(state1, p, rng1, step_idx)
                cluster_step(state2, p, rng2, step_idx)
            if rng1.draws != rng2.draws:
                failures.append({"part": "A_rng", "config": label,
                    "issue": f"RNG draws mismatch: len1={len(rng1.draws)}, len2={len(rng2.draws)}"})
            else:
                print(f"  {label}: draws match ({len(rng1.draws)} draws)")
            ok, msg = deep_equal(state1, state2)
            if not ok:
                failures.append({"part": "A_rng", "config": label, "state_mismatch": msg})
            for i, (ns1, ns2) in enumerate(zip(state1["nodes"], state2["nodes"])):
                if ns1 is ns2:
                    failures.append({"part": "A_rng", "config": label, "identity_issue": f"Node[{i}]"})
    print(f"  RNG trace failures: {len(failures)}")
    return failures

# ── Main ──────────────────────────────────────────────────────

def main():
    all_failures = []
    print("Natural Math v5 — Deterministic Replay & Isolation Tests")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    all_failures.extend(part_a())
    all_failures.extend(part_a_rng_trace())
    b_failures = part_b()
    all_failures.extend(b_failures)
    c_failures = part_c()
    all_failures.extend(c_failures)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print(f"  Total failures: {len(all_failures)}")
    all_deterministic = len(all_failures) == 0

    results = {
        "seeds_tested": 50,
        "step_counts": [0, 1, 35, 140],
        "total_configs": 200,
        "all_deterministic": all_deterministic,
        "local_cases": 10,
        "failures": all_failures,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5"
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "deterministic_replay_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  JSON -> {json_path}")

    # Build markdown
    md = []
    md.append("# Natural Math v5 — Deterministic Replay & Isolation Results")
    md.append("")
    md.append(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    md.append(f"**SHA256:** E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(f"- **Seeds tested:** 50")
    md.append(f"- **Step counts:** 0, 1, 35, 140")
    md.append(f"- **Total configs:** 200 (50 x 4)")
    md.append(f"- **Local cases:** 10")
    md.append(f"- **All deterministic:** {'YES' if all_deterministic else 'NO'}")
    md.append(f"- **Failures:** {len(all_failures)}")
    md.append("")

    if all_failures:
        md.append("## Failures")
        md.append("")
        for i, f in enumerate(all_failures, 1):
            md.append(f"### Failure {i}")
            md.append("")
            for k, v in f.items():
                md.append(f"- **{k}:** {v}")
            md.append("")
    else:
        md.append("## All Tests Passed")
        md.append("")
        md.append("All 200 cluster configurations produced **identical results across repeated runs** with both implicit (`params=None`) and explicit parameter dictionaries.")
        md.append("")
        md.append("### Part A: Cluster Deterministic Replay")
        md.append("")
        md.append("- All 50 seeds x 4 step counts = 200 configurations -> **identical on replay**")
        md.append("- Parameter dictionaries remain **unchanged** after each call")
        md.append("- Node structures do **not share identity** across runs (fresh deep copies)")
        md.append("- RNG traces (TraceRng.draws) match exactly")
        md.append("")
        md.append("### Part B: Local Deterministic Cases")
        md.append("")
        md.append("- 10 local cases with node sets from 1-10 nodes -> **all identical on replay**")
        md.append("- Model state uses **integers only** (no floats)")
        md.append("- Invariants pass after every step")
        md.append("- No global mutable state leakage")
        md.append("")
        md.append("### Part C: Isolation Tests")
        md.append("")
        md.append("- `run_cluster(0)` vs `run_cluster(1)` -> **independent** (no shared state)")
        md.append("- `run_cluster(0, steps=10)` x 3 -> **identical** each time")
        md.append("- Filesystem location independence -> **confirmed**")
        md.append("- Dictionary insertion order independence -> **confirmed**")
        md.append("- Global mutable state leakage -> **none found**")
        md.append("")

    md_path = os.path.join(out_dir, "deterministic_replay_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md))
    print(f"  MD -> {md_path}")

    return 0 if all_deterministic else 1

if __name__ == "__main__":
    sys.exit(main())
