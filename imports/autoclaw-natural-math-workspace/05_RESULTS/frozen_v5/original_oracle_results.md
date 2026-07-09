# Natural Math v5 — Frozen Original Oracle Results

**Runner:** stage_1_1_oracle_runner.py
**Timestamp:** 2026-06-23
**Overall Result:** ✅ PASS

## Summary

| Category | Passed | Total |
|----------|--------|-------|
| Integer Fixtures | 25 | 25 |
| Cluster Fixtures | 15 | 15 |
| **Total** | **40** | **40** |

## Integer Fixtures (25)

| # | Fixture Name | Status | Error |
|---|-------------|--------|-------|
| 0 | empty_list_returns_empty | PASS |  |
| 1 | energy_below_tau_restrict_dies_before_pressure | PASS |  |
| 2 | duplicate_live_position_contact_death | PASS |  |
| 3 | adjacent_live_nodes_sense_and_pressure | PASS |  |
| 4 | integer_gradient_successful_extend | PASS |  |
| 5 | fallback_extend_with_seeded_rng | PASS |  |
| 6 | blocked_fallback_target_pays_sense_and_conflict_pressure | PASS |  |
| 7 | contested_unblocked_fallback_target_high_energy_wins | PASS |  |
| 8 | bifurcation_successful_split_from_fallback_extend | PASS |  |
| 9 | bifurcation_pressure_below_threshold_moves_normally | PASS |  |
| 10 | bifurcation_energy_threshold_must_be_strictly_greater | PASS |  |
| 11 | bifurcation_child_position_blocked_by_frozen_occupancy | PASS |  |
| 12 | bifurcation_child_position_outside_boundary_moves_normally | PASS |  |
| 13 | bifurcation_reserved_child_position_blocks_later_split | PASS |  |
| 14 | bonding_adjacent_pair_forms_after_pressure_and_equalizes_energy | PASS |  |
| 15 | bonding_strict_rejects_distance_equal_to_threshold | PASS |  |
| 16 | bonding_non_strict_allows_distance_equal_to_threshold | PASS |  |
| 17 | bonding_max_live_degree_blocks_extra_pairs | PASS |  |
| 18 | bonding_historical_dead_bonds_do_not_count_against_live_capacity | PASS |  |
| 19 | bonding_collapse_positions_keeps_bonded_duplicate_live_nodes_alive | PASS |  |
| 20 | deficit_mode_can_reverse_gradient_direction | PASS |  |
| 21 | deficit_mode_is_zero_when_both_nodes_at_or_above_E0 | PASS |  |
| 22 | poc_scream_low_energy_neighbor_uses_suffering_strength | PASS |  |
| 23 | poc_scream_disables_bifurcation_and_extends_normally | PASS |  |
| 24 | validation_rejects_deficit_and_poc_scream_together | PASS |  |

## Cluster Fixtures (15)

### Initialization (2)

| # | Fixture Name | Status | Error |
|---|-------------|--------|-------|
| 0 | cluster_seed_3_initialization_summary | PASS |  |
| 1 | cluster_seed_11_initialization_summary | PASS |  |

### Metrics (3)

| # | Fixture Name | Status | Error |
|---|-------------|--------|-------|
| 0 | cluster_metrics_empty_state | PASS |  |
| 1 | cluster_metrics_connected_success_low_gini | PASS |  |
| 2 | cluster_metrics_fragmented_high_gini_far_resource | PASS |  |

### Action (5)

| # | Fixture Name | Status | Error |
|---|-------------|--------|-------|
| 0 | cluster_action_policy_seek_moves_toward_resource | PASS |  |
| 1 | cluster_action_policy_rest_adds_rest_gain | PASS |  |
| 2 | cluster_action_redistribute_transfers_energy_over_live_bond | PASS |  |
| 3 | cluster_action_policy_repair_fragmented_adds_first_valid_bond | PASS |  |
| 4 | cluster_resource_absorption_shares_integer_energy | PASS |  |

### Damage (1)

| # | Fixture Name | Status | Error |
|---|-------------|--------|-------|
| 0 | cluster_damage_loses_energy_and_breaks_seeded_bonds | PASS |  |

### Run (4)

| # | Fixture Name | Status | Error |
|---|-------------|--------|-------|
| 0 | cluster_seed_3_steps_0_exact_result | PASS |  |
| 1 | cluster_seed_3_steps_1_exact_result | PASS |  |
| 2 | cluster_seed_3_steps_35_damage_gate_exact_result | PASS |  |
| 3 | cluster_seed_3_steps_140_exact_result | PASS |  |

## Notes

- All fixtures are frozen oracle fixtures from the v5 specification.
- Comparisons are exact: energy, position, alive status, bonds, pressure, direction.
- Integer fixtures use `run_step()` from the clean package.
- Cluster fixtures use the clean package's `initialize_cluster()`, `compute_metrics()`, cluster actions, and `cluster_step()`.
