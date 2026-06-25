"""
Stage 2 Extension Harness — Error Hierarchy.

All harness-specific exceptions derive from HarnessError so that try/except
boundaries in the harness plumbing can distinguish harness protocol violations
from general Python exceptions without ambiguity.
"""


class HarnessError(Exception):
    """Root of the harness error hierarchy."""
    pass


class ExtensionRegistrationError(HarnessError):
    """Extension could not be registered (duplicate, hash mismatch, etc.)."""
    pass


class ManifestValidationError(HarnessError):
    """Extension manifest failed structural or semantic validation."""
    pass


class StateSchemaError(HarnessError):
    """Extension tried to store state that violates its declared schema version."""
    pass


class HookContractError(HarnessError):
    """Extension hook implementation violated the hook contract."""
    pass


class RandomnessPolicyError(HarnessError):
    """Extension violated the declared randomness policy."""
    pass


class ProposalValidationError(HarnessError):
    """A LocalMovePreferenceProposal failed runtime validation."""
    pass


class BaselineImmutabilityError(HarnessError):
    """Extension attempted to mutate baseline (read-only) state."""
    pass


class SnapshotMutationError(HarnessError):
    """A defensive snapshot was mutated after being handed to an extension."""
    pass
