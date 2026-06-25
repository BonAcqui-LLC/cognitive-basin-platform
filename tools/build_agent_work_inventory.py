from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEST_REPO = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\cognitive-basin-platform-import-2026-06"
)
AUTOCLAW_REPO = Path(r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE")
AUTOCLAW_HANDOFF = Path(r"C:\_MASTER_LIBRARY_Handoff")
GROK_INTAKE = Path(r"C:\Users\moop\Downloads\Grok\intake-deploy")
GROK_ROOT = Path(r"C:\Users\moop\Downloads\Grok")
FRACTALISH_AI = Path(r"C:\Users\moop\FractalishBuild\fractalish-ai")
KIMI_WORKSPACE = Path(r"C:\Users\moop\Documents\kimi\workspace")
AIA_REPO = Path(r"C:\Users\moop\Documents\AIA")
KIMI_REPORT = Path(r"C:\Users\moop\Downloads\Articles on X.com\Kimi SGTM Research report.md")
KIMI_ORIENTATION = Path(r"C:\Users\moop\Downloads\Articles on X.com\Natural Math\Kimi_Orientation.txt")
KIMI_SIGNAL_HYPOTHESIS = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\F R A C T A L I S H - - - A I - - - FRACTALISH-AI\Kimi_Signal_Jamming_Morphology_Hypothesis.csv"
)
ZAI_NATURAL_MATH_PROMPT = Path(r"C:\Users\moop\Downloads\Articles on X.com\Natural Math\z.ai.nm-ai-prompt.txt")
ZAI_CURATION_DOC = Path(r"C:\Users\moop\Downloads\Z.ai AutoClaw Library Curation.docx")
ZAI_ACCOUNT_USAGE_PDF = Path(r"C:\Users\moop\Downloads\z.ai.autoclaw.account.7b3ffc45-ea76-4aee-b822-9d28bb5f572a.usage.pdf")
ZAI_ACCOUNT_ID_PDF = Path(r"C:\Users\moop\Downloads\z.ai.account.synaptient.gmail.com.user.id.7b3ffc45-ea76-4aee-b822-9d28bb5f572a.pdf")
OPENCLAW_RUNTIME_JSON = Path(r"C:\Users\moop\.openclaw-autoclaw\openclaw.runtime.json")
OPENCLAW_CONFIG_JSON = Path(r"C:\Users\moop\.openclaw-autoclaw\openclaw.json")
KIMI_WEBBRIDGE_EXE = Path(r"C:\Users\moop\.kimi-webbridge\bin\kimi-webbridge.exe")

INVENTORY_CSV = DEST_REPO / "docs" / "provenance" / "agent-work-import-inventory.csv"
AUDIT_MD = DEST_REPO / "docs" / "provenance" / "agent-work-import-audit.md"
SHA_MANIFEST = DEST_REPO / "ops" / "manifests" / "agent-work-sha256.txt"


@dataclass
class Artifact:
    source_path: Path
    source_repository: str
    producer: str
    filename: str
    file_type: str
    project_area: str
    implementation_status: str
    proposed_destination: str
    import_decision: str
    reason: str
    git_commit: str = ""
    git_branch: str = ""
    note: str = ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def build_dest_hash_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for path in DEST_REPO.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        digest = sha256(path)
        index.setdefault(digest, []).append(path.relative_to(DEST_REPO).as_posix())
    return index


def file_row(artifact: Artifact, dest_hash_index: dict[str, list[str]]) -> dict[str, str]:
    path = artifact.source_path
    exists = path.exists()
    size = path.stat().st_size if exists and path.is_file() else 0
    digest = sha256(path) if exists and path.is_file() else ""
    identical_matches = dest_hash_index.get(digest, []) if digest else []
    already_present = "yes" if identical_matches else "no"
    relation = "identical" if identical_matches else ""

    return {
        "source_path": str(path),
        "source_repository": artifact.source_repository,
        "producing_system": artifact.producer,
        "filename": artifact.filename,
        "file_type": artifact.file_type,
        "byte_count": str(size),
        "sha256": digest,
        "git_commit": artifact.git_commit,
        "git_branch": artifact.git_branch,
        "project_area": artifact.project_area,
        "implementation_status": artifact.implementation_status,
        "already_present_in_github": already_present,
        "identical_to_existing_github_file": "; ".join(identical_matches),
        "newer_older_or_conflicting": relation,
        "proposed_destination": artifact.proposed_destination,
        "import_decision": artifact.import_decision,
        "reason": artifact.reason,
        "note": artifact.note,
    }


def directory_row(
    *,
    source_path: Path,
    source_repository: str,
    producer: str,
    filename: str,
    file_type: str,
    project_area: str,
    implementation_status: str,
    proposed_destination: str,
    import_decision: str,
    reason: str,
    git_commit: str = "",
    git_branch: str = "",
    note: str = "",
) -> dict[str, str]:
    size = 0
    if source_path.exists():
        size = sum(p.stat().st_size for p in source_path.rglob("*") if p.is_file())
    return {
        "source_path": str(source_path),
        "source_repository": source_repository,
        "producing_system": producer,
        "filename": filename,
        "file_type": file_type,
        "byte_count": str(size),
        "sha256": "",
        "git_commit": git_commit,
        "git_branch": git_branch,
        "project_area": project_area,
        "implementation_status": implementation_status,
        "already_present_in_github": "no",
        "identical_to_existing_github_file": "",
        "newer_older_or_conflicting": "conflicting",
        "proposed_destination": proposed_destination,
        "import_decision": import_decision,
        "reason": reason,
        "note": note,
    }


def main() -> None:
    (DEST_REPO / "docs" / "provenance").mkdir(parents=True, exist_ok=True)
    (DEST_REPO / "ops" / "manifests").mkdir(parents=True, exist_ok=True)

    dest_hash_index = build_dest_hash_index()
    rows: list[dict[str, str]] = []

    autoclaw_commit = git_output(AUTOCLAW_REPO, "rev-parse", "HEAD")
    autoclaw_branch = git_output(AUTOCLAW_REPO, "branch", "--show-current")
    tracked_files = git_output(AUTOCLAW_REPO, "ls-files").splitlines()
    for rel in tracked_files:
        path = AUTOCLAW_REPO / rel
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(AUTOCLAW_REPO),
                    producer="AutoClaw",
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area=f"AutoClaw/{Path(rel).parts[0] if Path(rel).parts else 'root'}",
                    implementation_status="Stage 1/1.1/2 verified workspace",
                    proposed_destination=f"imports/autoclaw-natural-math-workspace/{Path(rel).as_posix()}",
                    import_decision="IMPORT",
                    reason="Verified AutoClaw workspace preserved through history-preserving subtree import.",
                    git_commit=autoclaw_commit,
                    git_branch=autoclaw_branch,
                ),
                dest_hash_index,
            )
        )

    handoff_files = [
        "AUTOCLAW_HANDOFF_AUDIT.md",
        "AUTOCLAW_STAGE_STATUS.md",
        "AUTOCLAW_TEST_RESULTS.md",
        "AUTOCLAW_GIT_HISTORY.txt",
        "AUTOCLAW_FILE_MANIFEST.csv",
        "AUTOCLAW_SHA256_MANIFEST.txt",
        "AUTOCLAW_TOP_LEVEL_ARTIFACT_CLASSIFICATION.md",
        "AUTOCLAW_KNOWN_STALE_REPORTS.md",
        "AUTOCLAW_CONTINUATION_START_POINT.md",
        "AUTOCLAW_COMPLETION_RECEIPT.json",
        "run_autoclaw_audit.py",
        "autoclaw_workspace_handoff.zip",
    ]
    for name in handoff_files:
        path = AUTOCLAW_HANDOFF / name
        decision = "HISTORICAL EVIDENCE"
        destination = f"docs/provenance/autoclaw/{name}"
        reason = "External AutoClaw handoff evidence preserved for provenance."
        note = ""
        if name.endswith(".zip"):
            destination = "release-asset-only"
            reason = "Do not duplicate zip contents in git history when extracted files and preserved Git history are imported separately."
            note = "Archive should be referenced by checksum and, if desired, attached to a draft archival release."
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(AUTOCLAW_HANDOFF),
                    producer="AutoClaw",
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area="AutoClaw handoff",
                    implementation_status="Historical evidence",
                    proposed_destination=destination,
                    import_decision=decision,
                    reason=reason,
                    note=note,
                ),
                dest_hash_index,
            )
        )

    for name in ["worker.js", "wrangler.toml"]:
        path = GROK_INTAKE / name
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(GROK_INTAKE),
                    producer="Grok",
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area="Guardian Intake / EphUX",
                    implementation_status="Prototype implementation",
                    proposed_destination=f"imports/grok-guardian-intake/{path.name}",
                    import_decision="IMPORT",
                    reason="Concrete Grok-produced Guardian Intake worker not currently present in the destination repository.",
                ),
                dest_hash_index,
            )
        )

    secret_path = GROK_ROOT / "ALL_TOKENS_KEYS_FOR_GROK.txt"
    rows.append(
        file_row(
            Artifact(
                source_path=secret_path,
                source_repository=str(GROK_ROOT),
                producer="Grok",
                filename=secret_path.name,
                file_type="txt",
                project_area="Secrets",
                implementation_status="Excluded",
                proposed_destination="",
                import_decision="EXCLUDE - SECRET",
                reason="Contains tokens/keys and must never be uploaded.",
            ),
            dest_hash_index,
        )
    )

    grok_report_files = [
        "README.md",
        "FINAL_BUILD_REPORT.md",
        "EVOLUTION_PRIZE_COMPLETE_REPORT.md",
        "FRACTALISH_MORPHOLOGICAL_LANGUAGE_BUILD_REPORT.md",
        "evolution_prize_submission.md",
        "evolution_prize_submission_packet.json",
        "benchmark_results.md",
        "benchmark_results.json",
        "guardian_run_trace.json",
    ]
    for name in grok_report_files:
        path = FRACTALISH_AI / name
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(FRACTALISH_AI),
                    producer="Grok Build",
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area="Fractalish AI snapshot",
                    implementation_status="Historical evidence snapshot",
                    proposed_destination=f"evidence/grok/fractalish-ai/{path.name}",
                    import_decision="IMPORT",
                    reason="Standalone report/evidence artifact from Grok Build snapshot; preserves missing project history without importing overlapping code trees blindly.",
                ),
                dest_hash_index,
            )
        )

    rows.append(
        directory_row(
            source_path=FRACTALISH_AI,
            source_repository=str(FRACTALISH_AI),
            producer="Grok Build",
            filename="fractalish-ai",
            file_type="directory snapshot",
            project_area="Fractalish AI snapshot",
            implementation_status="Large overlapping prototype tree",
            proposed_destination="",
            import_decision="CONFLICT - REVIEW REQUIRED",
            reason="Large source snapshot lacks local Git provenance and overlaps heavily with existing platform modules; only selected reports/evidence are imported in this tranche.",
        )
    )

    for path, producer, project_area, destination in [
        (
            ZAI_NATURAL_MATH_PROMPT,
            "Z.ai",
            "Natural Math / developmental runtime planning",
            "docs/provenance/zai/z.ai.nm-ai-prompt.txt",
        ),
        (
            ZAI_CURATION_DOC,
            "Z.ai",
            "AutoClaw library curation",
            "docs/provenance/zai/Z.ai AutoClaw Library Curation.docx",
        ),
        (
            KIMI_REPORT,
            "Kimi",
            "Natural Math research",
            "evidence/kimi/Kimi SGTM Research report.md",
        ),
        (
            KIMI_ORIENTATION,
            "Kimi",
            "Natural Math / BasinLab architecture",
            "evidence/kimi/Kimi_Orientation.txt",
        ),
        (
            KIMI_SIGNAL_HYPOTHESIS,
            "Kimi",
            "Fractalish AI morphology research",
            "evidence/kimi/Kimi_Signal_Jamming_Morphology_Hypothesis.csv",
        ),
    ]:
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(path.parent),
                    producer=producer,
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area=project_area,
                    implementation_status="Historical research/spec artifact",
                    proposed_destination=destination,
                    import_decision="HISTORICAL EVIDENCE",
                    reason="Project-relevant authored artifact preserved as evidence/specification rather than active implementation.",
                ),
                dest_hash_index,
            )
        )

    for path, producer, project_area, decision, reason in [
        (
            ZAI_ACCOUNT_USAGE_PDF,
            "Z.ai",
            "Account usage record",
            "EXCLUDE - PERSONAL",
            "Account usage PDF is personal/account data and not repository material.",
        ),
        (
            ZAI_ACCOUNT_ID_PDF,
            "Z.ai",
            "Account identity record",
            "EXCLUDE - PERSONAL",
            "Account identity PDF is personal/account data and not repository material.",
        ),
        (
            OPENCLAW_RUNTIME_JSON,
            "Z.ai",
            "Local OpenClaw runtime state",
            "EXCLUDE - GENERATED CACHE",
            "Local runtime state file is generated machine state, not durable project evidence.",
        ),
        (
            OPENCLAW_CONFIG_JSON,
            "Z.ai",
            "Local OpenClaw config",
            "EXCLUDE - PERSONAL",
            "Local config file may contain user-specific account/runtime details and is not needed for project transfer.",
        ),
        (
            KIMI_WEBBRIDGE_EXE,
            "Kimi",
            "Local tool installation",
            "EXCLUDE - UNRELATED",
            "Installed bridge executable is tooling, not authored project work.",
        ),
    ]:
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(path.parent),
                    producer=producer,
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area=project_area,
                    implementation_status="Excluded",
                    proposed_destination="",
                    import_decision=decision,
                    reason=reason,
                ),
                dest_hash_index,
            )
        )

    rows.append(
        directory_row(
            source_path=AIA_REPO,
            source_repository=str(AIA_REPO),
            producer="unknown",
            filename="AIA",
            file_type="directory/git repo",
            project_area="AIA Android device tranche",
            implementation_status="Separate Codex-era workspace",
            proposed_destination="",
            import_decision="CONFLICT - REVIEW REQUIRED",
            reason="Project-relevant but outside the strictly attributable Grok/AutoClaw/Kimi tranche; contains device receipts and current Codex implementation work that should transfer under a separate reviewed tranche.",
            git_branch="master",
            git_commit="UNCOMMITTED",
        )
    )

    rows.append(
        directory_row(
            source_path=KIMI_WORKSPACE,
            source_repository=str(KIMI_WORKSPACE.parent),
            producer="Kimi",
            filename="workspace",
            file_type="directory",
            project_area="Kimi workspace",
            implementation_status="Workspace empty; evidence exists elsewhere",
            proposed_destination="",
            import_decision="SOURCE NOT FOUND",
            reason="The inspected Kimi workspace directory is empty; selected Kimi artifacts were found in other project roots and are inventoried separately.",
        )
    )

    fieldnames = list(rows[0].keys())
    with INVENTORY_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    decision_counts: dict[str, int] = {}
    for row in rows:
        decision_counts[row["import_decision"]] = decision_counts.get(row["import_decision"], 0) + 1

    audit_lines = [
        "# Agent Work Import Audit",
        "",
        "This inventory covers the verified AutoClaw workspace and handoff bundle, selected Z.ai planning artifacts, the Grok intake worker, selected Grok Build evidence artifacts, selected Kimi research artifacts, the inspected-but-deferred AIA workspace, and the separately recorded empty Kimi workspace directory.",
        "",
        "## Decision Summary",
        "",
    ]
    for decision, count in sorted(decision_counts.items()):
        audit_lines.append(f"- **{decision}:** {count}")
    audit_lines.extend(
        [
            "",
            "## Key Findings",
            "",
            "- AutoClaw is the only candidate source with a verified standalone Git lineage ready for history-preserving import.",
            "- The external AutoClaw handoff bundle should be preserved as provenance, but the zip archive itself should stay out of normal Git history.",
            "- The Grok intake worker is a small concrete implementation that is absent from the destination repo and safe to import after cache/secret exclusion.",
            "- Z.ai contributed planning and curation artifacts plus the verified AutoClaw workspace; local account/config/runtime files are excluded.",
            "- Kimi contributed project-relevant research and orientation documents, but no Kimi code baseline was located.",
            "- The larger `fractalish-ai` snapshot appears historically valuable but overlaps with the existing platform; this tranche imports only selected evidence/report artifacts and records the rest as conflict-review.",
            "- The AIA Android/device repo is project-relevant but not clearly attributable to the requested agent set, so it is deferred rather than silently mixed into this agent-work import.",
        ]
    )
    AUDIT_MD.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    sha_lines = []
    for row in rows:
        if row["sha256"]:
            sha_lines.append(f"{row['sha256']}  {row['source_path']}")
    SHA_MANIFEST.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "inventory_csv": str(INVENTORY_CSV),
                "audit_md": str(AUDIT_MD),
                "sha_manifest": str(SHA_MANIFEST),
                "rows": len(rows),
                "decision_counts": decision_counts,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
