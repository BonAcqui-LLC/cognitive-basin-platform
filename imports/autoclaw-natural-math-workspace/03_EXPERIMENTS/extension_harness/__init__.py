"""Extension Harness — Stage 2 adapter layer for Natural Math v5.

Wraps the frozen baseline (02_REFERENCE_IMPLEMENTATION/natural_math_v5/)
through a hook-based harness supporting three modes:
  BASELINE — direct baseline call
  HARNESS_NO_EXTENSIONS — through harness with empty registry
  HARNESS_WITH_EXTENSIONS — through harness with registered extensions
"""

# ── Protocol & Manifest ───────────────────────────────────────────────
from .protocol import (
    ON_RUN_START,
    BEFORE_STEP,
    AFTER_DECISION_FORMATION,
    AFTER_BIFURCATION_RESERVATION,
    AFTER_MOVEMENT_RESOLUTION,
    AFTER_PRESSURE_UPDATE,
    AFTER_BONDING,
    AFTER_CLUSTER_ACTION_SELECTION,
    AFTER_CLUSTER_ACTION,
    AFTER_RESOURCE_ABSORPTION,
    AFTER_STEP,
    ON_RUN_END,
    PROPOSE_LOCAL_MOVE_PREFERENCE,
    OBSERVATION_HOOKS,
    BEHAVIORAL_HOOKS,
    ALL_HOOKS,
    HookResult,
    NoChange,
    StateUpdate,
    DiagnosticEvent,
    LocalMovePreferenceProposal,
    VALID_EXTENSION_STATUSES,
    VALID_RANDOMNESS_POLICIES,
)
from .manifest import ExtensionManifest

# ── Registry & Context ────────────────────────────────────────────────
from .registry import ExtensionRegistry
from .context import RunContext

# ── Error hierarchy ───────────────────────────────────────────────────
from .errors import (
    HarnessError,
    ExtensionRegistrationError,
    ManifestValidationError,
    StateSchemaError,
    HookContractError,
    RandomnessPolicyError,
    ProposalValidationError,
    BaselineImmutabilityError,
    SnapshotMutationError,
)

# ── Hook validation ───────────────────────────────────────────────────
from .hook_results import validate_hook_result, validate_move_proposal

# ── Snapshots ─────────────────────────────────────────────────────────
from .snapshots import (
    snapshot_nodes,
    snapshot_occupancy,
    snapshot_params,
    snapshot_decisions,
    snapshot_movement_attempts,
    snapshot_bifurcation_reservations,
    snapshot_resource_state,
    snapshot_cluster_metrics,
)

# ── State store ───────────────────────────────────────────────────────
from .state_store import StateStore

# ── Compat types shim ─────────────────────────────────────────────────
from .types import HookPhase

# ── Extension RNG ─────────────────────────────────────────────────────
from .randomness import ExtensionRngPolicy, ExtensionRng

# ── Adapters ──────────────────────────────────────────────────────────
from .local_adapter import run_step_through_harness
from .cluster_adapter import run_cluster_through_harness

# ── Runners ───────────────────────────────────────────────────────────
from .runner import Mode, run_local, run_cluster
from .ab_runner import run_ab_local, run_ab_cluster, compare_ab_result

# ── Comparison ────────────────────────────────────────────────────────
from .comparison import deep_equal, structured_diff, hash_result

# ── Extensions ────────────────────────────────────────────────────────
from .noop_extension import NoopExtension

# ── Serialization ─────────────────────────────────────────────────────
from .serialization import serialize_run_output, serialize_ab_report

# ── Provenance ────────────────────────────────────────────────────────
from .provenance import create_provenance_record

__version__ = "1.0.0"
