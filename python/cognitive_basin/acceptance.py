"""
Aggregate deterministic acceptance entrypoint.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from python.basinlab.demos import run_all_scenarios
from python.action_permit.acceptance import run_acceptance_suite as run_action_permit_acceptance
from python.consciousness_lab.acceptance import run_acceptance_suite as run_consciousness_acceptance
from python.connector_lab.acceptance import run_acceptance_suite as run_connector_lab_acceptance
from python.ephux_local.acceptance import run_acceptance_suite as run_ephux_acceptance
from python.evaluation_lab.acceptance import run_acceptance_suite as run_evaluation_acceptance
from python.memory_governance.acceptance import run_acceptance_suite as run_memory_governance_acceptance
from python.natural_math_lab.acceptance import run_acceptance_suite as run_natural_math_acceptance
from python.predictive_cognition.acceptance import run_acceptance_suite as run_predictive_cognition_acceptance
from python.provider_lab.acceptance import run_acceptance_suite as run_provider_acceptance
from python.sandbox_lab.acceptance import run_acceptance_suite as run_sandbox_acceptance


ROOT = Path(__file__).resolve().parents[2]


def _current_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _suite_metadata(
    name: str,
    summary: dict,
    *,
    elapsed_s: float,
    artifact_root: Path | None,
    exact_commit: str,
    limitations: list[str],
    skipped_operations: list[str],
) -> dict:
    return {
        "suite_name": name,
        "passed": bool(summary["passed"]),
        "scenario_count": summary.get("scenario_count", summary.get("task_count", summary.get("run_count", 0))),
        "result": "PASS" if summary["passed"] else "FAIL",
        "elapsed_time_s": round(elapsed_s, 3),
        "evidence_artifact": str(artifact_root) if artifact_root else "",
        "exact_commit": exact_commit,
        "skipped_operations": skipped_operations,
        "limitations": limitations,
    }


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> dict:
    root = Path(artifact_dir) if artifact_dir else None
    if root:
        root.mkdir(parents=True, exist_ok=True)
    exact_commit = _current_commit()

    def run_named(name: str, fn, child: str) -> tuple[dict, dict]:
        child_root = (root / child) if root else None
        started = time.time()
        result = fn(child_root)
        limitation_map = {
            "basinlab": ["Deterministic local demonstrations only."],
            "ephux_local": ["Loopback-only local service path; no deployment verification."],
            "provider_lab": ["Deterministic fixtures only; live provider calls remain disabled."],
            "sandbox_lab": ["AST and bounded-worker sandbox checks only."],
            "evaluation_lab": ["Local deterministic registry and failure corpus only."],
            "natural_math_lab": ["Encoded local simulation only; no empirical claim beyond rules."],
            "memory_governance": result.get("limitations", ["Session-scoped governed memory only in current tranche."]),
            "action_permit": ["Explicit participant-issued permits only; no inherited authority."],
            "connector_lab": ["Fixture-backed connector execution only; no production deployment or live writes."],
            "consciousness_lab": ["Operational machine-consciousness layer only; no claim of subjective experience or sentience."],
            "predictive_cognition": ["Machine-native predictive cognition only; no claim of subjective experience or hidden mental-state access."],
        }
        skipped_map = {
            "basinlab": ["No production commit or deployment."],
            "ephux_local": ["No browser-store packaging or remote hosting."],
            "provider_lab": ["No live remote provider invocation."],
            "sandbox_lab": ["No privileged host operations."],
            "evaluation_lab": ["No live external benchmark execution."],
            "natural_math_lab": ["No non-deterministic or remote workloads."],
            "memory_governance": ["No auto-deletion and no legal-hold release workflow."],
            "action_permit": ["No implicit approvals, role inference, or credential-derived authority."],
            "connector_lab": ["No live external writes and no production deployment."],
            "consciousness_lab": ["No subjective-experience claims and no autonomous external authority."],
            "predictive_cognition": ["No production deployment and no unrestricted autonomous learning."],
        }
        return result, _suite_metadata(
            name,
            result,
            elapsed_s=time.time() - started,
            artifact_root=child_root,
            exact_commit=exact_commit,
            limitations=limitation_map[name],
            skipped_operations=skipped_map[name],
        )

    basinlab, basinlab_meta = run_named("basinlab", run_all_scenarios, "basinlab")
    ephux, ephux_meta = run_named("ephux_local", run_ephux_acceptance, "ephux")
    provider, provider_meta = run_named("provider_lab", run_provider_acceptance, "provider_lab")
    sandbox, sandbox_meta = run_named("sandbox_lab", run_sandbox_acceptance, "sandbox_lab")
    evaluation, evaluation_meta = run_named("evaluation_lab", run_evaluation_acceptance, "evaluation_lab")
    natural_math, natural_math_meta = run_named("natural_math_lab", run_natural_math_acceptance, "natural_math_lab")
    memory_governance, memory_meta = run_named("memory_governance", run_memory_governance_acceptance, "memory_governance")
    action_permit, action_permit_meta = run_named("action_permit", run_action_permit_acceptance, "action_permit")
    connector_lab, connector_meta = run_named("connector_lab", run_connector_lab_acceptance, "connector_lab")
    consciousness_lab, consciousness_meta = run_named("consciousness_lab", run_consciousness_acceptance, "consciousness_lab")
    predictive_cognition, predictive_cognition_meta = run_named("predictive_cognition", run_predictive_cognition_acceptance, "predictive_cognition")
    summary = {
        "passed": all(
            [
                basinlab["passed"],
                ephux["passed"],
                provider["passed"],
                sandbox["passed"],
                evaluation["passed"],
                natural_math["passed"],
                memory_governance["passed"],
                action_permit["passed"],
                connector_lab["passed"],
                consciousness_lab["passed"],
                predictive_cognition["passed"],
            ]
        ),
        "exact_commit": exact_commit,
        "suites": {
            "basinlab": basinlab_meta,
            "ephux_local": ephux_meta,
            "provider_lab": provider_meta,
            "sandbox_lab": sandbox_meta,
            "evaluation_lab": evaluation_meta,
            "natural_math_lab": natural_math_meta,
            "memory_governance": memory_meta,
            "action_permit": action_permit_meta,
            "connector_lab": connector_meta,
            "consciousness_lab": consciousness_meta,
            "predictive_cognition": predictive_cognition_meta,
        },
    }
    if root:
        (root / "combined-acceptance-manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"Aggregate acceptance: {len(summary['suites'])} suites, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
