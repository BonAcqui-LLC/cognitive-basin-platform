"""
Cognitive Basin Lab - Core Contracts (Phase C)
Pure stdlib implementation using dataclasses + json for formal schemas.
Versioned contracts. Export to JSON Schema (manual for stdlib compatibility).

DO NOT claim internal model mechanisms. These are external controller contracts.
"""

import dataclasses
import json
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

# Epistemic ternary - separate from action
class EpistemicState(str, Enum):
    CONTRADICTED = "CONTRADICTED"
    UNRESOLVED = "UNRESOLVED"
    SUPPORTED = "SUPPORTED"

# Action ternary - separate dimension
class ActionState(str, Enum):
    RETRACT = "RETRACT"
    HOLD = "HOLD"
    EXTEND = "EXTEND"

@dataclasses.dataclass
class ArtifactManifest:
    artifact_id: str
    artifact_version: str
    artifact_hash: str
    artifact_type: str  # e.g. "code_repo", "legal_contract", "document_collection", "full_bounded_artifact"
    title: str
    source: str
    created_at: str
    ingested_at: str
    trust_class: str  # e.g. "high", "medium", "adversarial_candidate"
    sanitization_status: str
    access_policy: str
    region_ids: List[str]
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self):
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(d: dict):
        return ArtifactManifest(**d)

    def to_json_schema(self) -> dict:
        # Simple manual schema for stdlib
        return {
            "type": "object",
            "properties": {
                "artifact_id": {"type": "string"},
                "artifact_version": {"type": "string"},
                "artifact_hash": {"type": "string"},
                # ... abbreviated for full impl
            },
            "required": ["artifact_id", "artifact_hash"]
        }

@dataclasses.dataclass
class RegionRecord:
    region_id: str
    artifact_id: str
    parent_region_id: Optional[str] = None
    source_path: str = ""
    section: str = ""
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    byte_start: Optional[int] = None
    byte_end: Optional[int] = None
    content_hash: str = ""
    content: str = ""
    content_type: str = "text"
    trust_class: str = "unknown"
    risk_flags: List[str] = dataclasses.field(default_factory=list)
    provenance: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class ClaimRecord:
    claim_id: str
    claim_text: str
    claim_type: str
    source_region_ids: List[str]
    supporting_evidence_ids: List[str] = dataclasses.field(default_factory=list)
    contradicting_evidence_ids: List[str] = dataclasses.field(default_factory=list)
    epistemic_state: EpistemicState = EpistemicState.UNRESOLVED
    confidence_proxy: float = 0.0  # Not truth probability
    verification_status: str = "pending"
    verification_method: str = "external"

    def to_dict(self):
        d = dataclasses.asdict(self)
        d["epistemic_state"] = self.epistemic_state.value
        return d

@dataclasses.dataclass
class EvidenceRecord:
    evidence_id: str
    claim_id: str
    region_id: str
    evidence_type: str
    direction: str  # "support" or "contradict"
    strength: float
    deterministic: bool = False
    verifier: str = "external_selector"
    result: str = ""

    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class CandidatePath:
    candidate_id: str
    parent_candidate_id: Optional[str] = None
    checkpoint_id: str = ""
    claims: List[str] = dataclasses.field(default_factory=list)
    selected_regions: List[str] = dataclasses.field(default_factory=list)
    ignored_regions: List[str] = dataclasses.field(default_factory=list)
    score: float = 0.0
    risk: float = 0.0
    resource_cost: float = 0.0
    status: str = "active"
    termination_reason: Optional[str] = None

    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class BasinState:
    activation_id: str
    purpose: str
    module: str  # PERCEPT | ATAL | RIGOR | etc.
    epistemic_state: EpistemicState = EpistemicState.UNRESOLVED
    action_state: ActionState = ActionState.HOLD
    active_candidates: List[str] = dataclasses.field(default_factory=list)
    held_candidates: List[str] = dataclasses.field(default_factory=list)
    retracted_candidates: List[str] = dataclasses.field(default_factory=list)
    supported_claims: List[str] = dataclasses.field(default_factory=list)
    unresolved_claims: List[str] = dataclasses.field(default_factory=list)
    contradicted_claims: List[str] = dataclasses.field(default_factory=list)
    resource_budget: float = 1.0
    resource_used: float = 0.0
    transition_count: int = 0
    checkpoint_ids: List[str] = dataclasses.field(default_factory=list)
    failure_scar_ids: List[str] = dataclasses.field(default_factory=list)

    def to_dict(self):
        d = dataclasses.asdict(self)
        d["epistemic_state"] = self.epistemic_state.value
        d["action_state"] = self.action_state.value
        return d

@dataclasses.dataclass
class TransitionRecord:
    transition_id: str
    activation_id: str
    timestamp: str
    module: str
    previous_epistemic_state: str
    next_epistemic_state: str
    previous_action: str
    action: str
    trigger: str
    evidence_delta: int = 0
    contradiction_delta: int = 0
    resource_delta: float = 0.0
    candidate_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    result: str = ""

    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class FailureScar:
    scar_id: str
    activation_id: str
    candidate_id: str
    checkpoint_id: str
    failure_type: str
    failed_claim_ids: List[str]
    violated_constraints: List[str]
    evidence: str
    cause_summary: str
    retry_changes: Dict[str, Any]
    created_at: str

    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class ReceptorEvent:
    event_id: str
    timestamp: str
    source_channel: str
    event_type: str  # observation, claim, decision, recommendation, action_request, warning, unresolved, failure, retry
    epistemic_state: str
    action: str
    payload: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self):
        return dataclasses.asdict(self)

# Utility to export simple schemas
def export_schemas() -> Dict[str, Any]:
    return {
        "ArtifactManifest": ArtifactManifest.to_json_schema(ArtifactManifest),
        "BasinState": {"type": "object", "properties": {"epistemic_state": {"enum": [e.value for e in EpistemicState]}, "action_state": {"enum": [a.value for a in ActionState]}}},
        "version": "0.1-basin-lab"
    }

if __name__ == "__main__":
    print("Contracts module loaded. Example BasinState:")
    state = BasinState(activation_id="test-001", purpose="whole-artifact-integrity-check", module="RIGOR")
    print(json.dumps(state.to_dict(), indent=2))
    print("Schemas:", list(export_schemas().keys()))

# === PROVENANCE (added during platform bootstrap, do not alter original) ===
# Original source: ephux-next/basin-lab/core/contracts.py
# Discovered and verified during M0 evidence acquisition (2026-06-17)
# Authors: James Clow (lead architect), Melissa Clow (Natural Math / conceptual collaborator), BonAcqui LLC
# Context: Part of Cognitive Basin / Fractalish architecture (PERCEPT/ATAL/RIGOR/CIRCUIT/GUARD/SERA)
# Imported snapshot for lineage. New implementation will reference this.
# Hash of original at import time recorded in ops/manifests/provenance.json
