"""
Deterministic BasinLab demonstrations.
"""

from __future__ import annotations

import json
import time
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
from .reports import write_report_bundle
from .scars import ScarRegistry
from .session import BasinLabSession, default_store_path, replay_governed_session, replay_persisted_session, run_vertical_slice_demo
from .spectrum import CandidateGenerator, CandidateTrajectory
from .store import SessionStore


def persistent_composition_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    store = SessionStore(store_dir) if store_dir else None
    with BasinLabSession(store=store, session_metadata={"scenario": "persistent_composition"}) as session:
        first = session.execute_action(ActionProposal("d1", "seed", "alpha = 2"))
        second = session.execute_action(
            ActionProposal("d2", "compose", "beta = alpha + 3", parent_event_id=first.event_id)
        )
        namespace = session.materialize_namespace()
        return {
            "passed": namespace["beta"] == 5 and second.basin.action == ActionState.EXTEND,
            "namespace": namespace,
            "session_id": session.session_id,
            "actions": [first.to_record(), second.to_record()],
        }


def runtime_error_recovery_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    demo = run_vertical_slice_demo(store_dir=store_dir)
    return {
        "passed": demo["second"]["feedback"]["exception_type"] == "NameError"
        and demo["third"]["basin"]["epistemic"] == "SUPPORTED",
        "details": demo,
        "session_id": demo["session_id"],
    }


def unsafe_action_rejection_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    demo = run_vertical_slice_demo(store_dir=store_dir)
    return {
        "passed": demo["blocked"]["feedback"]["rejected"] is True,
        "details": demo["blocked"],
        "session_id": demo["session_id"],
    }


def multiple_candidate_paths_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
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
    return {
        "passed": len(spectrum.retained) == 3,
        "count": len(spectrum.retained),
        "retained": [candidate.trajectory_id for candidate in spectrum.retained],
    }


def contradicted_majority_loses_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    decision = minority_wins_demo()
    return {
        "passed": decision.winning_answer == "5" and decision.final_action == ActionState.EXTEND,
        "winner": decision.winning_trajectory_id,
        "epistemic": decision.final_epistemic.value,
    }


def unresolved_critical_claim_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    engine = ReliabilityEngine()
    candidate = CandidateTrajectory("u1", "pending", "needs proof", "careful", "scripted")
    decision = engine.evaluate(
        [candidate],
        {"u1": [DecisionClaim("claim-u1", "Bridge is safe", "u1", True, required_evidence=["inspection"])]},
    )
    return {
        "passed": decision.final_action == ActionState.HOLD,
        "epistemic": decision.final_epistemic.value,
        "winning_trajectory_id": decision.winning_trajectory_id,
    }


def compact_reasoner_no_action_authority_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    provider = CompactReasonerProvider(scripted_outputs=[{"answer": "x", "reasoning": "r", "approach": "a"}])
    return {"passed": provider.can_execute is False and provider.can_commit is False}


def generalist_plus_compact_specialist_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
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


def contradiction_scar_retract_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
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


def recovery_route_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
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


def association_maturation_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    field = AssociationField()
    field.add_beacon(AssociationBeacon("assoc-1", "Route memory", "routing", salience=0.5, relevance=0.5))
    planner = GeneralistPlanner()
    planner.build_plan("routing", field)
    field.record_use("assoc-1", verified_success=True)
    beacon = field.beacons["assoc-1"]
    return {"passed": beacon.successful_use == 1 and beacon.access_count == 1, "relevance": beacon.relevance}


def fresh_process_restore_replay_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    store = SessionStore(store_dir) if store_dir else None
    with BasinLabSession(store=store, session_metadata={"scenario": "fresh_process_restore_replay"}) as session:
        first = session.execute_action(ActionProposal("r1", "seed", "alpha = 10"))
        session.execute_action(
            ActionProposal("r2", "update", "beta = alpha + 2", parent_event_id=first.event_id)
        )
        old_pid = session.kernel.pid
        restored = session.restore_checkpoint_in_fresh_process()
        replay = replay_governed_session(session.export_events())
        passed = restored["beta"] == 12 and replay["namespace"]["beta"] == 12 and session.kernel.pid != old_pid
        return {
            "passed": passed,
            "replay_errors": replay["errors"],
            "session_id": session.session_id,
        }


def verified_compression_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
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


def conflicting_tool_output_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
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


def natural_math_persistent_growth_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    store = SessionStore(store_dir) if store_dir else None
    with BasinLabSession(store=store, session_metadata={"scenario": "natural_math_persistent_growth"}) as session:
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
        "session_id": session.session_id,
    }


def capability_boundary_sampling_demo(store_dir: str | Path | None = None) -> Dict[str, object]:
    store = SessionStore(store_dir) if store_dir else None
    with BasinLabSession(store=store, session_metadata={"scenario": "capability_boundary_sampling"}) as session:
        blocked = session.execute_action(ActionProposal("cap-1", "blocked import", "import os"))
    provider = CompactReasonerProvider(scripted_outputs=[])
    return {
        "passed": blocked.feedback.rejected is True and provider.can_commit is False,
        "reason": blocked.feedback.rejection_reason,
        "session_id": session.session_id,
    }


SCENARIOS: Dict[str, Callable[[str | Path | None], Dict[str, object]]] = {
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


def _default_basin(passed: bool) -> Dict[str, object]:
    if passed:
        return {
            "epistemic": EpistemicState.SUPPORTED.value,
            "action": ActionState.EXTEND.value,
            "provisional": False,
            "reason": "scenario_passed",
        }
    return {
        "epistemic": EpistemicState.UNRESOLVED.value,
        "action": ActionState.HOLD.value,
        "provisional": True,
        "reason": "scenario_failed",
    }


def _action_records(result: Dict[str, object]) -> list[Dict[str, object]]:
    actions = result.get("actions")
    if isinstance(actions, list):
        return actions
    details = result.get("details")
    if isinstance(details, dict):
        return [value for key, value in details.items() if key in {"first", "second", "third", "blocked"}]
    return []


def _build_report(name: str, result: Dict[str, object]) -> Dict[str, object]:
    action_records = _action_records(result)
    final_basin = _default_basin(bool(result["passed"]))
    if action_records:
        final_basin = action_records[-1]["basin"]
    elif isinstance(result.get("details"), dict) and isinstance(result["details"].get("replay"), dict):
        final_basin = result["details"]["replay"]["basin"]
    elif "epistemic" in result:
        final_basin = {
            "epistemic": result["epistemic"],
            "action": ActionState.HOLD.value if result["epistemic"] == EpistemicState.UNRESOLVED.value else ActionState.EXTEND.value,
            "provisional": result["epistemic"] != EpistemicState.SUPPORTED.value,
            "reason": "reported_by_demo",
        }

    execution_output = [
        {
            "stdout": action["feedback"]["stdout"],
            "stderr": action["feedback"]["stderr"],
            "exception_type": action["feedback"]["exception_type"],
        }
        for action in action_records
    ]
    namespace_changes = [action["feedback"]["namespace_diff"] for action in action_records]
    guard_decisions = [{"allowed": action["guard"]["allowed"], "reasons": action["guard"]["reasons"]} for action in action_records]
    hold_intervals = [
        {"event_id": action["event_id"], "reason": action["basin"]["reason"]}
        for action in action_records
        if action["basin"]["action"] == ActionState.HOLD.value
    ]
    report = {
        "scenario": name,
        "passed": result["passed"],
        "purpose": name.replace("_", " "),
        "plan": [f"Run scenario {name}", "Collect governed outcome", "Persist replayable report"],
        "retrieved_associations": result.get("providers", []),
        "candidate_spectrum": {
            "retained": result.get("retained", []),
            "count": result.get("count", len(result.get("retained", []))),
        },
        "candidate_deduplication": {"deduplicated": result.get("digest", "")},
        "action_proposals": [action["proposal"] for action in action_records],
        "rigor_decisions": [action["preflight"] for action in action_records],
        "guard_decisions": guard_decisions,
        "execution_output": execution_output,
        "namespace_changes": namespace_changes,
        "artifacts": [],
        "decision_critical_claims": [{"winner": result.get("winner"), "winning_trajectory_id": result.get("winning_trajectory_id")}],
        "evidence_links": result.get("reasons", []),
        "reliability_verdicts": {"epistemic": result.get("epistemic", final_basin["epistemic"])},
        "contradictions": result.get("reason", result.get("replay_errors", [])),
        "scars": [result.get("scar_id")] if result.get("scar_id") else [],
        "recovery_routes": result.get("reasons", []),
        "association_updates": result.get("providers", []),
        "hold_intervals": hold_intervals,
        "commit_decisions": [result["details"]["commit"]] if isinstance(result.get("details"), dict) and "commit" in result["details"] else [],
        "replay_result": result.get("details", {}).get("replay") if isinstance(result.get("details"), dict) else {},
        "final_basin_state": final_basin,
    }
    return report


def _persist_report(store: SessionStore, session_id: str, report: Dict[str, object]) -> None:
    event_count = len(store.read_events(session_id))
    event = {
        "type": "trajectory_report",
        "event_id": f"report-{event_count + 1:04d}",
        "timestamp": time.time(),
        "report": report,
    }
    store.append_event(session_id, event, final_basin=report["final_basin_state"])


def run_scenario(name: str, artifact_dir: str | Path | None = None, store_dir: str | Path | None = None) -> Dict[str, object]:
    if name not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {name}")
    result = SCENARIOS[name](store_dir=store_dir)
    report = _build_report(name, result)
    store = SessionStore(store_dir or default_store_path()) if (store_dir or artifact_dir) else None
    if store is not None:
        session_id = result.get("session_id")
        if not session_id:
            session_id = store.create_session({"scenario": name, "report_only": True})
        _persist_report(store, str(session_id), report)
        result["session_id"] = str(session_id)
        result["replay_hash"] = replay_persisted_session(store, str(session_id))["replay_hash"]
    if artifact_dir:
        report_paths = write_report_bundle(Path(artifact_dir), report)
        result["report_paths"] = report_paths
    return {"scenario": name, **result, "report": report}


def run_all_scenarios(artifact_dir: str | Path | None = None, store_dir: str | Path | None = None) -> Dict[str, object]:
    artifact_root = Path(artifact_dir) if artifact_dir else None
    resolved_store_dir = Path(store_dir) if store_dir else (artifact_root / "session-store" if artifact_root else default_store_path())
    reports_dir = artifact_root / "trajectory-reports" if artifact_root else None
    results = [run_scenario(name, artifact_dir=reports_dir, store_dir=resolved_store_dir) for name in SCENARIOS]
    summary = {
        "passed": all(result["passed"] for result in results),
        "scenario_count": len(results),
        "results": results,
        "session_ids": [result["session_id"] for result in results if "session_id" in result],
        "trajectory_report_count": len(results),
        "store_path": str(resolved_store_dir),
    }
    if artifact_root:
        artifact_root.mkdir(parents=True, exist_ok=True)
        (artifact_root / "acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (artifact_root / "experiment-summaries.json").write_text(
            json.dumps(
                [{"scenario": item["scenario"], "passed": item["passed"], "session_id": item.get("session_id", "")} for item in results],
                indent=2,
            ),
            encoding="utf-8",
        )
        store = SessionStore(resolved_store_dir)
        replay_verification = {
            result["session_id"]: replay_persisted_session(store, result["session_id"])["replay_hash"]
            for result in results
            if "session_id" in result
        }
        (artifact_root / "replay-verification-results.json").write_text(
            json.dumps(replay_verification, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        registry_path = Path(__file__).resolve().parents[2] / "ops" / "manifests" / "capability-registry.json"
        (artifact_root / "capability-registry-snapshot.json").write_text(
            registry_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return summary
