"""
Persistent worker process for BasinLab.

The worker keeps a single Python namespace alive across action executions and
communicates over line-delimited JSON.
"""

from __future__ import annotations

import base64
import io
import json
import os
import pickle
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, Tuple


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "NameError": NameError,
    "RuntimeError": RuntimeError,
    "ZeroDivisionError": ZeroDivisionError,
}

MAX_PICKLE_BYTES = 262144
MAX_TEXT_CHARS = 8192


def _make_namespace() -> Dict[str, Any]:
    return {"__builtins__": SAFE_BUILTINS}


SESSION_NAMESPACE: Dict[str, Any] = _make_namespace()


def _trim_text(text: str) -> Tuple[str, bool]:
    if len(text) <= MAX_TEXT_CHARS:
        return text, False
    suffix = "\n...[truncated by BasinLab worker]"
    return text[: MAX_TEXT_CHARS - len(suffix)] + suffix, True


def _summarize_value(value: Any) -> str:
    text = repr(value)
    if len(text) > 160:
        text = text[:157] + "..."
    return text


def _serialize_value(value: Any) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    summary = {
        "type_name": type(value).__name__,
        "repr_text": _summarize_value(value),
        "serializable": False,
        "serialized_bytes": 0,
    }
    try:
        payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        return None, summary
    if len(payload) > MAX_PICKLE_BYTES:
        return None, summary
    summary["serializable"] = True
    summary["serialized_bytes"] = len(payload)
    return (
        {
            "encoding": "pickle+base64",
            "payload": base64.b64encode(payload).decode("ascii"),
            "summary": summary["repr_text"],
        },
        summary,
    )


def _deserialize_value(entry: Dict[str, Any]) -> Any:
    payload = base64.b64decode(entry["payload"].encode("ascii"))
    return pickle.loads(payload)


def _tracked_state() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    serialized: Dict[str, Dict[str, Any]] = {}
    summaries: Dict[str, Dict[str, Any]] = {}
    for name, value in SESSION_NAMESPACE.items():
        if name.startswith("_") or name == "__builtins__":
            continue
        encoded, summary = _serialize_value(value)
        summaries[name] = summary
        if encoded is not None:
            serialized[name] = encoded
    return serialized, summaries


def _state_fingerprint(summary: Dict[str, Any], serialized: Dict[str, Any] | None) -> str:
    if serialized is not None:
        return serialized["payload"]
    return json.dumps(summary, sort_keys=True)


def _diff(
    before_serialized: Dict[str, Dict[str, Any]],
    before_summary: Dict[str, Dict[str, Any]],
    after_serialized: Dict[str, Dict[str, Any]],
    after_summary: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    before_keys = set(before_summary)
    after_keys = set(after_summary)
    updated = []
    for name in sorted(before_keys & after_keys):
        if _state_fingerprint(before_summary[name], before_serialized.get(name)) != _state_fingerprint(
            after_summary[name], after_serialized.get(name)
        ):
            updated.append(name)
    return {
        "created": sorted(after_keys - before_keys),
        "updated": updated,
        "deleted": sorted(before_keys - after_keys),
    }


def _handle_execute(message: Dict[str, Any]) -> Dict[str, Any]:
    code = message["code"]
    started = time.perf_counter()
    before_serialized, before_summary = _tracked_state()
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    exception_type = ""
    condensed_traceback = ""

    try:
        compiled = compile(code, "<basinlab-action>", "exec")
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(compiled, SESSION_NAMESPACE, SESSION_NAMESPACE)
    except Exception as exc:
        exception_type = type(exc).__name__
        condensed_traceback = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__, limit=6)
        )

    after_serialized, summaries = _tracked_state()
    stdout, stdout_truncated = _trim_text(stdout_buffer.getvalue())
    stderr, stderr_truncated = _trim_text(stderr_buffer.getvalue())
    trimmed_traceback, traceback_truncated = _trim_text(condensed_traceback)
    duration_s = time.perf_counter() - started
    return {
        "ok": True,
        "stdout": stdout,
        "stderr": stderr,
        "exception_type": exception_type,
        "traceback": trimmed_traceback,
        "duration_s": duration_s,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "traceback_truncated": traceback_truncated,
        "namespace_diff": _diff(before_serialized, before_summary, after_serialized, summaries),
        "namespace_summary": summaries,
        "snapshot": after_serialized,
    }


def _handle_restore(message: Dict[str, Any]) -> Dict[str, Any]:
    SESSION_NAMESPACE.clear()
    SESSION_NAMESPACE.update(_make_namespace())
    for name, entry in message.get("snapshot", {}).items():
        SESSION_NAMESPACE[name] = _deserialize_value(entry)
    _, summaries = _tracked_state()
    return {"ok": True, "namespace_summary": summaries}


def _handle_load_bindings(message: Dict[str, Any]) -> Dict[str, Any]:
    for name, entry in message.get("bindings", {}).items():
        SESSION_NAMESPACE[name] = _deserialize_value(entry)
    _, summaries = _tracked_state()
    return {"ok": True, "namespace_summary": summaries}


def _dispatch(message: Dict[str, Any]) -> Dict[str, Any]:
    op = message.get("op")
    if op == "start":
        _, summaries = _tracked_state()
        return {"ok": True, "pid": os.getpid(), "namespace_summary": summaries}
    if op == "execute":
        return _handle_execute(message)
    if op == "inspect_namespace":
        _, summaries = _tracked_state()
        return {"ok": True, "namespace_summary": summaries}
    if op == "snapshot":
        snapshot, summaries = _tracked_state()
        return {"ok": True, "snapshot": snapshot, "namespace_summary": summaries}
    if op == "restore":
        return _handle_restore(message)
    if op == "load_bindings":
        return _handle_load_bindings(message)
    if op == "reset":
        SESSION_NAMESPACE.clear()
        SESSION_NAMESPACE.update(_make_namespace())
        return {"ok": True}
    if op == "crash":
        raise RuntimeError("Intentional BasinLab test crash")
    if op == "close":
        return {"ok": True, "closing": True}
    return {"ok": False, "error": f"Unknown op: {op}"}


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = _dispatch(message)
        except Exception as exc:
            response = {
                "ok": False,
                "error": f"worker protocol failure: {type(exc).__name__}: {exc}",
            }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
        if response.get("closing"):
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
