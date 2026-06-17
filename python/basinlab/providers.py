"""
Governed provider adapters for BasinLab spectrum generation and provider lab
integration.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol

from python.provider_lab import (
    CandidateReasoningPacket,
    FixtureProvider,
    ProblemPacket,
    ProviderCapabilities,
    ProviderError,
    ProviderPolicy,
    ProviderReceipt,
    ProviderRequest,
    ProviderResponse,
    ProviderRoute,
    ProviderUsage,
    ROLE_COMPACT_REASONER,
    ROLE_GENERALIST,
    UnavailableProvider,
    compact_reasoner_packet,
    new_invocation_id,
    stable_hash,
)


@dataclass
class ProviderCallRecord:
    provider: str
    model: str
    duration_s: float
    input_hash: str
    output_hash: str
    verified: bool
    error: str = ""
    token_count: int = 0
    receipt: Dict[str, Any] = field(default_factory=dict)


class Provider(Protocol):
    name: str
    model: str
    can_execute: bool
    can_commit: bool

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        ...


def _call_record_from_response(response: ProviderResponse, request: ProviderRequest) -> ProviderCallRecord:
    receipt = response.receipt.to_record() if response.receipt else {}
    return ProviderCallRecord(
        provider=response.provider,
        model=response.model,
        duration_s=response.usage.elapsed_ms / 1000.0,
        input_hash=stable_hash(request.to_record()),
        output_hash=receipt.get("response_hash", ""),
        verified=bool(response.receipt and response.receipt.deterministic_verification_result.endswith("VERIFIED")),
        error=response.error.error_class if response.error else "",
        token_count=(response.usage.input_tokens or 0) + (response.usage.output_tokens or 0),
        receipt=receipt,
    )


@dataclass
class ScriptedProvider(FixtureProvider):
    name: str = "scripted"
    model: str = "scripted-deterministic"
    scripted_outputs: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        FixtureProvider.__init__(
            self,
            self.name,
            model=self.model,
            scripted_outputs=self.scripted_outputs,
            capabilities=ProviderCapabilities(
                supports_text_generation=True,
                supports_structured_output=True,
                local=True,
                remote=False,
                reachable=True,
                can_execute=False,
                can_commit=False,
                can_use_tools=False,
                can_use_connectors=False,
                privacy_tier="private",
                verification_modes=["deterministic", "fixture"],
                latency_tier="low",
                budget_tier="zero-cost",
            ),
        )

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        request = ProviderRequest(
            invocation_id=new_invocation_id("scripted"),
            session_id=context.get("session_id", "spectrum"),
            role=context.get("role", ROLE_GENERALIST),
            task_domain=context.get("task_domain", purpose),
            prompt=purpose,
            context=context,
            existing_allowance_only=True,
            local_only=True,
            candidate_count=max(1, len(self.scripted_outputs) or 1),
        )
        route = ProviderRoute(
            provider_name=self.name,
            model=self.model,
            role=request.role,
            route_reason="scripted deterministic fixture",
            local_or_remote="local",
            policy=ProviderPolicy(budget_policy="zero-cost-only", allow_remote=False, allow_live_calls=False),
            availability_state="reachable",
            latency_tier="low",
            budget_tier="zero-cost",
        )
        response = self.invoke(request, route)
        return response.outputs, _call_record_from_response(response, request)


@dataclass
class GeneralistProvider(ScriptedProvider):
    name: str = "generalist"


@dataclass
class CompactReasonerProvider(ScriptedProvider):
    name: str = "compact-reasoner"

    def invoke(self, request: ProviderRequest, route: ProviderRoute) -> ProviderResponse:
        raw = super().invoke(request, route)
        constrained_outputs = []
        for output in raw.outputs:
            packet = compact_reasoner_packet(
                ProblemPacket(
                    exact_problem=request.prompt,
                    supplied_context=request.context,
                    constraints=list(request.metadata.get("constraints", [])),
                    answer_schema={"type": "candidate_reasoning_packet"},
                    verification_method=request.expected_verification,
                    candidate_count=request.candidate_count,
                    claims_requested=list(request.claims_requested),
                    prohibited_assumptions=list(request.prohibited_assumptions),
                    no_tool_declaration=True,
                ),
                CandidateReasoningPacket(
                    candidate_answer=output.get("answer", ""),
                    operational_rationale=output.get("reasoning", ""),
                    decision_claims=list(output.get("decision_claims", [])),
                    assumptions=[item.get("text", item) if isinstance(item, dict) else str(item) for item in output.get("assumptions", [])],
                    proposed_checks=[item.get("text", item) if isinstance(item, dict) else str(item) for item in output.get("predictions", [])],
                    uncertainty=output.get("uncertainty", ""),
                    no_action_request=True,
                ),
            )
            constrained_outputs.append(
                {
                    **output,
                    "problem_packet": packet["problem_packet"],
                    "candidate_reasoning_packet": packet["candidate_reasoning_packet"],
                }
            )
        raw.outputs = constrained_outputs
        if raw.receipt:
            raw.receipt.evidence_produced.append("bounded-problem-packet")
        return raw


@dataclass
class OpenAICompatibleProvider:
    name: str = "openai-compatible"
    model: str = "unconfigured"
    base_url: str = ""
    reachable: bool = False

    @property
    def can_execute(self) -> bool:
        return False

    @property
    def can_commit(self) -> bool:
        return False

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities()

    def _capabilities(self) -> ProviderCapabilities:
        is_local = self.base_url.startswith("http://127.0.0.1") or self.base_url.startswith("http://localhost")
        return ProviderCapabilities(
            supports_text_generation=True,
            supports_structured_output=True,
            local=is_local,
            remote=not is_local,
            reachable=self.reachable,
            can_execute=False,
            can_commit=False,
            can_use_tools=False,
            can_use_connectors=False,
            privacy_tier="private" if is_local else "remote-shared",
            verification_modes=["bounded-live", "fixture"],
            latency_tier="medium",
            budget_tier="existing-allowance",
        )

    def invoke(self, request: ProviderRequest, route: ProviderRoute) -> ProviderResponse:
        unavailable = UnavailableProvider(name=self.name, model=self.model)
        return unavailable.invoke(request, route)

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        request = ProviderRequest(
            invocation_id=new_invocation_id("provider"),
            session_id=context.get("session_id", "spectrum"),
            role=context.get("role", ROLE_GENERALIST),
            task_domain=context.get("task_domain", purpose),
            prompt=purpose,
            context=context,
            existing_allowance_only=True,
        )
        route = ProviderRoute(
            provider_name=self.name,
            model=self.model,
            role=request.role,
            route_reason="adapter unavailable in deterministic tranche",
            local_or_remote="local" if self._capabilities().local else "remote",
            policy=ProviderPolicy(),
            availability_state="reachable" if self.reachable else "unavailable",
            latency_tier=self._capabilities().latency_tier,
            budget_tier=self._capabilities().budget_tier,
        )
        response = self.invoke(request, route)
        return response.outputs, _call_record_from_response(response, request)


@dataclass
class AnthropicCompatibleProvider(OpenAICompatibleProvider):
    name: str = "anthropic-compatible"


@dataclass
class QwenCompatibleProvider(OpenAICompatibleProvider):
    name: str = "qwen-compatible"


@dataclass
class VibeThinkerProvider(OpenAICompatibleProvider):
    name: str = "vibethinker"
    model: str = "optional-unavailable"
    backend: str = "unavailable"

    def invoke(self, request: ProviderRequest, route: ProviderRoute) -> ProviderResponse:
        if any(token in request.prompt.lower() for token in ("tool call", "filesystem", "shell", "commit", "connector")):
            error = ProviderError(
                error_class="ForbiddenAuthorityRequest",
                message="VibeThinker adapter rejects tool, filesystem, shell, connector, and commit authority requests.",
                retryable=False,
            )
            usage = ProviderUsage(
                input_tokens=len(request.prompt.split()),
                output_tokens=0,
                cached_tokens=0,
                elapsed_ms=0,
                reported_cost_usd=None,
                estimated_cost_usd=None,
                allowance_classification=route.policy.budget_policy,
                privacy_classification=request.privacy_requirement,
            )
            receipt = ProviderReceipt(
                invocation_id=request.invocation_id,
                session_id=request.session_id,
                provider=self.name,
                model=self.model,
                role=request.role,
                request_hash=stable_hash(request.to_record()),
                response_hash="",
                timestamp=time.time(),
                usage=usage,
                route=route,
                error=error,
                claims_affected=list(request.claims_requested),
                evidence_produced=[],
                deterministic_verification_result="BLOCKED",
                final_disposition="REJECTED_PRE_EXECUTION",
            )
            return ProviderResponse(
                provider=self.name,
                model=self.model,
                role=request.role,
                usage=usage,
                receipt=receipt,
                error=error,
            )
        if not self.reachable:
            return UnavailableProvider(name=self.name, model=self.model).invoke(request, route)
        return super().invoke(request, route)

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        request = ProviderRequest(
            invocation_id=new_invocation_id("vibe"),
            session_id=context.get("session_id", "spectrum"),
            role=context.get("role", ROLE_COMPACT_REASONER),
            task_domain=context.get("task_domain", purpose),
            prompt=purpose,
            context=context,
            expected_verification=context.get("expected_verification", "deterministic"),
            existing_allowance_only=True,
            local_only=bool(context.get("local_only", False)),
            candidate_count=context.get("candidate_count", 1),
            claims_requested=list(context.get("claims_requested", [])),
            prohibited_assumptions=list(context.get("prohibited_assumptions", [])),
            metadata={"constraints": list(context.get("constraints", [])), "backend": self.backend},
        )
        route = ProviderRoute(
            provider_name=self.name,
            model=self.model,
            role=request.role,
            route_reason=f"bounded {self.backend} adapter",
            local_or_remote="local" if self._capabilities().local else "remote",
            policy=ProviderPolicy(budget_policy="local-only", allow_remote=False, allow_live_calls=False),
            availability_state="reachable" if self.reachable else "unavailable",
            latency_tier=self._capabilities().latency_tier,
            budget_tier=self._capabilities().budget_tier,
        )
        response = self.invoke(request, route)
        return response.outputs, _call_record_from_response(response, request)
