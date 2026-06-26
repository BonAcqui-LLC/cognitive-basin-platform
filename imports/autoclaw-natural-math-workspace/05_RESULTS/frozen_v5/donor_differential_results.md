# Natural Math v5 — Donor Differential Results

**Date:** 2026-06-23
**Clean Package:** `natural_math_v5` @ `C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION`

## Overall Summary

| Metric | Count |
|--------|-------|
| Total cases compared | 66 |
| Matching (identical) | 60 |
| Diverging | 6 |
| Diverging-but-correct | 6 |

## Expected Divergence Rules

These are CORRECT divergences where the clean package fixes donor gaps:

| # | Rule | Spec Section | Description |
|---|------|-------------|-------------|
| 1 | `reserved_child_positions` | Section 12 | Clean blocks movement into reserved child positions; donor omits this check |
| 2 | `parameter_validation_complete` | Section 5 | Clean validates all 32 parameters exhaustively; donor checks only subset |
| 3 | `strict_tuple_validation` | Section 6 | Clean requires tuples for pos/direction; donor accepts lists |

## Part A: Local/Integer Donor Comparison (25 Fixtures)

- **Total:** 25
- **Matching:** 25
- **Diverging:** 0
- **Diverging-but-correct:** 0

| Fixture | Matched | Divergences | Classification |
|---------|---------|-------------|----------------|
| ✅ `empty_list_returns_empty` | Yes | 0 | — |
| ✅ `energy_below_tau_restrict_dies_before_pressure` | Yes | 0 | — |
| ✅ `duplicate_live_position_contact_death` | Yes | 0 | — |
| ✅ `adjacent_live_nodes_sense_and_pressure` | Yes | 0 | — |
| ✅ `integer_gradient_successful_extend` | Yes | 0 | — |
| ✅ `fallback_extend_with_seeded_rng` | Yes | 0 | — |
| ✅ `blocked_fallback_target_pays_sense_and_conflict_pressure` | Yes | 0 | — |
| ✅ `contested_unblocked_fallback_target_high_energy_wins` | Yes | 0 | — |
| ✅ `bifurcation_successful_split_from_fallback_extend` | Yes | 0 | — |
| ✅ `bifurcation_pressure_below_threshold_moves_normally` | Yes | 0 | — |
| ✅ `bifurcation_energy_threshold_must_be_strictly_greater` | Yes | 0 | — |
| ✅ `bifurcation_child_position_blocked_by_frozen_occupancy` | Yes | 0 | — |
| ✅ `bifurcation_child_position_outside_boundary_moves_normally` | Yes | 0 | — |
| ✅ `bifurcation_reserved_child_position_blocks_later_split` | Yes | 0 | — |
| ✅ `bonding_adjacent_pair_forms_after_pressure_and_equalizes_energy` | Yes | 0 | — |
| ✅ `bonding_strict_rejects_distance_equal_to_threshold` | Yes | 0 | — |
| ✅ `bonding_non_strict_allows_distance_equal_to_threshold` | Yes | 0 | — |
| ✅ `bonding_max_live_degree_blocks_extra_pairs` | Yes | 0 | — |
| ✅ `bonding_historical_dead_bonds_do_not_count_against_live_capacity` | Yes | 0 | — |
| ✅ `bonding_collapse_positions_keeps_bonded_duplicate_live_nodes_alive` | Yes | 0 | — |
| ✅ `deficit_mode_can_reverse_gradient_direction` | Yes | 0 | — |
| ✅ `deficit_mode_is_zero_when_both_nodes_at_or_above_E0` | Yes | 0 | — |
| ✅ `poc_scream_low_energy_neighbor_uses_suffering_strength` | Yes | 0 | — |
| ✅ `poc_scream_disables_bifurcation_and_extends_normally` | Yes | 0 | — |
| ✅ `validation_rejects_deficit_and_poc_scream_together` | Yes | 0 | — |

### Divergence Details (Part A)

## Part B: Cluster Donor Comparison

- **Total:** 15
- **Matching:** 15
- **Diverging:** 0

| Kind | Name | Matched | Divergences |
|------|------|---------|-------------|
| initialization | ✅ `cluster_seed_3_initialization_summary` | Yes | 0 |
| initialization | ✅ `cluster_seed_11_initialization_summary` | Yes | 0 |
| cluster_run | ✅ `cluster_seed_3_steps_0_exact_result` | Yes | 0 |
| cluster_run | ✅ `cluster_seed_3_steps_1_exact_result` | Yes | 0 |
| cluster_run | ✅ `cluster_seed_3_steps_35_damage_gate_exact_result` | Yes | 0 |
| cluster_run | ✅ `cluster_seed_3_steps_140_exact_result` | Yes | 0 |
| action | ✅ `cluster_action_policy_seek_moves_toward_resource` | Yes | 0 |
| action | ✅ `cluster_action_policy_rest_adds_rest_gain` | Yes | 0 |
| action | ✅ `cluster_action_redistribute_transfers_energy_over_live_bond` | Yes | 0 |
| action | ✅ `cluster_action_policy_repair_fragmented_adds_first_valid_bond` | Yes | 0 |
| action | ✅ `cluster_resource_absorption_shares_integer_energy` | Yes | 0 |
| damage | ✅ `cluster_damage_loses_energy_and_breaks_seeded_bonds` | Yes | 0 |
| metrics | ✅ `cluster_metrics_empty_state` | Yes | 0 |
| metrics | ✅ `cluster_metrics_connected_success_low_gini` | Yes | 0 |
| metrics | ✅ `cluster_metrics_fragmented_high_gini_far_resource` | Yes | 0 |

### Divergence Details (Part B)

## Part C: Deterministic Generated Cases

### Local Cases

- **Total:** 10
- **Matching:** 10
- **Diverging:** 0

| Name | Seed | Nodes | Flags | Matched | Divergences |
|------|------|-------|-------|---------|-------------|
| ✅ `det_local_seed_42` | 42 | 1 | deficit=True, bonding=True | Yes | 0 |
| ✅ `det_local_seed_77` | 77 | 3 | deficit=False, bonding=False | Yes | 0 |
| ✅ `det_local_seed_123` | 123 | 1 | deficit=False, bonding=True | Yes | 0 |
| ✅ `det_local_seed_555` | 555 | 2 | deficit=False, bonding=True | Yes | 0 |
| ✅ `det_local_seed_999` | 999 | 1 | deficit=False, bonding=True | Yes | 0 |
| ✅ `det_local_seed_1337` | 1337 | 5 | deficit=False, bonding=False | Yes | 0 |
| ✅ `det_local_seed_2024` | 2024 | 4 | deficit=True, bonding=False | Yes | 0 |
| ✅ `det_local_seed_4096` | 4096 | 1 | deficit=True, bonding=False | Yes | 0 |
| ✅ `det_local_seed_7777` | 7777 | 2 | deficit=False, bonding=False | Yes | 0 |
| ✅ `det_local_seed_9999` | 9999 | 1 | deficit=False, bonding=True | Yes | 0 |

### Cluster Cases

- **Total:** 10
- **Matching:** 10
- **Diverging:** 0

| Name | Seed | Steps | Matched | Divergences |
|------|------|-------|---------|-------------|
| ✅ `det_cluster_seed_1_steps_2` | 1 | 2 | Yes | 0 |
| ✅ `det_cluster_seed_2_steps_3` | 2 | 3 | Yes | 0 |
| ✅ `det_cluster_seed_5_steps_6` | 5 | 6 | Yes | 0 |
| ✅ `det_cluster_seed_8_steps_9` | 8 | 9 | Yes | 0 |
| ✅ `det_cluster_seed_13_steps_4` | 13 | 4 | Yes | 0 |
| ✅ `det_cluster_seed_21_steps_2` | 21 | 2 | Yes | 0 |
| ✅ `det_cluster_seed_34_steps_5` | 34 | 5 | Yes | 0 |
| ✅ `det_cluster_seed_55_steps_6` | 55 | 6 | Yes | 0 |
| ✅ `det_cluster_seed_89_steps_10` | 89 | 10 | Yes | 0 |
| ✅ `det_cluster_seed_144_steps_5` | 144 | 5 | Yes | 0 |

## Part D: Explicit Divergence Trigger Tests

These test cases are specifically designed to expose the three expected divergences
where the clean package fixes donor gaps:

- **Total trigger tests:** 6
- **Divergences confirmed:** 6

| Test | Rule | Divergence Confirmed | Donor | Clean |
|------|------|---------------------|-------|-------|
| `reserved_child_positions_blocking` | Section 12 Movement Resolution | ✅ | allows movement (not blocked) | blocks movement (reserved) |
| | | | _Reason:_ When a position is reserved for a bifurcation child, the clean package correctly treats it as blocked. The donor only checks all_occupied and world bounds, missing the reserved_child_positions check.  | |
| `parameter_validation_complete` | Section 5 Parameters | ✅ | accepts eps_extend=0 (no check) | rejects eps_extend=0: Section 5 eps_extend: must be > 0 |
| | | | _Reason:_ The donor's validate_params only checks: tau>0, iota_sq>0 && r_sq>iota_sq, E0>tau, gamma_fallback_ppm in [0,1M], and repair_ignores_distance type. It does NOT check eps_extend>0, eps_sense>0, eps_spaw | |
| `parameter_validation_complete_b` | Section 5 Parameters | ✅ | N/A | N/A |
| `parameter_validation_complete_c` | Section 5 Parameters | ✅ | N/A | N/A |
| `strict_tuple_validation` | Section 6 Node Validation | ✅ | accepts list-typed pos and direction | rejects list-typed inputs: Section 6 pos: must be 3-integer tuple (got list) |
| | | | _Reason:_ The donor's as_tuple3 accepts both list and tuple inputs, converting lists to tuples. The clean package's as_tuple3_strict requires actual Python tuple instances. This is intentional: the spec require | |
| `strict_tuple_validation_direction` | Section 6 Node Validation | ✅ | N/A | N/A |

## Conclusions

1. **Local/Integer comparison:** 25/25 fixtures match exactly. 0 divergences are expected and correct (clean package fixes donor gaps).
2. **Cluster comparison:** 15/15 cases match. Any divergences indicate places where the clean package materially differs from the donor.
3. **Deterministic generated cases:** 20/20 match, confirming behavioral equivalence under controlled conditions.
4. **Explicit divergence triggers:** 6/6 tests confirmed the expected divergences.

### Key Findings

- **reserved_child_positions blocking** (Section 12): The clean package correctly blocks movement into positions reserved for bifurcation children. The donor does not enforce this, allowing conflicting occupancy.
- **Complete parameter validation** (Section 5): The clean package enforces all 32 parameter constraints. The donor only validates a partial subset (tau, iota_sq, r_sq, E0, gamma_fallback_ppm).
- **Strict tuple validation** (Section 6): The clean package requires actual Python `tuple` instances for `pos` and `direction`. The donor accepts both `list` and `tuple`, which can mask fixture preparation errors.

### Clean Package Authoritativeness

All detected divergences are cases where the clean package enforces spec requirements that the donor omits. The clean package result is authoritative in every divergence found.
