"""
Authority issuance, replay, and validation helpers.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from python.cognitive_basin.privacy import UNKNOWN_PARTICIPANT, explicit_participant

from .contracts import (
    ActionPermit,
    ApprovalDenial,
    ApprovalGrant,
    AuthorityClass,
    AuthorityViolation,
    ExternalActionProposal,
    PermitExpiration,
    PermitRevocation,
    PermitScope,
)


def _canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def payload_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def permit_signature(permit: ActionPermit) -> str:
    data = {
        "permit_id": permit.permit_id,
        "proposal_id": permit.proposal_id,
        "issued_to_participant": permit.issued_to_participant,
        "issued_by_participant": permit.issued_by_participant,
        "scope": permit.scope.to_record(),
        "expiration": permit.expiration.to_record(),
        "provenance": permit.provenance,
    }
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


@dataclass
class AuthorityLedger:
    proposals: Dict[str, ExternalActionProposal] = field(default_factory=dict)
    permits: Dict[str, ActionPermit] = field(default_factory=dict)
    grants: Dict[str, ApprovalGrant] = field(default_factory=dict)
    denials: Dict[str, ApprovalDenial] = field(default_factory=dict)
    revocations: Dict[str, PermitRevocation] = field(default_factory=dict)
    execution_counts: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_events(cls, events: List[Dict[str, Any]]) -> "AuthorityLedger":
        ledger = cls()
        for event in events:
            event_type = str(event.get("type", ""))
            if event_type == "session.external_action.proposed":
                proposal = ExternalActionProposal.from_record(event["external_action"]["proposal"])
                ledger.proposals[proposal.proposal_id] = proposal
            elif event_type == "session.external_action.approved":
                grant = ApprovalGrant(**event["external_action"]["grant"])
                permit = ActionPermit.from_record(event["external_action"]["permit"])
                ledger.grants[grant.proposal_id] = grant
                ledger.permits[permit.permit_id] = permit
                if grant.proposal_id in ledger.proposals:
                    ledger.proposals[grant.proposal_id].status = "APPROVED"
                    ledger.proposals[grant.proposal_id].permit_id = permit.permit_id
            elif event_type == "session.external_action.denied":
                denial = ApprovalDenial(**event["external_action"]["denial"])
                ledger.denials[denial.proposal_id] = denial
                if denial.proposal_id in ledger.proposals:
                    ledger.proposals[denial.proposal_id].status = "DENIED"
            elif event_type == "session.external_action.revoked":
                revocation = PermitRevocation(**event["external_action"]["revocation"])
                ledger.revocations[revocation.permit_id] = revocation
                permit = ledger.permits.get(revocation.permit_id)
                if permit is not None:
                    permit.revoked = True
                    permit.revocation_reason = revocation.reason
                for proposal in ledger.proposals.values():
                    if proposal.permit_id == revocation.permit_id:
                        proposal.status = "REVOKED"
            elif event_type == "session.external_action.executed":
                proposal_id = str(event["external_action"]["proposal_id"])
                permit_id = str(event["external_action"].get("permit_id", ""))
                ledger.execution_counts[proposal_id] = ledger.execution_counts.get(proposal_id, 0) + 1
                if proposal_id in ledger.proposals:
                    ledger.proposals[proposal_id].status = "EXECUTED"
                if permit_id and permit_id in ledger.permits:
                    ledger.permits[permit_id].use_count += 1
        return ledger


class AuthorityManager:
    def issue_permit(
        self,
        proposal: ExternalActionProposal,
        *,
        issued_by_participant: str,
        note: str,
        now: float | None = None,
        expires_in_s: float = 1800.0,
        single_use: bool = True,
    ) -> tuple[ApprovalGrant, ActionPermit]:
        timestamp = now if now is not None else time.time()
        approver = explicit_participant(issued_by_participant)
        subject = explicit_participant(proposal.participant)
        if approver == UNKNOWN_PARTICIPANT and proposal.required_authority.authority != AuthorityClass.READ_ONLY:
            raise AuthorityViolation("UNKNOWN participant cannot issue external-write permits")
        if subject == UNKNOWN_PARTICIPANT and proposal.required_authority.authority != AuthorityClass.READ_ONLY:
            raise AuthorityViolation("UNKNOWN participant cannot receive external-write permits")
        if approver == subject:
            raise AuthorityViolation("Self-approval is not allowed")
        if proposal.required_authority.requires_rollback and proposal.rollback_plan.required and not proposal.rollback_plan.steps:
            raise AuthorityViolation("Missing rollback plan blocks reversible high-impact work")
        permit = ActionPermit(
            permit_id=f"permit-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal.proposal_id,
            issued_to_participant=subject,
            issued_by_participant=approver,
            scope=PermitScope(
                connector_id=proposal.connector_id,
                account_label=proposal.account_label,
                operation=proposal.operation,
                target_locator=proposal.target.target_locator,
                payload_hash=proposal.payload_hash,
                authority=proposal.required_authority.authority,
                single_use=single_use,
            ),
            expiration=PermitExpiration(issued_at=timestamp, expires_at=timestamp + max(1.0, expires_in_s)),
            provenance=dict(proposal.provenance),
        )
        permit.signature = permit_signature(permit)
        grant = ApprovalGrant(
            proposal_id=proposal.proposal_id,
            participant=approver,
            note=note,
            timestamp=timestamp,
            permit_id=permit.permit_id,
        )
        return grant, permit

    def deny_proposal(
        self,
        proposal: ExternalActionProposal,
        *,
        participant: str,
        reason: str,
        now: float | None = None,
    ) -> ApprovalDenial:
        actor = explicit_participant(participant)
        return ApprovalDenial(
            proposal_id=proposal.proposal_id,
            participant=actor,
            reason=reason,
            timestamp=now if now is not None else time.time(),
        )

    def revoke_permit(
        self,
        permit: ActionPermit,
        *,
        participant: str,
        reason: str,
        now: float | None = None,
    ) -> PermitRevocation:
        return PermitRevocation(
            permit_id=permit.permit_id,
            participant=explicit_participant(participant),
            reason=reason,
            timestamp=now if now is not None else time.time(),
        )

    def validate_permit(
        self,
        proposal: ExternalActionProposal,
        permit: ActionPermit,
        ledger: AuthorityLedger,
        *,
        now: float | None = None,
    ) -> None:
        timestamp = now if now is not None else time.time()
        if permit.signature != permit_signature(permit):
            raise AuthorityViolation("Permit signature verification failed")
        if permit.revoked or permit.permit_id in ledger.revocations:
            raise AuthorityViolation("Permit has been revoked")
        if permit.expiration.expires_at < timestamp:
            raise AuthorityViolation("Permit has expired")
        if permit.scope.single_use and ledger.execution_counts.get(proposal.proposal_id, 0) > 0:
            raise AuthorityViolation("Single-use permit already used")
        if permit.scope.connector_id != proposal.connector_id:
            raise AuthorityViolation("Permit connector scope mismatch")
        if permit.scope.account_label != proposal.account_label:
            raise AuthorityViolation("Permit account scope mismatch")
        if permit.scope.operation != proposal.operation:
            raise AuthorityViolation("Permit operation scope mismatch")
        if permit.scope.target_locator != proposal.target.target_locator:
            raise AuthorityViolation("Permit target scope mismatch")
        if permit.scope.payload_hash != proposal.payload_hash:
            raise AuthorityViolation("Permit payload hash mismatch")
        if permit.scope.authority != proposal.required_authority.authority:
            raise AuthorityViolation("Permit authority class mismatch")
