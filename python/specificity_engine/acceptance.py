"""
Deterministic acceptance scenarios for Specificity Engine v0.3.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from packages.ternary.states import ActionState, EpistemicState
from python.natural_math_lab.core import NaturalMathProcessState

from .adapters import govern_basin_action, suggest_natural_math_process
from .contracts import (
    ComparisonMode,
    Representation,
    SpecificityTarget,
    TargetFeature,
)
from .debt import (
    DebtPosture,
    StructuralDebtInputs,
    assess_structural_debt,
)
from .demo import demonstration_target, run_demo
from .ledger import LedgerIntegrityError, SpecificityLedger
from .measurement import measure_specificity, verify_receipt


def _record() -> dict[str, Any]:
    return {
        "provenance": ["source", "transform"],
        "developmental_path": ["seed", "grow", "settle"],
        "energetic_cost": 10.0,
        "alternatives": ["a", "b"],
    }


def _form(record: dict[str, Any], *, energy: float | None = None) -> dict[str, Any]:
    return {
        "trace": {
            "provenance": list(record["provenance"]),
            "path": list(record["developmental_path"]),
            "alternatives": list(record["alternatives"]),
        },
        "metrics": {
            "energy": record["energetic_cost"] if energy is None else energy
        },
    }


def _receipt(representation_id: str = "rep"):
    record = _record()
    return measure_specificity(
        Representation(
            representation_id,
            demonstration_target(),
            record,
            _form(record),
            ("acceptance-fixture",),
        )
    )


def _scenario(name: str, fn: Callable[[], bool]) -> dict[str, Any]:
    try:
        passed = bool(fn())
        return {"scenario": name, "passed": passed, "detail": ""}
    except Exception as exc:  # pragma: no cover - surfaced in acceptance output
        return {
            "scenario": name,
            "passed": False,
            "detail": f"{type(exc).__name__}: {exc}",
        }


def _different_forms_change_measurement() -> bool:
    record = _record()
    target = demonstration_target()
    exact = measure_specificity(
        Representation("same-id", target, record, _form(record))
    )
    changed_form = _form(record)
    changed_form["trace"]["provenance"] = ["different"]
    changed = measure_specificity(
        Representation("same-id", target, record, changed_form)
    )
    return exact.gsr > changed.gsr and exact.receipt_id != changed.receipt_id


def _measurement_is_deterministic() -> bool:
    return _receipt("stable") == _receipt("stable")


def _missing_feature_becomes_residue() -> bool:
    record = _record()
    form = _form(record)
    del form["trace"]["path"]
    receipt = measure_specificity(
        Representation("missing", demonstration_target(), record, form)
    )
    path = next(
        item for item in receipt.feature_measurements if item.name == "developmental_path"
    )
    return path.observed_missing and path.score == 0.0 and receipt.ngr > 0.0


def _target_conditioning_ignores_unselected_fields() -> bool:
    target = SpecificityTarget(
        "selected-only",
        "Measure selected field only",
        (
            TargetFeature(
                "selected",
                ("selected",),
                ("selected",),
                comparison=ComparisonMode.EXACT,
            ),
        ),
    )
    left = measure_specificity(
        Representation("selected", target, {"selected": 1}, {"selected": 1, "noise": "a"})
    )
    right = measure_specificity(
        Representation("selected", target, {"selected": 1}, {"selected": 1, "noise": "b"})
    )
    return left == right


def _debt_uses_receipt_once() -> bool:
    receipt = _receipt("debt")
    inputs = StructuralDebtInputs.from_measurement(receipt, scar_load=0.2)
    first = assess_structural_debt(receipt, inputs, resolution_capacity=1.0)
    second = assess_structural_debt(receipt, inputs, resolution_capacity=1.0)
    return first == second and first.receipt_id == receipt.receipt_id


def _namespaces_remain_separate() -> bool:
    receipt = _receipt("namespaces")
    inputs = StructuralDebtInputs.from_measurement(
        receipt,
        discrepancy_debt=0.7,
    )
    assessment = assess_structural_debt(receipt, inputs, resolution_capacity=1.0)
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    process = suggest_natural_math_process(assessment)
    return (
        decision.epistemic == EpistemicState.SUPPORTED
        and decision.action == ActionState.HOLD
        and process == NaturalMathProcessState.SENSE
        and decision.action.value != process.value
    )


def _ledger_replays_final_state(root: Path) -> bool:
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
    ledger = SpecificityLedger(root / "acceptance-ledger.jsonl")
    event = ledger.append(receipt, assessment, decision)
    replay = ledger.replay()
    return (
        replay.event_count == 1
        and replay.chain_head == event.event_hash
        and replay.final_receipt == receipt
        and replay.final_assessment == assessment
        and replay.final_decision == decision
    )


def _ledger_detects_tampering(root: Path) -> bool:
    ledger_path = root / "tampered-ledger.jsonl"
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
    ledger = SpecificityLedger(ledger_path)
    ledger.append(receipt, assessment, decision)
    record = json.loads(ledger_path.read_text(encoding="utf-8"))
    record["payload"]["receipt"]["gsr"] = 0.0
    ledger_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    try:
        ledger.replay()
    except LedgerIntegrityError:
        return True
    return False


def _repair_trajectory_closes(root: Path) -> bool:
    summary = run_demo(root / "trajectory")
    phases = summary["phases"]
    return (
        phases[0]["gsr"] == 1.0
        and phases[1]["gsr"] < phases[0]["gsr"]
        and phases[2]["gsr"] == phases[0]["gsr"]
        and phases[1]["basin"]["action"] != ActionState.EXTEND.value
        and phases[2]["basin"]["action"] == ActionState.EXTEND.value
        and summary["replay"]["verified"]
        and summary["replay"]["final_basin"]["action"] == ActionState.EXTEND.value
    )


def _run_at(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    scenarios = [
        _scenario("geometric_form_affects_measurement", _different_forms_change_measurement),
        _scenario("measurement_is_deterministic", _measurement_is_deterministic),
        _scenario("missing_feature_becomes_residue", _missing_feature_becomes_residue),
        _scenario(
            "target_conditioning_ignores_unselected_fields",
            _target_conditioning_ignores_unselected_fields,
        ),
        _scenario("debt_uses_receipt_once", _debt_uses_receipt_once),
        _scenario("state_namespaces_remain_separate", _namespaces_remain_separate),
        _scenario(
            "ledger_replays_final_state",
            lambda: _ledger_replays_final_state(root),
        ),
        _scenario(
            "ledger_detects_tampering",
            lambda: _ledger_detects_tampering(root),
        ),
        _scenario(
            "repair_trajectory_closes",
            lambda: _repair_trajectory_closes(root),
        ),
        _scenario("receipt_self_verifies", lambda: verify_receipt(_receipt("verify"))),
    ]
    summary = {
        "passed": all(item["passed"] for item in scenarios),
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "limitations": [
            "Thresholds are policy defaults and require domain calibration.",
            "Feature paths and comparison modes must be declared by the caller.",
            "Acceptance proves deterministic local behavior, not empirical universality.",
        ],
    }
    (root / "specificity-acceptance.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def run_acceptance_suite(
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    if artifact_dir is not None:
        return _run_at(Path(artifact_dir))
    with tempfile.TemporaryDirectory(prefix="specificity-acceptance-") as directory:
        return _run_at(Path(directory))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(
        f"Specificity Engine acceptance: "
        f"{summary['scenario_count']} scenarios, passed={summary['passed']}"
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
