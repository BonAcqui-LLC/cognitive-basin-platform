# v3.6 vs v5 Test Crosswalk

Generated: 2026-06-23 T05:42 EDT

## Summary

| Metric | v3.6 Oracles | v5 Integer Oracles | v5 Cluster Oracles | Overlap |
|---|---|---|---|---|
| Count | 8 | 25 | 15 | 0 (zero overlap) |
| Pass status | 8/8 (float) | 25/25 (integer) | 15/15 (integer) | N/A |
| Numeric type | Float | Integer | Integer | — |
| Tested sections | Core movement, contact, bifurcation, pressure, fallback | Sections 2-17 (full run_step) | Sections 18-22 (cluster) | — |

## v3.6 Oracle Coverage (8 tests)

| # | Oracle | What It Tests | v5 Equivalent |
|---|---|---|---|
| 1 | oracle_1_single_seed | Single node extends upward, pays eps_extend | Covered by `integer_gradient_successful_extend` (different params) |
| 2 | oracle_2_contact_equality | Contact at iota_sq=1 causes SENSE not RESTRICT | Covered by `adjacent_live_nodes_sense_and_pressure` (iota_sq=1) |
| 3 | oracle_3_contact_strict | Contact < iota_sq causes RESTRICT | Covered by `duplicate_live_position_contact_death` (iota_sq=1) |
| 4 | oracle_4_bifurcation | Bifurcation creates branch+children under pressure | Covered by `bifurcation_successful_split_from_fallback_extend` |
| 5 | oracle_5_zero_gradient_fallback | Multi-seed symmetric config uses fallback | Covered by `fallback_extend_with_seeded_rng` |
| 6 | oracle_6_bifurcation_colocation | Child positions don't overlap | Covered by `bifurcation_reserved_child_position_blocks_later_split` |
| 7 | oracle_7_pressure_update | SENSE node gets pressure update after step | Covered by `adjacent_live_nodes_sense_and_pressure` |
| 8 | oracle_8_growth_initiation | Fallback enables initial growth | Covered by `fallback_extend_with_seeded_rng` |

## Critical Coverage Gaps in v3.6

### Not Tested by Any v3.6 Oracle
- Integer arithmetic correctness (v3.6 is float, so no integer oracle exists)
- Validation rules (v5 Section 6 — v3.6 has no validation)
- Runtime invariants (v5 Section 6A — v3.6 invariants are different)
- Deficit mode (v5 requires 2 specific deficit oracles)
- PoC scream mode (v5 requires 2 specific scream oracles)
- Bonding (v5 has 5 bonding oracles — v3.6 has no bonding)
- Bond collapse positions
- Bond max capacity
- Historical dead bonds vs live capacity
- Bifurcation energy threshold exact boundary
- Bifurcation child position blocked by frozen occupancy
- Bifurcation child position outside boundary
- Contested movement with high-energy-wins resolution
- Blocked movement with wall node
- Empty node list behavior
- Energy-below-tau death before other phases
- Validation rejects deficit+PoC together
- All 15 cluster oracle categories (initialization, metrics, actions, damage, full runs)

## v3.6 Oracle Semantics Are Not Transferable

The 8 v3.6 oracles all use floating-point arithmetic. Because v5 is integer-only with milli-units, none of the v3.6 oracle data (exact energy values, pressure calculations, gradient magnitudes) can be directly reused. The concepts map (contact, bifurcation, pressure, fallback) but the numbers are different by a factor of 1000 and use different comparison semantics.

## v5 Oracle Categories

### Integer Oracles (25 tests)
| Category | Count | Tests |
|---|---|---|
| Validation | 2 | empty list, deficit+scream conflict |
| Lifecycle | 1 | energy below tau dies |
| Contact | 2 | duplicate position, adjacent SENSE |
| Gradient/Extend | 2 | successful extend, deficit reversal, deficit at E0 |
| Fallback | 2 | fallback extend, blocked fallback |
| Movement contests | 1 | contested target high-energy-wins |
| Bifurcation | 6 | successful split, pressure threshold, energy threshold, blocked child, OOB child, reserved position |
| Pressure | — | Verified within contact/bifurcation fixtures |
| Bonding | 5 | adjacent pair, strict reject, non-strict allow, max degree, dead bonds cap, collapse |
| Deficit | 2 | gradient reversal, zero at E0 |
| PoC Scream | 2 | low-energy neighbor, disables bifurcation |

### Cluster Oracles (15 tests)
| Category | Count | Tests |
|---|---|---|
| Initialization | 2 | seed 3, seed 11 (full state verification) |
| Metrics | 3 | empty state, connected success, fragmented high-gini |
| Actions | 5 | SEEK, REST, REDISTRIBUTE, REPAIR, resource absorption |
| Damage | 1 | energy loss + bond breaking with seeded RNG |
| Full runs | 4 | seed 3 at steps 0, 1, 35 (damage gate), 140 (full run) |

## Conclusion

The v3.6 8/8 oracle suite and the v5 40/40 oracle suite **do not overlap**. They test different semantics (float vs integer) against different specifications. The v5 oracle suite is strictly more comprehensive (40 vs 8 tests) and covers entire categories absent from v3.6 (bonding, cluster, deficit, PoC scream, validation, invariants).

Any conformant v5 implementation must pass all 40 v5 oracles. The v3.6 oracles are not evidence of v5 conformance.
