"""Natural Math v5 reference implementation — operational trace instrumentation.

Zero-overhead-when-disabled trace recorder. All record() calls use keyword
arguments and never consume random draws, alter model state, ordering,
exceptions, or returned results.
"""

from __future__ import annotations

from typing import Any


class TraceRecorder:
    """Non-mutating trace recorder. Zero overhead when disabled (one boolean check)."""

    def __init__(self) -> None:
        self._enabled: bool = False
        self._records: list[dict[str, Any]] = []

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def record(self, **kwargs: Any) -> None:
        if self._enabled:
            self._records.append(dict(kwargs))

    def get_records(self) -> list[dict[str, Any]]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()


# Module-level singleton
_tracer = TraceRecorder()


def get_tracer() -> TraceRecorder:
    """Return the module-level TraceRecorder singleton."""
    return _tracer


def enable_tracing() -> None:
    """Enable trace recording globally."""
    _tracer.enable()


def disable_tracing() -> None:
    """Disable trace recording globally."""
    _tracer.disable()
