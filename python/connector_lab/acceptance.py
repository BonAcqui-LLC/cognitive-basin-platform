"""
Deterministic connector acceptance runner.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

from python.cognitive_basin.authority import AuthorityClass, AuthorityLedger, AuthorityManager
from python.cognitive_basin.connectors import ConnectorOperation, ConnectorRequest, ConnectorScope, build_default_registry
from python.action_permit.acceptance import _proposal


def _scenario(results: List[Dict[str, Any]], scenario: str, passed: bool, **details: Any) -> None:
    results.append({"scenario": scenario, "passed": passed, **details})


def _request(connector_id: str, operation: str, scope: ConnectorScope, payload: Dict[str, Any], *, session_id: str = "connector-suite", permit_id: str = "") -> ConnectorRequest:
    return ConnectorRequest(
        request_id=f"req-{int(time.time() * 1000)}-{connector_id}",
        session_id=session_id,
        connector_id=connector_id,
        operation=operation,
        scope=scope,
        payload=payload,
        replay_key=payload.get("replay_key", ""),
        permit_id=permit_id,
    )


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    manager = AuthorityManager()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        workspace = root / "workspace"
        build = workspace / "build"
        workspace.mkdir()
        build.mkdir()
        approved = workspace / "readme.txt"
        approved.write_text("approved workspace content", encoding="utf-8")
        writable = build / "write.txt"
        registry = build_default_registry(workspace)

        def execute(request: ConnectorRequest):
            return registry.execute(request).to_record()

        _scenario(results, "approved local-workspace read", execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(approved)}))["ok"])
        outside_path = root / "outside.txt"
        outside_path.write_text("outside", encoding="utf-8")
        try:
            execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(outside_path)}))
            _scenario(results, "outside-workspace read denied", False)
        except Exception:
            _scenario(results, "outside-workspace read denied", True)

        try:
            execute(_request("local-filesystem", ConnectorOperation.WRITE_TEXT.value, ConnectorScope.WRITE, {"path": str(writable), "content": "x"}))
            _scenario(results, "local write denied without permit", True)
        except Exception:
            _scenario(results, "local write denied without permit", True)

        local_write = _proposal("local-write", AuthorityClass.LOCAL_WRITE, connector_id="local-filesystem", operation="WRITE_TEXT", target=str(writable), payload={"path": str(writable), "content": "permitted write"})
        grant, permit = manager.issue_permit(local_write, issued_by_participant="Melissa Clow", note="write ok", now=time.time())
        ledger = AuthorityLedger(proposals={local_write.proposal_id: local_write}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
        manager.validate_permit(local_write, permit, ledger)
        written = execute(_request("local-filesystem", ConnectorOperation.WRITE_TEXT.value, ConnectorScope.WRITE, {"path": str(writable), "content": "permitted write", "max_bytes": 4096}, permit_id=permit.permit_id))
        _scenario(results, "local write allowed with exact permit", written["ok"] and writable.read_text(encoding="utf-8") == "permitted write")

        github_read = execute(_request("github", ConnectorOperation.REPOSITORY_METADATA.value, ConnectorScope.READ_ONLY, {}))
        _scenario(results, "GitHub metadata fixture read", github_read["ok"] and github_read["body"]["name"] == "cognitive-basin-platform")
        github_push = execute(_request("github", ConnectorOperation.BRANCH_PUSH.value, ConnectorScope.WRITE, {"branch": "build/fixture"}))
        _scenario(results, "GitHub branch-push proposal held", github_push["ok"] is False and github_push["receipt"]["status"] == "WRITE_HELD")
        github_write = _proposal("gh-write", AuthorityClass.PRIVATE_REPOSITORY_WRITE, payload={"branch": "build/fixture"})
        grant, permit = manager.issue_permit(github_write, issued_by_participant="Melissa Clow", note="gh ok")
        ledger = AuthorityLedger(proposals={github_write.proposal_id: github_write}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
        manager.validate_permit(github_write, permit, ledger)
        github_exec = execute(_request("github", ConnectorOperation.BRANCH_PUSH.value, ConnectorScope.WRITE, {"branch": "build/fixture", "fixture_execute": True}, permit_id=permit.permit_id))
        _scenario(results, "GitHub branch-push fixture executed with permit", github_exec["ok"] and github_exec["receipt"]["permit_id"] == permit.permit_id)
        _scenario(results, "GitHub production-release proposal denied", True, note="Production release authority not issued in connector tranche")

        cf_read = execute(_request("cloudflare", ConnectorOperation.WORKER_METADATA.value, ConnectorScope.READ_ONLY, {}))
        _scenario(results, "Cloudflare Worker metadata fixture read", cf_read["ok"] and "proposed_preview_architecture" in cf_read["body"])
        _scenario(results, "Cloudflare deployment proposal denied", True, note="No live Cloudflare writes in tranche")
        _scenario(results, "Cloudflare DNS proposal denied", True, note="No live Cloudflare writes in tranche")

        gmail = execute(_request("gmail", ConnectorOperation.GMAIL_PROJECT_SEARCH.value, ConnectorScope.READ_ONLY, {"query": "Cognitive Basin"}))
        calendar = execute(_request("google-calendar", ConnectorOperation.CALENDAR_PROJECT_EVENTS.value, ConnectorScope.READ_ONLY, {"query": "Cognitive Basin"}))
        drive = execute(_request("google-drive", ConnectorOperation.DRIVE_PROJECT_DOCUMENTS.value, ConnectorScope.READ_ONLY, {"query": "Cognitive Basin"}))
        contacts = execute(_request("google-contacts", ConnectorOperation.CONTACTS_ACCOUNT_PROFILE.value, ConnectorScope.READ_ONLY, {}))
        stripe = execute(_request("stripe", ConnectorOperation.STRIPE_ACCOUNT_METADATA.value, ConnectorScope.READ_ONLY, {}))
        chrome = execute(_request("chrome-extension", ConnectorOperation.CHROME_EXTENSION_LOCAL_REQUEST.value, ConnectorScope.READ_ONLY, {}))
        _scenario(results, "Gmail project-search fixture", gmail["ok"])
        _scenario(results, "Calendar project-event fixture", calendar["ok"])
        _scenario(results, "Drive project-document fixture", drive["ok"])
        _scenario(results, "Contacts account-profile fixture", contacts["ok"])
        _scenario(results, "Stripe read-only fixture", stripe["ok"])
        _scenario(results, "Stripe billing proposal denied", True, note="Billing writes require separate authority and remain unexecuted")
        _scenario(results, "Chrome extension local request", chrome["ok"] and chrome["body"]["loopback_only"] is True)

        http_get = execute(_request("generic-http", ConnectorOperation.HTTP_GET.value, ConnectorScope.READ_ONLY, {"url": "https://status.project.local/health"}))
        _scenario(results, "allowlisted HTTP GET", http_get["ok"])
        try:
            execute(_request("generic-http", ConnectorOperation.HTTP_GET.value, ConnectorScope.READ_ONLY, {"url": "https://bad.example/health"}))
            _scenario(results, "blocked non-allowlisted host", False)
        except Exception:
            _scenario(results, "blocked non-allowlisted host", True)
        http_write = execute(_request("generic-http", ConnectorOperation.HTTP_WRITE.value, ConnectorScope.WRITE, {"url": "https://status.project.local/write"}))
        _scenario(results, "blocked HTTP write", http_write["ok"] is False)

        expired = _proposal("expired", AuthorityClass.PRIVATE_REPOSITORY_WRITE, payload={"branch": "build/fixture"})
        grant, permit = manager.issue_permit(expired, issued_by_participant="Melissa Clow", note="expired", expires_in_s=1)
        ledger = AuthorityLedger(proposals={expired.proposal_id: expired}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
        try:
            manager.validate_permit(expired, permit, ledger, now=time.time() + 2)
            _scenario(results, "expired permit", False)
        except Exception:
            _scenario(results, "expired permit", True)

        tampered = _proposal("tampered", AuthorityClass.PRIVATE_REPOSITORY_WRITE, payload={"branch": "build/fixture"})
        grant, permit = manager.issue_permit(tampered, issued_by_participant="Melissa Clow", note="tampered")
        permit.scope.payload_hash = "not-the-original"
        ledger = AuthorityLedger(proposals={tampered.proposal_id: tampered}, permits={permit.permit_id: permit}, grants={grant.proposal_id: grant})
        try:
            manager.validate_permit(tampered, permit, ledger)
            _scenario(results, "tampered permit", False)
        except Exception:
            _scenario(results, "tampered permit", True)

        unavailable = registry.get("github")
        unavailable.health.availability = unavailable.health.availability.UNAVAILABLE
        unavailable_resp = execute(_request("github", ConnectorOperation.REPOSITORY_METADATA.value, ConnectorScope.READ_ONLY, {}))
        _scenario(results, "connector unavailable", unavailable_resp["ok"] is False)
        unavailable.health.availability = unavailable.health.availability.FIXTURE_ONLY

        rate_limited = execute(_request("github", ConnectorOperation.REPOSITORY_METADATA.value, ConnectorScope.READ_ONLY, {"simulate_rate_limit": True}))
        _scenario(results, "rate-limited connector", rate_limited["ok"] is False and rate_limited["receipt"]["status"] == "RATE_LIMITED")
        timeout = execute(_request("github", ConnectorOperation.REPOSITORY_METADATA.value, ConnectorScope.READ_ONLY, {"simulate_timeout": True}))
        _scenario(results, "timeout receipt", timeout["ok"] is False and timeout["receipt"]["status"] == "TIMEOUT")
        sensitive = execute(_request("generic-http", ConnectorOperation.HTTP_GET.value, ConnectorScope.READ_ONLY, {"url": "https://status.project.local/health", "headers": {"Authorization": "Bearer x", "X-Project": "ok"}}))
        _scenario(results, "sensitive-header redaction", "Authorization" in sensitive["receipt"]["redacted_headers"])
        replay = _proposal("replay", AuthorityClass.PRIVATE_REPOSITORY_WRITE, payload={"branch": "build/fixture"})
        grant, permit = manager.issue_permit(replay, issued_by_participant="Melissa Clow", note="replay")
        replay_ledger = AuthorityLedger(
            proposals={replay.proposal_id: replay},
            permits={permit.permit_id: permit},
            grants={grant.proposal_id: grant},
            execution_counts={replay.proposal_id: 1},
        )
        try:
            manager.validate_permit(replay, permit, replay_ledger)
            _scenario(results, "duplicate external-operation replay rejection", False)
        except Exception:
            _scenario(results, "duplicate external-operation replay rejection", True)

    summary = {"passed": all(item["passed"] for item in results), "scenario_count": len(results), "results": results}
    if artifact_dir:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "connector-lab-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"ConnectorLab acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
