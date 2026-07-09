"""
Executable deterministic Specificity Engine v0.3 demonstration.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from packages.ternary.states import EpistemicState

from .adapters import govern_basin_action, suggest_natural_math_process
from .contracts import (
    ComparisonMode,
    Representation,
    SpecificityTarget,
    TargetFeature,
)
from .debt import StructuralDebtInputs, assess_structural_debt
from .ledger import SpecificityLedger
from .measurement import measure_specificity


def demonstration_target() -> SpecificityTarget:
    return SpecificityTarget(
        target_id="developmental-memory-v1",
        purpose="Preserve provenance, developmental sequence, energy, and alternatives",
        features=(
            TargetFeature(
                "provenance",
                ("provenance",),
                ("trace", "provenance"),
                weight=2.0,
                comparison=ComparisonMode.SEQUENCE,
            ),
            TargetFeature(
                "developmental_path",
                ("developmental_path",),
                ("trace", "path"),
                weight=2.0,
                comparison=ComparisonMode.SEQUENCE,
            ),
            TargetFeature(
                "energetic_cost",
                ("energetic_cost",),
                ("metrics", "energy"),
                comparison=ComparisonMode.NUMERIC,
                tolerance=0.05,
            ),
            TargetFeature(
                "alternatives",
                ("alternatives",),
                ("trace", "alternatives"),
                comparison=ComparisonMode.SET,
            ),
        ),
    )


def _full_record() -> dict[str, Any]:
    return {
        "provenance": ["sensor-A", "filter-v2", "classifier-v1"],
        "developmental_path": ["seed", "branch", "settle"],
        "energetic_cost": 10.0,
        "alternatives": ["left", "right"],
    }


def _form(
    provenance: list[str],
    path: list[str],
    energy: float,
    alternatives: list[str],
) -> dict[str, Any]:
    return {
        "trace": {
            "provenance": provenance,
            "path": path,
            "alternatives": alternatives,
        },
        "metrics": {"energy": energy},
    }


def _phase(
    *,
    phase_name: str,
    representation: Representation,
    debt_components: dict[str, float],
    ledger: SpecificityLedger,
) -> dict[str, Any]:
    receipt = measure_specificity(representation)
    inputs = StructuralDebtInputs.from_measurement(receipt, **debt_components)
    assessment = assess_structural_debt(
        receipt,
        inputs,
        resolution_capacity=1.0,
    )
    decision = govern_basin_action(
        assessment,
        epistemic=EpistemicState.SUPPORTED,
    )
    event = ledger.append(receipt, assessment, decision)
    return {
        "phase": phase_name,
        "gsr": receipt.gsr,
        "ngr": receipt.ngr,
        "sdp": assessment.total_sdp,
        "debt_posture": assessment.posture.value,
        "basin": decision.to_record(),
        "natural_math_process": suggest_natural_math_process(assessment).value,
        "receipt_id": receipt.receipt_id,
        "ledger_event_hash": event.event_hash,
    }


def _run_at(root: Path) -> dict[str, Any]:
    target = demonstration_target()
    full_record = _full_record()
    ledger = SpecificityLedger(root / "specificity-events.jsonl")

    train = _phase(
        phase_name="TRAIN",
        representation=Representation(
            "train",
            target,
            full_record,
            _form(
                full_record["provenance"],
                full_record["developmental_path"],
                full_record["energetic_cost"],
                full_record["alternatives"],
            ),
            ("direct-observation",),
        ),
        debt_components={},
        ledger=ledger,
    )
    relocate = _phase(
        phase_name="RELOCATE",
        representation=Representation(
            "relocate",
            target,
            full_record,
            _form(["sensor-A"], ["seed", "settle"], 15.0, ["left"]),
            ("relocation-observation",),
        ),
        debt_components={
            "discrepancy_debt": 0.12,
            "scar_load": 0.10,
            "branching_burden": 0.10,
            "ambiguity_load": 0.08,
            "sera_waste_channel": 0.10,
        },
        ledger=ledger,
    )
    repair = _phase(
        phase_name="REPAIR",
        representation=Representation(
            "repair",
            target,
            full_record,
            _form(
                full_record["provenance"],
                full_record["developmental_path"],
                full_record["energetic_cost"],
                full_record["alternatives"],
            ),
            ("repair-observation", "relocate-receipt-reviewed"),
        ),
        debt_components={},
        ledger=ledger,
    )

    replay = ledger.replay()
    summary = {
        "engine_version": "0.3.0",
        "phases": [train, relocate, repair],
        "replay": {
            "verified": replay.event_count == 3,
            "event_count": replay.event_count,
            "chain_head": replay.chain_head,
            "final_receipt_id": (
                replay.final_receipt.receipt_id if replay.final_receipt else ""
            ),
            "final_basin": (
                replay.final_decision.to_record() if replay.final_decision else {}
            ),
        },
        "claim_boundary": (
            "Demonstrates deterministic local measurement and governed replay; "
            "it does not establish empirical validity for a deployment domain."
        ),
    }
    (root / "specificity-demo-summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def run_demo(artifact_dir: str | Path | None = None) -> dict[str, Any]:
    if artifact_dir is not None:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        return _run_at(root)
    with tempfile.TemporaryDirectory(prefix="specificity-v0.3-") as directory:
        return _run_at(Path(directory))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    summary = run_demo(args.artifact_dir or None)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
