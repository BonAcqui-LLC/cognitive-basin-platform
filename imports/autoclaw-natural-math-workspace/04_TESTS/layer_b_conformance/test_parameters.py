"""Gate 2: Section 5 Parameter Validation Conformance Tests."""
import sys, unittest
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
from natural_math_v5 import default_params, NaturalMathValidationError
from natural_math_v5.validation import validate_params

class TestExactParameterSet(unittest.TestCase):
    def test_38_keys_no_more_no_less(self):
        self.assertEqual(len(default_params()), 38)
    def test_exact_key_names_match_default(self):
        p = default_params()
        expected = {"tau","iota_sq","r_sq","eps_extend","eps_sense","eps_spawn","eps_split","E0","P_bifurcate","beta_num","beta_den","delta_P_baseline","delta_P_conflict","gamma_fallback_ppm","deficit_strength","suffering_strength","bond_distance_sq","max_bonds","decay_cost","move_cost","rest_gain","trade_rate_num","trade_rate_den","trade_cost","repair_cost","repair_prob_ppm","repair_ignores_distance","resource_absorb_rate","resource_radius_sq","critical_energy","low_energy_cutoff","success_max_distance_sq_num","success_max_distance_sq_den","gini_threshold_num","gini_threshold_den","world_size","damage_energy_loss","damage_bond_break_ppm"}
        self.assertEqual(set(p.keys()), expected)

class TestExtraParameterRejection(unittest.TestCase):
    def test_extra_key_rejected(self):
        p = default_params(); p["bogus"] = 42
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestTauMustBePositive(unittest.TestCase):
    def test_tau_zero(self):
        p = default_params(); p["tau"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_tau_negative(self):
        p = default_params(); p["tau"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestMissingParameterRejection(unittest.TestCase):
    def _check_missing(self, key):
        p = default_params(); p.pop(key)
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_missing_tau(self): self._check_missing("tau")
    def test_missing_E0(self): self._check_missing("E0")
    def test_missing_iota_sq(self): self._check_missing("iota_sq")
    def test_missing_r_sq(self): self._check_missing("r_sq")
    def test_missing_eps_extend(self): self._check_missing("eps_extend")
    def test_missing_eps_sense(self): self._check_missing("eps_sense")
    def test_missing_eps_spawn(self): self._check_missing("eps_spawn")
    def test_missing_eps_split(self): self._check_missing("eps_split")
    def test_missing_P_bifurcate(self): self._check_missing("P_bifurcate")
    def test_missing_beta_num(self): self._check_missing("beta_num")
    def test_missing_beta_den(self): self._check_missing("beta_den")
    def test_missing_delta_P_baseline(self): self._check_missing("delta_P_baseline")
    def test_missing_delta_P_conflict(self): self._check_missing("delta_P_conflict")
    def test_missing_gamma_fallback_ppm(self): self._check_missing("gamma_fallback_ppm")
    def test_missing_deficit_strength(self): self._check_missing("deficit_strength")
    def test_missing_bond_distance_sq(self): self._check_missing("bond_distance_sq")
    def test_missing_max_bonds(self): self._check_missing("max_bonds")
    def test_missing_decay_cost(self): self._check_missing("decay_cost")
    def test_missing_move_cost(self): self._check_missing("move_cost")
    def test_missing_rest_gain(self): self._check_missing("rest_gain")
    def test_missing_trade_rate_num(self): self._check_missing("trade_rate_num")
    def test_missing_trade_rate_den(self): self._check_missing("trade_rate_den")
    def test_missing_trade_cost(self): self._check_missing("trade_cost")
    def test_missing_repair_cost(self): self._check_missing("repair_cost")
    def test_missing_repair_prob_ppm(self): self._check_missing("repair_prob_ppm")
    def test_missing_repair_ignores_distance(self): self._check_missing("repair_ignores_distance")
    def test_missing_resource_absorb_rate(self): self._check_missing("resource_absorb_rate")
    def test_missing_resource_radius_sq(self): self._check_missing("resource_radius_sq")
    def test_missing_critical_energy(self): self._check_missing("critical_energy")
    def test_missing_low_energy_cutoff(self): self._check_missing("low_energy_cutoff")
    def test_missing_success_max_distance_sq_num(self): self._check_missing("success_max_distance_sq_num")
    def test_missing_success_max_distance_sq_den(self): self._check_missing("success_max_distance_sq_den")
    def test_missing_gini_threshold_num(self): self._check_missing("gini_threshold_num")
    def test_missing_gini_threshold_den(self): self._check_missing("gini_threshold_den")
    def test_missing_world_size(self): self._check_missing("world_size")
    def test_missing_damage_energy_loss(self): self._check_missing("damage_energy_loss")
    def test_missing_damage_bond_break_ppm(self): self._check_missing("damage_bond_break_ppm")

class TestIntegerTypeEnforcement(unittest.TestCase):
    def _check_float(self, key):
        p = default_params(); p[key] = float(p[key])
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def _check_str(self, key):
        p = default_params(); p[key] = "bad"
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_tau_float(self): self._check_float("tau")
    def test_tau_str(self): self._check_str("tau")
    def test_iota_sq_float(self): self._check_float("iota_sq")
    def test_iota_sq_str(self): self._check_str("iota_sq")
    def test_r_sq_float(self): self._check_float("r_sq")
    def test_r_sq_str(self): self._check_str("r_sq")
    def test_eps_extend_float(self): self._check_float("eps_extend")
    def test_eps_extend_str(self): self._check_str("eps_extend")
    def test_eps_sense_float(self): self._check_float("eps_sense")
    def test_eps_sense_str(self): self._check_str("eps_sense")
    def test_eps_spawn_float(self): self._check_float("eps_spawn")
    def test_eps_spawn_str(self): self._check_str("eps_spawn")
    def test_eps_split_float(self): self._check_float("eps_split")
    def test_eps_split_str(self): self._check_str("eps_split")
    def test_E0_float(self): self._check_float("E0")
    def test_E0_str(self): self._check_str("E0")
    def test_P_bifurcate_float(self): self._check_float("P_bifurcate")
    def test_P_bifurcate_str(self): self._check_str("P_bifurcate")
    def test_beta_num_float(self): self._check_float("beta_num")
    def test_beta_num_str(self): self._check_str("beta_num")
    def test_beta_den_float(self): self._check_float("beta_den")
    def test_beta_den_str(self): self._check_str("beta_den")
    def test_delta_P_baseline_float(self): self._check_float("delta_P_baseline")
    def test_delta_P_baseline_str(self): self._check_str("delta_P_baseline")
    def test_delta_P_conflict_float(self): self._check_float("delta_P_conflict")
    def test_delta_P_conflict_str(self): self._check_str("delta_P_conflict")
    def test_gamma_fallback_ppm_float(self): self._check_float("gamma_fallback_ppm")
    def test_gamma_fallback_ppm_str(self): self._check_str("gamma_fallback_ppm")
    def test_deficit_strength_float(self): self._check_float("deficit_strength")
    def test_deficit_strength_str(self): self._check_str("deficit_strength")
    def test_bond_distance_sq_float(self): self._check_float("bond_distance_sq")
    def test_bond_distance_sq_str(self): self._check_str("bond_distance_sq")
    def test_max_bonds_float(self): self._check_float("max_bonds")
    def test_max_bonds_str(self): self._check_str("max_bonds")
    def test_decay_cost_float(self): self._check_float("decay_cost")
    def test_decay_cost_str(self): self._check_str("decay_cost")
    def test_move_cost_float(self): self._check_float("move_cost")
    def test_move_cost_str(self): self._check_str("move_cost")
    def test_rest_gain_float(self): self._check_float("rest_gain")
    def test_rest_gain_str(self): self._check_str("rest_gain")
    def test_trade_rate_num_float(self): self._check_float("trade_rate_num")
    def test_trade_rate_num_str(self): self._check_str("trade_rate_num")
    def test_trade_rate_den_float(self): self._check_float("trade_rate_den")
    def test_trade_rate_den_str(self): self._check_str("trade_rate_den")
    def test_trade_cost_float(self): self._check_float("trade_cost")
    def test_trade_cost_str(self): self._check_str("trade_cost")
    def test_repair_cost_float(self): self._check_float("repair_cost")
    def test_repair_cost_str(self): self._check_str("repair_cost")
    def test_repair_prob_ppm_float(self): self._check_float("repair_prob_ppm")
    def test_repair_prob_ppm_str(self): self._check_str("repair_prob_ppm")
    def test_resource_absorb_rate_float(self): self._check_float("resource_absorb_rate")
    def test_resource_absorb_rate_str(self): self._check_str("resource_absorb_rate")
    def test_resource_radius_sq_float(self): self._check_float("resource_radius_sq")
    def test_resource_radius_sq_str(self): self._check_str("resource_radius_sq")
    def test_critical_energy_float(self): self._check_float("critical_energy")
    def test_critical_energy_str(self): self._check_str("critical_energy")
    def test_low_energy_cutoff_float(self): self._check_float("low_energy_cutoff")
    def test_low_energy_cutoff_str(self): self._check_str("low_energy_cutoff")
    def test_success_max_distance_sq_num_float(self): self._check_float("success_max_distance_sq_num")
    def test_success_max_distance_sq_num_str(self): self._check_str("success_max_distance_sq_num")
    def test_success_max_distance_sq_den_float(self): self._check_float("success_max_distance_sq_den")
    def test_success_max_distance_sq_den_str(self): self._check_str("success_max_distance_sq_den")
    def test_gini_threshold_num_float(self): self._check_float("gini_threshold_num")
    def test_gini_threshold_num_str(self): self._check_str("gini_threshold_num")
    def test_gini_threshold_den_float(self): self._check_float("gini_threshold_den")
    def test_gini_threshold_den_str(self): self._check_str("gini_threshold_den")
    def test_world_size_float(self): self._check_float("world_size")
    def test_world_size_str(self): self._check_str("world_size")
    def test_damage_energy_loss_float(self): self._check_float("damage_energy_loss")
    def test_damage_energy_loss_str(self): self._check_str("damage_energy_loss")
    def test_damage_bond_break_ppm_float(self): self._check_float("damage_bond_break_ppm")
    def test_damage_bond_break_ppm_str(self): self._check_str("damage_bond_break_ppm")

class TestRepairIgnoresDistanceBooleanOnly(unittest.TestCase):
    def test_must_be_bool_not_int(self):
        p = default_params(); p["repair_ignores_distance"] = 1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_must_be_bool_not_int_zero(self):
        p = default_params(); p["repair_ignores_distance"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_must_be_bool_not_str(self):
        p = default_params(); p["repair_ignores_distance"] = "False"
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_must_be_bool_not_float(self):
        p = default_params(); p["repair_ignores_distance"] = 0.0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_true_passes(self):
        p = default_params(); p["repair_ignores_distance"] = True
        validate_params(p)
    def test_false_passes(self):
        p = default_params(); p["repair_ignores_distance"] = False
        validate_params(p)

class TestTauMustBePositive(unittest.TestCase):
    def test_tau_zero(self):
        p = default_params(); p["tau"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_tau_negative(self):
        p = default_params(); p["tau"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestIotaSqMustBePositive(unittest.TestCase):
    def test_iota_sq_zero(self):
        p = default_params(); p["iota_sq"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_iota_sq_negative(self):
        p = default_params(); p["iota_sq"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestRSqGreaterThanIotaSq(unittest.TestCase):
    def test_r_sq_equal_to_iota_sq(self):
        p = default_params(); p["iota_sq"] = 5; p["r_sq"] = 5
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_r_sq_less_than_iota_sq(self):
        p = default_params(); p["iota_sq"] = 10; p["r_sq"] = 5
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestEpsExtendPositive(unittest.TestCase):
    def test_eps_extend_zero(self):
        p = default_params(); p["eps_extend"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_eps_extend_negative(self):
        p = default_params(); p["eps_extend"] = -100
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestEpsSensePositive(unittest.TestCase):
    def test_eps_sense_zero(self):
        p = default_params(); p["eps_sense"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_eps_sense_negative(self):
        p = default_params(); p["eps_sense"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestEpsSpawnPositive(unittest.TestCase):
    def test_eps_spawn_zero(self):
        p = default_params(); p["eps_spawn"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_eps_spawn_negative(self):
        p = default_params(); p["eps_spawn"] = -100
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestEpsSplitPositive(unittest.TestCase):
    def test_eps_split_zero(self):
        p = default_params(); p["eps_split"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_eps_split_negative(self):
        p = default_params(); p["eps_split"] = -10
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestE0GreaterThanTau(unittest.TestCase):
    def test_E0_equal_to_tau(self):
        p = default_params(); p["E0"] = 5000; p["tau"] = 5000
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_E0_less_than_tau(self):
        p = default_params(); p["E0"] = 1000; p["tau"] = 5000
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestPBifurcatePositive(unittest.TestCase):
    def test_P_bifurcate_zero(self):
        p = default_params(); p["P_bifurcate"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_P_bifurcate_negative(self):
        p = default_params(); p["P_bifurcate"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestBetaNumNonNegative(unittest.TestCase):
    def test_beta_num_negative(self):
        p = default_params(); p["beta_num"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_beta_num_zero_passes(self):
        p = default_params(); p["beta_num"] = 0; validate_params(p)

class TestBetaDenPositive(unittest.TestCase):
    def test_beta_den_zero(self):
        p = default_params(); p["beta_den"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_beta_den_negative(self):
        p = default_params(); p["beta_den"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestDeltaPBaselineNonNegative(unittest.TestCase):
    def test_delta_P_baseline_negative(self):
        p = default_params(); p["delta_P_baseline"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_delta_P_baseline_zero_passes(self):
        p = default_params(); p["delta_P_baseline"] = 0; validate_params(p)

class TestDeltaPConflictNonNegative(unittest.TestCase):
    def test_delta_P_conflict_negative(self):
        p = default_params(); p["delta_P_conflict"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_delta_P_conflict_zero_passes(self):
        p = default_params(); p["delta_P_conflict"] = 0; validate_params(p)

class TestGammaFallbackPpmRange(unittest.TestCase):
    def test_below_zero(self):
        p = default_params(); p["gamma_fallback_ppm"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_above_max(self):
        p = default_params(); p["gamma_fallback_ppm"] = 1000001
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["gamma_fallback_ppm"] = 0; validate_params(p)
    def test_max_passes(self):
        p = default_params(); p["gamma_fallback_ppm"] = 1000000; validate_params(p)

class TestDeficitStrengthNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["deficit_strength"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["deficit_strength"] = 0; validate_params(p)

class TestBondDistanceSqPositive(unittest.TestCase):
    def test_zero(self):
        p = default_params(); p["bond_distance_sq"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_negative(self):
        p = default_params(); p["bond_distance_sq"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestMaxBondsAtLeastOne(unittest.TestCase):
    def test_zero(self):
        p = default_params(); p["max_bonds"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_negative(self):
        p = default_params(); p["max_bonds"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestDecayCostNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["decay_cost"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["decay_cost"] = 0; validate_params(p)

class TestMoveCostNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["move_cost"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["move_cost"] = 0; validate_params(p)

class TestRestGainNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["rest_gain"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["rest_gain"] = 0; validate_params(p)

class TestTradeRateNumNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["trade_rate_num"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["trade_rate_num"] = 0; validate_params(p)

class TestTradeRateDenPositive(unittest.TestCase):
    def test_zero(self):
        p = default_params(); p["trade_rate_den"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_negative(self):
        p = default_params(); p["trade_rate_den"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestTradeCostNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["trade_cost"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["trade_cost"] = 0; validate_params(p)

class TestRepairCostNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["repair_cost"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["repair_cost"] = 0; validate_params(p)

class TestRepairProbPpmRange(unittest.TestCase):
    def test_below_zero(self):
        p = default_params(); p["repair_prob_ppm"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_above_max(self):
        p = default_params(); p["repair_prob_ppm"] = 1000001
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["repair_prob_ppm"] = 0; validate_params(p)
    def test_max_passes(self):
        p = default_params(); p["repair_prob_ppm"] = 1000000; validate_params(p)

class TestResourceAbsorbRatePositive(unittest.TestCase):
    def test_zero(self):
        p = default_params(); p["resource_absorb_rate"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_negative(self):
        p = default_params(); p["resource_absorb_rate"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestResourceRadiusSqPositive(unittest.TestCase):
    def test_zero(self):
        p = default_params(); p["resource_radius_sq"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_negative(self):
        p = default_params(); p["resource_radius_sq"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestCriticalLowEnergyOrdering(unittest.TestCase):
    def test_critical_equal_low_energy(self):
        p = default_params(); p["critical_energy"] = 30000; p["low_energy_cutoff"] = 30000
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_critical_greater_than_low_energy(self):
        p = default_params(); p["critical_energy"] = 50000; p["low_energy_cutoff"] = 38000
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_low_energy_greater_than_E0(self):
        p = default_params(); p["critical_energy"] = 1000; p["low_energy_cutoff"] = 2000000
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_critical_zero(self):
        p = default_params(); p["critical_energy"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_critical_negative(self):
        p = default_params(); p["critical_energy"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestSuccessDistanceFractionPositive(unittest.TestCase):
    def test_num_zero(self):
        p = default_params(); p["success_max_distance_sq_num"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_num_negative(self):
        p = default_params(); p["success_max_distance_sq_num"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_den_zero(self):
        p = default_params(); p["success_max_distance_sq_den"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_den_negative(self):
        p = default_params(); p["success_max_distance_sq_den"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)

class TestGiniFractionValid(unittest.TestCase):
    def test_gini_threshold_num_negative(self):
        p = default_params(); p["gini_threshold_num"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_gini_threshold_den_zero(self):
        p = default_params(); p["gini_threshold_den"] = 0
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_gini_threshold_den_negative(self):
        p = default_params(); p["gini_threshold_den"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_gini_threshold_num_zero_passes(self):
        p = default_params(); p["gini_threshold_num"] = 0; validate_params(p)

class TestWorldSizeMinimum(unittest.TestCase):
    def test_world_size_nine(self):
        p = default_params(); p["world_size"] = 9
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_world_size_negative(self):
        p = default_params(); p["world_size"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_world_size_ten_passes(self):
        p = default_params(); p["world_size"] = 10; validate_params(p)

class TestDamageEnergyLossNonNegative(unittest.TestCase):
    def test_negative(self):
        p = default_params(); p["damage_energy_loss"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["damage_energy_loss"] = 0; validate_params(p)

class TestDamageBondBreakPpmRange(unittest.TestCase):
    def test_below_zero(self):
        p = default_params(); p["damage_bond_break_ppm"] = -1
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_above_max(self):
        p = default_params(); p["damage_bond_break_ppm"] = 1000001
        with self.assertRaises(NaturalMathValidationError): validate_params(p)
    def test_zero_passes(self):
        p = default_params(); p["damage_bond_break_ppm"] = 0; validate_params(p)
    def test_max_passes(self):
        p = default_params(); p["damage_bond_break_ppm"] = 1000000; validate_params(p)

if __name__ == "__main__":
    unittest.main()
