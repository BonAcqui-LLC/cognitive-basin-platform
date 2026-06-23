"""Verification tests for the Stage 2 extension harness core infrastructure."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "03_EXPERIMENTS"))


class FakeNode:
    def __init__(self, node_id, x, y, alive=True):
        self.id = node_id
        self.position = (x, y)
        self.alive = alive
        self.bonds = set()

SHA_A = "a" * 64
SHA_B = "b" * 64

VALID_MANIFEST_DATA = {
    "extension_id": "test.ext",
    "extension_name": "Test Extension",
    "extension_version": "0.1.0",
    "status": "EXPERIMENTAL",
    "base_system": "natural_math_v5",
    "required_base_source_sha256": SHA_A,
    "required_base_package_manifest_sha256": SHA_B,
    "author": "tester",
    "purpose": "testing",
    "claim_boundary": "observation",
    "state_schema_version": 1,
    "hook_contract_version": 1,
    "randomness_policy": "NO_EXTENSION_RANDOMNESS",
}


def test_import():
    from extension_harness import (
        HarnessError, ExtensionRegistrationError, ManifestValidationError,
        StateSchemaError, HookContractError, RandomnessPolicyError,
        ProposalValidationError, BaselineImmutabilityError, SnapshotMutationError,
        ON_RUN_START, BEFORE_STEP, AFTER_DECISION_FORMATION,
        AFTER_BIFURCATION_RESERVATION, AFTER_MOVEMENT_RESOLUTION,
        AFTER_PRESSURE_UPDATE, AFTER_BONDING, AFTER_CLUSTER_ACTION_SELECTION,
        AFTER_CLUSTER_ACTION, AFTER_RESOURCE_ABSORPTION, AFTER_STEP, ON_RUN_END,
        PROPOSE_LOCAL_MOVE_PREFERENCE, OBSERVATION_HOOKS, BEHAVIORAL_HOOKS,
        ALL_HOOKS, VALID_EXTENSION_STATUSES, VALID_RANDOMNESS_POLICIES,
        HookResult, NoChange, StateUpdate, LocalMovePreferenceProposal,
        DiagnosticEvent, ExtensionManifest, RunContext,
        snapshot_nodes, snapshot_params, snapshot_occupancy,
        snapshot_decisions, snapshot_movement_attempts,
        snapshot_bifurcation_reservations, snapshot_cluster_metrics,
        snapshot_resource_state, StateStore,
        validate_hook_result, validate_move_proposal, ExtensionRegistry,
    )
    assert HarnessError is not None
    assert ALL_HOOKS is not None
    print("  PASS test_import")
    return True


def test_manifest_valid():
    from extension_harness import ExtensionManifest
    m = ExtensionManifest.from_dict(VALID_MANIFEST_DATA)
    assert m.extension_id == "test.ext"
    assert m.extension_version == "0.1.0"
    d = m.to_dict()
    assert d["extension_id"] == "test.ext"
    assert "created_timestamp" not in d
    print("  PASS test_manifest_valid")
    return True


def test_manifest_invalid_id_empty():
    from extension_harness import ManifestValidationError, ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["extension_id"] = ""
    try:
        ExtensionManifest.from_dict(data)
        assert False
    except ManifestValidationError:
        pass
    print("  PASS test_manifest_invalid_id_empty")
    return True


def test_manifest_invalid_version():
    from extension_harness import ManifestValidationError, ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["extension_version"] = "not-semver"
    try:
        ExtensionManifest.from_dict(data)
        assert False
    except ManifestValidationError:
        pass
    print("  PASS test_manifest_invalid_version")
    return True


def test_manifest_invalid_status():
    from extension_harness import ManifestValidationError, ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["status"] = "BOGUS"
    try:
        ExtensionManifest.from_dict(data)
        assert False
    except ManifestValidationError:
        pass
    print("  PASS test_manifest_invalid_status")
    return True


def test_manifest_invalid_sha():
    from extension_harness import ManifestValidationError, ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["required_base_source_sha256"] = "not-hex-" + "0" * 56
    try:
        ExtensionManifest.from_dict(data)
        assert False
    except ManifestValidationError:
        pass
    print("  PASS test_manifest_invalid_sha")
    return True


def test_manifest_invalid_schema_version():
    from extension_harness import ManifestValidationError, ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["state_schema_version"] = 0
    try:
        ExtensionManifest.from_dict(data)
        assert False
    except ManifestValidationError:
        pass
    print("  PASS test_manifest_invalid_schema_version")
    return True


def test_manifest_invalid_randomness_policy():
    from extension_harness import ManifestValidationError, ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["randomness_policy"] = "RANDOM_POLICY_BOGUS"
    try:
        ExtensionManifest.from_dict(data)
        assert False
    except ManifestValidationError:
        pass
    print("  PASS test_manifest_invalid_randomness_policy")
    return True


def test_manifest_missing_keys():
    from extension_harness import ManifestValidationError, ExtensionManifest
    try:
        ExtensionManifest.from_dict({"extension_id": "x"})
        assert False
    except ManifestValidationError as e:
        assert "Missing required keys" in str(e)
    print("  PASS test_manifest_missing_keys")
    return True


def test_manifest_with_timestamp():
    from extension_harness import ExtensionManifest
    data = dict(VALID_MANIFEST_DATA)
    data["created_timestamp"] = "2026-06-23T15:00:00Z"
    m = ExtensionManifest.from_dict(data)
    d = m.to_dict()
    assert d["created_timestamp"] == "2026-06-23T15:00:00Z"
    print("  PASS test_manifest_with_timestamp")
    return True


def test_registry_duplicate_rejection():
    from extension_harness import (
        ExtensionManifest, ExtensionRegistry, ExtensionRegistrationError
    )
    m1 = ExtensionManifest.from_dict(VALID_MANIFEST_DATA)
    reg = ExtensionRegistry()
    reg.register(object(), m1)
    try:
        reg.register(object(), m1)
        assert False
    except ExtensionRegistrationError:
        pass
    print("  PASS test_registry_duplicate_rejection")
    return True


def test_registry_same_id_different_version():
    from extension_harness import ExtensionManifest, ExtensionRegistry
    m1 = ExtensionManifest.from_dict(VALID_MANIFEST_DATA)
    data2 = dict(VALID_MANIFEST_DATA)
    data2["extension_version"] = "0.2.0"
    m2 = ExtensionManifest.from_dict(data2)
    reg = ExtensionRegistry()
    reg.register(object(), m1)
    reg.register(object(), m2)
    assert len(reg) == 2
    assert len(reg.get_by_id("test.ext")) == 2
    print("  PASS test_registry_same_id_different_version")
    return True


def test_registry_get_hooks():
    from extension_harness import (
        ExtensionManifest, ExtensionRegistry, ON_RUN_START, BEFORE_STEP
    )
    class ExtA:
        def ON_RUN_START(self, *a, **kw): pass
    class ExtB:
        def BEFORE_STEP(self, *a, **kw): pass
    m = ExtensionManifest.from_dict(VALID_MANIFEST_DATA)
    reg = ExtensionRegistry()
    reg.register(ExtA(), m)
    data2 = dict(VALID_MANIFEST_DATA)
    data2["extension_id"] = "other.ext"
    data2["extension_version"] = "1.0.0"
    m2 = ExtensionManifest.from_dict(data2)
    reg.register(ExtB(), m2)
    assert len(reg.get_hooks(ON_RUN_START)) == 1
    assert len(reg.get_hooks(BEFORE_STEP)) == 1
    assert len(reg.get_hooks("NONEXISTENT")) == 0
    print("  PASS test_registry_get_hooks")
    return True


def test_snapshot_nodes_immutable_bonds():
    from extension_harness import snapshot_nodes
    n1 = FakeNode("a", 0, 0)
    n1.bonds = {"b", "c"}
    snap = snapshot_nodes([n1])
    assert isinstance(snap[0].bonds, frozenset)
    assert isinstance(n1.bonds, set)
    print("  PASS test_snapshot_nodes_immutable_bonds")
    return True


def test_snapshot_nodes_deepcopy_isolation():
    from extension_harness import snapshot_nodes
    n1 = FakeNode("a", 0, 0)
    snap = snapshot_nodes([n1])
    snap[0].position = (99, 99)
    assert n1.position == (0, 0)
    print("  PASS test_snapshot_nodes_deepcopy_isolation")
    return True


def test_snapshot_occupancy():
    from extension_harness import snapshot_occupancy
    nodes = [FakeNode("a", 1, 2), FakeNode("b", 3, 4)]
    occ = snapshot_occupancy(nodes)
    assert isinstance(occ, frozenset)
    assert (1, 2) in occ
    print("  PASS test_snapshot_occupancy")
    return True


def test_snapshot_params_isolation():
    from extension_harness import snapshot_params
    original = {"alpha": 1.0, "nested": {"x": 42}}
    snap = snapshot_params(original)
    snap["alpha"] = 99.0
    snap["nested"]["x"] = 999
    assert original["alpha"] == 1.0
    assert original["nested"]["x"] == 42
    print("  PASS test_snapshot_params_isolation")
    return True


def test_state_store_isolation():
    from extension_harness import StateStore
    store = StateStore()
    store.set_state("run-1", "ext.a", "0.1.0", {"count": 1}, 1)
    store.set_state("run-2", "ext.a", "0.1.0", {"count": 2}, 1)
    assert store.get_state("run-1", "ext.a", "0.1.0")["count"] == 1
    assert store.get_state("run-2", "ext.a", "0.1.0")["count"] == 2
    print("  PASS test_state_store_isolation")
    return True


def test_state_store_reset_run():
    from extension_harness import StateStore
    store = StateStore()
    store.set_state("run-1", "ext.a", "0.1.0", {"x": 1}, 1)
    store.set_state("run-2", "ext.a", "0.1.0", {"x": 2}, 1)
    store.reset_run("run-1")
    assert store.get_state("run-1", "ext.a", "0.1.0") == {}
    assert store.get_state("run-2", "ext.a", "0.1.0") == {"x": 2}
    print("  PASS test_state_store_reset_run")
    return True


def test_state_store_reset_all():
    from extension_harness import StateStore
    store = StateStore()
    store.set_state("run-1", "ext.a", "0.1.0", {"x": 1}, 1)
    store.reset_all()
    assert store.get_state("run-1", "ext.a", "0.1.0") == {}
    print("  PASS test_state_store_reset_all")
    return True


def test_state_store_return_copy():
    from extension_harness import StateStore
    store = StateStore()
    store.set_state("run-1", "ext.a", "0.1.0", {"count": 1}, 1)
    s = store.get_state("run-1", "ext.a", "0.1.0")
    s["count"] = 999
    assert store.get_state("run-1", "ext.a", "0.1.0")["count"] == 1
    print("  PASS test_state_store_return_copy")
    return True


def test_state_store_invalid_types():
    from extension_harness import StateStore, StateSchemaError
    store = StateStore()
    try:
        store.set_state("r", "e", "0.1.0", {"bad": {1, 2, 3}}, 1)
        assert False
    except StateSchemaError:
        pass
    try:
        store.set_state("r", "e", "0.1.0", {42: "value"}, 1)
        assert False
    except StateSchemaError:
        pass
    try:
        store.set_state("r", "e", "0.1.0", {"val": float("nan")}, 1)
        assert False
    except StateSchemaError:
        pass
    print("  PASS test_state_store_invalid_types")
    return True


def test_validate_hook_result_observation():
    from extension_harness import (
        NoChange, DiagnosticEvent, LocalMovePreferenceProposal,
        validate_hook_result, HookContractError,
        ON_RUN_START, BEFORE_STEP,
    )
    ext_id = "test.ext"
    validate_hook_result(NoChange(), ON_RUN_START, ext_id)
    validate_hook_result(DiagnosticEvent("hello"), BEFORE_STEP, ext_id)
    proposal = LocalMovePreferenceProposal(
        "n1", (0, 1), 5, "test", ext_id, "0.1.0"
    )
    try:
        validate_hook_result(proposal, ON_RUN_START, ext_id)
        assert False
    except HookContractError:
        pass
    try:
        validate_hook_result("not a result", ON_RUN_START, ext_id)
        assert False
    except HookContractError:
        pass
    print("  PASS test_validate_hook_result_observation")
    return True


def test_validate_hook_result_behavioral():
    from extension_harness import (
        LocalMovePreferenceProposal, validate_hook_result,
        PROPOSE_LOCAL_MOVE_PREFERENCE, HookContractError,
    )
    ext_id = "test.ext"
    proposal = LocalMovePreferenceProposal("n1", (0, 1), 5, "test", ext_id, "0.1.0")
    validate_hook_result(proposal, PROPOSE_LOCAL_MOVE_PREFERENCE, ext_id)
    bad = LocalMovePreferenceProposal("n1", (0, 1), 5, "test", "wrong.id", "0.1.0")
    try:
        validate_hook_result(bad, PROPOSE_LOCAL_MOVE_PREFERENCE, ext_id)
        assert False
    except HookContractError:
        pass
    print("  PASS test_validate_hook_result_behavioral")
    return True


def test_validate_move_proposal():
    from extension_harness import (
        LocalMovePreferenceProposal, validate_move_proposal,
    )
    nodes = [FakeNode("a", 1, 1), FakeNode("b", 1, 2)]
    params = {"width": 5, "height": 5}
    occupancy = frozenset({(1, 1), (1, 2)})
    reserved = frozenset({(3, 3)})

    def mk_prop(node_id, direction, adj=5):
        return LocalMovePreferenceProposal(node_id, direction, adj, "rc", "eid", "0.1.0")

    v, r = validate_move_proposal(mk_prop("a", (1, 0)), nodes, params, occupancy, reserved)
    assert v, r
    v, r = validate_move_proposal(mk_prop("a", (1, 1)), nodes, params, occupancy, reserved)
    assert not v and "non-cardinal" in r
    v, r = validate_move_proposal(mk_prop("a", (0, 1)), nodes, params, occupancy, reserved)
    assert not v and "occupied" in r
    v, r = validate_move_proposal(mk_prop("nonexistent", (1, 0)), nodes, params, occupancy, reserved)
    assert not v and "not found" in r
    dead = FakeNode("dead", 2, 2, alive=False)
    v, r = validate_move_proposal(mk_prop("dead", (1, 0)), [dead], params, frozenset({(2, 2)}), reserved)
    assert not v and "dead" in r
    nodes2 = [FakeNode("c", 3, 2)]
    v, r = validate_move_proposal(mk_prop("c", (0, 1)), nodes2, params, frozenset({(3, 2)}), reserved)
    assert not v and "reserved" in r
    v, r = validate_move_proposal(
        LocalMovePreferenceProposal("a", (1, 0), 3.14, "rc", "eid", "0.1.0"),
        nodes, params, occupancy, reserved,
    )
    assert not v and "must be int" in r
    print("  PASS test_validate_move_proposal")
    return True


def test_error_hierarchy():
    from extension_harness import (
        HarnessError, ExtensionRegistrationError, ManifestValidationError,
        StateSchemaError, HookContractError, RandomnessPolicyError,
        ProposalValidationError, BaselineImmutabilityError, SnapshotMutationError,
    )
    for cls in [
        ExtensionRegistrationError, ManifestValidationError, StateSchemaError,
        HookContractError, RandomnessPolicyError, ProposalValidationError,
        BaselineImmutabilityError, SnapshotMutationError,
    ]:
        assert issubclass(cls, HarnessError)
    print("  PASS test_error_hierarchy")
    return True


def test_hook_result_types():
    from extension_harness import (
        HookResult, NoChange, StateUpdate, LocalMovePreferenceProposal, DiagnosticEvent,
    )
    nc = NoChange()
    assert nc.is_no_change() and not nc.is_state_update() and not nc.is_proposal()
    su = StateUpdate({"k": "v"})
    assert su.is_state_update() and su.state_patch == {"k": "v"}
    prop = LocalMovePreferenceProposal("n1", (0, 1), 5, "rc", "eid", "0.1.0")
    assert prop.is_proposal() and prop.node_id == "n1"
    diag = DiagnosticEvent("testing")
    assert diag.message == "testing"
    base = HookResult()
    assert not (base.is_no_change() or base.is_state_update() or base.is_proposal())
    print("  PASS test_hook_result_types")
    return True


def test_run_context():
    from extension_harness import RunContext
    ctx = RunContext("run-001", "test", 42, {"w": 10, "h": 10}, 100, SHA_A, SHA_B, "ts")
    assert ctx.run_id == "run-001" and ctx.seed == 42
    prov = ctx.to_provenance()
    assert prov["run_id"] == "run-001"
    print("  PASS test_run_context")
    return True


def run_all():
    tests = [
        test_import, test_manifest_valid, test_manifest_invalid_id_empty,
        test_manifest_invalid_version, test_manifest_invalid_status,
        test_manifest_invalid_sha, test_manifest_invalid_schema_version,
        test_manifest_invalid_randomness_policy, test_manifest_missing_keys,
        test_manifest_with_timestamp, test_registry_duplicate_rejection,
        test_registry_same_id_different_version, test_registry_get_hooks,
        test_snapshot_nodes_immutable_bonds, test_snapshot_nodes_deepcopy_isolation,
        test_snapshot_occupancy, test_snapshot_params_isolation,
        test_state_store_isolation, test_state_store_reset_run,
        test_state_store_reset_all, test_state_store_return_copy,
        test_state_store_invalid_types, test_validate_hook_result_observation,
        test_validate_hook_result_behavioral, test_validate_move_proposal,
        test_run_context, test_hook_result_types, test_error_hierarchy,
    ]
    passed = failed = 0
    for t in tests:
        try:
            if t():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
            import traceback; traceback.print_exc()
            failed += 1
    print(f"\n{'='*60}\nResults: {passed} passed, {failed} failed out of {len(tests)}")
    return failed == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if run_all() else 1)
