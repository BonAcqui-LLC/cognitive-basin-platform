"""
End-to-end local EphUX acceptance runner.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .service import LocalServiceConfig, start_service_in_thread


def _request(
    base_url: str,
    token: str,
    method: str,
    path: str,
    payload: Dict[str, Any] | None = None,
    *,
    timeout_s: float = 30.0,
) -> Tuple[int, str]:
    data = None
    headers = {"X-Ephux-Token": token}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config = LocalServiceConfig(port=0, store_dir=root / "store", report_dir=root / "reports")
        app, server, thread = start_service_in_thread(config)
        try:
            host, port = server.server_address
            base_url = f"http://{host}:{port}"

            results: List[Dict[str, Any]] = []

            status, body = _request(base_url, config.token, "POST", "/guardian/intake", {"text": "Browser selected text"})
            intake = json.loads(body)
            session_id = intake["session_id"]
            results.append({"scenario": "browser_text_intake", "passed": status == 201 and intake["intake_state"] == "ACCEPTED"})

            status, body = _request(base_url, config.token, "POST", "/activation", {"purpose": "Anchor purpose", "provider_preference": "scripted"})
            activation = json.loads(body)
            results.append({"scenario": "activation_anchor", "passed": status == 201 and bool(activation["selected_next_action"])})

            status, body = _request(base_url, config.token, "POST", "/guardian/intake", {"session_id": session_id, "text": "<script>alert(1)</script>"})
            held_intake = json.loads(body)
            results.append({"scenario": "unsafe_intake_held", "passed": held_intake["intake_state"] == "HELD"})

            status, body = _request(base_url, config.token, "POST", f"/sessions/{session_id}/claims", {"statement": "This is a contradiction", "contradictory_evidence": ["scan mismatch"]})
            contradicted = json.loads(body)
            results.append({"scenario": "contradiction_retract", "passed": contradicted["final_basin"]["action"] == "RETRACT"})

            status, body = _request(base_url, config.token, "POST", f"/sessions/{session_id}/hold", {"reason": "Need evidence", "required_evidence": ["proof-1"]})
            held = json.loads(body)
            results.append({"scenario": "hold_in_ui", "passed": held["final_basin"]["action"] == "HOLD"})

            status, body = _request(base_url, config.token, "POST", f"/sessions/{session_id}/evidence", {"detail": "proof-1", "temporary_artifact_text": "proof-1"})
            _ = json.loads(body)
            status, body = _request(base_url, config.token, "POST", f"/sessions/{session_id}/claims", {"statement": "Now supported", "supporting_evidence": ["proof-1"]})
            released = json.loads(body)
            results.append({"scenario": "valid_evidence_clears_hold", "passed": released["final_basin"]["action"] == "EXTEND"})

            status, body = _request(base_url, config.token, "POST", f"/sessions/{session_id}/commit", {"summary": "Bad completion", "completion_claim": "Deployment verified."})
            rejected_commit = json.loads(body)
            results.append({"scenario": "false_completion_rejected", "passed": rejected_commit["allowed"] is False})

            restart_session = activation["session_id"]
            server.shutdown()
            server.server_close()
            thread.join(timeout=30)
            time.sleep(0.2)
            app, server, thread = start_service_in_thread(
                LocalServiceConfig(host=host, port=port, store_dir=root / "store", report_dir=root / "reports", token=config.token)
            )
            status, body = _request(base_url, config.token, "GET", f"/sessions/{restart_session}")
            reopened = json.loads(body)
            results.append({"scenario": "restart_persistence", "passed": status == 200 and reopened["session_id"] == restart_session})

            status, body = _request(base_url, config.token, "GET", f"/sessions/{restart_session}/report")
            report = json.loads(body)
            results.append({"scenario": "report_path", "passed": status == 200 and report["html_path"].endswith(".html")})

            status, body = _request(base_url, config.token, "GET", f"/sessions/{restart_session}/report?format=html")
            results.append(
                {
                    "scenario": "report_html",
                    "passed": status == 200 and "<script>" not in body and restart_session in body,
                }
            )

            status, body = _request(base_url, config.token, "POST", f"/sessions/{restart_session}/labs/evaluation", {"requested_by": "acceptance"})
            evaluation = json.loads(body)
            results.append({"scenario": "evaluation_lab_surface", "passed": status == 200 and evaluation["summary"]["passed"] is True})

            status, body = _request(base_url, config.token, "POST", f"/sessions/{restart_session}/labs/natural-math", {"requested_by": "acceptance"})
            natural_math = json.loads(body)
            results.append(
                {
                    "scenario": "natural_math_lab_surface",
                    "passed": status == 200 and natural_math["summary"]["parameter_sweep"]["run_count"] == 3,
                }
            )

            status, body = _request(base_url, config.token, "POST", "/activation", {"purpose": "Natural Math", "provider_preference": "vibethinker"})
            provider_state = json.loads(body)
            results.append({"scenario": "provider_unavailable", "passed": "Provider unavailable" in " ".join(provider_state["capability_limitations"])})

            status, body = _request(base_url, config.token, "GET", "/capabilities")
            caps = json.loads(body)
            results.append({"scenario": "extension_contract", "passed": caps["security_controls"]["local_token"] == "ENFORCED"})

            summary = {"passed": all(item["passed"] for item in results), "scenario_count": len(results), "results": results}
            if artifact_dir:
                path = Path(artifact_dir)
                path.mkdir(parents=True, exist_ok=True)
                (path / "ephux-local-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            return summary
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=30)
            time.sleep(0.2)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args(argv)
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1
