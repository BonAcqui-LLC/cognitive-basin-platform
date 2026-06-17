"""
Deterministic provider abstractions for BasinLab spectrum generation.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


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


class Provider(Protocol):
    name: str
    model: str
    can_execute: bool
    can_commit: bool

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        ...


def _stable_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass
class ScriptedProvider:
    name: str
    model: str = "scripted-deterministic"
    scripted_outputs: List[Dict[str, Any]] = field(default_factory=list)
    can_execute: bool = False
    can_commit: bool = False

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        started = time.perf_counter()
        outputs = list(self.scripted_outputs)
        duration = time.perf_counter() - started
        call = ProviderCallRecord(
            provider=self.name,
            model=self.model,
            duration_s=duration,
            input_hash=_stable_hash({"purpose": purpose, "context": context}),
            output_hash=_stable_hash({"outputs": outputs}),
            verified=False,
            token_count=sum(len(str(item)) for item in outputs),
        )
        return outputs, call


@dataclass
class GeneralistProvider(ScriptedProvider):
    name: str = "generalist"
    can_execute: bool = False
    can_commit: bool = False


@dataclass
class CompactReasonerProvider(ScriptedProvider):
    name: str = "compact-reasoner"
    can_execute: bool = False
    can_commit: bool = False


@dataclass
class OpenAICompatibleProvider:
    name: str = "openai-compatible"
    model: str = "unconfigured"
    can_execute: bool = False
    can_commit: bool = False

    def generate(self, purpose: str, context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], ProviderCallRecord]:
        call = ProviderCallRecord(
            provider=self.name,
            model=self.model,
            duration_s=0.0,
            input_hash=_stable_hash({"purpose": purpose, "context": context}),
            output_hash="",
            verified=False,
            error="Provider unavailable in deterministic local tranche",
        )
        return [], call


@dataclass
class VibeThinkerProvider(OpenAICompatibleProvider):
    name: str = "vibethinker"
    model: str = "optional-unavailable"
