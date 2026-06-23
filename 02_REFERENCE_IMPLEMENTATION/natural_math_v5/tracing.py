"""Natural Math v5 reference implementation — optional trace instrumentation.

Frozen spec: trace mode must not alter model state, consume draws, or change outputs.
"""

from __future__ import annotations

from typing import Any


class TraceRecorder:
    """Optional trace recorder. Disabled by default, zero overhead when off.

    Trace mode records: phase, node_id, decision, target, energy before/after,
    pressure before/after, random draws, bifurcation scheduling,
    movement conflict results, bond formation, cluster actions, resource transfers.
    """

    def __init__(self) -> None:
        self.enabled: bool = False
        self.records: list[dict[str, Any]] = []

    def enable(self) -> None:
        self.enabled = True
        self.records = []

    def disable(self) -> None:
        self.enabled = False

    def record(self, entry: dict[str, Any]) -> None:
        if self.enabled:
            self.records.append(dict(entry))

    def get_records(self) -> list[dict[str, Any]]:
        return list(self.records)

    def clear(self) -> None:
        self.records = []


# Global singleton for module-level use
_tracer = TraceRecorder()


def get_tracer() -> TraceRecorder:
    return _tracer
