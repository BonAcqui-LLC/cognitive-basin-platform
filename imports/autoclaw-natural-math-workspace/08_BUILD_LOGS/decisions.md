# Interpretation Decisions — Stage 1

## 1. Unknown Runtime Flags
**Decision**: Python kwargs natural rejection (TypeError) satisfies spec requirement.
**Rationale**: Spec says "unknown runtime flag is a caller error." Python raises TypeError
for unknown keyword arguments automatically. No custom validation needed.
**Tested**: `run_step(nodes, params, bogus_flag=True)` raises TypeError.

## 2. Phase Ordering
**Decision**: Follow donor phase ordering, not Section 12 document ordering.
**Rationale**: Section 12 document order puts bifurcation check after movement attempts
but before movement resolution. Donor interleaves bifurcation with EXTEND decisions,
checking bifurcation eligibility during the decision loop. Following donor matches
all 25 oracles.
**Documented**: In deviations.md.

## 3. Bonded Node Exclusion from Contact
**Decision**: Exclude bonded nodes from contact distance computation.
**Rationale**: Donor explicitly filters `other["id"] not in node["bonds"]` in the
distance computation. This prevents bonded pairs from triggering contact death.
**Spec interpretation**: The spec does not explicitly mention bonded node exclusion,
but the behavior is implied by the bonding system reducing live contact detection.

## 4. SENSE Cost Application
**Decision**: Apply SENSE cost before movement resolution, not during.
**Rationale**: Donor applies eps_sense in a separate phase before movement for all
SENSE nodes. This ensures SENSE nodes pay cost regardless of movement outcome.

## 5. Pressure Baseline in Update Only
**Decision**: delta_P_baseline is applied only in update_pressure, not in movement.
**Rationale**: Donor adds delta_P_baseline solely through the pressure update formula,
not as a movement-phase addition. Movement phase adds only delta_P_conflict to losers.

## 6. Cluster Initialization
**Decision**: Use donor exact initialization (random positions, chain bonds, 435 PPM draws).
**Rationale**: The donor uses a specific RNG call sequence for cluster initialization
that differs from the spec's Section 18-19 description. Following donor RNG order
matches all 6 cluster oracles.

## 7. Cluster Output Format
**Decision**: Return donor summarize_cluster_result shape instead of minimal Section 22 dict.
**Rationale**: Oracle fixtures expect the full shape including first_five_nodes,
rng_ppm_draw_count, first_ten_rng_ppm_draws, etc.

## 8. live_bond_pairs in cluster_initialization
**Decision**: Extract live_bond_pairs to cluster_initialization.py for reuse.
**Rationale**: Used by cluster_actions (redistribute, damage) and cluster runner.
Placing in initialization avoids circular imports.

## 9. Donor Matching Policy
**Decision**: Match donor exactly for all behavioral code; enhance only validation.
**Rationale**: Oracle fixtures encode donor-specific behavior beyond written spec.
Following donor ensures fixture compatibility. Validation is the one area where
extending beyond donor improves compliance without breaking fixtures.

## Stage 2 — Extension Harness

### 10. Adapter Architecture
**Decision**: Implement separate local_adapter and cluster_adapter rather than a unified adapter.
**Rationale**: Local (run_step) and cluster (run_cluster) have different lifecycle phases.
Separate adapters allow cluster-specific hooks (AFTER_CLUSTER_ACTION_SELECTION, etc.)
without complicating the local adapter.

### 11. Hook Dispatch Error Handling
**Decision**: Catch exceptions from extension hooks and log as ERROR events rather than propagating.
**Rationale**: A misbehaving extension should not crash the entire run. Extensions are
observers by contract; their failures should be observable without disrupting the system.

### 12. Non-HookResult Return Handling
**Decision**: Adapter records the type name of whatever the extension returns without validation.
**Rationale**: The adapter layer prioritizes robustness — it should not crash because an
extension returned something unexpected. `validate_hook_result()` is available as a
separate utility for pre-flight checks.

### 13. Cluster Pipeline Reimplementation
**Decision**: `run_cluster_through_harness` reimplements the cluster pipeline step-by-step
rather than wrapping `cluster_step`.
**Rationale**: The harness needs to interleave snapshots and hook dispatches between
sub-steps (decay, damage, action selection, action application, resource absorption,
invariants). Wrapping `cluster_step` would prevent hook visibility into these sub-steps.

### 14. State Isolation via Deep Copy
**Decision**: StateStore deep-copies state on `set_state()` but returns shallow copies on `get_state()`.
**Rationale**: Deep-copy on write guarantees stored state is immutable. Shallow copy on read
is sufficient for scalar/string top-level values and avoids excessive copying.
Nested mutable values share references—documented as a caveat for extensions.
