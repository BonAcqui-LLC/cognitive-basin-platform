"""
Typed provider-layer contracts for governed routing, ledgering, and bounded
reasoning adapters.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProviderCapabilities:
    supports_text_generation: bool = True
    supports_structured_output: bool = True
    supports_embeddings: bool = False
    supports_retrieval: bool = False
    local: bool = False
    remote: bool = True
    reachable: bool = False
    can_execute: bool = False
    can_commit: bool = False
    can_use_tools: bool = False
    can_use_connectors: bool = False
    privacy_tier: str = "unknown"
    verification_modes: List[str] = field(default_factory=list)
    latency_tier: str = "unknown"
    budget_tier: str = "unknown"

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderRequest:
    invocation_id: str
    session_id: str
    role: str
    task_domain: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    context_requirement: str = "bounded"
    privacy_requirement: str = "private"
    expected_verification: str = "deterministic"
    local_only: bool = False
    existing_allowance_only: bool = True
    budget_limit_usd: Optional[float] = None
    expected_latency_ms: Optional[int] = None
    candidate_count: int = 1
    claims_requested: List[str] = field(default_factory=list)
    prohibited_assumptions: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    user_preference: str = ""
    model_preference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderUsage:
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    retries: int = 0
    elapsed_ms: int = 0
    reported_cost_usd: Optional[float] = None
    estimated_cost_usd: Optional[float] = None
    allowance_classification: str = "existing-allowance-only"
    privacy_classification: str = "private"

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderError:
    error_class: str
    message: str
    retryable: bool = False

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderPolicy:
    budget_policy: str = "existing-allowance-only"
    explicit_ceiling_usd: Optional[float] = None
    allow_remote: bool = False
    allow_live_calls: bool = False
    approval_required: bool = False
    required_privacy: str = "private"
    required_verification: str = "deterministic"
    allowed_roles: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderRoute:
    provider_name: str
    model: str
    role: str
    route_reason: str
    local_or_remote: str
    policy: ProviderPolicy
    availability_state: str
    latency_tier: str
    budget_tier: str

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["policy"] = self.policy.to_record()
        return payload


@dataclass
class ProviderReceipt:
    invocation_id: str
    session_id: str
    provider: str
    model: str
    role: str
    request_hash: str
    response_hash: str
    timestamp: float
    usage: ProviderUsage
    route: ProviderRoute
    error: Optional[ProviderError] = None
    claims_affected: List[str] = field(default_factory=list)
    evidence_produced: List[str] = field(default_factory=list)
    deterministic_verification_result: str = "UNVERIFIED"
    final_disposition: str = "RECORDED"

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["usage"] = self.usage.to_record()
        payload["route"] = self.route.to_record()
        payload["error"] = self.error.to_record() if self.error else None
        return payload


@dataclass
class ProviderResponse:
    provider: str
    model: str
    role: str
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    claims: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    receipt: Optional[ProviderReceipt] = None
    error: Optional[ProviderError] = None

    def to_record(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "role": self.role,
            "outputs": list(self.outputs),
            "claims": list(self.claims),
            "evidence": list(self.evidence),
            "usage": self.usage.to_record(),
            "receipt": self.receipt.to_record() if self.receipt else None,
            "error": self.error.to_record() if self.error else None,
        }


@dataclass
class ProblemPacket:
    exact_problem: str
    supplied_context: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    answer_schema: Dict[str, Any] = field(default_factory=dict)
    verification_method: str = "deterministic"
    candidate_count: int = 1
    claims_requested: List[str] = field(default_factory=list)
    prohibited_assumptions: List[str] = field(default_factory=list)
    no_tool_declaration: bool = True

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateReasoningPacket:
    candidate_answer: str
    operational_rationale: str
    decision_claims: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    proposed_checks: List[str] = field(default_factory=list)
    uncertainty: str = ""
    no_action_request: bool = True

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)
