# Stage 1 Execution Plan: Frozen v5 Executable Reference (REVISED)

Generated: 2026-06-23 T05:42 EDT (original)
Revised: 2026-06-23 T06:07 EDT (correction addendum)

## Correction Summary

The original plan assumed a single 40/40 runner. The corrected finding: v5 has two separate entry points (`run_step` and `run_cluster`) implemented in two separate runners, neither exposing both entry points. Stage 1 must integrate both donors, close spec gaps, and provide a unified importable library.

## Stage 0 Verdict (Corrected)

- **Selected Natural Math authority:** v5 frozen integer base (SHA256 verified)
- **Recommended implementation path:** Path B+C Revised — Integrate both Fixture-Conformant donors
- **Integer runner (run_step):** FIXTURE-CONFORMANT, 25/25, Sections 2-17, 2 spec gaps found
- **Cluster runner (run_cluster):** FIXTURE-CONFORMANT, 15/15, Sections 18-22, 1 API gap found
- **v3.6 reusable:** Structural patterns only (dataclass layout, reporting, pipeline ordering)
- **v3.6 incompatible:** All float arithmetic, 6 missing subsystems
- **v6/v7.2:** Research branches, not reusable now
- **Stick/crystal:** Historical, MCVA material later
- **Persistent attractor/PEFP:** Stage 7+ material
- **SymLan/Construction A+:** Inventoried, Stage 7+ material

## Stage 1 Objective

Establish a unified executable reference implementation that:
1. Exposes both `run_step()` and `run_cluster()` with exact Section 2A signatures
2. Passes all 40 frozen oracles (25 integer + 15 cluster)
3. Closes spec gaps identified in the gap audits
4. Can be imported as a clean library for Stage 2 extension work

## Starting Points

**Primary donor (run_step):** `C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_RUNNERS\natural_math_integer_oracle_runner.py` (687 lines)
**Primary donor (run_cluster):** `C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_RUNNERS\natural_math_cluster_oracle_runner.py` (~550 lines)
**Structural donor:** `C:\Users\moop\FractalishBuild\fractalish-ai\fractalish_ai\natural_math\v3_6_core.py` (reporting patterns only)

## Phase 1: Extract and Integrate Donors

### Step 1.1: Create Unified Package Structure
Write the following modules under `natural_math_v5/`:

```
natural_math_v5/
  __init__.py          — exports run_step, run_cluster, default_params, NaturalMathValidationError
  params.py            — DEFAULT_PARAMS dict + validate_params + constraints (merged from both runners)
  node.py              — node field definitions, FIELDS set, LIVE_TYPES, DEAD_TYPES, die_inert()
  validation.py        — validate_nodes + check_invariants (merged from both runners)
  helpers.py           — qdist, sign, dot, clamp_nonnegative, integer_div, add_pos, inside_world
  gradient.py          — gradient_direction (from integer runner, exact rational)
  decisions.py         — contact rules, decision dispatch (from integer runner)
  run_step.py          — full 18-step run_step pipeline (from integer runner)
  bonding.py           — apply_bonding, live_degree (from integer runner)
  deficit.py           — deficit computation (from integer runner)
  cluster_init.py      — initialize_cluster (from cluster runner)
  cluster_step.py      — cluster_step pipeline (from cluster runner)
  cluster_metrics.py   — compute_metrics, connected_components (from cluster runner)
  cluster_actions.py   — apply_seek, apply_redistribute, apply_repair, apply_rest, apply_resource_absorption (from cluster runner)
  cluster_damage.py    — apply_damage (from cluster runner)
  cluster.py           — run_cluster(seed, params=None, steps=140) wrapper
```

### Step 1.2: Create run_cluster Wrapper
Write `cluster.py` with exact Section 2A signature:

```python
def run_cluster(seed, params=None, steps=140):
    # Validate seed is int
    # Validate steps is non-negative int  
    # params = copy.deepcopy(default_params if params is None else params)
    # validate_params(params)
    # rng = ClusterTraceRng(seed)
    # state = initialize_cluster(seed, params, rng)
    # actions = []
    # for step_index in range(1, steps + 1):
    #     actions.append(cluster_step(state, params, rng, step_index))
    # metrics = compute_metrics(state["nodes"], state["resource_pos"], params)
    # return dict per Section 22
```

### Step 1.3: Merge Common Code
Both runners share identical implementations of `qdist()`, `live_degree()`, `live_bond_pairs()`, `DEFAULT_PARAMS`, and `kill_below_tau()`. Merge into shared modules. Both define `ClusterTraceRng` classes with identical behavior — unify into one `TraceRng` class in `helpers.py`.

## Phase 2: Close Spec Gaps

### Step 2.1: Integer Runner Gaps

**Gap 1 — Movement blocking missing reserved_child_positions:**
In `run_step.py` movement resolution, change:
```python
blocked = target in all_occupied or any(coord < -100 or coord > 100 for coord in target)
```
to:
```python
blocked = target in all_occupied or target in reserved_child_positions or any(coord < -100 or coord > 100 for coord in target)
```

**Gap 2 — Unknown runtime flag rejection:**
Add to `run_step()` signature processing:
```python
# After keyword-only args, add:
# (No unknown flags to accept beyond the 5 defined — caller passing extras is a Python TypeError, 
#  but spec requires explicit rejection of use_2d_signal as unknown. Since Python kwargs 
#  naturally prevent this, add explicit guard:)
```
Actually, kwargs naturally prevent unknown flags in Python. The spec requirement is `"use_2d_signal is not an accepted flag. Passing an unknown runtime flag is a caller error."` This is naturally enforced by Python's **kwargs syntax. No additional code needed — document it.

### Step 2.2: Missing Parameter Constraints

Add to `validate_params()`:
```python
eps_extend > 0, eps_sense > 0, eps_spawn > 0, eps_split > 0
P_bifurcate > 0
beta_num >= 0, beta_den > 0
delta_P_baseline >= 0, delta_P_conflict >= 0
deficit_strength >= 0
bond_distance_sq > 0
max_bonds >= 1
```

### Step 2.3: Cluster Wrapper Validation

Add to `run_cluster()`:
```python
if type(seed) is not int:
    raise NaturalMathValidationError("Section 2A seed: must be integer")
if type(steps) is not int or steps < 0:
    raise NaturalMathValidationError("Section 2A steps: must be non-negative integer")
validate_params(params)
```

## Phase 3: Verify Against Oracle Suites

### Step 3.1: Frozen Oracle Regression
- Write `tests/test_integer_oracles.py` — load frozen fixtures, run through run_step, verify 25/25 PASS
- Write `tests/test_cluster_oracles.py` — load frozen fixtures, run through run_cluster, verify 15/15 PASS
- Verify SHA256 of all fixture files matches expected values
- Verify spec SHA256 matches frozen v5

### Step 3.2: Implementation-Conformance Tests
New tests for spec behavior NOT covered by frozen fixtures:

```
tests/test_conformance_validation.py:
  - test_reject_unknown_runtime_flag (documented: Python kwargs natural)
  - test_rng_none_no_fallback_reachable (all nodes EXTEND via gradient, no fallback needed → should succeed)
  - test_rng_none_fallback_needed (gradient zero, no rng → NaturalMathValidationError)
  - test_all_eps_params_positive
  - test_p_bifurcate_positive
  - test_beta_constraints
  - test_delta_p_constraints
  - test_deficit_strength_constraint
  - test_bond_distance_sq_positive
  - test_max_bonds_minimum
  - test_e0_greater_than_tau
  - test_r_sq_greater_than_iota_sq

tests/test_conformance_movement.py:
  - test_movement_blocked_by_reserved_child_position
  - test_movement_blocked_by_frozen_occupancy
  - test_movement_blocked_by_boundary
  - test_contested_blocked_target_all_losers
  - test_tie_break_by_energy_then_id
  - test_return_identical_list_object

tests/test_conformance_cluster.py:
  - test_run_cluster_params_none_uses_defaults
  - test_run_cluster_seed_not_int
  - test_run_cluster_steps_negative
  - test_run_cluster_steps_zero
  - test_run_cluster_steps_140
  - test_run_cluster_deterministic_replay
  - test_cluster_metrics_empty
  - test_cluster_metrics_single_node_gini_zero
  - test_cluster_metrics_all_equal_energy_gini_zero
```

### Step 3.3: Scale Gate Verification (Optional)
- Read scale gate evidence from `02_VALIDATION_EVIDENCE/NATURAL_MATH_V5/SCALE_GATE_*/`
- Verify the reference implementation reproduces results where artifacts permit
- Document non-reproducible results

## Phase 4: Structural Improvements

### Step 4.1: Adapt v3.6 Reporting Patterns
- Add `StepStats` dataclass for per-step telemetry
- Add `SimulationSummary` dataclass for end-of-run reporting
- Add `run_simulation(params, seeds, max_steps)` convenience function
- Add `run_cluster_suite(seeds, steps)` batch runner
- Add `compare_runs(run_a, run_b)` for matched-seed A/B comparison (Stage 2 prep)

### Step 4.2: Documentation
- Write `README.md` with quick start, API reference, parameter table, constraint summary
- Write docstrings for all public functions referencing exact spec sections
- Write `CONFORMANCE.md` listing all frozen oracles passed + implementation-conformance test results
- Write `SPEC_GAPS_CLOSED.md` documenting each gap and its resolution

## Phase 5: Deliver Stage 1

### Deliverables
1. `natural_math_v5/` — clean, importable v5 reference implementation package
2. `tests/test_integer_oracles.py` — 25/25 frozen fixtures passing
3. `tests/test_cluster_oracles.py` — 15/15 frozen fixtures passing
4. `tests/test_conformance_*.py` — Implementation-conformance tests passing
5. `README.md` — usage, API, parameter table, constraints
6. `CONFORMANCE.md` — full conformance matrix with provenance
7. `SPEC_GAPS_CLOSED.md` — resolution of all audited gaps
8. `STAGE_1_REPORT.md` — summary of implementation decisions and test results

### Acceptance Criteria
- All 40 frozen oracle fixtures pass with exact matches
- Both entry points match Section 2A signatures exactly
- All audited spec gaps closed
- All implementation-conformance tests pass
- Frozen v5 source unchanged (SHA256 verified)
- Implementation uses integer arithmetic only
- NaturalMathValidationError raised for all documented validation failures
- Library importable (not just script-based)
- Frozen oracle fixtures and expected outputs never modified

## What Stage 1 Does NOT Do (Unchanged)

- No modifications to frozen v5 spec or oracle fixtures
- No new Natural Math behavior beyond v5 spec
- No extension interface (Stage 2)
- No trail memory (Stage 3)
- No scar memory (Stage 4)
- No Cognitive Basin integration (Stage 5)
- No Fractalish runtime (Stage 6)
- No Construction A+ or SymLan (Stage 7)
- No task ladder (Stage 8)
- No activation or product work (Stage 9)

## Resource Estimate (Revised)

| Phase | Work | Lines (est.) |
|---|---|---|
| 1. Extract + Integrate | 15 modules from 2 donor runners | ~900 restructured |
| 2. Close Spec Gaps | Fixes + validation additions | ~100 |
| 3. Verify | Oracle regression + conformance tests | ~400 |
| 4. Improve | Reporting, wrappers, docs | ~300 |
| 5. Deliver | Reports + documentation | ~200 |
| **Total** | | **~1900 lines** |

## Ready to Begin (Corrected)

All Stage 0 preconditions satisfied:
- Natural Math authority selected (v5 frozen)
- Implementation path recommended (B+C Revised, both donors audited)
- Spec gaps identified (3 total across both runners)
- Donor classification complete (both FIXTURE-CONFORMANT)
- Neither donor falsely classified as FULL-SPEC CONFORMANT
- All research branches inventoried and classified
- SymLan/Construction A+ inventoried
- No unresolved blockers

**Stage 1 is ready to begin upon operator approval.**
