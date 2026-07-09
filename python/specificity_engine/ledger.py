"""
Append-only hash-chained specificity ledger and verified replay.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from .adapters import BasinSpecificityDecision, govern_basin_action
from .contracts import MeasurementReceipt
from .debt import DebtAssessment, verify_debt_assessment
from .measurement import canonical_json, verify_receipt


class LedgerIntegrityError(ValueError):
    """Raised when replay detects malformed, reordered, or modified evidence."""


@dataclass(frozen=True)
class LedgerEvent:
    sequence: int
    previous_hash: str
    payload: Dict[str, Any]
    event_hash: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "previous_hash": self.previous_hash,
            "payload": self.payload,
            "event_hash": self.event_hash,
        }


@dataclass(frozen=True)
class ReplaySnapshot:
    event_count: int
    chain_head: str
    final_receipt: MeasurementReceipt | None
    final_assessment: DebtAssessment | None
    final_decision: BasinSpecificityDecision | None
    events: Tuple[LedgerEvent, ...]


def _event_hash(sequence: int, previous_hash: str, payload: Dict[str, Any]) -> str:
    body = {
        "sequence": sequence,
        "previous_hash": previous_hash,
        "payload": payload,
    }
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


class SpecificityLedger:
    """A local JSONL event ledger whose complete chain is checked on replay."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(
        self,
        receipt: MeasurementReceipt,
        assessment: DebtAssessment,
        decision: BasinSpecificityDecision,
    ) -> LedgerEvent:
        if not verify_receipt(receipt):
            raise LedgerIntegrityError("cannot append an invalid measurement receipt")
        if assessment.receipt_id != receipt.receipt_id:
            raise LedgerIntegrityError("debt assessment does not reference the receipt")
        if not verify_debt_assessment(receipt, assessment):
            raise LedgerIntegrityError("cannot append an invalid debt assessment")
        if decision.receipt_id != receipt.receipt_id:
            raise LedgerIntegrityError("governance decision does not reference the receipt")
        expected_decision = govern_basin_action(
            assessment,
            epistemic=decision.epistemic,
            requested_action=decision.requested_action,
        )
        if decision != expected_decision:
            raise LedgerIntegrityError("cannot append an invalid governance decision")

        snapshot = self.replay()
        sequence = snapshot.event_count + 1
        previous_hash = snapshot.chain_head
        payload = {
            "receipt": receipt.to_record(),
            "assessment": assessment.to_record(),
            "decision": decision.to_record(),
        }
        event = LedgerEvent(
            sequence=sequence,
            previous_hash=previous_hash,
            payload=payload,
            event_hash=_event_hash(sequence, previous_hash, payload),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(event.to_record()) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def replay(self) -> ReplaySnapshot:
        if not self.path.exists():
            return ReplaySnapshot(0, "", None, None, None, ())

        events = []
        previous_hash = ""
        final_receipt = None
        final_assessment = None
        final_decision = None
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                raise LedgerIntegrityError(f"blank ledger line at {line_number}")
            try:
                record = json.loads(line)
                sequence = int(record["sequence"])
                event_previous_hash = str(record["previous_hash"])
                payload = dict(record["payload"])
                recorded_hash = str(record["event_hash"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise LedgerIntegrityError(
                    f"malformed ledger event at line {line_number}"
                ) from exc
            if sequence != line_number:
                raise LedgerIntegrityError(
                    f"ledger sequence mismatch at line {line_number}"
                )
            if event_previous_hash != previous_hash:
                raise LedgerIntegrityError(
                    f"ledger chain mismatch at line {line_number}"
                )
            expected_hash = _event_hash(sequence, event_previous_hash, payload)
            if recorded_hash != expected_hash:
                raise LedgerIntegrityError(
                    f"ledger event hash mismatch at line {line_number}"
                )

            try:
                receipt = MeasurementReceipt.from_record(payload["receipt"])
                assessment = DebtAssessment.from_record(payload["assessment"])
                decision = BasinSpecificityDecision.from_record(payload["decision"])
            except (KeyError, TypeError, ValueError) as exc:
                raise LedgerIntegrityError(
                    f"invalid ledger payload at line {line_number}"
                ) from exc
            if not verify_receipt(receipt):
                raise LedgerIntegrityError(
                    f"invalid measurement receipt at line {line_number}"
                )
            if assessment.receipt_id != receipt.receipt_id:
                raise LedgerIntegrityError(
                    f"assessment receipt mismatch at line {line_number}"
                )
            if not verify_debt_assessment(receipt, assessment):
                raise LedgerIntegrityError(
                    f"invalid debt assessment at line {line_number}"
                )
            if decision.receipt_id != receipt.receipt_id:
                raise LedgerIntegrityError(
                    f"decision receipt mismatch at line {line_number}"
                )
            expected_decision = govern_basin_action(
                assessment,
                epistemic=decision.epistemic,
                requested_action=decision.requested_action,
            )
            if expected_decision != decision:
                raise LedgerIntegrityError(
                    f"invalid governance decision at line {line_number}"
                )

            event = LedgerEvent(
                sequence=sequence,
                previous_hash=event_previous_hash,
                payload=payload,
                event_hash=recorded_hash,
            )
            events.append(event)
            previous_hash = recorded_hash
            final_receipt = receipt
            final_assessment = assessment
            final_decision = decision

        return ReplaySnapshot(
            event_count=len(events),
            chain_head=previous_hash,
            final_receipt=final_receipt,
            final_assessment=final_assessment,
            final_decision=final_decision,
            events=tuple(events),
        )
