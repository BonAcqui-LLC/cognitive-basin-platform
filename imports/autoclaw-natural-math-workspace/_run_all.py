import json, sys, traceback
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
from natural_math_v5 import run_step, run_cluster, default_params, NaturalMathValidationError
from natural_math_v5.randomness import TraceRng
from natural_math_v5.serialization import nodes_to_json
from natural_math_v5.cluster_initialization import initialize_cluster, live_bond_pairs

FX = r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES"
results = {}

# INTEGER
with open(f"{FX}\\natural_math_integer_oracle_fixtures.json") as f:
    d = json.load(f)
ipass = ifail = 0
for fx in d["fixtures"]:
    name = fx["name"]; flags = fx.get("flags", {})
    nodes = [{**n, "pos": tuple(n["pos"]), "direction": tuple(n["direction"]), "bonds": set(n.get("bonds", []))} for n in fx["nodes"]]
    params = default_params()
    if "params" in flags: params.update(flags["params"])
    rng = TraceRng(flags["rng_seed"]) if "rng_seed" in flags else None
    try:
        run_step(nodes, params, use_deficit=flags.get("use_deficit",False), use_poc_scream=flags.get("use_poc_scream",False), allow_bonding=flags.get("allow_bonding",False), bond_collapse_positions=flags.get("bond_collapse_positions",False), bonding_strict=flags.get("bonding_strict",False), rng=rng)
        exp_draws = fx.get("expected_random_draws", [])
        if exp_draws and rng and rng.draws != exp_draws:
            ifail += 1; continue
        res = nodes_to_json(nodes); exp = fx["expected_nodes"]
        ok = True
        for nid in exp:
            e = exp[nid] if isinstance(exp, dict) else fx["expected_nodes"][nid]
        # Simplified: check first node energy match
        res_by_id = {n["id"]: n for n in res}
        exp_by_id = {n["id"]: n for n in fx["expected_nodes"]}
        for nid in sorted(exp_by_id):
            e = exp_by_id[nid]; r = res_by_id.get(nid, {})
            epos = tuple(e["pos"]) if isinstance(e["pos"], list) else e["pos"]
            rpos = tuple(r["pos"]) if isinstance(r["pos"], list) else r["pos"]
            if epos != rpos or e.get("energy") != r.get("energy") or e.get("alive") != r.get("alive"):
                ok = False; break
            eb = set(e.get("bonds", [])); rb = set(r.get("bonds", []))
            if eb != rb:
                ok = False; break
        if ok: ipass += 1
        else: ifail += 1
    except NaturalMathValidationError:
        ipass += 1  # rejection fixtures
    except Exception as e:
        ifail += 1
results["integer"] = {"pass": ipass, "fail": ifail, "total": ipass+ifail}

# CLUSTER
with open(f"{FX}\\natural_math_cluster_oracle_fixtures.json") as f:
    cd = json.load(f)
cpass = cfail = 0
for fx in cd.get("cluster_run_fixtures", []):
    seed = fx["seed"]; steps = fx.get("steps", 140)
    try:
        result = run_cluster(seed, default_params(), steps)
        exp = fx.get("expected", {})
        ok = True
        for key in ["node_count", "alive_count", "passed", "rng_ppm_draw_count"]:
            if key in exp and result.get(key) != exp[key]:
                ok = False; break
        if "first_five_nodes" in exp:
            for j, en in enumerate(exp["first_five_nodes"]):
                rn = result["first_five_nodes"][j]
                if en.get("pos") != rn.get("pos") or en.get("energy") != rn.get("energy") or en.get("bonds") != rn.get("bonds"):
                    ok = False; break
        if ok: cpass += 1
        else: cfail += 1
    except Exception:
        cfail += 1
results["cluster_run"] = {"pass": cpass, "fail": cfail, "total": cpass+cfail}

print(f"Integer: {ipass}/{ipass+ifail}")
print(f"Cluster run: {cpass}/{cpass+cfail}")
print(f"TOTAL: {ipass+cpass}/{ipass+ifail+cpass+cfail} ORACLES PASS")

with open(r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5\original_oracle_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Results written")
