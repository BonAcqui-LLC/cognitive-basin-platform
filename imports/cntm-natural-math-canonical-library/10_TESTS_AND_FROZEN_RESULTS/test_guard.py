"""GUARD decision tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.guard import evaluate_guard
from fractalish_ai.rigor import run_rigor_checks


def test_guard_holds_unsupported_claim() -> None:
    findings = [f.to_dict() for f in run_rigor_checks({
        "source": "test@local",
        "claim": "High-risk unsupported assertion.",
        "evidence": [],
        "supported": False,
        "risk_level": "high",
    })]
    result = evaluate_guard(findings, {"risk_level": "high"})
    assert result.decision == "HOLD"


def test_guard_reverses_boundary_violation() -> None:
    findings = [f.to_dict() for f in run_rigor_checks({
        "source": "test@local",
        "claim": "Within bounds.",
        "evidence": ["ok"],
        "supported": True,
        "boundary_violation": True,
    })]
    result = evaluate_guard(findings)
    assert result.decision == "REVERSE"


def test_false_continuity_routes_to_hold() -> None:
    basin = default_basin_state()
    prior = run_activation_event({
        "source": "a@local",
        "claim": "Unsettled prior claim.",
        "evidence": [],
        "supported": False,
        "risk_level": "high",
    }, basin)
    record = run_activation_event({
        "source": "a@local",
        "claim": "Continue as if settled.",
        "evidence": [],
        "supported": False,
        "assume_prior_settled": True,
        "risk_level": "high",
    }, prior["updated_basin_state"])
    assert record["guard_decision"]["decision"] == "HOLD"
    assert any(f["analyzer"] == "false_continuity" for f in record["rigor_findings"])