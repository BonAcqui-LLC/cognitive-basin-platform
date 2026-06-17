"""
AST-based guardrail checks for BasinLab action code.

These controls are an execution policy layer, not a full security boundary.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List


ENFORCED = "ENFORCED"
BEST_EFFORT = "BEST_EFFORT"
UNSUPPORTED = "UNSUPPORTED"

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
}

FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "pathlib",
    "shutil",
    "requests",
    "urllib",
    "http",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
}

FORBIDDEN_ATTRS = {
    "environ",
    "system",
    "popen",
    "spawn",
    "fork",
    "execv",
    "execve",
    "socket",
    "connect",
    "request",
}


@dataclass
class GuardDecision:
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    controls: Dict[str, str] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "controls": dict(self.controls),
        }


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        current: ast.AST | None = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def inspect_action_code(code: str) -> GuardDecision:
    controls = {
        "separate_process": ENFORCED,
        "restricted_builtins": ENFORCED,
        "import_block": ENFORCED,
        "subprocess_block": ENFORCED,
        "network_block": ENFORCED,
        "filesystem_mutation_block": ENFORCED,
        "memory_limit": BEST_EFFORT,
        "workspace_write_confinement": BEST_EFFORT,
        "orphan_cleanup": BEST_EFFORT,
        "timeout": BEST_EFFORT,
        "process_isolation": UNSUPPORTED,
        "network_egress_runtime": UNSUPPORTED,
    }
    reasons: List[str] = []

    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        return GuardDecision(False, [f"Syntax error: {exc.msg}"], controls)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = ", ".join(alias.name for alias in node.names)
            reasons.append(f"Imports are disabled in BasinLab actions: {modules}")
        elif isinstance(node, ast.ImportFrom):
            reasons.append(f"Imports are disabled in BasinLab actions: {node.module or '<relative>'}")
        elif isinstance(node, ast.Call):
            target = _call_name(node.func)
            if target in FORBIDDEN_CALLS:
                reasons.append(f"Forbidden call before execution: {target}")
            if any(target == blocked or target.startswith(f"{blocked}.") for blocked in FORBIDDEN_MODULES):
                reasons.append(f"Forbidden module usage before execution: {target}")
        elif isinstance(node, ast.Name):
            if node.id.startswith("__"):
                reasons.append(f"Dunder access is disabled in BasinLab actions: {node.id}")
            if node.id in FORBIDDEN_MODULES:
                reasons.append(f"Forbidden module reference before execution: {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                reasons.append(f"Dunder attribute access is disabled: {node.attr}")
            if node.attr in FORBIDDEN_ATTRS:
                reasons.append(f"Forbidden attribute usage before execution: {node.attr}")

    return GuardDecision(not reasons, reasons, controls)
