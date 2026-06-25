from __future__ import annotations

import csv
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_CSV = REPO_ROOT / "docs" / "provenance" / "agent-work-import-inventory.csv"
SHA_MANIFEST = REPO_ROOT / "ops" / "manifests" / "agent-work-sha256.txt"


def _inventory_rows() -> list[dict[str, str]]:
    with INVENTORY_CSV.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _find_row(filename: str) -> dict[str, str]:
    for row in _inventory_rows():
        if row["filename"] == filename:
            return row
    raise AssertionError(f"inventory row not found for {filename}")


def test_inventory_covers_selected_agent_artifacts() -> None:
    worker = _find_row("worker.js")
    assert worker["producing_system"] == "Grok"
    assert worker["import_decision"] == "IMPORT"
    assert worker["proposed_destination"] == "imports/grok-guardian-intake/worker.js"

    kimi_report = _find_row("Kimi SGTM Research report.md")
    assert kimi_report["producing_system"] == "Kimi"
    assert kimi_report["import_decision"] == "HISTORICAL EVIDENCE"

    zai_prompt = _find_row("z.ai.nm-ai-prompt.txt")
    assert zai_prompt["producing_system"] == "Z.ai"
    assert zai_prompt["import_decision"] == "HISTORICAL EVIDENCE"

    secret = _find_row("ALL_TOKENS_KEYS_FOR_GROK.txt")
    assert secret["import_decision"] == "EXCLUDE - SECRET"

    aia = _find_row("AIA")
    assert aia["import_decision"] == "CONFLICT - REVIEW REQUIRED"


def test_autoclaw_lineage_is_preserved_and_tagged() -> None:
    imported_root = REPO_ROOT / "imports" / "autoclaw-natural-math-workspace"
    assert imported_root.exists()
    assert not (imported_root / ".git").exists()

    assert _git("rev-parse", "ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9") == "ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9"
    assert _git("rev-parse", "28ffa5974b5fd157982f36fdb1189ac9d1fb6acb") == "28ffa5974b5fd157982f36fdb1189ac9d1fb6acb"
    assert _git("rev-parse", "autoclaw-natural-math-v5-reference-1.0^{}") == "28ffa5974b5fd157982f36fdb1189ac9d1fb6acb"

    continuation = (
        REPO_ROOT / "docs" / "handoffs" / "AUTOCLAW_CONTINUATION_START_POINT.md"
    ).read_text(encoding="utf-8")
    assert "Stage 2R Natural Math-specific harness repair" in continuation
    assert "autoclaw-natural-math-v5-reference-1.0" in continuation


def test_zip_is_not_duplicated_and_manifest_records_provenance() -> None:
    assert not (REPO_ROOT / "docs" / "provenance" / "autoclaw_workspace_handoff.zip").exists()
    assert not (REPO_ROOT / "docs" / "provenance" / "autoclaw" / "autoclaw_workspace_handoff.zip").exists()

    sha_manifest = SHA_MANIFEST.read_text(encoding="utf-8")
    assert "758F59126E14743ADEEF9DC0097043F891AA239774DF185C950D03FA7688198C" in sha_manifest
    assert "C:\\_MASTER_LIBRARY_Handoff\\autoclaw_workspace_handoff.zip" in sha_manifest
    assert "C:\\Users\\moop\\Downloads\\Articles on X.com\\Natural Math\\z.ai.nm-ai-prompt.txt" in sha_manifest
