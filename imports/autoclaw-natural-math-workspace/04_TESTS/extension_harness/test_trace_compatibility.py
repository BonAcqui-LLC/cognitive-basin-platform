"""Trace Compatibility Tests — Stage 2 Extension Harness.

Verify that harness runs produce compatible traces with baseline.

Tests:
  1. BASELINE trace == HARNESS_NO_EXTENSIONS trace
  2. BASELINE trace == HARNESS_WITH_EXTENSIONS (noop) trace
  3. Harness may add separate extension-event trace but must not change frozen trace
  4. Cluster mode trace compatibility across all 3 modes
  5. Trace data structures are valid JSON-serializable
"""

import json
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
    run_local,
    run_cluster,
    hash_result,
    deep_equal,
    structured_diff,
    serialize_run_output,
    serialize_ab_report,
)


def _make_two_nodes():
    return [
        make_node(1, (0, 0, 0), energy=1000000, node_type="seed"),
        make_node(2, (2, 0, 0), energy=1000000, node_type="tip"),
    ]


def _fresh_rng(seed=42):
    return TraceRng(seed)


class TestTraceCompatibility(unittest.TestCase):

    # ── Test 1: BASELINE trace == HARNESS_NO_EXTENSIONS trace ────────

    def test_baseline_trace_equals_no_extensions_trace(self):
        """BASELINE result must be deeply equal to HARNESS_NO_EXTENSIONS result."""
        params = nm.default_params()

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_NO_EXTENSIONS,
                         rng=_fresh_rng(42))

        self.assertTrue(deep_equal(out_a["result"], out_b["result"]),
                       "BASELINE and HARNESS_NO_EXTENSIONS results must be identical")

    # ── Test 2: BASELINE trace == HARNESS_WITH_EXTENSIONS (noop) ────

    def test_baseline_trace_equals_noop_trace(self):
        """BASELINE result must be deeply equal to HARNESS_WITH_EXTENSIONS (noop) result."""
        params = nm.default_params()
        noop = NoopExtension()

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[noop], rng=_fresh_rng(42))

        self.assertTrue(deep_equal(out_a["result"], out_b["result"]),
                       "BASELINE and HARNESS_WITH_EXTENSIONS (noop) results must be identical")

    # ── Test 3: Hash equality across all 3 modes ────────────────────

    def test_hash_equality_across_modes(self):
        """All 3 modes must produce identical SHA-256 hashes for the same inputs."""
        params = nm.default_params()
        noop = NoopExtension()

        hashes = {}
        for mode in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            nodes = _make_two_nodes()
            out = run_local(nodes, params, mode=mode,
                          extensions=[noop] if mode == Mode.HARNESS_WITH_EXTENSIONS else None,
                          rng=_fresh_rng(42))
            hashes[mode] = hash_result(out["result"])

        h_base = hashes[Mode.BASELINE]
        self.assertEqual(len(h_base), 64)
        self.assertEqual(h_base, hashes[Mode.HARNESS_NO_EXTENSIONS],
                        "Hash mismatch: BASELINE vs NO_EXTENSIONS")
        self.assertEqual(h_base, hashes[Mode.HARNESS_WITH_EXTENSIONS],
                        "Hash mismatch: BASELINE vs WITH_EXTENSIONS")

    # ── Test 4: Cluster mode trace compatibility ────────────────────

    def test_cluster_trace_compatibility(self):
        """All 3 cluster modes must produce identical results."""
        seed, steps = 7, 5
        noop = NoopExtension()

        out_a = run_cluster(seed=seed, steps=steps, mode=Mode.BASELINE)
        out_b = run_cluster(seed=seed, steps=steps, mode=Mode.HARNESS_NO_EXTENSIONS)
        out_c = run_cluster(seed=seed, steps=steps, mode=Mode.HARNESS_WITH_EXTENSIONS,
                           extensions=[noop])

        ha = hash_result(out_a["result"])
        hb = hash_result(out_b["result"])
        hc = hash_result(out_c["result"])

        self.assertEqual(ha, hb, "Cluster BASELINE vs NO_EXTENSIONS hash mismatch")
        self.assertEqual(ha, hc, "Cluster BASELINE vs WITH_EXTENSIONS hash mismatch")

    # ── Test 5: Hook events are JSON-serializable ──────────────────

    def test_hook_events_json_serializable(self):
        """Hook events in harness output must be JSON-serializable."""
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()

        out = run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                       extensions=[noop], rng=_fresh_rng(42))

        hook_events = out.get("hook_events", [])
        self.assertGreater(len(hook_events), 0, "Noop extension should generate hook events")

        # Must be JSON-serializable
        try:
            json.dumps(hook_events)
        except (TypeError, ValueError) as e:
            self.fail(f"Hook events not JSON-serializable: {e}")

    # ── Test 6: Harness trace structure is well-formed ──────────────

    def test_harness_trace_structure(self):
        """Harness output must have well-formed structure with required keys."""
        params = nm.default_params()
        noop = NoopExtension()
        nodes = _make_two_nodes()

        out = run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                       extensions=[noop], rng=_fresh_rng(42))

        # Required keys
        self.assertIn("mode", out)
        self.assertIn("result", out)
        self.assertIn("provenance", out)
        self.assertIn("hook_events", out)
        self.assertIn("extension_manifests", out)

        # Provenance structure
        prov = out["provenance"]
        self.assertIn("mode", prov)
        self.assertIn("result_sha256", prov)
        self.assertIn("provenance_format_version", prov)
        self.assertIn("harness_id", prov)

        # Result is valid
        s = serialize_run_output(out["result"])
        try:
            json.dumps(s)
        except (TypeError, ValueError) as e:
            self.fail(f"Result not JSON-serializable: {e}")

    # ── Test 7: No trace diffs between modes ────────────────────────

    def test_no_trace_diffs_between_modes(self):
        """structured_diff should report zero diffs between all 3 modes."""
        params = nm.default_params()
        noop = NoopExtension()

        results = {}
        for mode in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            nodes = _make_two_nodes()
            out = run_local(nodes, params, mode=mode,
                          extensions=[noop] if mode == Mode.HARNESS_WITH_EXTENSIONS else None,
                          rng=_fresh_rng(42))
            results[mode] = out["result"]

        diffs_01 = structured_diff(results[Mode.BASELINE], results[Mode.HARNESS_NO_EXTENSIONS])
        self.assertEqual(len(diffs_01), 0,
                        f"Unexpected diffs BASELINE vs NO_EXTENSIONS: {diffs_01}")

        diffs_02 = structured_diff(results[Mode.BASELINE], results[Mode.HARNESS_WITH_EXTENSIONS])
        self.assertEqual(len(diffs_02), 0,
                        f"Unexpected diffs BASELINE vs WITH_EXTENSIONS: {diffs_02}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
