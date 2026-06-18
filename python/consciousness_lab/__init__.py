"""
Acceptance and demo entrypoints for the operational consciousness tranche.
"""

from .acceptance import run_acceptance_suite
from .demo import run_demo

__all__ = ["run_acceptance_suite", "run_demo"]
