# Stage 1.1 — Section 5 Parameter Constraint Matrix

Generated: 2026-06-23
Spec: Frozen v5, Section 5
Tests: 04_TESTS/layer_b_conformance/test_parameters.py (200 tests)

| # | Parameter | Constraint | Spec Section | Test Function | Valid Boundary | Invalid Boundary | Status |
|---|-----------|-----------|-------------|---------------|----------------|------------------|--------|
| 1 | (all) | exact 38-key set | 5 | test_exact_parameter_set | all 38 keys present | 37 keys | PASS |
| 2 | tau | missing → error | 5 | test_missing_parameter_rejection | tau present | tau absent | PASS |
| 3 | (all 38) | extra key → error | 5 | test_extra_parameter_rejection | exactly 38 keys | 39 keys (bogus) | PASS |
| 4 | tau | integer only | 5 | test_integer_type_enforcement | int | float | PASS |
| 5 | tau | integer only | 5 | test_integer_type_enforcement | int | str | PASS |
| 6 | iota_sq | integer only | 5 | test_integer_type_enforcement | int | float | PASS |
| 7 | iota_sq | integer only | 5 | test_integer_type_enforcement | int | str | PASS |
| 8 | r_sq | integer only | 5 | test_integer_type_enforcement | int | float | PASS |
| 9 | r_sq | integer only | 5 | test_integer_type_enforcement | int | str | PASS |
| 10 | eps_extend | integer only | 5 | test_integer_type_enforcement | int | float | PASS |
| 11 | eps_extend | integer only | 5 | test_integer_type_enforcement | int | str | PASS |
| | ... | (74 type-enforcement tests total for all int params) | 5 | test_integer_type_enforcement | int | float/str | PASS |
| | repair_ignores_distance | Boolean only | 5 | test_repair_ignores_distance_boolean_only | True | 1 | PASS |
| | tau | > 0 | 5 | test_tau_must_be_positive | 1 | 0 | PASS |
| | iota_sq | > 0 | 5 | test_iota_sq_must_be_positive | 1 | 0 | PASS |
| | r_sq | > iota_sq | 5 | test_r_sq_greater_than_iota_sq | iota_sq+1 | iota_sq | PASS |
| | eps_extend | > 0 | 5 | test_eps_extend_positive | 1 | 0 | PASS |
| | eps_sense | > 0 | 5 | test_eps_sense_positive | 1 | 0 | PASS |
| | eps_spawn | > 0 | 5 | test_eps_spawn_positive | 1 | 0 | PASS |
| | eps_split | > 0 | 5 | test_eps_split_positive | 1 | 0 | PASS |
| | E0 | > tau | 5 | test_E0_greater_than_tau | tau+1 | tau | PASS |
| | P_bifurcate | > 0 | 5 | test_P_bifurcate_positive | 1 | 0 | PASS |
| | beta_num | >= 0 | 5 | test_beta_num_non_negative | 0 | -1 | PASS |
| | beta_den | > 0 | 5 | test_beta_den_positive | 1 | 0 | PASS |
| | delta_P_baseline | >= 0 | 5 | test_delta_P_baseline_non_negative | 0 | -1 | PASS |
| | delta_P_conflict | >= 0 | 5 | test_delta_P_conflict_non_negative | 0 | -1 | PASS |
| | gamma_fallback_ppm | [0, 1000000] | 5 | test_gamma_fallback_ppm_range | 500000 | 1000001 | PASS |
| | deficit_strength | >= 0 | 5 | test_deficit_strength_non_negative | 0 | -1 | PASS |
| | bond_distance_sq | > 0 | 5 | test_bond_distance_sq_positive | 1 | 0 | PASS |
| | max_bonds | >= 1 | 5 | test_max_bonds_at_least_one | 1 | 0 | PASS |
| | decay_cost | >= 0 | 5 | test_decay_cost_non_negative | 0 | -1 | PASS |
| | move_cost | >= 0 | 5 | test_move_cost_non_negative | 0 | -1 | PASS |
| | rest_gain | >= 0 | 5 | test_rest_gain_non_negative | 0 | -1 | PASS |
| | trade_rate_num | >= 0 | 5 | test_trade_rate_num_non_negative | 0 | -1 | PASS |
| | trade_rate_den | > 0 | 5 | test_trade_rate_den_positive | 1 | 0 | PASS |
| | trade_cost | >= 0 | 5 | test_trade_cost_non_negative | 0 | -1 | PASS |
| | repair_cost | >= 0 | 5 | test_repair_cost_non_negative | 0 | -1 | PASS |
| | repair_prob_ppm | [0, 1000000] | 5 | test_repair_prob_ppm_range | 500000 | 1000001 | PASS |
| | resource_absorb_rate | > 0 | 5 | test_resource_absorb_rate_positive | 1 | 0 | PASS |
| | resource_radius_sq | > 0 | 5 | test_resource_radius_sq_positive | 1 | 0 | PASS |
| | critical/low/E0 | 0 < critical < low < E0 | 5 | test_critical_low_energy_ordering | 1000,2000,3000 | 2000,1000,3000 | PASS |
| | success_num/den | positive | 5 | test_success_distance_fraction_positive | 1/1 | 0/1 | PASS |
| | gini_num/den | valid | 5 | test_gini_fraction_valid | 1/100 | -1/100 | PASS |
| | world_size | >= 10 | 5 | test_world_size_minimum | 10 | 9 | PASS |
| | damage_energy_loss | >= 0 | 5 | test_damage_energy_loss_non_negative | 0 | -1 | PASS |
| | damage_bond_break_ppm | [0, 1000000] | 5 | test_damage_bond_break_ppm_range | 500000 | 1000001 | PASS |

Total: 200 tests covering all 38 parameters and all stated constraints.
Implementation: natural_math_v5/parameters.py, validate_params()
