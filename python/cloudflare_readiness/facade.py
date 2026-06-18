"""
Worker-compatible facade over the local EphUX contracts.
"""

from __future__ import annotations

from typing import Any, Dict

from python.ephux_local.service import EphuxLocalService


class CloudflareReadyFacade:
    def __init__(self, service: EphuxLocalService) -> None:
        self.service = service

    def route_manifest(self) -> Dict[str, Any]:
        return {
            "worker_compatible": True,
            "routes": [
                "GET /health",
                "GET /capabilities",
                "GET /connectors",
                "POST /activation",
                "POST /guardian/intake",
                "POST /sessions",
                "GET /sessions/{id}",
                "POST /sessions/{id}/actions",
                "POST /sessions/{id}/evidence",
                "POST /sessions/{id}/claims",
                "POST /sessions/{id}/commit",
                "POST /sessions/{id}/hold",
                "POST /sessions/{id}/retract",
                "GET /sessions/{id}/events",
                "GET /sessions/{id}/report",
                "GET /sessions/{id}/memory",
                "GET /sessions/{id}/narrative",
                "POST /sessions/{id}/labs/evaluation",
                "POST /sessions/{id}/labs/natural-math",
                "GET /sessions/{id}/labs",
                "GET /sessions/{id}/external-actions",
                "POST /sessions/{id}/external-actions",
            ],
        }

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "service": "cloudflare_readiness", "backing_service": "ephux_local"}

    def capabilities(self) -> Dict[str, Any]:
        return self.service.capabilities()

    def connectors(self) -> Dict[str, Any]:
        return {"connectors": self.service.list_connectors()}

    def activation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.service.activation(payload)

    def create_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.service.create_session(payload)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self.service.get_session(session_id)

    def external_actions(self, session_id: str) -> Dict[str, Any]:
        return self.service.list_external_actions(session_id)
