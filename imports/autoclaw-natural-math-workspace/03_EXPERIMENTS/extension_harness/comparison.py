"""Extension Harness — deep result comparison utilities."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .serialization import serialize_run_output


def deep_equal(a: Any, b: Any) -> bool:
    """Recursive deep equality check."""
    if type(a) is not type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a == b
        return False

    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(deep_equal(a[k], b[k]) for k in a)

    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(deep_equal(x, y) for x, y in zip(a, b))

    if isinstance(a, set):
        try:
            return sorted(a, key=str) == sorted(b, key=str)
        except TypeError:
            return a == b

    if isinstance(a, bytes):
        return a == b

    return a == b


def structured_diff(a: Any, b: Any, path: str = "") -> list[dict[str, Any]]:
    """Generate structured difference records."""
    diffs: list[dict[str, Any]] = []

    if type(a) is not type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a != b:
                diffs.append({"path": path or "(root)", "type": "value_mismatch",
                              "a_value": a, "b_value": b})
            return diffs
        diffs.append({"path": path or "(root)", "type": "type_mismatch",
                      "a_type": type(a).__name__, "b_type": type(b).__name__,
                      "a_value": _safe_repr(a), "b_value": _safe_repr(b)})
        return diffs

    if isinstance(a, dict):
        ak, bk = set(a.keys()), set(b.keys())
        for k in sorted(ak - bk):
            diffs.append({"path": _jp(path, k), "type": "key_missing",
                         "side": "b", "a_value": _safe_repr(a[k])})
        for k in sorted(bk - ak):
            diffs.append({"path": _jp(path, k), "type": "key_extra",
                         "side": "b", "b_value": _safe_repr(b[k])})
        for k in sorted(ak & bk):
            diffs.extend(structured_diff(a[k], b[k], _jp(path, k)))
        return diffs

    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            diffs.append({"path": path or "(root)", "type": "length_mismatch",
                         "a_length": len(a), "b_length": len(b)})
        for i in range(min(len(a), len(b))):
            diffs.extend(structured_diff(a[i], b[i], _jp(path, f"[{i}]")))
        return diffs

    if isinstance(a, set):
        try:
            sa, sb = sorted(a, key=str), sorted(b, key=str)
        except TypeError:
            if a != b:
                diffs.append({"path": path or "(root)", "type": "value_mismatch",
                             "a_value": _safe_repr(a), "b_value": _safe_repr(b)})
            return diffs
        if sa != sb:
            diffs.append({"path": path or "(root)", "type": "value_mismatch",
                         "a_value": sa, "b_value": sb})
        return diffs

    if a != b:
        diffs.append({"path": path or "(root)", "type": "value_mismatch",
                     "a_value": a, "b_value": b})
    return diffs


def hash_result(result: Any) -> str:
    """Deterministic SHA-256 hash of a harness result."""
    s = serialize_run_output(result)
    return hashlib.sha256(
        json.dumps(s, sort_keys=True, indent=None, separators=(",", ":"))
        .encode("utf-8")
    ).hexdigest()


def _jp(base: str, seg: str) -> str:
    if not base:
        return str(seg)
    if seg.startswith("["):
        return base + seg
    return f"{base}.{seg}"


def _safe_repr(value: Any) -> str:
    s = repr(value)
    return s[:197] + "..." if len(s) > 200 else s
