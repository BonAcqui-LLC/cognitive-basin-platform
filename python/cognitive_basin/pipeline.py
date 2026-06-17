"""
Cognitive Basin executable pipeline (PERCEPT -> ATAL -> RIGOR -> CIRCUIT -> GUARD -> SERA -> Basin update -> Commit Gate).

Minimal but functional implementation to demonstrate the first full path and the 6 required scenarios.

Lineage: built on the ternary states and guard from the foundation commits, and legacy contracts/controller snapshots.

Original architecture by James Clow and Melissa Clow, BonAcqui LLC.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import time
from pathlib import Path

# Import from our foundation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from packages.ternary.states import EpistemicState, ActionState
from packages.completion_integrity.guard import attempt_transition

@dataclass
class Percept:
    data: Any
    provenance: str = "direct_input"

@dataclass
class ATALResult:
    salience: float
    uncertainty: float
    pressure: float

class ATAL:
    def modulate(self, percept: Percept, pressure: float = 0.5) -> ATALResult:
        # Simple pressure/salience modulation
        salience = max(0.0, 1.0 - pressure)
        uncertainty = pressure
        return ATALResult(salience=salience, uncertainty=uncertainty, pressure=pressure)

@dataclass
class Claim:
    text: str
    support: int = 0
    contradict: int = 0

@dataclass
class RIGORResult:
    epistemic: EpistemicState
    claims: List[Claim]
    contradictions: int

class RIGOR:
    def analyze(self, contradictions: int = 0, evidence_strength: float = 1.0) -> RIGORResult:
        # Epistemic state is determined solely by evidence/contradictions, independent of ATAL pressure.
        # Pressure affects only budgeting, salience, and escalation (in CIRCUIT/GUARD).
        if contradictions > 0:
            ep = EpistemicState.CONTRADICTED
        elif contradictions == 0 and evidence_strength > 0.7:
            ep = EpistemicState.SUPPORTED
        else:
            ep = EpistemicState.UNRESOLVED
        return RIGORResult(epistemic=ep, claims=[], contradictions=contradictions)

@dataclass
class CircuitDecision:
    action: ActionState
    epistemic: EpistemicState
    provisional: bool = False
    budget: float = 1.0

class CIRCUIT:
    def route(self, rigor: RIGORResult, pressure: float = 0.5, budget: float = 1.0) -> CircuitDecision:
        # Pressure affects budget/escalation only; epistemic truth comes from RIGOR.
        effective_budget = max(0.1, budget * (1.0 - pressure * 0.6))
        if rigor.epistemic == EpistemicState.CONTRADICTED:
            action = ActionState.RETRACT
        elif rigor.epistemic == EpistemicState.SUPPORTED and rigor.contradictions == 0:
            action = ActionState.EXTEND
        else:
            action = ActionState.HOLD
        provisional = (action == ActionState.HOLD) or (rigor.epistemic == EpistemicState.UNRESOLVED)
        return CircuitDecision(action=action, epistemic=rigor.epistemic, provisional=provisional, budget=effective_budget)

class GUARD:
    def check(self, circuit: CircuitDecision, artifact_paths: List[str] = None) -> Dict[str, Any]:
        if artifact_paths is None:
            artifact_paths = []
        guard_result = attempt_transition(
            capability_name="basin.commit",
            artifact_paths=artifact_paths,
            claimed_status="IMPLEMENTED" if circuit.action == ActionState.EXTEND else "PROVISIONAL"
        )
        allowed = guard_result.allowed and circuit.action != ActionState.RETRACT
        return {
            "allowed": allowed,
            "epistemic": circuit.epistemic.value,
            "action": circuit.action.value,
            "provisional": circuit.provisional or not allowed,
            "guard_reason": guard_result.reason
        }

class SERA:
    def record(self, guard_result: Dict[str, Any], events: List[Dict] = None) -> Dict[str, Any]:
        if events is None:
            events = []
        event = {
            "timestamp": time.time(),
            "epistemic": guard_result["epistemic"],
            "action": guard_result["action"],
            "provisional": guard_result["provisional"],
            "reason": guard_result.get("guard_reason", "")
        }
        events.append(event)
        return {"events": events, "last": event}

@dataclass
class BasinState:
    epistemic: EpistemicState
    action: ActionState
    provisional: bool
    events: List[Dict] = field(default_factory=list)

class CommitGate:
    def allow(self, guard_result: Dict[str, Any]) -> bool:
        return guard_result["allowed"] and not guard_result["provisional"]

def run_basin_pipeline(percept_data: Any, pressure: float = 0.5, contradictions: int = 0, artifact_paths: List[str] = None, prior_events: List[Dict] = None) -> Dict[str, Any]:
    if prior_events is None:
        prior_events = []
    p = Percept(percept_data)
    atal = ATAL().modulate(p, pressure)
    data_str = str(percept_data).lower() if percept_data else ""
    if contradictions == 0:
        if "insufficient" in data_str or "weak" in data_str:
            evidence_strength = 0.4
        else:
            evidence_strength = 1.0
    else:
        evidence_strength = 1.0
    rigor = RIGOR().analyze(contradictions=contradictions, evidence_strength=evidence_strength)
    circuit = CIRCUIT().route(rigor, pressure=pressure)
    guard = GUARD().check(circuit, artifact_paths)
    sera = SERA().record(guard, prior_events.copy())
    basin = BasinState(
        epistemic=EpistemicState(guard["epistemic"]),
        action=ActionState(guard["action"]),
        provisional=guard["provisional"],
        events=sera["events"]
    )
    gate = CommitGate().allow(guard)
    return {
        "basin": basin,
        "gate_allowed": gate,
        "events": sera["events"]
    }

def replay_events(events: List[Dict]) -> BasinState:
    # Simple replay: last event wins for state
    if not events:
        return BasinState(EpistemicState.UNRESOLVED, ActionState.HOLD, True, [])
    last = events[-1]
    return BasinState(
        epistemic=EpistemicState(last["epistemic"]),
        action=ActionState(last["action"]),
        provisional=last.get("provisional", True),
        events=events
    )
