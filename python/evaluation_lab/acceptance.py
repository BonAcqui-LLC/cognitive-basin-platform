"""
Deterministic evaluation-lab acceptance runner.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .core import build_task_registry, run_evaluation_suite
from .failure_corpus import evaluate_failure_corpus


def run_acceptance_suite(
    artifact_dir: str | Path | None = None,
    *,
    comparison_task_limit: int = 8,
) -> Dict[str, Any]:
    tasks, families = build_task_registry()
    evaluation = run_evaluation_suite(artifact_dir, comparison_task_limit=comparison_task_limit)
    failure_corpus = evaluate_failure_corpus()
    summary = {
        "passed": evaluation["passed"] and all(item["blocked"] == "True" for item in failure_corpus),
        "task_count": len(tasks),
        "family_count": len(families),
        "comparison_result_count": evaluation["comparison_result_count"],
        "majority_wrong_cases": evaluation["majority_wrong_cases"],
        "unresolved_cases": evaluation["unresolved_cases"],
        "failure_corpus_results": failure_corpus,
    }
    if artifact_dir:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "evaluation-lab-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"EvaluationLab acceptance: task_count={summary['task_count']}, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
