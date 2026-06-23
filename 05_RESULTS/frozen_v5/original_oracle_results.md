# Natural Math v5 — Stage 1 Oracle Results

**Overall:** PASS (40/40 fixtures)
**Date:** 2026-06-23

## Stage 1 Fixes Applied

- ISSUE 2: run_cluster returns Section 22 contract (6 keys)
- ISSUE 3: Phase ordering verified against spec; __init__.py updated
- ISSUE 4: cluster_step ValueError -> NaturalMathValidationError
- ISSUE 5: sample_two rewritten per spec algorithm (no rng.sample)
- ISSUE 6: as_tuple3_strict rejects lists; validate_nodes strict
- ISSUE 7: Removed non-spec bonding flag check from run_step
- ISSUE 8: tracing.py deferred to Stage 2

## Integer Oracle Fixtures (25)

- **PASS** `empty_list_returns_empty`
- **PASS** `energy_below_tau_restrict_dies_before_pressure`
- **PASS** `duplicate_live_position_contact_death`
- **PASS** `adjacent_live_nodes_sense_and_pressure`
- **PASS** `integer_gradient_successful_extend`
- **PASS** `fallback_extend_with_seeded_rng`
- **PASS** `blocked_fallback_target_pays_sense_and_conflict_pressure`
- **PASS** `contested_unblocked_fallback_target_high_energy_wins`
- **PASS** `bifurcation_successful_split_from_fallback_extend`
- **PASS** `bifurcation_pressure_below_threshold_moves_normally`
- **PASS** `bifurcation_energy_threshold_must_be_strictly_greater`
- **PASS** `bifurcation_child_position_blocked_by_frozen_occupancy`
- **PASS** `bifurcation_child_position_outside_boundary_moves_normally`
- **PASS** `bifurcation_reserved_child_position_blocks_later_split`
- **PASS** `bonding_adjacent_pair_forms_after_pressure_and_equalizes_energy`
- **PASS** `bonding_strict_rejects_distance_equal_to_threshold`
- **PASS** `bonding_non_strict_allows_distance_equal_to_threshold`
- **PASS** `bonding_max_live_degree_blocks_extra_pairs`
- **PASS** `bonding_historical_dead_bonds_do_not_count_against_live_capacity`
- **PASS** `bonding_collapse_positions_keeps_bonded_duplicate_live_nodes_alive`
- **PASS** `deficit_mode_can_reverse_gradient_direction`
- **PASS** `deficit_mode_is_zero_when_both_nodes_at_or_above_E0`
- **PASS** `poc_scream_low_energy_neighbor_uses_suffering_strength`
- **PASS** `poc_scream_disables_bifurcation_and_extends_normally`
- **PASS** `validation_rejects_deficit_and_poc_scream_together`
  - Error: `NaturalMathValidationError: Section 6 runtime flags: use_deficit and use_poc_scream conflict`

**Integer result: 25/25 passed**

## Cluster Oracle Fixtures (15)

- **PASS** `cluster_seed_3_initialization_summary` (cluster_initialization)
- **PASS** `cluster_seed_11_initialization_summary` (cluster_initialization)
- **PASS** `cluster_metrics_empty_state` (cluster_metrics)
- **PASS** `cluster_metrics_connected_success_low_gini` (cluster_metrics)
- **PASS** `cluster_metrics_fragmented_high_gini_far_resource` (cluster_metrics)
- **PASS** `cluster_action_policy_seek_moves_toward_resource` (cluster_action)
- **PASS** `cluster_action_policy_rest_adds_rest_gain` (cluster_action)
- **PASS** `cluster_action_redistribute_transfers_energy_over_live_bond` (cluster_action)
- **PASS** `cluster_action_policy_repair_fragmented_adds_first_valid_bond` (cluster_action)
- **PASS** `cluster_resource_absorption_shares_integer_energy` (cluster_action)
- **PASS** `cluster_damage_loses_energy_and_breaks_seeded_bonds` (cluster_damage)
- **PASS** `cluster_seed_3_steps_0_exact_result` (cluster_run)
- **PASS** `cluster_seed_3_steps_1_exact_result` (cluster_run)
- **PASS** `cluster_seed_3_steps_35_damage_gate_exact_result` (cluster_run)
- **PASS** `cluster_seed_3_steps_140_exact_result` (cluster_run)

**Cluster result: 15/15 passed**

## Provenance

- Runner: `stage_1_comprehensive_runner.py`
- Package: `natural_math_v5` (reference implementation)
- Integer fixtures: `C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_integer_oracle_fixtures.json`
- Cluster fixtures: `C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5\ORACLE_FIXTURES\natural_math_cluster_oracle_fixtures.json`
- Spec: Natural Math v5 - Status Frozen Int
