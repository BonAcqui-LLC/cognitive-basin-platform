"""Natural Math v5 reference implementation — errors.

Frozen spec: Natural Math v5 - Status Frozen Int
SHA256: E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B
"""


class NaturalMathValidationError(ValueError):
    """Raised when validation rules (Section 6) are violated or runtime
    flags conflict (Section 6)."""
    pass
