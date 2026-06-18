"""
Connector hardening unit tests.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from python.cognitive_basin.connectors import ConnectorOperation, ConnectorRequest, ConnectorScope, build_default_registry


def _request(connector_id: str, operation: str, scope: ConnectorScope, payload: dict, *, permit_id: str = "") -> ConnectorRequest:
    return ConnectorRequest(
        request_id="req-test",
        session_id="test-session",
        connector_id=connector_id,
        operation=operation,
        scope=scope,
        payload=payload,
        permit_id=permit_id,
    )


def test_local_filesystem_rejects_path_escape_patterns(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "build").mkdir()
    approved = workspace / "approved.txt"
    approved.write_text("approved", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    registry = build_default_registry(workspace)

    with pytest.raises(ValueError):
        registry.execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(workspace / ".." / "outside.txt")}))
    with pytest.raises(ValueError):
        registry.execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(outside)}))
    with pytest.raises(ValueError):
        registry.execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": "NUL"}))

    symlink = workspace / "build" / "escape.txt"
    try:
        symlink.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation is unavailable in this environment")
    with pytest.raises(ValueError):
        registry.execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(symlink)}))

    if os.name == "nt":
        with pytest.raises(ValueError):
            registry.execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(Path(str(workspace).upper()) / "MISSING.TXT")}))

    with pytest.raises(ValueError):
        registry.execute(_request("local-filesystem", ConnectorOperation.READ_TEXT.value, ConnectorScope.READ_ONLY, {"path": str(approved), "max_bytes": 2}))


def test_local_filesystem_write_requires_permit_and_allows_approved_write(tmp_path):
    workspace = tmp_path / "workspace"
    build = workspace / "build"
    workspace.mkdir()
    build.mkdir()
    writable = build / "write.txt"
    registry = build_default_registry(workspace)

    with pytest.raises(ValueError):
        registry.execute(_request("local-filesystem", ConnectorOperation.WRITE_TEXT.value, ConnectorScope.WRITE, {"path": str(writable), "content": "x"}))

    response = registry.execute(
        _request(
            "local-filesystem",
            ConnectorOperation.WRITE_TEXT.value,
            ConnectorScope.WRITE,
            {"path": str(writable), "content": "allowed"},
            permit_id="permit-123",
        )
    )
    assert response.ok is True
    assert writable.read_text(encoding="utf-8") == "allowed"


def test_generic_http_blocks_unallowlisted_hosts_and_write_without_permit(tmp_path):
    registry = build_default_registry(tmp_path)
    with pytest.raises(ValueError):
        registry.execute(_request("generic-http", ConnectorOperation.HTTP_GET.value, ConnectorScope.READ_ONLY, {"url": "https://bad.example/health"}))

    response = registry.execute(
        _request("generic-http", ConnectorOperation.HTTP_WRITE.value, ConnectorScope.WRITE, {"url": "https://status.project.local/write"})
    )
    assert response.ok is False
    assert response.receipt is not None
    assert response.receipt.status == "WRITE_HELD"
