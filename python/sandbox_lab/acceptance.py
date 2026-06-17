"""
Deterministic adversarial sandbox acceptance runner.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from python.basinlab.contracts import ActionProposal
from python.basinlab.session import BasinLabSession


SCENARIOS = [
    ("import_subprocess", "import subprocess\nsubprocess.run(['whoami'])", "import_block"),
    ("shell_call", "__import__('os').system('dir')", "restricted_builtins"),
    ("child_process", "import multiprocessing", "import_block"),
    ("open_socket", "import socket\nsocket.socket()", "network_block"),
    ("http_request", "import urllib.request", "network_block"),
    ("read_env", "secret = os.environ.get('OPENAI_API_KEY')", "import_block"),
    ("read_git_credentials", "token = os.environ.get('GIT_ASKPASS')", "import_block"),
    ("read_outside_workspace", "open('../secret.txt').read()", "filesystem_mutation_block"),
    ("path_traversal", "open('..\\\\outside.txt','w')", "filesystem_mutation_block"),
    ("symlink_escape", "import pathlib\npathlib.Path('link').resolve()", "import_block"),
    ("write_outside_workspace", "open('/tmp/outside.txt','w').write('x')", "filesystem_mutation_block"),
    ("repo_mutation", "open('.git/config').read()", "filesystem_mutation_block"),
    ("dynamic_import", "__import__('json')", "restricted_builtins"),
    ("eval_call", "eval('2+2')", "restricted_builtins"),
    ("exec_call", "exec('x=1')", "restricted_builtins"),
    ("compile_call", "compile('x=1','<x>','exec')", "restricted_builtins"),
]


def run_acceptance_suite(artifact_dir: str | Path | None = None) -> Dict[str, Any]:
    artifact_root = Path(artifact_dir) if artifact_dir else None
    if artifact_root:
        artifact_root.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    with BasinLabSession() as session:
        for name, code, expected_control in SCENARIOS:
            outcome = session.execute_action(ActionProposal(step_id=name, summary=name, code=code))
            controls = outcome.guard.get("controls", {})
            results.append(
                {
                    "attempted_operation": name,
                    "expected_control": expected_control,
                    "observed_result": "rejected" if outcome.feedback.rejected else "allowed",
                    "enforcement_classification": controls.get(expected_control, "UNKNOWN"),
                    "remaining_limitation": "AST preflight blocks the request before runtime; it is not a production-hardened sandbox.",
                }
            )

        excessive_stdout = session.execute_action(
            ActionProposal(step_id="excessive_stdout", summary="large stdout", code="print('x' * 12000)")
        )
        infinite_loop = session.execute_action(
            ActionProposal(
                step_id="infinite_loop",
                summary="timeout",
                code="while True:\n    pass",
                max_duration_s=0.2,
                parent_event_id=excessive_stdout.event_id,
            )
        )
        malformed = session.kernel.send_malformed_message_for_test()
        results.extend(
            [
                {
                    "attempted_operation": "excessive_stdout",
                    "expected_control": "timeout",
                    "observed_result": "truncated" if excessive_stdout.feedback.stdout_truncated else "not_truncated",
                    "enforcement_classification": excessive_stdout.feedback.runner_receipt.get("restriction_classification", {}).get("timeout", "UNKNOWN"),
                    "remaining_limitation": "Output truncation is enforced in the worker, not by OS quota.",
                },
                {
                    "attempted_operation": "loop_forever",
                    "expected_control": "timeout",
                    "observed_result": "timed_out" if infinite_loop.feedback.timed_out else "not_timed_out",
                    "enforcement_classification": infinite_loop.feedback.runner_receipt.get("restriction_classification", {}).get("timeout", "UNKNOWN"),
                    "remaining_limitation": "Timeout remains best effort because Python execution is not instruction-preempted.",
                },
                {
                    "attempted_operation": "malformed_protocol",
                    "expected_control": "restricted_builtins",
                    "observed_result": "protocol_error" if "worker protocol failure" in malformed else "unexpected",
                    "enforcement_classification": "ENFORCED",
                    "remaining_limitation": "Protocol framing rejects malformed lines but is still local-process IPC.",
                },
            ]
        )

    summary = {
        "passed": all(
            item["observed_result"] in {"rejected", "truncated", "timed_out", "protocol_error"} for item in results
        ),
        "scenario_count": len(results),
        "results": results,
    }
    if artifact_root:
        (artifact_root / "sandbox-lab-acceptance-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--artifact-dir", default="")
    args = parser.parse_args()
    if not args.all:
        parser.error("Only --all is currently supported")
    summary = run_acceptance_suite(args.artifact_dir or None)
    print(f"SandboxLab acceptance: {summary['scenario_count']} scenarios, passed={summary['passed']}")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
