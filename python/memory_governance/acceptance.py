"""
Deterministic governed-memory acceptance runner.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

from python.ephux_local.service import EphuxLocalService, LocalServiceConfig


ROOT = Path(__file__).resolve().parents[2]


def _current_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _participant_payload(participant: str) -> Dict[str, Any]:
    return {
        "participant": participant,
        "participant_mode": "explicit",
        "participant_source": "explicit",
    }


def _assert_scenario(results: List[Dict[str, Any]], scenario: str, passed: bool, **details: Any) -> None:
    results.append({"scenario": scenario, "passed": passed, **details})


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    artifact_root = Path(artifact_dir) if artifact_dir else None
    if artifact_root:
        artifact_root.mkdir(parents=True, exist_ok=True)

    commit = _current_commit()
    limitations = [
        "Governed memory remains session-scoped in the current tranche.",
        "Deletion requests are review-gated and do not auto-delete records.",
        "Legal holds are preservative only; release workflow is not yet implemented.",
    ]
    started = time.time()
    results: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        service = EphuxLocalService(LocalServiceConfig(port=0, store_dir=root / "store", report_dir=root / "reports"))

        session = service.create_session({"purpose": "memory governance routing", "privacy_setting": "shared-project"})
        session_id = session["session_id"]

        service.add_evidence(
            session_id,
            {
                "detail": "inspection report confirms routing corridor",
                "temporary_artifact_text": "inspection report confirms routing corridor",
                "visibility_scope": "PRIVATE_JAMES",
                **_participant_payload("James Clow"),
            },
        )
        james_memory = next(item for item in service.session_memory(session_id, "James Clow")["items"] if item["participant"] == "James Clow")
        _assert_scenario(results, "memory-item creation from evidence", james_memory["memory_id"].startswith("memory-evidence-"), memory_id=james_memory["memory_id"])

        service.add_claim(
            session_id,
            {
                "statement": "routing corridor is supported",
                "supporting_evidence": ["inspection report confirms routing corridor"],
                "visibility_scope": "SHARED_PROJECT",
                **_participant_payload("Melissa Clow"),
            },
        )
        shared_state = service.session_memory(session_id, "UNKNOWN")
        claim_memory = next(item for item in shared_state["items"] if item["participant"] == "Melissa Clow")
        _assert_scenario(results, "memory-item creation from claims", claim_memory["memory_id"].startswith("memory-claim-"), memory_id=claim_memory["memory_id"])

        retrieval = service.retrieve_memory(session_id, {**_participant_payload("Melissa Clow"), "purpose": "routing"})
        _assert_scenario(results, "purpose-aware retrieval", bool(retrieval["retrievals"]) and retrieval["retrievals"][0]["purpose_relevance"] > 0, top=retrieval["retrievals"][0] if retrieval["retrievals"] else {})

        service.add_claim(
            session_id,
            {
                "statement": "routing corridor is unsafe contradiction",
                "contradictory_evidence": ["scan mismatch"],
                "visibility_scope": "SHARED_PROJECT",
                **_participant_payload("Melissa Clow"),
            },
        )
        contradiction_retrieval = service.retrieve_memory(session_id, {**_participant_payload("Melissa Clow"), "purpose": "routing"})
        contradicted_item = next(item for item in service.session_memory(session_id, "Melissa Clow")["items"] if item["contradiction_status"] == "contradicted")
        top_id = contradiction_retrieval["retrievals"][0]["memory_id"] if contradiction_retrieval["retrievals"] else ""
        _assert_scenario(results, "contradiction-aware retrieval", top_id != contradicted_item["memory_id"], top_memory_id=top_id, contradicted_memory_id=contradicted_item["memory_id"])

        service.promote_memory(
            session_id,
            {
                "memory_id": claim_memory["memory_id"],
                "note": "verified-use-1",
                **_participant_payload("Melissa Clow"),
            },
        )
        service.promote_memory(
            session_id,
            {
                "memory_id": claim_memory["memory_id"],
                "note": "verified-use-2",
                **_participant_payload("Melissa Clow"),
            },
        )
        post_promote = next(item for item in service.session_memory(session_id, "Melissa Clow")["items"] if item["memory_id"] == claim_memory["memory_id"])
        _assert_scenario(results, "frequency not becoming truth", post_promote["epistemic_state"] == "SUPPORTED", epistemic_state=post_promote["epistemic_state"])

        service.add_claim(
            session_id,
            {
                "statement": "dramatic but unsupported story",
                "visibility_scope": "SHARED_PROJECT",
                **_participant_payload("Melissa Clow"),
            },
        )
        vivid_item = next(item for item in service.session_memory(session_id, "Melissa Clow")["items"] if item["evidence_status"] == "unresolved")
        _assert_scenario(results, "salience not becoming evidence", vivid_item["epistemic_state"] == "UNRESOLVED", epistemic_state=vivid_item["epistemic_state"])

        promoted = service.promote_memory(
            session_id,
            {
                "memory_id": claim_memory["memory_id"],
                "note": "replay-verified",
                "replay_reference": "replay-1",
                **_participant_payload("Melissa Clow"),
            },
        )
        _assert_scenario(
            results,
            "promotion after verified use",
            len(promoted["memory_item"]["successful_uses"]) >= 3 and bool(promoted["memory_item"]["promotion_history"]),
            memory_item=promoted["memory_item"],
        )

        demoted = service.demote_memory(
            session_id,
            {
                "memory_id": claim_memory["memory_id"],
                "note": "failed-use-path",
                **_participant_payload("Melissa Clow"),
            },
        )
        _assert_scenario(results, "failed-use demotion", "failed-use-path" in demoted["memory_item"]["failed_uses"], memory_item=demoted["memory_item"])

        contradicted = service.demote_memory(
            session_id,
            {
                "memory_id": claim_memory["memory_id"],
                "note": "contradiction-demotion",
                "contradiction_detail": "new contradiction",
                "recovery_route_id": "recovery-route-1",
                **_participant_payload("Melissa Clow"),
            },
        )
        _assert_scenario(results, "contradiction demotion", contradicted["memory_item"]["contradiction_status"] == "contradicted", memory_item=contradicted["memory_item"])

        bundle = service.export_session_bundle(session_id)
        import_root = root / "imported"
        imported_service = EphuxLocalService(LocalServiceConfig(port=0, store_dir=import_root / "store", report_dir=import_root / "reports"))
        imported = imported_service.import_session_bundle(bundle)
        imported_memory = imported_service.session_memory(session_id, "Melissa Clow")
        _assert_scenario(results, "replay survival", len(imported_memory["items"]) >= 3, imported_session=imported["session_id"])

        scar_item = next(item for item in service.session_memory(session_id, "Melissa Clow")["items"] if item["scar_links"])
        _assert_scenario(results, "scar retention", bool(scar_item["scar_links"]), scar_links=scar_item["scar_links"])

        recovery_item = next(item for item in service.session_memory(session_id, "Melissa Clow")["items"] if item["recovery_links"])
        _assert_scenario(results, "recovery-history retention", bool(recovery_item["recovery_links"]), recovery_links=recovery_item["recovery_links"])

        prune_session = service.create_session({"purpose": "retention expiry", "privacy_setting": "shared-project"})
        prune_session_id = prune_session["session_id"]
        service.add_evidence(
            prune_session_id,
            {
                "detail": "temporary working note",
                "temporary_artifact_text": "temporary working note",
                "visibility_scope": "SHARED_PROJECT",
                **_participant_payload("Melissa Clow"),
            },
        )
        prune_item = service.session_memory(prune_session_id, "Melissa Clow")["items"][0]
        pruned = service.prune_memory(
            prune_session_id,
            {
                "memory_id": prune_item["memory_id"],
                "reason": "retention-expiry",
                **_participant_payload("Melissa Clow"),
            },
        )
        _assert_scenario(results, "auditable pruning", pruned["allowed"] is True, prune_result=pruned)

        held_session = service.create_session({"purpose": "legal hold", "privacy_setting": "shared-project"})
        held_session_id = held_session["session_id"]
        service.add_evidence(
            held_session_id,
            {
                "detail": "preserve this note",
                "temporary_artifact_text": "preserve this note",
                "visibility_scope": "SHARED_PROJECT",
                **_participant_payload("James Clow"),
            },
        )
        held_item = service.session_memory(held_session_id, "James Clow")["items"][0]
        hold = service.place_legal_hold(
            held_session_id,
            {
                "target_memory_id": held_item["memory_id"],
                "reason": "litigation hold",
                **_participant_payload("James Clow"),
            },
        )
        blocked_prune = service.prune_memory(
            held_session_id,
            {
                "memory_id": held_item["memory_id"],
                "reason": "cleanup",
                **_participant_payload("James Clow"),
            },
        )
        _assert_scenario(results, "legal-hold preservation", hold["status"] == "ACTIVE" and blocked_prune["allowed"] is False, prune_result=blocked_prune)

        audit_session = service.create_session({"purpose": "audit retention", "privacy_setting": "audit-retained"})
        audit_session_id = audit_session["session_id"]
        service.add_evidence(
            audit_session_id,
            {
                "detail": "audit trail evidence",
                "temporary_artifact_text": "audit trail evidence",
                "visibility_scope": "AUDIT_RETAINED",
                **_participant_payload("Melissa Clow"),
            },
        )
        audit_item = service.session_memory(audit_session_id, "Melissa Clow")["items"][0]
        audit_prune = service.prune_memory(
            audit_session_id,
            {
                "memory_id": audit_item["memory_id"],
                "reason": "cleanup",
                **_participant_payload("Melissa Clow"),
            },
        )
        _assert_scenario(results, "audit-retained preservation", audit_prune["allowed"] is False and audit_prune["reason"] == "audit_retained", prune_result=audit_prune)

        private_view = service.session_memory(session_id, "James Clow")
        melissa_view = service.session_memory(session_id, "Melissa Clow")
        _assert_scenario(results, "private James visibility", any(item["visibility_scope"] == "PRIVATE_JAMES" for item in private_view["items"]) and all(item["visibility_scope"] != "PRIVATE_JAMES" for item in melissa_view["items"]), james_count=len(private_view["items"]), melissa_count=len(melissa_view["items"]))

        service.add_evidence(
            session_id,
            {
                "detail": "Melissa private note",
                "temporary_artifact_text": "Melissa private note",
                "visibility_scope": "PRIVATE_MELISSA",
                **_participant_payload("Melissa Clow"),
            },
        )
        melissa_private = service.session_memory(session_id, "Melissa Clow")
        unknown_view = service.session_memory(session_id, "UNKNOWN")
        _assert_scenario(results, "private Melissa visibility", any(item["visibility_scope"] == "PRIVATE_MELISSA" for item in melissa_private["items"]) and all(item["visibility_scope"] != "PRIVATE_MELISSA" for item in unknown_view["items"]), melissa_count=len(melissa_private["items"]), unknown_count=len(unknown_view["items"]))

        _assert_scenario(results, "shared-project visibility", any(item["visibility_scope"] == "SHARED_PROJECT" for item in unknown_view["items"]), shared_items=unknown_view["items"])

        unknown_narrative = service.add_narrative_contribution(
            session_id,
            {
                "contribution": "Unknown participant note",
                "participant": "",
                "participant_mode": "explicit",
                "participant_source": "explicit",
            },
        )
        _assert_scenario(results, "UNKNOWN participant behavior", "UNKNOWN" in unknown_narrative["participant_histories"], participant_histories=unknown_narrative["participant_histories"])

        secret_session = service.create_session({"purpose": "redacted export", "privacy_setting": "exportable-redacted"})
        secret_session_id = secret_session["session_id"]
        export_fixture = "governed export artifact " * 12
        service.add_evidence(
            secret_session_id,
            {
                "detail": export_fixture,
                "temporary_artifact_text": export_fixture,
                "visibility_scope": "EXPORTABLE_REDACTED",
                **_participant_payload("James Clow"),
            },
        )
        redacted = service.export_privacy(secret_session_id, {**_participant_payload("James Clow")})
        redacted_text = redacted["items"][0]["memory_fragments"][0]["text"]
        _assert_scenario(results, "redacted export", "[redacted-secret]" in redacted_text or len(redacted_text) <= 160, export=redacted)

        tampered = json.loads(json.dumps(bundle))
        tampered["events"][0]["type"] = "tampered"
        tampered_error = ""
        try:
            tampered_root = root / "tampered-import"
            tampered_service = EphuxLocalService(
                LocalServiceConfig(port=0, store_dir=tampered_root / "store", report_dir=tampered_root / "reports")
            )
            tampered_service.import_session_bundle(tampered)
        except ValueError as exc:
            tampered_error = str(exc)
        _assert_scenario(results, "tampered import rejection", "hash mismatch" in tampered_error.lower(), error=tampered_error)

        _assert_scenario(results, "retention expiry", pruned["reason"] == "retention-expiry" and pruned["allowed"] is True, prune_result=pruned)

        deletion = service.request_deletion(
            session_id,
            {
                "target_memory_id": claim_memory["memory_id"],
                "reason": "delete after review",
                **_participant_payload("Melissa Clow"),
            },
        )
        _assert_scenario(results, "deletion request review", deletion["status"] == "PENDING_REVIEW", deletion=deletion)

        service.add_narrative_contribution(
            session_id,
            {**_participant_payload("James Clow"), "contribution": "Architecture lineage", "visibility_scope": "shared-project"},
        )
        service.add_narrative_decision(
            session_id,
            {**_participant_payload("Melissa Clow"), "decision": "Preserve contradiction state", "superseded_decision": "Old package ambiguity", "visibility_scope": "shared-project"},
        )
        service.add_narrative_disagreement(
            session_id,
            {**_participant_payload("Melissa Clow"), "disagreement": "Release scope differs", "unresolved_question": "How broad should automation become?", "visibility_scope": "shared-project"},
        )
        service.add_narrative_commitment(
            session_id,
            {**_participant_payload("James Clow"), "commitment": "Stabilize memory branch", "failure": "CI path bug", "recovery": "Portable helper repair", "visibility_scope": "shared-project"},
        )

        imported_bundle = service.export_session_bundle(session_id)
        narrative_import_root = root / "narrative-import"
        narrative_service = EphuxLocalService(LocalServiceConfig(port=0, store_dir=narrative_import_root / "store", report_dir=narrative_import_root / "reports"))
        narrative_service.import_session_bundle(imported_bundle)
        replayed_narrative = narrative_service.session_narrative(session_id)
        _assert_scenario(results, "TeamNarrative replay", "James Clow" in replayed_narrative["participant_histories"] and "Melissa Clow" in replayed_narrative["participant_histories"], records=replayed_narrative["participant_histories"])
        _assert_scenario(results, "superseded decisions", bool(replayed_narrative["participant_histories"]["Melissa Clow"]["superseded_decisions"]), record=replayed_narrative["participant_histories"]["Melissa Clow"])
        _assert_scenario(results, "unresolved disagreements", bool(replayed_narrative["participant_histories"]["Melissa Clow"]["unresolved_questions"]), record=replayed_narrative["participant_histories"]["Melissa Clow"])
        _assert_scenario(results, "failure and recovery continuity", bool(replayed_narrative["participant_histories"]["James Clow"]["failures"]) and bool(replayed_narrative["participant_histories"]["James Clow"]["recovery_history"]), record=replayed_narrative["participant_histories"]["James Clow"])

        artifacts = {
            "bundle_path": "",
            "summary_path": str((artifact_root / "memory-governance-acceptance-summary.json")) if artifact_root else "",
        }
        summary = {
            "passed": all(item["passed"] for item in results),
            "scenario_count": len(results),
            "results": results,
            "exact_commit": commit,
            "artifacts": artifacts,
            "limitations": limitations,
            "elapsed_s": round(time.time() - started, 3),
        }
        if artifact_root:
            summary_path = artifact_root / "memory-governance-acceptance-summary.json"
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            artifacts["summary_path"] = str(summary_path)
        return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(
        f"MemoryGovernance acceptance: commit={summary['exact_commit']} scenarios={summary['scenario_count']} passed={summary['passed']}"
    )
    for result in summary["results"]:
        print(f"- {result['scenario']}: {'PASS' if result['passed'] else 'FAIL'}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
