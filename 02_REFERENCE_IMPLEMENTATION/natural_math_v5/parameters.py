"""Natural Math v5 reference implementation — parameters.

Frozen spec: Section 5 (Parameters)
"""

from __future__ import annotations

import copy
from typing import Any

from .errors import NaturalMathValidationError

# Section 5: complete parameter table with integer defaults (milli-units)
DEFAULT_PARAMS: dict[str, Any] = {
    "tau": 5000,
    "iota_sq": 1,
    "r_sq": 625,
    "eps_extend": 500,
    "eps_sense": 1200,
    "eps_spawn": 4000,
    "eps_split": 9000,
    "E0": 1600000,
    "P_bifurcate": 12000,
    "beta_num": 85,
    "beta_den": 100,
    "delta_P_baseline": 2100,
    "delta_P_conflict": 5000,
    "gamma_fallback_ppm": 300000,
    "deficit_strength": 15000,
    "suffering_strength": -50000,
    "bond_distance_sq": 4,
    "max_bonds": 4,
    "decay_cost": 220,
    "move_cost": 300,
    "rest_gain": 220,
    "trade_rate_num": 18,
    "trade_rate_den": 100,
    "trade_cost": 25,
    "repair_cost": 350,
    "repair_prob_ppm": 700000,
    "repair_ignores_distance": False,
    "resource_absorb_rate": 14000,
    "resource_radius_sq": 4,
    "critical_energy": 30000,
    "low_energy_cutoff": 38000,
    "success_max_distance_sq_num": 9,
    "success_max_distance_sq_den": 4,
    "gini_threshold_num": 7,
    "gini_threshold_den": 100,
    "world_size": 25,
    "damage_energy_loss": 14000,
    "damage_bond_break_ppm": 180000,
}

# Section 2A: runtime flags and their defaults
RUNTIME_FLAGS = frozenset({
    "use_deficit", "use_poc_scream", "allow_bonding",
    "bond_collapse_positions", "bonding_strict",
})


def default_params() -> dict[str, Any]:
    """Return a fresh copy of DEFAULT_PARAMS. Section 5.

    Callers must not mutate each other's copies.
    """
    return copy.deepcopy(DEFAULT_PARAMS)


def validate_params(params: dict[str, Any]) -> None:
    """Validate all Section 5 parameter constraints.

    Raises NaturalMathValidationError on any violation.
    """
    required = set(DEFAULT_PARAMS)
    actual = set(params)
    if actual != required:
        missing = required - actual
        extra = actual - required
        msg = "Section 5 params: required parameter set mismatch"
        if missing:
            msg += f"; missing: {sorted(missing)}"
        if extra:
            msg += f"; extra: {sorted(extra)}"
        raise NaturalMathValidationError(msg)

    # Integer type check (except repair_ignores_distance)
    for key in required:
        value = params[key]
        if key == "repair_ignores_distance":
            if type(value) is not bool:
                raise NaturalMathValidationError(
                    f"Section 5 {key}: must be Boolean, got {type(value).__name__}"
                )
        elif type(value) is not int:
            raise NaturalMathValidationError(
                f"Section 5 {key}: must be integer, got {type(value).__name__}"
            )

    # Ordered constraints
    if not params["tau"] > 0:
        raise NaturalMathValidationError("Section 5 tau: must be > 0")
    if not params["iota_sq"] > 0:
        raise NaturalMathValidationError("Section 5 iota_sq: must be > 0")
    if not params["r_sq"] > params["iota_sq"]:
        raise NaturalMathValidationError("Section 5 r_sq: must be > iota_sq")
    if not params["eps_extend"] > 0:
        raise NaturalMathValidationError("Section 5 eps_extend: must be > 0")
    if not params["eps_sense"] > 0:
        raise NaturalMathValidationError("Section 5 eps_sense: must be > 0")
    if not params["eps_spawn"] > 0:
        raise NaturalMathValidationError("Section 5 eps_spawn: must be > 0")
    if not params["eps_split"] > 0:
        raise NaturalMathValidationError("Section 5 eps_split: must be > 0")
    if not params["E0"] > params["tau"]:
        raise NaturalMathValidationError("Section 5 E0: must be > tau")
    if not params["P_bifurcate"] > 0:
        raise NaturalMathValidationError("Section 5 P_bifurcate: must be > 0")
    if not params["beta_num"] >= 0:
        raise NaturalMathValidationError("Section 5 beta_num: must be >= 0")
    if not params["beta_den"] > 0:
        raise NaturalMathValidationError("Section 5 beta_den: must be > 0")
    if not params["delta_P_baseline"] >= 0:
        raise NaturalMathValidationError("Section 5 delta_P_baseline: must be >= 0")
    if not params["delta_P_conflict"] >= 0:
        raise NaturalMathValidationError("Section 5 delta_P_conflict: must be >= 0")
    if not 0 <= params["gamma_fallback_ppm"] <= 1000000:
        raise NaturalMathValidationError("Section 5 gamma_fallback_ppm: must be in [0, 1000000]")
    if not params["deficit_strength"] >= 0:
        raise NaturalMathValidationError("Section 5 deficit_strength: must be >= 0")
    # suffering_strength is integer, may be negative (already checked by int type check)
    if not params["bond_distance_sq"] > 0:
        raise NaturalMathValidationError("Section 5 bond_distance_sq: must be > 0")
    if not params["max_bonds"] >= 1:
        raise NaturalMathValidationError("Section 5 max_bonds: must be >= 1")
    # Cluster constraints
    if not params["decay_cost"] >= 0:
        raise NaturalMathValidationError("Section 5 decay_cost: must be >= 0")
    if not params["move_cost"] >= 0:
        raise NaturalMathValidationError("Section 5 move_cost: must be >= 0")
    if not params["rest_gain"] >= 0:
        raise NaturalMathValidationError("Section 5 rest_gain: must be >= 0")
    if not params["trade_rate_num"] >= 0:
        raise NaturalMathValidationError("Section 5 trade_rate_num: must be >= 0")
    if not params["trade_rate_den"] > 0:
        raise NaturalMathValidationError("Section 5 trade_rate_den: must be > 0")
    if not params["trade_cost"] >= 0:
        raise NaturalMathValidationError("Section 5 trade_cost: must be >= 0")
    if not params["repair_cost"] >= 0:
        raise NaturalMathValidationError("Section 5 repair_cost: must be >= 0")
    if not 0 <= params["repair_prob_ppm"] <= 1000000:
        raise NaturalMathValidationError("Section 5 repair_prob_ppm: must be in [0, 1000000]")
    if not params["resource_absorb_rate"] > 0:
        raise NaturalMathValidationError("Section 5 resource_absorb_rate: must be > 0")
    if not params["resource_radius_sq"] > 0:
        raise NaturalMathValidationError("Section 5 resource_radius_sq: must be > 0")
    if not 0 < params["critical_energy"] < params["low_energy_cutoff"] < params["E0"]:
        raise NaturalMathValidationError("Section 5: must have 0 < critical_energy < low_energy_cutoff < E0")
    if not params["success_max_distance_sq_num"] > 0:
        raise NaturalMathValidationError("Section 5 success_max_distance_sq_num: must be > 0")
    if not params["success_max_distance_sq_den"] > 0:
        raise NaturalMathValidationError("Section 5 success_max_distance_sq_den: must be > 0")
    if not params["gini_threshold_num"] >= 0:
        raise NaturalMathValidationError("Section 5 gini_threshold_num: must be >= 0")
    if not params["gini_threshold_den"] > 0:
        raise NaturalMathValidationError("Section 5 gini_threshold_den: must be > 0")
    if not params["world_size"] >= 10:
        raise NaturalMathValidationError("Section 5 world_size: must be >= 10")
    if not 0 <= params["damage_bond_break_ppm"] <= 1000000:
        raise NaturalMathValidationError("Section 5 damage_bond_break_ppm: must be in [0, 1000000]")
    # damage_energy_loss may be any non-negative integer (default 14000)
    if params["damage_energy_loss"] < 0:
        raise NaturalMathValidationError("Section 5 damage_energy_loss: must be >= 0")
