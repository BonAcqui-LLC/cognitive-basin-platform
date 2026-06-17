"""
Loopback-only local EphUX / Guardian service backed by BasinLab.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import platform
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
from python.basinlab.memory_map import FractalMemoryMap, MemoryNode
from python.basinlab.providers import CompactReasonerProvider, GeneralistProvider, OpenAICompatibleProvider, ScriptedProvider, VibeThinkerProvider
from python.basinlab.reliability import DecisionClaim, ReliabilityEngine
from python.basinlab.reports import write_report_bundle
from python.basinlab.scars import ScarRegistry
from python.basinlab.session import BasinLabSession, default_store_path, replay_persisted_session
from python.basinlab.spectrum import CandidateTrajectory
from python.basinlab.store import SessionStore
from python.basinlab.team_narrative import NarrativeRecord, TeamNarrative
from python.cognitive_basin.pipeline import run_basin_pipeline

from .contracts import ActivationRecord, IntakeRecord, IntakeState, SanitizationState


MAX_REQUEST_BYTES = 48_000
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".md", ".json"}
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
    return redacted, found


def _bounded_excerpt(text: str, limit: int = 240) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 27] + "...[bounded by EphUX local]"


def _sanitize_filename(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError("Path traversal is not allowed in uploaded file names")
    return Path(name).name


def _provider_inventory() -> List[Dict[str, Any]]:
    hardware = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }
    cache_candidates = {
        "huggingface": Path.home() / ".cache" / "huggingface",
        "ollama": Path.home() / ".ollama" / "models",
        "lm_studio": Path.home() / ".cache" / "lm-studio",
        "gpt4all": Path.home() / "AppData" / "Local" / "nomic.ai",
    }
    caches = {
        name: {
            "path": str(path),
            "exists": path.exists(),
        }
        for name, path in cache_candidates.items()
    }
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
            "available": provider.name == "scripted"
            or (provider.name == "openai-compatible" and bool(os.environ.get("OPENAI_API_KEY")))
            or False,
            "hardware": hardware,
            "model_caches": caches,
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
        self.memory_map = FractalMemoryMap()
        self.team_narrative = TeamNarrative()
        self.team_narrative.update(
            NarrativeRecord(
                person="James Clow",
                contributions=["Cognitive Basin and EphUX architecture lineage"],
                current_purposes=["Local EphUX product integration"],
            )
        )
        self.team_narrative.update(
            NarrativeRecord(
                person="Melissa Clow",
                contributions=["Governance framing and continuity"],
                current_purposes=["Local EphUX product integration"],
            )
        )

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
                "privacy_setting": payload.get("privacy_setting", "local-only"),
                "constraints": payload.get("constraints", []),
            },
        ) as session:
            session_id = str(session.session_id)
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        inspected = self.store.inspect_session(session_id)
        inspected["events"] = self.store.read_events(session_id)
        inspected["report_location"] = str(self.report_dir / session_id / f"{session_id}.html")
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
        self.memory_map.upsert(
            MemoryNode(
                memory_id=evidence_id,
                purpose_links=[self.store.get_session(session_id).metadata.get("purpose", "")],
                evidence_links=[evidence_id],
                survival_reason="local evidence submitted",
                verified_compression_references=[session_id],
            )
        )
        return self.get_session(session_id)

    def add_claim(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
            self._append_event(
                session_id,
                "scar",
                "session.scar",
                {"scar": {"scar_id": scar.scar_id, "claim_id": scar.claim_id, "evidence": scar.contradictory_evidence}},
                basin=basin,
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

    def generate_report(self, session_id: str) -> Dict[str, str]:
        inspected = self.store.inspect_session(session_id)
        events = self.store.read_events(session_id)
        claims = [event for event in events if event.get("type") == "session.claim"]
        evidence = [event for event in events if event.get("type") == "session.evidence"]
        holds = [event for event in events if event.get("type") == "session.hold"]
        retracts = [event for event in events if event.get("type") == "session.retract"]
        actions = [event for event in events if event.get("type") == "action"]
        commits = [event for event in events if event.get("type") == "commit"]
        replay = replay_persisted_session(self.store, session_id)
        report = {
            "scenario": session_id,
            "passed": inspected["final_basin"].get("action") != ActionState.RETRACT.value,
            "purpose": inspected["metadata"].get("purpose", "local ephux session"),
            "plan": [action["result"]["proposal"]["summary"] for action in actions],
            "retrieved_associations": [],
            "candidate_spectrum": {"providers": [provider["name"] for provider in _provider_inventory()]},
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
            "recovery_routes": [],
            "association_updates": [],
            "hold_intervals": [event.get("hold", {}) for event in holds],
            "commit_decisions": [item["decision"] for item in commits],
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
        return {"html_path": str(html_path), "json_path": str(json_path)}

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
            },
        }

    def extension_contract(self) -> Dict[str, Any]:
        return {
            "send_selection_endpoint": "/guardian/intake",
            "activation_endpoint": "/activation",
            "token_header": "X-Ephux-Token",
            "report_url_template": f"http://{self.config.host}:{self.config.port}/sessions/{{session_id}}/report?format=html",
        }

    def ui_html(self) -> str:
        token = html.escape(self.config.token)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>EphUX Local</title>
  <style>
    :root {{
      --paper: #f6f2e7;
      --ink: #1f261b;
      --accent: #315f48;
      --soft: #d8e4d7;
      --warn: #9a5b44;
    }}
    body {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; color: var(--ink); background: radial-gradient(circle at top, #fffdf8, var(--paper)); }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    h1, h2 {{ font-family: 'Palatino Linotype', 'Book Antiqua', serif; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }}
    .card {{ background: rgba(255,255,255,0.74); border: 1px solid #c2cfbe; border-radius: 1rem; padding: 1rem; box-shadow: 0 12px 24px rgba(31,38,27,0.06); }}
    textarea, input {{ width: 100%; box-sizing: border-box; margin-top: 0.5rem; padding: 0.7rem; border-radius: 0.7rem; border: 1px solid #b7c4b2; font-family: inherit; }}
    button {{ margin-top: 0.75rem; background: var(--accent); color: white; border: none; border-radius: 999px; padding: 0.7rem 1rem; font-family: inherit; cursor: pointer; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #fbfcf8; border: 1px solid #d2dccd; padding: 0.75rem; border-radius: 0.75rem; max-height: 360px; overflow: auto; }}
    .status {{ color: var(--warn); font-style: italic; }}
  </style>
</head>
<body>
  <main>
    <h1>EphUX Local Integration</h1>
    <p class="status">Loopback-only development service. Not production-secure.</p>
    <div class="grid">
      <section class="card">
        <h2>Start Session</h2>
        <label>Purpose<input id="purpose" placeholder="What is this session trying to do?"></label>
        <button onclick="startSession()">Create Session</button>
      </section>
      <section class="card">
        <h2>Guardian Intake</h2>
        <label>Session ID<input id="intake-session"></label>
        <label>Text<textarea id="intake-text" rows="8" placeholder="Paste intake text here"></textarea></label>
        <button onclick="sendIntake()">Submit Intake</button>
      </section>
      <section class="card">
        <h2>Activation</h2>
        <label>Purpose<input id="activation-purpose" placeholder="Activation purpose"></label>
        <button onclick="activate()">Start Activation</button>
      </section>
    </div>
    <div class="grid" style="margin-top: 1rem;">
      <section class="card">
        <h2>Current Session</h2>
        <label>Session ID<input id="session-id"></label>
        <button onclick="refreshSession()">Refresh Session</button>
        <button onclick="openReport()">Open Report</button>
      </section>
      <section class="card">
        <h2>Evidence / Contradictions</h2>
        <label>Evidence<textarea id="evidence-text" rows="5" placeholder="Add evidence detail"></textarea></label>
        <button onclick="submitEvidence()">Submit Evidence</button>
        <label>Claim<textarea id="claim-text" rows="5" placeholder="Add a claim or contradiction"></textarea></label>
        <button onclick="submitClaim()">Submit Claim</button>
      </section>
    </div>
    <section class="card" style="margin-top: 1rem;">
      <h2>Session Output</h2>
      <pre id="output">Ready.</pre>
    </section>
  </main>
  <script>
    const TOKEN = "{token}";
    async function api(path, method="GET", body=null, raw=false) {{
      const headers = {{ "X-Ephux-Token": TOKEN }};
      if (body && !raw) headers["Content-Type"] = "application/json";
      const response = await fetch(path, {{
        method,
        headers,
        body: body ? (raw ? body : JSON.stringify(body)) : null
      }});
      const text = await response.text();
      if (!response.ok) throw new Error(text);
      try {{ return JSON.parse(text); }} catch {{ return text; }}
    }}
    function write(data) {{
      document.getElementById("output").textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    }}
    async function startSession() {{
      const purpose = document.getElementById("purpose").value;
      const data = await api("/sessions", "POST", {{ purpose }});
      document.getElementById("session-id").value = data.session_id;
      document.getElementById("intake-session").value = data.session_id;
      write(data);
    }}
    async function sendIntake() {{
      const session_id = document.getElementById("intake-session").value;
      const text = document.getElementById("intake-text").value;
      write(await api("/guardian/intake", "POST", {{ session_id, text }}));
    }}
    async function activate() {{
      const purpose = document.getElementById("activation-purpose").value;
      const data = await api("/activation", "POST", {{ purpose, provider_preference: "scripted" }});
      document.getElementById("session-id").value = data.session_id;
      document.getElementById("intake-session").value = data.session_id;
      write(data);
    }}
    async function refreshSession() {{
      const session_id = document.getElementById("session-id").value;
      write(await api(`/sessions/${{session_id}}`));
    }}
    async function submitEvidence() {{
      const session_id = document.getElementById("session-id").value;
      const detail = document.getElementById("evidence-text").value;
      write(await api(`/sessions/${{session_id}}/evidence`, "POST", {{ detail }}));
    }}
    async function submitClaim() {{
      const session_id = document.getElementById("session-id").value;
      const statement = document.getElementById("claim-text").value;
      const contradictory = statement.toLowerCase().includes("contradiction");
      write(await api(`/sessions/${{session_id}}/claims`, "POST", {{
        statement,
        contradictory_evidence: contradictory ? ["user marked contradiction"] : [],
        supporting_evidence: contradictory ? [] : ["user provided local evidence"]
      }}));
    }}
    async function openReport() {{
      const session_id = document.getElementById("session-id").value;
      window.open(`/sessions/${{session_id}}/report?format=html`, "_blank");
    }}
  </script>
</body>
</html>"""


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
                if parsed.path == "/health":
                    _json_response(self, 200, {"ok": True, "service": "ephux_local"}, origin=origin)
                    return
                if parsed.path == "/capabilities":
                    _json_response(self, 200, app.capabilities(), origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/events"):
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, {"session_id": session_id, "events": app.session_events(session_id)}, origin=origin)
                    return
                if parsed.path.startswith("/sessions/") and parsed.path.endswith("/report"):
                    session_id = parsed.path.split("/")[2]
                    report = app.generate_report(session_id)
                    if parse_qs(parsed.query).get("format") == ["html"]:
                        _text_response(self, 200, Path(report["html_path"]).read_text(encoding="utf-8"), content_type="text/html; charset=utf-8", origin=origin)
                    else:
                        _json_response(self, 200, report, origin=origin)
                    return
                if parsed.path.startswith("/sessions/"):
                    session_id = parsed.path.split("/")[2]
                    _json_response(self, 200, app.get_session(session_id), origin=origin)
                    return
                _json_response(self, 404, {"error": "Not found"}, origin=origin)
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
