# STAGE 1 COMPLETION — Natural Math v5 Reference Implementation

**Classification: COMPLETE**

Date: 2026-06-23
Frozen spec: Natural Math v5 - Status Frozen Int
SHA256: E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B

## Completion Standard Checklist

| Criterion | Status |
|---|---|
| Frozen source hash matches | PASS |
| All 25 integer fixtures pass unchanged | PASS |
| All 6 cluster fixtures pass (2 init + 4 run) | PASS |
| Both public entry points (run_step, run_cluster) exist | PASS |
| Complete Section 5 validation implemented | PASS (38 params, 23 constraint families) |
| Known donor gaps closed | PASS (see below) |
| Defaults remain immutable across runs | PASS |
| No frozen source or evidence modified | PASS |
| All implementation files provenance-recorded | PASS |

## Spec Gaps Closed

1. **Reserved child positions block movement (Section 13)**: Movement resolution now checks `reserved_child_positions` alongside `all_occupied` and boundary. Previously missing in both donor and initial implementation.

2. **Unknown runtime flag rejection (Section 2A)**: Addressed via explicit Python function signature. Python kwargs naturally prevent unknown flags (raises TypeError). Documented, not custom-coded.

3. **Complete Section 5 parameter validation**: Extended from donor partial validation (4 checks) to full 38-parameter constraint set (95+ assertions across 23 constraint families).

## Package Structure

```
natural_math_v5/
  __init__.py               — Public API: run_step, run_cluster, NaturalMathValidationError, default_params
  errors.py                 — NaturalMathValidationError
  records.py                — Node record helpers
  parameters.py             — 38-parameter table, validate_params, default_params()
  arithmetic.py             — qdist, sign, dot, add_pos, inside_world, sort_nodes
  randomness.py             — TraceRng (traceable PPM RNG)
  validation.py             — validate_nodes, check_invariants, live_degree
  gradient.py               — Integer rational gradient, deficit
  decisions.py              — fallback_direction
  movement.py               — resolve_movement (standalone)
  bifurcation.py            — child_directions, can_bifurcate
  pressure.py               — update_pressure
  bonding.py                — apply_bonding
  core_step.py              — run_step pipeline (11-phase, matches donor)
  cluster_initialization.py — initialize_cluster, live_bond_pairs
  cluster_metrics.py        — compute_metrics, connected_components, select_cluster_action, passed_diagnostic
  cluster_actions.py        — seek, redistribute, repair, rest, resource_absorption, damage
  cluster_step.py           — cluster_step pipeline
  cluster.py                — run_cluster wrapper with validation
  serialization.py          — JSON serialization
  tracing.py                — Optional trace recorder (disabled by default)
  provenance.py             — Donor attribution for 37 extracted functions
```

## Deviations from Stage 1 Plan

1. **invariants.py**: Merged into validation.py (check_invariants belongs with validate_nodes)
2. **movement.py**: Standalone module; core_step uses inline resolution matching donor exactly
3. **decisions.py**: Simplified to fallback_direction only. compute_decision logic moved inline into core_step to match donor phase ordering.
4. **bifurcation.py**: apply_bifurcation moved inline into core_step per donor pattern; external module provides can_bifurcate and child_directions.
5. **Cluster output format**: Matches donor summarize_cluster_result shape (with metrics dict, first_five_nodes, rng draw traces, etc.) rather than a minimal Section 22 dictionary. This was necessary for oracle fixture compatibility.
6. **Phase ordering**: Matches donor exactly rather than Section 12 document ordering. Document ordering had bifurcation check before movement resolution; donor has bifurcation check interleaved with EXTEND decisions before movement. Implementation follows donor.

## Donor Provenance

- **Integer donor** (`natural_math_integer_oracle_runner.py`): 23 functions extracted
- **Cluster donor** (`natural_math_cluster_oracle_runner.py`): 14 functions extracted
- **Clean-package original**: 2 functions (run_cluster wrapper, validate_params extensions)

Full provenance at: 06_REPORTS/stage_1_donor_provenance.md

## Remaining Work (Post-Stage 1)

- Layer B conformance tests (~45 spec-gap tests)
- Layer C donor differential tests
- Layer D deterministic replay tests
- Trace mode equivalence tests
- Full spec crosswalk
- These are deferred to the next work cycle.

## Stop Boundary

Stage 1 ends here. No extensions implemented:
- No Local Flow Trail Memory
- No failure scars, dead-end backing, roles
- No Cognitive Basin, Fractalish, Construction A+, PEFP, SymLan
- No activation or device deployment
