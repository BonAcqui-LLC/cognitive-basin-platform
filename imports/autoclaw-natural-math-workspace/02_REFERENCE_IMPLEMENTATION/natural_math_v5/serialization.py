"""Natural Math v5 reference implementation — serialization.

Frozen spec: JSON output format for oracle verification.
"""

from __future__ import annotations

import json
from typing import Any


def nodes_to_json(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialize nodes to JSON-safe format.

    Converts tuples to lists, sets to sorted lists, and ensures
    all values are JSON-serializable.
    """
    result = []
    for node in nodes:
        record = {}
        for key, value in node.items():
            if isinstance(value, tuple):
                record[key] = list(value)
            elif isinstance(value, set):
                record[key] = sorted(value)
            elif isinstance(value, bool):
                record[key] = value
            elif isinstance(value, int):
                record[key] = value
            elif value is None:
                record[key] = value
            else:
                record[key] = str(value)
        result.append(record)
    return result


def to_json(data: Any) -> str:
    """Serialize to JSON string with determinism."""
    return json.dumps(data, sort_keys=True, indent=None, separators=(",", ":"))


def cluster_to_json(result: dict[str, Any]) -> dict[str, Any]:
    """Serialize cluster run result to JSON-safe format."""
    return {
        "nodes": nodes_to_json(result["nodes"]),
        "resource_pos": list(result["resource_pos"]),
        "seed": result["seed"],
        "steps": result["steps"],
        "final_metrics": {
            k: (list(v) if isinstance(v, tuple) else v)
            for k, v in result["final_metrics"].items()
        },
        "passed": result["passed"],
    }
