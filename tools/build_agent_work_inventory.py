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
MOTOROLA_ROOT = Path(r"C:\Motorola-Activation")
CNTM_ROOT = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\CNTM_Natural_Math_Canonical_Library"
)
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


def append_tree_files(
    rows: list[dict[str, str]],
    dest_hash_index: dict[str, list[str]],
    *,
    source_root: Path,
    source_repository: str,
    producer: str,
    project_area: str,
    implementation_status: str,
    proposed_destination_root: str,
    import_decision: str,
    reason: str,
    excluded_dir_names: set[str] | None = None,
    excluded_relative_paths: set[str] | None = None,
    renamed_relative_paths: dict[str, str] | None = None,
    git_commit: str = "",
    git_branch: str = "",
    note: str = "",
) -> None:
    excluded_dir_names = excluded_dir_names or set()
    excluded_relative_paths = excluded_relative_paths or set()
    renamed_relative_paths = renamed_relative_paths or {}

    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source_root).as_posix()
        if rel in excluded_relative_paths:
            continue
        if any(part in excluded_dir_names for part in path.parts):
            continue
        destination_rel = renamed_relative_paths.get(rel, rel)
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=source_repository,
                    producer=producer,
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area=project_area,
                    implementation_status=implementation_status,
                    proposed_destination=f"{proposed_destination_root}/{destination_rel}",
                    import_decision=import_decision,
                    reason=reason,
                    git_commit=git_commit,
                    git_branch=git_branch,
                    note=note,
                ),
                dest_hash_index,
            )
        )


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

    append_tree_files(
        rows,
        dest_hash_index,
        source_root=AIA_REPO,
        source_repository=str(AIA_REPO),
        producer="AIA",
        project_area="AIA Android device tranche",
        implementation_status="Structural snapshot of the accepted stock-Android vertical slice",
        proposed_destination_root="imports/aia-sovereign-activation-device",
        import_decision="IMPORT",
        reason="Private stock-Android AIA tranche is now preserved as a structural snapshot with generated artifacts and raw device identifiers excluded.",
        excluded_dir_names={".git", ".tmp", "artifacts", ".gradle", "build", "raw"},
        excluded_relative_paths={
            "android/app/build",
            "android/build",
            "android/local.properties",
            "receipts/device_audit.json",
            "receipts/raw",
        },
        git_branch="master",
        git_commit="UNCOMMITTED",
    )

    rows.append(
        file_row(
            Artifact(
                source_path=AIA_REPO / "receipts" / "device_audit.json",
                source_repository=str(AIA_REPO),
                producer="AIA",
                filename="device_audit.json",
                file_type="json",
                project_area="AIA Android device tranche",
                implementation_status="Excluded raw device receipt",
                proposed_destination="",
                import_decision="EXCLUDE - RAW DEVICE RECEIPT",
                reason="Tracked AIA import excludes gitignored raw device receipts to keep persistent identifiers out of repository content.",
                git_branch="master",
                git_commit="UNCOMMITTED",
            ),
            dest_hash_index,
        )
    )

    rows.append(
        directory_row(
            source_path=AIA_REPO / "artifacts",
            source_repository=str(AIA_REPO),
            producer="AIA",
            filename="artifacts",
            file_type="directory",
            project_area="AIA Android device tranche",
            implementation_status="Excluded generated screenshots",
            proposed_destination="",
            import_decision="EXCLUDE - GENERATED ARTIFACTS",
            reason="AIA screenshots and UI dumps remain outside this structural snapshot to avoid growing the repo with generated mobile evidence.",
            git_branch="master",
            git_commit="UNCOMMITTED",
        )
    )

    append_tree_files(
        rows,
        dest_hash_index,
        source_root=CNTM_ROOT,
        source_repository=str(CNTM_ROOT),
        producer="CNTM",
        project_area="CNTM / Natural Math canonical library",
        implementation_status="Curated canonical library snapshot",
        proposed_destination_root="imports/cntm-natural-math-canonical-library",
        import_decision="IMPORT",
        reason="CNTM and adjacent Natural Math / Cognitive Basin / SymLan materials are preserved as a curated library snapshot with duplicate/version/archive buckets excluded.",
        excluded_dir_names={".git", "90_CANDIDATE_VERSIONS", "91_DUPLICATES", "92_CONFLICTING_VERSIONS", "99_ARCHIVES"},
        excluded_relative_paths={
            "10_TESTS_AND_FROZEN_RESULTS/__pycache__",
            "10_TESTS_AND_FROZEN_RESULTS/archive.zip",
            "CNTM_Natural_Math_Canonical_Library.zip",
            "manifests/local_provenance_private.json",
        },
        renamed_relative_paths={
            "04_CNTM_SIMULATOR/CNT Morphology Simulator First Prompt to Grok Build from ChatGPT _had to remove 2 evo 2 prize references_.docx": "04_CNTM_SIMULATOR/CNT_Morphology_Simulator_First_Prompt_trimmed.docx",
            "06_MORPHOLOGICAL_CODING/The Architecture of Morphological Coding - Unifying Thermodynamics_ Material Computation__76d33afebc.docx": "06_MORPHOLOGICAL_CODING/architecture_of_morphological_coding_unifying_thermodynamics_76d33afebc.docx",
            "06_MORPHOLOGICAL_CODING/Fractalish_Natural_Math_Morphological_Memory_Current_Master_Thesis_and_Working_Appraisal.docx": "06_MORPHOLOGICAL_CODING/Fractalish_Natural_Math_Morphological_Memory_Master_Thesis.docx",
        },
    )

    rows.append(
        file_row(
            Artifact(
                source_path=CNTM_ROOT / "manifests" / "local_provenance_private.json",
                source_repository=str(CNTM_ROOT),
                producer="CNTM",
                filename="local_provenance_private.json",
                file_type="json",
                project_area="CNTM / Natural Math canonical library",
                implementation_status="Excluded private provenance",
                proposed_destination="",
                import_decision="EXCLUDE - PRIVATE PROVENANCE",
                reason="Local provenance file is explicitly private and remains outside repository content.",
            ),
            dest_hash_index,
        )
    )

    rows.append(
        directory_row(
            source_path=CNTM_ROOT / "91_DUPLICATES",
            source_repository=str(CNTM_ROOT),
            producer="CNTM",
            filename="91_DUPLICATES",
            file_type="directory",
            project_area="CNTM / Natural Math canonical library",
            implementation_status="Excluded duplicate bucket",
            proposed_destination="",
            import_decision="EXCLUDE - DUPLICATE BUCKET",
            reason="Duplicate/version-bucket material is intentionally excluded from the curated canonical import to avoid redundant history.",
        )
    )

    rows.append(
        file_row(
            Artifact(
                source_path=CNTM_ROOT / "CNTM_Natural_Math_Canonical_Library.zip",
                source_repository=str(CNTM_ROOT),
                producer="CNTM",
                filename="CNTM_Natural_Math_Canonical_Library.zip",
                file_type="zip",
                project_area="CNTM / Natural Math canonical library",
                implementation_status="Excluded archive bundle",
                proposed_destination="",
                import_decision="EXCLUDE - ARCHIVE BUNDLE",
                reason="The root CNTM archive bundle is excluded because the unpacked curated contents are imported directly.",
            ),
            dest_hash_index,
        )
    )

    for motorola_dir, area in [
        (MOTOROLA_ROOT / "baseline-unlocked", "Motorola activation baseline"),
        (MOTOROLA_ROOT / "activations" / "A01-stock-closure", "Motorola activation A01"),
        (MOTOROLA_ROOT / "activations" / "A02A-offline-stock-topology", "Motorola activation A02A"),
        (MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "evidence" / "sanitized", "Motorola activation sanitized evidence"),
        (MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "hardware", "Motorola activation hardware snapshot"),
        (MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "manifests", "Motorola activation manifests"),
        (MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "reports", "Motorola activation reports"),
    ]:
        append_tree_files(
            rows,
            dest_hash_index,
            source_root=motorola_dir,
            source_repository=str(MOTOROLA_ROOT),
            producer="Motorola Activation",
            project_area=area,
            implementation_status="Read-only activation evidence snapshot",
            proposed_destination_root="evidence/motorola-activation/"
            + motorola_dir.relative_to(MOTOROLA_ROOT).as_posix(),
            import_decision="IMPORT",
            reason="Read-only Motorola activation evidence is preserved as provenance for native-device work without importing firmware or private receipts.",
        )

    append_tree_files(
        rows,
        dest_hash_index,
        source_root=MOTOROLA_ROOT / "activations" / "A02B-live-read-only-topology",
        source_repository=str(MOTOROLA_ROOT),
        producer="Motorola Activation",
        project_area="Motorola activation A02B",
        implementation_status="Read-only activation evidence snapshot",
        proposed_destination_root="evidence/motorola-activation/activations/A02B-live-read-only-topology",
        import_decision="IMPORT",
        reason="A02B live read-only topology evidence is preserved, while the private preflight receipt remains excluded.",
        excluded_dir_names={"__pycache__", "private"},
        excluded_relative_paths={"scripts/__pycache__", "private"},
    )

    for path in [
        MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "current-build-identity.json",
        MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "current-build-identity.md",
        MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "package-candidate.json",
        MOTOROLA_ROOT / "tools" / "a02a_offline_topology.py",
    ]:
        destination = "evidence/motorola-activation/" + path.relative_to(MOTOROLA_ROOT).as_posix()
        rows.append(
            file_row(
                Artifact(
                    source_path=path,
                    source_repository=str(MOTOROLA_ROOT),
                    producer="Motorola Activation",
                    filename=path.name,
                    file_type=path.suffix.lstrip(".") or "file",
                    project_area="Motorola activation support files",
                    implementation_status="Read-only activation evidence snapshot",
                    proposed_destination=destination,
                    import_decision="IMPORT",
                    reason="Supplemental Motorola activation support file preserved without including write-capable firmware content.",
                ),
                dest_hash_index,
            )
        )

    rows.append(
        file_row(
            Artifact(
                source_path=MOTOROLA_ROOT
                / "device"
                / "motorola"
                / "gnevan"
                / "stock"
                / "original"
                / "XT2317-2_GNEVAN_RETUS_14_U1THS34.65-74-1-7-8_subsidy-DEFAULT_regulatory-DEFAULT_cid50_CFC.xml.zip",
                source_repository=str(MOTOROLA_ROOT),
                producer="Motorola Activation",
                filename="XT2317-2_GNEVAN_RETUS_14_U1THS34.65-74-1-7-8_subsidy-DEFAULT_regulatory-DEFAULT_cid50_CFC.xml.zip",
                file_type="zip",
                project_area="Motorola firmware package",
                implementation_status="Excluded firmware package",
                proposed_destination="",
                import_decision="EXCLUDE - FIRMWARE",
                reason="Large Motorola stock package remains outside repository content; only hashes and read-only derived evidence are imported.",
            ),
            dest_hash_index,
        )
    )

    rows.append(
        directory_row(
            source_path=MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "extracted",
            source_repository=str(MOTOROLA_ROOT),
            producer="Motorola Activation",
            filename="extracted",
            file_type="directory",
            project_area="Motorola firmware extraction",
            implementation_status="Excluded extracted images",
            proposed_destination="",
            import_decision="EXCLUDE - FIRMWARE IMAGES",
            reason="Extracted partition images are excluded from git history; the repo preserves only the analysis and sanitized evidence built from them.",
        )
    )

    rows.append(
        directory_row(
            source_path=MOTOROLA_ROOT / "activations" / "A02B-live-read-only-topology" / "private",
            source_repository=str(MOTOROLA_ROOT),
            producer="Motorola Activation",
            filename="private",
            file_type="directory",
            project_area="Motorola activation private receipts",
            implementation_status="Excluded private receipt bucket",
            proposed_destination="",
            import_decision="EXCLUDE - PRIVATE RECEIPTS",
            reason="Private A02B preflight receipts remain outside repository content.",
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
        "This inventory covers the verified AutoClaw workspace and handoff bundle, selected Z.ai planning artifacts, the Grok intake worker, selected Grok Build evidence artifacts, selected Kimi research artifacts, the imported AIA stock-Android snapshot, the imported CNTM canonical library snapshot, the imported Motorola activation evidence tranche, and the separately recorded empty Kimi workspace directory.",
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
            "- The AIA stock-Android tranche is now preserved as a structural snapshot, while its raw device audit receipt and generated screenshots remain excluded.",
            "- The CNTM canonical library is now represented as a curated snapshot without duplicate/version/archive buckets or the private local-provenance manifest.",
            "- The Motorola activation tranche is now represented by read-only activations, sanitized evidence, and derived reports; firmware packages, extracted images, and private receipts remain excluded.",
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
