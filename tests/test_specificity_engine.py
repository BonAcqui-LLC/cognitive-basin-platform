"""
Executable contract tests for Specificity Engine v0.3.
"""

from __future__ import annotations

import json

import pytest

from packages.ternary.states import ActionState, EpistemicState
from python.natural_math_lab.core import NaturalMathProcessState
from python.specificity_engine import (
    ComparisonMode,
    DebtPolicy,
    DebtPosture,
    LedgerIntegrityError,
    Representation,
    SpecificityLedger,
    SpecificityTarget,
    StructuralDebtInputs,
    TargetFeature,
    assess_structural_debt,
    govern_basin_action,
    measure_specificity,
    suggest_natural_math_process,
    verify_receipt,
)
from python.specificity_engine.ledger import _event_hash
from python.specificity_engine.measurement import canonical_json


def _target() -> SpecificityTarget:
    return SpecificityTarget(
        "test-target",
        "Measure target-relevant memory",
        (
            TargetFeature(
                "identity",
                ("identity",),
                ("encoded", "identity"),
                weight=2.0,
                comparison=ComparisonMode.EXACT,
            ),
            TargetFeature(
                "energy",
                ("energy",),
                ("encoded", "energy"),
                comparison=ComparisonMode.NUMERIC,
                tolerance=0.1,
            ),
            TargetFeature(
                "evidence",
                ("evidence",),
                ("encoded", "evidence"),
                comparison=ComparisonMode.SET,
            ),
            TargetFeature(
                "path",
                ("path",),
                ("encoded", "path"),
                comparison=ComparisonMode.SEQUENCE,
            ),
        ),
    )


def _record():
    return {
        "identity": "node-7",
        "energy": 10.0,
        "evidence": ["a", "b"],
        "path": ["seed", "grow", "settle"],
    }


def _form():
    record = _record()
    return {"encoded": dict(record)}


def _receipt(representation_id: str = "rep"):
    return measure_specificity(
        Representation(
            representation_id,
            _target(),
            _record(),
            _form(),
            ("unit-test",),
        )
    )


def test_exact_measurement_is_deterministic_and_self_verifying():
    first = _receipt("stable")
    second = _receipt("stable")
    assert first == second
    assert first.gsr == 1.0
    assert first.ngr == 0.0
    assert verify_receipt(first)


def test_changed_geometric_form_changes_measurement():
    exact = _receipt("changed")
    changed_form = _form()
    changed_form["encoded"]["identity"] = "node-8"
    changed = measure_specificity(
        Representation("changed", _target(), _record(), changed_form)
    )
    assert changed.gsr < exact.gsr
    assert changed.receipt_id != exact.receipt_id


def test_target_conditioning_ignores_undeclared_form_fields():
    baseline = _form()
    noisy = _form()
    baseline["not_targeted"] = {"value": 1}
    noisy["not_targeted"] = {"value": 999}
    left = measure_specificity(
        Representation("targeted", _target(), _record(), baseline)
    )
    right = measure_specificity(
        Representation("targeted", _target(), _record(), noisy)
    )
    assert left == right


def test_missing_observed_feature_scores_zero():
    form = _form()
    del form["encoded"]["path"]
    receipt = measure_specificity(
        Representation("missing", _target(), _record(), form)
    )
    path = next(item for item in receipt.feature_measurements if item.name == "path")
    assert path.observed_missing
    assert path.score == 0.0
    assert receipt.ngr > 0.0


def test_sequence_and_set_comparators_preserve_partial_credit():
    form = _form()
    form["encoded"]["evidence"] = ["a", "c"]
    form["encoded"]["path"] = ["seed", "settle"]
    receipt = measure_specificity(
        Representation("partial", _target(), _record(), form)
    )
    scores = {item.name: item.score for item in receipt.feature_measurements}
    assert scores["evidence"] == pytest.approx(1 / 3)
    assert scores["path"] == pytest.approx(2 / 3)


def test_non_json_input_is_rejected():
    form = _form()
    form["encoded"]["identity"] = object()
    with pytest.raises(ValueError, match="JSON-compatible"):
        measure_specificity(
            Representation("bad-json", _target(), _record(), form)
        )


def test_debt_assessment_requires_receipt_ngr():
    receipt = _receipt("debt-mismatch")
    inputs = StructuralDebtInputs(ngr_applied=0.4)
    with pytest.raises(ValueError, match="carry NGR"):
        assess_structural_debt(receipt, inputs, resolution_capacity=1.0)


def test_debt_policy_thresholds_are_calibratable_and_ordered():
    with pytest.raises(ValueError, match="strictly increasing"):
        DebtPolicy(
            operational_threshold=0.6,
            caution_threshold=0.3,
        )

    receipt = _receipt("calibration")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(
            receipt,
            discrepancy_debt=0.7,
        ),
        resolution_capacity=1.0,
    )
    assert assessment.posture == DebtPosture.CONSTRAINED


def test_basin_adapter_preserves_epistemic_truth_namespace():
    receipt = _receipt("basin")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(
            receipt,
            discrepancy_debt=0.7,
        ),
        resolution_capacity=1.0,
    )
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    assert decision.epistemic == EpistemicState.SUPPORTED
    assert decision.action == ActionState.HOLD
    assert decision.provisional


def test_natural_math_process_state_is_not_basin_action_state():
    receipt = _receipt("natural-math")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(
            receipt,
            discrepancy_debt=0.7,
        ),
        resolution_capacity=1.0,
    )
    basin = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    process = suggest_natural_math_process(assessment)
    assert basin.action == ActionState.HOLD
    assert process == NaturalMathProcessState.SENSE
    assert basin.action.value != process.value


def test_ledger_replay_reconstructs_governed_state(tmp_path):
    receipt = _receipt("ledger")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(receipt),
        resolution_capacity=1.0,
    )
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    ledger = SpecificityLedger(tmp_path / "events.jsonl")
    first = ledger.append(receipt, assessment, decision)
    replay = ledger.replay()
    assert replay.event_count == 1
    assert replay.chain_head == first.event_hash
    assert replay.final_receipt == receipt
    assert replay.final_assessment == assessment
    assert replay.final_decision == decision


def test_ledger_rejects_modified_payload(tmp_path):
    receipt = _receipt("tamper")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(receipt),
        resolution_capacity=1.0,
    )
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    ledger_path = tmp_path / "events.jsonl"
    ledger = SpecificityLedger(ledger_path)
    ledger.append(receipt, assessment, decision)

    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    payload["payload"]["decision"]["action"] = ActionState.RETRACT.value
    ledger_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(LedgerIntegrityError, match="hash mismatch"):
        ledger.replay()


def test_ledger_rejects_rehashed_invalid_debt_assessment(tmp_path):
    receipt = _receipt("forged-debt")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(receipt),
        resolution_capacity=1.0,
    )
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    ledger_path = tmp_path / "events.jsonl"
    ledger = SpecificityLedger(ledger_path)
    ledger.append(receipt, assessment, decision)

    record = json.loads(ledger_path.read_text(encoding="utf-8"))
    record["payload"]["assessment"]["total_sdp"] = 99.0
    record["event_hash"] = _event_hash(
        record["sequence"],
        record["previous_hash"],
        record["payload"],
    )
    ledger_path.write_text(canonical_json(record) + "\n", encoding="utf-8")
    with pytest.raises(LedgerIntegrityError, match="invalid debt assessment"):
        ledger.replay()


def test_ledger_rejects_rehashed_invalid_governance_decision(tmp_path):
    receipt = _receipt("forged-decision")
    assessment = assess_structural_debt(
        receipt,
        StructuralDebtInputs.from_measurement(receipt),
        resolution_capacity=1.0,
    )
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    ledger_path = tmp_path / "events.jsonl"
    ledger = SpecificityLedger(ledger_path)
    ledger.append(receipt, assessment, decision)

    record = json.loads(ledger_path.read_text(encoding="utf-8"))
    record["payload"]["decision"]["action"] = ActionState.RETRACT.value
    record["event_hash"] = _event_hash(
        record["sequence"],
        record["previous_hash"],
        record["payload"],
    )
    ledger_path.write_text(canonical_json(record) + "\n", encoding="utf-8")
    with pytest.raises(LedgerIntegrityError, match="invalid governance decision"):
        ledger.replay()
