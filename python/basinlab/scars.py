"""
Contradiction scar tracking for BasinLab.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List

from packages.ternary.states import EpistemicState


def _scar_hash(claim_id: str, contradictory_evidence: List[str]) -> str:
    payload = json.dumps({"claim_id": claim_id, "evidence": sorted(contradictory_evidence)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ContradictionScar:
    scar_id: str
    claim_id: str
    trajectory_id: str
    prior_epistemic_state: EpistemicState
    contradictory_evidence: List[str]
    timestamp: float
    source: str
    confidence: float
    unresolved_questions: List[str]
    recovery_eligibility: bool
    provenance: str
    evidence_hash: str


class ScarRegistry:
    def __init__(self) -> None:
        self._scars: Dict[str, ContradictionScar] = {}

    def record_scar(
        self,
        claim_id: str,
        trajectory_id: str,
        prior_epistemic_state: EpistemicState,
        contradictory_evidence: List[str],
        source: str,
        confidence: float,
        unresolved_questions: List[str],
        recovery_eligibility: bool,
        provenance: str,
    ) -> ContradictionScar:
        evidence_hash = _scar_hash(claim_id, contradictory_evidence)
        if evidence_hash in self._scars:
            return self._scars[evidence_hash]
        scar = ContradictionScar(
            scar_id=f"scar-{len(self._scars) + 1:04d}",
            claim_id=claim_id,
            trajectory_id=trajectory_id,
            prior_epistemic_state=prior_epistemic_state,
            contradictory_evidence=list(contradictory_evidence),
            timestamp=time.time(),
            source=source,
            confidence=confidence,
            unresolved_questions=list(unresolved_questions),
            recovery_eligibility=recovery_eligibility,
            provenance=provenance,
            evidence_hash=evidence_hash,
        )
        self._scars[evidence_hash] = scar
        return scar

    def all_scars(self) -> List[ContradictionScar]:
        return list(self._scars.values())

    def export_records(self) -> List[Dict[str, object]]:
        return [
            {
                "scar_id": scar.scar_id,
                "claim_id": scar.claim_id,
                "trajectory_id": scar.trajectory_id,
                "prior_epistemic_state": scar.prior_epistemic_state.value,
                "contradictory_evidence": list(scar.contradictory_evidence),
                "timestamp": scar.timestamp,
                "source": scar.source,
                "confidence": scar.confidence,
                "unresolved_questions": list(scar.unresolved_questions),
                "recovery_eligibility": scar.recovery_eligibility,
                "provenance": scar.provenance,
                "evidence_hash": scar.evidence_hash,
            }
            for scar in self.all_scars()
        ]

    @classmethod
    def from_records(cls, records: List[Dict[str, object]]) -> "ScarRegistry":
        registry = cls()
        for record in records:
            scar = ContradictionScar(
                scar_id=str(record["scar_id"]),
                claim_id=str(record["claim_id"]),
                trajectory_id=str(record["trajectory_id"]),
                prior_epistemic_state=EpistemicState(str(record["prior_epistemic_state"])),
                contradictory_evidence=list(record["contradictory_evidence"]),
                timestamp=float(record["timestamp"]),
                source=str(record["source"]),
                confidence=float(record["confidence"]),
                unresolved_questions=list(record["unresolved_questions"]),
                recovery_eligibility=bool(record["recovery_eligibility"]),
                provenance=str(record["provenance"]),
                evidence_hash=str(record["evidence_hash"]),
            )
            registry._scars[scar.evidence_hash] = scar
        return registry
