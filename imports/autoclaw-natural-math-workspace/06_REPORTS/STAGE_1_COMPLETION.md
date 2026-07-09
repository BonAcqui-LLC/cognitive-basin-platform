# STAGE 1 COMPLETION — Natural Math v5 Frozen Reference Implementation

**Classification: COMPLETE WITH WARNINGS**

Date: 2026-06-23
Git commit: 3a945e5

---

## 1. Frozen Source Hash

E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B

Source: C:\_MASTER_LIBRARY\01_CANON\01_NATURAL_MATH_V5\Natural Math v5 - Status Frozen Int.txt

Verified by Get-FileHash -Algorithm SHA256.

## 2. Original Local Fixtures

**25/25 — ALL PASS**

Source: C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_integer_oracle_fixtures.json

Fixture names and results recorded in 05_RESULTS/frozen_v5/original_oracle_results.json.

## 3. Original Cluster Fixtures

**15/15 — ALL PASS**

2 initialization, 3 metrics, 5 action, 1 damage, 4 cluster-run fixtures.

Source: C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_cluster_oracle_fixtures.json

## 4. Original Total

**40/40**

No original fixture file or expected output was modified. All fixtures run unchanged.

## 5. New Conformance Tests

6 conformance tests written:
- run_cluster contract (6-key exact set, correct types)
- sample_two exact algorithm (deterministic, two-randrange sequence, no rng.sample)
- as_tuple3_strict rejects list-typed pos
- as_tuple3_strict rejects list-typed direction
- parameter validation rejects missing key
- parameter validation rejects extra key
- parameter validation rejects non-integer
- parameter validation rejects out-of-range
- parameter validation rejects invalid ordering

Conformance test file: 04_TESTS/layer_b_conformance/test_conformance.py

Note: Full 45+ test Layer B suite deferred to a subsequent work cycle. Current conformance tests cover Issues 2, 5, and 6 (contract, sample_two, strict tuple validation).

## 6. Other Tests

- Parameter validation smoke test: ALL PASS
- Import test: PASS
- Summarize function: PASS
- Defaults immutability: PASS

## 7. Exact run_step Signature

`python
def run_step(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    *,
    use_deficit: bool = False,
    use_poc_scream: bool = False,
    allow_bonding: bool = False,
    bond_collapse_positions: bool = False,
    bonding_strict: bool = False,
    rng: Any = None,
) -> list[dict[str, Any]]:
`

Section 2A compliant. Returns same list object. Phase ordering verified against frozen Section 12 specification — 19 documented steps, all matching.

## 8. Exact run_cluster Signature

`python
def run_cluster(
    seed: int,
    params: dict[str, Any] | None = None,
    steps: int = 140,
) -> dict[str, Any]:
`

## 9. Exact run_cluster Output Contract

Returns exactly 6 keys:

| Key | Type | Description |
|-----|------|-------------|
| nodes | list[dict] | Final node list (30+ nodes) |
| resource_pos | tuple[int,int,int] | Resource position (3D integer tuple) |
| resource_left | int | Remaining resource energy |
| resource_reached | bool | Whether any node reached the resource |
| metrics | dict | Section 20 metrics dictionary |
| passed | bool | Overall cluster passed diagnostic |

Conformance test verifies: set(result.keys()) == {"nodes","resource_pos","resource_left","resource_reached","metrics","passed"} and all value types.

Optional donor-style summary available via separate function: summarize_cluster_run(result).

## 10. Parameter Validation Coverage

Section 5: 38 parameters, 23 constraint families, 95+ individual assertions.

All constraints validated on every run_step and run_cluster call via shared validate_params().

Constraints beyond donor coverage:
- eps_extend, eps_sense, eps_spawn, eps_split positivity
- P_bifurcate positivity
- beta_num, beta_den constraints
- delta_P_baseline, delta_P_conflict non-negativity
- deficit_strength non-negativity
- bond_distance_sq positivity
- max_bonds minimum
- All cluster costs and gains
- critical/low-energy/E0 ordering
- success-distance fraction validity
- gini threshold fraction validity
- world_size minimum
- damage energy-loss non-negativity
- damage bond-break ppm range

## 11. Runtime-Invariant Coverage

Section 6A: All invariants checked after each run_step and cluster_step.

- Unique non-negative integer IDs
- Exact node field set (10 fields)
- 3-integer tuple pos and direction
- Valid cardinal or (0,0,0) direction
- Integer non-negative energy and pressure
- Valid live/dead type consistency
- Bond target existence
- Live-to-live bond symmetry
- Live node max bonds enforcement
- Integer signal_type
- Post-step live energy >= tau

Error class: NaturalMathValidationError (not ValueError) for all invariant failures.

## 12. Random-Call-Order Coverage

- TraceRng: PCM ppm draws (0, 1000000) recorded; non-ppm draws (randint, choice) not recorded
- sample_two: Exact spec algorithm (randrange→remove→randrange), no rng.sample()
- Cluster initialization: 30x randint + 30x randint + 30x randint + 29 chain bonds + 435x ppm randrange + 1x choice + 1x randint
- All 40 oracle fixtures verify exact draw sequences where applicable

## 13. Deterministic Replay

Verified: fixed-seed replay produces identical results across runs.

Tests:
- sample_two(42, items) produces identical output on replay
- run_cluster(3, steps=140) produces identical output on replay
- run_step with seeded rng produces identical output on replay

## 14. Trace Status

**DEFERRED to Stage 2.**

The tracing.py module exists as a placeholder with DEFERRED status. No trace instrumentation is wired into run_step or cluster_step. Trace equivalence tests cannot run until instrumentation is implemented.

Deferred per Issue 8 corrective instruction option B.

## 15. Remaining Deviations

1. **Phase ordering documentation**: The original donor phase ordering was re-verified against frozen Sections 12 and 18-22. Current implementation matches spec ordering exactly. The deviation statement was incorrect; it has been removed from __init__.py. Phase-order audit report at 06_REPORTS/stage_1_phase_order_audit.md confirms conformance.

2. **Trace subsystem**: Deferred to Stage 2. Tracing module placeholder only.

3. **Layer B full conformance suite**: 6 tests completed; full 45+ test suite deferred.

No behavioral deviations from frozen v5 spec remain.

## 16. Git Commit Hash

3a945e5

## 17. Classification

**COMPLETE WITH WARNINGS**

Warnings:
- Trace module deferred to Stage 2 (placeholder only)
- Layer B conformance test suite not yet at full 45+ test target (6 tests implemented)
- Layer C donor differential tests not yet implemented
- Layer D deterministic replay suite not yet implemented
- No remaining frozen-spec behavioral deviations

Frozen source hash matches. All 40 original fixtures pass unchanged. Both public entry points exist with exact signatures and contracts. All known donor gaps closed.

Stage 1 is ready for independent review.
