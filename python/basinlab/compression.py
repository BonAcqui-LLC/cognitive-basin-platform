"""
Verified compression for BasinLab trajectories.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class FullTrajectoryRecord:
    purpose: str
    decisive_claims: List[str]
    evidence_links: Dict[str, List[str]]
    contradictory_evidence: Dict[str, List[str]]
    failures_changed_route: List[str]
    scar_ids: List[str]
    recovery_decisions: List[str]
    commit_decision: str
    replay_references: Dict[str, str]
    final_epistemic: str
    uncertainty: List[str] = field(default_factory=list)
    provenance_complete: bool = True


@dataclass
class CompressedTrajectory:
    purpose: str
    decisive_claims: List[str]
    evidence_links: Dict[str, List[str]]
    contradictory_evidence: Dict[str, List[str]]
    failures_changed_route: List[str]
    scar_ids: List[str]
    recovery_decisions: List[str]
    commit_decision: str
    replay_references: Dict[str, str]
    final_epistemic: str
    uncertainty: List[str]
    digest: str


class VerifiedCompression:
    def __init__(self, replay_validator: Callable[[FullTrajectoryRecord, CompressedTrajectory], bool]) -> None:
        self.replay_validator = replay_validator

    def compress(self, full: FullTrajectoryRecord) -> CompressedTrajectory:
        if not full.provenance_complete:
            raise ValueError("Compression rejected: provenance becomes incomplete")
        if not full.decisive_claims:
            raise ValueError("Compression rejected: decisive claims missing")
        for claim in full.decisive_claims:
            if claim not in full.evidence_links or not full.evidence_links[claim]:
                raise ValueError(f"Compression rejected: decisive evidence lost for {claim}")
        for claim, evidence in full.contradictory_evidence.items():
            if evidence and claim not in full.evidence_links:
                raise ValueError(f"Compression rejected: contradiction without evidence link for {claim}")

        compressed = CompressedTrajectory(
            purpose=full.purpose,
            decisive_claims=list(full.decisive_claims),
            evidence_links={claim: list(links) for claim, links in full.evidence_links.items()},
            contradictory_evidence={claim: list(links) for claim, links in full.contradictory_evidence.items()},
            failures_changed_route=list(full.failures_changed_route),
            scar_ids=list(full.scar_ids),
            recovery_decisions=list(full.recovery_decisions),
            commit_decision=full.commit_decision,
            replay_references=dict(full.replay_references),
            final_epistemic=full.final_epistemic,
            uncertainty=list(full.uncertainty),
            digest="",
        )
        compressed.digest = hashlib.sha256(
            json.dumps(
                {
                    "purpose": compressed.purpose,
                    "decisive_claims": compressed.decisive_claims,
                    "evidence_links": compressed.evidence_links,
                    "contradictory_evidence": compressed.contradictory_evidence,
                    "replay_references": compressed.replay_references,
                    "final_epistemic": compressed.final_epistemic,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        if full.contradictory_evidence and not compressed.contradictory_evidence:
            raise ValueError("Compression rejected: contradictions disappear")
        if full.uncertainty and compressed.final_epistemic == "SUPPORTED":
            raise ValueError("Compression rejected: uncertainty converted into support")
        if not self.replay_validator(full, compressed):
            raise ValueError("Compression rejected: replay no longer reconstructs governed result")
        return compressed
