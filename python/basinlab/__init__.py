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
from .reports import build_static_html, normalize_report, write_report_bundle
from .recovery import RecoveryManager
from .scars import ScarRegistry
from .session import BasinLabSession, replay_governed_session
from .store import SessionStore
from .spectrum import CandidateGenerator, CandidateTrajectory
from .stabilization import StabilizationEvidence, StabilizationResult, assess_stabilization
from .hold import HoldFogRecord, HoldFogTracker
from .memory_map import FractalMemoryMap, MemoryNode
from .team_narrative import NarrativeRecord, TeamNarrative

__all__ = [
    "ActionProposal",
    "AssociationField",
    "CommitProposal",
    "FractalMemoryMap",
    "BasinLabSession",
    "CandidateGenerator",
    "CandidateTrajectory",
    "CompactReasonerProvider",
    "GeneralistPlanner",
    "GeneralistProvider",
    "HoldFogRecord",
    "HoldFogTracker",
    "MemoryNode",
    "NarrativeRecord",
    "RecoveryManager",
    "ReliabilityEngine",
    "ScarRegistry",
    "SessionStore",
    "ScriptedProvider",
    "seeded_three_world",
    "StabilizationEvidence",
    "StabilizationResult",
    "TeamNarrative",
    "VerifiedCompression",
    "VibeThinkerProvider",
    "assess_stabilization",
    "build_static_html",
    "minority_wins_demo",
    "normalize_report",
    "replay_governed_session",
    "write_report_bundle",
]
