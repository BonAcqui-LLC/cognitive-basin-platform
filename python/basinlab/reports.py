"""
Static BasinLab trajectory reports.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPORT_FIELDS = [
    "purpose",
    "plan",
    "retrieved_associations",
    "candidate_spectrum",
    "candidate_deduplication",
    "action_proposals",
    "rigor_decisions",
    "guard_decisions",
    "execution_output",
    "namespace_changes",
    "artifacts",
    "decision_critical_claims",
    "evidence_links",
    "reliability_verdicts",
    "contradictions",
    "scars",
    "recovery_routes",
    "association_updates",
    "hold_intervals",
    "commit_decisions",
    "replay_result",
    "final_basin_state",
]


def _bounded(value: Any, max_chars: int = 4000) -> Any:
    if isinstance(value, str):
        if len(value) <= max_chars:
            return value
        return value[: max_chars - 29] + "...[bounded by BasinLab report]"
    if isinstance(value, list):
        return [_bounded(item, max_chars=max_chars // 2 if max_chars > 200 else max_chars) for item in value[:50]]
    if isinstance(value, dict):
        bounded = {}
        for index, key in enumerate(sorted(value)):
            if index >= 50:
                bounded["..."] = "additional keys omitted"
                break
            bounded[key] = _bounded(value[key], max_chars=max_chars // 2 if max_chars > 200 else max_chars)
        return bounded
    return value


def normalize_report(report: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "scenario": report.get("scenario", "unknown"),
        "passed": bool(report.get("passed", False)),
    }
    for field in REPORT_FIELDS:
        normalized[field] = _bounded(report.get(field, [] if field.endswith("s") else ""))
    return normalized


def _json_block(value: Any) -> str:
    rendered = json.dumps(_bounded(value), indent=2, sort_keys=True, default=str)
    return html.escape(rendered)


def build_static_html(report: Dict[str, Any]) -> str:
    normalized = normalize_report(report)
    sections = []
    for field in REPORT_FIELDS:
        sections.append(
            f"<section><h2>{html.escape(field.replace('_', ' ').title())}</h2><pre>{_json_block(normalized[field])}</pre></section>"
        )
    title = html.escape(f"BasinLab trajectory: {normalized['scenario']}")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Georgia, 'Times New Roman', serif; margin: 2rem auto; max-width: 1100px; color: #182018; background: linear-gradient(180deg, #fbfaf5 0%, #eef1e4 100%); }}
    h1, h2 {{ font-family: 'Palatino Linotype', 'Book Antiqua', serif; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f6f8ee; border: 1px solid #c8d1b4; padding: 1rem; border-radius: 0.5rem; }}
    .banner {{ padding: 1rem 1.25rem; border-radius: 0.75rem; background: {'#d9f2df' if normalized['passed'] else '#f5ddd9'}; border: 1px solid {'#8ab394' if normalized['passed'] else '#c08a80'}; }}
    section {{ margin-top: 1.5rem; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="banner">
    <strong>Passed:</strong> {html.escape(str(normalized['passed']))}
  </div>
  {''.join(sections)}
</body>
</html>
"""


def write_report_bundle(output_dir: str | Path, report: Dict[str, Any]) -> Dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    normalized = normalize_report(report)
    stem = normalized["scenario"]
    json_path = root / f"{stem}.json"
    html_path = root / f"{stem}.html"
    json_path.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")
    html_path.write_text(build_static_html(normalized), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}
