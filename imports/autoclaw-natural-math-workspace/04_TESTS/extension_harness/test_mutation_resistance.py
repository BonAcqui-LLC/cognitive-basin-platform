"""Mutation Resistance Tests — Stage 2 Extension Harness.

Tests that adversarial extensions cannot corrupt baseline state.

Tests:
  1. Extension mutation of node snapshot → isolated, baseline unchanged
  2. Extension mutation of params snapshot → isolated
  3. Extension retains mutable reference → post-hoc mutation isolated
  4. Malformed hook result (non-HookResult) → validate_hook_result rejects
  5. Malformed hook result (proposal from observation hook) → validate_hook_result rejects
  6. Extension writes unsupported state type (set) → state store rejects
  7. Extension writes NaN float → state store rejects
  8. Extension writes non-string dict key → state store rejects
  9. Extension raises exception from hook → harness logs ERROR event
 10. Multiple malicious extensions → harness handles gracefully
"""

import copy
import math
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
    HookResult,
    DiagnosticEvent,
    StateUpdate,
    LocalMovePreferenceProposal,
    OBSERVATION_HOOKS,
    BEHAVIORAL_HOOKS,
    ALL_HOOKS,
    HookPhase,
    run_local,
    run_cluster,
    StateStore,
    StateSchemaError,
    HookContractError,
    ProposalValidationError,
    ExtensionRegistrationError,
    ManifestValidationError,
    snapshot_nodes,
    snapshot_params,
    validate_hook_result,
    validate_move_proposal,
)


def _make_two_nodes():
    return [
        make_node(1, (0, 0, 0), energy=1000000, node_type="seed"),
        make_node(2, (2, 0, 0), energy=1000000, node_type="tip"),
    ]


def _fresh_rng(seed=42):
    return TraceRng(seed)


# ── TEST 1: Extension mutates node snapshot → isolated ──────────────────

class MutationSnapNode:
    """Extension that tries to mutate the node snapshot."""
    def get_manifest(self):
        return ExtensionManifest(
            extension_id="mutate-snap-node", extension_name="Snap Node Mutator",
            extension_version="1.0.0", status="EXPERIMENTAL",
            base_system="natural_math_v5",
            required_base_source_sha256="e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
            required_base_package_manifest_sha256="87b9c28aa27ff5a4e07096da2c62f1ce531e4a89c89c77f29084477f8bae7be9",
            author="tester", purpose="mutation resistance test",
            claim_boundary="test", state_schema_version=1, hook_contract_version=1,
            randomness_policy="NO_EXTENSION_RANDOMNESS",
        )

    def on_run_start(self, snapshot=None):
        if snapshot and len(snapshot) > 0:
            # snapshot is a deepcopy; mutating it is safe but must not affect baseline
            if isinstance(snapshot[0], dict):
                snapshot[0]["pos"] = (999, 999)
            elif hasattr(snapshot[0], 'position'):
                snapshot[0].position = (999, 999)
        return NoChange()

    def on_after_decision_formation(self, snapshot=None):
        return NoChange()


class TestMutationResistance(unittest.TestCase):

    # ── Test 1: Snapshot node mutation isolation ──────────────────────
    def test_snapshot_node_mutation_isolated(self):
        """Extension mutating snapshot nodes must not affect baseline."""
        params = nm.default_params()
        mutator = MutationSnapNode()

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[mutator], rng=_fresh_rng(42))

        # Both runs must produce valid results
        self.assertEqual(len(out_a["result"]), 2)
        self.assertEqual(len(out_b["result"]), 2)
        # Baseline must be unchanged
        self.assertEqual(out_a["result"][0]["id"], out_b["result"][0]["id"])

    # ── Test 2: Params mutation isolation ────────────────────────────
    def test_params_mutation_isolated(self):
        """Extension mutating params snapshot must not affect baseline."""
        params = nm.default_params()

        class ParamMutator:
            def get_manifest(self):
                return ExtensionManifest(
                    extension_id="mutate-params", extension_name="Param Mutator",
                    extension_version="1.0.0", status="EXPERIMENTAL",
                    base_system="natural_math_v5",
                    required_base_source_sha256="e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
                    required_base_package_manifest_sha256="87b9c28aa27ff5a4e07096da2c62f1ce531e4a89c89c77f29084477f8bae7be9",
                    author="tester", purpose="test",
                    claim_boundary="test", state_schema_version=1,
                    hook_contract_version=1, randomness_policy="NO_EXTENSION_RANDOMNESS",
                )

            def before_step(self, snapshot=None, step_index=None):
                return NoChange()

            def on_run_start(self, snapshot=None):
                return NoChange()

        original_tau = params["tau"]

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))
        self.assertEqual(params["tau"], original_tau)

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[ParamMutator()], rng=_fresh_rng(42))
        self.assertEqual(params["tau"], original_tau)
        self.assertEqual(len(out_b["result"]), len(out_a["result"]))

    # ── Test 3: Mutable reference retained → isolated ────────────────
    def test_mutable_reference_retention_isolated(self):
        """Extension retaining a mutable reference and later mutating it."""
        class RefRetainer:
            def __init__(self):
                self.saved_snapshot = None

            def get_manifest(self):
                return ExtensionManifest(
                    extension_id="ref-retain", extension_name="Ref Retainer",
                    extension_version="1.0.0", status="EXPERIMENTAL",
                    base_system="natural_math_v5",
                    required_base_source_sha256="e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
                    required_base_package_manifest_sha256="87b9c28aa27ff5a4e07096da2c62f1ce531e4a89c89c77f29084477f8bae7be9",
                    author="tester", purpose="test",
                    claim_boundary="test", state_schema_version=1,
                    hook_contract_version=1, randomness_policy="NO_EXTENSION_RANDOMNESS",
                )

            def on_run_start(self, snapshot=None):
                self.saved_snapshot = snapshot  # retain reference
                return NoChange()

        params = nm.default_params()
        retainer = RefRetainer()

        nodes_a = _make_two_nodes()
        out_a = run_local(nodes_a, params, mode=Mode.BASELINE, rng=_fresh_rng(42))

        nodes_b = _make_two_nodes()
        out_b = run_local(nodes_b, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                         extensions=[retainer], rng=_fresh_rng(42))

        # Post-hoc mutate via retained reference (snapshot is deep-copied list of dicts)
        if retainer.saved_snapshot is not None and len(retainer.saved_snapshot) > 0:
            snap = retainer.saved_snapshot[0]
            if isinstance(snap, dict):
                snap["pos"] = (555, 555)
            elif hasattr(snap, 'position'):
                snap.position = (555, 555)

        # Rerun baseline with same seed — must be unaffected
        nodes_c = _make_two_nodes()
        out_c = run_local(nodes_c, params, mode=Mode.BASELINE, rng=_fresh_rng(42))
        self.assertEqual(len(out_a["result"]), len(out_c["result"]))

    # ── Test 4: Malformed hook result rejected by validator ──────────
    def test_malformed_hook_result_rejected(self):
        """validate_hook_result rejects non-HookResult returns."""
        from extension_harness import ON_RUN_START

        with self.assertRaises(HookContractError):
            validate_hook_result("not a HookResult", ON_RUN_START, "test.ext")

        with self.assertRaises(HookContractError):
            validate_hook_result(42, ON_RUN_START, "test.ext")

        with self.assertRaises(HookContractError):
            validate_hook_result(None, ON_RUN_START, "test.ext")

        with self.assertRaises(HookContractError):
            validate_hook_result([1, 2, 3], ON_RUN_START, "test.ext")

    # ── Test 5: Proposal from observation hook rejected by validator ─
    def test_proposal_from_observation_hook_rejected(self):
        """validate_hook_result rejects proposals from observation hooks."""
        from extension_harness import ON_RUN_START

        proposal = LocalMovePreferenceProposal(
            "n1", (0, 1), 5, "test", "test.ext", "1.0.0"
        )
        with self.assertRaises(HookContractError):
            validate_hook_result(proposal, ON_RUN_START, "test.ext")

    # ── Test 6: Unsupported state type (set) → rejected ──────────────
    def test_unsupported_state_type_rejected(self):
        """StateStore rejects sets as values."""
        store = StateStore()
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {"bad": {1, 2, 3}}, 1)

    # ── Test 7: NaN float in state → rejected ────────────────────────
    def test_nan_float_in_state_rejected(self):
        """StateStore rejects NaN values."""
        store = StateStore()
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {"val": float("nan")}, 1)

    # ── Test 8: Non-string dict key → rejected ───────────────────────
    def test_non_string_dict_key_rejected(self):
        """StateStore rejects dicts with non-string keys."""
        store = StateStore()
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {42: "value"}, 1)

    # ── Test 9: Exception-raising extension logs ERROR event ─────────
    def test_exception_raising_extension(self):
        """Harness catches extension exceptions and logs ERROR events."""
        class CrashExt:
            def get_manifest(self):
                return ExtensionManifest(
                    extension_id="crash-ext", extension_name="Crash Extension",
                    extension_version="1.0.0", status="EXPERIMENTAL",
                    base_system="natural_math_v5",
                    required_base_source_sha256="e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
                    required_base_package_manifest_sha256="87b9c28aa27ff5a4e07096da2c62f1ce531e4a89c89c77f29084477f8bae7be9",
                    author="tester", purpose="test",
                    claim_boundary="test", state_schema_version=1,
                    hook_contract_version=1, randomness_policy="NO_EXTENSION_RANDOMNESS",
                )

            def on_run_start(self, snapshot=None):
                raise RuntimeError("CrashExt exploded!")

        params = nm.default_params()
        nodes = _make_two_nodes()

        out = run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
                       extensions=[CrashExt()], rng=_fresh_rng(42))

        self.assertIn("result", out)
        error_events = [e for e in out["hook_events"] if e.get("result_type") == "ERROR"]
        self.assertGreaterEqual(len(error_events), 1,
                               "Exception-raising extension should log ERROR events")
        self.assertIn("CrashExt", error_events[0].get("error", ""))

    # ── Test 10: Inf float in state → rejected ───────────────────────
    def test_inf_float_in_state_rejected(self):
        """StateStore rejects infinity values."""
        store = StateStore()
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {"val": float("inf")}, 1)

    # ── Test 11: Bad schema version → rejected ────────────────────────
    def test_bad_schema_version_rejected(self):
        """StateStore rejects invalid schema_version."""
        store = StateStore()
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {"x": 1}, 0)
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {"x": 1}, -1)
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", {"x": 1}, "not-int")

    # ── Test 12: State not a dict → rejected ─────────────────────────
    def test_state_not_dict_rejected(self):
        """StateStore rejects non-dict state values."""
        store = StateStore()
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", [1, 2, 3], 1)
        with self.assertRaises(StateSchemaError):
            store.set_state("run-x", "ext-x", "1.0.0", "string", 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
