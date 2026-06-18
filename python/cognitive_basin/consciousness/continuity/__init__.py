"""
Temporal continuity contracts and replay checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..common import stable_hash


@dataclass
class TemporalMoment:
    moment_id: str
    event_id: str
    timestamp: float
    repo_head: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "moment_id": self.moment_id,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "repo_head": self.repo_head,
        }


@dataclass
class TemporalSequence:
    sequence_id: str
    moment_ids: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"sequence_id": self.sequence_id, "moment_ids": list(self.moment_ids)}


@dataclass
class TemporalAnchor:
    anchor_id: str
    session_id: str
    participant: str
    purpose: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "session_id": self.session_id,
            "participant": self.participant,
            "purpose": self.purpose,
        }


@dataclass
class TemporalGap:
    gap_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"gap_id": self.gap_id, "detail": self.detail}


@dataclass
class TemporalPrediction:
    prediction_id: str
    expected_next_event: str

    def to_record(self) -> Dict[str, Any]:
        return {"prediction_id": self.prediction_id, "expected_next_event": self.expected_next_event}


@dataclass
class TemporalCorrection:
    correction_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"correction_id": self.correction_id, "detail": self.detail}


@dataclass
class ContinuityCheckpoint:
    checkpoint_id: str
    session_id: str
    latest_event_id: str
    latest_hash: str
    repo_head: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "latest_event_id": self.latest_event_id,
            "latest_hash": self.latest_hash,
            "repo_head": self.repo_head,
        }


@dataclass
class ContinuityBreak:
    break_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"break_id": self.break_id, "reason": self.reason}


@dataclass
class ContinuityRepair:
    repair_id: str
    reason: str

    def to_record(self) -> Dict[str, Any]:
        return {"repair_id": self.repair_id, "reason": self.reason}


@dataclass
class ContinuityThread:
    thread_id: str
    moments: List[TemporalMoment] = field(default_factory=list)
    breaks: List[ContinuityBreak] = field(default_factory=list)
    repairs: List[ContinuityRepair] = field(default_factory=list)
    unresolved_threads: List[str] = field(default_factory=list)
    resumed_work: List[str] = field(default_factory=list)
    superseded_purposes: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "moments": [item.to_record() for item in self.moments],
            "breaks": [item.to_record() for item in self.breaks],
            "repairs": [item.to_record() for item in self.repairs],
            "unresolved_threads": list(self.unresolved_threads),
            "resumed_work": list(self.resumed_work),
            "superseded_purposes": list(self.superseded_purposes),
        }


@dataclass
class ContinuityReceipt:
    anchor: TemporalAnchor
    checkpoint: ContinuityCheckpoint
    thread: ContinuityThread
    sequence: TemporalSequence
    gaps: List[TemporalGap]
    corrections: List[TemporalCorrection]

    def to_record(self) -> Dict[str, Any]:
        return {
            "anchor": self.anchor.to_record(),
            "checkpoint": self.checkpoint.to_record(),
            "thread": self.thread.to_record(),
            "sequence": self.sequence.to_record(),
            "gaps": [item.to_record() for item in self.gaps],
            "corrections": [item.to_record() for item in self.corrections],
        }


class ContinuityManager:
    def assess(
        self,
        *,
        session_id: str,
        events: List[Dict[str, Any]],
        repo_head: str,
        participant: str,
        purpose: str,
        prior_checkpoint: Dict[str, Any] | None = None,
    ) -> ContinuityReceipt:
        moments = [
            TemporalMoment(
                moment_id=f"moment-{index:04d}",
                event_id=str(event.get("event_id", f"event-{index:04d}")),
                timestamp=float(event.get("timestamp", 0.0)),
                repo_head=repo_head,
            )
            for index, event in enumerate(events, start=1)
        ]
        gaps: List[TemporalGap] = []
        breaks: List[ContinuityBreak] = []
        repairs: List[ContinuityRepair] = []
        expected_index = 1
        previous_timestamp = 0.0
        for event in events:
            event_id = str(event.get("event_id", ""))
            if "-" in event_id:
                tail = event_id.rsplit("-", 1)[-1]
                if tail.isdigit():
                    observed = int(tail)
                    if observed > expected_index:
                        gaps.append(TemporalGap(f"gap-{observed}", f"missing event before {event_id}"))
                        breaks.append(ContinuityBreak(f"break-{observed}", "missing_event"))
                    expected_index = observed + 1
            timestamp = float(event.get("timestamp", 0.0))
            if timestamp < previous_timestamp:
                breaks.append(ContinuityBreak(f"break-reordered-{event_id}", "reordered_event"))
            previous_timestamp = timestamp
        if prior_checkpoint and prior_checkpoint.get("repo_head") and prior_checkpoint.get("repo_head") != repo_head:
            breaks.append(ContinuityBreak("break-main-commit-change", "main_commit_change"))
        latest_hash = stable_hash(
            {
                "session_id": session_id,
                "latest_event_id": events[-1].get("event_id", "") if events else "",
                "repo_head": repo_head,
            }
        )
        checkpoint = ContinuityCheckpoint(
            checkpoint_id=f"checkpoint-{latest_hash[:10]}",
            session_id=session_id,
            latest_event_id=events[-1].get("event_id", "") if events else "",
            latest_hash=latest_hash,
            repo_head=repo_head,
        )
        if gaps or breaks:
            repairs.append(ContinuityRepair("repair-replay", "Continuity requires replay validation or checkpoint refresh"))
        thread = ContinuityThread(
            thread_id=f"thread-{stable_hash((session_id, repo_head))[:10]}",
            moments=moments,
            breaks=breaks,
            repairs=repairs,
            unresolved_threads=[item.reason for item in breaks],
        )
        return ContinuityReceipt(
            anchor=TemporalAnchor(f"anchor-{session_id}", session_id, participant, purpose),
            checkpoint=checkpoint,
            thread=thread,
            sequence=TemporalSequence(f"sequence-{session_id}", [item.moment_id for item in moments]),
            gaps=gaps,
            corrections=[TemporalCorrection("correction-refresh", "checkpoint hash refreshed")] if events else [],
        )


__all__ = [
    "ContinuityBreak",
    "ContinuityCheckpoint",
    "ContinuityManager",
    "ContinuityReceipt",
    "ContinuityRepair",
    "ContinuityThread",
    "TemporalAnchor",
    "TemporalCorrection",
    "TemporalGap",
    "TemporalMoment",
    "TemporalPrediction",
    "TemporalSequence",
]
