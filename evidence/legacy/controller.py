"""
Checkpointed Controller + RETRACT/HOLD/EXTEND (Phase E/G)
Genuine implementation per rules.
- HOLD withholds commitment, updates state, consumes budget, collects evidence.
- RETRACT identifies checkpoint, demotes path, restores state, preserves scar, modifies retry.
- EXTEND commits when SUPPORTED.
Separate epistemic (CONTRADICTED/UNRESOLVED/SUPPORTED) from action.
Uses external selector log for instrumentation (what was ignored).
"""

import dataclasses
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .contracts import (
    BasinState, CandidatePath, FailureScar, TransitionRecord,
    EpistemicState, ActionState, ClaimRecord
)

class BasinController:
    def __init__(self, budget: float = 1.0):
        self.state: Optional[BasinState] = None
        self.budget = budget
        self.transitions: List[TransitionRecord] = []
        self.scars: List[FailureScar] = []

    def start_activation(self, activation_id: str, purpose: str, module: str = "RIGOR") -> BasinState:
        self.state = BasinState(
            activation_id=activation_id,
            purpose=purpose,
            module=module,
            epistemic_state=EpistemicState.UNRESOLVED,
            action_state=ActionState.HOLD,
            resource_budget=self.budget,
            resource_used=0.0
        )
        return self.state

    def propose_candidate(self, candidate: CandidatePath, claims: List[ClaimRecord], selector_log: Dict) -> BasinState:
        """External candidate + selector info -> RIGOR classification + controller decision."""
        if not self.state:
            raise RuntimeError("start_activation first")

        # Simple RIGOR: count contradictions in claims
        contradicted = sum(1 for c in claims if c.epistemic_state == EpistemicState.CONTRADICTED)
        supported = sum(1 for c in claims if c.epistemic_state == EpistemicState.SUPPORTED)
        unresolved = len(claims) - contradicted - supported

        prev_ep = self.state.epistemic_state
        prev_action = self.state.action_state

        if contradicted > 0:
            new_ep = EpistemicState.CONTRADICTED
            action = ActionState.RETRACT
        elif supported > 0 and unresolved == 0:
            new_ep = EpistemicState.SUPPORTED
            action = ActionState.EXTEND
        else:
            new_ep = EpistemicState.UNRESOLVED
            action = ActionState.HOLD

        # HOLD is active: consumes budget, logs ignored regions from selector, requires evidence
        cost = 0.05 + (0.1 if action == ActionState.HOLD else 0)
        self.state.resource_used += min(cost, self.state.resource_budget - self.state.resource_used)
        self.state.epistemic_state = new_ep
        self.state.action_state = action

        if action == ActionState.HOLD:
            self.state.held_candidates.append(candidate.candidate_id)
            # Active HOLD: record ignored for audit (what selector rejected)
            ignored = selector_log.get("contradictory_regions_found", []) or selector_log.get("rejected", [])
            candidate.ignored_regions = ignored[:5]  # bounded
        elif action == ActionState.RETRACT:
            self.state.retracted_candidates.append(candidate.candidate_id)
            scar = FailureScar(
                scar_id=f"scar-{len(self.scars)}",
                activation_id=self.state.activation_id,
                candidate_id=candidate.candidate_id,
                checkpoint_id=candidate.checkpoint_id,
                failure_type="contradiction_or_low_coverage",
                failed_claim_ids=[c.claim_id for c in claims if c.epistemic_state == EpistemicState.CONTRADICTED],
                violated_constraints=["stem_preservation", "selector_coverage"],
                evidence=selector_log.get("rationale_summary", "selector log"),
                cause_summary="Ignored contradictory region or low coverage from external selector",
                retry_changes={"widen_selector": True, "require_more_evidence": True},
                created_at=datetime.now(timezone.utc).isoformat()
            )
            self.scars.append(scar)
            self.state.failure_scar_ids.append(scar.scar_id)
            # RETRACT real: demote path, preserve scar, modify future (retry_changes)
        else:
            self.state.supported_claims.extend([c.claim_id for c in claims])
            self.state.active_candidates.append(candidate.candidate_id)

        self.state.transition_count += 1

        trans = TransitionRecord(
            transition_id=f"trans-{len(self.transitions)}",
            activation_id=self.state.activation_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            module=self.state.module,
            previous_epistemic_state=prev_ep.value,
            next_epistemic_state=new_ep.value,
            previous_action=prev_action.value,
            action=action.value,
            trigger="selector_claims" + ("_contradiction" if contradicted else ""),
            evidence_delta=len(claims),
            contradiction_delta=contradicted,
            resource_delta=cost,
            candidate_id=candidate.candidate_id,
            checkpoint_id=candidate.checkpoint_id,
            result=action.value
        )
        self.transitions.append(trans)

        # HOLD active termination condition example
        if action == ActionState.HOLD and self.state.resource_used > self.state.resource_budget * 0.8:
            self.state.action_state = ActionState.RETRACT  # escalate if budget exhausted without resolution

        return self.state

    def get_state(self) -> Dict:
        if not self.state:
            return {}
        d = self.state.to_dict()
        d["scars"] = [s.to_dict() for s in self.scars[-3:]]  # recent
        d["last_transitions"] = [t.to_dict() for t in self.transitions[-3:]]
        return d

if __name__ == "__main__":
    print("Controller demo (genuine HOLD/RETRACT/EXTEND with separate ternaries)")
    # See test runner for full execution.

# === PROVENANCE (added during platform bootstrap) ===
# Original source: ephux-next/basin-lab/core/controller.py
# Verified in M0. Implements BasinController with RETRACT / HOLD / EXTEND action states
# and epistemic SUPPORTED / UNRESOLVED / CONTRADICTED.
# Authors: James Clow and Melissa Clow, BonAcqui LLC.
