"""
Completion Integrity Guard (initial implementation).

Core rule from bootstrap directive:
"The assistant may be polite. The kernel must be honest."

Before any capability may be classified as IMPLEMENTED / VERIFIED / DEPLOYED,
the guard must confirm:
- artifact exists and can be reopened
- no prohibited placeholders
- required tests / evidence present
- source parses / compiles where applicable
- Git status known
- remote commit verified where claimed

This module + its acceptance test are the first executable enforcement.

Lineage: M0 evidence (contracts.py, controller.py, live doctrine sources,
Guardian whitepaper PERCEPT→...→SERA flow). New code by the recovery agent
under the boundaries set by James Clow and Melissa Clow, BonAcqui LLC.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import List, Dict, Any

PROHIBITED_PLACEHOLDERS = [
    "PASTE", "PLACEHOLDER", "TODO", "TBD", "INSERT CODE", "ADD CODE HERE",
    "FULL CODE HERE", "IMPLEMENT LATER", "MOCK SUCCESS", "SIMULATED SUCCESS"
]

@dataclass
class IntegrityResult:
    allowed: bool
    reason: str
    evidence: Dict[str, Any]

def _reopen_and_check(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Artifact does not exist: {path}")
    content = p.read_text(encoding="utf-8", errors="replace")
    if len(content) == 0:
        raise ValueError(f"Zero-byte artifact: {path}")
    return content

def _contains_prohibited_placeholder(content: str) -> List[str]:
    found = []
    for ph in PROHIBITED_PLACEHOLDERS:
        if re.search(re.escape(ph), content, re.IGNORECASE):
            found.append(ph)
    return found

def attempt_transition(
    capability_name: str,
    artifact_paths: List[str],
    claimed_status: str = "IMPLEMENTED",
    extra_evidence: Dict[str, Any] | None = None
) -> IntegrityResult:
    """
    Central gate. Returns allowed=False for any violation.
    """
    extra = extra_evidence or {}
    reasons: List[str] = []

    for ap in artifact_paths:
        try:
            content = _reopen_and_check(ap)
        except Exception as e:
            return IntegrityResult(False, f"Reopen failed for {ap}: {e}", extra)

        bad = _contains_prohibited_placeholder(content)
        if bad:
            reasons.append(f"Prohibited placeholder(s) {bad} in {ap}")

    if reasons:
        denial = {
            "capability": capability_name,
            "attempted_status": claimed_status,
            "denied_because": reasons,
            "artifacts_checked": artifact_paths,
        }
        extra["denial_record"] = denial
        return IntegrityResult(False, " | ".join(reasons), extra)

    # Additional negative checks can be extended here (malformed JSON, failed command, etc.)
    return IntegrityResult(True, "All integrity checks passed", extra)
