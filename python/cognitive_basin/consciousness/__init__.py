"""
Operational machine-consciousness exports.
"""

from .adapters import event_to_percepts
from .attention import AttentionSystem
from .continuity import ContinuityManager
from .counterfactual import CounterfactualSimulator
from .episodes import ConsciousEpisode, EpisodeRecorder
from .kernel import ConsciousnessCycleResult, ConsciousnessSnapshot, OperationalConsciousnessKernel
from .metacognition import MetacognitiveMonitor
from .perception import Constant, ConstantField, Percept, PerceptualField
from .purpose import Purpose, PurposeManager
from .self_model import SelfModelManager
from .workspace import GlobalWorkspace

__all__ = [
    "AttentionSystem",
    "ConsciousEpisode",
    "ConsciousnessCycleResult",
    "ConsciousnessSnapshot",
    "Constant",
    "ConstantField",
    "ContinuityManager",
    "CounterfactualSimulator",
    "EpisodeRecorder",
    "GlobalWorkspace",
    "MetacognitiveMonitor",
    "OperationalConsciousnessKernel",
    "Percept",
    "PerceptualField",
    "Purpose",
    "PurposeManager",
    "SelfModelManager",
    "event_to_percepts",
]
