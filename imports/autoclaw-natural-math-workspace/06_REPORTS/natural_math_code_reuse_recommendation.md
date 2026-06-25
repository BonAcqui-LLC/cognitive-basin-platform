# Natural Math Code Reuse Recommendation (REVISED)

Generated: 2026-06-23 T05:42 EDT (original)
Revised: 2026-06-23 T06:07 EDT (correction addendum)

## Correction

The original report incorrectly stated that `natural_math_integer_oracle_runner.py` was a complete 40/40 implementation. In fact:

- The integer oracle runner implements **only** `run_step` (Sections 2-17, 25/25 fixtures)
- A separate cluster oracle runner implements the cluster benchmark (Sections 18-22, 15/15 fixtures)
- Neither runner alone implements both `run_step` and `run_cluster`
- Fixture passing (40/40 across two runners) is not the same as full-spec conformance

See `stage_0_correction_addendum.md` for full details.

## Recommendation: Path B+C Revised

**Build a clean v5 reference implementation by integrating both donor runners.**

### Integer Runner (run_step Donor)
- Path: `C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_RUNNERS\natural_math_integer_oracle_runner.py`
- Classification: **FIXTURE-CONFORMANT** — 25/25 fixtures pass
- 2 spec gaps found (reserved_child_positions in movement blocking, unknown flag rejection)
- 9 validation parameter checks omitted (eps_* constraints, P_bifurcate, beta, delta_P, etc.)
- Excellent code quality: clean helpers, correct invariants, proper mutation semantics

### Cluster Runner (run_cluster Donor)
- Path: `C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_RUNNERS\natural_math_cluster_oracle_runner.py`
- Classification: **FIXTURE-CONFORMANT** — 15/15 fixtures pass
- 1 spec gap found (missing `run_cluster(seed, params=None, steps=140)` API wrapper)
- No behavioral gaps in cluster logic
- 0 validation gaps (all cluster invariants enforced post-step)

## Why Not Path A (Correct v3.6)

v3.6 has ~350 lines of float-based code. Correcting it to integer v5 conformance would modify ~80% of lines — a rewrite, not a correction. The gradient, bifurcation, randomness, and parameter systems are fundamentally incompatible. The existing v5 runners are already correct for their respective paths.

## Why Not Path C Alone (Use Existing Runners As-Is)

Neither runner alone exposes both `run_step` and `run_cluster`. They are structured as test harnesses (CLI, JSON fixture loading, report generation). They must be restructured into a clean importable library. The cluster runner does not expose the exact Section 2A `run_cluster` signature.

## Why Not Path D (Stop)

Both v5 entry points have working, fixture-conformant implementations on disk. The path forward is clear: integrate, close gaps, test.

## Reusable v3.6 Components (Unchanged)

| Component | File | Reuse Decision |
|---|---|---|
| CoreNode dataclass structure | v3_6_core.py | **Adapt** — add bonds, signal_type, rename dir→direction, remove T |
| quadrance() concept | v3_6_core.py | **Adapt** — change return type from float to int |
| compute_decision() logic flow | v3_6_core.py | **Adapt** — structural pattern only, all thresholds need integer rewrite |
| step_once() pipeline structure | v3_6_core.py | **Adapt** — basic ordering, but v5 adds 6+ new phases |
| resolve_conflicts() structure | v3_6_core.py | **Adapt** — concept maps to v5 movement resolution, details differ |
| simulate() loop + reporting | v3_6_core.py | **Adapt** — structural pattern for simulation loop and summary generation |

## Incompatible v3.6 Components (Unchanged)

compute_gradient, update_direction, project_to_lattice, bifurcation_children, random_direction, all float comparison helpers, CoreParams defaults, initialize_default, check_invariants (partial).

## Implementation Strategy for Stage 1 (Revised)

1. Extract `run_step` logic from integer runner into clean importable modules
2. Extract cluster initialization, stepping, and metrics from cluster runner
3. Create `run_cluster(seed, params=None, steps=140)` wrapper matching Section 2A
4. **Fix spec gap:** Add `reserved_child_positions` to movement blocking condition
5. **Fix spec gap:** Add unknown runtime flag rejection
6. **Add:** Missing parameter constraint checks (eps_*, P_bifurcate, beta, delta_P, etc.)
7. **Add:** `rng=None` preemptive check at run_step entry
8. Adapt v3.6 reporting patterns (StepStats, SimulationSummary, history)
9. Validate all 40 frozen fixtures still pass
10. Add implementation-conformance tests for new spec coverage
11. Create scale reproduction tests where artifacts permit

## Donor Matrix

| Donor | Sections | Fixtures | Gaps | Can Donate |
|---|---|---|---|---|
| Integer runner | 2-17 | 25/25 | 2 spec + 9 validation | ✅ run_step |
| Cluster runner | 18-22 | 15/15 | 1 API + 0 behavioral | ✅ run_cluster |
| v3.6 core | None (float) | 0/40 | 26 (total incompatibility) | ⚠️ Structural patterns only |

## Status of Research Branches (Unchanged)

v6, v7.2: Research branches, not validated against v5, not reusable now.
Stick/crystal (v4): Historical, MCVA material later.
Persistent attractor/PEFP: Stage 7+ material, must be adapted for v5 integer states.
