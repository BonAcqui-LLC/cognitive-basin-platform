"""
Bounded operational machine-consciousness coordinator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from packages.ternary.states import ActionState, EpistemicState
from python.cognitive_basin.pipeline import run_basin_pipeline
from python.cognitive_basin.anomalies import AnomalyDetector, AnomalyReceipt
from python.cognitive_basin.boundaries import AgencyReceipt, BoundaryEngine, BoundaryReceipt
from python.cognitive_basin.calibration import CalibrationReceipt, CalibrationTracker
from python.cognitive_basin.causality import CausalClaim, CausalEvidence, CausalGraph, CausalReceipt, InterventionControl, InterventionPrediction, InterventionProposal, InterventionTarget, InterventionValue, InterventionVariable
from python.cognitive_basin.interoception import InteroceptionMonitor, RegulationReceipt
from python.cognitive_basin.learning import LearningManager
from python.cognitive_basin.perspectives import PerspectiveReceipt, PerspectiveRegistry
from python.cognitive_basin.planning import PlanReceipt, Planner
from python.cognitive_basin.prediction import PredictionEngine, PredictionReceipt
from python.cognitive_basin.rehearsal import RehearsalManager, RehearsalReceipt
from python.cognitive_basin.world_model import WorldModel, WorldObservation, WorldPrediction, WorldReceipt

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
    boundary_receipt: BoundaryReceipt
    agency_receipt: AgencyReceipt
    world_receipt: WorldReceipt
    prediction_receipt: PredictionReceipt
    interoception_receipt: RegulationReceipt
    causal_receipt: CausalReceipt
    perspective_receipt: PerspectiveReceipt
    planning_receipts: List[PlanReceipt]
    rehearsal_receipt: RehearsalReceipt
    anomaly_receipt: AnomalyReceipt
    calibration_receipt: CalibrationReceipt
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
            "boundary_receipt": self.boundary_receipt.to_record(),
            "agency_receipt": self.agency_receipt.to_record(),
            "world_receipt": self.world_receipt.to_record(),
            "prediction_receipt": self.prediction_receipt.to_record(),
            "interoception_receipt": self.interoception_receipt.to_record(),
            "causal_receipt": self.causal_receipt.to_record(),
            "perspective_receipt": self.perspective_receipt.to_record(),
            "planning_receipts": [item.to_record() for item in self.planning_receipts],
            "rehearsal_receipt": self.rehearsal_receipt.to_record(),
            "anomaly_receipt": self.anomaly_receipt.to_record(),
            "calibration_receipt": self.calibration_receipt.to_record(),
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
    boundaries: Dict[str, Any]
    agency: Dict[str, Any]
    world: Dict[str, Any]
    prediction: Dict[str, Any]
    interoception: Dict[str, Any]
    causal_model: Dict[str, Any]
    perspectives: Dict[str, Any]
    plans: List[Dict[str, Any]]
    rehearsals: Dict[str, Any]
    anomalies: Dict[str, Any]
    calibration: Dict[str, Any]
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
            "boundaries": self.boundaries,
            "agency": self.agency,
            "world": self.world,
            "prediction": self.prediction,
            "interoception": self.interoception,
            "causal_model": self.causal_model,
            "perspectives": self.perspectives,
            "plans": list(self.plans),
            "rehearsals": self.rehearsals,
            "anomalies": self.anomalies,
            "calibration": self.calibration,
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
        self.boundaries = BoundaryEngine()
        self.world_model = WorldModel()
        self.prediction_engine = PredictionEngine()
        self.interoception = InteroceptionMonitor()
        self.causality = CausalGraph()
        self.learning = LearningManager()
        self.perspectives = PerspectiveRegistry()
        self.planner = Planner()
        self.rehearsal = RehearsalManager()
        self.anomalies = AnomalyDetector()
        self.calibration = CalibrationTracker()
        self.purpose_text = purpose_text
        self.cycle_budget = cycle_budget
        self.cycle_count = 0
        self.paused = False
        self.last_cycle: ConsciousnessCycleResult | None = None
        self.posted_percepts: List[Percept] = []
        self.posted_constants: List[Constant] = []
        self.posted_purposes: Dict[str, Purpose] = {}
        self.posted_world_observations: List[WorldObservation] = []
        self.posted_prediction_specs: List[Dict[str, Any]] = []
        self.posted_causal_claims: Dict[str, CausalClaim] = {}
        self.posted_interventions: List[InterventionProposal] = []
        self.posted_perspectives: List[Dict[str, Any]] = []
        self.posted_rehearsals: List[str] = []
        self.failures: List[ConsciousnessFailure] = []

    def add_percept(self, percept: Percept) -> None:
        self.posted_percepts.append(percept)

    def add_constant(self, constant: Constant) -> None:
        self.posted_constants.append(constant)

    def add_purpose(self, purpose: Purpose) -> None:
        self.posted_purposes[purpose.purpose_id] = purpose
        self.purposes.add(purpose)

    def add_world_observation(self, observation: WorldObservation) -> None:
        self.posted_world_observations.append(observation)

    def add_prediction_spec(self, spec: Dict[str, Any]) -> None:
        self.posted_prediction_specs.append(dict(spec))

    def add_causal_claim(self, claim: CausalClaim) -> None:
        self.posted_causal_claims[claim.claim_id] = claim

    def add_intervention(self, proposal: InterventionProposal) -> None:
        self.posted_interventions.append(proposal)

    def add_perspective_record(self, record: Dict[str, Any]) -> None:
        self.posted_perspectives.append(dict(record))

    def add_rehearsal_request(self, detail: str) -> None:
        self.posted_rehearsals.append(detail)

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
            elif event_type == "session.world.observation":
                for item in event.get("observations", []):
                    if isinstance(item, dict):
                        kernel.add_world_observation(WorldObservation.from_record(item))
            elif event_type == "session.prediction.request":
                kernel.add_prediction_spec(dict(event.get("prediction", {})))
            elif event_type == "session.causal.hypothesis":
                payload = dict(event.get("claim", {}))
                kernel.add_causal_claim(
                    CausalClaim(
                        claim_id=str(payload.get("claim_id", f"claim-{len(kernel.posted_causal_claims) + 1:04d}")),
                        source_node_id=str(payload.get("source_node_id", "")),
                        target_node_id=str(payload.get("target_node_id", "")),
                        relation_type=str(payload.get("relation_type", "HYPOTHESIZED")),
                        evidence=[CausalEvidence(str(item.get("detail", item))) for item in payload.get("evidence", [])],
                        confounders=list(payload.get("confounders", [])),
                        alternative_explanations=list(payload.get("alternative_explanations", [])),
                        confidence=float(payload.get("confidence", 0.4)),
                        validity_scope=str(payload.get("validity_scope", "LOCAL")),
                    )
                )
            elif event_type == "session.intervention":
                payload = dict(event.get("intervention", {}))
                kernel.add_intervention(
                    InterventionProposal(
                        proposal_id=str(payload.get("proposal_id", f"intervention-proposal-{len(kernel.posted_interventions) + 1:04d}")),
                        target=InterventionTarget(str(payload.get("target_id", "")), str(payload.get("target_type", "SIMULATION"))),
                        variable=InterventionVariable(str(payload.get("variable", ""))),
                        value=InterventionValue(payload.get("value")),
                        control=InterventionControl(payload.get("control_value")),
                        prediction=InterventionPrediction(str(payload.get("prediction_detail", ""))),
                        allowed_domain=str(payload.get("allowed_domain", "SIMULATION")),
                        simulated=bool(payload.get("simulated", True)),
                    )
                )
            elif event_type == "session.perspective.record":
                kernel.add_perspective_record(dict(event.get("perspective", {})))
            elif event_type == "session.rehearsal.request":
                kernel.add_rehearsal_request(str(event.get("detail", "offline rehearsal")))
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
        boundary_receipt = self.boundaries.classify_percepts(self.posted_percepts)
        world_observations = self._world_observations()
        world_receipt = self.world_model.observe(world_observations)
        self._apply_pending_predictions()
        prediction_receipt = self.prediction_engine.verify(world_observations)
        interoception_receipt = self.interoception.assess(
            self._interoception_metrics(prediction_receipt, world_receipt),
            connector_availability=all(item.get("identity", {}).get("connector_id") for item in connectors) if connectors else False,
            replay_integrity=True,
            ci_state="success",
        )
        for claim in self.posted_causal_claims.values():
            self.causality.add_claim(claim)
        for proposal in self.posted_interventions:
            observed_value = proposal.value.value
            if world_observations:
                for observation in world_observations:
                    if observation.property_name == proposal.variable.name:
                        observed_value = observation.value
                        break
            self.causality.apply_intervention(proposal, observed_value)
        causal_receipt = self.causality.snapshot()
        for record in self.posted_perspectives:
            self.perspectives.record_statement(
                owner_id=str(record.get("owner_id", "UNKNOWN")),
                owner_class=str(record.get("owner_class", "UNKNOWN")),
                statement=str(record.get("statement", "")),
                label=str(record.get("label", "uncertainty")),
                evidence_category=str(record.get("evidence_category", "UNKNOWN")),
            )
        perspective_receipt = self.perspectives.receipt()
        anomaly_receipt = self.anomalies.detect(
            residual_types=[item.residual_type for item in prediction_receipt.residuals],
            contradiction_count=self._unresolved_contradictions(),
            replay_integrity=True,
            authority_conflicts=len(boundary_receipt.conflicts),
        )
        world_revisions = []
        if prediction_receipt.residuals:
            world_revisions.append(
                self.world_model.revise(
                    trigger="prediction_failure",
                    reason="prediction discrepancies detected",
                    evidence=[item.residual_type for item in prediction_receipt.residuals],
                    affected_entity_ids=world_receipt.admitted_entity_ids,
                )
            )
        if self._unresolved_contradictions():
            world_revisions.append(
                self.world_model.revise(
                    trigger="contradiction",
                    reason="contradictory world evidence retained",
                    evidence=[item.conflict_id for item in self.perception.conflicts],
                    affected_entity_ids=world_receipt.admitted_entity_ids,
                )
            )
        if world_revisions:
            world_receipt = WorldReceipt(
                admitted_entity_ids=world_receipt.admitted_entity_ids,
                observations=world_receipt.observations,
                identity=world_receipt.identity,
                revisions=world_revisions,
                snapshot=self.world_model.snapshot(),
            )
        constant_snapshot = self.constants.apply(self.posted_constants).to_record() if self.posted_constants else self.constants.export().to_record()
        purpose_receipt = self.purposes.arbitrate()
        active_purpose = purpose_receipt.active_purpose.description if purpose_receipt.active_purpose else self.purpose_text
        candidates = self._workspace_candidates(active_purpose)
        workspace_receipt = self.workspace.compete(candidates, cycle_id=cycle_id)
        attention_receipt = self.attention.select(workspace_receipt.snapshot.items, active_purpose=active_purpose, cycle_index=self.cycle_count)
        planning_receipts = self.planner.build(
            purpose=active_purpose,
            resource_pressure=bool(interoception_receipt.pressures),
            authority_needed="LOCAL_STATE_WRITE" if allow_internal_action else "EXPLICIT_AUTHORITY",
        )
        rehearsal_receipt = self.rehearsal.rehearse(
            detail=self.posted_rehearsals[0] if self.posted_rehearsals else "replay surprising branch",
            budget_available=(self.cycle_budget - self.cycle_count) > 0,
        )
        current_facts = {
            "active_purpose": active_purpose,
            "workspace_items": [item.item_id for item in workspace_receipt.snapshot.items],
            "contradictions": [item.to_record() for item in self.perception.conflicts],
            "predictions": prediction_receipt.to_record(),
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
        if interoception_receipt.pressures and basin["action"] == ActionState.EXTEND.value:
            basin = {"epistemic": basin["epistemic"], "action": ActionState.HOLD.value, "provisional": True, "reason": "resource_pressure"}
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
        calibration_receipt = self.calibration.assess(*self._confidence_outcomes())
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
        self.boundaries.record_action(
            action_id=f"action-{cycle_id}",
            proposed_by="IMPLEMENTATION_AGENT",
            authored_by="IMPLEMENTATION_AGENT",
            executed_by="SYSTEM_SELF" if allow_internal_action and basin["action"] == ActionState.EXTEND.value else "SYSTEM_SELF",
            approved_by="PARTICIPANT_JAMES" if allow_internal_action else "UNKNOWN",
            owned_by="SYSTEM_SELF",
            responsibility="SYSTEM_SELF",
            intent=active_purpose,
            outcome_state=basin["action"],
            outcome_detail=basin["reason"],
            authority_basis="explicit authority" if allow_internal_action else "missing or withheld authority",
        )
        agency_receipt = self.boundaries.agency_receipt()
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
            boundary_receipt=boundary_receipt,
            agency_receipt=agency_receipt,
            world_receipt=world_receipt,
            prediction_receipt=prediction_receipt,
            interoception_receipt=interoception_receipt,
            causal_receipt=causal_receipt,
            perspective_receipt=perspective_receipt,
            planning_receipts=planning_receipts,
            rehearsal_receipt=rehearsal_receipt,
            anomaly_receipt=anomaly_receipt,
            calibration_receipt=calibration_receipt,
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
        boundary_receipt = self.boundaries.classify_percepts([])
        agency_receipt = self.boundaries.agency_receipt()
        world_receipt = WorldReceipt([], [], self.world_model.observe([]).identity, [], self.world_model.snapshot())
        prediction_receipt = self.prediction_engine.verify([])
        interoception_receipt = self.interoception.assess(
            {"cycle_budget_remaining": 1.0, "workspace_occupancy": 0.0, "prediction_error_rate": 0.0, "failed_action_rate": 0.0, "hold_duration": 0.0},
            connector_availability=bool(connectors),
            replay_integrity=True,
            ci_state="success",
        )
        causal_receipt = self.causality.snapshot()
        perspective_receipt = self.perspectives.receipt()
        planning_receipts = self.planner.build(purpose=self.purpose_text, resource_pressure=True, authority_needed="NONE")
        rehearsal_receipt = self.rehearsal.rehearse(detail="budget exhausted", budget_available=False)
        anomaly_receipt = self.anomalies.detect(residual_types=[], contradiction_count=0, replay_integrity=True, authority_conflicts=0)
        calibration_receipt = self.calibration.assess([], [])
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
            boundary_receipt=boundary_receipt,
            agency_receipt=agency_receipt,
            world_receipt=world_receipt,
            prediction_receipt=prediction_receipt,
            interoception_receipt=interoception_receipt,
            causal_receipt=causal_receipt,
            perspective_receipt=perspective_receipt,
            planning_receipts=planning_receipts,
            rehearsal_receipt=rehearsal_receipt,
            anomaly_receipt=anomaly_receipt,
            calibration_receipt=calibration_receipt,
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
        snapshot_cycle = self.run_cycle(
            events=events,
            connectors=connectors,
            claimed_capabilities=claimed_capabilities,
            tested_capabilities=tested_capabilities,
            allow_internal_action=False,
        )
        snapshot_cycle.paused = True
        self.paused = was_paused
        self.last_cycle = snapshot_cycle
        return snapshot_cycle

    def snapshot(self) -> ConsciousnessSnapshot:
        last = self.last_cycle
        if isinstance(last, dict):
            boundaries = dict(last.get("boundary_receipt", {}))
            agency = dict(last.get("agency_receipt", {}))
            world = dict(last.get("world_receipt", {}))
            prediction = dict(last.get("prediction_receipt", {}))
            interoception = dict(last.get("interoception_receipt", {}))
            causal_model = dict(last.get("causal_receipt", {}))
            perspectives = dict(last.get("perspective_receipt", {}))
            plans = list(last.get("planning_receipts", []))
            rehearsals = dict(last.get("rehearsal_receipt", {}))
            anomalies = dict(last.get("anomaly_receipt", {}))
            calibration = dict(last.get("calibration_receipt", {}))
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
            boundaries = last.boundary_receipt.to_record() if last else {}
            agency = last.agency_receipt.to_record() if last else {}
            world = last.world_receipt.to_record() if last else {}
            prediction = last.prediction_receipt.to_record() if last else {}
            interoception = last.interoception_receipt.to_record() if last else {}
            causal_model = last.causal_receipt.to_record() if last else {}
            perspectives = last.perspective_receipt.to_record() if last else {}
            plans = [item.to_record() for item in last.planning_receipts] if last else []
            rehearsals = last.rehearsal_receipt.to_record() if last else {}
            anomalies = last.anomaly_receipt.to_record() if last else {}
            calibration = last.calibration_receipt.to_record() if last else {}
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
            boundaries=boundaries,
            agency=agency,
            world=world,
            prediction=prediction,
            interoception=interoception,
            causal_model=causal_model,
            perspectives=perspectives,
            plans=plans,
            rehearsals=rehearsals,
            anomalies=anomalies,
            calibration=calibration,
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

    def _world_observations(self) -> List[WorldObservation]:
        observations = list(self.posted_world_observations)
        for percept in self.posted_percepts:
            category = {
                "MEMORY": "REMEMBERED",
                "PREDICTION": "PREDICTED",
                "SIMULATION": "SIMULATED",
            }.get(percept.verification_state, "OBSERVED")
            observations.append(
                WorldObservation(
                    observation_id=f"world-{percept.percept_id}",
                    entity_type="ABSTRACT_OBJECT",
                    property_name=percept.topic(),
                    value=percept.content,
                    category=category,
                    source=percept.source,
                    provenance=percept.provenance,
                    entity_id=f"entity-{stable_hash([percept.topic(), percept.source])[:12]}",
                    identity_hints={"topic": percept.topic(), "source": percept.source},
                    uncertainty=max(0.0, 1.0 - percept.confidence),
                    contradiction_links=list(percept.contradiction_links),
                )
            )
        return observations

    def _apply_pending_predictions(self) -> None:
        for spec in self.posted_prediction_specs:
            prediction = self.prediction_engine.create_prediction(
                entity_id=str(spec.get("entity_id", f"entity-{stable_hash(spec)[:12]}")),
                property_name=str(spec.get("property_name", "state")),
                expected_value=spec.get("expected_value"),
                horizon=str(spec.get("horizon", "NEXT_CYCLE")),
                source_model=str(spec.get("source_model", "predictive-cognition")),
                confidence=float(spec.get("confidence", 0.6)),
                assumptions=list(spec.get("assumptions", [])),
                evidence=list(spec.get("evidence", [])),
                verification_method=str(spec.get("verification_method", "future observation")),
                expiry=float(spec.get("expiry", now_ts() + 60.0)),
            )
            self.world_model.mark_prediction(
                WorldPrediction(
                    prediction_id=prediction.prediction_id.value,
                    entity_id=prediction.target.entity_id,
                    property_name=prediction.target.property_name,
                    expected_value=prediction.distribution.expected_value,
                    horizon=prediction.horizon.value,
                    source_model=prediction.source_model,
                    uncertainty=max(0.0, 1.0 - prediction.distribution.confidence),
                )
            )
        self.posted_prediction_specs = []

    def _interoception_metrics(self, prediction_receipt: PredictionReceipt, world_receipt: WorldReceipt) -> Dict[str, float]:
        workspace_load = min(1.0, len(world_receipt.snapshot.entities) / 10.0)
        tracked_predictions = max(0, len(prediction_receipt.predictions))
        prediction_failures = [
            item
            for item in prediction_receipt.residuals
            if item.prediction_id != "unexpected-observation" and item.residual_type != "NONE"
        ]
        error_rate = min(1.0, len(prediction_failures) / tracked_predictions) if tracked_predictions else 0.0
        last_action = ""
        if isinstance(self.last_cycle, dict):
            last_action = str(self.last_cycle.get("basin", {}).get("action", ""))
        elif self.last_cycle is not None:
            last_action = str(self.last_cycle.basin.get("action", ""))
        hold_duration = 1.0 if last_action == ActionState.HOLD.value else 0.0
        return {
            "cycle_budget_remaining": 1.0 - min(1.0, self.cycle_count / max(1, self.cycle_budget)),
            "workspace_occupancy": workspace_load,
            "prediction_error_rate": error_rate,
            "failed_action_rate": min(1.0, len(self.failures) / max(1, self.cycle_count)),
            "hold_duration": hold_duration,
        }

    def _confidence_outcomes(self) -> tuple[List[float], List[float]]:
        confidences: List[float] = []
        outcomes: List[float] = []
        for prediction in self.prediction_engine.predictions.values():
            if prediction.status in {"VERIFIED", "FALSIFIED"}:
                confidences.append(prediction.distribution.confidence)
                outcomes.append(1.0 if prediction.status == "VERIFIED" else 0.0)
        return confidences, outcomes

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
