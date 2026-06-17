"""
Contracts for local EphUX / Guardian integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class IntakeState(str, Enum):
    RECEIVED = "RECEIVED"
    PARSED = "PARSED"
    HELD = "HELD"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    SANITIZED = "SANITIZED"
    FAILED = "FAILED"


class SanitizationState(str, Enum):
    UNSANITIZED = "UNSANITIZED"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    SANITIZED = "SANITIZED"


@dataclass
class IntakeRecord:
    intake_id: str
    state: IntakeState
    content_hash: str
    content_type: str
    source_metadata: Dict[str, Any]
    sensitivity: str
    sanitization_state: SanitizationState
    duplicate_of: str = ""
    issues: List[str] = field(default_factory=list)
    redacted_excerpt: str = ""

    def to_record(self) -> Dict[str, Any]:
        return {
            "intake_id": self.intake_id,
            "state": self.state.value,
            "content_hash": self.content_hash,
            "content_type": self.content_type,
            "source_metadata": dict(self.source_metadata),
            "sensitivity": self.sensitivity,
            "sanitization_state": self.sanitization_state.value,
            "duplicate_of": self.duplicate_of,
            "issues": list(self.issues),
            "redacted_excerpt": self.redacted_excerpt,
        }


@dataclass
class ActivationRecord:
    activation_id: str
    purpose: str
    purpose_anchor: str
    desired_output_type: str
    provider_preference: str
    privacy_setting: str
    selected_next_action: str
    missing_evidence: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    capability_limitations: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "activation_id": self.activation_id,
            "purpose": self.purpose,
            "purpose_anchor": self.purpose_anchor,
            "desired_output_type": self.desired_output_type,
            "provider_preference": self.provider_preference,
            "privacy_setting": self.privacy_setting,
            "selected_next_action": self.selected_next_action,
            "missing_evidence": list(self.missing_evidence),
            "contradictions": list(self.contradictions),
            "capability_limitations": list(self.capability_limitations),
        }
