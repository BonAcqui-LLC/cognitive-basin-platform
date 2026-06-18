"""
Bounded causal graph and deterministic local interventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class CausalNode:
    node_id: str
    label: str

    def to_record(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "label": self.label}


@dataclass
class CausalEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    direction: str
    relation_type: str
    conditions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    confounders: List[str] = field(default_factory=list)
    alternative_explanations: List[str] = field(default_factory=list)
    intervention_history: List[str] = field(default_factory=list)
    confidence: float = 0.4
    validity_scope: str = "LOCAL"

    def to_record(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "direction": self.direction,
            "relation_type": self.relation_type,
            "conditions": list(self.conditions),
            "evidence": list(self.evidence),
            "confounders": list(self.confounders),
            "alternative_explanations": list(self.alternative_explanations),
            "intervention_history": list(self.intervention_history),
            "confidence": self.confidence,
            "validity_scope": self.validity_scope,
        }


@dataclass
class CausalEvidence:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class CausalClaim:
    claim_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    evidence: List[CausalEvidence]
    confounders: List[str] = field(default_factory=list)
    alternative_explanations: List[str] = field(default_factory=list)
    confidence: float = 0.4
    validity_scope: str = "LOCAL"

    def to_record(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relation_type": self.relation_type,
            "evidence": _record(self.evidence),
            "confounders": list(self.confounders),
            "alternative_explanations": list(self.alternative_explanations),
            "confidence": self.confidence,
            "validity_scope": self.validity_scope,
        }


@dataclass
class CausalHypothesis:
    hypothesis_id: str
    detail: str
    status: str

    def to_record(self) -> Dict[str, Any]:
        return {"hypothesis_id": self.hypothesis_id, "detail": self.detail, "status": self.status}


@dataclass
class CausalConfounder:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class InterventionTarget:
    target_id: str
    target_type: str

    def to_record(self) -> Dict[str, Any]:
        return {"target_id": self.target_id, "target_type": self.target_type}


@dataclass
class InterventionVariable:
    name: str

    def to_record(self) -> Dict[str, Any]:
        return {"name": self.name}


@dataclass
class InterventionValue:
    value: Any

    def to_record(self) -> Dict[str, Any]:
        return {"value": self.value}


@dataclass
class InterventionControl:
    control_value: Any

    def to_record(self) -> Dict[str, Any]:
        return {"control_value": self.control_value}


@dataclass
class InterventionPrediction:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class InterventionObservation:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class InterventionComparison:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class InterventionProposal:
    proposal_id: str
    target: InterventionTarget
    variable: InterventionVariable
    value: InterventionValue
    control: InterventionControl
    prediction: InterventionPrediction
    allowed_domain: str
    simulated: bool = True

    def to_record(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target": self.target.to_record(),
            "variable": self.variable.to_record(),
            "value": self.value.to_record(),
            "control": self.control.to_record(),
            "prediction": self.prediction.to_record(),
            "allowed_domain": self.allowed_domain,
            "simulated": self.simulated,
        }


@dataclass
class CausalIntervention:
    intervention_id: str
    proposal: InterventionProposal
    outcome: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "proposal": self.proposal.to_record(),
            "outcome": self.outcome,
        }


@dataclass
class CausalOutcome:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class CausalRevision:
    revision_id: str
    claim_id: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"revision_id": self.revision_id, "claim_id": self.claim_id, "detail": self.detail}


@dataclass
class InterventionReceipt:
    interventions: List[CausalIntervention]
    comparisons: List[InterventionComparison]

    def to_record(self) -> Dict[str, Any]:
        return {"interventions": _record(self.interventions), "comparisons": _record(self.comparisons)}


@dataclass
class CausalReceipt:
    nodes: List[CausalNode]
    edges: List[CausalEdge]
    claims: List[CausalClaim]
    revisions: List[CausalRevision]
    intervention_receipt: InterventionReceipt

    def to_record(self) -> Dict[str, Any]:
        return {
            "nodes": _record(self.nodes),
            "edges": _record(self.edges),
            "claims": _record(self.claims),
            "revisions": _record(self.revisions),
            "intervention_receipt": self.intervention_receipt.to_record(),
        }


class CausalGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, CausalNode] = {}
        self.claims: Dict[str, CausalClaim] = {}
        self.edges: Dict[str, CausalEdge] = {}
        self.revisions: List[CausalRevision] = []
        self.interventions: List[CausalIntervention] = []

    def add_claim(self, claim: CausalClaim) -> None:
        self.claims[claim.claim_id] = claim
        self.nodes.setdefault(claim.source_node_id, CausalNode(claim.source_node_id, claim.source_node_id))
        self.nodes.setdefault(claim.target_node_id, CausalNode(claim.target_node_id, claim.target_node_id))
        self.edges[claim.claim_id] = CausalEdge(
            edge_id=f"edge-{claim.claim_id}",
            source_node_id=claim.source_node_id,
            target_node_id=claim.target_node_id,
            direction="FORWARD",
            relation_type=claim.relation_type,
            evidence=[item.detail for item in claim.evidence],
            confounders=list(claim.confounders),
            alternative_explanations=list(claim.alternative_explanations),
            confidence=claim.confidence,
            validity_scope=claim.validity_scope,
        )

    def apply_intervention(self, proposal: InterventionProposal, observed_value: Any) -> CausalIntervention:
        outcome = "INTERVENTION_SUPPORTED" if observed_value == proposal.value.value else "CONTRADICTED"
        intervention = CausalIntervention(
            intervention_id=f"intervention-{len(self.interventions) + 1:04d}",
            proposal=proposal,
            outcome=outcome,
        )
        self.interventions.append(intervention)
        for edge in self.edges.values():
            if edge.target_node_id == proposal.target.target_id or edge.source_node_id == proposal.target.target_id:
                edge.intervention_history.append(intervention.intervention_id)
                if outcome == "INTERVENTION_SUPPORTED":
                    edge.relation_type = "INTERVENTION_SUPPORTED"
                    edge.confidence = min(1.0, edge.confidence + 0.3)
                else:
                    edge.relation_type = "CONTRADICTED"
                    edge.confidence = max(0.05, edge.confidence - 0.2)
                    self.revisions.append(
                        CausalRevision(
                            revision_id=f"causal-revision-{len(self.revisions) + 1:04d}",
                            claim_id=edge.edge_id.replace("edge-", ""),
                            detail=f"intervention observed {observed_value}",
                        )
                    )
        return intervention

    def snapshot(self) -> CausalReceipt:
        return CausalReceipt(
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            claims=list(self.claims.values()),
            revisions=list(self.revisions),
            intervention_receipt=InterventionReceipt(
                interventions=list(self.interventions),
                comparisons=[InterventionComparison(item.outcome) for item in self.interventions],
            ),
        )


__all__ = [
    "CausalClaim",
    "CausalConfounder",
    "CausalEdge",
    "CausalEvidence",
    "CausalGraph",
    "CausalHypothesis",
    "CausalIntervention",
    "CausalNode",
    "CausalOutcome",
    "CausalReceipt",
    "CausalRevision",
    "InterventionComparison",
    "InterventionControl",
    "InterventionObservation",
    "InterventionPrediction",
    "InterventionProposal",
    "InterventionReceipt",
    "InterventionTarget",
    "InterventionValue",
    "InterventionVariable",
]
