import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fractalish_ai.morphological_language.natural_math_adapter import term_to_natural_math_stub

def test_disabled_speculative_operator():
    t = {"term_id": "T2", "label": "spec", "plain_definition": "x", "version": "0.1", "confidence": 0.1, "status": "PROPOSED", "negative_examples": ["all"]}
    stub = term_to_natural_math_stub(t)
    assert stub["enabled"] is False
    assert "experimental" in stub.get("notes", "").lower() or "disabled" in str(stub).lower()
print("test_natural_math_adapter.py loaded.")