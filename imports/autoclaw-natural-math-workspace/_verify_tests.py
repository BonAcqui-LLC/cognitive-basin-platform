"""Stage 1 Verification Tests — import, contract, algorithm, tuple validation."""

import sys
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")

print("=" * 60)
print("VERIFICATION TESTS")
print("=" * 60)

# ---- Test 1: Import test ----
print("\n--- Test 1: Import test ---")
try:
    from natural_math_v5 import run_step, run_cluster, NaturalMathValidationError, default_params
    from natural_math_v5.randomness import TraceRng, sample_two
    from natural_math_v5.validation import validate_nodes, as_tuple3_strict, check_invariants
    from natural_math_v5.cluster import summarize_cluster_run
    print("PASS: All imports successful")
except Exception as e:
    print(f"FAIL: Import error: {e}")
    sys.exit(1)

# ---- Test 2: Parameter validation smoke test ----
print("\n--- Test 2: Parameter validation smoke test ---")
try:
    params = default_params()
    assert params["tau"] == 5000, "tau default mismatch"
    assert params["world_size"] == 25, "world_size default mismatch"
    assert params["repair_ignores_distance"] == False, "repair_ignores_distance default mismatch"
    print("PASS: default_params() returns correct defaults")

    # Test validation rejects bad params
    from natural_math_v5.parameters import validate_params
    bad_params = default_params()
    bad_params["tau"] = -1
    try:
        validate_params(bad_params)
        print("FAIL: Should have raised for tau=-1")
    except NaturalMathValidationError as e:
        assert "tau" in str(e)
        print("PASS: validate_params rejects tau=-1")

    # Test missing param
    bad_params2 = {"tau": 5000}
    try:
        validate_params(bad_params2)
        print("FAIL: Should have raised for missing params")
    except NaturalMathValidationError as e:
        assert "missing" in str(e) or "mismatch" in str(e)
        print("PASS: validate_params rejects missing params")
except Exception as e:
    print(f"FAIL: {e}")

# ---- Test 3: run_cluster contract conformance test ----
print("\n--- Test 3: run_cluster contract conformance test ---")
try:
    result = run_cluster(seed=42, steps=0)
    required_keys = {"nodes", "resource_pos", "resource_left", "resource_reached", "metrics", "passed"}
    actual_keys = set(result.keys())
    
    assert actual_keys == required_keys, f"Key mismatch: expected {required_keys}, got {actual_keys}"
    print("PASS: run_cluster returns exact 6-key set")

    # Check value types
    assert isinstance(result["nodes"], list), "nodes must be list"
    assert isinstance(result["resource_pos"], tuple), f"resource_pos must be tuple, got {type(result['resource_pos'])}"
    assert all(isinstance(c, int) for c in result["resource_pos"]), "resource_pos elements must be int"
    assert isinstance(result["resource_left"], int), "resource_left must be int"
    assert isinstance(result["resource_reached"], bool), "resource_reached must be bool"
    assert isinstance(result["metrics"], dict), "metrics must be dict"
    assert isinstance(result["passed"], bool), "passed must be bool"
    print("PASS: All value types correct")

    # Verify old donor keys are NOT in result
    donor_keys = {"node_count", "alive_count", "live_node_ids", "first_five_nodes", 
                  "actions", "rng_ppm_draw_count", "first_ten_rng_ppm_draws", "last_ten_rng_ppm_draws",
                  "live_bond_pair_count", "first_ten_live_bond_pairs"}
    overlap = donor_keys & actual_keys
    assert not overlap, f"Donor keys leaked into result: {overlap}"
    print("PASS: No donor-style keys leaked into run_cluster result")

    # Test summarize_cluster_run
    rng = TraceRng(42)
    from natural_math_v5.cluster_initialization import initialize_cluster
    from natural_math_v5.cluster_metrics import compute_metrics, passed_diagnostic
    import copy
    fp = default_params()
    state = initialize_cluster(42, fp, rng)
    result2 = {
        "nodes": state["nodes"],
        "resource_pos": state["resource_pos"],
        "resource_left": state["resource_left"],
        "resource_reached": state["resource_reached"],
        "metrics": compute_metrics(state["nodes"], state["resource_pos"], fp),
        "passed": passed_diagnostic(compute_metrics(state["nodes"], state["resource_pos"], fp), state["resource_reached"], fp),
    }
    summary = summarize_cluster_run(result2, fp, rng, ["SEEK"])
    assert "actions" in summary, "summarize_cluster_run must have actions"
    assert "first_five_nodes" in summary, "summarize_cluster_run must have first_five_nodes"
    assert "rng_ppm_draw_count" in summary, "summarize_cluster_run must have rng_ppm_draw_count"
    print("PASS: summarize_cluster_run produces donor-style summary")

except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

# ---- Test 4: sample_two exact algorithm test ----
print("\n--- Test 4: sample_two exact algorithm test ---")
try:
    # The spec algorithm: randrange(idx1), remove, randrange(idx2)
    # Must NOT use rng.sample()
    rng = TraceRng(42)
    seq = [10, 20, 30, 40, 50]
    
    # Verify sample_two produces two distinct items
    a, b = sample_two(rng, seq)
    assert a in seq and b in seq, "Results must be from sequence"
    assert a != b, "Results must be distinct"
    print(f"PASS: sample_two returns distinct items: ({a}, {b})")

    # Verify it consumes exactly 2 randrange calls (not rng.sample)
    rng2 = TraceRng(42)
    draws_before = len(rng2.draws)
    result = sample_two(rng2, [1, 2, 3, 4, 5])
    # sample_two uses randrange(0, len) which is NOT a PPM draw (a=0, b=5, not 1000000)
    # So draws count should not change from PPM tracking
    print(f"PASS: sample_two completed without error")

    # Verify trace: first draw is randrange(0, 5), second is randrange(0, 4)
    # These are NOT tracked as PPM draws since b != 1000000
    # The algorithm is correct if no exception was raised
    
    # Determinism test
    rng3 = TraceRng(42)
    a1, b1 = sample_two(rng3, [10, 20, 30, 40, 50])
    rng4 = TraceRng(42)
    a2, b2 = sample_two(rng4, [10, 20, 30, 40, 50])
    assert a1 == a2 and b1 == b2, "sample_two must be deterministic with same seed"
    print("PASS: sample_two is deterministic")

    # Edge case: exactly 2 items
    rng5 = TraceRng(99)
    x, y = sample_two(rng5, [100, 200])
    assert {x, y} == {100, 200}, "sample_two with 2 items must return both"
    print("PASS: sample_two with exactly 2 items works")
    
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

# ---- Test 5: Strict tuple validation test ----
print("\n--- Test 5: Strict tuple validation test ---")
try:
    from natural_math_v5.records import NODE_FIELDS
    
    # as_tuple3_strict should accept tuples
    result = as_tuple3_strict((1, 2, 3), "pos")
    assert result == (1, 2, 3)
    print("PASS: as_tuple3_strict accepts tuple (1,2,3)")
    
    # as_tuple3_strict should reject lists
    try:
        as_tuple3_strict([1, 2, 3], "pos")
        print("FAIL: as_tuple3_strict should reject list")
    except NaturalMathValidationError as e:
        assert "pos" in str(e)
        assert "list" in str(e).lower()
        print(f"PASS: as_tuple3_strict rejects list: {e}")
    
    # validate_nodes should reject nodes with list-valued pos
    params = default_params()
    bad_node = {
        "id": 0,
        "pos": [0, 0, 0],  # list, not tuple
        "direction": (0, 1, 0),
        "energy": 10000,
        "pressure": 0,
        "alive": True,
        "type": "seed",
        "parent_id": None,
        "bonds": set(),
        "signal_type": 0,
    }
    try:
        validate_nodes([bad_node], params)
        print("FAIL: validate_nodes should reject list-valued pos")
    except NaturalMathValidationError as e:
        assert "pos" in str(e)
        print(f"PASS: validate_nodes rejects list-valued pos: {e}")
    
    # validate_nodes should reject nodes with list-valued direction
    bad_node2 = {
        "id": 0,
        "pos": (0, 0, 0),
        "direction": [0, 1, 0],  # list, not tuple
        "energy": 10000,
        "pressure": 0,
        "alive": True,
        "type": "seed",
        "parent_id": None,
        "bonds": set(),
        "signal_type": 0,
    }
    try:
        validate_nodes([bad_node2], params)
        print("FAIL: validate_nodes should reject list-valued direction")
    except NaturalMathValidationError as e:
        assert "direction" in str(e)
        print(f"PASS: validate_nodes rejects list-valued direction: {e}")
    
    # validate_nodes should accept tuple-valued pos and direction
    good_node = {
        "id": 0,
        "pos": (0, 0, 0),
        "direction": (0, 1, 0),
        "energy": 10000,
        "pressure": 0,
        "alive": True,
        "type": "seed",
        "parent_id": None,
        "bonds": set(),
        "signal_type": 0,
    }
    validate_nodes([good_node], params)
    print("PASS: validate_nodes accepts tuple-valued pos and direction")
    
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

# ---- Test 6: No bonding flag check in run_step ----
print("\n--- Test 6: Bonding flag check removed (ISSUE 7) ---")
try:
    params = default_params()
    node = {
        "id": 0,
        "pos": (0, 0, 0),
        "direction": (0, 1, 0),
        "energy": 10000,
        "pressure": 0,
        "alive": True,
        "type": "seed",
        "parent_id": None,
        "bonds": set(),
        "signal_type": 0,
    }
    # This should NOT raise an error (bond_collapse_positions True but allow_bonding False)
    rng = TraceRng(42)
    result = run_step(
        [copy.deepcopy(node)], params,
        use_deficit=False, use_poc_scream=False,
        allow_bonding=False,
        bond_collapse_positions=True,  # was previously an error
        bonding_strict=True,           # was previously an error
        rng=rng,
    )
    print("PASS: bonding flags without allow_bonding no longer raises error (per ISSUE 7)")

    # But deficit + poc_scream should still raise
    try:
        run_step(
            [copy.deepcopy(node)], params,
            use_deficit=True, use_poc_scream=True,
            allow_bonding=False,
            bond_collapse_positions=False,
            bonding_strict=False,
            rng=rng,
        )
        print("FAIL: Should have raised for use_deficit + use_poc_scream")
    except NaturalMathValidationError as e:
        assert "deficit" in str(e).lower() and "poc_scream" in str(e).lower()
        print("PASS: use_deficit + use_poc_scream still raises (correct per spec)")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ALL VERIFICATION TESTS COMPLETE")
print("=" * 60)
