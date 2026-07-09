#!/usr/bin/env python3
"""Guardian Authority Corpus CLI — local-first, no network."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.guardian_authority.corpus import GuardianAuthorityCorpus


def cmd_ingest(path: Path) -> int:
    corpus = GuardianAuthorityCorpus()
    result = corpus.ingest(path)
    source = result["source"]
    print(f"ingested: {source.source_name} ({len(result['records'])} records)")
    return 0


def cmd_evaluate_claim(text: str) -> int:
    corpus = GuardianAuthorityCorpus()
    samples = ROOT / "guardian_authority" / "samples" / "corpus"
    for path in sorted(samples.glob("mock_*.json")):
        corpus.ingest(path)
    corpus.detect_conflicts()
    result = corpus.evaluate_claim(text)
    claim = result["claim"]
    print(f"claim_id:        {claim.claim_id}")
    print(f"support_status:  {claim.support_status}")
    print(f"guard:           {claim.guard_recommendation}")
    print(f"routes:          {len(result['routes'])}")
    for route in result["routes"][:3]:
        print(f"  route {route.route_id}: {route.final_status} strength={route.route_strength:.2f}")
        print(f"    scope={route.scope_match} juris={route.jurisdiction_match} version={route.version_match}")
    basin_guard = result["basin_record"].get("guard_decision", {})
    if isinstance(basin_guard, dict):
        print(f"basin_guard:     {basin_guard.get('decision', basin_guard)}")
    return 0


def cmd_detect_conflicts() -> int:
    corpus = GuardianAuthorityCorpus()
    samples = ROOT / "guardian_authority" / "samples" / "corpus"
    for path in sorted(samples.glob("mock_*.json")):
        corpus.ingest(path)
    conflicts = corpus.detect_conflicts()
    print(f"conflicts detected: {len(conflicts)}")
    for c in conflicts[:5]:
        print(f"  {c.conflict_type}: {c.record_a} vs {c.record_b} → {c.guard_recommendation}")
    return 0


def cmd_run_demo() -> int:
    corpus = GuardianAuthorityCorpus()
    summary = corpus.run_demo()
    print(f"Authority corpus demo complete.")
    print(f"  sources: {summary['sources']}")
    print(f"  records: {summary['records']}")
    print(f"  claims:  {summary['claims_evaluated']}")
    print(f"  conflicts: {summary['conflicts']}")
    for gd in summary["guard_decisions"]:
        print(f"  {gd['claim_text'][:50]:50s} {gd['support_status']:22s} {gd['authority_guard_recommendation']}")
    print(f"Summary: {corpus.output_root / 'authority_demo_summary.json'}")
    return 0


def cmd_export_dashboard() -> int:
    corpus = GuardianAuthorityCorpus()
    if not list(corpus.output_root.glob("authority_sources.json")):
        corpus.run_demo()
    path = corpus.export_dashboard()
    print(f"Dashboard summary: {path}")
    return 0


def cmd_purge_demo() -> int:
    corpus = GuardianAuthorityCorpus()
    samples = ROOT / "guardian_authority" / "samples" / "corpus"
    corpus.ingest(samples / "mock_dictionary_entries.json")
    report = corpus.purge_demo()
    print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guardian Authority Corpus v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_p = sub.add_parser("ingest", help="Ingest a corpus JSON file")
    ingest_p.add_argument("path", type=Path)

    eval_p = sub.add_parser("evaluate-claim", help="Evaluate a user claim against corpus")
    eval_p.add_argument("text", type=str)

    sub.add_parser("detect-conflicts", help="Detect conflicts in ingested corpus")
    sub.add_parser("run-demo", help="Ingest all samples, evaluate claims, export summary")
    sub.add_parser("export-dashboard", help="Export dashboard_summary.json")
    sub.add_parser("purge-demo", help="Purge demo lifecycle artifacts")

    args = parser.parse_args(argv)
    if args.command == "ingest":
        return cmd_ingest(args.path)
    if args.command == "evaluate-claim":
        return cmd_evaluate_claim(args.text)
    if args.command == "detect-conflicts":
        return cmd_detect_conflicts()
    if args.command == "run-demo":
        return cmd_run_demo()
    if args.command == "export-dashboard":
        return cmd_export_dashboard()
    if args.command == "purge-demo":
        return cmd_purge_demo()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())