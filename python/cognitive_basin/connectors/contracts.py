"""
Typed connector-layer contracts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Dict, List

from python.cognitive_basin.authority import AuthorityClass


class ConnectorAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    FIXTURE_ONLY = "FIXTURE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"


class ConnectorScope(StrEnum):
    READ_ONLY = "READ_ONLY"
    WRITE = "WRITE"


class ConnectorSideEffect(StrEnum):
    NONE = "NONE"
    LOCAL_FILESYSTEM_WRITE = "LOCAL_FILESYSTEM_WRITE"
    REPOSITORY_MUTATION = "REPOSITORY_MUTATION"
    DEPLOYMENT_CHANGE = "DEPLOYMENT_CHANGE"
    DNS_CHANGE = "DNS_CHANGE"
    BILLING_CHANGE = "BILLING_CHANGE"
    SECRET_CHANGE = "SECRET_CHANGE"
    NETWORK_IO = "NETWORK_IO"


class ConnectorOperation(StrEnum):
    READ_TEXT = "READ_TEXT"
    WRITE_TEXT = "WRITE_TEXT"
    REPOSITORY_METADATA = "REPOSITORY_METADATA"
    BRANCH_METADATA = "BRANCH_METADATA"
    BRANCH_PUSH = "BRANCH_PUSH"
    PULL_REQUEST_METADATA = "PULL_REQUEST_METADATA"
    WORKFLOW_RUN_METADATA = "WORKFLOW_RUN_METADATA"
    ISSUE_METADATA = "ISSUE_METADATA"
    COMMIT_METADATA = "COMMIT_METADATA"
    WORKER_METADATA = "WORKER_METADATA"
    DEPLOYMENT_METADATA = "DEPLOYMENT_METADATA"
    DNS_METADATA = "DNS_METADATA"
    D1_METADATA = "D1_METADATA"
    KV_METADATA = "KV_METADATA"
    R2_METADATA = "R2_METADATA"
    DURABLE_OBJECT_METADATA = "DURABLE_OBJECT_METADATA"
    QUEUE_METADATA = "QUEUE_METADATA"
    PAGES_METADATA = "PAGES_METADATA"
    EMAIL_ROUTING_METADATA = "EMAIL_ROUTING_METADATA"
    GMAIL_PROJECT_SEARCH = "GMAIL_PROJECT_SEARCH"
    CALENDAR_PROJECT_EVENTS = "CALENDAR_PROJECT_EVENTS"
    DRIVE_PROJECT_DOCUMENTS = "DRIVE_PROJECT_DOCUMENTS"
    CONTACTS_ACCOUNT_PROFILE = "CONTACTS_ACCOUNT_PROFILE"
    STRIPE_ACCOUNT_METADATA = "STRIPE_ACCOUNT_METADATA"
    CHROME_EXTENSION_LOCAL_REQUEST = "CHROME_EXTENSION_LOCAL_REQUEST"
    HTTP_GET = "HTTP_GET"
    HTTP_WRITE = "HTTP_WRITE"


class ConnectorCostClass(StrEnum):
    FREE = "FREE"
    LOW = "LOW"
    METERED = "METERED"
    BILLING_SENSITIVE = "BILLING_SENSITIVE"


class ConnectorDataClassification(StrEnum):
    LOCAL_WORKSPACE = "LOCAL_WORKSPACE"
    PROJECT_METADATA = "PROJECT_METADATA"
    PRIVATE_ACCOUNT = "PRIVATE_ACCOUNT"
    PRIVATE_PROJECT = "PRIVATE_PROJECT"
    BILLING_SENSITIVE = "BILLING_SENSITIVE"
    NETWORK_METADATA = "NETWORK_METADATA"


@dataclass
class ConnectorRateLimit:
    requests_per_minute: int
    burst: int
    behavior_on_limit: str = "HOLD"

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectorIdentity:
    connector_id: str
    connector_type: str
    account_label: str
    local_or_remote: str
    deployment_state: str

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectorCapability:
    operation: ConnectorOperation
    scope: ConnectorScope
    required_scopes: List[str] = field(default_factory=list)
    data_classifications: List[ConnectorDataClassification] = field(default_factory=list)
    side_effects: List[ConnectorSideEffect] = field(default_factory=list)
    reversibility: str = "REVERSIBLE"
    cost_class: ConnectorCostClass = ConnectorCostClass.FREE

    def to_record(self) -> Dict[str, Any]:
        return {
            "operation": self.operation.value,
            "scope": self.scope.value,
            "required_scopes": list(self.required_scopes),
            "data_classifications": [item.value for item in self.data_classifications],
            "side_effects": [item.value for item in self.side_effects],
            "reversibility": self.reversibility,
            "cost_class": self.cost_class.value,
        }


@dataclass
class ConnectorPolicy:
    default_authority: AuthorityClass
    verification_method: str
    audit_policy: str
    no_live_writes: bool = False

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["default_authority"] = self.default_authority.value
        return payload


@dataclass
class ConnectorHealth:
    availability: ConnectorAvailability
    authentication_present: bool
    safe_account_label: str
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: float = 0.0

    def to_record(self) -> Dict[str, Any]:
        return {
            "availability": self.availability.value,
            "authentication_present": self.authentication_present,
            "safe_account_label": self.safe_account_label,
            "details": dict(self.details),
            "checked_at": self.checked_at,
        }


@dataclass
class ConnectorEvidence:
    evidence_type: str
    summary: str
    content_hash: str

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectorError:
    error_class: str
    message: str
    retryable: bool = False

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectorReceipt:
    request_id: str
    connector_id: str
    operation: str
    status: str
    timestamp: float
    permit_id: str = ""
    evidence: List[ConnectorEvidence] = field(default_factory=list)
    redacted_headers: List[str] = field(default_factory=list)
    error: ConnectorError | None = None

    def to_record(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "operation": self.operation,
            "status": self.status,
            "timestamp": self.timestamp,
            "permit_id": self.permit_id,
            "evidence": [item.to_record() for item in self.evidence],
            "redacted_headers": list(self.redacted_headers),
            "error": self.error.to_record() if self.error else None,
        }


@dataclass
class ConnectorRequest:
    request_id: str
    session_id: str
    connector_id: str
    operation: str
    scope: ConnectorScope
    payload: Dict[str, Any] = field(default_factory=dict)
    replay_key: str = ""
    timeout_s: float = 5.0
    permit_id: str = ""

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["scope"] = self.scope.value
        return payload


@dataclass
class ConnectorResponse:
    ok: bool
    connector_id: str
    operation: str
    body: Dict[str, Any] = field(default_factory=dict)
    receipt: ConnectorReceipt | None = None
    error: ConnectorError | None = None

    def to_record(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "connector_id": self.connector_id,
            "operation": self.operation,
            "body": dict(self.body),
            "receipt": self.receipt.to_record() if self.receipt else None,
            "error": self.error.to_record() if self.error else None,
        }
