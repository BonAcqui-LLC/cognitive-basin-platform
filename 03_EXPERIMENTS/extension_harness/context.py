"""
Stage 2 Extension Harness — Immutable Run Context.

A RunContext is created once at the start of a run and handed to every
extension hook invocation so extensions can inspect the execution
environment without being able to change it.
"""

from __future__ import annotations

from typing import Any


class RunContext:
    """
    Frozen snapshot of the run-level parameters handed to every hook.

    Instances are read-only by convention (Python cannot truly enforce
    immutability on dict values, but harness code MUST NOT mutate).
    """

    __slots__ = (
        "_run_id",
        "_mode",
        "_seed",
        "_params",
        "_steps",
        "_baseline_sha256",
        "_package_manifest_sha256",
        "_timestamp",
    )

    def __init__(
        self,
        run_id: str,
        mode: str,
        seed: int,
        params: dict,
        steps: int,
        baseline_sha256: str,
        package_manifest_sha256: str,
        timestamp: str,
    ) -> None:
        self._run_id = run_id
        self._mode = mode
        self._seed = seed
        self._params = params
        self._steps = steps
        self._baseline_sha256 = baseline_sha256
        self._package_manifest_sha256 = package_manifest_sha256
        self._timestamp = timestamp

    # ── Read-only property access ──────────────────────────────────

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def params(self) -> dict:
        return self._params

    @property
    def steps(self) -> int:
        return self._steps

    @property
    def baseline_sha256(self) -> str:
        return self._baseline_sha256

    @property
    def package_manifest_sha256(self) -> str:
        return self._package_manifest_sha256

    @property
    def timestamp(self) -> str:
        return self._timestamp

    # ── Provenance ─────────────────────────────────────────────────

    def to_provenance(self) -> dict[str, Any]:
        """Return a JSON-serialisable provenance record."""
        return {
            "run_id": self._run_id,
            "mode": self._mode,
            "seed": self._seed,
            "params": self._params,
            "steps": self._steps,
            "baseline_sha256": self._baseline_sha256,
            "package_manifest_sha256": self._package_manifest_sha256,
            "timestamp": self._timestamp,
        }

    def __repr__(self) -> str:
        return f"RunContext(run_id={self._run_id!r}, mode={self._mode!r}, seed={self._seed}, steps={self._steps})"
