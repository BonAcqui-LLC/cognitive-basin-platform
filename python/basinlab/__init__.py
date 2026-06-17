"""
BasinLab vertical-slice runtime.

Original architecture: James Clow and Melissa Clow, BonAcqui LLC.
Implementation in this repository is a clean-room BasinLab runtime that
reuses only the public ideas and the existing Cognitive Basin contracts.
"""

from .associations import AssociationField
from .compression import VerifiedCompression
from .contracts import ActionProposal, CommitProposal
from .natural_math import seeded_three_world
from .planner import GeneralistPlanner
from .providers import CompactReasonerProvider, GeneralistProvider, ScriptedProvider, VibeThinkerProvider
from .reliability import ReliabilityEngine, minority_wins_demo
from .recovery import RecoveryManager
from .scars import ScarRegistry
from .session import BasinLabSession, replay_governed_session
from .spectrum import CandidateGenerator, CandidateTrajectory

__all__ = [
    "ActionProposal",
    "AssociationField",
    "CommitProposal",
    "BasinLabSession",
    "CandidateGenerator",
    "CandidateTrajectory",
    "CompactReasonerProvider",
    "GeneralistPlanner",
    "GeneralistProvider",
    "RecoveryManager",
    "ReliabilityEngine",
    "ScarRegistry",
    "ScriptedProvider",
    "seeded_three_world",
    "VerifiedCompression",
    "VibeThinkerProvider",
    "minority_wins_demo",
    "replay_governed_session",
]
