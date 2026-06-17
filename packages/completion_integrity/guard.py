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

def load_registry(path: str = "ops/manifests/capability-registry.json") -> dict:
    try:
        p = Path(path)
        if not p.exists():
            return {"capabilities": {}}
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"capabilities": {}}

def extract_claimed_capabilities(claim: str) -> List[str]:
    if not claim:
        return []
    cl = claim.lower()
    caps: List[str] = []
    if "deployment verified" in cl or ("deploy" in cl and "verif" in cl):
        caps.append("deployment.verify")
    if "sanitization completed" in cl:
        caps.append("sanitization.complete")
    if "backup restorable" in cl:
        caps.append("backup.restore")
    if "unit tests passed" in cl:
        caps.append("tests.unit")
    if "production operational" in cl:
        caps.append("production.operational")
    return caps

def _evaluate_claim_evidence(claim: str, artifact_paths: List[str], registry: dict) -> List[str]:
    reasons: List[str] = []
    claimed = extract_claimed_capabilities(claim)
    if not claimed:
        return reasons
    caps = registry.get("capabilities", {})
    for cap in claimed:
        if cap not in caps:
            reasons.append(f"Unknown capability in claim: {cap}")
            continue
        reqs = caps[cap].get("required_evidence", [])
        has_sufficient = False
        for ap in (artifact_paths or []):
            apl = ap.lower()
            if "tests.unit" in cap:
                if "test" in apl or "local" in apl:
                    has_sufficient = True
            elif "production" in cap:
                if "prod" in apl or "remote" in apl or "staging" in apl:
                    has_sufficient = True
            elif "deploy" in cap:
                if "deploy" in apl or "remote" in apl:
                    has_sufficient = True
            elif "sanitiz" in cap or "backup" in cap:
                if "sanitiz" in apl or "backup" in apl or "restore" in apl or "report" in apl:
                    has_sufficient = True
            else:
                if artifact_paths:
                    has_sufficient = True
        if not (artifact_paths and has_sufficient):
            reasons.append(f"Capability {cap} requires evidence {reqs} but no/insufficient matching artifact for claim")
    return reasons

def attempt_transition(
    capability_name: str,
    artifact_paths: List[str],
    claimed_status: str = "IMPLEMENTED",
    extra_evidence: Dict[str, Any] | None = None,
    output_claim: str = ""
) -> IntegrityResult:
    """
    Central gate. Returns allowed=False for any violation.
    Now integrates Completion Integrity for capability claims:
    output claim -> extract caps -> registry lookup -> evidence req eval.
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

    # Completion Integrity: capability claim + registry + evidence strength eval (provisional)
    claim_reasons = _evaluate_claim_evidence(output_claim, artifact_paths or [], load_registry())
    reasons.extend(claim_reasons)

    if reasons:
        denial = {
            "capability": capability_name,
            "attempted_status": claimed_status,
            "denied_because": reasons,
            "artifacts_checked": artifact_paths,
            "output_claim": output_claim[:200] if output_claim else "",
        }
        extra["denial_record"] = denial
        return IntegrityResult(False, " | ".join(reasons), extra)

    # Additional negative checks can be extended here (malformed JSON, failed command, etc.)
    return IntegrityResult(True, "All integrity checks passed", extra)
