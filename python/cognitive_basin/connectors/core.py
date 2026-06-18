"""
Deterministic governed connector adapters and registry.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

from python.cognitive_basin.authority import AuthorityClass, ExternalActionProposal
from python.cognitive_basin.connectors.contracts import (
    ConnectorAvailability,
    ConnectorCapability,
    ConnectorCostClass,
    ConnectorDataClassification,
    ConnectorError,
    ConnectorEvidence,
    ConnectorHealth,
    ConnectorIdentity,
    ConnectorOperation,
    ConnectorPolicy,
    ConnectorRateLimit,
    ConnectorReceipt,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorScope,
    ConnectorSideEffect,
)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sanitize_label(value: str) -> str:
    return value.strip().replace("@", "_at_").replace("/", "_") or "sanitized-account"


def _redact_headers(headers: Dict[str, str]) -> tuple[Dict[str, str], List[str]]:
    redacted = {}
    hidden: List[str] = []
    for key, value in headers.items():
        if key.lower() in {"authorization", "x-api-key", "cookie"}:
            redacted[key] = "[redacted-secret]"
            hidden.append(key)
        else:
            redacted[key] = value
    return redacted, hidden


class Connector:
    def __init__(
        self,
        identity: ConnectorIdentity,
        *,
        capabilities: Iterable[ConnectorCapability],
        policy: ConnectorPolicy,
        health: ConnectorHealth,
        rate_limit: ConnectorRateLimit,
    ) -> None:
        self.identity = identity
        self.capabilities = list(capabilities)
        self.policy = policy
        self.health = health
        self.rate_limit = rate_limit

    def _capability_for(self, operation: str) -> ConnectorCapability:
        for capability in self.capabilities:
            if capability.operation.value == operation:
                return capability
        raise ValueError(f"Unsupported operation for {self.identity.connector_id}: {operation}")

    def inventory_record(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_record(),
            "health": self.health.to_record(),
            "policy": self.policy.to_record(),
            "rate_limit": self.rate_limit.to_record(),
            "capabilities": [capability.to_record() for capability in self.capabilities],
        }

    def execute(self, request: ConnectorRequest, proposal: ExternalActionProposal | None = None) -> ConnectorResponse:
        raise NotImplementedError


class LocalFilesystemConnector(Connector):
    def __init__(self, read_roots: List[Path], write_roots: List[Path]) -> None:
        self.read_roots = [root.resolve() for root in read_roots]
        self.write_roots = [root.resolve() for root in write_roots]
        super().__init__(
            ConnectorIdentity(
                connector_id="local-filesystem",
                connector_type="LOCAL_FILESYSTEM",
                account_label="approved-workspace",
                local_or_remote="LOCAL",
                deployment_state="LOCAL",
            ),
            capabilities=[
                ConnectorCapability(
                    operation=ConnectorOperation.READ_TEXT,
                    scope=ConnectorScope.READ_ONLY,
                    data_classifications=[ConnectorDataClassification.LOCAL_WORKSPACE],
                ),
                ConnectorCapability(
                    operation=ConnectorOperation.WRITE_TEXT,
                    scope=ConnectorScope.WRITE,
                    data_classifications=[ConnectorDataClassification.LOCAL_WORKSPACE],
                    side_effects=[ConnectorSideEffect.LOCAL_FILESYSTEM_WRITE],
                    cost_class=ConnectorCostClass.LOW,
                ),
            ],
            policy=ConnectorPolicy(
                default_authority=AuthorityClass.READ_ONLY,
                verification_method="path-root-and-hash",
                audit_policy="persist-request-receipt",
            ),
            health=ConnectorHealth(
                availability=ConnectorAvailability.AVAILABLE,
                authentication_present=True,
                safe_account_label="approved-workspace",
                checked_at=time.time(),
            ),
            rate_limit=ConnectorRateLimit(requests_per_minute=120, burst=16),
        )

    def _is_reserved_device(self, path_text: str) -> bool:
        first = path_text.replace("\\", "/").split("/")[-1].split(".")[0].upper()
        return os.name == "nt" and first in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}

    def _allowed_root(self, path: Path, roots: List[Path]) -> bool:
        candidate = str(path.resolve())
        for root in roots:
            root_text = str(root.resolve())
            if os.name == "nt":
                if candidate.casefold().startswith(root_text.casefold()):
                    return True
            elif candidate.startswith(root_text):
                return True
        return False

    def _validated_path(self, raw_path: str, *, for_write: bool) -> Path:
        text = str(raw_path or "").strip()
        if not text:
            raise ValueError("Path is required")
        if self._is_reserved_device(text):
            raise ValueError("Reserved device paths are rejected")
        path = Path(text)
        resolved = path.resolve(strict=False)
        roots = self.write_roots if for_write else self.read_roots
        if not self._allowed_root(resolved, roots):
            raise ValueError("Path is outside approved roots")
        if any(token in resolved.name.lower() for token in (".env", "secret", "credential", "token")):
            raise ValueError("Credential locations are rejected")
        return resolved

    def execute(self, request: ConnectorRequest, proposal: ExternalActionProposal | None = None) -> ConnectorResponse:
        capability = self._capability_for(request.operation)
        if request.operation == ConnectorOperation.READ_TEXT.value:
            path = self._validated_path(str(request.payload.get("path", "")), for_write=False)
            limit = int(request.payload.get("max_bytes", 4096))
            text = path.read_text(encoding="utf-8")
            if len(text.encode("utf-8")) > limit:
                raise ValueError("Bounded read exceeded")
            excerpt = text[: min(240, len(text))]
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="READ_OK",
                timestamp=time.time(),
                evidence=[ConnectorEvidence("file_sha256", path.name, _hash_text(text))],
            )
            return ConnectorResponse(
                ok=True,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                body={"path": str(path), "excerpt": excerpt, "sha256": _hash_text(text), "bytes": len(text.encode("utf-8"))},
                receipt=receipt,
            )
        if request.operation == ConnectorOperation.WRITE_TEXT.value:
            if not request.permit_id:
                raise ValueError("Local filesystem writes require an exact permit")
            path = self._validated_path(str(request.payload.get("path", "")), for_write=True)
            content = str(request.payload.get("content", ""))
            if len(content.encode("utf-8")) > int(request.payload.get("max_bytes", 4096)):
                raise ValueError("Bounded write exceeded")
            temp_path = path.with_suffix(path.suffix + ".tmp")
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(path)
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="WRITE_OK",
                timestamp=time.time(),
                permit_id=request.permit_id,
                evidence=[ConnectorEvidence("file_sha256", path.name, _hash_text(content))],
            )
            return ConnectorResponse(
                ok=True,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                body={"path": str(path), "sha256": _hash_text(content), "bytes": len(content.encode("utf-8"))},
                receipt=receipt,
            )
        raise ValueError(f"Unsupported local filesystem operation: {request.operation}")


class FixtureConnector(Connector):
    def __init__(
        self,
        connector_id: str,
        connector_type: str,
        account_label: str,
        *,
        local_or_remote: str,
        deployment_state: str,
        capabilities: Iterable[ConnectorCapability],
        fixture_responses: Dict[str, Dict[str, Any]],
        rate_limit: ConnectorRateLimit,
        no_live_writes: bool = True,
        availability: ConnectorAvailability = ConnectorAvailability.FIXTURE_ONLY,
        auth_present: bool = False,
    ) -> None:
        self.fixture_responses = fixture_responses
        super().__init__(
            ConnectorIdentity(
                connector_id=connector_id,
                connector_type=connector_type,
                account_label=account_label,
                local_or_remote=local_or_remote,
                deployment_state=deployment_state,
            ),
            capabilities=list(capabilities),
            policy=ConnectorPolicy(
                default_authority=AuthorityClass.READ_ONLY,
                verification_method="fixture-receipt",
                audit_policy="persist-request-receipt",
                no_live_writes=no_live_writes,
            ),
            health=ConnectorHealth(
                availability=availability,
                authentication_present=auth_present,
                safe_account_label=account_label,
                checked_at=time.time(),
            ),
            rate_limit=rate_limit,
        )

    def execute(self, request: ConnectorRequest, proposal: ExternalActionProposal | None = None) -> ConnectorResponse:
        if self.health.availability == ConnectorAvailability.UNAVAILABLE:
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="UNAVAILABLE",
                timestamp=time.time(),
                error=ConnectorError("unavailable", "Connector unavailable", retryable=True),
            )
            return ConnectorResponse(False, self.identity.connector_id, request.operation, receipt=receipt, error=receipt.error)
        if request.payload.get("simulate_rate_limit"):
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="RATE_LIMITED",
                timestamp=time.time(),
                error=ConnectorError("rate_limit", "Connector rate limited", retryable=True),
            )
            return ConnectorResponse(False, self.identity.connector_id, request.operation, receipt=receipt, error=receipt.error)
        if request.payload.get("simulate_timeout"):
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="TIMEOUT",
                timestamp=time.time(),
                error=ConnectorError("timeout", "Connector timed out", retryable=True),
            )
            return ConnectorResponse(False, self.identity.connector_id, request.operation, receipt=receipt, error=receipt.error)
        capability = self._capability_for(request.operation)
        if capability.scope == ConnectorScope.WRITE and not request.permit_id:
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="WRITE_HELD",
                timestamp=time.time(),
                error=ConnectorError("write_held", "Write operation requires an exact permit", retryable=False),
            )
            return ConnectorResponse(False, self.identity.connector_id, request.operation, receipt=receipt, error=receipt.error)
        if capability.scope == ConnectorScope.WRITE and self.policy.no_live_writes and not request.payload.get("fixture_execute"):
            receipt = ConnectorReceipt(
                request_id=request.request_id,
                connector_id=self.identity.connector_id,
                operation=request.operation,
                status="WRITE_HELD",
                timestamp=time.time(),
                error=ConnectorError("write_held", "Write operation requires permit and fixture execution flag", retryable=False),
            )
            return ConnectorResponse(False, self.identity.connector_id, request.operation, receipt=receipt, error=receipt.error)
        record = dict(self.fixture_responses.get(request.operation, {"fixture": True, "connector_id": self.identity.connector_id}))
        headers, hidden = _redact_headers(dict(request.payload.get("headers", {})))
        record["headers"] = headers
        record["fixture_mode"] = True
        receipt = ConnectorReceipt(
            request_id=request.request_id,
            connector_id=self.identity.connector_id,
            operation=request.operation,
            status="FIXTURE_OK",
            timestamp=time.time(),
            permit_id=request.permit_id,
            evidence=[ConnectorEvidence("fixture", self.identity.connector_id, _hash_text(_canonical_json(record)))],
            redacted_headers=hidden,
        )
        return ConnectorResponse(True, self.identity.connector_id, request.operation, body=record, receipt=receipt)


class GenericHTTPConnector(FixtureConnector):
    def __init__(self) -> None:
        super().__init__(
            "generic-http",
            "GENERIC_HTTP",
            "allowlisted-hosts",
            local_or_remote="REMOTE",
            deployment_state="LOCAL_POLICY_ONLY",
            capabilities=[
                ConnectorCapability(
                    operation=ConnectorOperation.HTTP_GET,
                    scope=ConnectorScope.READ_ONLY,
                    data_classifications=[ConnectorDataClassification.NETWORK_METADATA],
                    side_effects=[ConnectorSideEffect.NETWORK_IO],
                ),
                ConnectorCapability(
                    operation=ConnectorOperation.HTTP_WRITE,
                    scope=ConnectorScope.WRITE,
                    data_classifications=[ConnectorDataClassification.NETWORK_METADATA],
                    side_effects=[ConnectorSideEffect.NETWORK_IO],
                ),
            ],
            fixture_responses={
                ConnectorOperation.HTTP_GET.value: {"status": 200, "content_type": "application/json", "body": {"ok": True}},
                ConnectorOperation.HTTP_WRITE.value: {"status": 202, "accepted": True},
            },
            rate_limit=ConnectorRateLimit(requests_per_minute=30, burst=4),
        )
        self.allowed_schemes = {"https"}
        self.allowed_hosts = {"status.project.local", "preview.project.local"}

    def execute(self, request: ConnectorRequest, proposal: ExternalActionProposal | None = None) -> ConnectorResponse:
        parsed = urlparse(str(request.payload.get("url", "")))
        if parsed.scheme not in self.allowed_schemes:
            raise ValueError("HTTP scheme is not allowlisted")
        if parsed.hostname not in self.allowed_hosts:
            raise ValueError("HTTP host is not allowlisted")
        if parsed.hostname and parsed.hostname.startswith(("127.", "10.", "192.168.")):
            raise ValueError("Private-address targets are blocked")
        return super().execute(request, proposal)


class ConnectorRegistry:
    def __init__(self, connectors: Iterable[Connector]) -> None:
        self._connectors = {connector.identity.connector_id: connector for connector in connectors}

    def list_connectors(self) -> List[Dict[str, Any]]:
        return [connector.inventory_record() for connector in self._connectors.values()]

    def get(self, connector_id: str) -> Connector:
        if connector_id not in self._connectors:
            raise ValueError(f"Unknown connector: {connector_id}")
        return self._connectors[connector_id]

    def execute(self, request: ConnectorRequest, proposal: ExternalActionProposal | None = None) -> ConnectorResponse:
        return self.get(request.connector_id).execute(request, proposal)


def build_default_registry(workspace_root: Path) -> ConnectorRegistry:
    filesystem = LocalFilesystemConnector(
        read_roots=[workspace_root, workspace_root / "apps", workspace_root / "python"],
        write_roots=[workspace_root / "build", workspace_root / "ops", workspace_root / "evidence"],
    )
    github = FixtureConnector(
        "github",
        "GITHUB",
        "BonAcqui-LLC_cognitive-basin-platform",
        local_or_remote="REMOTE",
        deployment_state="PRIVATE_REPOSITORY",
        capabilities=[
            ConnectorCapability(ConnectorOperation.REPOSITORY_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.BRANCH_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.PULL_REQUEST_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.WORKFLOW_RUN_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.ISSUE_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.COMMIT_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.BRANCH_PUSH, ConnectorScope.WRITE, side_effects=[ConnectorSideEffect.REPOSITORY_MUTATION]),
        ],
        fixture_responses={
            ConnectorOperation.REPOSITORY_METADATA.value: {"name": "cognitive-basin-platform", "default_branch": "main"},
            ConnectorOperation.BRANCH_METADATA.value: {"branch": "main", "protected": True},
            ConnectorOperation.PULL_REQUEST_METADATA.value: {"number": 8, "state": "merged"},
            ConnectorOperation.WORKFLOW_RUN_METADATA.value: {"run_id": 27739749185, "status": "success"},
            ConnectorOperation.ISSUE_METADATA.value: {"number": 1, "title": "fixture issue"},
            ConnectorOperation.COMMIT_METADATA.value: {"sha": "0cbdfa0a7bd99f59f1e48ad9edce08493fa3fe8c"},
            ConnectorOperation.BRANCH_PUSH.value: {"branch": "build/fixture", "executed": True},
        },
        rate_limit=ConnectorRateLimit(requests_per_minute=60, burst=8),
        auth_present=True,
    )
    cloudflare = FixtureConnector(
        "cloudflare",
        "CLOUDFLARE",
        "prototype-account",
        local_or_remote="REMOTE",
        deployment_state="PREVIEW_ARCHITECTURE_ONLY",
        capabilities=[
            ConnectorCapability(ConnectorOperation.WORKER_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.DEPLOYMENT_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.DNS_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.D1_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.KV_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.R2_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.DURABLE_OBJECT_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.QUEUE_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.PAGES_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
            ConnectorCapability(ConnectorOperation.EMAIL_ROUTING_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PROJECT_METADATA]),
        ],
        fixture_responses={
            ConnectorOperation.WORKER_METADATA.value: {
                "current_observed_live_prototype": "loopback ephux local",
                "local_implementation": "python.ephux_local.service",
                "proposed_preview_architecture": "worker+durable-object+d1+r2",
                "proposed_production_architecture": "not authorized in tranche",
            },
            ConnectorOperation.DEPLOYMENT_METADATA.value: {"scripts": ["ephux-preview"], "live_write_enabled": False},
            ConnectorOperation.DNS_METADATA.value: {"zones": ["example.invalid"], "live_write_enabled": False},
            ConnectorOperation.D1_METADATA.value: {"databases": ["preview_state"], "live_write_enabled": False},
            ConnectorOperation.KV_METADATA.value: {"namespaces": ["preview_config"], "live_write_enabled": False},
            ConnectorOperation.R2_METADATA.value: {"buckets": ["preview-artifacts"], "live_write_enabled": False},
            ConnectorOperation.DURABLE_OBJECT_METADATA.value: {"classes": ["SessionCoordinator"], "live_write_enabled": False},
            ConnectorOperation.QUEUE_METADATA.value: {"queues": ["audit-events"], "live_write_enabled": False},
            ConnectorOperation.PAGES_METADATA.value: {"projects": ["ephux-local-ui"], "live_write_enabled": False},
            ConnectorOperation.EMAIL_ROUTING_METADATA.value: {"routes": ["support@example.invalid"], "live_write_enabled": False},
        },
        rate_limit=ConnectorRateLimit(requests_per_minute=40, burst=4),
    )
    gmail = FixtureConnector(
        "gmail",
        "GMAIL",
        "project-scoped-mailbox",
        local_or_remote="REMOTE",
        deployment_state="READ_ONLY",
        capabilities=[ConnectorCapability(ConnectorOperation.GMAIL_PROJECT_SEARCH, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PRIVATE_PROJECT])],
        fixture_responses={ConnectorOperation.GMAIL_PROJECT_SEARCH.value: {"matches": [{"thread_id": "t-1", "subject": "Cognitive Basin project sync"}]}},
        rate_limit=ConnectorRateLimit(requests_per_minute=20, burst=3),
    )
    calendar = FixtureConnector(
        "google-calendar",
        "GOOGLE_CALENDAR",
        "project-calendar",
        local_or_remote="REMOTE",
        deployment_state="READ_ONLY",
        capabilities=[ConnectorCapability(ConnectorOperation.CALENDAR_PROJECT_EVENTS, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PRIVATE_PROJECT])],
        fixture_responses={ConnectorOperation.CALENDAR_PROJECT_EVENTS.value: {"events": [{"id": "evt-1", "summary": "Connector review"}]}},
        rate_limit=ConnectorRateLimit(requests_per_minute=20, burst=3),
    )
    drive = FixtureConnector(
        "google-drive",
        "GOOGLE_DRIVE",
        "project-drive",
        local_or_remote="REMOTE",
        deployment_state="READ_ONLY",
        capabilities=[ConnectorCapability(ConnectorOperation.DRIVE_PROJECT_DOCUMENTS, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PRIVATE_PROJECT])],
        fixture_responses={ConnectorOperation.DRIVE_PROJECT_DOCUMENTS.value: {"documents": [{"id": "doc-1", "title": "Connector tranche"}]}},
        rate_limit=ConnectorRateLimit(requests_per_minute=20, burst=3),
    )
    contacts = FixtureConnector(
        "google-contacts",
        "GOOGLE_CONTACTS",
        "account-profile",
        local_or_remote="REMOTE",
        deployment_state="READ_ONLY",
        capabilities=[ConnectorCapability(ConnectorOperation.CONTACTS_ACCOUNT_PROFILE, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.PRIVATE_ACCOUNT])],
        fixture_responses={ConnectorOperation.CONTACTS_ACCOUNT_PROFILE.value: {"profile": {"displayName": "Project Contact", "domain": "example.invalid"}}},
        rate_limit=ConnectorRateLimit(requests_per_minute=20, burst=3),
    )
    chrome = FixtureConnector(
        "chrome-extension",
        "CHROME_EXTENSION",
        "local-browser",
        local_or_remote="LOCAL",
        deployment_state="LOCAL",
        capabilities=[ConnectorCapability(ConnectorOperation.CHROME_EXTENSION_LOCAL_REQUEST, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.LOCAL_WORKSPACE])],
        fixture_responses={ConnectorOperation.CHROME_EXTENSION_LOCAL_REQUEST.value: {"extension_state": "ready", "loopback_only": True}},
        rate_limit=ConnectorRateLimit(requests_per_minute=120, burst=12),
        availability=ConnectorAvailability.AVAILABLE,
        auth_present=True,
    )
    stripe = FixtureConnector(
        "stripe",
        "STRIPE",
        "billing-account",
        local_or_remote="REMOTE",
        deployment_state="READ_ONLY",
        capabilities=[ConnectorCapability(ConnectorOperation.STRIPE_ACCOUNT_METADATA, ConnectorScope.READ_ONLY, data_classifications=[ConnectorDataClassification.BILLING_SENSITIVE], cost_class=ConnectorCostClass.BILLING_SENSITIVE)],
        fixture_responses={ConnectorOperation.STRIPE_ACCOUNT_METADATA.value: {"country": "US", "charges_enabled": False, "payouts_enabled": False}},
        rate_limit=ConnectorRateLimit(requests_per_minute=12, burst=2),
    )
    return ConnectorRegistry([filesystem, github, cloudflare, gmail, calendar, drive, contacts, chrome, stripe, GenericHTTPConnector()])
