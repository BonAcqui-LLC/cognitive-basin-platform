"""Extension Harness — No-Op Reference Extension.

A reference extension implementing all 13 harness observation hooks
as pure observers (returning NoChange()). Validates harness
infrastructure — not a Natural Math theory extension.
"""

from __future__ import annotations

from typing import Any

from .manifest import ExtensionManifest
from .protocol import NoChange


class NoopExtension:
    """Reference no-op extension for harness validation."""

    def __init__(self) -> None:
        self.hook_counts: dict[str, int] = {}

    def get_manifest(self) -> ExtensionManifest:
        return ExtensionManifest(
            extension_id="noop-reference",
            extension_name="No-Op Reference Extension",
            extension_version="1.0.0",
            status="EXPERIMENTAL",
            base_system="Natural Math v5 frozen integer base",
            required_base_source_sha256=(
                "e5ab47d41b82f6af573866be637bf3b0"
                "054d96c7f45a613ec6cae2124ad84c7b"
            ),
            required_base_package_manifest_sha256=(
                "87b9c28aa27ff5a4e07096da2c62f1ce"
                "531e4a89c89c77f29084477f8bae7be9"
            ),
            author="BasinLab Harness Validation",
            purpose=(
                "Harness validation infrastructure — "
                "not a Natural Math theory extension"
            ),
            claim_boundary=(
                "No Natural Math v5 behavioral claims. "
                "Purely tests harness infrastructure."
            ),
            state_schema_version=1,
            hook_contract_version=1,
            randomness_policy="NO_EXTENSION_RANDOMNESS",
        )

    # ── Lifecycle Hooks ─────────────────────────────────────────────────

    def on_run_start(self, snapshot=None) -> NoChange:
        self.hook_counts["on_run_start"] = self.hook_counts.get("on_run_start", 0) + 1
        return NoChange()

    def before_step(self, snapshot=None, step_index=None) -> NoChange:
        self.hook_counts["before_step"] = self.hook_counts.get("before_step", 0) + 1
        return NoChange()

    def on_after_decision_formation(self, snapshot=None) -> NoChange:
        self.hook_counts["on_after_decision_formation"] = (
            self.hook_counts.get("on_after_decision_formation", 0) + 1
        )
        return NoChange()

    def on_after_bifurcation_reservation(self, snapshot=None) -> NoChange:
        self.hook_counts["on_after_bifurcation_reservation"] = (
            self.hook_counts.get("on_after_bifurcation_reservation", 0) + 1
        )
        return NoChange()

    def on_after_movement_resolution(self, snapshot=None) -> NoChange:
        self.hook_counts["on_after_movement_resolution"] = (
            self.hook_counts.get("on_after_movement_resolution", 0) + 1
        )
        return NoChange()

    def on_after_pressure_update(self, snapshot=None) -> NoChange:
        self.hook_counts["on_after_pressure_update"] = (
            self.hook_counts.get("on_after_pressure_update", 0) + 1
        )
        return NoChange()

    def on_after_bonding(self, snapshot=None) -> NoChange:
        self.hook_counts["on_after_bonding"] = (
            self.hook_counts.get("on_after_bonding", 0) + 1
        )
        return NoChange()

    def on_after_cluster_action_selection(
        self, snapshot=None, action=None, step_index=None
    ) -> NoChange:
        self.hook_counts["on_after_cluster_action_selection"] = (
            self.hook_counts.get("on_after_cluster_action_selection", 0) + 1
        )
        return NoChange()

    def on_after_cluster_action(
        self, snapshot=None, action=None, step_index=None
    ) -> NoChange:
        self.hook_counts["on_after_cluster_action"] = (
            self.hook_counts.get("on_after_cluster_action", 0) + 1
        )
        return NoChange()

    def on_after_resource_absorption(
        self, snapshot=None, step_index=None
    ) -> NoChange:
        self.hook_counts["on_after_resource_absorption"] = (
            self.hook_counts.get("on_after_resource_absorption", 0) + 1
        )
        return NoChange()

    def after_step(self, snapshot=None, step_index=None) -> NoChange:
        self.hook_counts["after_step"] = self.hook_counts.get("after_step", 0) + 1
        return NoChange()

    def on_run_end(self, snapshot=None) -> NoChange:
        self.hook_counts["on_run_end"] = self.hook_counts.get("on_run_end", 0) + 1
        return NoChange()

    # ── Behavioral hook stub ────────────────────────────────────────────

    def propose_local_move_preference(
        self, snapshot=None, node_id=None, step_index=None
    ) -> NoChange:
        self.hook_counts["propose_local_move_preference"] = (
            self.hook_counts.get("propose_local_move_preference", 0) + 1
        )
        return NoChange()
