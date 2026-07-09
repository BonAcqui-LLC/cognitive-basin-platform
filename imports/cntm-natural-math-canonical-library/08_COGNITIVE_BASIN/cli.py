#!/usr/bin/env python3
"""Operational Self + Fractal Attractor Memory CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.operational_self.continuity_spine import OperationalSelfEngine

_ENGINE: OperationalSelfEngine | None = None


def _engine() -> OperationalSelfEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = OperationalSelfEngine()
    return _ENGINE


def _engine_with_state() -> OperationalSelfEngine:
    eng = OperationalSelfEngine()
    state_path = eng.output_root / "self_state.json"
    if state_path.exists():
        eng.run_demo()
        return OperationalSelfEngine()
    return eng


def cmd_run_demo() -> int:
    eng = OperationalSelfEngine()
    summary = eng.run_demo()
    print("Operational Self demo complete.")
    for k, v in summary.items():
        if k != "doctrine":
            print(f"  {k}: {v}")
    print(f"Outputs: {eng.output_root}")
    return 0


def cmd_ingest(kind: str, path: Path) -> int:
    eng = _engine()
    if kind == "session":
        r = eng.ingest_session(path)
    elif kind == "guardian":
        r = eng.ingest_guardian(path)
    else:
        r = eng.ingest_authority(path)
    print(f"ingested {r['events_ingested']} events from {path.name}")
    return 0


def cmd_retrieve(query: str) -> int:
    eng = OperationalSelfEngine()
    samples = ROOT / "operational_self" / "samples"
    for sub in ("session_events", "guardian_events", "authority_events", "chat_turns"):
        for p in (samples / sub).glob("*.json"):
            eng.ingest_bundle(p)
    result = eng.retrieve_query(query)
    print(json.dumps(result, indent=2))
    eng.export_dashboard()
    return 0


def cmd_replay(label: str) -> int:
    eng = OperationalSelfEngine()
    eng.run_demo()
    route = eng.replay_route(label)
    print(json.dumps(route, indent=2))
    return 0


def cmd_decay() -> int:
    eng = OperationalSelfEngine()
    if not eng.memories:
        eng.run_demo()
    else:
        for p in (ROOT / "operational_self" / "samples").rglob("*.json"):
            eng.ingest_bundle(p)
    result = eng.decay_demo()
    print(json.dumps(result, indent=2))
    return 0


def cmd_export_dashboard() -> int:
    eng = OperationalSelfEngine()
    if not (eng.output_root / "self_state.json").exists():
        eng.run_demo()
    path = eng.export_dashboard()
    print(f"Dashboard: {path}")
    return 0


def cmd_purge() -> int:
    eng = OperationalSelfEngine()
    eng.run_demo()
    result = eng.purge_demo()
    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operational Self + Fractal Attractor Memory v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-demo")
    p = sub.add_parser("ingest-session")
    p.add_argument("path", type=Path)
    p = sub.add_parser("ingest-guardian")
    p.add_argument("path", type=Path)
    p = sub.add_parser("ingest-authority")
    p.add_argument("path", type=Path)
    p = sub.add_parser("retrieve")
    p.add_argument("query", type=str)
    p = sub.add_parser("replay-route")
    p.add_argument("label", type=str)
    sub.add_parser("decay-demo")
    sub.add_parser("export-dashboard")
    sub.add_parser("purge-demo")

    args = parser.parse_args(argv)
    if args.command == "run-demo":
        return cmd_run_demo()
    if args.command == "ingest-session":
        return cmd_ingest("session", args.path)
    if args.command == "ingest-guardian":
        return cmd_ingest("guardian", args.path)
    if args.command == "ingest-authority":
        return cmd_ingest("authority", args.path)
    if args.command == "retrieve":
        return cmd_retrieve(args.query)
    if args.command == "replay-route":
        return cmd_replay(args.label)
    if args.command == "decay-demo":
        return cmd_decay()
    if args.command == "export-dashboard":
        return cmd_export_dashboard()
    if args.command == "purge-demo":
        return cmd_purge()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())