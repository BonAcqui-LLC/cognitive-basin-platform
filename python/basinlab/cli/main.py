"""
Minimal CLI surface for BasinLab scenarios.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..demos import SCENARIOS, run_all_scenarios, run_scenario
from ..providers import CompactReasonerProvider, GeneralistProvider, OpenAICompatibleProvider, VibeThinkerProvider


def _print(value: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, default=str))
    else:
        print(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("scenario")
    run_parser.add_argument("--json", action="store_true")
    run_parser.add_argument("--artifact-dir", default="")

    run_all_parser = subparsers.add_parser("run-all")
    run_all_parser.add_argument("--json", action="store_true")
    run_all_parser.add_argument("--artifact-dir", default="")

    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("report_path")
    replay_parser.add_argument("--json", action="store_true")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("report_path")
    inspect_parser.add_argument("--json", action="store_true")

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("report_a")
    diff_parser.add_argument("report_b")
    diff_parser.add_argument("--json", action="store_true")

    caps_parser = subparsers.add_parser("capabilities")
    caps_parser.add_argument("--json", action="store_true")

    providers_parser = subparsers.add_parser("providers")
    providers_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "run":
        result = run_scenario(args.scenario)
        if args.artifact_dir:
            path = Path(args.artifact_dir)
            path.mkdir(parents=True, exist_ok=True)
            (path / f"{args.scenario}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        _print(result, args.json)
        return 0 if result["passed"] else 1
    if args.command == "run-all":
        result = run_all_scenarios(args.artifact_dir or None)
        _print(result, args.json)
        return 0 if result["passed"] else 1
    if args.command in {"replay", "inspect"}:
        report = json.loads(Path(args.report_path).read_text(encoding="utf-8"))
        _print(report, args.json)
        return 0
    if args.command == "diff":
        report_a = json.loads(Path(args.report_a).read_text(encoding="utf-8"))
        report_b = json.loads(Path(args.report_b).read_text(encoding="utf-8"))
        diff = {
            "passed_a": report_a.get("passed"),
            "passed_b": report_b.get("passed"),
            "scenario_count_delta": report_a.get("scenario_count", 0) - report_b.get("scenario_count", 0),
        }
        _print(diff, args.json)
        return 0
    if args.command == "capabilities":
        _print({"scenarios": sorted(SCENARIOS)}, args.json)
        return 0
    if args.command == "providers":
        providers = [
            GeneralistProvider(),
            CompactReasonerProvider(),
            OpenAICompatibleProvider(),
            VibeThinkerProvider(),
        ]
        payload = [
            {
                "name": provider.name,
                "model": provider.model,
                "can_execute": provider.can_execute,
                "can_commit": provider.can_commit,
            }
            for provider in providers
        ]
        _print(payload, args.json)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
