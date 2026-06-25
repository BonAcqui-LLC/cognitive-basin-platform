# FINAL BUILD REPORT — Evolution Prize Lanes

**Generated:** 2026-06-11T20:49:51.954228+00:00

## 1. Persistent Attractor Fix

Implemented **pre-step maintenance injection** in `natural_math_persistent_attractor.py`:

- Preview per-step energy cost from `compute_decision`
- Inject `maintenance_energy_rate` (default 8.0) before `step_once` when projected energy ≤ threshold
- Default `maintenance_energy_threshold = 0` (inject before extinction cliff)
- Saves `final_state.json` per run

### Quick test

```json
{
  "maintenance_injections": 49,
  "final_active_count": 2,
  "final_total_energy": 56.6,
  "termination_status": "persistent_hold",
  "pass": true
}
```

## 2. PEFP Results (5 ICs)

- Distinct glyphs: **2**
- H(V): **1.0 bits**
- Collisions: **3**

### Per IC

```json
[
  {
    "ic_id": "ic-0042",
    "glyph": 19519,
    "base_glyph": 9759,
    "tau_E": 1,
    "active_count": 3,
    "maintenance_injections": 31,
    "final_active_count": 3,
    "final_total_energy": 52.6,
    "reaccess": {
      "0.05": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      },
      "0.1": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      },
      "0.15": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      }
    },
    "replay_hit_rate": 1.0
  },
  {
    "ic_id": "ic-0043",
    "glyph": 19519,
    "base_glyph": 9759,
    "tau_E": 1,
    "active_count": 2,
    "maintenance_injections": 29,
    "final_active_count": 2,
    "final_total_energy": 55.0,
    "reaccess": {
      "0.05": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      },
      "0.1": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      },
      "0.15": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      }
    },
    "replay_hit_rate": 1.0
  },
  {
    "ic_id": "ic-0044",
    "glyph": 19519,
    "base_glyph": 9759,
    "tau_E": 1,
    "active_count": 6,
    "maintenance_injections": 27,
    "final_active_count": 6,
    "final_total_energy": 80.4,
    "reaccess": {
      "0.05": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      },
      "0.1": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      },
      "0.15": {
        "hit": true,
        "original_glyph": 19519,
        "observed_glyph": 19519
      }
    },
    "replay_hit_rate": 1.0
  },
  {
    "ic_id": "ic-0045",
    "glyph": 19847,
    "base_glyph": 9923,
    "tau_E": 1,
    "active_count": 56,
    "maintenance_injections": 1,
    "final_active_count": 56,
    "final_total_energy": 158.91,
    "reaccess": {
      "0.05": {
        "hit": false,
        "original_glyph": 19847,
        "observed_glyph": null
      },
      "0.1": {
        "hit": false,
        "original_glyph": 19847,
        "observed_glyph": null
      },
      "0.15": {
        "hit": false,
        "original_glyph": 19847,
        "observed_glyph": null
      }
    },
    "replay_hit_rate": 0.0
  },
  {
    "ic_id": "ic-0046",
    "glyph": 19847,
    "base_glyph": 9923,
    "tau_E": 1,
    "active_count": 32,
    "maintenance_injections": 3,
    "final_active_count": 32,
    "final_total_energy": 129.01,
    "reaccess": {
      "0.05": {
        "hit": false,
        "original_glyph": 19847,
        "observed_glyph": null
      },
      "0.1": {
        "hit": false,
        "original_glyph": 19847,
        "observed_glyph": null
      },
      "0.15": {
        "hit": false,
        "original_glyph": 19847,
        "observed_glyph": null
      }
    },
    "replay_hit_rate": 0.0
  }
]
```

## 3. Replay Hit Rates

- ICs with hit rate ≥ 0.95: **3**
- Max hit rate: **1.0**

## 4. Chemical Hopfield ODE

```json
{
  "lane": "chemical_hopfield_ode",
  "status": "FAIL",
  "substrate": "chemical_ode_hill_hopfield",
  "seed": 42,
  "N": 1024,
  "M": 54,
  "alpha": 0.0527,
  "beta": 2.0,
  "lambda_separation": 0.9216,
  "entropy_HV_bits": 7.1931,
  "collision_count": 0,
  "vocabulary_size": 232,
  "mean_replay_hit_rate": 0.9216,
  "shuffled_hit_rate": 0.0,
  "passes_prize_thresholds": false,
  "target_benchmark": {
    "lambda": 1.0,
    "entropy_HV": 5.755,
    "collisions": 0,
    "replay": 1.0
  },
  "matches_benchmark": false
}
```

Matches discrete benchmark (Λ≈1.0, H(V)≈5.755, 0 collisions): **False**

## 5. Overall Status

| Lane | Status |
|------|--------|
| Persistent attractor + PEFP | FAIL |
| Chemical Hopfield ODE | FAIL |
| Guardian | SUPPORT_ONLY |
| Hopfield benchmark | BENCHMARK_ONLY |

## 6. Prize Submission Readiness

**Prize submission ready: NO**

Chemical Hopfield ODE did not meet all thresholds in this execution. Persistent attractor lane does not meet H(V) ≥ 5 or full replay criteria with N=5 ICs.
