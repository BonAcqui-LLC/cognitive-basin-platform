"""Canonical Natural Math package for the Fractalish workspace.

This package now contains the stable local-growth baseline ported from the
smoke-tested `Natural_Math_Simulator_v1.2.py` branch. It is still a staged
implementation, not a full Appendix B-complete reproduction proof engine.
"""

from .decisions import CONSERVE, EXTEND, REPRODUCE, RESTRICT, SENSE
from .invariants import validate_state
from .simulator import NaturalMathPopSim, NaturalMathSimulator
from .state import AgentState, NodeState, SimulationState

__all__ = [
    "AgentState",
    "NodeState",
    "SimulationState",
    "NaturalMathSimulator",
    "NaturalMathPopSim",
    "validate_state",
    "EXTEND",
    "SENSE",
    "RESTRICT",
    "CONSERVE",
    "REPRODUCE",
]
