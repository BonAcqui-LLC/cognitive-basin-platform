"""
Contradiction scar, recovery, and association tests for BasinLab.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ternary.states import EpistemicState
from python.basinlab.associations import AssociationBeacon, AssociationBrush, AssociationField
from python.basinlab.planner import GeneralistPlanner
from python.basinlab.recovery import RecoveryAttempt, RecoveryManager, RecoveryRequirement, RecoveryRoute
from python.basinlab.scars import ScarRegistry


def test_supported_to_contradicted_creates_scar():
    registry = ScarRegistry()
    scar = registry.record_scar(
        claim_id="claim-1",
        trajectory_id="traj-1",
        prior_epistemic_state=EpistemicState.SUPPORTED,
        contradictory_evidence=["evidence-a"],
        source="deterministic-check",
        confidence=0.9,
        unresolved_questions=["why mismatch"],
        recovery_eligibility=True,
        provenance="unit-test",
    )
    assert scar.prior_epistemic_state == EpistemicState.SUPPORTED
    assert len(registry.all_scars()) == 1


def test_unresolved_to_contradicted_preserves_prior_state_honestly():
    registry = ScarRegistry()
    scar = registry.record_scar(
        claim_id="claim-2",
        trajectory_id="traj-2",
        prior_epistemic_state=EpistemicState.UNRESOLVED,
        contradictory_evidence=["evidence-b"],
        source="deterministic-check",
        confidence=0.5,
        unresolved_questions=["missing context"],
        recovery_eligibility=True,
        provenance="unit-test",
    )
    assert scar.prior_epistemic_state == EpistemicState.UNRESOLVED


def test_duplicate_contradictory_evidence_does_not_duplicate_scars():
    registry = ScarRegistry()
    first = registry.record_scar(
        "claim-3",
        "traj-3",
        EpistemicState.SUPPORTED,
        ["same-evidence"],
        "deterministic",
        1.0,
        [],
        True,
        "test",
    )
    second = registry.record_scar(
        "claim-3",
        "traj-3",
        EpistemicState.SUPPORTED,
        ["same-evidence"],
        "deterministic",
        1.0,
        [],
        True,
        "test",
    )
    assert first.scar_id == second.scar_id
    assert len(registry.all_scars()) == 1


def test_scars_survive_export_import():
    registry = ScarRegistry()
    registry.record_scar(
        "claim-4",
        "traj-4",
        EpistemicState.SUPPORTED,
        ["evidence-c"],
        "deterministic",
        0.8,
        ["follow-up"],
        True,
        "test",
    )
    replayed = ScarRegistry.from_records(registry.export_records())
    assert len(replayed.all_scars()) == 1
    assert replayed.all_scars()[0].claim_id == "claim-4"


def test_recovery_requires_explicit_evidence():
    manager = RecoveryManager()
    route = RecoveryRoute(
        route_id="route-1",
        originating_scar_id="scar-1",
        evidence_required=[RecoveryRequirement("Need deterministic log", ["log-1"])],
        prohibited_shortcuts=["pressure-only"],
        permitted_transitions=["CONTRADICTED->UNRESOLVED", "UNRESOLVED->SUPPORTED"],
        review_requirement="human review",
        success_condition="Required evidence present",
        failure_condition="Evidence missing",
        retained_uncertainty="review still required",
    )
    failed = manager.attempt_recovery(
        route,
        RecoveryAttempt(route_id="route-1", provided_evidence=[], shortcut_attempts=["pressure-only"], pressure=1.0),
    )
    succeeded = manager.attempt_recovery(
        route,
        RecoveryAttempt(route_id="route-1", provided_evidence=["log-1"], shortcut_attempts=[]),
    )
    assert failed.succeeded is False
    assert succeeded.succeeded is True
    assert len(manager.results) == 2


def test_failed_recovery_remains_recorded_and_success_does_not_erase_history():
    manager = RecoveryManager()
    route = RecoveryRoute(
        route_id="route-2",
        originating_scar_id="scar-2",
        evidence_required=[RecoveryRequirement("Need proof", ["proof-1"])],
        prohibited_shortcuts=[],
        permitted_transitions=["CONTRADICTED->SUPPORTED"],
        review_requirement="review",
        success_condition="proof present",
        failure_condition="proof missing",
        retained_uncertainty="none",
    )
    manager.attempt_recovery(route, RecoveryAttempt("route-2", [], []))
    manager.attempt_recovery(route, RecoveryAttempt("route-2", ["proof-1"], []))
    assert len(manager.results) == 2
    assert [result.succeeded for result in manager.results] == [False, True]


def test_association_retrieval_increases_accessibility_not_truth():
    field = AssociationField()
    field.add_beacon(AssociationBeacon("assoc-1", "River route", "routing", salience=0.8, relevance=0.9))
    retrievals = field.retrieve("routing")
    beacon = field.beacons["assoc-1"]
    assert retrievals[0].context_only is True
    assert beacon.access_count == 1
    assert beacon.retrieval_count == 1
    assert beacon.successful_use == 0


def test_successful_verified_use_promotes_and_failed_use_demotes():
    field = AssociationField()
    field.add_beacon(AssociationBeacon("assoc-2", "Bridge route", "routing", salience=0.5, relevance=0.5))
    field.record_use("assoc-2", verified_success=True)
    field.record_use("assoc-2", verified_success=False, contradicted=True)
    beacon = field.beacons["assoc-2"]
    assert beacon.successful_use == 1
    assert beacon.failed_use == 1
    assert beacon.contradiction_count == 1


def test_contradiction_scars_affect_weighting():
    field = AssociationField()
    field.add_beacon(AssociationBeacon("assoc-3", "Old route", "routing", salience=0.5, relevance=0.5))
    before = field.beacons["assoc-3"].relevance
    field.record_use("assoc-3", verified_success=False, contradicted=True)
    after = field.beacons["assoc-3"].relevance
    assert after < before


def test_retrieved_associations_enter_planner_as_context():
    field = AssociationField()
    field.add_beacon(AssociationBeacon("assoc-4", "Contour memory", "mapping", salience=0.4, relevance=0.7))
    field.add_edge(AssociationBrush("assoc-4", "assoc-4", "self", "unit-test"))
    planner = GeneralistPlanner()
    plan = planner.build_plan("mapping", field)
    assert plan.context["association_ids"] == ["assoc-4"]
    assert plan.retrievals[0].context_only is True
