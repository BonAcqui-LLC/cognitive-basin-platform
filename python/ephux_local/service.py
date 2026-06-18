"""
Loopback-only local EphUX / Guardian service backed by BasinLab.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from packages.ternary.states import ActionState, EpistemicState
from python.basinlab.contracts import ActionProposal, BasinGovernanceState, CommitProposal
from python.basinlab.hold import HoldFogRecord
from python.basinlab.providers import CompactReasonerProvider, GeneralistProvider, OpenAICompatibleProvider, ScriptedProvider, VibeThinkerProvider
from python.basinlab.reliability import DecisionClaim, ReliabilityEngine
from python.basinlab.reports import write_report_bundle
from python.basinlab.scars import ScarRegistry
from python.basinlab.session import BasinLabSession, default_store_path, replay_persisted_session
from python.basinlab.recovery import RecoveryRequirement, RecoveryRoute
from python.basinlab.spectrum import CandidateTrajectory
from python.basinlab.store import SessionStore
from python.cognitive_basin.memory import (
    FractalMemoryMap,
    MemoryContradictionLink,
    MemoryEvidenceLink,
    MemoryFragment,
    MemoryItem,
    MemoryPurposeLink,
    MemoryRecoveryLink,
    MemoryScarLink,
)
from python.cognitive_basin.privacy import (
    RetentionClass,
    SensitivityLevel,
    VisibilityScope,
    content_hash,
    explicit_participant,
    redact_text,
)
from python.cognitive_basin.team_narrative import NarrativeRecord, TeamNarrative
from python.cognitive_basin.pipeline import run_basin_pipeline
from python.evaluation_lab.acceptance import run_acceptance_suite as run_evaluation_lab_acceptance
from python.natural_math_lab.acceptance import run_acceptance_suite as run_natural_math_lab_acceptance
from python.provider_lab import local_model_inventory, provider_inventory

from .contracts import ActivationRecord, IntakeRecord, IntakeState, SanitizationState


MAX_REQUEST_BYTES = 48_000
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".md", ".json"}
TEXT_ARTIFACT_SUFFIXES = {".txt", ".md", ".json", ".html", ".csv", ".log"}
INSTRUCTION_CONFLICT_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
]
SECRET_PATTERNS = [
    re.compile(r"\bgho_[A-Za-z0-9_]+\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bapi[_ -]?key\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
]


@dataclass
class LocalServiceConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    store_dir: Path = field(default_factory=lambda: default_store_path())
    report_dir: Path = field(default_factory=lambda: default_store_path() / "reports")
    ui_asset_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / "apps" / "ephux-local-ui")
    extension_origin: str = "chrome-extension://ephux-local-dev"
    max_request_bytes: int = MAX_REQUEST_BYTES
    token: str = field(default_factory=lambda: secrets.token_urlsafe(24))


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _default_basin(
    epistemic: EpistemicState = EpistemicState.UNRESOLVED,
    action: ActionState = ActionState.HOLD,
    provisional: bool = True,
    reason: str = "local_service_default",
) -> Dict[str, Any]:
    return BasinGovernanceState(epistemic=epistemic, action=action, provisional=provisional, reason=reason).to_record()


def _redact_secrets(text: str) -> tuple[str, bool]:
    redacted = text
    found = False
    for pattern in SECRET_PATTERNS:
        if pattern.search(redacted):
            found = True
            redacted = pattern.sub("[redacted-secret]", redacted)
    helper_redacted, helper_found = redact_text(redacted, VisibilityScope.SESSION_ONLY)
    return helper_redacted, found or helper_found


def _bounded_excerpt(text: str, limit: int = 240) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 27] + "...[bounded by EphUX local]"


def _sanitize_filename(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError("Path traversal is not allowed in uploaded file names")
    return Path(name).name


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _report_summary_from_bundle(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_spectrum": report.get("candidate_spectrum", {}),
        "decision_critical_claims": report.get("decision_critical_claims", []),
        "evidence_links": report.get("evidence_links", []),
        "reliability_verdicts": report.get("reliability_verdicts", []),
        "contradictions": report.get("contradictions", []),
        "scars": report.get("scars", []),
        "recovery_routes": report.get("recovery_routes", []),
        "association_updates": report.get("association_updates", []),
        "hold_intervals": report.get("hold_intervals", []),
        "commit_decisions": report.get("commit_decisions", []),
        "action_proposals": report.get("action_proposals", []),
    }


def _provider_inventory() -> List[Dict[str, Any]]:
    inventory = {entry["provider_name"]: entry for entry in provider_inventory()}
    hardware = local_model_inventory()
    providers = [
        ScriptedProvider(name="scripted"),
        GeneralistProvider(),
        CompactReasonerProvider(),
        OpenAICompatibleProvider(model=os.environ.get("OPENAI_MODEL", "unconfigured")),
        VibeThinkerProvider(),
    ]
    return [
        {
            "name": provider.name,
            "model": provider.model,
            "can_execute": provider.can_execute,
            "can_commit": provider.can_commit,
            "available": inventory.get(provider.name, {}).get("reachable", False),
            "inventory": inventory.get(provider.name, {}),
            "hardware": hardware,
        }
        for provider in providers
    ]


def _security_controls(config: LocalServiceConfig) -> Dict[str, str]:
    return {
        "loopback_bind": "ENFORCED" if config.host in {"127.0.0.1", "localhost"} else "BEST EFFORT",
        "local_token": "ENFORCED",
        "restricted_cors": "ENFORCED",
        "request_size_limit": "ENFORCED",
        "content_type_enforcement": "ENFORCED",
        "safe_error_responses": "ENFORCED",
        "secret_redaction_in_reports": "BEST EFFORT",
        "arbitrary_filesystem_paths": "ENFORCED",
        "production_security": "NOT PROVIDED",
    }


class EphuxLocalService:
    def __init__(self, config: LocalServiceConfig) -> None:
        self.config = config
        self.store = SessionStore(config.store_dir)
        self.report_dir = config.report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.narrative_seeds = [
            NarrativeRecord(
                person="James Clow",
                contributions=["Cognitive Basin and EphUX architecture lineage"],
                current_purposes=["Local EphUX product integration"],
            ),
            NarrativeRecord(
                person="Melissa Clow",
                contributions=["Governance framing and continuity"],
                current_purposes=["Local EphUX product integration"],
            ),
        ]

    def _allowed_origin(self, origin: str) -> bool:
        allowed = {
            f"http://{self.config.host}:{self.config.port}",
            f"http://127.0.0.1:{self.config.port}",
            self.config.extension_origin,
        }
        return origin in allowed

    def _ensure_token(self, headers: Dict[str, str]) -> None:
        if headers.get("x-ephux-token", "") != self.config.token:
            raise PermissionError("Missing or invalid local service token")

    def _next_event_id(self, session_id: str, prefix: str) -> str:
        highest = 0
        for event in self.store.read_events(session_id):
            event_id = event.get("event_id", "")
            if "-" in event_id:
                tail = event_id.rsplit("-", 1)[-1]
                if tail.isdigit():
                    highest = max(highest, int(tail))
        return f"{prefix}-{highest + 1:04d}"

    def _append_event(
        self,
        session_id: str,
        prefix: str,
        event_type: str,
        payload: Dict[str, Any],
        *,
        basin: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = {
            "type": event_type,
            "event_id": self._next_event_id(session_id, prefix),
            "timestamp": time.time(),
            **payload,
        }
        self.store.append_event(session_id, event, final_basin=basin)
        return event

    def _visibility_scope(self, privacy_setting: str) -> VisibilityScope:
        normalized = str(privacy_setting or "local-only").strip().lower()
        return {
            "private-james": VisibilityScope.PRIVATE_JAMES,
            "private-melissa": VisibilityScope.PRIVATE_MELISSA,
            "shared-project": VisibilityScope.SHARED_PROJECT,
            "exportable-redacted": VisibilityScope.EXPORTABLE_REDACTED,
            "audit-retained": VisibilityScope.AUDIT_RETAINED,
        }.get(normalized, VisibilityScope.SESSION_ONLY)

    def _retention_class(self, scope: VisibilityScope) -> RetentionClass:
        if scope in {VisibilityScope.PRIVATE_JAMES, VisibilityScope.PRIVATE_MELISSA}:
            return RetentionClass.PRIVATE_WORKING
        if scope in {VisibilityScope.SHARED_PROJECT, VisibilityScope.EXPORTABLE_REDACTED}:
            return RetentionClass.SHARED_WORKING
        if scope == VisibilityScope.AUDIT_RETAINED:
            return RetentionClass.AUDIT_RECORD
        return RetentionClass.SESSION_WORKING

    def _seed_session_narrative(self, session_id: str) -> None:
        existing = [event for event in self.store.read_events(session_id) if event.get("type") == "session.narrative"]
        if existing:
            return
        basin = self.store.inspect_session(session_id).get("final_basin", {})
        for record in self.narrative_seeds:
            self._append_event(
                session_id,
                "narrative",
                "session.narrative",
                {"narrative": record.to_record(), "seeded": True},
                basin=basin,
            )

    def _build_memory_map(self, session_id: str) -> FractalMemoryMap:
        return FractalMemoryMap.from_events(self.store.read_events(session_id))

    def _build_team_narrative(self, session_id: str) -> TeamNarrative:
        return TeamNarrative.from_events(self.store.read_events(session_id))

    def _record_memory_item(self, session_id: str, item: MemoryItem, basin: Dict[str, Any]) -> MemoryItem:
        memory_map = self._build_memory_map(session_id)
        stored = memory_map.upsert(item)
        self._append_event(
            session_id,
            "memory",
            "session.memory.upsert",
            {"memory_item": stored.to_record()},
            basin=basin,
        )
        return stored

    def _open_session(self, session_id: str) -> BasinLabSession:
        session = BasinLabSession.resume_from_store(self.store, session_id)
        inspected = self.store.inspect_session(session_id)
        final_basin = inspected.get("final_basin") or {}
        if final_basin:
            session.last_basin = BasinGovernanceState(
                epistemic=EpistemicState(final_basin["epistemic"]),
                action=ActionState(final_basin["action"]),
                provisional=bool(final_basin["provisional"]),
                reason=final_basin.get("reason", ""),
            )
        return session

    def create_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with BasinLabSession(
            store=self.store,
            session_metadata={
                "purpose": payload.get("purpose", ""),
                "context": payload.get("context", ""),
                "privacy_setting": payload.get("privacy_setting", "local-only"),
                "constraints": payload.get("constraints", []),
            },
        ) as session:
            session_id = str(session.session_id)
        self._seed_session_narrative(session_id)
        return self.get_session(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for item in self.store.list_sessions():
            sessions.append(
                {
                    "session_id": item.session_id,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "purpose": item.metadata.get("purpose", ""),
                    "context": item.metadata.get("context", ""),
                    "privacy_setting": item.metadata.get("privacy_setting", "local-only"),
                    "final_basin": item.final_basin,
                    "event_count": len(self.store.read_events(item.session_id)),
                }
            )
        return sessions

    def get_session(self, session_id: str) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        events = self.store.read_events(session_id)
        memory_state = self.session_memory(session_id)
        narrative_state = self.session_narrative(session_id)
        report = self.generate_report(session_id)
        report_data = report["report"]
        review_events = [event for event in events if event.get("type", "").startswith("session.review.")]
        inspected["events"] = events
        inspected["timeline"] = events
        inspected["review_events"] = review_events
        inspected["report_location"] = report["html_path"]
        inspected["report_data"] = report_data
        inspected["current_epistemic_state"] = inspected["final_basin"].get("epistemic", EpistemicState.UNRESOLVED.value)
        inspected["current_action_state"] = inspected["final_basin"].get("action", ActionState.HOLD.value)
        inspected["candidate_spectrum"] = report_data.get("candidate_spectrum", {})
        inspected["decision_critical_claims"] = report_data.get("decision_critical_claims", [])
        inspected["supporting_evidence"] = report_data.get("evidence_links", [])
        inspected["contradictory_evidence"] = report_data.get("contradictions", [])
        inspected["hold_reasons"] = report_data.get("hold_intervals", [])
        inspected["retract_reasons"] = report_data.get("contradictions", [])
        inspected["contradiction_scars"] = report_data.get("scars", [])
        inspected["recovery_routes"] = report_data.get("recovery_routes", [])
        inspected["associations"] = report_data.get("association_updates", [])
        inspected["lab_runs"] = report_data.get("lab_runs", [])
        inspected["latest_action_proposal"] = (
            report_data.get("action_proposals", [])[-1] if report_data.get("action_proposals") else None
        )
        inspected["latest_commit_decision"] = (
            report_data.get("commit_decisions", [])[-1] if report_data.get("commit_decisions") else None
        )
        inspected["latest_lab_run"] = report_data.get("lab_runs", [])[-1] if report_data.get("lab_runs") else None
        inspected["memory_items"] = memory_state["items"]
        inspected["memory_retrievals"] = memory_state["retrievals"]
        inspected["memory_replay_receipts"] = memory_state["replay_receipts"]
        inspected["team_narrative"] = narrative_state["records"]
        return inspected

    def session_events(self, session_id: str) -> List[Dict[str, Any]]:
        return self.store.read_events(session_id)

    def add_action(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = self._open_session(session_id)
        try:
            result = session.execute_action(
                ActionProposal(
                    step_id=payload["step_id"],
                    summary=payload["summary"],
                    code=payload["code"],
                    expected_variables=payload.get("expected_variables", []),
                    completion_claim=payload.get("completion_claim", ""),
                    max_duration_s=float(payload.get("max_duration_s", 5.0)),
                    parent_event_id=payload.get("parent_event_id"),
                )
            )
        finally:
            session.close()
        return result.to_record()

    def add_evidence(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        evidence_text = payload.get("detail", "")
        redacted, had_secret = _redact_secrets(evidence_text)
        evidence_id = payload.get("evidence_id") or f"evidence-{uuid.uuid4().hex[:8]}"
        record = {
            "evidence": {
                "evidence_id": evidence_id,
                "detail": _bounded_excerpt(redacted),
                "raw_secret_redacted": had_secret,
                "source": payload.get("source", "local"),
                "provenance": payload.get("provenance", "user-provided"),
            }
        }
        self._append_event(session_id, "evidence", "session.evidence", record, basin=self.store.inspect_session(session_id)["final_basin"])
        if payload.get("temporary_artifact_text"):
            artifact_dir = self.config.store_dir / "evidence-artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifact_dir / f"{session_id}-{evidence_id}.txt"
            artifact_path.write_text(payload["temporary_artifact_text"], encoding="utf-8")
            self.store.register_artifact(
                session_id,
                artifact_path,
                event_id=evidence_id,
                artifact_type="evidence",
                temporary=bool(payload.get("temporary", False)),
                metadata={"source": payload.get("source", "local")},
            )
        scope = self._visibility_scope(inspected["metadata"].get("privacy_setting", "local-only"))
        fragment_text, _ = redact_text(redacted, scope)
        self._record_memory_item(
            session_id,
            MemoryItem(
                memory_id=f"memory-{evidence_id}",
                origin_session_id=session_id,
                origin_event_id=evidence_id,
                participant=explicit_participant(payload.get("participant")),
                purpose=str(inspected["metadata"].get("purpose", "")),
                content_hash=content_hash(evidence_text),
                provenance=str(payload.get("provenance", "user-provided")),
                evidence_status="supported",
                epistemic_state=EpistemicState(inspected["final_basin"].get("epistemic", EpistemicState.UNRESOLVED.value)),
                action_state=ActionState(inspected["final_basin"].get("action", ActionState.HOLD.value)),
                sensitivity=SensitivityLevel.RESTRICTED if had_secret else SensitivityLevel.MODERATE,
                visibility_scope=scope,
                retention_class=self._retention_class(scope),
                survival_reason="local evidence submitted",
                memory_fragments=[
                    MemoryFragment(
                        fragment_id=f"fragment-{evidence_id}",
                        text=_bounded_excerpt(fragment_text),
                        content_hash=content_hash(fragment_text),
                        provenance=str(payload.get("provenance", "user-provided")),
                    )
                ],
                purpose_links=[
                    MemoryPurposeLink(
                        purpose=str(inspected["metadata"].get("purpose", "")),
                        relevance=1.0,
                        provenance="session-purpose",
                    )
                ]
                if inspected["metadata"].get("purpose")
                else [],
                evidence_links=[
                    MemoryEvidenceLink(
                        evidence_id=evidence_id,
                        detail=_bounded_excerpt(fragment_text),
                        provenance=str(payload.get("provenance", "user-provided")),
                    )
                ],
                replay_references=[session_id],
                created_time=time.time(),
                last_reviewed_time=time.time(),
            ),
            inspected["final_basin"],
        )
        return self.get_session(session_id)

    def add_claim(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        claim_id = payload.get("claim_id") or f"claim-{uuid.uuid4().hex[:8]}"
        trajectory_id = payload.get("trajectory_id", "local-claim")
        claim = DecisionClaim(
            claim_id=claim_id,
            statement=payload["statement"],
            source_trajectory_id=trajectory_id,
            critical=bool(payload.get("critical", True)),
            required_evidence=payload.get("required_evidence", []),
            supporting_evidence=payload.get("supporting_evidence", []),
            contradictory_evidence=payload.get("contradictory_evidence", []),
            provenance=payload.get("provenance", "local-api"),
        )
        trajectory = CandidateTrajectory(
            trajectory_id=trajectory_id,
            answer=payload.get("answer", payload["statement"]),
            reasoning=payload.get("reasoning", payload["statement"]),
            approach=payload.get("approach", "local-claim"),
            provider="scripted",
        )
        decision = ReliabilityEngine().evaluate([trajectory], {trajectory_id: [claim]})
        basin = BasinGovernanceState(
            epistemic=decision.final_epistemic,
            action=decision.final_action,
            provisional=decision.final_action != ActionState.EXTEND,
            reason="; ".join(decision.reasons),
        ).to_record()
        scar_id = ""
        self._append_event(
            session_id,
            "claim",
            "session.claim",
            {
                "claim": {
                    "claim_id": claim.claim_id,
                    "statement": claim.statement,
                    "critical": claim.critical,
                    "required_evidence": claim.required_evidence,
                    "supporting_evidence": claim.supporting_evidence,
                    "contradictory_evidence": claim.contradictory_evidence,
                },
                "decision": {
                    "final_epistemic": decision.final_epistemic.value,
                    "final_action": decision.final_action.value,
                    "reasons": list(decision.reasons),
                },
            },
            basin=basin,
        )
        if claim.contradictory_evidence:
            scar = ScarRegistry().record_scar(
                claim_id=claim.claim_id,
                trajectory_id=trajectory_id,
                prior_epistemic_state=EpistemicState.SUPPORTED,
                contradictory_evidence=claim.contradictory_evidence,
                source="local-api",
                confidence=1.0,
                unresolved_questions=[],
                recovery_eligibility=True,
                provenance="local-api",
            )
            scar_id = scar.scar_id
            self._append_event(
                session_id,
                "scar",
                "session.scar",
                {"scar": {"scar_id": scar.scar_id, "claim_id": scar.claim_id, "evidence": scar.contradictory_evidence}},
                basin=basin,
            )
        scope = self._visibility_scope(inspected["metadata"].get("privacy_setting", "local-only"))
        claim_text, _ = redact_text(claim.statement, scope)
        contradiction_status = "contradicted" if claim.contradictory_evidence else "none"
        self._record_memory_item(
            session_id,
            MemoryItem(
                memory_id=f"memory-{claim_id}",
                origin_session_id=session_id,
                origin_event_id=claim_id,
                participant=explicit_participant(payload.get("participant")),
                purpose=str(inspected["metadata"].get("purpose", "")),
                content_hash=content_hash(claim.statement),
                provenance=claim.provenance,
                evidence_status=(
                    "contradicted"
                    if claim.contradictory_evidence
                    else "supported"
                    if claim.supporting_evidence
                    else "unresolved"
                ),
                epistemic_state=decision.final_epistemic,
                action_state=decision.final_action,
                sensitivity=SensitivityLevel.MODERATE,
                visibility_scope=scope,
                retention_class=self._retention_class(scope),
                survival_reason="claim evaluation recorded",
                contradiction_status=contradiction_status,
                memory_fragments=[
                    MemoryFragment(
                        fragment_id=f"fragment-{claim_id}",
                        text=_bounded_excerpt(claim_text),
                        content_hash=content_hash(claim_text),
                        provenance=claim.provenance,
                    )
                ],
                purpose_links=[
                    MemoryPurposeLink(
                        purpose=str(inspected["metadata"].get("purpose", "")),
                        relevance=1.0,
                        provenance="session-purpose",
                    )
                ]
                if inspected["metadata"].get("purpose")
                else [],
                evidence_links=[
                    MemoryEvidenceLink(
                        evidence_id=f"claim-support-{index + 1}",
                        detail=str(detail),
                        provenance=claim.provenance,
                    )
                    for index, detail in enumerate(claim.supporting_evidence)
                ],
                contradiction_links=[
                    MemoryContradictionLink(
                        contradiction_id=f"claim-contradiction-{index + 1}",
                        detail=str(detail),
                        provenance=claim.provenance,
                    )
                    for index, detail in enumerate(claim.contradictory_evidence)
                ],
                scar_links=[MemoryScarLink(scar_id=scar_id, claim_id=claim_id, provenance="local-api")] if scar_id else [],
                recovery_links=[
                    MemoryRecoveryLink(route_id=f"recovery-{claim_id}", status="open", provenance="local-api")
                ]
                if claim.contradictory_evidence
                else [],
                replay_references=[session_id],
                created_time=time.time(),
                last_reviewed_time=time.time(),
            ),
            basin,
        )
        return self.get_session(session_id)

    def hold_session(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        hold = HoldFogRecord(
            reason=payload["reason"],
            affected_circuit=payload.get("affected_circuit", "guardian"),
            blocked_actions=payload.get("blocked_actions", ["commit"]),
            permitted_actions=payload.get("permitted_actions", ["inspect", "submit_evidence"]),
            required_evidence=payload.get("required_evidence", []),
            review_condition=payload.get("review_condition", "review pending"),
            expiry_condition=payload.get("expiry_condition", "evidence satisfied"),
            recovery_path=payload.get("recovery_path", "submit evidence"),
        )
        basin = BasinGovernanceState(
            epistemic=EpistemicState.UNRESOLVED,
            action=ActionState.HOLD,
            provisional=True,
            reason=hold.reason,
        ).to_record()
        self._append_event(session_id, "hold", "session.hold", {"hold": hold.__dict__}, basin=basin)
        return self.get_session(session_id)

    def retract_session(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        reason = payload["reason"]
        basin = BasinGovernanceState(
            epistemic=EpistemicState.CONTRADICTED,
            action=ActionState.RETRACT,
            provisional=True,
            reason=reason,
        ).to_record()
        self._append_event(
            session_id,
            "retract",
            "session.retract",
            {"retract": {"reason": reason, "contradictory_evidence": payload.get("contradictory_evidence", [])}},
            basin=basin,
        )
        return self.get_session(session_id)

    def commit_session(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = self._open_session(session_id)
        try:
            decision = session.propose_commit(
                CommitProposal(
                    summary=payload["summary"],
                    artifact_paths=payload.get("artifact_paths", []),
                    completion_claim=payload.get("completion_claim", ""),
                    claimed_status=payload.get("claimed_status", "IMPLEMENTED"),
                    parent_event_id=payload.get("parent_event_id"),
                )
            )
        finally:
            session.close()
        return decision.to_record()

    def activation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        purpose = str(payload.get("purpose", "")).strip()
        if not purpose:
            raise ValueError("purpose is required")
        session_payload = {
            "purpose": purpose,
            "privacy_setting": payload.get("privacy_setting", "local-only"),
            "constraints": payload.get("declared_constraints", []),
        }
        created = self.create_session(session_payload)
        session_id = created["session_id"]
        purpose_anchor = f"purpose-{_sha256_text(purpose)[:12]}"
        capability_limitations = []
        provider_name = payload.get("provider_preference", "scripted")
        providers = {item["name"]: item for item in _provider_inventory()}
        chosen = providers.get(provider_name, providers["scripted"])
        if not chosen["available"]:
            capability_limitations.append(f"Provider unavailable: {provider_name}")
        action_result = self.add_action(
            session_id,
            {
                "step_id": "activate-anchor",
                "summary": "Anchor the purpose for local activation",
                "code": f"purpose_anchor = {purpose_anchor!r}\npurpose_text = {purpose[:200]!r}",
                "expected_variables": ["purpose_anchor", "purpose_text"],
            },
        )
        activation = ActivationRecord(
            activation_id=f"activation-{uuid.uuid4().hex[:10]}",
            purpose=purpose,
            purpose_anchor=purpose_anchor,
            desired_output_type=str(payload.get("desired_output_type", "report")),
            provider_preference=provider_name,
            privacy_setting=str(payload.get("privacy_setting", "local-only")),
            selected_next_action="submit_evidence" if not payload.get("optional_evidence") else "review_claims",
            missing_evidence=[] if payload.get("optional_evidence") else ["optional_evidence"],
            contradictions=[],
            capability_limitations=capability_limitations,
        )
        inspected = self.get_session(session_id)
        basin = action_result["basin"]
        self._append_event(session_id, "activation", "session.activation", {"activation": activation.to_record()}, basin=basin)
        report = self.generate_report(session_id)
        return {
            "session_id": session_id,
            "purpose_anchor": purpose_anchor,
            "percept_status": IntakeState.RECEIVED.value,
            "epistemic_state": basin["epistemic"],
            "action_state": basin["action"],
            "missing_evidence": activation.missing_evidence,
            "contradictions": activation.contradictions,
            "selected_next_action": activation.selected_next_action,
            "capability_limitations": capability_limitations,
            "report_location": report["html_path"],
        }

    def _register_directory_artifacts(
        self,
        session_id: str,
        artifact_root: Path,
        *,
        event_id: str,
        artifact_type: str,
    ) -> List[str]:
        registered: List[str] = []
        for path in sorted(artifact_root.rglob("*")):
            if not path.is_file():
                continue
            self.store.register_artifact(
                session_id,
                path,
                event_id=event_id,
                artifact_type=artifact_type,
                metadata={"generated_by": "ephux_local.lab", "relative_path": str(path.relative_to(artifact_root))},
            )
            registered.append(str(path))
        return registered

    def _lab_basin(self, current: Dict[str, Any], *, passed: bool, reason: str) -> Dict[str, Any]:
        if not passed:
            return BasinGovernanceState(
                epistemic=EpistemicState.UNRESOLVED,
                action=ActionState.HOLD,
                provisional=True,
                reason=reason,
            ).to_record()
        if current:
            return current
        return BasinGovernanceState(
            epistemic=EpistemicState.SUPPORTED,
            action=ActionState.EXTEND,
            provisional=False,
            reason=reason,
        ).to_record()

    def run_evaluation_lab(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        artifact_root = self.report_dir / session_id / "labs" / f"evaluation-{int(time.time())}"
        artifact_root.mkdir(parents=True, exist_ok=True)
        summary = run_evaluation_lab_acceptance(artifact_root)
        event_id = self._next_event_id(session_id, "lab")
        basin = self._lab_basin(
            self.store.inspect_session(session_id).get("final_basin", {}),
            passed=bool(summary.get("passed")),
            reason="evaluation_lab_completed" if summary.get("passed") else "evaluation_lab_failed",
        )
        artifacts = self._register_directory_artifacts(
            session_id,
            artifact_root,
            event_id=event_id,
            artifact_type="evaluation_lab",
        )
        event = {
            "type": "session.lab.evaluation",
            "event_id": event_id,
            "timestamp": time.time(),
            "lab": {
                "lab_kind": "evaluation",
                "task_count": summary.get("task_count", 0),
                "family_count": summary.get("family_count", 0),
                "comparison_result_count": summary.get("comparison_result_count", 0),
                "passed": bool(summary.get("passed")),
                "artifact_root": str(artifact_root),
                "artifact_paths": artifacts,
                "requested_by": str(payload.get("requested_by", "local-ui")),
            },
        }
        self.store.append_event(session_id, event, final_basin=basin)
        return {
            "session_id": session_id,
            "event_id": event_id,
            "lab_kind": "evaluation",
            "artifact_root": str(artifact_root),
            "artifact_paths": artifacts,
            "summary": summary,
            "basin": basin,
        }

    def run_natural_math_lab(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        artifact_root = self.report_dir / session_id / "labs" / f"natural-math-{int(time.time())}"
        artifact_root.mkdir(parents=True, exist_ok=True)
        summary = run_natural_math_lab_acceptance(artifact_root)
        event_id = self._next_event_id(session_id, "lab")
        basin = self._lab_basin(
            self.store.inspect_session(session_id).get("final_basin", {}),
            passed=bool(summary.get("passed")),
            reason="natural_math_lab_completed" if summary.get("passed") else "natural_math_lab_failed",
        )
        artifacts = self._register_directory_artifacts(
            session_id,
            artifact_root,
            event_id=event_id,
            artifact_type="natural_math_lab",
        )
        event = {
            "type": "session.lab.natural_math",
            "event_id": event_id,
            "timestamp": time.time(),
            "lab": {
                "lab_kind": "natural_math",
                "run_count": summary.get("parameter_sweep", {}).get("run_count", 0),
                "node_count": summary.get("simulation", {}).get("simulation_metrics", {}).get("node_count", 0),
                "passed": bool(summary.get("passed")),
                "artifact_root": str(artifact_root),
                "artifact_paths": artifacts,
                "requested_by": str(payload.get("requested_by", "local-ui")),
            },
        }
        self.store.append_event(session_id, event, final_basin=basin)
        return {
            "session_id": session_id,
            "event_id": event_id,
            "lab_kind": "natural_math",
            "artifact_root": str(artifact_root),
            "artifact_paths": artifacts,
            "summary": summary,
            "basin": basin,
        }

    def session_labs(self, session_id: str) -> Dict[str, Any]:
        events = [
            event for event in self.store.read_events(session_id) if event.get("type") in {"session.lab.evaluation", "session.lab.natural_math"}
        ]
        runs = [event.get("lab", {}) | {"event_id": event.get("event_id", ""), "timestamp": event.get("timestamp", 0)} for event in events]
        return {"session_id": session_id, "lab_runs": runs}

    def review_session(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        review_action = str(payload.get("review_action", "")).strip()
        reviewer = str(payload.get("reviewer", "local-reviewer")).strip() or "local-reviewer"
        provenance = str(payload.get("provenance", "human-local-review")).strip() or "human-local-review"
        note = str(payload.get("note", "")).strip()
        if not review_action:
            raise ValueError("review_action is required")

        events = self.store.read_events(session_id)
        basin = self.store.inspect_session(session_id)["final_basin"]
        record = {
            "review": {
                "review_action": review_action,
                "reviewer": reviewer,
                "target_id": str(payload.get("target_id", "")),
                "target_type": str(payload.get("target_type", "session")),
                "decision": str(payload.get("decision", "")),
                "note": note,
                "provenance": provenance,
                "contradictory_evidence": list(payload.get("contradictory_evidence", [])),
                "approved_claims": list(payload.get("approved_claims", [])),
            }
        }
        if review_action == "approve_commit":
            commit_events = [event for event in events if event.get("type") == "commit"]
            if not commit_events:
                raise ValueError("No commit proposal exists to approve")
            latest = commit_events[-1]["decision"]
            if not latest.get("allowed", False):
                raise PermissionError("Commit cannot be approved because policy denied the proposal")
        elif review_action == "place_hold":
            return self.hold_session(
                session_id,
                {
                    "reason": payload.get("reason", note or "human review hold"),
                    "required_evidence": payload.get("required_evidence", []),
                    "review_condition": payload.get("review_condition", "human review pending"),
                    "recovery_path": payload.get("recovery_path", "submit additional evidence"),
                },
            )
        self._append_event(session_id, "review", f"session.review.{review_action}", record, basin=basin)
        return self.get_session(session_id)

    def add_narrative(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = NarrativeRecord(
            person=str(payload.get("person", "")),
            contributions=list(payload.get("contributions", [])),
            decisions=list(payload.get("decisions", [])),
            conflicts=list(payload.get("conflicts", [])),
            superseded_decisions=list(payload.get("superseded_decisions", [])),
            unresolved_questions=list(payload.get("unresolved_questions", [])),
            current_purposes=list(payload.get("current_purposes", [])),
            commitments=list(payload.get("commitments", [])),
            failures=list(payload.get("failures", [])),
            recovery_history=list(payload.get("recovery_history", [])),
            visibility_scope=self._visibility_scope(str(payload.get("visibility_scope", "shared-project"))),
            explicit_identity=bool(str(payload.get("person", "")).strip()),
        )
        basin = self.store.inspect_session(session_id)["final_basin"]
        self._append_event(session_id, "narrative", "session.narrative", {"narrative": record.to_record()}, basin=basin)
        return self.session_narrative(session_id)

    def session_narrative(self, session_id: str) -> Dict[str, Any]:
        narrative = self._build_team_narrative(session_id)
        return {"session_id": session_id, "records": narrative.to_records(), "events": list(narrative.events)}

    def session_memory(self, session_id: str) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        memory_map = self._build_memory_map(session_id)
        purpose = str(inspected["metadata"].get("purpose", session_id))
        replay = replay_persisted_session(self.store, session_id)
        return {
            "session_id": session_id,
            "items": memory_map.export_records(),
            "retrievals": [item.to_record() for item in memory_map.retrieve(purpose)],
            "replay_receipts": [item.to_record() for item in memory_map.replay_receipts(session_id, replay["replay_hash"])],
            "events": list(memory_map.events),
        }

    def guardian_intake(self, payload: Dict[str, Any], raw_text: str = "") -> Dict[str, Any]:
        body: Dict[str, Any]
        if raw_text:
            body = {"text": raw_text, "source_metadata": {"content_type": "text/plain"}}
        else:
            body = payload
        session_id = body.get("session_id")
        if session_id:
            self.store.get_session(session_id)
        else:
            session_id = self.create_session({"purpose": body.get("purpose", "guardian intake")})["session_id"]
        self._append_event(session_id, "intake", "guardian.intake.received", {"state": IntakeState.RECEIVED.value}, basin=self.store.inspect_session(session_id)["final_basin"])

        issues: List[str] = []
        source_metadata = body.get("source_metadata", {})
        content = ""
        content_type = source_metadata.get("content_type", "application/json")
        if "text" in body:
            content = str(body["text"])
            content_type = source_metadata.get("content_type", "text/plain")
        elif "json_payload" in body:
            content = _canonical_json(body["json_payload"])
            content_type = "application/json"
        elif "file_name" in body and "file_text" in body:
            file_name = _sanitize_filename(str(body["file_name"]))
            suffix = Path(file_name).suffix.lower()
            if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
                raise ValueError("Unsupported file type")
            content = str(body["file_text"])
            content_type = f"file:{suffix}"
        else:
            raise ValueError("Intake requires text, json_payload, or file_name + file_text")

        content_hash = _sha256_text(content)
        redacted, had_secret = _redact_secrets(content)
        existing = [
            event
            for event in self.store.read_events(session_id)
            if event.get("type") == "guardian.intake.accepted"
            and event.get("intake", {}).get("content_hash") == content_hash
        ]
        sensitivity = body.get("sensitivity", "restricted" if had_secret else "local")
        sanitization_state = (
            SanitizationState.SANITIZED
            if body.get("sanitization_evidence")
            else SanitizationState.EVIDENCE_REQUIRED
        )

        if len(content.encode("utf-8")) > self.config.max_request_bytes:
            issues.append("Oversized input")
            state = IntakeState.REJECTED
            basin = _default_basin(EpistemicState.CONTRADICTED, ActionState.RETRACT, True, "oversized_input")
        elif any(pattern.search(content) for pattern in INSTRUCTION_CONFLICT_PATTERNS) or "<script" in content.lower():
            issues.append("Embedded instruction conflict or script content")
            state = IntakeState.HELD
            basin = _default_basin(EpistemicState.UNRESOLVED, ActionState.HOLD, True, "intake_held")
        elif existing:
            issues.append("Duplicate intake replay")
            state = IntakeState.HELD
            basin = _default_basin(EpistemicState.UNRESOLVED, ActionState.HOLD, True, "duplicate_intake")
        else:
            state = IntakeState.ACCEPTED
            contradictions = 1 if "contradiction" in content.lower() else 0
            pipeline = run_basin_pipeline(redacted, contradictions=contradictions, completion_claim="")
            basin_state = pipeline["basin"]
            basin = {
                "epistemic": basin_state.epistemic.value,
                "action": basin_state.action.value,
                "provisional": basin_state.provisional,
                "reason": "guardian_pipeline",
            }

        record = IntakeRecord(
            intake_id=f"intake-{uuid.uuid4().hex[:10]}",
            state=state,
            content_hash=content_hash,
            content_type=content_type,
            source_metadata=source_metadata,
            sensitivity=sensitivity,
            sanitization_state=sanitization_state,
            duplicate_of=existing[0]["intake"]["intake_id"] if existing else "",
            issues=issues,
            redacted_excerpt=_bounded_excerpt(redacted),
        )
        self._append_event(session_id, "intake", "guardian.intake.parsed", {"state": IntakeState.PARSED.value, "content_type": content_type}, basin=basin)
        self._append_event(
            session_id,
            "intake",
            f"guardian.intake.{state.value.lower()}",
            {"intake": record.to_record()},
            basin=basin,
        )
        if sanitization_state == SanitizationState.SANITIZED:
            self._append_event(
                session_id,
                "intake",
                "guardian.intake.sanitized",
                {
                    "state": IntakeState.SANITIZED.value,
                    "sanitization_evidence": list(body.get("sanitization_evidence", [])),
                },
                basin=basin,
            )
        report = self.generate_report(session_id)
        return {
            "session_id": session_id,
            "intake_state": state.value,
            "report_location": report["html_path"],
            "issues": issues,
            "sanitization_state": sanitization_state.value if "sanitization_state" in locals() else SanitizationState.UNSANITIZED.value,
        }

    def export_session_bundle(self, session_id: str) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        events = self.store.read_events(session_id)
        snapshots = self.store.list_snapshots(session_id)
        report = self.generate_report(session_id)
        report_json = report["report"]
        report_html = Path(report["html_path"]).read_text(encoding="utf-8")
        artifacts = []
        for artifact in self.store.list_artifacts(session_id):
            record = dict(artifact)
            artifact_path = Path(artifact["artifact_path"])
            if artifact_path.exists() and artifact_path.suffix.lower() in TEXT_ARTIFACT_SUFFIXES and artifact_path.is_file():
                record["embedded_text"] = artifact_path.read_text(encoding="utf-8")
            artifacts.append(record)
        bundle = {
            "bundle_version": "1.0",
            "exported_at": time.time(),
            "session": inspected,
            "events": events,
            "snapshots": snapshots,
            "claims": [event.get("claim", {}) for event in events if event.get("type") == "session.claim"],
            "evidence": [event.get("evidence", {}) for event in events if event.get("type") == "session.evidence"],
            "scars": [event.get("scar", {}) for event in events if event.get("type") == "session.scar"],
            "recovery_routes": report_json.get("recovery_routes", []),
            "associations": report_json.get("association_updates", []),
            "reports": {
                "json": report_json,
                "html": report_html,
            },
            "artifacts": artifacts,
        }
        hashes = {
            "events_sha256": _sha256_text(_canonical_json(bundle["events"])),
            "snapshots_sha256": _sha256_text(_canonical_json(bundle["snapshots"])),
            "reports_sha256": _sha256_text(_canonical_json(bundle["reports"])),
            "artifacts_sha256": _sha256_text(_canonical_json(bundle["artifacts"])),
        }
        bundle["hashes"] = hashes
        bundle["bundle_sha256"] = _sha256_text(_canonical_json(bundle))
        return bundle

    def import_session_bundle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        required = {"bundle_version", "session", "events", "snapshots", "reports", "artifacts", "hashes"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(f"Import bundle is missing fields: {missing}")
        session_record = payload["session"]
        session_id = str(session_record["session_id"])
        if self.store.session_exists(session_id):
            raise ValueError(f"Import would overwrite existing session: {session_id}")
        expected = payload["hashes"]
        checks = {
            "events_sha256": _sha256_text(_canonical_json(payload["events"])),
            "snapshots_sha256": _sha256_text(_canonical_json(payload["snapshots"])),
            "reports_sha256": _sha256_text(_canonical_json(payload["reports"])),
            "artifacts_sha256": _sha256_text(_canonical_json(payload["artifacts"])),
        }
        for key, actual in checks.items():
            if expected.get(key, "") != actual:
                raise ValueError(f"Import hash mismatch for {key}")

        metadata = dict(session_record.get("metadata", {}))
        metadata["imported_from_bundle_sha256"] = payload.get("bundle_sha256", "")
        metadata["imported_at"] = time.time()
        self.store.create_session(metadata, session_id=session_id)
        snapshots_by_event = {
            item.get("event_id", ""): item.get("snapshot", {})
            for item in payload.get("snapshots", [])
        }
        events = list(payload["events"])
        last_index = len(events) - 1
        for index, event in enumerate(events):
            final_basin = session_record.get("final_basin", {}) if index == last_index else None
            snapshot = snapshots_by_event.get(event.get("event_id", ""), None)
            self.store.append_event(session_id, event, snapshot=snapshot, final_basin=final_basin)

        target_dir = self.report_dir / session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        html_path = target_dir / f"{session_id}.html"
        json_path = target_dir / f"{session_id}.json"
        html_path.write_text(str(payload["reports"].get("html", "")), encoding="utf-8")
        json_path.write_text(json.dumps(payload["reports"].get("json", {}), indent=2), encoding="utf-8")
        self.store.register_artifact(session_id, html_path, event_id=session_id, artifact_type="trajectory_html", metadata={"imported": True})
        self.store.register_artifact(session_id, json_path, event_id=session_id, artifact_type="trajectory_json", metadata={"imported": True})

        imported_dir = self.config.store_dir / "imported-artifacts" / session_id
        imported_dir.mkdir(parents=True, exist_ok=True)
        for artifact in payload.get("artifacts", []):
            embedded_text = artifact.get("embedded_text")
            artifact_path = Path(str(artifact.get("artifact_path", "")))
            if not embedded_text or not artifact_path.name:
                continue
            restored = imported_dir / artifact_path.name
            restored.write_text(str(embedded_text), encoding="utf-8")
            self.store.register_artifact(
                session_id,
                restored,
                event_id=str(artifact.get("artifact_id", session_id)),
                artifact_type=str(artifact.get("metadata", {}).get("artifact_type", "artifact")),
                temporary=bool(artifact.get("temporary", False)),
                metadata={"imported": True, "original_path": str(artifact_path)},
            )
        return self.get_session(session_id)

    def _candidate_spectrum(self, purpose: str, evidence: List[Dict[str, Any]], claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        retained = [
            {
                "trajectory_id": "candidate-evidence-first",
                "answer": f"Advance '{purpose}' only with auditable evidence.",
                "reasoning": "Local EphUX prefers evidence-bearing progress over unsupported completion claims.",
                "approach": "evidence-first",
                "provider": "local-strategy",
            },
            {
                "trajectory_id": "candidate-contradiction-check",
                "answer": f"Stress-test '{purpose}' against contradictions before extending.",
                "reasoning": f"Observed evidence count={len(evidence)} and claim count={len(claims)} inform contradiction review.",
                "approach": "contradiction-check",
                "provider": "local-strategy",
            },
        ]
        if evidence:
            retained.append(
                {
                    "trajectory_id": "candidate-recovery-route",
                    "answer": f"Use submitted evidence to recover '{purpose}' from HOLD when requirements are satisfied.",
                    "reasoning": "Recovery should preserve contradiction history rather than erase it.",
                    "approach": "recovery-route",
                    "provider": "local-strategy",
                }
            )
        return {
            "retained": retained,
            "merged": [],
            "rejected": [],
            "providers": [provider["name"] for provider in _provider_inventory()],
        }

    def generate_report(self, session_id: str) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        events = self.store.read_events(session_id)
        memory_map = self._build_memory_map(session_id)
        narrative = self._build_team_narrative(session_id)
        claims = [event for event in events if event.get("type") == "session.claim"]
        evidence = [event for event in events if event.get("type") == "session.evidence"]
        holds = [event for event in events if event.get("type") == "session.hold"]
        retracts = [event for event in events if event.get("type") == "session.retract"]
        actions = [event for event in events if event.get("type") == "action"]
        commits = [event for event in events if event.get("type") == "commit"]
        reviews = [event for event in events if event.get("type", "").startswith("session.review.")]
        lab_runs = [event for event in events if event.get("type") in {"session.lab.evaluation", "session.lab.natural_math"}]
        replay = replay_persisted_session(self.store, session_id)
        purpose = inspected["metadata"].get("purpose", "local ephux session")
        spectrum = self._candidate_spectrum(purpose, evidence, claims)
        recovery_routes = []
        associations = []
        for scar_event in [event for event in events if event.get("type") == "session.scar"]:
            scar = scar_event.get("scar", {})
            scar_id = scar.get("scar_id", "")
            claim_id = scar.get("claim_id", "")
            contradictory_evidence = list(scar.get("evidence", []))
            route = RecoveryRoute(
                route_id=f"recovery-{scar_id or claim_id or 'local'}",
                originating_scar_id=scar_id,
                evidence_required=[RecoveryRequirement(description="Resolve contradiction", required_evidence=contradictory_evidence)],
                prohibited_shortcuts=["ignore contradiction", "approve without evidence"],
                permitted_transitions=["CONTRADICTED->UNRESOLVED", "UNRESOLVED->SUPPORTED"],
                review_requirement="Human review required",
                success_condition="Contradictory evidence is answered with new support",
                failure_condition="Contradictions remain unresolved",
                retained_uncertainty="Contradiction history remains visible after recovery",
            )
            recovery_routes.append(
                {
                    "route_id": route.route_id,
                    "originating_scar_id": route.originating_scar_id,
                    "evidence_required": [requirement.__dict__ for requirement in route.evidence_required],
                    "prohibited_shortcuts": list(route.prohibited_shortcuts),
                    "permitted_transitions": list(route.permitted_transitions),
                    "review_requirement": route.review_requirement,
                    "success_condition": route.success_condition,
                    "failure_condition": route.failure_condition,
                    "retained_uncertainty": route.retained_uncertainty,
                }
            )
        for node in memory_map.items.values():
            associations.append(
                {
                    "memory_id": node.memory_id,
                    "purpose_links": [link.to_record() for link in node.purpose_links],
                    "evidence_links": [link.to_record() for link in node.evidence_links],
                    "recovery_routes": [link.to_record() for link in node.recovery_links],
                    "survival_reason": node.survival_reason,
                }
            )
        report = {
            "scenario": session_id,
            "passed": inspected["final_basin"].get("action") != ActionState.RETRACT.value,
            "purpose": purpose,
            "context": inspected["metadata"].get("context", ""),
            "plan": [action["result"]["proposal"]["summary"] for action in actions],
            "retrieved_associations": associations,
            "candidate_spectrum": spectrum,
            "candidate_deduplication": {"note": "Local product path uses stored claims and provider availability"},
            "action_proposals": [action["result"]["proposal"] for action in actions],
            "rigor_decisions": [event for event in events if event.get("type", "").startswith("guardian.intake")],
            "guard_decisions": [action["result"]["guard"] for action in actions],
            "execution_output": [action["result"]["feedback"] for action in actions],
            "namespace_changes": [action["result"]["feedback"]["namespace_diff"] for action in actions],
            "artifacts": inspected["artifacts"],
            "decision_critical_claims": [claim["claim"]["claim_id"] for claim in claims if "claim" in claim],
            "evidence_links": [item.get("evidence", {}) for item in evidence],
            "reliability_verdicts": [claim.get("decision", {}) for claim in claims],
            "contradictions": [event.get("retract", {}) for event in retracts],
            "scars": [event.get("scar", {}) for event in events if event.get("type") == "session.scar"],
            "recovery_routes": recovery_routes,
            "association_updates": associations,
            "memory_governance": {
                "items": memory_map.export_records(),
                "retrievals": [item.to_record() for item in memory_map.retrieve(purpose)],
                "replay_receipts": [item.to_record() for item in memory_map.replay_receipts(session_id, replay["replay_hash"])],
            },
            "team_narrative": narrative.to_records(),
            "hold_intervals": [event.get("hold", {}) for event in holds],
            "commit_decisions": [item["decision"] for item in commits],
            "review_decisions": [item.get("review", {}) for item in reviews],
            "lab_runs": [item.get("lab", {}) | {"event_id": item.get("event_id", "")} for item in lab_runs],
            "replay_result": {
                "basin": replay["basin"].to_record(),
                "errors": replay["errors"],
                "replay_hash": replay["replay_hash"],
            },
            "final_basin_state": inspected["final_basin"],
        }
        target_dir = self.report_dir / session_id
        bundle = write_report_bundle(target_dir, report)
        html_path = target_dir / f"{session_id}.html"
        json_path = target_dir / f"{session_id}.json"
        Path(bundle["html"]).replace(html_path)
        Path(bundle["json"]).replace(json_path)
        self.store.register_artifact(
            session_id,
            html_path,
            event_id=session_id,
            artifact_type="trajectory_html",
            metadata={"generated_by": "ephux_local"},
        )
        self.store.register_artifact(
            session_id,
            json_path,
            event_id=session_id,
            artifact_type="trajectory_json",
            metadata={"generated_by": "ephux_local"},
        )
        return {"html_path": str(html_path), "json_path": str(json_path), "report": report}

    def capabilities(self) -> Dict[str, Any]:
        registry_path = Path(__file__).resolve().parents[2] / "ops" / "manifests" / "capability-registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        return {
            "registry": registry,
            "security_controls": _security_controls(self.config),
            "providers": _provider_inventory(),
            "extension_contract": self.extension_contract(),
            "service": {
                "host": self.config.host,
                "port": self.config.port,
                "loopback_only": self.config.host in {"127.0.0.1", "localhost"},
                "request_size_limit": self.config.max_request_bytes,
                "installable_pwa": True,
                "labs_available": ["evaluation", "natural_math"],
            },
        }

    def extension_contract(self) -> Dict[str, Any]:
        return {
            "send_selection_endpoint": "/guardian/intake",
            "activation_endpoint": "/activation",
            "token_header": "X-Ephux-Token",
            "report_url_template": f"http://{self.config.host}:{self.config.port}/sessions/{{session_id}}/report?format=html",
            "session_list_endpoint": "/sessions",
            "session_import_endpoint": "/sessions/import",
            "session_lab_list_endpoint": "/sessions/{session_id}/labs",
            "session_memory_endpoint": "/sessions/{session_id}/memory",
            "session_narrative_endpoint": "/sessions/{session_id}/narrative",
            "evaluation_lab_endpoint": "/sessions/{session_id}/labs/evaluation",
            "natural_math_lab_endpoint": "/sessions/{session_id}/labs/natural-math",
        }

    def ui_html(self) -> str:
        index_path = self.config.ui_asset_dir / "index.html"
        return index_path.read_text(encoding="utf-8")


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any], *, origin: str = "") -> None:
    body = json.dumps(payload, indent=2, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(handler: BaseHTTPRequestHandler, status: int, text: str, *, content_type: str = "text/plain; charset=utf-8", origin: str = "") -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
    handler.end_headers()
    handler.wfile.write(body)


def _asset_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".webmanifest": "application/manifest+json; charset=utf-8",
        ".json": "application/json; charset=utf-8",
    }.get(suffix, "text/plain; charset=utf-8")


def make_handler(app: EphuxLocalService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "EphuxLocal/0.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _origin(self) -> str:
            origin = self.headers.get("Origin", "")
            return origin if app._allowed_origin(origin) else ""

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length > app.config.max_request_bytes:
                raise ValueError("Request body exceeds local size limit")
            return self.rfile.read(length)

        def _parse_json(self) -> Dict[str, Any]:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise ValueError("Content-Type must be application/json")
            body = self._read_body()
            try:
                return json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON: {exc.msg}") from exc

        def _authorized(self) -> None:
            app._ensure_token({key.lower(): value for key, value in self.headers.items()})

        def do_OPTIONS(self) -> None:
            origin = self._origin()
            self.send_response(HTTPStatus.NO_CONTENT)
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Ephux-Token")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:
            origin = self._origin()
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/":
                    _text_response(self, 200, app.ui_html(), content_type="text/html; charset=utf-8", origin=origin)
                    return
                if parsed.path in {"/app.js", "/manifest.webmanifest", "/sw.js"}:
                    file_name = parsed.path.lstrip("/")
                    asset_path = app.config.ui_asset_dir / file_name
                    _text_response(self, 200, asset_path.read_text(encoding="utf-8"), content_type=_asset_content_type(asset_path), origin=origin)
                    return
                if parsed.path == "/health":
                    _json_response(self, 200, {"ok": True, "service": "ephux_local"}, origin=origin)
                    return
                if parsed.path == "/capabilities":
                    _json_response(self, 200, app.capabilities(), origin=origin)
                    return
                if parsed.path == "/sessions":
                    self._authorized()
                    _json_response(self, 200, {"sessions": app.list_sessions()}, origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/events"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, {"session_id": session_id, "events": app.session_events(session_id)}, origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/labs"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_labs(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/memory"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_memory(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_narrative(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/export"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.export_session_bundle(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/report"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    report = app.generate_report(session_id)
                    if parse_qs(parsed.query).get("format") == ["html"]:
                        _text_response(self, 200, Path(report["html_path"]).read_text(encoding="utf-8"), content_type="text/html; charset=utf-8", origin=origin)
                    else:
                        _json_response(self, 200, report, origin=origin)
                    return
                if parsed.path.startswith("/sessions/"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.get_session(session_id), origin=origin)
                    return
                _json_response(self, 404, {"error": "Not found"}, origin=origin)
            except PermissionError as exc:
                _json_response(self, 403, {"error": str(exc)}, origin=origin)
            except Exception as exc:
                _json_response(self, 400, {"error": str(exc)}, origin=origin)

        def do_POST(self) -> None:
            origin = self._origin()
            parsed = urlparse(self.path)
            try:
                if parsed.path not in {"/health", "/capabilities"}:
                    self._authorized()
                if parsed.path == "/sessions":
                    payload = self._parse_json()
                    _json_response(self, 201, app.create_session(payload), origin=origin)
                    return
                if parsed.path == "/sessions/import":
                    payload = self._parse_json()
                    _json_response(self, 201, app.import_session_bundle(payload), origin=origin)
                    return
                if parsed.path == "/guardian/intake":
                    content_type = self.headers.get("Content-Type", "")
                    if "text/plain" in content_type:
                        body = self._read_body().decode("utf-8")
                        _json_response(self, 201, app.guardian_intake({}, raw_text=body), origin=origin)
                    else:
                        payload = self._parse_json()
                        _json_response(self, 201, app.guardian_intake(payload), origin=origin)
                    return
                if parsed.path == "/activation":
                    payload = self._parse_json()
                    _json_response(self, 201, app.activation(payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/actions"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_action(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/evidence"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_evidence(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/claims"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_claim(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/commit"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.commit_session(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/hold"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.hold_session(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/retract"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.retract_session(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/review"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.review_session(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_narrative(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/labs/evaluation"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.run_evaluation_lab(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/labs/natural-math"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.run_natural_math_lab(session_id, payload), origin=origin)
                    return
                _json_response(self, 404, {"error": "Not found"}, origin=origin)
            except PermissionError as exc:
                _json_response(self, 403, {"error": str(exc)}, origin=origin)
            except Exception as exc:
                _json_response(self, 400, {"error": str(exc)}, origin=origin)

    return Handler


def start_service_in_thread(config: LocalServiceConfig) -> tuple[EphuxLocalService, ThreadingHTTPServer, threading.Thread]:
    app = EphuxLocalService(config)
    handler = make_handler(app)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    app.config.port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return app, server, thread


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--store-dir", default="")
    parser.add_argument("--report-dir", default="")
    parser.add_argument("--token", default="")
    args = parser.parse_args(argv)
    config = LocalServiceConfig(
        host=args.host,
        port=args.port,
        store_dir=Path(args.store_dir) if args.store_dir else default_store_path(),
        report_dir=Path(args.report_dir) if args.report_dir else default_store_path() / "reports",
        token=args.token or secrets.token_urlsafe(24),
    )
    app, server, thread = start_service_in_thread(config)
    try:
        print(
            json.dumps(
                {
                    "host": config.host,
                    "port": config.port,
                    "token": config.token,
                    "loopback_only": config.host in {"127.0.0.1", "localhost"},
                }
            )
        )
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
    return 0
