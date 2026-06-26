from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

AIA_ROOT = Path(r"C:\Users\moop\Documents\AIA")
CNTM_ROOT = Path(
    r"C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\CNTM_Natural_Math_Canonical_Library"
)
MOTOROLA_ROOT = Path(r"C:\Motorola-Activation")


@dataclass(frozen=True)
class TreeSync:
    name: str
    source_root: Path
    destination_root: Path
    excluded_dir_names: tuple[str, ...] = ()
    excluded_relative_paths: tuple[str, ...] = ()
    renamed_relative_paths: dict[str, str] | None = None


def _as_posix(path: Path) -> str:
    text = path.as_posix()
    return "" if text == "." else text


def _should_skip_dir(relative_dir: str, dir_name: str, selection: TreeSync) -> bool:
    if dir_name in selection.excluded_dir_names:
        return True
    return relative_dir in selection.excluded_relative_paths


def _should_skip_file(relative_file: str, selection: TreeSync) -> bool:
    return relative_file in selection.excluded_relative_paths


def _copy_tree(selection: TreeSync) -> int:
    copied = 0
    destination_root = REPO_ROOT / selection.destination_root
    destination_root.mkdir(parents=True, exist_ok=True)
    renamed_relative_paths = selection.renamed_relative_paths or {}

    for source_path in selection.source_root.rglob("*"):
        relative_path = _as_posix(source_path.relative_to(selection.source_root))
        if source_path.is_dir():
            if _should_skip_dir(relative_path, source_path.name, selection):
                continue
            continue

        if _should_skip_file(relative_path, selection):
            continue

        if any(part in selection.excluded_dir_names for part in source_path.parts):
            continue

        parent_rel = _as_posix(source_path.parent.relative_to(selection.source_root))
        if parent_rel and parent_rel in selection.excluded_relative_paths:
            continue

        destination_relative_path = renamed_relative_paths.get(relative_path, relative_path)
        dest_path = destination_root / destination_relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        copied += 1

    for excluded_rel in selection.excluded_relative_paths:
        excluded_dest = destination_root / excluded_rel
        if excluded_dest.is_file():
            excluded_dest.unlink()
        elif excluded_dest.is_dir():
            shutil.rmtree(excluded_dest)

    legacy_cleanup = {
        "imports/aia-sovereign-activation-device/gitignore",
        "imports/cntm-natural-math-canonical-library/gitignore",
        "imports/cntm-natural-math-canonical-library/CNTM_Natural_Math_Canonical_Library.zip",
        "imports/cntm-natural-math-canonical-library/10_TESTS_AND_FROZEN_RESULTS/__pycache__",
        "imports/cntm-natural-math-canonical-library/04_CNTM_SIMULATOR/CNT Morphology Simulator First Prompt to Grok Build from ChatGPT _had to remove 2 evo 2 prize references_.docx",
        "imports/cntm-natural-math-canonical-library/06_MORPHOLOGICAL_CODING/The Architecture of Morphological Coding - Unifying Thermodynamics_ Material Computation__76d33afebc.docx",
        "imports/cntm-natural-math-canonical-library/06_MORPHOLOGICAL_CODING/Fractalish_Natural_Math_Morphological_Memory_Current_Master_Thesis_and_Working_Appraisal.docx",
    }
    for rel in legacy_cleanup:
        cleanup_path = REPO_ROOT / rel
        if cleanup_path.exists():
            if cleanup_path.is_dir():
                shutil.rmtree(cleanup_path)
            else:
                cleanup_path.unlink()

    return copied


def _copy_file(source_path: Path, destination_rel: str) -> int:
    destination_path = REPO_ROOT / destination_rel
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)
    return 1


def main() -> None:
    selections = [
        TreeSync(
            name="AIA",
            source_root=AIA_ROOT,
            destination_root=Path("imports/aia-sovereign-activation-device"),
            excluded_dir_names=(".git", ".tmp", "artifacts", ".gradle", "build", "raw"),
            excluded_relative_paths=(
                "android/app/build",
                "android/build",
                "android/local.properties",
                "receipts/device_audit.json",
                "receipts/raw",
            ),
        ),
        TreeSync(
            name="CNTM",
            source_root=CNTM_ROOT,
            destination_root=Path("imports/cntm-natural-math-canonical-library"),
            excluded_dir_names=(
                ".git",
                ".pytest_cache",
                "__pycache__",
                "90_CANDIDATE_VERSIONS",
                "91_DUPLICATES",
                "92_CONFLICTING_VERSIONS",
                "99_ARCHIVES",
            ),
            excluded_relative_paths=(
                "10_TESTS_AND_FROZEN_RESULTS/__pycache__",
                "10_TESTS_AND_FROZEN_RESULTS/archive.zip",
                "CNTM_Natural_Math_Canonical_Library.zip",
                "manifests/local_provenance_private.json",
            ),
            renamed_relative_paths={
                "04_CNTM_SIMULATOR/CNT Morphology Simulator First Prompt to Grok Build from ChatGPT _had to remove 2 evo 2 prize references_.docx": "04_CNTM_SIMULATOR/CNT_Morphology_Simulator_First_Prompt_trimmed.docx",
                "06_MORPHOLOGICAL_CODING/The Architecture of Morphological Coding - Unifying Thermodynamics_ Material Computation__76d33afebc.docx": "06_MORPHOLOGICAL_CODING/architecture_of_morphological_coding_unifying_thermodynamics_76d33afebc.docx",
                "06_MORPHOLOGICAL_CODING/Fractalish_Natural_Math_Morphological_Memory_Current_Master_Thesis_and_Working_Appraisal.docx": "06_MORPHOLOGICAL_CODING/Fractalish_Natural_Math_Morphological_Memory_Master_Thesis.docx",
            },
        ),
        TreeSync(
            name="Motorola baseline",
            source_root=MOTOROLA_ROOT / "baseline-unlocked",
            destination_root=Path("evidence/motorola-activation/baseline-unlocked"),
        ),
        TreeSync(
            name="Motorola A01",
            source_root=MOTOROLA_ROOT / "activations" / "A01-stock-closure",
            destination_root=Path("evidence/motorola-activation/activations/A01-stock-closure"),
        ),
        TreeSync(
            name="Motorola A02A",
            source_root=MOTOROLA_ROOT / "activations" / "A02A-offline-stock-topology",
            destination_root=Path("evidence/motorola-activation/activations/A02A-offline-stock-topology"),
        ),
        TreeSync(
            name="Motorola A02B",
            source_root=MOTOROLA_ROOT / "activations" / "A02B-live-read-only-topology",
            destination_root=Path("evidence/motorola-activation/activations/A02B-live-read-only-topology"),
            excluded_dir_names=("__pycache__", "private"),
            excluded_relative_paths=("private", "scripts/__pycache__"),
        ),
        TreeSync(
            name="Motorola sanitized evidence",
            source_root=MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "evidence" / "sanitized",
            destination_root=Path("evidence/motorola-activation/device/motorola/gnevan/evidence/sanitized"),
        ),
        TreeSync(
            name="Motorola hardware",
            source_root=MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "hardware",
            destination_root=Path("evidence/motorola-activation/device/motorola/gnevan/hardware"),
        ),
        TreeSync(
            name="Motorola manifests",
            source_root=MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "manifests",
            destination_root=Path("evidence/motorola-activation/device/motorola/gnevan/manifests"),
        ),
        TreeSync(
            name="Motorola reports",
            source_root=MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "reports",
            destination_root=Path("evidence/motorola-activation/device/motorola/gnevan/reports"),
        ),
    ]

    copied_counts: dict[str, int] = {}
    for selection in selections:
        copied_counts[selection.name] = _copy_tree(selection)

    copied_counts["Motorola current-build-identity.json"] = _copy_file(
        MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "current-build-identity.json",
        "evidence/motorola-activation/device/motorola/gnevan/stock/current-build-identity.json",
    )
    copied_counts["Motorola current-build-identity.md"] = _copy_file(
        MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "current-build-identity.md",
        "evidence/motorola-activation/device/motorola/gnevan/stock/current-build-identity.md",
    )
    copied_counts["Motorola package-candidate.json"] = _copy_file(
        MOTOROLA_ROOT / "device" / "motorola" / "gnevan" / "stock" / "package-candidate.json",
        "evidence/motorola-activation/device/motorola/gnevan/stock/package-candidate.json",
    )
    copied_counts["Motorola A02A tool"] = _copy_file(
        MOTOROLA_ROOT / "tools" / "a02a_offline_topology.py",
        "evidence/motorola-activation/tools/a02a_offline_topology.py",
    )

    summary_path = REPO_ROOT / "ops" / "manifests" / "private-workspace-import-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(copied_counts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"copied_counts": copied_counts, "summary_path": str(summary_path)}, indent=2))


if __name__ == "__main__":
    main()
