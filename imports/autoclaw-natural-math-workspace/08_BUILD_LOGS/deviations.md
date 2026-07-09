# Deviations from Stage 1 Plan

## 1. Module Structure
**Planned**: 22 modules including invariants.py
**Actual**: 21 modules; invariants.py merged into validation.py
**Reason**: check_invariants logically belongs with validate_nodes in validation module.
Both perform data integrity checks. Separation added unnecessary import complexity.

## 2. Cluster Output Format
**Planned**: Section 22 exact dictionary shape
**Actual**: Donor summarize_cluster_result shape (expanded)
**Reason**: Oracle fixtures expect donor-specific fields (first_five_nodes, rng_ppm_draw_count,
first_ten_rng_ppm_draws, last_ten_rng_ppm_draws, live_bond_pair_count). 
A minimal Section 22 dict would fail oracle comparison.

## 3. Phase Ordering in core_step
**Planned**: Section 12 document ordering (bifurcation check after movement attempts)
**Actual**: Donor ordering (bifurcation interleaved with EXTEND decisions)
**Reason**: Section 12 describes phases conceptually; the donor embodies the actual
execution order that produces correct oracle results. The bifurcation check must occur
within the EXTEND decision loop so that bifurcating nodes skip movement scheduling.

## 4. compute_decision Extraction
**Planned**: Separate compute_decision function in decisions.py
**Actual**: Decision logic inline in core_step.run_step
**Reason**: Phase ordering interleaves decision computation with movement scheduling.
Extracting would require passing mutable accumulators (movement_attempts, decisions)
back and forth, reducing clarity.

## 5. resolve_movement Not Called by core_step
**Planned**: Movement resolution extracted to movement.resolve_movement
**Actual**: core_step uses inline movement resolution
**Reason**: Donor inlines the entire movement phase including bidding, winner selection,
and position updates. Extracting would duplicate the donor matching effort.
movement.py remains as a standalone reference but is unused by core_step.

## 6. Cluster Initialization: Random Positions
**Planned**: Ring placement at radius world_size
**Actual**: Random positions within +-2 of center (world_size//2, world_size//2, 0)
**Reason**: Donor uses random placement with randint(-2,2) offsets, not ring placement.
Ring placement was a misreading of the spec.

## 7. Cluster Initialization: 55000 Base Energy
**Planned**: E0 (1,600,000) base energy per node
**Actual**: 55000 + randint(-5000, 5000) per node
**Reason**: Donor uses a fixed base of 55000 for cluster nodes, not E0.
E0 is a local-core parameter; cluster uses its own energy model.

## 8. Bond Probability: 80000 ppm
**Planned**: Arbitrary bond probability
**Actual**: 80000/1000000 (8%) threshold for PPM bond draws
**Reason**: Donor hardcodes 80000 as the bond formation threshold during init.
This is a cluster-internal constant, not derived from any spec parameter.

## Stage 2 — Extension Harness

### 9. Cluster Adapter Reimplements Pipeline
**Planned**: Wrap existing `cluster_step` function through harness hooks.
**Actual**: Full reimplementation of cluster step pipeline in `cluster_adapter.py`.
**Reason**: The harness needs to interleave defensive snapshots and hook dispatches
between sub-steps (decay, kill, damage, action selection, action application,
resource absorption, invariants). A simple wrapper around `cluster_step` would
not provide the granularity needed for extension observation hooks.

### 10. Performance Overhead
**Planned**: Negligible harness overhead (< 5%).
**Actual**: ~1300% overhead in harness modes vs baseline.
**Reason**: The harness creates deep copies (snapshots) of the entire node state
at every hook point. For 140 steps with 5 hook points per step, this means
700+ deep copy operations. This is by design — correctness and isolation are
prioritized over performance. The baseline mode remains available for
performance-sensitive work.

### 11. Hook Result Validation
**Planned**: Hook results validated inline during dispatch.
**Actual**: Adapter records result types without validation; `validate_hook_result`
available as separate utility.
**Reason**: The adapter should not crash the run due to a misbehaving extension.
The validation utility is available for pre-flight and post-hoc checking.
This follows the principle of "be robust in what you accept, strict in what you test."
