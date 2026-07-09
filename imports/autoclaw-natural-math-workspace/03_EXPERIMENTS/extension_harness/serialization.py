"""Extension Harness — deterministic output serialization."""

from __future__ import annotations

from typing import Any


def _normalize_node(node: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for key, value in node.items():
        if isinstance(value, tuple):
            record[key] = list(value)
        elif isinstance(value, set):
            record[key] = sorted(value)
        elif isinstance(value, (bool, int, type(None))):
            record[key] = value
        else:
            record[key] = str(value)
    return record


def serialize_run_output(result: Any) -> dict[str, Any]:
    """Serialize a run result to a deterministic JSON-safe dict."""
    if isinstance(result, list):
        if result and isinstance(result[0], dict) and "id" in result[0]:
            return {
                "type": "local_nodes",
                "node_count": len(result),
                "nodes": sorted(
                    [_normalize_node(n) for n in result],
                    key=lambda n: n["id"],
                ),
            }

    if isinstance(result, dict):
        if "nodes" in result and "metrics" in result:
            return {
                "type": "cluster_result",
                "node_count": len(result["nodes"]),
                "nodes": sorted(
                    [_normalize_node(n) for n in result["nodes"]],
                    key=lambda n: n["id"],
                ),
                "resource_pos": (
                    list(result["resource_pos"])
                    if isinstance(result["resource_pos"], tuple)
                    else result["resource_pos"]
                ),
                "resource_left": result.get("resource_left"),
                "resource_reached": result.get("resource_reached"),
                "metrics": _normalize_metrics(result.get("metrics", {})),
                "passed": result.get("passed"),
            }
        if "result" in result:
            inner = serialize_run_output(result["result"])
            return {"type": "harness_output", "mode": result.get("mode"), "result": inner}

    try:
        return {"type": "unknown", "value": str(result)}
    except Exception:
        return {"type": "unknown", "value": "<unserializable>"}


def _normalize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in sorted(metrics.items()):
        if isinstance(v, tuple):
            out[k] = list(v)
        elif isinstance(v, (int, float, bool, str, type(None))):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def serialize_ab_report(report: dict[str, Any]) -> dict[str, Any]:
    """Serialize an A/B comparison report."""
    s: dict[str, Any] = {"arms_equal": report.get("arms_equal", False)}
    if "arm_a" in report:
        s["arm_a"] = {"mode": report["arm_a"].get("mode"),
                       "provenance": report["arm_a"].get("provenance", {})}
    if "arm_b" in report:
        s["arm_b"] = {"mode": report["arm_b"].get("mode"),
                      "provenance": report["arm_b"].get("provenance", {}),
                      "hook_event_count": len(report["arm_b"].get("hook_events", []))}
    if "comparison" in report:
        c = report["comparison"]
        s["comparison"] = {"equal": c.get("equal"), "diff_count": len(c.get("diffs", [])),
                           "hash_a": c.get("hash_a"), "hash_b": c.get("hash_b")}
    return s
