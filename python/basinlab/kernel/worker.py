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


def _make_namespace() -> Dict[str, Any]:
    return {"__builtins__": SAFE_BUILTINS}


SESSION_NAMESPACE: Dict[str, Any] = _make_namespace()


def _summarize_value(value: Any) -> str:
    text = repr(value)
    if len(text) > 160:
        text = text[:157] + "..."
    return f"{type(value).__name__}: {text}"


def _serialize_value(value: Any) -> Dict[str, str] | None:
    try:
        payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        return None
    if len(payload) > MAX_PICKLE_BYTES:
        return None
    return {
        "encoding": "pickle+base64",
        "payload": base64.b64encode(payload).decode("ascii"),
        "summary": _summarize_value(value),
    }


def _deserialize_value(entry: Dict[str, str]) -> Any:
    payload = base64.b64decode(entry["payload"].encode("ascii"))
    return pickle.loads(payload)


def _tracked_state() -> Tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    serialized: Dict[str, Dict[str, str]] = {}
    summaries: Dict[str, str] = {}
    for name, value in SESSION_NAMESPACE.items():
        if name.startswith("_") or name == "__builtins__":
            continue
        summaries[name] = _summarize_value(value)
        encoded = _serialize_value(value)
        if encoded is not None:
            serialized[name] = encoded
    return serialized, summaries


def _diff(before: Dict[str, Dict[str, str]], after: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    before_keys = set(before)
    after_keys = set(after)
    updated = []
    for name in sorted(before_keys & after_keys):
        if before[name]["payload"] != after[name]["payload"]:
            updated.append(name)
    return {
        "created": sorted(after_keys - before_keys),
        "updated": updated,
        "deleted": sorted(before_keys - after_keys),
    }


def _handle_execute(message: Dict[str, Any]) -> Dict[str, Any]:
    code = message["code"]
    started = time.perf_counter()
    before_state, _ = _tracked_state()
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

    after_state, summaries = _tracked_state()
    duration_s = time.perf_counter() - started
    return {
        "ok": True,
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_buffer.getvalue(),
        "exception_type": exception_type,
        "traceback": condensed_traceback,
        "duration_s": duration_s,
        "namespace_diff": _diff(before_state, after_state),
        "namespace_summary": summaries,
        "snapshot": after_state,
    }


def _handle_restore(message: Dict[str, Any]) -> Dict[str, Any]:
    SESSION_NAMESPACE.clear()
    SESSION_NAMESPACE.update(_make_namespace())
    for name, entry in message.get("snapshot", {}).items():
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
        snapshot, _ = _tracked_state()
        return {"ok": True, "snapshot": snapshot}
    if op == "restore":
        return _handle_restore(message)
    if op == "reset":
        SESSION_NAMESPACE.clear()
        SESSION_NAMESPACE.update(_make_namespace())
        return {"ok": True}
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
