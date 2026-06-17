"""
Governed provider routing, inventory, and auditable invocation ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import URLError
from urllib.request import urlopen

from .contracts import (
    CandidateReasoningPacket,
    ProblemPacket,
    ProviderCapabilities,
    ProviderError,
    ProviderPolicy,
    ProviderReceipt,
    ProviderRequest,
    ProviderResponse,
    ProviderRoute,
    ProviderUsage,
)


ROLE_GENERALIST = "generalist-planner"
ROLE_ACTOR = "actor"
ROLE_COMPACT_REASONER = "compact-reasoner"
ROLE_VERIFIER = "verifier"
ROLE_SUMMARIZER = "summarizer"
ROLE_RETRIEVAL = "embedding-or-retrieval"


def stable_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def new_invocation_id(prefix: str = "prov") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class ProviderAdapter:
    name = "provider"
    model = "unconfigured"

    def __init__(self, *, capabilities: Optional[ProviderCapabilities] = None) -> None:
        self.capabilities = capabilities or ProviderCapabilities()

    @property
    def can_execute(self) -> bool:
        return self.capabilities.can_execute

    @property
    def can_commit(self) -> bool:
        return self.capabilities.can_commit

    def invoke(self, request: ProviderRequest, route: ProviderRoute) -> ProviderResponse:
        raise NotImplementedError

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        request = ProviderRequest(
            invocation_id=new_invocation_id("legacy"),
            session_id=context.get("session_id", "legacy-spectrum"),
            role=ROLE_GENERALIST,
            task_domain=context.get("task_domain", purpose),
            prompt=purpose,
            context=context,
            existing_allowance_only=True,
        )
        route = ProviderRoute(
            provider_name=self.name,
            model=self.model,
            role=request.role,
            route_reason="legacy-spectrum compatibility",
            local_or_remote="local" if self.capabilities.local else "remote",
            policy=ProviderPolicy(),
            availability_state="available" if self.capabilities.reachable else "unavailable",
            latency_tier=self.capabilities.latency_tier,
            budget_tier=self.capabilities.budget_tier,
        )
        response = self.invoke(request, route)
        receipt = response.receipt.to_record() if response.receipt else {}
        return response.outputs, receipt


class FixtureProvider(ProviderAdapter):
    def __init__(
        self,
        name: str,
        *,
        model: str,
        scripted_outputs: Iterable[Dict[str, Any]],
        capabilities: ProviderCapabilities,
    ) -> None:
        super().__init__(capabilities=capabilities)
        self.name = name
        self.model = model
        self.scripted_outputs = list(scripted_outputs)

    def invoke(self, request: ProviderRequest, route: ProviderRoute) -> ProviderResponse:
        started = time.time()
        outputs = list(self.scripted_outputs)[: max(1, request.candidate_count)]
        usage = ProviderUsage(
            input_tokens=len(request.prompt.split()),
            output_tokens=sum(len(json.dumps(item)) for item in outputs),
            cached_tokens=0,
            elapsed_ms=max(1, int((time.time() - started) * 1000)),
            reported_cost_usd=None,
            estimated_cost_usd=0.0,
            allowance_classification=route.policy.budget_policy,
            privacy_classification=request.privacy_requirement,
        )
        claims = []
        for index, output in enumerate(outputs, start=1):
            for claim in output.get("decision_claims", []):
                claims.append(
                    {
                        "claim_id": f"{self.name}-claim-{index}-{len(claims)+1}",
                        "text": claim,
                        "provider": self.name,
                    }
                )
        evidence = [{"kind": "fixture-output", "provider": self.name, "count": len(outputs)}]
        receipt = ProviderReceipt(
            invocation_id=request.invocation_id,
            session_id=request.session_id,
            provider=self.name,
            model=self.model,
            role=request.role,
            request_hash=stable_hash(request.to_record()),
            response_hash=stable_hash({"outputs": outputs, "claims": claims}),
            timestamp=time.time(),
            usage=usage,
            route=route,
            claims_affected=list(request.claims_requested),
            evidence_produced=["fixture-output"],
            deterministic_verification_result="FIXTURE_VERIFIED",
            final_disposition="RECORDED",
        )
        return ProviderResponse(
            provider=self.name,
            model=self.model,
            role=request.role,
            outputs=outputs,
            claims=claims,
            evidence=evidence,
            usage=usage,
            receipt=receipt,
        )


class UnavailableProvider(ProviderAdapter):
    name = "unavailable"
    model = "unavailable"

    def __init__(self, name: str = "unavailable", model: str = "unavailable") -> None:
        super().__init__(
            capabilities=ProviderCapabilities(
                supports_text_generation=False,
                supports_structured_output=False,
                local=False,
                remote=True,
                reachable=False,
                can_execute=False,
                can_commit=False,
                can_use_tools=False,
                can_use_connectors=False,
                privacy_tier="unknown",
                verification_modes=[],
                latency_tier="unknown",
                budget_tier="unknown",
            )
        )
        self.name = name
        self.model = model

    def invoke(self, request: ProviderRequest, route: ProviderRoute) -> ProviderResponse:
        error = ProviderError(
            error_class="ProviderUnavailable",
            message=f"{self.name} is unavailable in this environment",
            retryable=False,
        )
        usage = ProviderUsage(
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
            deterministic_verification_result="UNAVAILABLE",
            final_disposition="NO_OUTPUT",
        )
        return ProviderResponse(
            provider=self.name,
            model=self.model,
            role=request.role,
            outputs=[],
            claims=[],
            evidence=[],
            usage=usage,
            receipt=receipt,
            error=error,
        )


class ProviderLedger:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "provider-ledger.jsonl"

    def record(self, receipt: ProviderReceipt) -> Dict[str, Any]:
        payload = receipt.to_record()
        sanitized = {
            "invocation_id": payload["invocation_id"],
            "session_id": payload["session_id"],
            "provider": payload["provider"],
            "model": payload["model"],
            "role": payload["role"],
            "request_hash": payload["request_hash"],
            "response_hash": payload["response_hash"],
            "timestamp": payload["timestamp"],
            "elapsed_ms": payload["usage"]["elapsed_ms"],
            "input_tokens": payload["usage"]["input_tokens"],
            "output_tokens": payload["usage"]["output_tokens"],
            "cached_tokens": payload["usage"]["cached_tokens"],
            "retries": payload["usage"]["retries"],
            "error_class": payload["error"]["error_class"] if payload["error"] else "",
            "reported_cost_usd": payload["usage"]["reported_cost_usd"],
            "estimated_cost_usd": payload["usage"]["estimated_cost_usd"],
            "allowance_classification": payload["usage"]["allowance_classification"],
            "privacy_classification": payload["usage"]["privacy_classification"],
            "claims_affected": list(payload["claims_affected"]),
            "evidence_produced": list(payload["evidence_produced"]),
            "deterministic_verification_result": payload["deterministic_verification_result"],
            "final_disposition": payload["final_disposition"],
            "route": payload["route"],
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sanitized, sort_keys=True) + "\n")
        return sanitized

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


def budget_policy_allows(policy: ProviderPolicy, request: ProviderRequest, adapter: ProviderAdapter) -> bool:
    if policy.budget_policy == "zero-cost-only":
        return adapter.capabilities.local
    if policy.budget_policy == "local-only":
        return adapter.capabilities.local
    if policy.budget_policy == "existing-allowance-only":
        return request.existing_allowance_only
    if policy.budget_policy == "human-approval-required":
        return False
    if policy.budget_policy == "explicit-fixed-ceiling":
        if request.budget_limit_usd is None or policy.explicit_ceiling_usd is None:
            return False
        return request.budget_limit_usd <= policy.explicit_ceiling_usd
    return True


class ProviderRouter:
    def __init__(self, adapters: Iterable[ProviderAdapter]) -> None:
        self.adapters = {adapter.name: adapter for adapter in adapters}

    def route(self, request: ProviderRequest, policy: ProviderPolicy) -> ProviderRoute:
        candidates = list(self.adapters.values())
        if request.user_preference and request.user_preference in self.adapters:
            candidates = [self.adapters[request.user_preference]] + [
                adapter for adapter in candidates if adapter.name != request.user_preference
            ]

        scored: List[tuple[int, ProviderAdapter, str]] = []
        for adapter in candidates:
            reason_bits: List[str] = []
            score = 0
            if request.local_only and not adapter.capabilities.local:
                reason_bits.append("remote blocked by request.local_only")
                score -= 50
            if request.privacy_requirement == "private" and adapter.capabilities.remote and not policy.allow_remote:
                reason_bits.append("private request prefers local path")
                score -= 30
            if request.role == ROLE_COMPACT_REASONER and adapter.name in {"compact-reasoner", "vibethinker"}:
                score += 40
                reason_bits.append("role-specific compact reasoning")
            if request.role == ROLE_GENERALIST and adapter.name == "generalist":
                score += 40
                reason_bits.append("role-specific generalist planning")
            if request.role == ROLE_VERIFIER and adapter.name in {"generalist", "scripted"}:
                score += 20
                reason_bits.append("verifier prefers deterministic path")
            if request.role == ROLE_RETRIEVAL and adapter.capabilities.supports_embeddings:
                score += 30
                reason_bits.append("retrieval capability present")
            if request.expected_verification == "deterministic" and adapter.capabilities.local:
                score += 20
                reason_bits.append("local deterministic verification")
            if adapter.capabilities.reachable:
                score += 10
                reason_bits.append("reachable")
            if not budget_policy_allows(policy, request, adapter):
                reason_bits.append("budget policy does not allow this adapter")
                score -= 40
            if request.model_preference and request.model_preference == adapter.model:
                score += 15
                reason_bits.append("requested model matched")
            if request.task_domain in {"code", "repair"} and adapter.name in {"generalist", "compact-reasoner"}:
                score += 10
                reason_bits.append("task-domain affinity")
            if not reason_bits:
                reason_bits.append("default fallback")
            scored.append((score, adapter, "; ".join(reason_bits)))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        _, adapter, reason = scored[0]
        return ProviderRoute(
            provider_name=adapter.name,
            model=adapter.model,
            role=request.role,
            route_reason=reason,
            local_or_remote="local" if adapter.capabilities.local else "remote",
            policy=policy,
            availability_state="reachable" if adapter.capabilities.reachable else "unavailable",
            latency_tier=adapter.capabilities.latency_tier,
            budget_tier=adapter.capabilities.budget_tier,
        )

    def invoke(self, request: ProviderRequest, policy: ProviderPolicy, ledger: ProviderLedger) -> ProviderResponse:
        route = self.route(request, policy)
        adapter = self.adapters[route.provider_name]
        response = adapter.invoke(request, route)
        if response.receipt:
            ledger.record(response.receipt)
        return response


def _check_url(url: str, timeout_s: float = 0.4) -> bool:
    try:
        with urlopen(url, timeout=timeout_s) as response:
            return response.status < 500
    except (URLError, ValueError, TimeoutError):
        return False


def _gpu_inventory() -> List[Dict[str, Any]]:
    if shutil.which("nvidia-smi") is None:
        return []
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if completed.returncode != 0:
        return []
    inventory = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        inventory.append({"gpu_model": parts[0], "vram_mb": int(parts[1]) if len(parts) > 1 else None})
    return inventory


def local_model_inventory() -> Dict[str, Any]:
    disk = shutil.disk_usage(Path.cwd())
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "system_ram_gb": round((os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) / (1024**3), 2)
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names
        else None,
        "free_disk_gb": round(disk.free / (1024**3), 2),
        "gpus": _gpu_inventory(),
        "huggingface_cache": str(Path.home() / ".cache" / "huggingface"),
        "ollama_models": str(Path.home() / ".ollama" / "models"),
        "lm_studio_cache": str(Path.home() / ".cache" / "lm-studio"),
        "vllm_endpoint": os.environ.get("VLLM_BASE_URL", ""),
        "sglang_endpoint": os.environ.get("SGLANG_BASE_URL", ""),
        "openai_compatible_endpoint": os.environ.get("OPENAI_BASE_URL", ""),
    }


def provider_inventory() -> List[Dict[str, Any]]:
    entries = [
        {
            "provider_name": "scripted",
            "credential_present": False,
            "endpoint_class": "deterministic-fixture",
            "configured_models": ["scripted-deterministic"],
            "allowance_status": "local-only",
            "local_or_remote": "local",
            "reachable": True,
        },
        {
            "provider_name": "openai-compatible",
            "credential_present": bool(os.environ.get("OPENAI_API_KEY")),
            "endpoint_class": "openai-compatible",
            "configured_models": [os.environ.get("OPENAI_MODEL", "unconfigured")],
            "allowance_status": "existing-allowance-only" if os.environ.get("OPENAI_API_KEY") else "unknown",
            "local_or_remote": "remote" if not os.environ.get("OPENAI_BASE_URL", "").startswith("http://127.0.0.1") else "local",
            "reachable": _check_url(os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1/models"))
            if os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_KEY")
            else False,
        },
        {
            "provider_name": "anthropic-compatible",
            "credential_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "endpoint_class": "anthropic-compatible",
            "configured_models": [os.environ.get("ANTHROPIC_MODEL", "unconfigured")],
            "allowance_status": "existing-allowance-only" if os.environ.get("ANTHROPIC_API_KEY") else "unknown",
            "local_or_remote": "remote",
            "reachable": False,
        },
        {
            "provider_name": "qwen-compatible",
            "credential_present": bool(os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")),
            "endpoint_class": "qwen-compatible",
            "configured_models": [os.environ.get("QWEN_MODEL", "unconfigured")],
            "allowance_status": "existing-allowance-only"
            if os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
            else "unknown",
            "local_or_remote": "remote",
            "reachable": False,
        },
        {
            "provider_name": "vibethinker",
            "credential_present": bool(
                os.environ.get("VIBETHINKER_MODEL")
                or os.environ.get("VLLM_BASE_URL")
                or os.environ.get("SGLANG_BASE_URL")
                or os.environ.get("OPENAI_BASE_URL")
            ),
            "endpoint_class": "local-transformers-or-compatible",
            "configured_models": [
                os.environ.get("VIBETHINKER_MODEL", "optional-unavailable"),
                os.environ.get("VLLM_MODEL", ""),
                os.environ.get("SGLANG_MODEL", ""),
            ],
            "allowance_status": "local-only" if os.environ.get("VLLM_BASE_URL") or os.environ.get("SGLANG_BASE_URL") else "unknown",
            "local_or_remote": "local" if os.environ.get("VLLM_BASE_URL") or os.environ.get("SGLANG_BASE_URL") else "unknown",
            "reachable": _check_url(os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000/v1/models"))
            if os.environ.get("VLLM_BASE_URL")
            else _check_url(os.environ.get("SGLANG_BASE_URL", "http://127.0.0.1:30000/v1/models"))
            if os.environ.get("SGLANG_BASE_URL")
            else False,
        },
    ]
    return entries


def compact_reasoner_packet(problem: ProblemPacket, answer: CandidateReasoningPacket) -> Dict[str, Any]:
    return {
        "problem_packet": problem.to_record(),
        "candidate_reasoning_packet": answer.to_record(),
    }
