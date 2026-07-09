"""Extension Harness — run provenance records."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from typing import Any

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
import natural_math_v5 as nm

from .manifest import ExtensionManifest

HARNESS_ID = "extension_harness_v1"
BASELINE_SHA256 = "e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b"


def create_provenance_record(
    mode: str,
    seed: int | None,
    params: dict[str, Any] | None,
    steps: int,
    extension_manifests: list[ExtensionManifest],
    result_hash: str,
) -> dict[str, Any]:
    """Create a deterministic provenance record for a harness run."""
    ts = time.time()
    record: dict[str, Any] = {
        "provenance_format_version": 1,
        "harness_id": HARNESS_ID,
        "baseline_sha256": BASELINE_SHA256,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
        "mode": mode,
        "seed": seed,
        "steps": steps,
        "params_sha256": _hash_params(params),
        "extension_count": len(extension_manifests),
        "extensions": [_manifest_to_dict(m) for m in extension_manifests],
        "result_sha256": result_hash,
    }
    rh = hashlib.sha256(
        json.dumps(record, sort_keys=True).encode("utf-8")
    ).hexdigest()
    record["provenance_sha256"] = rh
    return record


def _manifest_to_dict(m: ExtensionManifest) -> dict[str, Any]:
    if hasattr(m, "to_dict"):
        return m.to_dict()
    return {
        "extension_id": m.extension_id,
        "extension_name": m.extension_name,
        "extension_version": m.extension_version,
        "status": m.status,
    }


def _hash_params(params: dict[str, Any] | None) -> str:
    if params is None:
        params = nm.default_params()
    n = dict(sorted(params.items()))
    return hashlib.sha256(
        json.dumps(n, sort_keys=True).encode("utf-8")
    ).hexdigest()
