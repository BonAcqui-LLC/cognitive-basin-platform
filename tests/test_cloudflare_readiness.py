"""
Cloudflare-compatible facade tests.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from python.cloudflare_readiness.facade import CloudflareReadyFacade
from python.ephux_local.service import EphuxLocalService, LocalServiceConfig


def test_cloudflare_ready_facade_uses_local_service_contracts():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        service = EphuxLocalService(LocalServiceConfig(port=0, store_dir=root / "store", report_dir=root / "reports"))
        facade = CloudflareReadyFacade(service)

        assert facade.health()["ok"] is True
        assert facade.capabilities()["extension_contract"]["session_external_actions_endpoint"].endswith("/external-actions")
        assert any(route.endswith("/external-actions") for route in facade.route_manifest()["routes"])
        assert facade.connectors()["connectors"]
