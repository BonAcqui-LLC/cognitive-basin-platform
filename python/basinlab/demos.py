"""
Deterministic BasinLab demonstrations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict

from packages.ternary.states import ActionState, EpistemicState

from .associations import AssociationBeacon, AssociationField
from .compression import FullTrajectoryRecord, VerifiedCompression
from .contracts import ActionProposal
from .natural_math import advance_steps, extract_growth_graph, seeded_three_world
from .planner import GeneralistPlanner
from .providers import CompactReasonerProvider, GeneralistProvider
from .reliability import DecisionClaim, ReliabilityEngine, minority_wins_demo
from .recovery import RecoveryAttempt, RecoveryManager, RecoveryRequirement, RecoveryRoute
from .scars import ScarRegistry
from .session import BasinLabSession, replay_governed_session, run_vertical_slice_demo
from .spectrum import CandidateGenerator, CandidateTrajectory


def persistent_composition_demo() -> Dict[str, object]:
    with BasinLabSession() as session:
        first = session.execute_action(ActionProposal("d1", "seed", "alpha = 2"))
        second = session.execute_action(
            ActionProposal("d2", "compose", "beta = alpha + 3", parent_event_id=first.event_id)
        )
        namespace = session.materialize_namespace()
    return {"passed": namespace["beta"] == 5 and second.basin.action == ActionState.EXTEND, "namespace": namespace}


def runtime_error_recovery_demo() -> Dict[str, object]:
    demo = run_vertical_slice_demo()
    return {
        "passed": demo["second"]["feedback"]["exception_type"] == "NameError"
        and demo["third"]["basin"]["epistemic"] == "SUPPORTED",
        "details": demo,
    }


def unsafe_action_rejection_demo() -> Dict[str, object]:
    demo = run_vertical_slice_demo()
    return {"passed": demo["blocked"]["feedback"]["rejected"] is True, "details": demo["blocked"]}


def multiple_candidate_paths_demo() -> Dict[str, object]:
    generator = CandidateGenerator(
        deterministic_strategies=[
            lambda _purpose, _context: [
                CandidateTrajectory("c1", "north", "route north", "north-first", "det"),
                CandidateTrajectory("c2", "south", "route south", "south-first", "det"),
                CandidateTrajectory("c3", "east", "route east", "east-first", "det"),
            ]
        ]
    )
    spectrum = generator.generate("route", {})
    return {"passed": len(spectrum.retained) == 3, "count": len(spectrum.retained)}


def contradicted_majority_loses_demo() -> Dict[str, object]:
    decision = minority_wins_demo()
    return {
        "passed": decision.winning_answer == "5" and decision.final_action == ActionState.EXTEND,
        "winner": decision.winning_trajectory_id,
    }


def unresolved_critical_claim_demo() -> Dict[str, object]:
    engine = ReliabilityEngine()
    candidate = CandidateTrajectory("u1", "pending", "needs proof", "careful", "scripted")
    decision = engine.evaluate(
        [candidate],
        {"u1": [DecisionClaim("claim-u1", "Bridge is safe", "u1", True, required_evidence=["inspection"])]},
    )
    return {"passed": decision.final_action == ActionState.HOLD, "epistemic": decision.final_epistemic.value}


def compact_reasoner_no_action_authority_demo() -> Dict[str, object]:
    provider = CompactReasonerProvider(scripted_outputs=[{"answer": "x", "reasoning": "r", "approach": "a"}])
    return {"passed": provider.can_execute is False and provider.can_commit is False}


def generalist_plus_compact_specialist_demo() -> Dict[str, object]:
    generator = CandidateGenerator(
        providers=[
            GeneralistProvider(scripted_outputs=[{"answer": "broad", "reasoning": "wide", "approach": "general"}]),
            CompactReasonerProvider(
                scripted_outputs=[{"answer": "narrow", "reasoning": "exact", "approach": "compact"}]
            ),
        ]
    )
    spectrum = generator.generate("compare", {})
    providers = {candidate.provider for candidate in spectrum.retained}
    return {"passed": providers == {"generalist", "compact-reasoner"}, "providers": sorted(providers)}


def contradiction_scar_retract_demo() -> Dict[str, object]:
    scar = ScarRegistry().record_scar(
        "claim-1",
        "traj-1",
        EpistemicState.SUPPORTED,
        ["evidence-a"],
        "deterministic",
        1.0,
        [],
        True,
        "demo",
    )
    return {"passed": scar.prior_epistemic_state == EpistemicState.SUPPORTED, "scar_id": scar.scar_id}


def recovery_route_demo() -> Dict[str, object]:
    manager = RecoveryManager()
    route = RecoveryRoute(
        "route-1",
        "scar-1",
        [RecoveryRequirement("Need log", ["log-1"])],
        ["pressure-only"],
        ["CONTRADICTED->UNRESOLVED"],
        "review",
        "log present",
        "log missing",
        "review",
    )
    result = manager.attempt_recovery(route, RecoveryAttempt("route-1", ["log-1"], []))
    return {"passed": result.succeeded is True, "reasons": result.reasons}


def association_maturation_demo() -> Dict[str, object]:
    field = AssociationField()
    field.add_beacon(AssociationBeacon("assoc-1", "Route memory", "routing", salience=0.5, relevance=0.5))
    planner = GeneralistPlanner()
    planner.build_plan("routing", field)
    field.record_use("assoc-1", verified_success=True)
    beacon = field.beacons["assoc-1"]
    return {"passed": beacon.successful_use == 1 and beacon.access_count == 1, "relevance": beacon.relevance}


def fresh_process_restore_replay_demo() -> Dict[str, object]:
    with BasinLabSession() as session:
        first = session.execute_action(ActionProposal("r1", "seed", "alpha = 10"))
        second = session.execute_action(
            ActionProposal("r2", "update", "beta = alpha + 2", parent_event_id=first.event_id)
        )
        old_pid = session.kernel.pid
        restored = session.restore_checkpoint_in_fresh_process()
        replay = replay_governed_session(session.export_events())
        passed = restored["beta"] == 12 and replay["namespace"]["beta"] == 12 and session.kernel.pid != old_pid
        return {"passed": passed, "replay_errors": replay["errors"]}


def verified_compression_demo() -> Dict[str, object]:
    full = FullTrajectoryRecord(
        purpose="inspection",
        decisive_claims=["claim-1"],
        evidence_links={"claim-1": ["report"], "claim-2": ["note"]},
        contradictory_evidence={"claim-2": ["scan"]},
        failures_changed_route=["first-failure"],
        scar_ids=["scar-1"],
        recovery_decisions=["route-1:success"],
        commit_decision="commit-1",
        replay_references={"session": "s1"},
        final_epistemic="UNRESOLVED",
        uncertainty=["follow-up"],
    )
    compressed = VerifiedCompression(
        lambda left, right: left.final_epistemic == right.final_epistemic and left.replay_references == right.replay_references
    ).compress(full)
    return {"passed": compressed.final_epistemic == "UNRESOLVED", "digest": compressed.digest}


def conflicting_tool_output_demo() -> Dict[str, object]:
    engine = ReliabilityEngine()
    decision = engine.evaluate(
        [
            CandidateTrajectory("a", "yes", "tool says yes", "tool-a", "scripted"),
            CandidateTrajectory("b", "yes", "tool says yes too fast", "tool-b", "scripted"),
        ],
        {
            "a": [DecisionClaim("claim-a", "safe", "a", True, required_evidence=["report"])],
            "b": [DecisionClaim("claim-b", "safe", "b", True, contradictory_evidence=["scan says unsafe"])],
        },
    )
    return {"passed": decision.final_action == ActionState.HOLD, "epistemic": decision.final_epistemic.value}


def natural_math_persistent_growth_demo() -> Dict[str, object]:
    with BasinLabSession() as session:
        session.load_bindings(
            {
                "seeded_three_world": seeded_three_world,
                "advance_steps": advance_steps,
                "extract_growth_graph": extract_growth_graph,
            }
        )
        create = session.execute_action(ActionProposal("nm1", "create world", "world = seeded_three_world(seed=31)"))
        advance = session.execute_action(
            ActionProposal(
                "nm2",
                "advance world",
                "summary = advance_steps(world, steps=3)\ngraph = extract_growth_graph(world)",
                parent_event_id=create.event_id,
            )
        )
        namespace = session.materialize_namespace()
    return {
        "passed": advance.basin.action == ActionState.EXTEND and namespace["world"].step_count == 3,
        "step_count": namespace["world"].step_count,
    }


def capability_boundary_sampling_demo() -> Dict[str, object]:
    with BasinLabSession() as session:
        blocked = session.execute_action(ActionProposal("cap-1", "blocked import", "import os"))
    provider = CompactReasonerProvider(scripted_outputs=[])
    return {
        "passed": blocked.feedback.rejected is True and provider.can_commit is False,
        "reason": blocked.feedback.rejection_reason,
    }


SCENARIOS: Dict[str, Callable[[], Dict[str, object]]] = {
    "persistent_composition": persistent_composition_demo,
    "runtime_error_recovery": runtime_error_recovery_demo,
    "unsafe_action_rejection": unsafe_action_rejection_demo,
    "multiple_candidate_paths": multiple_candidate_paths_demo,
    "contradicted_majority_loses": contradicted_majority_loses_demo,
    "unresolved_critical_claim": unresolved_critical_claim_demo,
    "compact_reasoner_no_action_authority": compact_reasoner_no_action_authority_demo,
    "generalist_plus_compact_specialist": generalist_plus_compact_specialist_demo,
    "contradiction_scar_retract": contradiction_scar_retract_demo,
    "recovery_route": recovery_route_demo,
    "association_maturation": association_maturation_demo,
    "fresh_process_restore_replay": fresh_process_restore_replay_demo,
    "verified_compression": verified_compression_demo,
    "conflicting_tool_output": conflicting_tool_output_demo,
    "natural_math_persistent_growth": natural_math_persistent_growth_demo,
    "capability_boundary_sampling": capability_boundary_sampling_demo,
}


def run_scenario(name: str) -> Dict[str, object]:
    if name not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {name}")
    result = SCENARIOS[name]()
    return {"scenario": name, **result}


def run_all_scenarios(artifact_dir: str | None = None) -> Dict[str, object]:
    results = [run_scenario(name) for name in SCENARIOS]
    summary = {
        "passed": all(result["passed"] for result in results),
        "scenario_count": len(results),
        "results": results,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
