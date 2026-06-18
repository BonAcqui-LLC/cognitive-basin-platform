"""
Typed authority contracts for governed external actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional


class AuthorityClass(StrEnum):
    READ_ONLY = "READ_ONLY"
    LOCAL_WRITE = "LOCAL_WRITE"
    PRIVATE_REPOSITORY_WRITE = "PRIVATE_REPOSITORY_WRITE"
    PREVIEW_DEPLOYMENT = "PREVIEW_DEPLOYMENT"
    PRODUCTION_WRITE = "PRODUCTION_WRITE"
    BILLING_CHANGE = "BILLING_CHANGE"
    DESTRUCTIVE_OPERATION = "DESTRUCTIVE_OPERATION"


@dataclass
class ActionTarget:
    target_type: str
    target_locator: str
    environment: str = "LOCAL"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SideEffectDeclaration:
    effect_type: str
    description: str
    reversible: bool
    destructive: bool = False
    cost_impact: str = "LOW"

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorityRequirement:
    authority: AuthorityClass
    reason: str
    requires_rollback: bool = False
    privacy_impact: str = "LOW"
    security_impact: str = "LOW"

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["authority"] = self.authority.value
        return payload


@dataclass
class VerificationPlan:
    steps: List[str] = field(default_factory=list)
    expected_evidence: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RollbackPlan:
    steps: List[str] = field(default_factory=list)
    rollback_target: str = ""
    required: bool = False

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RollbackReceipt:
    proposal_id: str
    performed_by: str
    timestamp: float
    status: str
    evidence: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExternalActionProposal:
    proposal_id: str
    session_id: str
    participant: str
    system: str
    connector_id: str
    account_label: str
    operation: str
    target: ActionTarget
    payload_hash: str
    payload_preview: Dict[str, Any] = field(default_factory=dict)
    side_effects: List[SideEffectDeclaration] = field(default_factory=list)
    reversible: bool = True
    expected_cost: str = "LOW"
    privacy_impact: str = "LOW"
    security_impact: str = "LOW"
    required_authority: AuthorityRequirement = field(
        default_factory=lambda: AuthorityRequirement(AuthorityClass.READ_ONLY, "default read authority")
    )
    verification_plan: VerificationPlan = field(default_factory=VerificationPlan)
    rollback_plan: RollbackPlan = field(default_factory=RollbackPlan)
    expires_at: float = 0.0
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    status: str = "PROPOSED"
    permit_id: str = ""

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["target"] = self.target.to_record()
        payload["side_effects"] = [item.to_record() for item in self.side_effects]
        payload["required_authority"] = self.required_authority.to_record()
        payload["verification_plan"] = self.verification_plan.to_record()
        payload["rollback_plan"] = self.rollback_plan.to_record()
        return payload

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "ExternalActionProposal":
        return cls(
            proposal_id=str(record["proposal_id"]),
            session_id=str(record["session_id"]),
            participant=str(record["participant"]),
            system=str(record["system"]),
            connector_id=str(record["connector_id"]),
            account_label=str(record["account_label"]),
            operation=str(record["operation"]),
            target=ActionTarget(**record["target"]),
            payload_hash=str(record["payload_hash"]),
            payload_preview=dict(record.get("payload_preview", {})),
            side_effects=[SideEffectDeclaration(**item) for item in record.get("side_effects", [])],
            reversible=bool(record.get("reversible", True)),
            expected_cost=str(record.get("expected_cost", "LOW")),
            privacy_impact=str(record.get("privacy_impact", "LOW")),
            security_impact=str(record.get("security_impact", "LOW")),
            required_authority=AuthorityRequirement(
                authority=AuthorityClass(record.get("required_authority", {}).get("authority", AuthorityClass.READ_ONLY.value)),
                reason=str(record.get("required_authority", {}).get("reason", "")),
                requires_rollback=bool(record.get("required_authority", {}).get("requires_rollback", False)),
                privacy_impact=str(record.get("required_authority", {}).get("privacy_impact", "LOW")),
                security_impact=str(record.get("required_authority", {}).get("security_impact", "LOW")),
            ),
            verification_plan=VerificationPlan(**record.get("verification_plan", {})),
            rollback_plan=RollbackPlan(**record.get("rollback_plan", {})),
            expires_at=float(record.get("expires_at", 0.0)),
            provenance=dict(record.get("provenance", {})),
            created_at=float(record.get("created_at", 0.0)),
            status=str(record.get("status", "PROPOSED")),
            permit_id=str(record.get("permit_id", "")),
        )


@dataclass
class PermitScope:
    connector_id: str
    account_label: str
    operation: str
    target_locator: str
    payload_hash: str
    authority: AuthorityClass
    single_use: bool = True

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["authority"] = self.authority.value
        return payload


@dataclass
class PermitExpiration:
    issued_at: float
    expires_at: float

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovalGrant:
    proposal_id: str
    participant: str
    note: str
    timestamp: float
    permit_id: str

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovalDenial:
    proposal_id: str
    participant: str
    reason: str
    timestamp: float

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionPermit:
    permit_id: str
    proposal_id: str
    issued_to_participant: str
    issued_by_participant: str
    scope: PermitScope
    expiration: PermitExpiration
    provenance: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    revoked: bool = False
    revocation_reason: str = ""
    use_count: int = 0

    def to_record(self) -> Dict[str, Any]:
        return {
            "permit_id": self.permit_id,
            "proposal_id": self.proposal_id,
            "issued_to_participant": self.issued_to_participant,
            "issued_by_participant": self.issued_by_participant,
            "scope": self.scope.to_record(),
            "expiration": self.expiration.to_record(),
            "provenance": dict(self.provenance),
            "signature": self.signature,
            "revoked": self.revoked,
            "revocation_reason": self.revocation_reason,
            "use_count": self.use_count,
        }

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "ActionPermit":
        return cls(
            permit_id=str(record["permit_id"]),
            proposal_id=str(record["proposal_id"]),
            issued_to_participant=str(record["issued_to_participant"]),
            issued_by_participant=str(record["issued_by_participant"]),
            scope=PermitScope(
                connector_id=str(record["scope"]["connector_id"]),
                account_label=str(record["scope"]["account_label"]),
                operation=str(record["scope"]["operation"]),
                target_locator=str(record["scope"]["target_locator"]),
                payload_hash=str(record["scope"]["payload_hash"]),
                authority=AuthorityClass(record["scope"]["authority"]),
                single_use=bool(record["scope"].get("single_use", True)),
            ),
            expiration=PermitExpiration(**record["expiration"]),
            provenance=dict(record.get("provenance", {})),
            signature=str(record.get("signature", "")),
            revoked=bool(record.get("revoked", False)),
            revocation_reason=str(record.get("revocation_reason", "")),
            use_count=int(record.get("use_count", 0)),
        )


@dataclass
class PermitRevocation:
    permit_id: str
    participant: str
    reason: str
    timestamp: float

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionReceipt:
    proposal_id: str
    connector_id: str
    status: str
    verification_result: str
    response_hash: str
    timestamp: float
    permit_id: str = ""
    redacted_fields: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


class AuthorityViolation(ValueError):
    """Raised when external authority requirements are not satisfied."""

