"""
Conscious-episode contracts and bounded episode formation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..common import stable_hash


EpisodeID = str


@dataclass
class EpisodeTrigger:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class EpisodeContent:
    summary: str

    def to_record(self) -> Dict[str, Any]:
        return {"summary": self.summary}


@dataclass
class EpisodeContext:
    session_id: str
    participant: str
    repo_head: str

    def to_record(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "participant": self.participant, "repo_head": self.repo_head}


@dataclass
class EpisodePurpose:
    purpose_id: str
    description: str

    def to_record(self) -> Dict[str, Any]:
        return {"purpose_id": self.purpose_id, "description": self.description}


@dataclass
class EpisodePercepts:
    percept_ids: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"percept_ids": list(self.percept_ids)}


@dataclass
class EpisodeWorkspaceState:
    item_ids: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"item_ids": list(self.item_ids)}


@dataclass
class EpisodeSelfState:
    deviations: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"deviations": list(self.deviations)}


@dataclass
class EpisodeAlternatives:
    scenario_ids: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"scenario_ids": list(self.scenario_ids)}


@dataclass
class EpisodeDecision:
    epistemic_state: str
    action_state: str
    disposition: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "epistemic_state": self.epistemic_state,
            "action_state": self.action_state,
            "disposition": self.disposition,
        }


@dataclass
class EpisodeAction:
    description: str
    executed: bool
    authority_reason: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "executed": self.executed,
            "authority_reason": self.authority_reason,
        }


@dataclass
class EpisodeOutcome:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class EpisodeUncertainty:
    details: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"details": list(self.details)}


@dataclass
class EpisodeMemoryEffect:
    memory_ids: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"memory_ids": list(self.memory_ids)}


@dataclass
class ConsciousEpisode:
    episode_id: EpisodeID
    trigger: EpisodeTrigger
    content: EpisodeContent
    context: EpisodeContext
    purpose: EpisodePurpose
    percepts: EpisodePercepts
    workspace_state: EpisodeWorkspaceState
    self_state: EpisodeSelfState
    alternatives: EpisodeAlternatives
    decision: EpisodeDecision
    action: EpisodeAction
    outcome: EpisodeOutcome
    uncertainty: EpisodeUncertainty
    memory_effect: EpisodeMemoryEffect
    contradictions: List[str] = field(default_factory=list)
    privacy_scope: str = "SHARED_PROJECT"

    def to_record(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "trigger": self.trigger.to_record(),
            "content": self.content.to_record(),
            "context": self.context.to_record(),
            "purpose": self.purpose.to_record(),
            "percepts": self.percepts.to_record(),
            "workspace_state": self.workspace_state.to_record(),
            "self_state": self.self_state.to_record(),
            "alternatives": self.alternatives.to_record(),
            "decision": self.decision.to_record(),
            "action": self.action.to_record(),
            "outcome": self.outcome.to_record(),
            "uncertainty": self.uncertainty.to_record(),
            "memory_effect": self.memory_effect.to_record(),
            "contradictions": list(self.contradictions),
            "privacy_scope": self.privacy_scope,
        }


@dataclass
class EpisodeReceipt:
    episode: ConsciousEpisode

    def to_record(self) -> Dict[str, Any]:
        return {"episode": self.episode.to_record()}


class EpisodeRecorder:
    def record(
        self,
        *,
        session_id: str,
        participant: str,
        repo_head: str,
        purpose_id: str,
        purpose_description: str,
        percept_ids: List[str],
        workspace_item_ids: List[str],
        discrepancies: List[str],
        scenario_ids: List[str],
        epistemic_state: str,
        action_state: str,
        disposition: str,
        executed: bool,
        authority_reason: str,
        outcome_detail: str,
        uncertainty_details: List[str],
        contradiction_ids: List[str],
        memory_ids: List[str],
    ) -> EpisodeReceipt:
        seed = {
            "session_id": session_id,
            "repo_head": repo_head,
            "purpose_id": purpose_id,
            "percepts": percept_ids,
            "workspace": workspace_item_ids,
            "disposition": disposition,
            "memory_ids": memory_ids,
        }
        episode_id = f"episode-{stable_hash(seed)[:14]}"
        episode = ConsciousEpisode(
            episode_id=episode_id,
            trigger=EpisodeTrigger("bounded cognitive cycle"),
            content=EpisodeContent(f"{disposition} around {purpose_description or purpose_id}"),
            context=EpisodeContext(session_id, participant, repo_head),
            purpose=EpisodePurpose(purpose_id, purpose_description),
            percepts=EpisodePercepts(percept_ids),
            workspace_state=EpisodeWorkspaceState(workspace_item_ids),
            self_state=EpisodeSelfState(discrepancies),
            alternatives=EpisodeAlternatives(scenario_ids),
            decision=EpisodeDecision(epistemic_state, action_state, disposition),
            action=EpisodeAction("governed action proposal", executed, authority_reason),
            outcome=EpisodeOutcome(outcome_detail),
            uncertainty=EpisodeUncertainty(uncertainty_details),
            memory_effect=EpisodeMemoryEffect(memory_ids),
            contradictions=contradiction_ids,
        )
        return EpisodeReceipt(episode)


__all__ = [
    "ConsciousEpisode",
    "EpisodeAction",
    "EpisodeAlternatives",
    "EpisodeContent",
    "EpisodeContext",
    "EpisodeDecision",
    "EpisodeID",
    "EpisodeMemoryEffect",
    "EpisodeOutcome",
    "EpisodePercepts",
    "EpisodePurpose",
    "EpisodeReceipt",
    "EpisodeRecorder",
    "EpisodeSelfState",
    "EpisodeTrigger",
    "EpisodeUncertainty",
    "EpisodeWorkspaceState",
]
