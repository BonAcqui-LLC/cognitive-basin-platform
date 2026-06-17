"""
Minimal CLI surface for BasinLab scenarios.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.contracts.capability_registry import load_registry
from python.provider_lab import local_model_inventory, provider_inventory
from ..demos import SCENARIOS, run_all_scenarios, run_scenario
from ..providers import (
    AnthropicCompatibleProvider,
    CompactReasonerProvider,
    GeneralistProvider,
    OpenAICompatibleProvider,
    QwenCompatibleProvider,
    ScriptedProvider,
    VibeThinkerProvider,
)
from ..session import default_store_path, inspect_persisted_session, replay_persisted_session
from ..store import SessionStore


def _print(value: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, default=str))
    else:
        print(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-dir", default="")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("scenario")
    run_parser.add_argument("--json", action="store_true")
    run_parser.add_argument("--artifact-dir", default="")

    run_all_parser = subparsers.add_parser("run-all")
    run_all_parser.add_argument("--json", action="store_true")
    run_all_parser.add_argument("--artifact-dir", default="")

    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("session_id")
    replay_parser.add_argument("--json", action="store_true")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("session_id")
    inspect_parser.add_argument("--json", action="store_true")

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("session_a")
    diff_parser.add_argument("session_b")
    diff_parser.add_argument("--json", action="store_true")

    caps_parser = subparsers.add_parser("capabilities")
    caps_parser.add_argument("--json", action="store_true")

    providers_parser = subparsers.add_parser("providers")
    providers_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    store = SessionStore(args.store_dir or default_store_path())

    if args.command == "run":
        result = run_scenario(args.scenario, artifact_dir=args.artifact_dir or None, store_dir=store.root)
        if args.artifact_dir:
            path = Path(args.artifact_dir)
            path.mkdir(parents=True, exist_ok=True)
            (path / f"{args.scenario}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        _print(result, args.json)
        return 0 if result["passed"] else 1
    if args.command == "run-all":
        result = run_all_scenarios(args.artifact_dir or None, store_dir=store.root)
        _print(result, args.json)
        return 0 if result["passed"] else 1
    if args.command in {"replay", "inspect"}:
        payload = (
            replay_persisted_session(store, args.session_id)
            if args.command == "replay"
            else inspect_persisted_session(store, args.session_id)
        )
        if args.command == "replay":
            payload = {
                **payload,
                "basin": payload["basin"].to_record(),
            }
        _print(payload, args.json)
        return 0
    if args.command == "diff":
        diff = store.diff_sessions(args.session_a, args.session_b)
        _print(diff, args.json)
        return 0
    if args.command == "capabilities":
        registry = load_registry()
        _print({"scenarios": sorted(SCENARIOS), "registry_entries": sorted(registry)}, args.json)
        return 0
    if args.command == "providers":
        providers = [
            ScriptedProvider(),
            GeneralistProvider(),
            CompactReasonerProvider(),
            OpenAICompatibleProvider(),
            AnthropicCompatibleProvider(),
            QwenCompatibleProvider(),
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
        _print({"providers": payload, "inventory": provider_inventory(), "local_model_inventory": local_model_inventory()}, args.json)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
