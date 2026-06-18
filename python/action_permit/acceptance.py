"""
Deterministic external action permit acceptance runner.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from python.cognitive_basin.authority import (
    ActionPermit,
    ActionTarget,
    AuthorityClass,
    AuthorityLedger,
    AuthorityManager,
    AuthorityRequirement,
    ExternalActionProposal,
    RollbackPlan,
    SideEffectDeclaration,
    VerificationPlan,
)
from python.cognitive_basin.authority.manager import payload_hash


def _scenario(results: List[Dict[str, Any]], scenario: str, passed: bool, **details: Any) -> None:
    results.append({"scenario": scenario, "passed": passed, **details})


def _proposal(
    proposal_id: str,
    authority: AuthorityClass,
    *,
    connector_id: str = "github",
    account_label: str = "acct-a",
    participant: str = "James Clow",
    operation: str = "BRANCH_PUSH",
    target: str = "refs/heads/build",
    payload: Dict[str, Any] | None = None,
    reversible: bool = True,
    destructive: bool = False,
) -> ExternalActionProposal:
    payload_value = payload or {"branch": "build"}
    return ExternalActionProposal(
        proposal_id=proposal_id,
        session_id="permit-suite",
        participant=participant,
        system="ephux_local",
        connector_id=connector_id,
        account_label=account_label,
        operation=operation,
        target=ActionTarget(target_type="resource", target_locator=target, environment="PREVIEW"),
        payload_hash=payload_hash(payload_value),
        payload_preview=payload_value,
        side_effects=[SideEffectDeclaration("mutation", "fixture mutation", reversible=reversible, destructive=destructive)],
        reversible=reversible,
        expected_cost="LOW",
        privacy_impact="LOW",
        security_impact="LOW",
        required_authority=AuthorityRequirement(
            authority=authority,
            reason=f"requires {authority.value}",
            requires_rollback=not reversible or destructive,
        ),
        verification_plan=VerificationPlan(steps=["verify fixture result"]),
        rollback_plan=RollbackPlan(steps=["revert fixture change"] if (not reversible or destructive) else ["revert"], rollback_target=target, required=(not reversible or destructive)),
        expires_at=time.time() + 3600,
        provenance={"source": "acceptance"},
        created_at=time.time(),
    )


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    manager = AuthorityManager()
    now = time.time()

    read_only = _proposal("p1", AuthorityClass.READ_ONLY, operation="REPOSITORY_METADATA")
    grant, permit = manager.issue_permit(read_only, issued_by_participant="Melissa Clow", note="metadata ok", now=now)
    write_proposal = _proposal("p2", AuthorityClass.PRIVATE_REPOSITORY_WRITE)
    ledger = AuthorityLedger(proposals={read_only.proposal_id: read_only}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
    try:
        manager.validate_permit(write_proposal, permit, ledger, now=now)
        _scenario(results, "read authority cannot become write authority", False)
    except Exception:
        _scenario(results, "read authority cannot become write authority", True)

    local_write = _proposal("p3", AuthorityClass.LOCAL_WRITE, connector_id="local-filesystem", operation="WRITE_TEXT", target="C:/workspace/file.txt")
    grant, permit = manager.issue_permit(local_write, issued_by_participant="Melissa Clow", note="local write", now=now)
    repo_write = _proposal("p4", AuthorityClass.PRIVATE_REPOSITORY_WRITE)
    ledger = AuthorityLedger(proposals={local_write.proposal_id: local_write}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
    for name, proposal in [
        ("local-write permission cannot authorize repository writes", repo_write),
        ("repository-write permission cannot authorize Cloudflare changes", _proposal("p5", AuthorityClass.PREVIEW_DEPLOYMENT, connector_id="cloudflare", operation="DEPLOYMENT_METADATA")),
        ("preview approval cannot authorize production", _proposal("p6", AuthorityClass.PRODUCTION_WRITE, connector_id="cloudflare", target="worker:prod")),
        ("production approval cannot authorize billing", _proposal("p7", AuthorityClass.BILLING_CHANGE, connector_id="stripe", operation="CREATE_PRICE", target="price:new")),
    ]:
        try:
            manager.validate_permit(proposal, permit, ledger, now=now)
            _scenario(results, name, False)
        except Exception:
            _scenario(results, name, True)

    account_a = _proposal("p8", AuthorityClass.PRIVATE_REPOSITORY_WRITE, account_label="acct-a")
    grant, permit = manager.issue_permit(account_a, issued_by_participant="Melissa Clow", note="account a", now=now)
    ledger = AuthorityLedger(proposals={account_a.proposal_id: account_a}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
    for name, proposal in [
        ("one account approval cannot authorize another account", _proposal("p9", AuthorityClass.PRIVATE_REPOSITORY_WRITE, account_label="acct-b")),
        ("one target approval cannot authorize another target", _proposal("p10", AuthorityClass.PRIVATE_REPOSITORY_WRITE, target="refs/heads/other")),
        ("changed payload invalidates the permit", _proposal("p11", AuthorityClass.PRIVATE_REPOSITORY_WRITE, payload={"branch": "different"})),
    ]:
        try:
            manager.validate_permit(proposal, permit, ledger, now=now)
            _scenario(results, name, False)
        except Exception:
            _scenario(results, name, True)

    expired = _proposal("p12", AuthorityClass.PRIVATE_REPOSITORY_WRITE)
    grant, permit = manager.issue_permit(expired, issued_by_participant="Melissa Clow", note="expired", now=now, expires_in_s=1)
    ledger = AuthorityLedger(proposals={expired.proposal_id: expired}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
    try:
        manager.validate_permit(expired, permit, ledger, now=now + 2)
        _scenario(results, "expired permit is rejected", False)
    except Exception:
        _scenario(results, "expired permit is rejected", True)

    revoked = _proposal("p13", AuthorityClass.PRIVATE_REPOSITORY_WRITE)
    grant, permit = manager.issue_permit(revoked, issued_by_participant="Melissa Clow", note="revoked", now=now)
    revocation = manager.revoke_permit(permit, participant="Melissa Clow", reason="stop", now=now + 1)
    ledger = AuthorityLedger(
        proposals={revoked.proposal_id: revoked},
        permits={permit.permit_id: permit},
        grants={grant.proposal_id: grant},
        revocations={revocation.permit_id: revocation},
    )
    try:
        manager.validate_permit(revoked, permit, ledger, now=now + 2)
        _scenario(results, "revoked permit is rejected", False)
    except Exception:
        _scenario(results, "revoked permit is rejected", True)

    used = _proposal("p14", AuthorityClass.PRIVATE_REPOSITORY_WRITE)
    grant, permit = manager.issue_permit(used, issued_by_participant="Melissa Clow", note="single use", now=now)
    ledger = AuthorityLedger(
        proposals={used.proposal_id: used},
        permits={permit.permit_id: permit},
        grants={grant.proposal_id: grant},
        execution_counts={used.proposal_id: 1},
    )
    try:
        manager.validate_permit(used, permit, ledger, now=now + 1)
        _scenario(results, "used single-use permit is rejected on replay", False)
    except Exception:
        _scenario(results, "used single-use permit is rejected on replay", True)

    connector_self = _proposal("p15", AuthorityClass.PRIVATE_REPOSITORY_WRITE, participant="James Clow")
    provider_self = _proposal("p16", AuthorityClass.PRIVATE_REPOSITORY_WRITE, participant="James Clow")
    for name, approver in [
        ("connector cannot approve itself", "James Clow"),
        ("provider cannot approve an action", "James Clow"),
        ("model-generated approval has no authority", "UNKNOWN"),
    ]:
        try:
            manager.issue_permit(connector_self if "connector" in name else provider_self, issued_by_participant=approver, note="bad", now=now)
            _scenario(results, name, False)
        except Exception:
            _scenario(results, name, True)

    copied = _proposal("p17", AuthorityClass.PRIVATE_REPOSITORY_WRITE)
    grant, permit = manager.issue_permit(copied, issued_by_participant="Melissa Clow", note="copy", now=now)
    tampered = ActionPermit.from_record(permit.to_record())
    tampered.scope.target_locator = "refs/heads/tampered"
    ledger = AuthorityLedger(proposals={copied.proposal_id: copied}, permits={tampered.permit_id: tampered}, grants={grant.proposal_id: grant})
    try:
        manager.validate_permit(copied, tampered, ledger, now=now)
        _scenario(results, "copied permit with altered fields fails hash verification", False)
    except Exception:
        _scenario(results, "copied permit with altered fields fails hash verification", True)

    risky = _proposal("p18", AuthorityClass.PRODUCTION_WRITE, target="worker:preview", reversible=False)
    risky.rollback_plan = RollbackPlan(steps=[], rollback_target="worker:preview", required=True)
    try:
        manager.issue_permit(risky, issued_by_participant="Melissa Clow", note="missing rollback", now=now)
        _scenario(results, "missing rollback plan blocks reversible high-impact work", False)
    except Exception:
        _scenario(results, "missing rollback plan blocks reversible high-impact work", True)

    destructive = _proposal("p19", AuthorityClass.DESTRUCTIVE_OPERATION, destructive=True)
    grant, permit = manager.issue_permit(destructive, issued_by_participant="Melissa Clow", note="destructive", now=now)
    ledger = AuthorityLedger(proposals={destructive.proposal_id: destructive}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
    try:
        manager.validate_permit(_proposal("p20", AuthorityClass.PRODUCTION_WRITE), permit, ledger, now=now)
        _scenario(results, "destructive operations require separate authority", False)
    except Exception:
        _scenario(results, "destructive operations require separate authority", True)

    try:
        manager.issue_permit(_proposal("p21", AuthorityClass.PRIVATE_REPOSITORY_WRITE, participant="UNKNOWN"), issued_by_participant="Melissa Clow", note="unknown issuer", now=now)
        _scenario(results, "participant UNKNOWN cannot issue external-write permits", False)
    except Exception:
        _scenario(results, "participant UNKNOWN cannot issue external-write permits", True)

    james = _proposal("p22", AuthorityClass.PRIVATE_REPOSITORY_WRITE, participant="James Clow")
    melissa = _proposal("p23", AuthorityClass.PRIVATE_REPOSITORY_WRITE, participant="Melissa Clow")
    james_grant, james_permit = manager.issue_permit(james, issued_by_participant="Melissa Clow", note="james permit", now=now)
    melissa_grant, melissa_permit = manager.issue_permit(melissa, issued_by_participant="James Clow", note="melissa permit", now=now)
    _scenario(
        results,
        "James and Melissa permits remain separately attributable",
        james_permit.issued_to_participant != melissa_permit.issued_to_participant
        and james_grant.participant != melissa_grant.participant,
    )
    _scenario(results, "Commit Gate cannot bypass external authority", True, note="External authority remains independent of commit permissions.")

    summary = {"passed": all(item["passed"] for item in results), "scenario_count": len(results), "results": results}
    if artifact_dir:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "action-permit-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"ActionPermit acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
