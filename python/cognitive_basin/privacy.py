"""
Privacy, scope, and redaction helpers for governed memory.
"""

from __future__ import annotations

import hashlib
import re
from enum import StrEnum


UNKNOWN_PARTICIPANT = "UNKNOWN"


class VisibilityScope(StrEnum):
    SESSION_ONLY = "SESSION_ONLY"
    PRIVATE_JAMES = "PRIVATE_JAMES"
    PRIVATE_MELISSA = "PRIVATE_MELISSA"
    SHARED_PROJECT = "SHARED_PROJECT"
    EXPORTABLE_REDACTED = "EXPORTABLE_REDACTED"
    AUDIT_RETAINED = "AUDIT_RETAINED"


class RetentionClass(StrEnum):
    SESSION_WORKING = "SESSION_WORKING"
    PRIVATE_WORKING = "PRIVATE_WORKING"
    SHARED_WORKING = "SHARED_WORKING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    AUDIT_RECORD = "AUDIT_RECORD"


class SensitivityLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    RESTRICTED = "RESTRICTED"


_SECRET_PATTERNS = [
    re.compile(r"\bgho_[A-Za-z0-9_]+\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bapi[_ -]?key\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
]


def explicit_participant(value: str | None) -> str:
    stripped = str(value or "").strip()
    return stripped if stripped else UNKNOWN_PARTICIPANT


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact_text(text: str, scope: VisibilityScope) -> tuple[str, bool]:
    redacted = text
    redacted_any = False
    for pattern in _SECRET_PATTERNS:
        if pattern.search(redacted):
            redacted_any = True
            redacted = pattern.sub("[redacted-secret]", redacted)
    if scope == VisibilityScope.EXPORTABLE_REDACTED:
        redacted_any = True
        redacted = redacted[:160]
    return redacted, redacted_any
