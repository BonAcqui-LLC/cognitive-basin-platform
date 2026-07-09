"""RNG Equivalence Tests — Stage 2 Extension Harness.

Verify that the harness preserves exact baseline RNG behavior.

Tests:
  1. No-op execution preserves exact baseline draw traces
  2. No-op adds zero additional baseline RNG draws
  3. Extension state initialization consumes no hidden randomness
  4. Python global random is not consulted
  5. TraceRng draw count identical across all 3 modes
"""

import sys
import unittest
import random as py_random

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE")

import natural_math_v5 as nm
from natural_math_v5.records import make_node
from natural_math_v5.randomness import TraceRng, sample_two

from extension_harness import (
    Mode,
    NoopExtension,
    ExtensionManifest,
    ExtensionRegistry,
    ExtensionRng,
    ExtensionRngPolicy,
    run_local,
    run_cluster,
    hash_result,
    deep_equal,
    snapshot_nodes,
)

py_random.seed(0)  # Guard: verify global random not consulted


def _make_two_nodes():
    return [
        make_node(1, (0, 0, 0), energy=1000000, node_type="seed"),
        make_node(2, (2, 0, 0), energy=1000000, node_type="tip"),
    ]


def _fresh_rng(seed=42):
    return TraceRng(seed)


class TestRngEquivalence(unittest.TestCase):

    # ── Test 1: No-op preserves exact baseline draw traces ───────────

    def test_noop_preserves_draw_traces(self):
        """No-op execution produces identical RNG draw traces as baseline."""
        params = nm.default_params()

        rng_a = _fresh_rng(42)
        nodes_a = _make_two_nodes()
        run_local(nodes_a, params, mode=Mode.BASELINE, rng=rng_a)

        rng_b = _fresh_rng(42)
        noop = NoopExtension()
        nodes_b = _make_two_nodes()
        run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=rng_b)

        # Draw traces must be identical
        self.assertEqual(rng_a.draws, rng_b.draws,
                        f"Draw traces must be identical: {rng_a.draws} vs {rng_b.draws}")

    # ── Test 2: No-op adds zero additional baseline RNG draws ────────

    def test_noop_adds_zero_baseline_draws(self):
        """No-op extension must not consume any baseline RNG draws."""
        params = nm.default_params()

        rng_a = _fresh_rng(42)
        nodes_a = _make_two_nodes()
        run_local(nodes_a, params, mode=Mode.BASELINE, rng=rng_a)
        draw_count_a = len(rng_a.draws)

        rng_b = _fresh_rng(42)
        noop = NoopExtension()
        nodes_b = _make_two_nodes()
        run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=rng_b)
        draw_count_b = len(rng_b.draws)

        self.assertEqual(draw_count_a, draw_count_b,
                        f"No-op must not add draws: {draw_count_a} vs {draw_count_b}")

    # ── Test 3: Extension state init consumes no hidden randomness ───

    def test_extension_init_no_randomness(self):
        """Creating extension instances must not consume randomness."""
        # Record global random state before
        start_state = py_random.getstate()

        for _ in range(100):
            noop = NoopExtension()
            _ = noop.get_manifest()

        end_state = py_random.getstate()

        # Global random should not have been consulted
        self.assertEqual(start_state, end_state,
                        "Extension init must not consume Python global randomness")

    # ── Test 4: Global random not consulted during no-op run ─────────

    def test_global_random_not_consulted(self):
        """No-op harness execution must not consult Python global random."""
        params = nm.default_params()
        noop = NoopExtension()

        # Set global random to a known state
        py_random.seed(999)
        state_before = py_random.getstate()

        nodes = _make_two_nodes()
        run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                 extensions=[noop], rng=_fresh_rng(42))

        state_after = py_random.getstate()

        # Global random state should be unchanged
        self.assertEqual(state_before, state_after,
                        "Harness must not consult Python global random")

    # ── Test 5: ExtensionRng is deactivated ──────────────────────────

    def test_extension_rng_deactivated(self):
        """ExtensionRng must be deactivated and return zero draws."""
        rng = ExtensionRng(policy=ExtensionRngPolicy.NO_RANDOMNESS)
        self.assertFalse(rng.is_active())
        self.assertEqual(rng.get_draw_count(), 0)
        with self.assertRaises(RuntimeError):
            rng.randrange(0, 100)

    # ── Test 6: All 3 modes produce identical RNG traces ─────────────

    def test_all_modes_identical_rng_traces(self):
        """BASELINE, NO_EXTENSIONS, and WITH_EXTENSIONS produce identical draw traces."""
        params = nm.default_params()
        noop = NoopExtension()

        draws_per_mode = {}
        for mode in [Mode.BASELINE, Mode.HARNESS_NO_EXTENSIONS, Mode.HARNESS_WITH_EXTENSIONS]:
            rng = _fresh_rng(42)
            nodes = _make_two_nodes()
            run_local(nodes, params, mode=mode,
                     extensions=[noop] if mode == Mode.HARNESS_WITH_EXTENSIONS else None,
                     rng=rng)
            draws_per_mode[mode] = rng.draws

        self.assertEqual(draws_per_mode[Mode.BASELINE],
                        draws_per_mode[Mode.HARNESS_NO_EXTENSIONS])
        self.assertEqual(draws_per_mode[Mode.BASELINE],
                        draws_per_mode[Mode.HARNESS_WITH_EXTENSIONS])


if __name__ == "__main__":
    unittest.main(verbosity=2)
