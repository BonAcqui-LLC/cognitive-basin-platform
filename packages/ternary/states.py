"""
Canonical Ternary Contracts for Cognitive Basin / Fractalish.

Epistemic (truth) states and Action states are deliberately separate, per the
architecture defined by James Clow and Melissa Clow (BonAcqui LLC).

This is new implementation with explicit lineage to the canonical sources
imported in evidence/legacy/.

Original research and architecture: James Clow (lead synthesizer, system architect),
Melissa Clow (co-author, Natural Math contributor, core conceptual collaborator),
BonAcqui LLC.
"""

from enum import Enum
from typing import Literal

# Epistemic (truth) states - separate from action
class EpistemicState(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNRESOLVED = "UNRESOLVED"
    CONTRADICTED = "CONTRADICTED"

# Action states - separate dimension (RETRACT / HOLD / EXTEND)
class ActionState(str, Enum):
    EXTEND = "EXTEND"   # Commit when SUPPORTED
    HOLD = "HOLD"       # Withhold, collect evidence, consume budget, record ignored
    RETRACT = "RETRACT" # Demote path, create scar, preserve for recovery

EpistemicStateLiteral = Literal["SUPPORTED", "UNRESOLVED", "CONTRADICTED"]
ActionStateLiteral = Literal["EXTEND", "HOLD", "RETRACT"]

def is_epistemic(state: str) -> bool:
    return state in (s.value for s in EpistemicState)

def is_action(state: str) -> bool:
    return state in (s.value for s in ActionState)

# For capability registry and Completion Integrity Guard usage
ALL_EPISTEMIC = [s.value for s in EpistemicState]
ALL_ACTIONS = [s.value for s in ActionState]
