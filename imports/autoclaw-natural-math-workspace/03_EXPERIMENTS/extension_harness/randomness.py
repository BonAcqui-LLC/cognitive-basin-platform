"""Extension Harness — managed extension RNG.

Designed for future use. Deactivated in Stage 2 — all methods
return False/no-op because extensions must not consume randomness
until the managed RNG policy is activated.
"""

from __future__ import annotations


class ExtensionRngPolicy:
    """RNG policies for extensions."""

    NO_RANDOMNESS = "NO_EXTENSION_RANDOMNESS"
    SHARED_TRACE_RNG = "SHARED_TRACE_RNG"  # Future
    ISOLATED_RNG = "ISOLATED_RNG"           # Future


class ExtensionRng:
    """Managed extension RNG.

    In Stage 2 this RNG is fully deactivated. Extensions that
    require randomness must declare it in their manifest and
    wait for a future stage where managed RNG is activated.

    The harness passes an ExtensionRng instance to adapter functions.
    Extensions receive it through hook arguments and can check
    is_active() before attempting any random draws.
    """

    def __init__(self, policy: str = ExtensionRngPolicy.NO_RANDOMNESS) -> None:
        self.policy = policy

    def is_active(self) -> bool:
        """Return True if this RNG is permitted to produce random values."""
        return False

    def randrange(self, a: int, b: int) -> int:
        """Stub — raises if called while inactive."""
        if not self.is_active():
            raise RuntimeError(
                "ExtensionRng is deactivated (policy={}). "
                "Extensions must not consume randomness in Stage 2.".format(
                    self.policy
                )
            )
        raise NotImplementedError("ExtensionRng.randrange not implemented")

    def randint(self, a: int, b: int) -> int:
        """Stub — raises if called while inactive."""
        if not self.is_active():
            raise RuntimeError(
                "ExtensionRng is deactivated (policy={}).".format(self.policy)
            )
        raise NotImplementedError("ExtensionRng.randint not implemented")

    def get_draw_count(self) -> int:
        """Return number of random draws consumed by this RNG."""
        return 0
