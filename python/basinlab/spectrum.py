"""
Candidate spectrum generation and deduplication.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List

from .providers import Provider, ProviderCallRecord


NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}


def _normalize_text(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    normalized = re.sub(r"\b(the|a|an|answer|is|equals)\b", " ", lowered).strip()
    tokens = [NUMBER_WORDS.get(token, token) for token in normalized.split()]
    return " ".join(tokens)


def _payload_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass
class CandidateAssumption:
    text: str
    provenance: str

    @property
    def normalized(self) -> str:
        return _normalize_text(self.text)


@dataclass
class CandidatePrediction:
    text: str
    required_evidence: List[str] = field(default_factory=list)


@dataclass
class CandidateTrajectory:
    trajectory_id: str
    answer: str
    reasoning: str
    approach: str
    provider: str
    assumptions: List[CandidateAssumption] = field(default_factory=list)
    predictions: List[CandidatePrediction] = field(default_factory=list)
    remembered: bool = False
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_answer(self) -> str:
        return _normalize_text(self.answer)

    @property
    def reasoning_fingerprint(self) -> str:
        return _payload_hash(
            {
                "approach": _normalize_text(self.approach),
                "reasoning": _normalize_text(self.reasoning),
                "assumptions": [assumption.normalized for assumption in self.assumptions],
                "predictions": [_normalize_text(prediction.text) for prediction in self.predictions],
            }
        )


@dataclass
class CandidateAuditEntry:
    trajectory_id: str
    decision: str
    reason: str
    merged_into: str = ""


@dataclass
class CandidateSpectrum:
    retained: List[CandidateTrajectory] = field(default_factory=list)
    merged: List[CandidateAuditEntry] = field(default_factory=list)
    rejected: List[CandidateAuditEntry] = field(default_factory=list)
    contradicted: List[CandidateAuditEntry] = field(default_factory=list)
    unresolved: List[CandidateAuditEntry] = field(default_factory=list)
    provider_calls: List[ProviderCallRecord] = field(default_factory=list)


class CandidateDeduplicator:
    def deduplicate(self, candidates: Iterable[CandidateTrajectory]) -> CandidateSpectrum:
        spectrum = CandidateSpectrum()
        retained_by_key: Dict[tuple[str, str], CandidateTrajectory] = {}
        for candidate in sorted(candidates, key=lambda item: item.trajectory_id):
            key = (candidate.normalized_answer, candidate.reasoning_fingerprint)
            if key in retained_by_key:
                merged_into = retained_by_key[key].trajectory_id
                spectrum.merged.append(
                    CandidateAuditEntry(
                        trajectory_id=candidate.trajectory_id,
                        decision="merged",
                        reason="Equivalent answer and materially equivalent reasoning",
                        merged_into=merged_into,
                    )
                )
                continue
            retained_by_key[key] = candidate
            spectrum.retained.append(candidate)
        return spectrum


class CandidateGenerator:
    def __init__(
        self,
        deterministic_strategies: Iterable[Callable[[str, Dict[str, Any]], Iterable[CandidateTrajectory]]] = (),
        providers: Iterable[Provider] = (),
        remembered_trajectories: Iterable[CandidateTrajectory] = (),
    ) -> None:
        self.deterministic_strategies = list(deterministic_strategies)
        self.providers = list(providers)
        self.remembered_trajectories = list(remembered_trajectories)

    def generate(self, purpose: str, context: Dict[str, Any]) -> CandidateSpectrum:
        all_candidates: List[CandidateTrajectory] = []
        provider_calls: List[ProviderCallRecord] = []
        for strategy in self.deterministic_strategies:
            all_candidates.extend(list(strategy(purpose, context)))
        for trajectory in self.remembered_trajectories:
            remembered = CandidateTrajectory(**{**trajectory.__dict__, "remembered": True})
            all_candidates.append(remembered)
        for provider in self.providers:
            outputs, call = provider.generate(purpose, context)
            provider_calls.append(call)
            for index, output in enumerate(outputs, start=1):
                all_candidates.append(
                    CandidateTrajectory(
                        trajectory_id=output.get("trajectory_id", f"{provider.name}-{index}"),
                        answer=output["answer"],
                        reasoning=output.get("reasoning", ""),
                        approach=output.get("approach", provider.name),
                        provider=provider.name,
                        assumptions=[
                            CandidateAssumption(text=item["text"], provenance=item.get("provenance", provider.name))
                            for item in output.get("assumptions", [])
                        ],
                        predictions=[
                            CandidatePrediction(
                                text=item["text"],
                                required_evidence=list(item.get("required_evidence", [])),
                            )
                            for item in output.get("predictions", [])
                        ],
                        metadata=dict(output.get("metadata", {})),
                    )
                )
        valid_candidates = []
        spectrum = CandidateSpectrum(provider_calls=provider_calls)
        for candidate in all_candidates:
            if not candidate.answer.strip():
                spectrum.rejected.append(
                    CandidateAuditEntry(
                        trajectory_id=candidate.trajectory_id,
                        decision="rejected",
                        reason="Candidate answer is empty after provider/strategy generation",
                    )
                )
                continue
            valid_candidates.append(candidate)

        deduped = CandidateDeduplicator().deduplicate(valid_candidates)
        spectrum.retained = deduped.retained
        spectrum.merged = deduped.merged
        spectrum.provider_calls = provider_calls
        retained_ids = {candidate.trajectory_id for candidate in spectrum.retained}
        for candidate in valid_candidates:
            if candidate.trajectory_id in retained_ids:
                continue
            if any(entry.trajectory_id == candidate.trajectory_id for entry in spectrum.merged):
                continue
            spectrum.rejected.append(
                CandidateAuditEntry(
                    trajectory_id=candidate.trajectory_id,
                    decision="rejected",
                    reason="Filtered during candidate processing",
                )
            )
        return spectrum
