"""
Governed connector contracts, adapters, and registry.
"""

from .contracts import (
    ConnectorAvailability,
    ConnectorCapability,
    ConnectorCostClass,
    ConnectorDataClassification,
    ConnectorError,
    ConnectorEvidence,
    ConnectorHealth,
    ConnectorIdentity,
    ConnectorOperation,
    ConnectorPolicy,
    ConnectorRateLimit,
    ConnectorReceipt,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorScope,
    ConnectorSideEffect,
)
from .core import Connector, ConnectorRegistry, build_default_registry

__all__ = [
    "Connector",
    "ConnectorAvailability",
    "ConnectorCapability",
    "ConnectorCostClass",
    "ConnectorDataClassification",
    "ConnectorError",
    "ConnectorEvidence",
    "ConnectorHealth",
    "ConnectorIdentity",
    "ConnectorOperation",
    "ConnectorPolicy",
    "ConnectorRateLimit",
    "ConnectorReceipt",
    "ConnectorRegistry",
    "ConnectorRequest",
    "ConnectorResponse",
    "ConnectorScope",
    "ConnectorSideEffect",
    "build_default_registry",
]
