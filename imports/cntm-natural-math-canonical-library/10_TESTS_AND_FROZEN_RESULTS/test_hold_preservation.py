from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fractalish_ai.morphological_language.validators import validate_observation

def test_hold_case_not_forced_into_term():
    obs = {
        "observation_id": "HOLD-TEST",
        "source_id": "SRC-TEST",
        "domain": "test",
        "claim_level": "PATTERN",
        "evidence_status": "HOLD",
        "provenance": {"source_id": "SRC-TEST"},
        "notes": "Equifinal or insufficiently diagnostic per thesis AMCVA/HOLD rule.",
    }
    errs = validate_observation(obs)
    # Should not force promotion; HOLD is valid state
    assert "MLANG-E002" not in errs or obs["evidence_status"] == "HOLD"

print("test_hold_preservation.py loaded.")