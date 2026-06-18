"""
Canonical Cognitive Basin Python package exports.
"""

from .authority import AuthorityManager
from .connectors import ConnectorRegistry, build_default_registry
from .pipeline import CommitGate, replay_events, run_basin_pipeline

__all__ = [
    "AuthorityManager",
    "CommitGate",
    "ConnectorRegistry",
    "build_default_registry",
    "replay_events",
    "run_basin_pipeline",
]
