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
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from copy import deepcopy
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
from python.cognitive_basin.authority import (
    ActionPermit,
    ActionTarget,
    ApprovalGrant,
    AuthorityClass,
    AuthorityLedger,
    AuthorityManager,
    AuthorityRequirement,
    ExecutionReceipt,
    ExternalActionProposal,
    PermitRevocation,
    RollbackPlan,
    SideEffectDeclaration,
    VerificationPlan,
)
from python.cognitive_basin.authority.manager import payload_hash
from python.cognitive_basin.connectors import ConnectorRequest, ConnectorScope, build_default_registry
from python.cognitive_basin.consciousness import OperationalConsciousnessKernel
from python.cognitive_basin.consciousness.perception import (
    Constant,
    ConstantClass,
    ConstantDomain,
    ConstantEvidence,
    ConstantExpiry,
    ConstantScope,
    ConstantSource,
    ConstantValue,
    Percept,
    PerceptChannel,
    PerceptFeature,
    PerceptModality,
    PerceptReliability,
    PerceptSource,
)
from python.cognitive_basin.consciousness.purpose import (
    Purpose,
    PurposeConstraint,
    PurposeDependency,
    PurposePriority,
    PurposeSource,
)
from python.cognitive_basin.causality import (
    CausalClaim,
    CausalEvidence,
    InterventionControl,
    InterventionPrediction,
    InterventionProposal,
    InterventionTarget,
    InterventionValue,
    InterventionVariable,
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
from python.cognitive_basin.world_model import WorldObservation
from python.evaluation_lab.acceptance import run_acceptance_suite as run_evaluation_lab_acceptance
from python.natural_math_lab.acceptance import run_acceptance_suite as run_natural_math_lab_acceptance
from python.provider_lab import local_model_inventory, provider_inventory

from .contracts import ActivationRecord, IntakeRecord, IntakeState, SanitizationState


MAX_REQUEST_BYTES = 256_000
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
        self.authority = AuthorityManager()
        self.connector_registry = build_default_registry(Path(__file__).resolve().parents[2])
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

    def _participant_from_payload(self, payload: Dict[str, Any]) -> str:
        if bool(payload.get("infer_participant")):
            raise ValueError("Participant inference is not allowed")
        if str(payload.get("participant_mode", "explicit")).strip().lower() != "explicit":
            raise ValueError("Participant mode must remain explicit")
        if str(payload.get("participant_source", "explicit")).strip().lower() != "explicit":
            raise ValueError("Participant source must remain explicit")
        return explicit_participant(payload.get("participant"))

    def _visible_to_participant(self, item: MemoryItem, viewer_participant: str) -> bool:
        viewer = explicit_participant(viewer_participant)
        if item.visibility_scope in {VisibilityScope.SHARED_PROJECT, VisibilityScope.SESSION_ONLY, VisibilityScope.AUDIT_RETAINED}:
            return True
        if item.visibility_scope == VisibilityScope.EXPORTABLE_REDACTED:
            return True
        if item.visibility_scope == VisibilityScope.PRIVATE_JAMES:
            return viewer == "James Clow"
        if item.visibility_scope == VisibilityScope.PRIVATE_MELISSA:
            return viewer == "Melissa Clow"
        return viewer == item.participant

    def _privacy_state(self, session_id: str) -> Dict[str, Any]:
        events = self.store.read_events(session_id)
        legal_holds = [event.get("privacy", {}) for event in events if event.get("type") == "session.privacy.legal_hold"]
        deletion_requests = [event.get("privacy", {}) for event in events if event.get("type") == "session.privacy.deletion_request"]
        exports = [event.get("privacy", {}) for event in events if event.get("type") == "session.privacy.export"]
        return {
            "legal_holds": legal_holds,
            "deletion_requests": deletion_requests,
            "exports": exports,
        }

    def _active_legal_hold(self, session_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
        privacy_state = self._privacy_state(session_id)
        for hold in privacy_state["legal_holds"]:
            target = str(hold.get("target_memory_id", ""))
            if target in {"", memory_id} and str(hold.get("status", "ACTIVE")) == "ACTIVE":
                return hold
        return None

    def _clone_memory_item(self, session_id: str, memory_id: str) -> MemoryItem:
        memory_map = self._build_memory_map(session_id)
        if memory_id not in memory_map.items:
            raise ValueError(f"Unknown memory item: {memory_id}")
        return MemoryItem.from_record(memory_map.items[memory_id].to_record())

    def _external_action_ledger(self, session_id: str) -> AuthorityLedger:
        return AuthorityLedger.from_events(self.store.read_events(session_id))

    def _visibility_enum(self, raw_value: str) -> VisibilityScope:
        normalized = str(raw_value or "SHARED_PROJECT").strip().replace("-", "_").upper()
        try:
            return VisibilityScope(normalized)
        except Exception:
            return VisibilityScope.SHARED_PROJECT

    def _external_action_visible(self, record: Dict[str, Any], viewer_participant: str) -> bool:
        scope = self._visibility_enum(str(record.get("visibility_scope", VisibilityScope.SHARED_PROJECT.value)))
        viewer = explicit_participant(viewer_participant)
        if scope in {VisibilityScope.SHARED_PROJECT, VisibilityScope.SESSION_ONLY, VisibilityScope.EXPORTABLE_REDACTED, VisibilityScope.AUDIT_RETAINED}:
            return True
        if scope == VisibilityScope.PRIVATE_JAMES:
            return viewer == "James Clow"
        if scope == VisibilityScope.PRIVATE_MELISSA:
            return viewer == "Melissa Clow"
        return viewer == explicit_participant(record.get("participant"))

    def _required_authority_for_operation(self, connector_id: str, operation: str, environment: str) -> AuthorityRequirement:
        env = str(environment or "LOCAL").strip().upper()
        if connector_id == "local-filesystem" and operation == "WRITE_TEXT":
            return AuthorityRequirement(AuthorityClass.LOCAL_WRITE, "Local filesystem mutation requires explicit local-write permit")
        if connector_id == "github" and operation == "BRANCH_PUSH":
            if env == "PRODUCTION":
                return AuthorityRequirement(AuthorityClass.PRODUCTION_WRITE, "Production release authority is required")
            return AuthorityRequirement(AuthorityClass.PRIVATE_REPOSITORY_WRITE, "Repository write authority is required")
        if connector_id == "cloudflare":
            if env == "PRODUCTION":
                return AuthorityRequirement(AuthorityClass.PRODUCTION_WRITE, "Production Cloudflare changes require production authority", requires_rollback=True)
            return AuthorityRequirement(AuthorityClass.PREVIEW_DEPLOYMENT, "Preview Cloudflare changes require preview deployment authority", requires_rollback=True)
        if connector_id == "stripe":
            return AuthorityRequirement(AuthorityClass.BILLING_CHANGE, "Billing changes require billing authority", requires_rollback=True)
        if operation in {"DELETE", "DESTROY", "HTTP_WRITE"}:
            return AuthorityRequirement(AuthorityClass.DESTRUCTIVE_OPERATION, "Destructive operations require separate authority", requires_rollback=True)
        return AuthorityRequirement(AuthorityClass.READ_ONLY, "Read-only connector access")

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

    def _repo_head(self) -> str:
        result = subprocess.run(
            ["git", "-C", str(Path(__file__).resolve().parents[2]), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def _consciousness_kernel(self, session_id: str) -> OperationalConsciousnessKernel:
        inspected = self.store.inspect_session(session_id)
        metadata = inspected.get("metadata", {})
        return OperationalConsciousnessKernel.from_events(
            session_id=session_id,
            events=self.store.read_events(session_id),
            purpose_text=str(metadata.get("purpose", "")),
            participant="UNKNOWN",
            repo_head=self._repo_head(),
            connectors=self.list_connectors(),
        )

    def _percept_from_payload(self, payload: Dict[str, Any], index: int = 1) -> Percept:
        modality_text = str(payload.get("modality", PerceptModality.TEXT.value))
        source_text = str(payload.get("source_type", PerceptSource.HUMAN.value)).upper()
        channel_text = str(payload.get("channel", PerceptChannel.USER.value)).upper()
        content = payload.get("content", payload.get("detail", ""))
        topic = str(payload.get("topic", payload.get("label", f"percept-{index}")))
        return Percept(
            percept_id=str(payload.get("percept_id", f"percept-{uuid.uuid4().hex[:8]}")),
            source=str(payload.get("source", "ephux-local")),
            source_type=PerceptSource(source_text),
            timestamp=float(payload.get("timestamp", time.time())),
            observed_content_hash=content_hash(str(content)),
            modality=PerceptModality(modality_text),
            channel=PerceptChannel(channel_text),
            content=content,
            confidence=float(payload.get("confidence", 0.8)),
            reliability=PerceptReliability(
                current=float(payload.get("confidence", 0.8)),
                history=list(payload.get("reliability_history", [float(payload.get("confidence", 0.8))])),
                source_dependence=float(payload.get("source_dependence", 0.0)),
            ),
            privacy_classification=str(payload.get("privacy_classification", "restricted")),
            provenance=str(payload.get("provenance", "ephux-local")),
            novelty=float(payload.get("novelty", 0.5)),
            salience=float(payload.get("salience", 0.5)),
            purpose_relevance=float(payload.get("purpose_relevance", 0.8)),
            contradiction_links=list(payload.get("contradiction_links", [])),
            prediction_links=list(payload.get("prediction_links", [])),
            verification_state=str(payload.get("verification_state", "OBSERVATION")),
            retention_policy=str(payload.get("retention_policy", "SESSION_WORKING")),
            features=[PerceptFeature("topic", topic, 1.0)]
            + [PerceptFeature(**feature) for feature in payload.get("features", []) if feature.get("key") != "topic"],
        )

    def _constant_from_payload(self, payload: Dict[str, Any], index: int = 1) -> Constant:
        expiry_until = float(payload.get("valid_until", 0.0) or 0.0)
        return Constant(
            constant_id=str(payload.get("constant_id", f"constant-{index}")),
            constant_class=ConstantClass(str(payload.get("constant_class", ConstantClass.SYSTEM_CONSTRAINT.value))),
            value=ConstantValue(payload.get("value"), str(payload.get("unit", ""))),
            domain=ConstantDomain(str(payload.get("domain_id", "domain")), str(payload.get("domain_type", "system")), str(payload.get("domain_detail", "ephux-local"))),
            scope=ConstantScope(str(payload.get("scope_id", "scope")), str(payload.get("scope_type", "session")), str(payload.get("scope_detail", "ephux-local"))),
            source=ConstantSource(str(payload.get("source", "ephux-local")), str(payload.get("source_type", "policy")), str(payload.get("provenance", "ephux-local"))),
            evidence=[ConstantEvidence(str(payload.get("evidence_id", f"evidence-{index}")), str(payload.get("evidence_detail", "explicit constant")), float(payload.get("confidence", 1.0)))],
            confidence=float(payload.get("confidence", 1.0)),
            validity_interval=ConstantExpiry(valid_from=float(payload.get("valid_from", time.time())), valid_until=expiry_until),
            expiry=ConstantExpiry(valid_from=float(payload.get("valid_from", time.time())), valid_until=expiry_until) if expiry_until else None,
            applicability_conditions=list(payload.get("applicability_conditions", [])),
            category=str(payload.get("category", "constraint")),
        )

    def _purpose_from_payload(self, payload: Dict[str, Any]) -> Purpose:
        return Purpose(
            purpose_id=str(payload.get("purpose_id", f"purpose-{uuid.uuid4().hex[:8]}")),
            description=str(payload.get("description", payload.get("purpose", ""))),
            source=PurposeSource(str(payload.get("source_type", "explicit human request")), str(payload.get("source_detail", "ephux-local"))),
            priority=PurposePriority(float(payload.get("priority_weight", 1.0)), float(payload.get("priority_urgency", 0.2))),
            constraints=[PurposeConstraint(str(item)) if not isinstance(item, dict) else PurposeConstraint(str(item.get("detail", ""))) for item in payload.get("constraints", [])],
            dependencies=[
                PurposeDependency(str(payload.get("purpose_id", "")), str(item))
                if not isinstance(item, dict)
                else PurposeDependency(str(payload.get("purpose_id", "")), str(item.get("depends_on", "")))
                for item in payload.get("dependencies", [])
            ],
            status=str(payload.get("status", "ACTIVE")),
        )

    def _world_observation_from_payload(self, payload: Dict[str, Any], index: int = 1) -> WorldObservation:
        return WorldObservation(
            observation_id=str(payload.get("observation_id", f"observation-{uuid.uuid4().hex[:8]}")),
            entity_type=str(payload.get("entity_type", "ABSTRACT_OBJECT")),
            property_name=str(payload.get("property_name", payload.get("topic", f"property-{index}"))),
            value=payload.get("value", payload.get("content", "")),
            category=str(payload.get("category", "OBSERVED")).upper(),
            source=str(payload.get("source", "ephux-local")),
            provenance=str(payload.get("provenance", "ephux-local")),
            timestamp=float(payload.get("timestamp", time.time())),
            entity_id=str(payload.get("entity_id", "")),
            identity_hints=dict(payload.get("identity_hints", {})),
            visibility=str(payload.get("visibility", "SHARED_PROJECT")),
            uncertainty=float(payload.get("uncertainty", 0.0)),
            contradiction_links=list(payload.get("contradiction_links", [])),
        )

    def _causal_claim_from_payload(self, payload: Dict[str, Any]) -> CausalClaim:
        evidence_payloads = payload.get("evidence", [])
        if not evidence_payloads:
            evidence_payloads = [{"detail": str(payload.get("evidence_detail", "deterministic local evidence"))}]
        return CausalClaim(
            claim_id=str(payload.get("claim_id", f"claim-{uuid.uuid4().hex[:8]}")),
            source_node_id=str(payload.get("source_node_id", payload.get("source_variable", ""))),
            target_node_id=str(payload.get("target_node_id", payload.get("target_variable", ""))),
            relation_type=str(payload.get("relation_type", "HYPOTHESIZED")).upper(),
            evidence=[CausalEvidence(str(item.get("detail", item))) for item in evidence_payloads],
            confounders=list(payload.get("confounders", [])),
            alternative_explanations=list(payload.get("alternative_explanations", [])),
            confidence=float(payload.get("confidence", 0.4)),
            validity_scope=str(payload.get("validity_scope", "LOCAL")),
        )

    def _intervention_from_payload(self, payload: Dict[str, Any]) -> InterventionProposal:
        return InterventionProposal(
            proposal_id=str(payload.get("proposal_id", f"intervention-{uuid.uuid4().hex[:8]}")),
            target=InterventionTarget(str(payload.get("target_id", "")), str(payload.get("target_type", "SIMULATION"))),
            variable=InterventionVariable(str(payload.get("variable", payload.get("property_name", "")))),
            value=InterventionValue(payload.get("value")),
            control=InterventionControl(payload.get("control_value")),
            prediction=InterventionPrediction(str(payload.get("prediction_detail", "bounded local intervention"))),
            allowed_domain=str(payload.get("allowed_domain", "SIMULATION")),
            simulated=bool(payload.get("simulated", True)),
        )

    def session_consciousness(self, session_id: str) -> Dict[str, Any]:
        return self._consciousness_kernel(session_id).snapshot().to_record()

    def session_consciousness_workspace(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "workspace": consciousness.get("workspace", {})}

    def session_consciousness_attention(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "attention": consciousness.get("attention", {})}

    def session_consciousness_self(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "self_model": consciousness.get("self_model", {})}

    def session_consciousness_continuity(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "continuity": consciousness.get("continuity", {})}

    def session_consciousness_purposes(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "purposes": consciousness.get("purposes", {})}

    def session_consciousness_episodes(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "episodes": consciousness.get("episodes", [])}

    def session_consciousness_episode(self, session_id: str, episode_id: str) -> Dict[str, Any]:
        episodes = self.session_consciousness_episodes(session_id)["episodes"]
        for episode in episodes:
            if episode.get("episode_id") == episode_id:
                return {"session_id": session_id, "episode": episode}
        raise ValueError(f"Unknown consciousness episode: {episode_id}")

    def session_world(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "world": consciousness.get("world", {})}

    def session_world_entities(self, session_id: str) -> Dict[str, Any]:
        world = self.session_world(session_id)["world"]
        return {"session_id": session_id, "entities": world.get("snapshot", {}).get("entities", [])}

    def session_world_events(self, session_id: str) -> Dict[str, Any]:
        world = self.session_world(session_id)["world"]
        return {"session_id": session_id, "events": world.get("snapshot", {}).get("events", [])}

    def session_predictions(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "prediction": consciousness.get("prediction", {})}

    def session_prediction_errors(self, session_id: str) -> Dict[str, Any]:
        prediction = self.session_predictions(session_id)["prediction"]
        return {"session_id": session_id, "prediction_errors": prediction.get("residuals", [])}

    def session_interoception(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "interoception": consciousness.get("interoception", {})}

    def session_regulation(self, session_id: str) -> Dict[str, Any]:
        interoception = self.session_interoception(session_id)["interoception"]
        return {"session_id": session_id, "regulation": {"pressures": interoception.get("pressures", []), "proposals": interoception.get("proposals", [])}}

    def session_causal_model(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "causal_model": consciousness.get("causal_model", {})}

    def session_perspectives(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "perspectives": consciousness.get("perspectives", {})}

    def session_plans(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "plans": consciousness.get("plans", [])}

    def session_rehearsals(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "rehearsals": consciousness.get("rehearsals", {})}

    def session_anomalies(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "anomalies": consciousness.get("anomalies", {})}

    def session_calibration(self, session_id: str) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        return {"session_id": session_id, "calibration": consciousness.get("calibration", {})}

    def add_consciousness_percepts(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        percept_payloads = payload.get("percepts", [])
        if not percept_payloads:
            percept_payloads = [payload]
        percepts = [self._percept_from_payload(item, index) for index, item in enumerate(percept_payloads, start=1)]
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.percept",
            {"percepts": [item.to_record() for item in percepts]},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        constant_payloads = payload.get("constants", [])
        if constant_payloads:
            constants = [self._constant_from_payload(item, index) for index, item in enumerate(constant_payloads, start=1)]
            self._append_event(
                session_id,
                "consciousness",
                "session.consciousness.constant",
                {"constants": [item.to_record() for item in constants]},
                basin=self.store.inspect_session(session_id)["final_basin"],
            )
        return self.session_consciousness(session_id)

    def add_consciousness_purpose(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        purpose = self._purpose_from_payload(payload)
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.purpose",
            {"purpose": purpose.to_record()},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_consciousness_purposes(session_id)

    def set_consciousness_attention(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        detail = {
            "lock_target_id": str(payload.get("lock_target_id", payload.get("target_id", ""))),
            "reason": str(payload.get("reason", "manual")),
        }
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.attention",
            {"attention": detail},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_consciousness_attention(session_id)

    def pause_consciousness(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.pause",
            {"reason": str(payload.get("reason", "paused"))},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_consciousness(session_id)

    def resume_consciousness(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.resume",
            {"reason": str(payload.get("reason", "resumed"))},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_consciousness(session_id)

    def add_world_observations(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        observation_payloads = payload.get("observations", [])
        if not observation_payloads:
            observation_payloads = [payload]
        observations = [self._world_observation_from_payload(item, index) for index, item in enumerate(observation_payloads, start=1)]
        self._append_event(
            session_id,
            "world",
            "session.world.observation",
            {"observations": [item.to_record() for item in observations]},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_world(session_id)

    def add_prediction_request(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction = {
            "entity_id": str(payload.get("entity_id", "")),
            "property_name": str(payload.get("property_name", payload.get("topic", "state"))),
            "expected_value": payload.get("expected_value"),
            "horizon": str(payload.get("horizon", "NEXT_CYCLE")),
            "source_model": str(payload.get("source_model", "predictive-cognition")),
            "confidence": float(payload.get("confidence", 0.6)),
            "assumptions": list(payload.get("assumptions", [])),
            "evidence": list(payload.get("evidence", [])),
            "verification_method": str(payload.get("verification_method", "future observation")),
            "expiry": float(payload.get("expiry", time.time() + 60.0)),
        }
        self._append_event(
            session_id,
            "prediction",
            "session.prediction.request",
            {"prediction": prediction},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return {"session_id": session_id, "prediction_request": prediction}

    def add_causal_hypothesis(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = self._causal_claim_from_payload(payload)
        self._append_event(
            session_id,
            "causal",
            "session.causal.hypothesis",
            {"claim": claim.to_record()},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_causal_model(session_id)

    def add_intervention_request(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        proposal = self._intervention_from_payload(payload)
        self._append_event(
            session_id,
            "intervention",
            "session.intervention",
            {"intervention": proposal.to_record()},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return {"session_id": session_id, "intervention": proposal.to_record()}

    def add_perspective_record(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "owner_id": str(payload.get("owner_id", payload.get("participant", "UNKNOWN"))),
            "owner_class": str(payload.get("owner_class", "UNKNOWN")),
            "statement": str(payload.get("statement", payload.get("detail", ""))),
            "label": str(payload.get("label", "uncertainty")),
            "evidence_category": str(payload.get("evidence_category", "UNKNOWN")),
        }
        self._append_event(
            session_id,
            "perspective",
            "session.perspective.record",
            {"perspective": record},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return self.session_perspectives(session_id)

    def add_plan_request(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = {
            "purpose": str(payload.get("purpose", payload.get("description", ""))),
            "horizon": str(payload.get("horizon", "SESSION")),
            "requested_by": str(payload.get("requested_by", "ephux-local")),
        }
        self._append_event(
            session_id,
            "plan",
            "session.plan.request",
            {"plan_request": request},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return {"session_id": session_id, "plan_request": request, "plans": self.session_plans(session_id)["plans"]}

    def add_rehearsal_request(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        detail = str(payload.get("detail", "offline rehearsal"))
        self._append_event(
            session_id,
            "rehearsal",
            "session.rehearsal.request",
            {"detail": detail},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return {"session_id": session_id, "detail": detail}

    def review_world(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        review = {
            "requested_by": str(payload.get("requested_by", "ephux-local")),
            "world": self.session_world(session_id)["world"],
            "prediction_errors": self.session_prediction_errors(session_id)["prediction_errors"],
        }
        self._append_event(
            session_id,
            "world",
            "session.world.review",
            {"review": review},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return {"session_id": session_id, "review": review}

    def review_consciousness(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        consciousness = self.session_consciousness(session_id)
        review = {
            "requested_by": str(payload.get("requested_by", "ephux-local")),
            "metacognition": consciousness.get("metacognition", {}),
            "current_action_state": consciousness.get("current_action_state", ActionState.HOLD.value),
            "current_epistemic_state": consciousness.get("current_epistemic_state", EpistemicState.UNRESOLVED.value),
        }
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.review",
            {"review": review},
            basin=self.store.inspect_session(session_id)["final_basin"],
        )
        return {"session_id": session_id, "review": review}

    def run_consciousness_cycle(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        kernel = self._consciousness_kernel(session_id)
        for index, percept_payload in enumerate(payload.get("percepts", []), start=1):
            kernel.add_percept(self._percept_from_payload(percept_payload, index))
        for index, constant_payload in enumerate(payload.get("constants", []), start=1):
            kernel.add_constant(self._constant_from_payload(constant_payload, index))
        for index, observation_payload in enumerate(payload.get("observations", []), start=1):
            kernel.add_world_observation(self._world_observation_from_payload(observation_payload, index))
        if payload.get("prediction_request"):
            kernel.add_prediction_spec(dict(payload.get("prediction_request", {})))
        for prediction_payload in payload.get("predictions", []):
            kernel.add_prediction_spec(dict(prediction_payload))
        if payload.get("causal_claim"):
            kernel.add_causal_claim(self._causal_claim_from_payload(dict(payload.get("causal_claim", {}))))
        for claim_payload in payload.get("causal_claims", []):
            kernel.add_causal_claim(self._causal_claim_from_payload(dict(claim_payload)))
        if payload.get("intervention"):
            kernel.add_intervention(self._intervention_from_payload(dict(payload.get("intervention", {}))))
        for intervention_payload in payload.get("interventions", []):
            kernel.add_intervention(self._intervention_from_payload(dict(intervention_payload)))
        if payload.get("perspective"):
            kernel.add_perspective_record(dict(payload.get("perspective", {})))
        for perspective_payload in payload.get("perspectives", []):
            kernel.add_perspective_record(dict(perspective_payload))
        if payload.get("rehearsal_detail"):
            kernel.add_rehearsal_request(str(payload.get("rehearsal_detail")))
        if payload.get("purpose") or payload.get("description"):
            kernel.add_purpose(self._purpose_from_payload(payload))
        result = kernel.run_cycle(
            events=self.store.read_events(session_id),
            connectors=self.list_connectors(),
            claimed_capabilities=dict(payload.get("claimed_capabilities", {})),
            tested_capabilities=dict(payload.get("tested_capabilities", {})),
            allow_internal_action=bool(payload.get("allow_internal_action", False)),
        )
        result_record = result.to_record()
        self._append_event(
            session_id,
            "consciousness",
            "session.consciousness.cycle",
            {"cycle_result": result_record},
            basin=result.basin,
        )
        scope = self._visibility_scope(self.store.inspect_session(session_id)["metadata"].get("privacy_setting", "local-only"))
        episode = result.episode_receipt.episode
        if episode.memory_effect.memory_ids:
            memory_id = episode.memory_effect.memory_ids[0]
            self._record_memory_item(
                session_id,
                MemoryItem(
                    memory_id=memory_id,
                    origin_session_id=session_id,
                    origin_event_id=result.cycle_id,
                    participant="UNKNOWN",
                    purpose=episode.purpose.description,
                    content_hash=content_hash(episode.content.summary),
                    provenance="consciousness-cycle",
                    evidence_status="supported" if result.basin["epistemic"] == EpistemicState.SUPPORTED.value else "unresolved",
                    epistemic_state=EpistemicState(result.basin["epistemic"]),
                    action_state=ActionState(result.basin["action"]),
                    sensitivity=SensitivityLevel.MODERATE,
                    visibility_scope=scope,
                    retention_class=self._retention_class(scope),
                    survival_reason="conscious episode summary",
                    memory_fragments=[
                        MemoryFragment(
                            fragment_id=f"fragment-{memory_id}",
                            text=_bounded_excerpt(episode.content.summary),
                            content_hash=content_hash(episode.content.summary),
                            provenance="consciousness-cycle",
                        )
                    ],
                    purpose_links=[MemoryPurposeLink(episode.purpose.description, 1.0, "consciousness-cycle")],
                    contradiction_links=[
                        MemoryContradictionLink(item, "episode contradiction", "consciousness-cycle")
                        for item in episode.contradictions
                    ],
                    replay_references=[result.cycle_id],
                    created_time=time.time(),
                    last_reviewed_time=time.time(),
                ),
                result.basin,
            )
        return {"session_id": session_id, "cycle": result_record, "consciousness": kernel.snapshot().to_record()}

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
        stored = self.store.get_session(session_id)
        return {
            "session_id": stored.session_id,
            "created_at": stored.created_at,
            "updated_at": stored.updated_at,
            "purpose": stored.metadata.get("purpose", ""),
            "context": stored.metadata.get("context", ""),
            "privacy_setting": stored.metadata.get("privacy_setting", "local-only"),
            "constraints": stored.metadata.get("constraints", []),
            "final_basin": stored.final_basin or _default_basin(),
            "event_count": 0,
        }

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
        privacy_state = self._privacy_state(session_id)
        external_actions = self.list_external_actions(session_id)["external_actions"]
        consciousness = self.session_consciousness(session_id)
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
        inspected["privacy_governance"] = privacy_state
        inspected["external_actions"] = external_actions
        inspected["consciousness"] = consciousness
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
        participant = self._participant_from_payload(payload) if any(key in payload for key in {"participant", "participant_mode", "participant_source", "infer_participant"}) else "UNKNOWN"
        scope = (
            VisibilityScope(str(payload["visibility_scope"]))
            if payload.get("visibility_scope")
            else self._visibility_scope(inspected["metadata"].get("privacy_setting", "local-only"))
        )
        fragment_text, _ = redact_text(redacted, scope)
        self._record_memory_item(
            session_id,
            MemoryItem(
                memory_id=f"memory-{evidence_id}",
                origin_session_id=session_id,
                origin_event_id=evidence_id,
                participant=participant,
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
        participant = self._participant_from_payload(payload) if any(key in payload for key in {"participant", "participant_mode", "participant_source", "infer_participant"}) else "UNKNOWN"
        scope = (
            VisibilityScope(str(payload["visibility_scope"]))
            if payload.get("visibility_scope")
            else self._visibility_scope(inspected["metadata"].get("privacy_setting", "local-only"))
        )
        claim_text, _ = redact_text(claim.statement, scope)
        contradiction_status = "contradicted" if claim.contradictory_evidence else "none"
        self._record_memory_item(
            session_id,
            MemoryItem(
                memory_id=f"memory-{claim_id}",
                origin_session_id=session_id,
                origin_event_id=claim_id,
                participant=participant,
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
        summary = run_evaluation_lab_acceptance(artifact_root, comparison_task_limit=4)
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

    def add_narrative_contribution(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        contribution = str(payload.get("contribution", "")).strip()
        if not contribution:
            raise ValueError("contribution is required")
        return self.add_narrative(
            session_id,
            {
                "person": participant if participant != "UNKNOWN" else "",
                "contributions": [contribution],
                "current_purposes": list(payload.get("current_purposes", [])),
                "visibility_scope": payload.get("visibility_scope", "shared-project"),
            },
        )

    def add_narrative_decision(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        decision = str(payload.get("decision", "")).strip()
        if not decision:
            raise ValueError("decision is required")
        superseded = str(payload.get("superseded_decision", "")).strip()
        return self.add_narrative(
            session_id,
            {
                "person": participant if participant != "UNKNOWN" else "",
                "decisions": [decision],
                "superseded_decisions": [superseded] if superseded else [],
                "current_purposes": list(payload.get("current_purposes", [])),
                "visibility_scope": payload.get("visibility_scope", "shared-project"),
            },
        )

    def add_narrative_disagreement(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        disagreement = str(payload.get("disagreement", "")).strip()
        if not disagreement:
            raise ValueError("disagreement is required")
        unresolved = str(payload.get("unresolved_question", "")).strip()
        return self.add_narrative(
            session_id,
            {
                "person": participant if participant != "UNKNOWN" else "",
                "conflicts": [disagreement],
                "unresolved_questions": [unresolved] if unresolved else [],
                "visibility_scope": payload.get("visibility_scope", "shared-project"),
            },
        )

    def add_narrative_commitment(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        commitment = str(payload.get("commitment", "")).strip()
        if not commitment:
            raise ValueError("commitment is required")
        failure = str(payload.get("failure", "")).strip()
        recovery = str(payload.get("recovery", "")).strip()
        return self.add_narrative(
            session_id,
            {
                "person": participant if participant != "UNKNOWN" else "",
                "commitments": [commitment],
                "failures": [failure] if failure else [],
                "recovery_history": [recovery] if recovery else [],
                "visibility_scope": payload.get("visibility_scope", "shared-project"),
            },
        )

    def session_narrative(self, session_id: str, viewer_participant: str = "UNKNOWN") -> Dict[str, Any]:
        narrative = self._build_team_narrative(session_id)
        records = narrative.to_records()
        return {
            "session_id": session_id,
            "viewer_participant": explicit_participant(viewer_participant),
            "records": records,
            "events": list(narrative.events),
            "participant_histories": {
                record["participant_id"]: record for record in records
            },
        }

    def retrieve_memory(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        purpose = str(payload.get("purpose", "")).strip() or str(self.store.inspect_session(session_id)["metadata"].get("purpose", session_id))
        memory_state = self.session_memory(session_id, viewer_participant=participant, purpose_override=purpose)
        return {
            "session_id": session_id,
            "viewer_participant": participant,
            "purpose": purpose,
            "retrievals": memory_state["retrievals"],
            "items": memory_state["items"],
        }

    def promote_memory(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        provenance = str(payload.get("provenance", "memory-promote")).strip() or "memory-promote"
        memory_id = str(payload.get("memory_id", "")).strip()
        if not memory_id:
            raise ValueError("memory_id is required")
        item = self._clone_memory_item(session_id, memory_id)
        if not self._visible_to_participant(item, participant):
            raise PermissionError("Requested memory item is not visible to this participant")
        note = str(payload.get("note", "verified-use")).strip() or "verified-use"
        item.successful_uses.append(note)
        if payload.get("replay_reference"):
            item.replay_references.append(str(payload["replay_reference"]))
        basin = self.store.inspect_session(session_id)["final_basin"]
        stored = self._record_memory_item(session_id, item, basin)
        self._append_event(
            session_id,
            "memory",
            "session.memory.promote",
            {"memory_id": memory_id, "participant": participant, "provenance": provenance, "note": note},
            basin=basin,
        )
        return {"session_id": session_id, "memory_item": stored.to_record()}

    def demote_memory(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        provenance = str(payload.get("provenance", "memory-demote")).strip() or "memory-demote"
        memory_id = str(payload.get("memory_id", "")).strip()
        if not memory_id:
            raise ValueError("memory_id is required")
        item = self._clone_memory_item(session_id, memory_id)
        if not self._visible_to_participant(item, participant):
            raise PermissionError("Requested memory item is not visible to this participant")
        note = str(payload.get("note", "failed-use")).strip() or "failed-use"
        item.failed_uses.append(note)
        if payload.get("contradiction_detail"):
            item.contradiction_status = "contradicted"
            item.contradiction_links.append(
                MemoryContradictionLink(
                    contradiction_id=f"{memory_id}-contradiction-{len(item.contradiction_links) + 1}",
                    detail=str(payload["contradiction_detail"]),
                    provenance=provenance,
                )
            )
        if payload.get("recovery_route_id"):
            item.recovery_links.append(
                MemoryRecoveryLink(
                    route_id=str(payload["recovery_route_id"]),
                    status=str(payload.get("recovery_status", "open")),
                    provenance=provenance,
                )
            )
        basin = self.store.inspect_session(session_id)["final_basin"]
        stored = self._record_memory_item(session_id, item, basin)
        self._append_event(
            session_id,
            "memory",
            "session.memory.demote",
            {"memory_id": memory_id, "participant": participant, "provenance": provenance, "note": note},
            basin=basin,
        )
        return {"session_id": session_id, "memory_item": stored.to_record()}

    def prune_memory(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        provenance = str(payload.get("provenance", "memory-prune")).strip() or "memory-prune"
        memory_id = str(payload.get("memory_id", "")).strip()
        if not memory_id:
            raise ValueError("memory_id is required")
        item = self._clone_memory_item(session_id, memory_id)
        if not self._visible_to_participant(item, participant):
            raise PermissionError("Requested memory item is not visible to this participant")
        legal_hold = self._active_legal_hold(session_id, memory_id)
        if legal_hold:
            self._append_event(
                session_id,
                "memory",
                "session.memory.prune_denied",
                {"memory_id": memory_id, "participant": participant, "provenance": provenance, "reason": "legal_hold"},
                basin=self.store.inspect_session(session_id)["final_basin"],
            )
            return {"session_id": session_id, "allowed": False, "reason": "legal_hold", "memory_id": memory_id}
        if item.visibility_scope == VisibilityScope.AUDIT_RETAINED:
            self._append_event(
                session_id,
                "memory",
                "session.memory.prune_denied",
                {"memory_id": memory_id, "participant": participant, "provenance": provenance, "reason": "audit_retained"},
                basin=self.store.inspect_session(session_id)["final_basin"],
            )
            return {"session_id": session_id, "allowed": False, "reason": "audit_retained", "memory_id": memory_id}
        reason = str(payload.get("reason", "retention-expiry")).strip() or "retention-expiry"
        basin = self.store.inspect_session(session_id)["final_basin"]
        self._append_event(
            session_id,
            "memory",
            "session.memory.prune",
            {"memory_id": memory_id, "participant": participant, "provenance": provenance, "reason": reason},
            basin=basin,
        )
        return {"session_id": session_id, "allowed": True, "memory_id": memory_id, "reason": reason}

    def export_privacy(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        provenance = str(payload.get("provenance", "privacy-export")).strip() or "privacy-export"
        memory_state = self.session_memory(session_id, viewer_participant=participant)
        redacted_items = []
        for item in memory_state["items"]:
            item_copy = deepcopy(item)
            for fragment in item_copy.get("memory_fragments", []):
                text, _ = redact_text(str(fragment.get("text", "")), VisibilityScope.EXPORTABLE_REDACTED)
                fragment["text"] = text
            redacted_items.append(item_copy)
        basin = self.store.inspect_session(session_id)["final_basin"]
        export_payload = {
            "session_id": session_id,
            "viewer_participant": participant,
            "items": redacted_items,
            "deletion_requests": self._privacy_state(session_id)["deletion_requests"],
            "legal_holds": self._privacy_state(session_id)["legal_holds"],
        }
        self._append_event(
            session_id,
            "privacy",
            "session.privacy.export",
            {
                "privacy": {
                    "participant": participant,
                    "provenance": provenance,
                    "item_count": len(redacted_items),
                    "redacted": True,
                }
            },
            basin=basin,
        )
        return export_payload

    def request_deletion(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        provenance = str(payload.get("provenance", "deletion-request")).strip() or "deletion-request"
        reason = str(payload.get("reason", "")).strip()
        if not reason:
            raise ValueError("reason is required")
        request_id = f"deletion-{uuid.uuid4().hex[:10]}"
        record = {
            "privacy": {
                "request_id": request_id,
                "participant": participant,
                "provenance": provenance,
                "reason": reason,
                "target_memory_id": str(payload.get("target_memory_id", "")),
                "status": "PENDING_REVIEW",
            }
        }
        basin = self.store.inspect_session(session_id)["final_basin"]
        self._append_event(session_id, "privacy", "session.privacy.deletion_request", record, basin=basin)
        return {"session_id": session_id, **record["privacy"]}

    def place_legal_hold(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        provenance = str(payload.get("provenance", "legal-hold")).strip() or "legal-hold"
        reason = str(payload.get("reason", "")).strip()
        if not reason:
            raise ValueError("reason is required")
        hold_id = f"hold-{uuid.uuid4().hex[:10]}"
        record = {
            "privacy": {
                "hold_id": hold_id,
                "participant": participant,
                "provenance": provenance,
                "reason": reason,
                "target_memory_id": str(payload.get("target_memory_id", "")),
                "status": "ACTIVE",
            }
        }
        basin = self.store.inspect_session(session_id)["final_basin"]
        self._append_event(session_id, "privacy", "session.privacy.legal_hold", record, basin=basin)
        return {"session_id": session_id, **record["privacy"]}

    def session_memory(self, session_id: str, viewer_participant: str = "UNKNOWN", purpose_override: str | None = None) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        memory_map = self._build_memory_map(session_id)
        viewer = explicit_participant(viewer_participant)
        purpose = str(purpose_override or inspected["metadata"].get("purpose", session_id))
        replay = replay_persisted_session(self.store, session_id)
        visible_items = [
            item.to_record()
            for item in memory_map.items.values()
            if not item.pruned and self._visible_to_participant(item, viewer)
        ]
        retrievals = [
            item.to_record()
            for item in memory_map.retrieve(purpose)
            if item.memory_id in {entry["memory_id"] for entry in visible_items}
        ]
        return {
            "session_id": session_id,
            "viewer_participant": viewer,
            "purpose": purpose,
            "items": visible_items,
            "retrievals": retrievals,
            "replay_receipts": [item.to_record() for item in memory_map.replay_receipts(session_id, replay["replay_hash"])],
            "events": list(memory_map.events),
            "privacy": self._privacy_state(session_id),
        }

    def list_connectors(self) -> List[Dict[str, Any]]:
        return self.connector_registry.list_connectors()

    def get_connector(self, connector_id: str) -> Dict[str, Any]:
        return self.connector_registry.get(connector_id).inventory_record()

    def connector_request(self, connector_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = ConnectorRequest(
            request_id=f"connector-{uuid.uuid4().hex[:12]}",
            session_id=str(payload.get("session_id", "")),
            connector_id=connector_id,
            operation=str(payload.get("operation", "")),
            scope=ConnectorScope(str(payload.get("scope", ConnectorScope.READ_ONLY.value))),
            payload=dict(payload.get("payload", {})),
            replay_key=str(payload.get("replay_key", "")),
            timeout_s=float(payload.get("timeout_s", 5.0)),
            permit_id=str(payload.get("permit_id", "")),
        )
        return self.connector_registry.execute(request).to_record()

    def list_external_actions(self, session_id: str, viewer_participant: str = "UNKNOWN") -> Dict[str, Any]:
        ledger = self._external_action_ledger(session_id)
        actions = []
        for proposal in ledger.proposals.values():
            record = proposal.to_record()
            record["visibility_scope"] = record.get("provenance", {}).get("visibility_scope", VisibilityScope.SHARED_PROJECT.value)
            if not self._external_action_visible(record, viewer_participant):
                continue
            if proposal.permit_id and proposal.permit_id in ledger.permits:
                record["permit"] = ledger.permits[proposal.permit_id].to_record()
            if proposal.proposal_id in ledger.grants:
                record["grant"] = ledger.grants[proposal.proposal_id].to_record()
            if proposal.proposal_id in ledger.denials:
                record["denial"] = ledger.denials[proposal.proposal_id].to_record()
            actions.append(record)
        actions.sort(key=lambda item: item.get("created_at", 0.0))
        return {"session_id": session_id, "viewer_participant": explicit_participant(viewer_participant), "external_actions": actions}

    def get_external_action(self, session_id: str, proposal_id: str, viewer_participant: str = "UNKNOWN") -> Dict[str, Any]:
        for item in self.list_external_actions(session_id, viewer_participant)["external_actions"]:
            if item["proposal_id"] == proposal_id:
                return item
        raise ValueError(f"Unknown external action proposal: {proposal_id}")

    def propose_external_action(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        connector_id = str(payload.get("connector_id", "")).strip()
        operation = str(payload.get("operation", "")).strip()
        target_locator = str(payload.get("target_locator", "")).strip()
        if not connector_id or not operation or not target_locator:
            raise ValueError("connector_id, operation, and target_locator are required")
        target = ActionTarget(
            target_type=str(payload.get("target_type", "resource")).strip() or "resource",
            target_locator=target_locator,
            environment=str(payload.get("environment", "LOCAL")).strip() or "LOCAL",
            metadata=dict(payload.get("target_metadata", {})),
        )
        request_payload = dict(payload.get("payload", {}))
        requirement = self._required_authority_for_operation(connector_id, operation, target.environment)
        proposal = ExternalActionProposal(
            proposal_id=f"proposal-{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            participant=participant,
            system="ephux_local",
            connector_id=connector_id,
            account_label=str(payload.get("account_label", "sanitized-account")).strip() or "sanitized-account",
            operation=operation,
            target=target,
            payload_hash=payload_hash(request_payload),
            payload_preview=request_payload,
            side_effects=[
                SideEffectDeclaration(
                    effect_type=str(payload.get("side_effect", "connector-operation")),
                    description=str(payload.get("side_effect_description", "Connector-governed external operation")),
                    reversible=bool(payload.get("reversible", True)),
                    destructive=bool(payload.get("destructive", False)),
                    cost_impact=str(payload.get("expected_cost", "LOW")),
                )
            ],
            reversible=bool(payload.get("reversible", True)),
            expected_cost=str(payload.get("expected_cost", "LOW")),
            privacy_impact=str(payload.get("privacy_impact", "LOW")),
            security_impact=str(payload.get("security_impact", "LOW")),
            required_authority=requirement,
            verification_plan=VerificationPlan(steps=list(payload.get("verification_steps", ["verify fixture receipt"]))),
            rollback_plan=RollbackPlan(
                steps=list(payload.get("rollback_steps", [])),
                rollback_target=target_locator,
                required=bool(payload.get("rollback_required", requirement.requires_rollback)),
            ),
            expires_at=float(payload.get("expires_at", time.time() + 1800)),
            provenance={"source": "ephux_local", "visibility_scope": str(payload.get("visibility_scope", VisibilityScope.SHARED_PROJECT.value))},
            created_at=time.time(),
        )
        event = self._append_event(
            session_id,
            "external",
            "session.external_action.proposed",
            {"external_action": {"proposal": proposal.to_record()}},
            basin=self.store.inspect_session(session_id).get("final_basin", _default_basin()),
        )
        return {"proposal": proposal.to_record(), "event_id": event["event_id"]}

    def approve_external_action(self, session_id: str, proposal_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        ledger = self._external_action_ledger(session_id)
        if proposal_id not in ledger.proposals:
            raise ValueError("Unknown proposal")
        proposal = ledger.proposals[proposal_id]
        grant, permit = self.authority.issue_permit(
            proposal,
            issued_by_participant=participant,
            note=str(payload.get("note", "approved")).strip() or "approved",
            now=time.time(),
            expires_in_s=float(payload.get("expires_in_s", 1800)),
            single_use=bool(payload.get("single_use", True)),
        )
        self._append_event(
            session_id,
            "external",
            "session.external_action.approved",
            {"external_action": {"grant": grant.to_record(), "permit": permit.to_record()}},
            basin=self.store.inspect_session(session_id).get("final_basin", _default_basin()),
        )
        return {"grant": grant.to_record(), "permit": permit.to_record()}

    def deny_external_action(self, session_id: str, proposal_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        ledger = self._external_action_ledger(session_id)
        if proposal_id not in ledger.proposals:
            raise ValueError("Unknown proposal")
        denial = self.authority.deny_proposal(
            ledger.proposals[proposal_id],
            participant=participant,
            reason=str(payload.get("reason", "denied")).strip() or "denied",
            now=time.time(),
        )
        self._append_event(
            session_id,
            "external",
            "session.external_action.denied",
            {"external_action": {"denial": denial.to_record()}},
            basin=self.store.inspect_session(session_id).get("final_basin", _default_basin()),
        )
        return {"denial": denial.to_record()}

    def revoke_external_action(self, session_id: str, proposal_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant = self._participant_from_payload(payload)
        ledger = self._external_action_ledger(session_id)
        proposal = ledger.proposals.get(proposal_id)
        if proposal is None or not proposal.permit_id or proposal.permit_id not in ledger.permits:
            raise ValueError("No permit exists to revoke")
        permit = ledger.permits[proposal.permit_id]
        revocation = self.authority.revoke_permit(
            permit,
            participant=participant,
            reason=str(payload.get("reason", "revoked")).strip() or "revoked",
            now=time.time(),
        )
        self._append_event(
            session_id,
            "external",
            "session.external_action.revoked",
            {"external_action": {"proposal_id": proposal_id, "revocation": revocation.to_record()}},
            basin=self.store.inspect_session(session_id).get("final_basin", _default_basin()),
        )
        return {"revocation": revocation.to_record()}

    def execute_external_action(self, session_id: str, proposal_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ledger = self._external_action_ledger(session_id)
        proposal = ledger.proposals.get(proposal_id)
        if proposal is None:
            raise ValueError("Unknown proposal")
        if not proposal.permit_id or proposal.permit_id not in ledger.permits:
            raise ValueError("No valid permit exists for execution")
        permit = ledger.permits[proposal.permit_id]
        self.authority.validate_permit(proposal, permit, ledger, now=time.time())
        request = ConnectorRequest(
            request_id=f"external-{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            connector_id=proposal.connector_id,
            operation=proposal.operation,
            scope=ConnectorScope.READ_ONLY if proposal.required_authority.authority == AuthorityClass.READ_ONLY else ConnectorScope.WRITE,
            payload=proposal.payload_preview | dict(payload.get("payload_overrides", {})) | {"fixture_execute": bool(payload.get("fixture_execute", True))},
            replay_key=proposal.proposal_id,
            timeout_s=float(payload.get("timeout_s", 5.0)),
            permit_id=permit.permit_id,
        )
        response = self.connector_registry.execute(request, proposal).to_record()
        receipt = ExecutionReceipt(
            proposal_id=proposal_id,
            connector_id=proposal.connector_id,
            status="EXECUTED" if response["ok"] else "HELD",
            verification_result="FIXTURE_OK" if response["ok"] else "DENIED",
            response_hash=payload_hash(response["body"]),
            timestamp=time.time(),
            permit_id=permit.permit_id,
            redacted_fields=list(response.get("receipt", {}).get("redacted_headers", [])) if response.get("receipt") else [],
            details=response,
        )
        self._append_event(
            session_id,
            "external",
            "session.external_action.executed",
            {"external_action": {"proposal_id": proposal_id, "permit_id": permit.permit_id, "receipt": receipt.to_record()}},
            basin=self.store.inspect_session(session_id).get("final_basin", _default_basin()),
        )
        return {"proposal_id": proposal_id, "permit_id": permit.permit_id, "response": response, "receipt": receipt.to_record()}

    def external_action_receipt(self, session_id: str, proposal_id: str) -> Dict[str, Any]:
        for event in self.store.read_events(session_id):
            if event.get("type") == "session.external_action.executed" and event.get("external_action", {}).get("proposal_id") == proposal_id:
                return event["external_action"]["receipt"]
        raise ValueError("No execution receipt exists for this proposal")

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
        privacy_state = self._privacy_state(session_id)
        claims = [event for event in events if event.get("type") == "session.claim"]
        evidence = [event for event in events if event.get("type") == "session.evidence"]
        holds = [event for event in events if event.get("type") == "session.hold"]
        retracts = [event for event in events if event.get("type") == "session.retract"]
        actions = [event for event in events if event.get("type") == "action"]
        commits = [event for event in events if event.get("type") == "commit"]
        reviews = [event for event in events if event.get("type", "").startswith("session.review.")]
        lab_runs = [event for event in events if event.get("type") in {"session.lab.evaluation", "session.lab.natural_math"}]
        external_actions = self.list_external_actions(session_id)["external_actions"]
        consciousness = self.session_consciousness(session_id)
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
            "privacy_governance": privacy_state,
            "connectors": self.list_connectors(),
            "external_actions": external_actions,
            "consciousness": consciousness,
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
            "connectors": self.list_connectors(),
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
            "session_consciousness_endpoint": "/sessions/{session_id}/consciousness",
            "session_consciousness_workspace_endpoint": "/sessions/{session_id}/consciousness/workspace",
            "session_consciousness_attention_endpoint": "/sessions/{session_id}/consciousness/attention",
            "session_consciousness_self_endpoint": "/sessions/{session_id}/consciousness/self",
            "session_consciousness_continuity_endpoint": "/sessions/{session_id}/consciousness/continuity",
            "session_consciousness_purposes_endpoint": "/sessions/{session_id}/consciousness/purposes",
            "session_consciousness_episodes_endpoint": "/sessions/{session_id}/consciousness/episodes",
            "session_consciousness_episode_detail_endpoint": "/sessions/{session_id}/consciousness/episodes/{episode_id}",
            "session_consciousness_cycle_endpoint": "/sessions/{session_id}/consciousness/cycles",
            "session_consciousness_pause_endpoint": "/sessions/{session_id}/consciousness/pause",
            "session_consciousness_resume_endpoint": "/sessions/{session_id}/consciousness/resume",
            "session_consciousness_percepts_endpoint": "/sessions/{session_id}/consciousness/percepts",
            "session_consciousness_attention_write_endpoint": "/sessions/{session_id}/consciousness/attention",
            "session_consciousness_review_endpoint": "/sessions/{session_id}/consciousness/review",
            "session_world_endpoint": "/sessions/{session_id}/world",
            "session_world_entities_endpoint": "/sessions/{session_id}/world/entities",
            "session_world_events_endpoint": "/sessions/{session_id}/world/events",
            "session_prediction_endpoint": "/sessions/{session_id}/predictions",
            "session_prediction_errors_endpoint": "/sessions/{session_id}/prediction-errors",
            "session_interoception_endpoint": "/sessions/{session_id}/interoception",
            "session_regulation_endpoint": "/sessions/{session_id}/regulation",
            "session_causal_model_endpoint": "/sessions/{session_id}/causal-model",
            "session_perspectives_endpoint": "/sessions/{session_id}/perspectives",
            "session_plans_endpoint": "/sessions/{session_id}/plans",
            "session_rehearsals_endpoint": "/sessions/{session_id}/rehearsals",
            "session_anomalies_endpoint": "/sessions/{session_id}/anomalies",
            "session_calibration_endpoint": "/sessions/{session_id}/calibration",
            "session_world_observations_endpoint": "/sessions/{session_id}/world/observations",
            "session_prediction_write_endpoint": "/sessions/{session_id}/predictions",
            "session_causal_hypothesis_write_endpoint": "/sessions/{session_id}/causal-hypotheses",
            "session_intervention_write_endpoint": "/sessions/{session_id}/interventions",
            "session_perspective_write_endpoint": "/sessions/{session_id}/perspectives",
            "session_plan_write_endpoint": "/sessions/{session_id}/plans",
            "session_rehearsal_write_endpoint": "/sessions/{session_id}/rehearsals",
            "session_world_review_endpoint": "/sessions/{session_id}/world/review",
            "connector_inventory_endpoint": "/connectors",
            "connector_request_endpoint": "/connectors/{connector_id}/requests",
            "session_external_actions_endpoint": "/sessions/{session_id}/external-actions",
            "session_external_action_detail_endpoint": "/sessions/{session_id}/external-actions/{proposal_id}",
            "session_external_action_approve_endpoint": "/sessions/{session_id}/external-actions/{proposal_id}/approve",
            "session_external_action_deny_endpoint": "/sessions/{session_id}/external-actions/{proposal_id}/deny",
            "session_external_action_revoke_endpoint": "/sessions/{session_id}/external-actions/{proposal_id}/revoke",
            "session_external_action_execute_endpoint": "/sessions/{session_id}/external-actions/{proposal_id}/execute",
            "session_external_action_receipt_endpoint": "/sessions/{session_id}/external-actions/{proposal_id}/receipt",
            "session_memory_retrieve_endpoint": "/sessions/{session_id}/memory/retrieve",
            "session_memory_promote_endpoint": "/sessions/{session_id}/memory/promote",
            "session_memory_demote_endpoint": "/sessions/{session_id}/memory/demote",
            "session_memory_prune_endpoint": "/sessions/{session_id}/memory/prune",
            "session_narrative_endpoint": "/sessions/{session_id}/narrative",
            "session_narrative_contributions_endpoint": "/sessions/{session_id}/narrative/contributions",
            "session_narrative_decisions_endpoint": "/sessions/{session_id}/narrative/decisions",
            "session_narrative_disagreements_endpoint": "/sessions/{session_id}/narrative/disagreements",
            "session_narrative_commitments_endpoint": "/sessions/{session_id}/narrative/commitments",
            "session_privacy_export_endpoint": "/sessions/{session_id}/privacy/export",
            "session_privacy_deletion_requests_endpoint": "/sessions/{session_id}/privacy/deletion-requests",
            "session_privacy_legal_holds_endpoint": "/sessions/{session_id}/privacy/legal-holds",
            "evaluation_lab_endpoint": "/sessions/{session_id}/labs/evaluation",
            "natural_math_lab_endpoint": "/sessions/{session_id}/labs/natural-math",
        }

    def ui_html(self) -> str:
        index_path = self.config.ui_asset_dir / "index.html"
        return index_path.read_text(encoding="utf-8")


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any], *, origin: str = "") -> None:
    body = json.dumps(payload, indent=2, default=str).encode("utf-8")
    try:
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        if origin:
            handler.send_header("Access-Control-Allow-Origin", origin)
            handler.send_header("Vary", "Origin")
        handler.end_headers()
        handler.wfile.write(body)
    except OSError:
        return


def _text_response(handler: BaseHTTPRequestHandler, status: int, text: str, *, content_type: str = "text/plain; charset=utf-8", origin: str = "") -> None:
    body = text.encode("utf-8")
    try:
        handler.send_response(status)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(body)))
        if origin:
            handler.send_header("Access-Control-Allow-Origin", origin)
            handler.send_header("Vary", "Origin")
        handler.end_headers()
        handler.wfile.write(body)
    except OSError:
        return


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
                self.rfile.read(length)
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
                if parsed.path == "/connectors":
                    self._authorized()
                    _json_response(self, 200, {"connectors": app.list_connectors()}, origin=origin)
                    return
                if parsed.path.startswith("/connectors/"):
                    self._authorized()
                    connector_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.get_connector(connector_id), origin=origin)
                    return
                if parsed.path == "/sessions":
                    self._authorized()
                    _json_response(self, 200, {"sessions": app.list_sessions()}, origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/external-actions"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    participant = parse_qs(parsed.query).get("participant", ["UNKNOWN"])[0]
                    _json_response(self, 200, app.list_external_actions(session_id, participant), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/receipt") and "/external-actions/" in parsed.path:
                    self._authorized()
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    proposal_id = parts[4]
                    _json_response(self, 200, app.external_action_receipt(session_id, proposal_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and "/external-actions/" in parsed.path:
                    self._authorized()
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    proposal_id = parts[4]
                    participant = parse_qs(parsed.query).get("participant", ["UNKNOWN"])[0]
                    _json_response(self, 200, app.get_external_action(session_id, proposal_id, participant), origin=origin)
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
                    participant = parse_qs(parsed.query).get("participant", ["UNKNOWN"])[0]
                    _json_response(self, 200, app.session_memory(session_id, viewer_participant=participant), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/workspace"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness_workspace(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/attention"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness_attention(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/self"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness_self(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/continuity"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness_continuity(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/purposes"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness_purposes(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/episodes"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_consciousness_episodes(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and "/consciousness/episodes/" in parsed.path:
                    self._authorized()
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    episode_id = parts[5]
                    _json_response(self, 200, app.session_consciousness_episode(session_id, episode_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/world"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_world(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/world/entities"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_world_entities(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/world/events"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_world_events(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/predictions"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_predictions(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/prediction-errors"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_prediction_errors(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/interoception"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_interoception(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/regulation"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_regulation(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/causal-model"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_causal_model(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/perspectives"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_perspectives(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/plans"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_plans(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/rehearsals"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_rehearsals(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/anomalies"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_anomalies(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/calibration"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.session_calibration(session_id), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative"):
                    self._authorized()
                    session_id = parsed.path.split("/")[2]
                    participant = parse_qs(parsed.query).get("participant", ["UNKNOWN"])[0]
                    _json_response(self, 200, app.session_narrative(session_id, viewer_participant=participant), origin=origin)
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
                if parsed.path.startswith("/connectors/") and parsed.path.endswith("/requests"):
                    connector_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.connector_request(connector_id, payload), origin=origin)
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
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/cycles"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.run_consciousness_cycle(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/pause"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.pause_consciousness(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/resume"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.resume_consciousness(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/purposes"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_consciousness_purpose(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/percepts"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_consciousness_percepts(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/attention"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.set_consciousness_attention(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/consciousness/review"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.review_consciousness(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/world/observations"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_world_observations(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/predictions"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_prediction_request(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/causal-hypotheses"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_causal_hypothesis(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/interventions"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_intervention_request(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/perspectives"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_perspective_record(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/plans"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_plan_request(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/rehearsals"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_rehearsal_request(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/world/review"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.review_world(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/review"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.review_session(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/external-actions"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 201, app.propose_external_action(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/approve") and "/external-actions/" in parsed.path:
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    proposal_id = parts[4]
                    payload = self._parse_json()
                    _json_response(self, 200, app.approve_external_action(session_id, proposal_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/deny") and "/external-actions/" in parsed.path:
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    proposal_id = parts[4]
                    payload = self._parse_json()
                    _json_response(self, 200, app.deny_external_action(session_id, proposal_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/revoke") and "/external-actions/" in parsed.path:
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    proposal_id = parts[4]
                    payload = self._parse_json()
                    _json_response(self, 200, app.revoke_external_action(session_id, proposal_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/execute") and "/external-actions/" in parsed.path:
                    parts = parsed.path.split("/")
                    session_id = parts[2]
                    proposal_id = parts[4]
                    payload = self._parse_json()
                    _json_response(self, 200, app.execute_external_action(session_id, proposal_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/memory/retrieve"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.retrieve_memory(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/memory/promote"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.promote_memory(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/memory/demote"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.demote_memory(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/memory/prune"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.prune_memory(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_narrative(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative/contributions"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_narrative_contribution(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative/decisions"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_narrative_decision(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative/disagreements"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_narrative_disagreement(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/narrative/commitments"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.add_narrative_commitment(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/privacy/export"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.export_privacy(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/privacy/deletion-requests"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.request_deletion(session_id, payload), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/privacy/legal-holds"):
                    session_id = parsed.path.split("/")[2]
                    payload = self._parse_json()
                    _json_response(self, 200, app.place_legal_hold(session_id, payload), origin=origin)
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
