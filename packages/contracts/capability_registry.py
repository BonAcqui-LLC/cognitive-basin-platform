"""
Capability Registry (initial).

Simple registry + validator used by Completion Integrity Guard.

Capabilities are declared with required evidence types.
Transitions (SPECIFIED -> IMPLEMENTED etc.) are gated by the guard.

This is new executable code with lineage to M0 evidence (contracts.py, controller.py,
live doctrine sources, whitepaper flow).

Authors of architecture: James Clow and Melissa Clow, BonAcqui LLC.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import json

@dataclass
class Capability:
    name: str
    status: str = "SPECIFIED"  # SPECIFIED | IMPLEMENTED | PARTIAL | BLOCKED | DEFERRED
    required_evidence: List[str] = field(default_factory=list)
    notes: str = ""

REGISTRY: Dict[str, Capability] = {}

def register_capability(name: str, required_evidence: List[str], notes: str = "") -> Capability:
    cap = Capability(name=name, required_evidence=required_evidence, notes=notes)
    REGISTRY[name] = cap
    return cap

def load_registry(path: str = "ops/manifests/capability-registry.json") -> Dict[str, Capability]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for name, meta in data.get("capabilities", {}).items():
            register_capability(
                name,
                meta.get("required_evidence", []),
                meta.get("notes", "")
            )
    except FileNotFoundError:
        pass
    return REGISTRY

def get_capability(name: str) -> Capability | None:
    return REGISTRY.get(name)

# Initial core capabilities (M1 foundation)
register_capability(
    "ternary.epistemic",
    required_evidence=["source:contracts.py", "test:epistemic"],
    notes="SUPPORTED / UNRESOLVED / CONTRADICTED - lineage to legacy/contracts.py"
)
register_capability(
    "ternary.action",
    required_evidence=["source:contracts.py", "test:action", "controller:HOLD"],
    notes="EXTEND / HOLD / RETRACT with scars and budget - lineage to legacy/controller.py"
)
register_capability(
    "completion_integrity.guard",
    required_evidence=["test:completion_integrity_acceptance", "source:guard.py"],
    notes="Must detect PLACEHOLDER, missing artifacts, failed commands, absent remote commits, etc."
)
