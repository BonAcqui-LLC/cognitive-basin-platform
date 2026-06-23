"""Natural Math v5 — Frozen Integer Reference Implementation.

Frozen spec: Natural Math v5 - Status Frozen Int
SHA256: E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B

Public API:
  run_step(nodes, params, *, use_deficit=False, ...) -> list[dict]
  run_cluster(seed, params=None, steps=140) -> dict
  NaturalMathValidationError
  default_params

Donors:
  - natural_math_integer_oracle_runner.py (run_step, 25/25 fixtures)
  - natural_math_cluster_oracle_runner.py (cluster behavior, 15/15 fixtures)

Internal module structure:
  errors.py       — NaturalMathValidationError
  records.py      — node record helpers, die_inert, die_branch
  parameters.py   — DEFAULT_PARAMS, validate_params, default_params()
  arithmetic.py   — qdist, sign, dot, add_pos, inside_world
  randomness.py   — TraceRng, sample_two
  validation.py   — validate_nodes, check_invariants, live_degree
  gradient.py     — gradient_direction, deficit
  decisions.py    — fallback_direction
  movement.py     — resolve_movement (standalone; core_step has inline)
  bifurcation.py  — child_directions, can_bifurcate
  pressure.py     — update_pressure
  bonding.py      — apply_bonding
  core_step.py    — run_step pipeline
  cluster_initialization.py — initialize_cluster, live_bond_pairs
  cluster_metrics.py        — compute_metrics, connected_components, etc.
  cluster_actions.py        — seek, redistribute, repair, rest, absorb, damage
  cluster_step.py           — cluster_step pipeline
  cluster.py                — run_cluster wrapper
  serialization.py          — JSON serialization helpers
  tracing.py                — optional trace recorder
  provenance.py             — donor attribution records

Deviations from Stage 1 plan:
  - invariants.py: merged into validation.py (check_invariants)
  - movement.py: standalone module; core_step uses inline resolution matching donor
  - decisions.py: simplified to fallback_direction only (decision logic inline in core_step)
  - bifurcation.py: apply_bifurcation merged inline into core_step per donor pattern
  - cluster output format: matches donor summarize_cluster_result shape (not Section 22 exact)
  - Phase ordering: now matches donor exactly rather than Section 12 document ordering
"""

from .core_step import run_step
from .cluster import run_cluster
from .errors import NaturalMathValidationError
from .parameters import default_params

__all__ = [
    "run_step",
    "run_cluster",
    "NaturalMathValidationError",
    "default_params",
]
__version__ = "1.0.0"
__spec_sha256__ = "E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B"
