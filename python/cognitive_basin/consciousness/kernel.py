"""
Bounded operational machine-consciousness coordinator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from packages.ternary.states import ActionState, EpistemicState
from python.cognitive_basin.pipeline import run_basin_pipeline

from .adapters import event_to_percepts
from .attention import AttentionBudget, AttentionPolicy, AttentionReceipt, AttentionSystem
from .common import now_ts, stable_hash
from .continuity import ContinuityManager, ContinuityReceipt
from .counterfactual import CounterfactualReceipt, CounterfactualSimulator
from .episodes import EpisodeReceipt, EpisodeRecorder
from .failures import ConsciousnessFailure
from .metacognition import MetaReceipt, MetacognitiveMonitor
from .perception import (
    Constant,
    ConstantField,
    Percept,
    PerceptReceipt,
    PerceptualField,
)
from .purpose import Purpose, PurposeManager, PurposePriority, PurposeReceipt, PurposeSource
from .self_model import SelfModelManager, SelfReceipt, SelfResource
from .workspace import GlobalWorkspace, WorkspaceBudget, WorkspaceCandidate, WorkspaceReceipt


@dataclass
class ConsciousnessCycleResult:
    cycle_id: str
    percept_receipt: PerceptReceipt
    constant_snapshot: Dict[str, Any]
    workspace_receipt: WorkspaceReceipt
    attention_receipt: AttentionReceipt
    purpose_receipt: PurposeReceipt
    self_receipt: SelfReceipt
    continuity_receipt: ContinuityReceipt
    counterfactual_receipt: CounterfactualReceipt
    meta_receipt: MetaReceipt
    episode_receipt: EpisodeReceipt
    basin: Dict[str, Any]
    predictions: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]
    paused: bool = False

    def to_record(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "percept_receipt": self.percept_receipt.to_record(),
            "constant_snapshot": dict(self.constant_snapshot),
            "workspace_receipt": self.workspace_receipt.to_record(),
            "attention_receipt": self.attention_receipt.to_record(),
            "purpose_receipt": self.purpose_receipt.to_record(),
            "self_receipt": self.self_receipt.to_record(),
            "continuity_receipt": self.continuity_receipt.to_record(),
            "counterfactual_receipt": self.counterfactual_receipt.to_record(),
            "meta_receipt": self.meta_receipt.to_record(),
            "episode_receipt": self.episode_receipt.to_record(),
            "basin": dict(self.basin),
            "predictions": list(self.predictions),
            "failures": list(self.failures),
            "paused": self.paused,
        }


@dataclass
class ConsciousnessSnapshot:
    session_id: str
    cycle_count: int
    paused: bool
    percept_field: Dict[str, Any]
    constant_field: Dict[str, Any]
    workspace: Dict[str, Any]
    attention: Dict[str, Any]
    purposes: Dict[str, Any]
    self_model: Dict[str, Any]
    continuity: Dict[str, Any]
    counterfactuals: Dict[str, Any]
    metacognition: Dict[str, Any]
    episodes: List[Dict[str, Any]]
    current_epistemic_state: str
    current_action_state: str
    hold_reason: str
    required_evidence: List[str]
    next_predictions: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]

    def to_record(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "cycle_count": self.cycle_count,
            "paused": self.paused,
            "percept_field": self.percept_field,
            "constant_field": self.constant_field,
            "workspace": self.workspace,
            "attention": self.attention,
            "purposes": self.purposes,
            "self_model": self.self_model,
            "continuity": self.continuity,
            "counterfactuals": self.counterfactuals,
            "metacognition": self.metacognition,
            "episodes": list(self.episodes),
            "current_epistemic_state": self.current_epistemic_state,
            "current_action_state": self.current_action_state,
            "hold_reason": self.hold_reason,
            "required_evidence": list(self.required_evidence),
            "next_predictions": list(self.next_predictions),
            "failures": list(self.failures),
        }


class OperationalConsciousnessKernel:
    def __init__(
        self,
        *,
        session_id: str,
        purpose_text: str,
        participant: str = "UNKNOWN",
        repo_head: str = "",
        workspace_budget: WorkspaceBudget | None = None,
        cycle_budget: int = 5,
    ) -> None:
        self.session_id = session_id
        self.participant = participant
        self.repo_head = repo_head
        self.workspace = GlobalWorkspace(workspace_budget)
        self.attention = AttentionSystem(AttentionPolicy(), AttentionBudget())
        self.perception = PerceptualField()
        self.constants = ConstantField()
        self.purposes = PurposeManager()
        self.self_model = SelfModelManager()
        self.continuity = ContinuityManager()
        self.counterfactual = CounterfactualSimulator()
        self.metacognition = MetacognitiveMonitor()
        self.episodes = EpisodeRecorder()
        self.purpose_text = purpose_text
        self.cycle_budget = cycle_budget
        self.cycle_count = 0
        self.paused = False
        self.last_cycle: ConsciousnessCycleResult | None = None
        self.posted_percepts: List[Percept] = []
        self.posted_constants: List[Constant] = []
        self.posted_purposes: Dict[str, Purpose] = {}
        self.failures: List[ConsciousnessFailure] = []

    def add_percept(self, percept: Percept) -> None:
        self.posted_percepts.append(percept)

    def add_constant(self, constant: Constant) -> None:
        self.posted_constants.append(constant)

    def add_purpose(self, purpose: Purpose) -> None:
        self.posted_purposes[purpose.purpose_id] = purpose
        self.purposes.add(purpose)

    def set_pause(self, paused: bool) -> None:
        self.paused = paused

    @classmethod
    def from_events(
        cls,
        *,
        session_id: str,
        events: List[Dict[str, Any]],
        purpose_text: str,
        participant: str,
        repo_head: str,
        connectors: List[Dict[str, Any]] | None = None,
    ) -> "OperationalConsciousnessKernel":
        kernel = cls(session_id=session_id, purpose_text=purpose_text, participant=participant, repo_head=repo_head)
        explicit_percepts: List[Percept] = []
        explicit_constants: List[Constant] = []
        for event in events:
            event_type = str(event.get("type", ""))
            if event_type == "session.consciousness.pause":
                kernel.paused = True
            elif event_type == "session.consciousness.resume":
                kernel.paused = False
            elif event_type == "session.consciousness.percept":
                explicit_percepts.extend(
                    Percept.from_record(item) if isinstance(item, dict) else item for item in event.get("percepts", [])
                )
            elif event_type == "session.consciousness.constant":
                explicit_constants.extend(
                    Constant.from_record(item) if isinstance(item, dict) else item for item in event.get("constants", [])
                )
            elif event_type == "session.consciousness.purpose":
                purpose_payload = event.get("purpose")
                if isinstance(purpose_payload, Purpose):
                    kernel.add_purpose(purpose_payload)
                elif isinstance(purpose_payload, dict):
                    kernel.add_purpose(Purpose.from_record(purpose_payload))
            elif event_type == "session.consciousness.attention":
                lock_target_id = str(event.get("attention", {}).get("lock_target_id", "")).strip()
                if lock_target_id:
                    kernel.attention.set_lock(lock_target_id, str(event.get("attention", {}).get("reason", "manual")))
            elif event_type == "session.consciousness.cycle":
                kernel.cycle_count += 1
                kernel.last_cycle = event.get("cycle_result")
        for percept in event_to_percepts(events):
            kernel.add_percept(percept)
        for percept in explicit_percepts:
            kernel.add_percept(percept)
        for constant in explicit_constants:
            kernel.add_constant(constant)
        if not kernel.posted_purposes and purpose_text:
            kernel.add_purpose(
                Purpose(
                    purpose_id="purpose-session",
                    description=purpose_text,
                    source=PurposeSource("explicit human request", "session metadata"),
                    priority=PurposePriority(1.0, 0.2),
                )
            )
        return kernel

    def run_cycle(
        self,
        *,
        events: List[Dict[str, Any]],
        connectors: List[Dict[str, Any]],
        claimed_capabilities: Dict[str, bool],
        tested_capabilities: Dict[str, bool],
        allow_internal_action: bool = False,
    ) -> ConsciousnessCycleResult:
        if self.paused:
            return self.snapshot_only(events, connectors, claimed_capabilities, tested_capabilities)
        if self.cycle_count >= self.cycle_budget:
            self.cycle_count += 1
            return self._budget_exhausted_result(events, connectors, claimed_capabilities, tested_capabilities)
        self.cycle_count += 1
        cycle_id = f"cycle-{self.cycle_count:04d}"
        percept_receipt = self.perception.ingest(self.posted_percepts, cycle_index=self.cycle_count)
        constant_snapshot = self.constants.apply(self.posted_constants).to_record() if self.posted_constants else self.constants.export().to_record()
        purpose_receipt = self.purposes.arbitrate()
        active_purpose = purpose_receipt.active_purpose.description if purpose_receipt.active_purpose else self.purpose_text
        candidates = self._workspace_candidates(active_purpose)
        workspace_receipt = self.workspace.compete(candidates, cycle_id=cycle_id)
        attention_receipt = self.attention.select(workspace_receipt.snapshot.items, active_purpose=active_purpose, cycle_index=self.cycle_count)
        current_facts = {
            "active_purpose": active_purpose,
            "workspace_items": [item.item_id for item in workspace_receipt.snapshot.items],
            "contradictions": [item.to_record() for item in self.perception.conflicts],
        }
        counterfactual_receipt = self.counterfactual.simulate(
            current_facts=current_facts,
            action_description="advance current purpose with a governed local step",
            authority_required="LOCAL_STATE_WRITE" if allow_internal_action else "EXPLICIT_AUTHORITY",
        )
        contradictions = self._unresolved_contradictions() + len(self.constants.conflicts)
        insufficient = not workspace_receipt.snapshot.items or all(
            item.evidence_quality < 0.55 and item.contradiction_pressure == 0.0 for item in workspace_receipt.snapshot.items
        )
        urgency_text = " urgency high" if any(item.urgency > 0.8 for item in workspace_receipt.snapshot.items) else ""
        evidence_text = "insufficient evidence" if insufficient else "supported evidence"
        basin_result = run_basin_pipeline(
            f"{active_purpose}: {evidence_text}{urgency_text}",
            contradictions=contradictions,
            completion_claim="",
        )
        basin_state = basin_result["basin"]
        basin = {
            "epistemic": basin_state.epistemic.value,
            "action": basin_state.action.value,
            "provisional": basin_state.provisional,
            "reason": getattr(basin_state, "reason", ""),
        }
        authority_missing = not allow_internal_action and basin["action"] == ActionState.EXTEND.value
        if authority_missing:
            basin = {"epistemic": basin["epistemic"], "action": ActionState.HOLD.value, "provisional": True, "reason": "authority_required"}
        self_receipt = self.self_model.build(
            session_id=self.session_id,
            current_purpose=active_purpose,
            connectors=connectors,
            provider_availability=["scripted", "generalist", "compact-reasoner"],
            resources=[
                SelfResource("cycles", max(0, self.cycle_budget - self.cycle_count), "cycles"),
                SelfResource("workspace_items", self.workspace.budget.max_items - len(workspace_receipt.snapshot.items), "items"),
            ],
            expected_next_action="governed local step" if basin["action"] == ActionState.EXTEND.value else "gather evidence",
            actual_next_action="governed local step" if allow_internal_action and basin["action"] == ActionState.EXTEND.value else "hold",
            recent_failures=[item.failure_type for item in self.failures],
            unresolved_tasks=[item.description for item in self.posted_purposes.values() if item.status != "COMPLETED"],
            scars=[item.conflict_id for item in self.perception.conflicts],
            recovery_routes=["replay and gather evidence"] if contradictions else [],
            claimed_capabilities=claimed_capabilities,
            tested_capabilities=tested_capabilities,
            attention_target=attention_receipt.focus[0].label if attention_receipt.focus else "",
        )
        continuity_receipt = self.continuity.assess(
            session_id=self.session_id,
            events=events,
            repo_head=self.repo_head,
            participant=self.participant,
            purpose=active_purpose,
            prior_checkpoint=self.last_cycle.continuity_receipt.checkpoint.to_record() if self.last_cycle else None,
        )
        repeated_without_progress = self.cycle_count > 2 and basin["action"] == ActionState.HOLD.value
        purpose_drift = any("purpose" in entry.category for entry in self_receipt.operational_self.discrepancies)
        meta_receipt = self.metacognition.assess(
            contradiction_count=contradictions,
            source_count=len({item.source for item in self.posted_percepts}) or 1,
            workspace_overload=workspace_receipt.snapshot.starvation_detected or workspace_receipt.snapshot.priority_inversion_detected,
            authority_missing=authority_missing,
            attention_state=attention_receipt.state,
            repeated_without_progress=repeated_without_progress,
            purpose_drift=purpose_drift,
            simulation_as_fact=False,
        )
        disposition = self._episode_disposition(basin, contradictions, authority_missing)
        predictions = [
            {"label": "next-cycle", "detail": "seek new evidence" if basin["action"] != ActionState.EXTEND.value else "verify action outcome"},
            {"label": "continuity", "detail": continuity_receipt.checkpoint.latest_hash},
        ]
        required_evidence = []
        if basin["action"] == ActionState.HOLD.value:
            required_evidence.append("current verification or second independent source")
        memory_ids = [f"consciousness-memory-{cycle_id}"]
        episode_receipt = self.episodes.record(
            session_id=self.session_id,
            participant=self.participant,
            repo_head=self.repo_head,
            purpose_id=purpose_receipt.active_purpose.purpose_id if purpose_receipt.active_purpose else "purpose-session",
            purpose_description=active_purpose,
            percept_ids=list(self.perception.percepts.keys()),
            workspace_item_ids=[item.item_id for item in workspace_receipt.snapshot.items],
            discrepancies=[item.detail for item in self_receipt.operational_self.discrepancies],
            scenario_ids=[item.scenario_id for item in counterfactual_receipt.scenarios],
            epistemic_state=basin["epistemic"],
            action_state=basin["action"],
            disposition=disposition,
            executed=allow_internal_action and basin["action"] == ActionState.EXTEND.value,
            authority_reason="internal action allowed" if allow_internal_action else "explicit authority required",
            outcome_detail=basin["reason"],
            uncertainty_details=[item.detail for item in meta_receipt.uncertainties],
            contradiction_ids=[item.conflict_id for item in self.perception.conflicts],
            memory_ids=memory_ids,
        )
        failures = [item.to_record() for item in self.failures]
        result = ConsciousnessCycleResult(
            cycle_id=cycle_id,
            percept_receipt=percept_receipt,
            constant_snapshot=constant_snapshot,
            workspace_receipt=workspace_receipt,
            attention_receipt=attention_receipt,
            purpose_receipt=purpose_receipt,
            self_receipt=self_receipt,
            continuity_receipt=continuity_receipt,
            counterfactual_receipt=counterfactual_receipt,
            meta_receipt=meta_receipt,
            episode_receipt=episode_receipt,
            basin=basin,
            predictions=predictions,
            failures=failures,
            paused=False,
        )
        self.last_cycle = result
        return result

    def _budget_exhausted_result(
        self,
        events: List[Dict[str, Any]],
        connectors: List[Dict[str, Any]],
        claimed_capabilities: Dict[str, bool],
        tested_capabilities: Dict[str, bool],
    ) -> ConsciousnessCycleResult:
        cycle_id = f"cycle-{self.cycle_count:04d}"
        percept_receipt = self.perception.ingest([], cycle_index=self.cycle_count)
        constant_snapshot = self.constants.export().to_record()
        purpose_receipt = self.purposes.arbitrate()
        workspace_receipt = self.workspace.compete([], cycle_id=cycle_id)
        attention_receipt = self.attention.select([], active_purpose=self.purpose_text, cycle_index=self.cycle_count)
        self_receipt = self.self_model.build(
            session_id=self.session_id,
            current_purpose=self.purpose_text,
            connectors=connectors,
            provider_availability=["scripted"],
            resources=[SelfResource("cycles", 0, "cycles")],
            expected_next_action="stop",
            actual_next_action="stop",
            recent_failures=["cycle_budget_exhausted"],
            unresolved_tasks=[item.description for item in self.posted_purposes.values()],
            scars=[],
            recovery_routes=["increase budget or end run"],
            claimed_capabilities=claimed_capabilities,
            tested_capabilities=tested_capabilities,
            attention_target="",
        )
        continuity_receipt = self.continuity.assess(
            session_id=self.session_id,
            events=events,
            repo_head=self.repo_head,
            participant=self.participant,
            purpose=self.purpose_text,
        )
        counterfactual_receipt = self.counterfactual.simulate(
            current_facts={"budget": "exhausted"},
            action_description="terminate cycle safely",
            authority_required="NONE",
        )
        meta_receipt = self.metacognition.assess(
            contradiction_count=0,
            source_count=1,
            workspace_overload=False,
            authority_missing=False,
            attention_state="stable",
            repeated_without_progress=False,
            purpose_drift=False,
            simulation_as_fact=False,
        )
        episode_receipt = self.episodes.record(
            session_id=self.session_id,
            participant=self.participant,
            repo_head=self.repo_head,
            purpose_id="purpose-session",
            purpose_description=self.purpose_text,
            percept_ids=[],
            workspace_item_ids=[],
            discrepancies=[],
            scenario_ids=[item.scenario_id for item in counterfactual_receipt.scenarios],
            epistemic_state=EpistemicState.UNRESOLVED.value,
            action_state=ActionState.HOLD.value,
            disposition="WAIT",
            executed=False,
            authority_reason="cycle budget exhausted",
            outcome_detail="cycle_budget_exhausted",
            uncertainty_details=["budget exhausted"],
            contradiction_ids=[],
            memory_ids=[f"consciousness-memory-{cycle_id}"],
        )
        result = ConsciousnessCycleResult(
            cycle_id=cycle_id,
            percept_receipt=percept_receipt,
            constant_snapshot=constant_snapshot,
            workspace_receipt=workspace_receipt,
            attention_receipt=attention_receipt,
            purpose_receipt=purpose_receipt,
            self_receipt=self_receipt,
            continuity_receipt=continuity_receipt,
            counterfactual_receipt=counterfactual_receipt,
            meta_receipt=meta_receipt,
            episode_receipt=episode_receipt,
            basin={
                "epistemic": EpistemicState.UNRESOLVED.value,
                "action": ActionState.HOLD.value,
                "provisional": True,
                "reason": "cycle_budget_exhausted",
            },
            predictions=[{"label": "terminate", "detail": "safe cycle termination"}],
            failures=[],
            paused=False,
        )
        self.last_cycle = result
        return result

    def snapshot_only(
        self,
        events: List[Dict[str, Any]],
        connectors: List[Dict[str, Any]],
        claimed_capabilities: Dict[str, bool],
        tested_capabilities: Dict[str, bool],
    ) -> ConsciousnessCycleResult:
        if self.last_cycle is not None:
            self.last_cycle.paused = True
            return self.last_cycle
        was_paused = self.paused
        self.paused = False
        placeholder = self.run_cycle(
            events=events,
            connectors=connectors,
            claimed_capabilities=claimed_capabilities,
            tested_capabilities=tested_capabilities,
            allow_internal_action=False,
        )
        placeholder.paused = True
        self.paused = was_paused
        self.last_cycle = placeholder
        return placeholder

    def snapshot(self) -> ConsciousnessSnapshot:
        last = self.last_cycle
        if isinstance(last, dict):
            workspace = dict(last.get("workspace_receipt", {}))
            attention = dict(last.get("attention_receipt", {}))
            purposes = dict(last.get("purpose_receipt", {}))
            self_model = dict(last.get("self_receipt", {}))
            continuity = dict(last.get("continuity_receipt", {}))
            counterfactuals = dict(last.get("counterfactual_receipt", {}))
            metacognition = dict(last.get("meta_receipt", {}))
            episodes = [dict(last.get("episode_receipt", {}).get("episode", {}))] if last.get("episode_receipt") else []
            basin = dict(last.get("basin", {}))
            predictions = list(last.get("predictions", []))
            failures = list(last.get("failures", []))
        else:
            workspace = last.workspace_receipt.to_record() if last else {}
            attention = last.attention_receipt.to_record() if last else {}
            purposes = last.purpose_receipt.to_record() if last else {}
            self_model = last.self_receipt.to_record() if last else {}
            continuity = last.continuity_receipt.to_record() if last else {}
            counterfactuals = last.counterfactual_receipt.to_record() if last else {}
            metacognition = last.meta_receipt.to_record() if last else {}
            episodes = [last.episode_receipt.episode.to_record()] if last else []
            basin = last.basin if last else {}
            predictions = last.predictions if last else []
            failures = last.failures if last else []
        return ConsciousnessSnapshot(
            session_id=self.session_id,
            cycle_count=self.cycle_count,
            paused=self.paused,
            percept_field=self.perception.export(),
            constant_field=self.constants.export().to_record(),
            workspace=workspace,
            attention=attention,
            purposes=purposes,
            self_model=self_model,
            continuity=continuity,
            counterfactuals=counterfactuals,
            metacognition=metacognition,
            episodes=episodes,
            current_epistemic_state=(basin.get("epistemic", EpistemicState.UNRESOLVED.value)),
            current_action_state=(basin.get("action", ActionState.HOLD.value)),
            hold_reason=(basin.get("reason", "") if basin.get("action") == ActionState.HOLD.value else ""),
            required_evidence=(["current verification or second independent source"] if basin.get("action") == ActionState.HOLD.value else []),
            next_predictions=predictions,
            failures=failures,
        )

    def _workspace_candidates(self, active_purpose: str) -> List[WorkspaceCandidate]:
        candidates: List[WorkspaceCandidate] = []
        for percept in self.perception.percepts.values():
            candidates.append(
                WorkspaceCandidate(
                    candidate_id=percept.percept_id,
                    title=percept.topic(),
                    content=percept.content,
                    source_ids=[percept.source],
                    purpose_relevance=percept.purpose_relevance if active_purpose else 0.4,
                    novelty=percept.novelty,
                    unresolved_contradiction=1.0 if percept.contradiction_links else 0.0,
                    safety_significance=0.8 if percept.modality.value in {"system_constraint", "connector_state"} else 0.2,
                    predicted_consequence=0.6 if percept.channel.value == "GOVERNANCE" else 0.2,
                    temporal_urgency=0.8 if "urgent" in str(percept.content).lower() else 0.1,
                    memory_value=0.5 if percept.source_type.value == "MEMORY" else 0.2,
                    human_request=0.9 if percept.source_type.value == "HUMAN" else 0.1,
                    resource_cost=0.1,
                    salience=percept.salience,
                    evidence_quality=percept.confidence,
                    actionability=0.7 if percept.verification_state in {"OBSERVATION", "VERIFIED_FACT"} else 0.2,
                )
            )
        return candidates

    def _unresolved_contradictions(self) -> int:
        topics: Dict[str, List[Percept]] = {}
        for percept in self.perception.percepts.values():
            if percept.contradiction_links:
                topics.setdefault(percept.topic(), []).append(percept)
        unresolved = 0
        for items in topics.values():
            if any(item.verification_state == "VERIFIED_FACT" for item in items):
                continue
            unresolved += 1
        return unresolved

    def _episode_disposition(self, basin: Dict[str, Any], contradictions: int, authority_missing: bool) -> str:
        if authority_missing:
            return "REQUEST_EVIDENCE"
        if contradictions > 0:
            return "RETRACT"
        if basin["action"] == ActionState.HOLD.value:
            return "HOLD"
        return "EXTEND"


__all__ = ["ConsciousnessCycleResult", "ConsciousnessSnapshot", "OperationalConsciousnessKernel"]
