"""
Local EphUX product integration surface for BasinLab.
"""

from .acceptance import run_acceptance_suite
from .service import EphuxLocalService, LocalServiceConfig, start_service_in_thread

__all__ = [
    "EphuxLocalService",
    "LocalServiceConfig",
    "run_acceptance_suite",
    "start_service_in_thread",
]
