"""Verification tests for Extension Harness Stage 2 adapters.

Tests:
  1. run_local BASELINE == direct nm.run_step
  2. run_local HARNESS_NO_EXTENSIONS == BASELINE  
  3. run_local HARNESS_WITH_EXTENSIONS (noop) == BASELINE
  4. run_cluster in all 3 modes (results match)
  5. A/B runner with no-op extension (arms equal)
  6. No-op extension hooks are called
  7. No-op extension state is isolated between runs
  8. No-op extension consumes no randomness
"""

import copy
import sys
import unittest

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS")

import natural_math_v5 as nm
from natural_math_v5.records import make_node
from natural_math_v5.randomness import TraceRng

from extension_harness import (
    Mode,
    ExtensionRegistry,
    RunContext,
    NoChange,
    NoopExtension,
    ExtensionRng,
    ExtensionRngPolicy,
    ExtensionManifest,
    ALL_HOOKS,
    HookPhase,
    run_local,
    run_cluster,
    run_ab_local,
    run_ab_cluster,
    compare_ab_result,
    deep_equal,
    structured_diff,
    hash_result,
    create_provenance_record,
    serialize_run_output,
    serialize_ab_report,
    snapshot_nodes,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_two_nodes():
    return [
        make_node(1, (0, 0, 0), energy=1000000, node_type="seed"),
        make_node(2, (2, 0, 0), energy=1000000, node_type="tip"),
    ]


def _nodes_equal(a, b):
    if len(a) != len(b):
        return False
    for na, nb in zip(sorted(a, key=lambda n: n["id"]),
                      sorted(b, key=lambda n: n["id"])):
        for key in ("id", "pos", "direction", "energy", "pressure",
                     "alive", "type", "parent_id", "signal_type"):
            if na.get(key) != nb.get(key):
                return False
        if set(na.get("bonds", set())) != set(nb.get("bonds", set())):
            return False
    return True


def _fresh_rng(seed=42):
    """Create a fresh TraceRng — never reuse the same instance between calls."""
    return TraceRng(seed)


# ── Test 1: BASELINE matches direct nm.run_step ─────────────────────────────

class TestLocalBaseline(unittest.TestCase):
    def test_baseline_equals_direct(self):
        params = nm.default_params()
        nodes_direct = _make_two_nodes()
        rng_direct = _fresh_rng(42)
        result_direct = nm.run_step(nodes_direct, params, rng=rng_direct)

        nodes_runner = _make_two_nodes()
        rng_runner = _fresh_rng(42)  # fresh RNG with same seed
        output = run_local(nodes_runner, params, mode=Mode.BASELINE, rng=rng_runner)

        self.assertEqual(output["mode"], Mode.BASELINE)
        self.assertTrue(
            _nodes_equal(result_direct, output["result"]),
            "BASELINE runner must match direct call.",
        )
        self.assertEqual(len(output["hook_events"]), 0)

    def test_baseline_preserves_node_count(self):
        params = nm.default_params()
        nodes = _make_two_nodes()
        output = run_local(nodes, params, mode=Mode.BASELINE, rng=_fresh_rng(99))
        self.assertGreaterEqual(len(output["result"]), 2)


# ── Test 2: HARNESS_NO_EXTENSIONS == BASELINE ───────────────────────────────

class TestHarnessNoExtensions(unittest.TestCase):
    def test_no_extensions_equals_baseline(self):
        params = nm.default_params()
        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_NO_EXTENSIONS,
                         rng=_fresh_rng(42))

        self.assertTrue(_nodes_equal(out_a["result"], out_b["result"]))

    def test_no_extensions_has_provenance(self):
        params = nm.default_params()
        nodes = _make_two_nodes()
        out = run_local(nodes, params, mode=Mode.HARNESS_NO_EXTENSIONS,
                       rng=_fresh_rng(7))
        self.assertIn("provenance", out)
        self.assertEqual(out["provenance"]["mode"], Mode.HARNESS_NO_EXTENSIONS)


# ── Test 3: HARNESS_WITH_EXTENSIONS (noop) == BASELINE ─────────────────────

class TestHarnessWithNoopExtension(unittest.TestCase):
    def test_noop_equals_baseline(self):
        params = nm.default_params()
        noop = NoopExtension()

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[noop], rng=_fresh_rng(42))

        self.assertTrue(_nodes_equal(out_a["result"], out_b["result"]))

    def test_noop_with_different_seed(self):
        params = nm.default_params()
        noop = NoopExtension()

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(12345))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[noop], rng=_fresh_rng(12345))

        self.assertTrue(_nodes_equal(out_a["result"], out_b["result"]))


# ── Test 4: run_cluster in all 3 modes ─────────────────────────────────────

class TestClusterModes(unittest.TestCase):
    def test_cluster_baseline_runs(self):
        result = run_cluster(seed=42, steps=10, mode=Mode.BASELINE)
        self.assertEqual(result["mode"], Mode.BASELINE)
        self.assertIn("result", result)

    def test_cluster_no_extensions_runs(self):
        result = run_cluster(seed=42, steps=10, mode=Mode.HARNESS_NO_EXTENSIONS)
        self.assertEqual(result["mode"], Mode.HARNESS_NO_EXTENSIONS)

    def test_cluster_with_noop_runs(self):
        noop = NoopExtension()
        result = run_cluster(seed=42, steps=10,
                            mode=Mode.HARNESS_WITH_EXTENSIONS, extensions=[noop])
        self.assertEqual(result["mode"], Mode.HARNESS_WITH_EXTENSIONS)
        self.assertGreater(len(result["hook_events"]), 0)

    def test_cluster_all_modes_equal(self):
        seed, steps = 42, 8
        out_a = run_cluster(seed=seed, steps=steps, mode=Mode.BASELINE)
        out_b = run_cluster(seed=seed, steps=steps, mode=Mode.HARNESS_NO_EXTENSIONS)
        noop = NoopExtension()
        out_c = run_cluster(seed=seed, steps=steps,
                           mode=Mode.HARNESS_WITH_EXTENSIONS, extensions=[noop])
        ha = hash_result(out_a["result"])
        hb = hash_result(out_b["result"])
        hc = hash_result(out_c["result"])
        self.assertEqual(ha, hb,
                        "BASELINE and HARNESS_NO_EXTENSIONS cluster hashes must match")
        self.assertEqual(ha, hc,
                        "BASELINE and HARNESS_WITH_EXTENSIONS cluster hashes must match")


# ── Test 5: A/B Runner ─────────────────────────────────────────────────────

class TestABRunner(unittest.TestCase):
    def test_ab_local_arms_equal(self):
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()
        report = run_ab_local(nodes, params, extensions=[noop], seed=42)
        self.assertTrue(report["arms_equal"])

    def test_ab_cluster_arms_equal(self):
        noop = NoopExtension()
        report = run_ab_cluster(seed=42, params=None, steps=8, extensions=[noop])
        self.assertTrue(report["arms_equal"])

    def test_ab_comparison_fields(self):
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()
        report = run_ab_local(nodes, params, extensions=[noop], seed=42)
        self.assertIn("comparison", report)
        self.assertIn("hash_a", report["comparison"])
        self.assertIn("hash_b", report["comparison"])


# ── Test 6: No-Op Hooks Called ─────────────────────────────────────────────

class TestNoopHooksCalled(unittest.TestCase):
    def test_local_hooks_called(self):
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()
        run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=_fresh_rng(42))

        self.assertEqual(noop.hook_counts.get("on_run_start", 0), 1)
        self.assertEqual(noop.hook_counts.get("on_run_end", 0), 1)
        self.assertEqual(noop.hook_counts.get("before_step", 0), 1)
        self.assertEqual(noop.hook_counts.get("after_step", 0), 1)

    def test_hooks_have_nonzero_counts(self):
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()
        run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=_fresh_rng(42))
        total = sum(noop.hook_counts.values())
        self.assertGreater(total, 0, "At least some hooks should fire")

    def test_cluster_hooks_called(self):
        noop = NoopExtension()
        steps = 5
        run_cluster(seed=42, steps=steps,
                   mode=Mode.HARNESS_WITH_EXTENSIONS, extensions=[noop])

        self.assertEqual(noop.hook_counts.get("on_run_start", 0), 1)
        self.assertEqual(noop.hook_counts.get("on_run_end", 0), 1)
        self.assertEqual(noop.hook_counts.get("before_step", 0), steps)
        self.assertEqual(noop.hook_counts.get("after_step", 0), steps)
        self.assertGreater(
            noop.hook_counts.get("on_after_cluster_action_selection", 0), 0)


# ── Test 7: No-Op State Isolation ──────────────────────────────────────────

class TestNoopStateIsolation(unittest.TestCase):
    def test_separate_instances_independent(self):
        params = nm.default_params()
        noop1 = NoopExtension()
        noop2 = NoopExtension()

        nodes = _make_two_nodes()
        run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop1], rng=_fresh_rng(42))

        nodes2 = _make_two_nodes()
        run_local(nodes2, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop2], rng=_fresh_rng(42))
        # Run again on noop2 only
        nodes3 = _make_two_nodes()
        run_local(nodes3, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop2], rng=_fresh_rng(99))

        t1 = sum(noop1.hook_counts.values())
        t2 = sum(noop2.hook_counts.values())
        self.assertNotEqual(t1, t2,
                           "Separate instances must have independent state")

    def test_same_instance_accumulates(self):
        params = nm.default_params()
        noop = NoopExtension()

        nodes1 = _make_two_nodes()
        run_local(nodes1, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=_fresh_rng(42))
        first_counts = dict(noop.hook_counts)

        nodes2 = _make_two_nodes()
        run_local(nodes2, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=_fresh_rng(42))

        for hook_name, count in first_counts.items():
            self.assertEqual(
                noop.hook_counts[hook_name], count * 2,
                f"Hook {hook_name} should accumulate",
            )


# ── Test 8: No Randomness Consumption ──────────────────────────────────────

class TestNoopRandomness(unittest.TestCase):
    def test_extension_rng_deactivated(self):
        rng = ExtensionRng(policy=ExtensionRngPolicy.NO_RANDOMNESS)
        self.assertFalse(rng.is_active())
        self.assertEqual(rng.get_draw_count(), 0)

    def test_extension_rng_raises_on_draw(self):
        rng = ExtensionRng(policy=ExtensionRngPolicy.NO_RANDOMNESS)
        with self.assertRaises(RuntimeError):
            rng.randrange(0, 100)

    def test_rng_draws_identical(self):
        """Baseline TraceRng draw count must be identical with/without noop."""
        params = nm.default_params()

        rng_a = _fresh_rng(42)
        nodes_a = _make_two_nodes()
        run_local(nodes_a, params, mode=Mode.BASELINE, rng=rng_a)
        draws_a = len(rng_a.draws)

        rng_b = _fresh_rng(42)
        noop = NoopExtension()
        nodes_b = _make_two_nodes()
        run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=rng_b)
        draws_b = len(rng_b.draws)

        self.assertEqual(draws_a, draws_b,
                        f"RNG draw count must be identical: {draws_a} vs {draws_b}")

    def test_noop_manifest_no_randomness(self):
        noop = NoopExtension()
        m = noop.get_manifest()
        self.assertEqual(m.randomness_policy, "NO_EXTENSION_RANDOMNESS")


# ── Comparison Utilities ──────────────────────────────────────────────────

class TestComparisonUtilities(unittest.TestCase):
    def test_deep_equal_identical(self):
        self.assertTrue(deep_equal({"a": [1, 2]}, {"a": [1, 2]}))

    def test_deep_equal_different(self):
        self.assertFalse(deep_equal({"a": 1}, {"a": 2}))

    def test_structured_diff_no_differences(self):
        self.assertEqual(len(structured_diff(42, 42)), 0)

    def test_structured_diff_value_mismatch(self):
        diffs = structured_diff(42, 43)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["type"], "value_mismatch")

    def test_structured_diff_deep(self):
        diffs = structured_diff({"x": {"y": 1}}, {"x": {"y": 2}})
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["path"], "x.y")

    def test_hash_result_consistent(self):
        h1 = hash_result({"key": "val"})
        h2 = hash_result({"key": "val"})
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


# ── Serialization ─────────────────────────────────────────────────────────

class TestSerialization(unittest.TestCase):
    def test_serialize_local_nodes(self):
        nodes = _make_two_nodes()
        s = serialize_run_output(nodes)
        self.assertEqual(s["type"], "local_nodes")
        self.assertEqual(s["node_count"], 2)

    def test_serialize_cluster_result(self):
        result = run_cluster(seed=42, steps=3, mode=Mode.BASELINE)
        s = serialize_run_output(result["result"])
        self.assertEqual(s["type"], "cluster_result")

    def test_serialize_ab_report(self):
        noop = NoopExtension()
        nodes = _make_two_nodes()
        report = run_ab_local(nodes, nm.default_params(), extensions=[noop], seed=42)
        s = serialize_ab_report(report)
        self.assertIn("arms_equal", s)


# ── Provenance ────────────────────────────────────────────────────────────

class TestProvenance(unittest.TestCase):
    def test_create_baseline_provenance(self):
        prov = create_provenance_record(
            mode=Mode.BASELINE, seed=42, params=nm.default_params(),
            steps=1, extension_manifests=[], result_hash="abc123",
        )
        self.assertEqual(prov["mode"], Mode.BASELINE)
        self.assertIn("provenance_sha256", prov)

    def test_create_harness_provenance(self):
        noop = NoopExtension()
        m = noop.get_manifest()
        prov = create_provenance_record(
            mode=Mode.HARNESS_WITH_EXTENSIONS, seed=99,
            params=nm.default_params(), steps=10,
            extension_manifests=[m], result_hash="def456",
        )
        self.assertEqual(prov["extension_count"], 1)
        self.assertEqual(prov["extensions"][0]["extension_id"], "noop-reference")


# ── Manifest ──────────────────────────────────────────────────────────────

class TestManifest(unittest.TestCase):
    def test_noop_manifest_fields(self):
        noop = NoopExtension()
        m = noop.get_manifest()
        self.assertEqual(m.extension_id, "noop-reference")
        self.assertEqual(m.status, "EXPERIMENTAL")
        self.assertEqual(m.state_schema_version, 1)
        self.assertEqual(m.randomness_policy, "NO_EXTENSION_RANDOMNESS")

    def test_noop_manifest_sha256(self):
        noop = NoopExtension()
        m = noop.get_manifest()
        self.assertEqual(
            m.required_base_source_sha256,
            "e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
        )


# ── Registry ──────────────────────────────────────────────────────────────

class TestRegistry(unittest.TestCase):
    def test_empty_registry(self):
        reg = ExtensionRegistry()
        self.assertEqual(len(reg), 0)
        self.assertEqual(len(reg.get_all()), 0)

    def test_register_extension(self):
        reg = ExtensionRegistry()
        noop = NoopExtension()
        m = noop.get_manifest()
        reg.register(noop, m)
        self.assertEqual(len(reg), 1)

    def test_duplicate_raises(self):
        reg = ExtensionRegistry()
        noop = NoopExtension()
        m = noop.get_manifest()
        reg.register(noop, m)
        with self.assertRaises(Exception):
            reg.register(noop, m)

    def test_get_hooks(self):
        reg = ExtensionRegistry()
        noop = NoopExtension()
        reg.register(noop, noop.get_manifest())
        hooks = reg.get_hooks("on_run_start")
        self.assertEqual(len(hooks), 1)


# ── Mode Constants ────────────────────────────────────────────────────────

class TestMode(unittest.TestCase):
    def test_all_modes(self):
        self.assertIn(Mode.BASELINE, Mode.ALL)
        self.assertIn(Mode.HARNESS_NO_EXTENSIONS, Mode.ALL)
        self.assertIn(Mode.HARNESS_WITH_EXTENSIONS, Mode.ALL)
        self.assertEqual(len(Mode.ALL), 3)

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            run_local(_make_two_nodes(), nm.default_params(), mode="INVALID")


# ── Hook Phase Constants ──────────────────────────────────────────────────

class TestHookPhase(unittest.TestCase):
    def test_all_hooks_count(self):
        self.assertEqual(len(ALL_HOOKS), 13)

    def test_method_map_coverage(self):
        self.assertEqual(len(HookPhase.METHOD_MAP), 13)
        for phase in sorted(ALL_HOOKS):
            self.assertIn(phase, HookPhase.METHOD_MAP, f"Missing map for {phase}")


# ── Edge Cases ────────────────────────────────────────────────────────────

class TestEdgeCases(unittest.TestCase):
    def test_empty_nodes_baseline(self):
        output = run_local([], nm.default_params(), mode=Mode.BASELINE)
        self.assertEqual(len(output["result"]), 0)

    def test_empty_nodes_harness(self):
        noop = NoopExtension()
        output = run_local([], nm.default_params(),
                          mode=Mode.HARNESS_WITH_EXTENSIONS, extensions=[noop])
        self.assertEqual(len(output["result"]), 0)

    def test_compare_ab_identical(self):
        c = compare_ab_result({"x": 1}, {"x": 1})
        self.assertTrue(c["equal"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
