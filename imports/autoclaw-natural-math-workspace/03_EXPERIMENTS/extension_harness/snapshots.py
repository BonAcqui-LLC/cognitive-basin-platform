"""
Stage 2 Extension Harness — Defensive Snapshots.

Every piece of mutable model state handed to an extension hook MUST be
a read-only snapshot.  These helpers produce the snapshots and are the
single point where the harness decides *what* shape each snapshot takes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, FrozenSet, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
#  Node / occupancy snapshots
# ═══════════════════════════════════════════════════════════════════════

def snapshot_nodes(nodes: list) -> list:
    """
    Return a deepcopy of *nodes* where every node's ``bonds`` set is
    replaced with a ``frozenset`` so the returned list is re-orderable
    but every node's bond membership is immutable.
    """
    copy_nodes = deepcopy(nodes)
    for node in copy_nodes:
        if hasattr(node, "bonds") and isinstance(node.bonds, (set, list, frozenset)):
            node.bonds = frozenset(node.bonds)
    return copy_nodes


def snapshot_occupancy(nodes: list) -> frozenset:
    """
    Return a ``frozenset`` of all occupied positions.

    Expects each node to expose either ``.position`` or ``.pos`` as a
    tuple (x, y).
    """
    positions = []
    for node in nodes:
        pos = _extract_position(node)
        if pos is not None:
            positions.append(pos)
    return frozenset(positions)


# ═══════════════════════════════════════════════════════════════════════
#  Parameter snapshots
# ═══════════════════════════════════════════════════════════════════════

def snapshot_params(params: dict) -> dict:
    """Deep-copy the parameter dictionary."""
    return deepcopy(params)


# ═══════════════════════════════════════════════════════════════════════
#  Decision / movement snapshots
# ═══════════════════════════════════════════════════════════════════════

def snapshot_decisions(decisions: dict) -> dict:
    """Return a shallow-key copy of the decisions dict."""
    return dict(decisions)


def snapshot_movement_attempts(attempts: dict) -> dict:
    """
    Return a dict keyed by (node_id, direction) tuples.
    Converts any mutable keys to canonical tuple form.
    """
    result: dict = {}
    for key, value in attempts.items():
        canonical_key = tuple(key) if not isinstance(key, tuple) else key
        result[canonical_key] = value
    return result


# ═══════════════════════════════════════════════════════════════════════
#  Bifurcation / resource snapshots
# ═══════════════════════════════════════════════════════════════════════

def snapshot_bifurcation_reservations(reservations) -> frozenset:
    """Return a frozenset of reserved positions."""
    return frozenset(reservations)


def snapshot_resource_state(
    resource_pos: Any,
    resource_left: Any,
    resource_reached: Any,
) -> tuple:
    """Return a tuple snapshot of the three resource state components."""
    return (resource_pos, resource_left, resource_reached)


# ═══════════════════════════════════════════════════════════════════════
#  Cluster metrics snapshot
# ═══════════════════════════════════════════════════════════════════════

def snapshot_cluster_metrics(metrics: Any) -> Any:
    """
    Deep-copy cluster metrics, converting ``center_sum`` to a tuple
    when it is a mutable sequence.
    """
    copy_metrics = deepcopy(metrics)
    if hasattr(copy_metrics, "center_sum"):
        if not isinstance(copy_metrics.center_sum, tuple):
            copy_metrics.center_sum = tuple(copy_metrics.center_sum)
    return copy_metrics


# ═══════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════════════════════

def _extract_position(node) -> Optional[tuple]:
    """Return (x, y) from node.position or node.pos, or None."""
    for attr in ("position", "pos"):
        if hasattr(node, attr):
            val = getattr(node, attr)
            if isinstance(val, (tuple, list)) and len(val) == 2:
                return (val[0], val[1])
    return None
