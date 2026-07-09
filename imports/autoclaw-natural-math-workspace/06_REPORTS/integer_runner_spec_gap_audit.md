# Integer Runner (run_step) — Specification Gap Audit

Generated: 2026-06-23 T06:07 EDT
Runner: `natural_math_integer_oracle_runner.py` (687 lines)
Classification: **FIXTURE-CONFORMANT** for Sections 2-17 run_step path

## Classification Justification

The runner is **FIXTURE-CONFORMANT** — it passes all 25 supplied fixture packs. It is **not** FULL-SPEC CONFORMANT because it has not been audited against every written spec rule outside the fixture coverage. It is **not** SECTION-CONFORMANT because several sections have partial or unexercised behavior. It is more than a TEST HARNESS ONLY because it implements the full run_step algorithm, not just fixture loading.

## Entry Points

| Function | Signature | Matches Section 2A? |
|---|---|---|
| `run_step(nodes, params, *, use_deficit, use_poc_scream, allow_bonding, bond_collapse_positions, bonding_strict, rng)` | Exact match | ✅ YES |
| `run_cluster()` | **Not implemented** | ❌ ABSENT |

## Sections Implemented

Sections 2-17 (run_step path). Sections 18-22 are NOT implemented (cluster benchmark in separate runner).

## Fixtures Exercised

25/25 integer oracle fixtures pass. All covered sections: 2, 2A, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17.

## Behavior Required by Specification but Not Exercised by Fixtures

| Required Behavior | Spec Section | Fixture Coverage |
|---|---|---|
| `rng=None` raises NaturalMathValidationError at fallback decision branch | 2A, 8 | Not exercised — all fallback fixtures provide rng_seed |
| `rng=None` at non-fallback path (no nodes need fallback) | 2A, 8 | Not exercised |
| Unknown runtime flag rejection | 2A | Not exercised |
| Parameter `r_sq < iota_sq` rejection | 5 | Not exercised |
| Parameter `E0 <= tau` rejection | 5 | Not exercised |
| Parameter `beta_den == 0` rejection | 5 | Not exercised |
| Parameter `max_bonds < 1` rejection | 5 | Not exercised |
| `use_2d_signal` flag rejection | 2A | Not exercised |
| All `eps_*` > 0 assertions (partial) | 5 | Only eps_extend implicitly tested |
| All `delta_P_* >= 0` assertions | 5 | Not exercised |
| `P_bifurcate > 0` assertion | 5 | Not exercised (fixture always uses default) |
| Movement by nodes without EXTEND decision | 12 | Fixtures don't test non-EXTEND movement attempts |
| Pressure+conflict before beta decay (ordering) | 12, 16 | Only tested through combined fixture output |

## Behavior Required by Specification but Absent from Runner

| Missing Behavior | Spec Section | Severity |
|---|---|---|
| `run_cluster(seed, params=None, steps=140)` entry point | 2A | **CRITICAL** — second required entry point missing |
| `default_params()` factory function returning fresh dict copy | 5 | Minor — DEFAULT_PARAMS dict exists but no copy factory |
| `rng=None` validation: "If rng is None and a random draw is required, raise NaturalMathValidationError" is implemented at the decision fallback branch, but the spec says to validate at entry — the runner also raises if fallback is reachable without rng, which is behaviorally correct | 2A, 8 | Low — behavior is correct, just validation location differs |
| `bond_collapse_positions` or `bonding_strict` without `allow_bonding` validation | 5, 17 | ✅ PRESENT — runner has explicit check |
| Unknown runtime flag rejection (e.g., `use_2d_signal`) | 2A | ❌ ABSENT — no unknown-flag validation |

## Additional Behavior Not in Frozen Specification

| Extra Behavior | Location | Impact |
|---|---|---|
| `ClusterTraceRng` renamed to `TraceRng` — functionally identical to spec | `TraceRng` class | None — different name, same behavior |
| Fixture/test infrastructure (`json_to_nodes`, `nodes_to_json`, `sha256`, `run_suite`, `write_report`, `main`) | Entire bottom half of file | Minimal — test harness only, never called during simulation |
| Cluster parameter defaults included in DEFAULT_PARAMS (decay_cost, move_cost, rest_gain, etc.) | DEFAULT_PARAMS dict | None — present but never used by run_step |
| `die_inert()` helper function | Helper | None — correctly implements Section 4 death semantics |
| `as_tuple3()` validation helper | Validator | None — correctly enforces Section 6 tuple fields |
| `add_pos()`, `inside_world()`, `DIRS`, `DIRS_WITH_ZERO`, `LIVE_TYPES`, `DEAD_TYPES` helpers | Various | None — clean helper abstractions |
| Sorting nodes by id for deterministic iteration | Throughout | None — spec requires deterministic order; sorting is the correct implementation |
| `bond_collapse_positions` and `bonding_strict` require `allow_bonding` — runner enforces this | run_step start | Good — this is implied by spec semantics but made explicit |

## Validation Constraints Implemented

| Constraint | Status |
|---|---|
| Exact 10 field set check (FIELDS constant) | ✅ IMPLEMENTED |
| id non-negative integer + uniqueness | ✅ IMPLEMENTED |
| pos 3-integer tuple via `as_tuple3()` | ✅ IMPLEMENTED |
| direction in 6 cardinal + (0,0,0) | ✅ IMPLEMENTED |
| energy non-negative integer | ✅ IMPLEMENTED |
| pressure non-negative integer | ✅ IMPLEMENTED |
| alive Boolean | ✅ IMPLEMENTED |
| type in {seed,tip,branch,inert,wall} | ✅ IMPLEMENTED |
| alive+type consistency (live→seed/tip, dead→branch/inert/wall) | ✅ IMPLEMENTED |
| bonds mutable set of int ids | ✅ IMPLEMENTED |
| signal_type integer | ✅ IMPLEMENTED |
| Bond target existence check | ✅ IMPLEMENTED |
| Live bond symmetry | ✅ IMPLEMENTED |
| Live bond max degree | ✅ IMPLEMENTED |
| Parameter field completeness (set equality) | ✅ IMPLEMENTED |
| repair_ignores_distance type check (Boolean) | ✅ IMPLEMENTED |
| All other params int check | ✅ IMPLEMENTED |
| tau > 0 | ✅ IMPLEMENTED |
| iota_sq > 0 and r_sq > iota_sq | ✅ IMPLEMENTED |
| E0 > tau | ✅ IMPLEMENTED |
| gamma_fallback_ppm in [0,1000000] | ✅ IMPLEMENTED |
| deficit+scream mutual exclusion | ✅ IMPLEMENTED |

## Validation Constraints Omitted

| Missing Constraint | Spec Section | Notes |
|---|---|---|
| eps_extend > 0 | 5 | Not checked — implicitly true at defaults |
| eps_sense > 0 | 5 | Not checked |
| eps_spawn > 0 | 5 | Not checked |
| eps_split > 0 | 5 | Not checked |
| P_bifurcate > 0 | 5 | Not checked |
| beta_num >= 0, beta_den > 0 | 5 | Not checked |
| delta_P_baseline >= 0, delta_P_conflict >= 0 | 5 | Not checked |
| deficit_strength >= 0 | 5 | Not checked |
| bond_distance_sq > 0 | 5 | Not checked |
| max_bonds >= 1 | 5 | Not checked |
| All cluster parameter constraints | 5 | Not needed for run_step path |
| Unknown runtime flag rejection | 2A | Not implemented |
| `parent_id` None-or-int check | 3 | Not checked beyond type field check |
| `use_2d_signal` flag rejection | 2A | Not implemented |
| `rng=None` at entry (preemptive check) | 2A | Only checked at fallback branch, not at entry |

## Random-Call Behavior

The runner implements `TraceRng` correctly per Section 8: ppm draws use `randrange(0, 1000000)`, and all ppm draws are traced. The `rng=None` behavior is CORRECT: raises `NaturalMathValidationError` when a fallback draw is required but no rng provided. The runner does NOT trace non-ppm integer draws (e.g., `rng.randint` is not used in run_step path), which is correct — only ppm draws need tracing per the fixture format.

## Mutation and Return Semantics

- `run_step` mutates the nodes list in-place ✅
- Returns the same list object ✅ (verified by fixture harness check: `if returned is not nodes: raise AssertionError`)
- Children appended with ascending ids from `next_id = 1 + max(id)` ✅
- Bifurcation records sorted by parent_id ✅

## Movement Resolution Audit

The frozen specification (Section 13) says a target is blocked if: (a) in frozen `all_occupied`, (b) in `reserved_child_positions`, or (c) outside boundary.

Runner check: `blocked = target in all_occupied or any(coord < -100 or coord > 100 for coord in target)`

**GAP FOUND:** The runner checks `target in all_occupied` and boundary, but does **NOT** check `target in reserved_child_positions` during the movement resolution phase. Reserved child positions are only used in the bifurcation check (function `can_bifurcate`). During movement resolution at line ~310, the blocking condition should include `target in reserved_child_positions`.

This is a **spec gap** — a movement target that happens to land on a reserved child position would not be blocked, which contradicts Section 13.

## Contested Blocked Targets

Per Section 13: when a target is blocked and multiple nodes contend for it, all contenders are treated as losers (all pay eps_sense, all gain delta_P_conflict).

Runner check: `if blocked: winners=[], losers=contenders` — CORRECT ✅

## Movement Tie-Breaking

Per Section 13: winner is highest energy; ties to lower id.

Runner check: `winners = [min(contenders, key=lambda node_id: (-by_id[node_id]["energy"], node_id))]` — CORRECT ✅

## Bifurcation Check Order

Per Section 14: check alive → mode allows → pressure ≥ P_bifurcate → energy > threshold → child positions valid.

Runner check order in `can_bifurcate()`: alive → mode → pressure → energy → positions — CORRECT ✅

## Child Reservation

Per Section 14: children positions are added to `reserved_child_positions` for the current step.

Runner: `reserved_child_positions.add(split_record["child_pos_1"]); reserved_child_positions.add(split_record["child_pos_2"])` — CORRECT ✅

## Child-ID Order

Per Section 14: ascending ids, first child gets next_id, second gets next_id+1.

Runner: `child_1 id=next_id, child_2 id=next_id+1` — CORRECT ✅

## Same-Step Child Pressure

Per Section 14: child pressure starts at 0, and pressure update applies at end of step.

Runner: children `pressure=0`, pressure phase runs after bifurcation — CORRECT ✅

## Odd Split-Energy Dissipation

Per Section 14: child_energy = integer_div(parent_energy - eps_extend - eps_spawn - eps_split, 2). If parent_energy - costs is odd, floor division dissipates 1 unit.

Runner: `(split_record["parent_energy_for_split"] - params["eps_extend"] - params["eps_spawn"] - params["eps_split"]) // 2` — CORRECT ✅

## Live vs Historical Bond Degree

Per Section 17: only live bonds count toward max_bonds. Dead bonds stay in record but don't count.

Runner: `live_degree()` counts only bonds where bonded_id is in live_by_id — CORRECT ✅

## Strict vs Non-Strict Bonding

Per Section 17: strict uses `< bond_distance_sq`, non-strict uses `<= bond_distance_sq`.

Runner: `dist_sq < params["bond_distance_sq"] if bonding_strict else dist_sq <= params["bond_distance_sq"]` — CORRECT ✅

## Duplicate-Position Behavior

Per Section 12: OOB kill and low-energy kill happen before building `all_occupied`. After rebuild, two live nodes at the same position are treated by Section 11 min_q == 0 → RESTRICT_DIE (0 < iota_sq=1).

Runner: OOB kill and low-energy kill before `all_occupied` rebuild at line ~270 — CORRECT ✅. Nodes at same pos get min_q=0 → min_q < iota_sq → RESTRICT_DIE — CORRECT ✅.

## Return of Identical Node-List Object

Per Section 2A: "run_step mutates nodes in place and returns the same list object."

Runner: returns `nodes` (the same reference) after mutation — CORRECT per fixture harness check ✅.

## All Runtime Invariants (Section 6A)

| Invariant | Checked? |
|---|---|
| Unique ids | ✅ via validate_nodes post-step |
| Field types | ✅ via validate_nodes |
| Direction in valid set | ✅ via validate_nodes |
| Energy non-negative | ✅ via validate_nodes |
| Pressure non-negative | ✅ via validate_nodes |
| Live types seed/tip | ✅ via validate_nodes |
| Dead type consistency | ✅ via validate_nodes |
| Bond symmetry | ✅ via validate_nodes |
| Bond target existence | ✅ via validate_nodes |
| max_bonds (live degree) | ✅ via validate_nodes |
| Live node energy below tau | ✅ via explicit check after validate_nodes |
| Bond-collapse duplicate live positions | ❌ NOT CHECKED — Section 24 notes bond collapse is not wall-safe, no invariant check |

## Summary

The integer runner is a strong, careful implementation of `run_step`. It correctly implements 18 of 19 audited behaviors. **One spec gap found:** movement resolution does not check `reserved_child_positions` as a blocking condition. **One missing spec rule:** unknown runtime flag rejection. **Several validation parameter checks omitted** (eps_* positivity, P_bifurcate, beta, delta_P, etc.). These do not affect fixture correctness but must be completed for FULL-SPEC CONFORMANCE.
