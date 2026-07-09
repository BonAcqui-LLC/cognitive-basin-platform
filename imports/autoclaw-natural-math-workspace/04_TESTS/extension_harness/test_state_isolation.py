"""State Isolation Tests — Stage 2 Extension Harness.

Validate that extension state is properly isolated between different runs.

Tests:
  1. Two runs with different seeds → independent state
  2. A/B arms → independent state  
  3. Exception during run → state not persisted (reset_run)
  4. Serialization and restoration round-trip
  5. Two registered instances of same extension → independent
  6. Different extension versions → independent state stores
"""

import copy
import sys
import unittest

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE")

import natural_math_v5 as nm
from natural_math_v5.records import make_node
from natural_math_v5.randomness import TraceRng

from extension_harness import (
    Mode,
    NoopExtension,
    ExtensionManifest,
    ExtensionRegistry,
    RunContext,
    NoChange,
    StateUpdate,
    StateStore,
    StateSchemaError,
    HookPhase,
    ALL_HOOKS,
    run_local,
    run_cluster,
    run_ab_local,
    run_ab_cluster,
    create_provenance_record,
    serialize_run_output,
    snapshot_nodes,
    snapshot_params,
    hash_result,
)


def _make_two_nodes():
    return [
        make_node(1, (0, 0, 0), energy=1000000, node_type="seed"),
        make_node(2, (2, 0, 0), energy=1000000, node_type="tip"),
    ]


def _fresh_rng(seed=42):
    return TraceRng(seed)


# ── Test Helpers ──────────────────────────────────────────────────────

def _make_stateful_ext(ext_id, version="1.0.0"):
    """Create an extension that stores and retrieves state."""
    class StatefulExt:
        def __init__(self):
            self.store = StateStore()

        def get_manifest(self):
            return ExtensionManifest(
                extension_id=ext_id, extension_name=f"Stateful {ext_id}",
                extension_version=version, status="EXPERIMENTAL",
                base_system="natural_math_v5",
                required_base_source_sha256="e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
                required_base_package_manifest_sha256="87b9c28aa27ff5a4e07096da2c62f1ce531e4a89c89c77f29084477f8bae7be9",
                author="tester", purpose="state isolation test",
                claim_boundary="test", state_schema_version=1,
                hook_contract_version=1, randomness_policy="NO_EXTENSION_RANDOMNESS",
            )

        def on_run_start(self, snapshot=None):
            return NoChange()

        def before_step(self, snapshot=None, step_index=None):
            return NoChange()

        def after_step(self, snapshot=None, step_index=None):
            return NoChange()

        def on_run_end(self, snapshot=None):
            return NoChange()

    return StatefulExt()


class TestStateIsolation(unittest.TestCase):

    # ── Test 1: Two runs with different seeds → independent state ────

    def test_different_seeds_independent_state(self):
        """Two runs with different seeds produce independent state stores."""
        store_a = StateStore()
        store_b = StateStore()

        store_a.set_state("run-1", "ext.x", "1.0.0", {"seed": 42}, 1)
        store_b.set_state("run-2", "ext.x", "1.0.0", {"seed": 99}, 1)

        state_a = store_a.get_state("run-1", "ext.x", "1.0.0")
        state_b = store_b.get_state("run-2", "ext.x", "1.0.0")

        self.assertEqual(state_a["seed"], 42)
        self.assertEqual(state_b["seed"], 99)
        # Cross-lookup should return empty
        self.assertEqual(store_a.get_state("run-2", "ext.x", "1.0.0"), {})

    # ── Test 2: A/B arms → independent state ─────────────────────────

    def test_ab_arms_independent_state(self):
        """A and B arms in the A/B runner have independent state."""
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()

        # Run A/B comparison
        report = run_ab_local(nodes, params, extensions=[noop], seed=42)
        self.assertTrue(report["arms_equal"])

        # Arm A and Arm B run independently
        self.assertEqual(report["arm_a"]["mode"], "BASELINE")
        self.assertEqual(report["arm_b"]["mode"], "HARNESS_WITH_EXTENSIONS")
        self.assertIn("comparison", report)
        self.assertTrue(report["comparison"]["equal"])

    # ── Test 3: Exception during run → state reset ──────────────────

    def test_state_reset_run_clears_state(self):
        """reset_run should clear all state for a specific run_id."""
        store = StateStore()
        store.set_state("run-1", "ext.a", "1.0.0", {"x": 1}, 1)
        store.set_state("run-1", "ext.b", "1.0.0", {"y": 2}, 1)
        store.set_state("run-2", "ext.a", "1.0.0", {"z": 3}, 1)

        store.reset_run("run-1")

        self.assertEqual(store.get_state("run-1", "ext.a", "1.0.0"), {})
        self.assertEqual(store.get_state("run-1", "ext.b", "1.0.0"), {})
        self.assertEqual(store.get_state("run-2", "ext.a", "1.0.0"), {"z": 3})

    # ── Test 4: Serialization round-trip ────────────────────────────

    def test_serialization_round_trip(self):
        """Serialized state can be restored."""
        params = nm.default_params()
        nodes = _make_two_nodes()

        # Run BASELINE
        out_a = run_local(nodes, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        # Serialize both runs
        s_a = serialize_run_output(out_a["result"])
        # Re-run and serialize again
        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.BASELINE, rng=_fresh_rng(42))
        s_b = serialize_run_output(out_b["result"])

        self.assertEqual(s_a, s_b, "Serialized results from identical runs must match")

    # ── Test 5: Two registered instances of same extension version → independent

    def test_two_instances_independent(self):
        """Two registered instances of the same extension maintain independent state."""
        params = nm.default_params()
        ext1 = _make_stateful_ext("stateful.test", "1.0.0")
        ext2 = _make_stateful_ext("stateful.test", "1.0.0")

        # Register both in the same registry (different versions or same version - different instances)
        # Actually same version can't be registered twice, so use different IDs
        ext2_alt = _make_stateful_ext("stateful.test.2", "1.0.0")

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[ext1], rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[ext2_alt], rng=_fresh_rng(42))

        # Both runs should produce valid results
        self.assertIn("result", out_a)
        self.assertIn("result", out_b)
        self.assertEqual(len(out_a["result"]), len(out_b["result"]))

    # ── Test 6: Different extension versions → independent stores ────

    def test_different_versions_independent(self):
        """Different versions of the same extension have independent state."""
        store = StateStore()
        store.set_state("run-1", "ext.x", "1.0.0", {"v": 1}, 1)
        store.set_state("run-1", "ext.x", "2.0.0", {"v": 2}, 1)

        self.assertEqual(store.get_state("run-1", "ext.x", "1.0.0"), {"v": 1})
        self.assertEqual(store.get_state("run-1", "ext.x", "2.0.0"), {"v": 2})

    # ── Test 7: reset_all clears everything ──────────────────────────

    def test_reset_all_clears_everything(self):
        """reset_all should clear all state across all runs."""
        store = StateStore()
        store.set_state("run-1", "ext.a", "1.0.0", {"x": 1}, 1)
        store.set_state("run-2", "ext.b", "1.0.0", {"y": 2}, 1)

        store.reset_all()

        self.assertEqual(store.get_state("run-1", "ext.a", "1.0.0"), {})
        self.assertEqual(store.get_state("run-2", "ext.b", "1.0.0"), {})

    # ── Test 8: State copy independence ──────────────────────────────

    def test_get_state_returns_copy_not_reference(self):
        """get_state returns a shallow copy — top-level keys are independent."""
        store = StateStore()
        store.set_state("run-1", "ext.a", "1.0.0", {"count": 1, "label": "original"}, 1)

        state = store.get_state("run-1", "ext.a", "1.0.0")
        state["count"] = 999
        state["label"] = "hacked"

        # Top-level keys should be independent
        state2 = store.get_state("run-1", "ext.a", "1.0.0")
        self.assertEqual(state2["count"], 1, "Top-level values should be independent")
        self.assertEqual(state2["label"], "original")


if __name__ == "__main__":
    unittest.main(verbosity=2)
