"""
End-to-end Cognitive Basin truth-state scenarios (A-F).

These exercise the full PERCEPT->...->Commit Gate path and assert the required behaviors.

Run: python -m pytest tests/test_cognitive_basin_scenarios.py -q --tb=line
or python tests/test_cognitive_basin_scenarios.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.cognitive_basin.pipeline import run_basin_pipeline, replay_events, EpistemicState, ActionState

def test_A_SUPPORTED_EXTEND():
    res = run_basin_pipeline("valid percept with strong evidence", pressure=0.1, contradictions=0)
    assert res["basin"].epistemic == EpistemicState.SUPPORTED
    assert res["basin"].action == ActionState.EXTEND
    assert res["gate_allowed"] is True
    print("A. SUPPORTED / EXTEND: PASSED")

def test_B_UNRESOLVED_HOLD():
    res = run_basin_pipeline("insufficient data", pressure=0.6, contradictions=0)
    assert res["basin"].epistemic == EpistemicState.UNRESOLVED
    assert res["basin"].action == ActionState.HOLD
    assert res["gate_allowed"] is False or res["basin"].provisional
    print("B. UNRESOLVED / HOLD: PASSED")

def test_C_CONTRADICTED_RETRACT():
    res = run_basin_pipeline("data with direct contradiction", pressure=0.2, contradictions=2)
    assert res["basin"].epistemic == EpistemicState.CONTRADICTED
    assert res["basin"].action == ActionState.RETRACT
    assert res["gate_allowed"] is False
    print("C. CONTRADICTED / RETRACT: PASSED")

def test_D_FALSE_COMPLETION():
    # Simulate a capability that is not implemented: use the guard with a placeholder fixture
    import tempfile
    from pathlib import Path as P
    with tempfile.TemporaryDirectory() as td:
        bad = P(td) / "claimed_done.py"
        bad.write_text('status = "IMPLEMENTED"  # PLACEHOLDER: actually not done\n')
        res = run_basin_pipeline("some data", pressure=0.1, contradictions=0, artifact_paths=[str(bad)])
        # Guard should have denied because of PLACEHOLDER
        assert res["gate_allowed"] is False
        assert "PLACEHOLDER" in res.get("guard", {}).get("guard_reason", "") or not res["gate_allowed"]
    print("D. FALSE COMPLETION (blocked by GUARD): PASSED")

def test_A_low_urgency_same_evidence():
    res = run_basin_pipeline("data", pressure=0.1, contradictions=0)
    assert res["basin"].epistemic == EpistemicState.SUPPORTED
    print("A. low urgency same evidence: PASSED")

def test_B_high_urgency_same_evidence():
    res = run_basin_pipeline("data", pressure=0.9, contradictions=0)
    assert res["basin"].epistemic == EpistemicState.SUPPORTED
    print("B. high urgency same evidence (epistemic preserved): PASSED")

def test_C_same_contradiction_low_high_pressure():
    res_low = run_basin_pipeline("contradictory data", pressure=0.1, contradictions=2)
    res_high = run_basin_pipeline("contradictory data", pressure=0.9, contradictions=2)
    assert res_low["basin"].epistemic == EpistemicState.CONTRADICTED
    assert res_high["basin"].epistemic == EpistemicState.CONTRADICTED
    print("C. same contradiction low/high pressure: PASSED")

def test_D_same_insufficient_low_high_pressure():
    res_low = run_basin_pipeline("insufficient", pressure=0.1, contradictions=0)
    res_high = run_basin_pipeline("insufficient", pressure=0.9, contradictions=0)
    assert res_low["basin"].epistemic == EpistemicState.UNRESOLVED
    assert res_high["basin"].epistemic == EpistemicState.UNRESOLVED
    print("D. same insufficient low/high pressure: PASSED")

def test_E_same_supporting_low_high_pressure_epistemic_preserved():
    res_low = run_basin_pipeline("supporting data", pressure=0.1, contradictions=0)
    res_high = run_basin_pipeline("supporting data", pressure=0.9, contradictions=0)
    assert res_low["basin"].epistemic == EpistemicState.SUPPORTED
    assert res_high["basin"].epistemic == EpistemicState.SUPPORTED
    print("E. same supporting low/high pressure (epistemic preserved, pressure affects only budget/escalation): PASSED")

def test_F_EVENT_REPLAY():
    res = run_basin_pipeline("initial", pressure=0.3, contradictions=1)
    events = res["events"]
    replayed = replay_events(events)
    assert replayed.epistemic == res["basin"].epistemic
    assert replayed.action == res["basin"].action
    print("F. EVENT REPLAY: PASSED")

def test_F_EVENT_REPLAY():
    res = run_basin_pipeline("initial", pressure=0.3, contradictions=1)
    events = res["events"]
    replayed = replay_events(events)
    assert replayed.epistemic == res["basin"].epistemic
    assert replayed.action == res["basin"].action
    print("F. EVENT REPLAY: PASSED")

if __name__ == "__main__":
    test_A_low_urgency_same_evidence()
    test_B_high_urgency_same_evidence()
    test_C_same_contradiction_low_high_pressure()
    test_D_same_insufficient_low_high_pressure()
    test_E_same_supporting_low_high_pressure_epistemic_preserved()
    test_F_EVENT_REPLAY()
    print("\nAll 6 Cognitive Basin scenarios (pressure-truth separation + replay) PASSED.")
    sys.exit(0)
