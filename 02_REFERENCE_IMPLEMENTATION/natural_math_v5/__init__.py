"""Natural Math v5 — Frozen Integer Reference Implementation.

Frozen spec: Natural Math v5 - Status Frozen Int
SHA256: E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B

Public API:
  run_step(nodes, params, *, use_deficit=False, ...) -> list[dict]
  run_cluster(seed, params=None, steps=140) -> dict  (Section 22 contract)
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
  validation.py   — validate_nodes, check_invariants, live_degree, as_tuple3_strict
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
  cluster.py                — run_cluster wrapper (Section 22 contract)
  serialization.py          — JSON serialization helpers
  tracing.py                — trace instrumentation (operational, wired into run_step and cluster_step)
  provenance.py             — donor attribution records

Deviations from Stage 1 plan:
  - invariants.py: merged into validation.py (check_invariants)
  - movement.py: standalone module; core_step uses inline resolution matching donor
  - decisions.py: simplified to fallback_direction only (decision logic inline in core_step)
  - bifurcation.py: apply_bifurcation merged inline into core_step per donor pattern
  - tracing.py: implemented and fully wired (non-mutating, zero-overhead when disabled)

Phase ordering verified against spec:
  - core_step.py: matches Section 12 step ordering exactly
  - cluster_step.py: matches Section 19 step ordering exactly
  - See 06_REPORTS/stage_1_phase_order_audit.md for detailed audit
"""

from .core_step import run_step
from .cluster import run_cluster
from .errors import NaturalMathValidationError
from .parameters import default_params
from .tracing import TraceRecorder, get_tracer, enable_tracing, disable_tracing

__all__ = [
    "run_step",
    "run_cluster",
    "NaturalMathValidationError",
    "default_params",
    "TraceRecorder",
    "get_tracer",
    "enable_tracing",
    "disable_tracing",
]
__version__ = "1.0.0"
__spec_sha256__ = "E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B"
