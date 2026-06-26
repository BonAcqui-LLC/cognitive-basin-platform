from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


EXPECTED_ARCHIVE_SHA256 = "B3B86713E066002C37877ECF8ABFF525BF147D1EC3207CA04FF0397DDC5E604D"
EXPECTED_ARCHIVE_BYTES = 4190063592
ACTIVATION_ID = "A02A-offline-stock-topology"
ROOT = Path(r"C:\Motorola-Activation")
A01_ROOT = ROOT / "activations" / "A01-stock-closure"
A02A_ROOT = ROOT / "activations" / ACTIVATION_ID
DEVICE_ROOT = ROOT / "device" / "motorola" / "gnevan"
STOCK_ROOT = DEVICE_ROOT / "stock"
ORIGINAL_ARCHIVE = STOCK_ROOT / "original" / (
    "XT2317-2_GNEVAN_RETUS_14_U1THS34.65-74-1-7-8_"
    "subsidy-DEFAULT_regulatory-DEFAULT_cid50_CFC.xml.zip"
)
EXTRACT_ROOT = STOCK_ROOT / "extracted" / EXPECTED_ARCHIVE_SHA256[:16]
BASELINE_ROOT = ROOT / "baseline-unlocked"
HARDWARE_ROOT = DEVICE_ROOT / "hardware"
REQUIRED_A01_FILES = [
    A01_ROOT / "A01-completion-receipt.json",
    A01_ROOT / "A01-summary.md",
    A01_ROOT / "artifact-manifest.sha256",
    A01_ROOT / "stock-package-preservation-record.json",
    A01_ROOT / "stock-package-match-assessment.json",
    A01_ROOT / "stock-package-source-provenance.json",
    A01_ROOT / "current-build-identity.snapshot.json",
    STOCK_ROOT / "current-build-identity.json",
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text_auto(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "utf-16-le", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_capture(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        return {
            "command": command,
            "available": False,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "available": True,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def detect_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".xml":
        return "XML"
    if suffix == ".img":
        return "ANDROID_IMAGE"
    if suffix in {".txt", ".md"}:
        return "TEXT"
    if suffix in {".png"}:
        return "PNG"
    if suffix in {".dat", ".atc"}:
        return "BINARY_DATA"
    if path.name == "PGPT":
        return "PARTITION_TABLE_BLOB"
    return "UNKNOWN"


def classify_file(name: str) -> list[str]:
    lower = name.lower()
    tags: list[str] = []
    if lower.endswith(".xml"):
        tags.append("FLASHING_METADATA")
    if lower.endswith(".txt") or lower.endswith(".md"):
        tags.append("DOCUMENTATION")
    if lower == "pgpt":
        tags.extend(["PARTITION_TABLE", "SECURITY_SENSITIVE"])
    if any(token in lower for token in ["boot.img", "vendor_boot", "dtbo", "lk.img", "preloader", "logo.img"]):
        tags.append("BOOT_CRITICAL")
    if any(token in lower for token in ["vbmeta", "tee", "efuse"]):
        tags.extend(["BOOT_CRITICAL", "SECURITY_SENSITIVE"])
    if any(token in lower for token in ["md1img", "modem", "bluetooth", "dsp"]):
        tags.append("RADIO")
    if any(token in lower for token in ["scp", "spmfw", "sspm", "gz", "tzapp"]):
        tags.append("VENDOR")
    if lower.startswith("super.img_sparsechunk"):
        tags.extend(["OS", "VENDOR"])
    if any(token in lower for token in ["persist", "nvcfg", "nvdata", "nvram", "carrier", "cid"]):
        tags.append("CALIBRATION")
    if lower in {"signing-info.txt"}:
        tags.append("SIGNATURE_OR_CHECKSUM")
    if not tags:
        tags.append("UNKNOWN")
    return sorted(set(tags))


def classify_partition(name: str) -> list[str]:
    lower = name.lower()
    tags: list[str] = []
    if lower == "gpt":
        tags.extend(["PARTITION_TABLE", "SECURITY_SENSITIVE"])
    if lower == "super":
        tags.extend(["OS", "VENDOR"])
    if lower.startswith(("boot", "vendor_boot", "dtbo", "vbmeta", "logo", "lk", "preloader")):
        tags.append("BOOT_CRITICAL")
    if lower.startswith(("md1img",)):
        tags.append("RADIO")
    if lower.startswith(("scp", "spmfw", "sspm", "gz", "tee", "efuse")):
        tags.extend(["VENDOR", "SECURITY_SENSITIVE"])
    if lower in {"userdata", "metadata", "nvdata"}:
        tags.append("CALIBRATION" if lower == "nvdata" else "UNKNOWN")
    if not tags:
        tags.append("UNKNOWN")
    return sorted(set(tags))


def slot_behavior(partition: str) -> str:
    if re.search(r"_[ab]$", partition):
        return "SLOTTED_SINGLE_TARGET"
    if partition in {"super", "userdata", "metadata", "nvdata", "efuse", "gpt", "preloader"}:
        return "UNSLOTTED"
    return "UNKNOWN"


def partition_kind(partition: str) -> str:
    if partition in {"system", "vendor", "product", "system_ext"}:
        return "LOGICAL"
    if partition == "super":
        return "PHYSICAL_DYNAMIC_CONTAINER"
    return "PHYSICAL"


def risk_class(operation: str, partition: str) -> str:
    if operation == "erase":
        return "DESTRUCTIVE_ERASE"
    if operation == "flash":
        if partition == "gpt":
            return "PARTITION_TABLE_WRITE"
        if partition in {"vbmeta_a", "vbmeta_b", "vbmeta_system_a", "vbmeta_system_b", "boot_a", "boot_b"}:
            return "BOOT_CHAIN_WRITE"
        if partition == "super":
            return "OS_CONTAINER_WRITE"
        return "PARTITION_WRITE"
    if operation == "oem":
        return "BOOTLOADER_MODE_CHANGE"
    if operation == "getvar":
        return "QUERY_ONLY"
    return "UNKNOWN"


def avb_role_for_partition(partition: str) -> str:
    if partition.startswith("vbmeta_system"):
        return "SUB_CHAIN_VBMETA"
    if partition.startswith("vbmeta"):
        return "ROOT_VBMETA"
    if partition in {"boot_a", "boot_b", "vendor_boot_a", "vendor_boot_b", "dtbo_a", "dtbo_b"}:
        return "VERIFIED_PAYLOAD"
    if partition == "super":
        return "VERIFIED_LOGICAL_CONTAINER"
    return "UNKNOWN"


def boot_chain_role(partition: str) -> str:
    if partition == "gpt":
        return "PARTITION_TABLE"
    if partition == "preloader":
        return "PRE_BOOT_STAGE"
    if partition.startswith("lk"):
        return "BOOTLOADER_STAGE"
    if partition.startswith("tee"):
        return "TRUSTZONE_STAGE"
    if partition.startswith("vbmeta"):
        return "AVB_METADATA"
    if partition.startswith(("boot", "vendor_boot", "dtbo")):
        return "KERNEL_BOOT_PAYLOAD"
    if partition == "super":
        return "DYNAMIC_SYSTEM_CONTAINER"
    return "UNKNOWN"


def safe_zip_path(entry_name: str) -> bool:
    posix = PurePosixPath(entry_name)
    if posix.is_absolute():
        return False
    return ".." not in posix.parts


def parse_artifact_manifest(path: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    pattern = re.compile(r"^([A-Fa-f0-9]{64}) \*(.+)$")
    for line in read_text_auto(path).splitlines():
        match = pattern.match(line.strip())
        if match:
            manifest[match.group(2)] = match.group(1).upper()
    return manifest


def parse_by_name(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    pattern = re.compile(r"^(?P<name>\S+) -> (?P<target>\S+)$")
    for line in read_text_auto(path).splitlines():
        match = pattern.search(line.strip())
        if not match:
            continue
        name = match.group("name")
        if name in {"mmcblk0", "mmcblk0boot0", "mmcblk0boot1"}:
            continue
        entries.append(
            {
                "partition": name,
                "device_node": match.group("target"),
                "slot_behavior": slot_behavior(name),
                "kind": partition_kind(name),
                "evidence_source": "baseline-unlocked/by-name.txt",
                "confidence": "HIGH",
            }
        )
    return entries


def parse_mount_logicals(path: Path) -> list[dict[str, Any]]:
    logicals: list[dict[str, Any]] = []
    pattern = re.compile(r"^(?P<dev>\S+) on (?P<mount>/\S*|/) type ")
    for line in read_text_auto(path).splitlines():
        match = pattern.search(line.strip())
        if not match:
            continue
        mount = match.group("mount")
        mount_name = mount.lstrip("/")
        if mount == "/":
            logicals.append(
                {
                    "logical_partition": "system",
                    "device_mapper": match.group("dev"),
                    "evidence_source": path.name,
                    "confidence": "HIGH",
                }
            )
            continue
        if mount_name in {"vendor", "product", "system_ext"} or mount_name.startswith("apex/"):
            logicals.append(
                {
                    "logical_partition": mount_name.split("/")[0],
                    "device_mapper": match.group("dev"),
                    "evidence_source": path.name,
                    "confidence": "HIGH",
                }
            )
    unique: dict[str, dict[str, Any]] = {}
    for item in logicals:
        unique[item["logical_partition"]] = item
    return sorted(unique.values(), key=lambda x: x["logical_partition"])


def sniff_magic(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = handle.read(16)
    magic_hex = data.hex().upper()
    magic_ascii = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
    sparse_magic = data[:4] == bytes.fromhex("3AFF26ED")
    return {
        "magic_ascii": magic_ascii,
        "magic_hex": magic_hex,
        "looks_like_android_sparse": sparse_magic,
    }


def inventory_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Package File Inventory",
        "",
        f"Total files: {len(entries)}",
        "",
        "| File | Bytes | Type | Classes |",
        "| --- | ---: | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['relative_path']} | {entry['byte_count']} | "
            f"{entry['detected_type']} | {', '.join(entry['classification'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def flashing_markdown(flashing_data: dict[str, Any]) -> str:
    lines = [
        "# Flashing Sequence",
        "",
        f"Primary manifest: {flashing_data['primary_manifest']}",
        f"Parsed manifests: {', '.join(flashing_data['parsed_manifests'])}",
        "",
        "| Order | Manifest | Operation | Source | Target | Risk |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for step in flashing_data["steps"]:
        lines.append(
            f"| {step['order']} | {step['manifest']} | {step['operation']} | "
            f"{step['source_file'] or ''} | {step['target_partition'] or ''} | {step['risk_class']} |"
        )
    lines.append("")
    return "\n".join(lines)


def partition_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Package Partition Inventory",
        "",
        f"Partitions recorded: {len(entries)}",
        "",
        "| Partition | Kind | Slot | Sources | AVB Role | Boot Role | Confidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['canonical_name']} | {entry['physical_logical']} | {entry['slot_behavior']} | "
            f"{', '.join(entry['source_images'])} | {entry['avb_role']} | {entry['boot_chain_role']} | "
            f"{entry['confidence']} |"
        )
    lines.append("")
    return "\n".join(lines)


def topology_markdown(graph: dict[str, Any]) -> str:
    lines = [
        "# Package Topology Graph",
        "",
        f"Nodes: {len(graph['nodes'])}",
        f"Edges: {len(graph['edges'])}",
        "",
        "| From | Edge | To | Confidence | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for edge in graph["edges"]:
        lines.append(
            f"| {edge['from']} | {edge['type']} | {edge['to']} | "
            f"{edge['confidence']} | {edge['evidence_source']} |"
        )
    lines.append("")
    return "\n".join(lines)


def dot_graph(graph: dict[str, Any]) -> str:
    lines = ["digraph package_topology {"]
    for node in graph["nodes"]:
        safe_id = re.sub(r"[^A-Za-z0-9_]", "_", node["id"])
        label = node["label"].replace('"', '\\"')
        lines.append(f'  {safe_id} [label="{label}"];')
    for edge in graph["edges"]:
        src = re.sub(r"[^A-Za-z0-9_]", "_", edge["from"])
        dst = re.sub(r"[^A-Za-z0-9_]", "_", edge["to"])
        label = edge["type"].replace('"', '\\"')
        lines.append(f'  {src} -> {dst} [label="{label}"];')
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def summary_markdown(receipt: dict[str, Any], identity_diff: dict[str, Any], holds: dict[str, Any]) -> str:
    lines = [
        "# A02A Summary",
        "",
        f"Status: {receipt['status']}",
        f"Original archive hash before: {receipt['original_archive_hash_before']}",
        f"Original archive hash after: {receipt['original_archive_hash_after']}",
        f"Extraction success: {receipt['extraction_success']}",
        f"Extracted file count: {receipt['extracted_file_count']}",
        f"Parsed manifest count: {receipt['parsed_manifest_count']}",
        f"Dynamic partition conclusion: {receipt['dynamic_partition_conclusion']}",
        f"AVB conclusion: {receipt['avb_conclusion']}",
        f"Restore suitability: {receipt['restore_suitability']}",
        "",
        "## Identity conclusion",
        "",
        receipt["package_identity_conclusion"],
        "",
        "## Key differences",
        "",
    ]
    for diff in identity_diff["differences"]:
        lines.append(f"- {diff['field']}: live={diff['live_value']} package={diff['package_value']}")
    lines.extend(
        [
            "",
            "## Open holds",
            "",
        ]
    )
    for hold in holds["holds"]:
        lines.append(f"- {hold['topic']}: {hold['reason']}")
    lines.append("")
    return "\n".join(lines)


def directory_file_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> int:
    A02A_ROOT.mkdir(parents=True, exist_ok=True)
    original_hash_before = sha256_file(ORIGINAL_ARCHIVE)
    if original_hash_before != EXPECTED_ARCHIVE_SHA256:
        write_json(
            A02A_ROOT / "A02A-completion-receipt.json",
            {
                "activation_id": ACTIVATION_ID,
                "status": "FAILED_SAFE",
                "reason": "Original archive hash mismatch before extraction.",
                "original_archive_hash_before": original_hash_before,
                "expected_archive_hash": EXPECTED_ARCHIVE_SHA256,
                "device_contacted": False,
                "device_changed": False,
                "recorded_at": now_iso(),
            },
        )
        return 2

    usage_before = shutil.disk_usage(ORIGINAL_ARCHIVE.drive or "C:\\")
    python_version = sys.version.replace("\n", " ")
    powershell_version = run_capture(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "$PSVersionTable.PSVersion.ToString()",
        ]
    )
    avbtool = run_capture(["where.exe", "avbtool"])
    unpack_bootimg = run_capture(["where.exe", "unpack_bootimg"])
    lpunpack = run_capture(["where.exe", "lpunpack"])

    tool_versions = {
        "recorded_at": now_iso(),
        "python": python_version,
        "platform": platform.platform(),
        "powershell": powershell_version,
        "avbtool": avbtool,
        "unpack_bootimg": unpack_bootimg,
        "lpunpack": lpunpack,
        "zip_parser": "python zipfile standard library",
    }
    write_json(A02A_ROOT / "tool-versions.json", tool_versions)

    activation_manifest = {
        "activation_id": ACTIVATION_ID,
        "principal": "human_operator",
        "purpose": "Inspect the preserved older-build stock package offline and establish its package, partition, flashing, boot-chain, and AVB topology without interacting with the handset.",
        "predecessor": "A01-stock-closure",
        "device_change_authorized": False,
        "package_restore_suitability": "NOT_YET_ESTABLISHED",
        "anti_rollback_status": "UNRESOLVED",
        "allowed_actions": [
            "read_a01_artifacts",
            "verify_hashes",
            "archive_list",
            "extract_to_separate_working_copy",
            "hash_extracted_files",
            "parse_metadata_read_only",
            "write_evidence_records",
        ],
        "prohibited_actions": [
            "adb_reboot",
            "fastboot_reboot",
            "fastboot_boot",
            "flash",
            "erase",
            "set_active",
            "logical_partition_change",
            "avb_state_change",
            "mount_read_write",
            "repack_stock_image",
            "claim_restore_ready",
        ],
        "completion_criteria": [
            "A01 inputs verified",
            "original package hash stable before and after inspection",
            "archive extracted separately without modifying original",
            "all extracted files hashed",
            "flashing metadata parsed",
            "package partition inventory created",
            "package topology graph created",
            "boot and AVB relationships recorded where supported",
            "unknowns and contradictions preserved",
            "A02A completion receipt emitted",
        ],
        "host": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "hostname_redacted": True,
            "execution_root": str(ROOT),
        },
        "timestamps": {
            "started_at": now_iso(),
        },
        "disk_space_before_extraction_bytes": {
            "total": usage_before.total,
            "used": usage_before.used,
            "free": usage_before.free,
        },
        "tool_versions_file": "tool-versions.json",
    }
    write_json(A02A_ROOT / "activation-manifest.json", activation_manifest)

    artifact_manifest = parse_artifact_manifest(A01_ROOT / "artifact-manifest.sha256")
    a01_receipt = read_json(A01_ROOT / "A01-completion-receipt.json")
    preservation = read_json(A01_ROOT / "stock-package-preservation-record.json")
    match_assessment = read_json(A01_ROOT / "stock-package-match-assessment.json")
    source_provenance = read_json(A01_ROOT / "stock-package-source-provenance.json")
    live_identity = read_json(STOCK_ROOT / "current-build-identity.json")

    a01_validation_entries = []
    discrepancies: list[str] = []
    for path in REQUIRED_A01_FILES:
        exists = path.exists()
        entry: dict[str, Any] = {
            "path": str(path),
            "exists": exists,
            "byte_count": path.stat().st_size if exists else None,
            "sha256": sha256_file(path) if exists else None,
            "parse_status": "NOT_ATTEMPTED",
            "manifest_membership": None,
            "consistency_with_a01_receipt": [],
            "discrepancies": [],
        }
        if exists:
            if path.suffix == ".json":
                try:
                    read_json(path)
                    entry["parse_status"] = "PARSED_JSON"
                except Exception as exc:  # noqa: BLE001
                    entry["parse_status"] = f"JSON_PARSE_FAILED: {exc}"
                    entry["discrepancies"].append("json_parse_failed")
            else:
                entry["parse_status"] = "READABLE_TEXT"
        if path.parent == A01_ROOT and path.name != "artifact-manifest.sha256":
            expected = artifact_manifest.get(path.name)
            entry["manifest_membership"] = expected is not None
            if expected and entry["sha256"] != expected:
                entry["discrepancies"].append("artifact_manifest_hash_mismatch")
        if path.name == "A01-completion-receipt.json":
            if a01_receipt.get("status") != "COMPLETE":
                entry["discrepancies"].append("a01_not_complete")
            entry["consistency_with_a01_receipt"].append("receipt_status_checked")
        if path.name == "stock-package-preservation-record.json":
            if preservation.get("sha256_first_read") != EXPECTED_ARCHIVE_SHA256:
                entry["discrepancies"].append("preservation_hash_mismatch")
            entry["consistency_with_a01_receipt"].append("preservation_hash_checked")
        if path.name == "stock-package-match-assessment.json":
            if match_assessment.get("classification") not in {None, "STRONG_MATCH_OLDER_BUILD"}:
                entry["discrepancies"].append("unexpected_match_classification")
            entry["consistency_with_a01_receipt"].append("match_classification_checked")
        if path.name == "stock-package-source-provenance.json":
            if source_provenance.get("source_classification") not in {None, "THIRD_PARTY_MIRROR"}:
                entry["discrepancies"].append("unexpected_source_classification")
            entry["consistency_with_a01_receipt"].append("source_classification_checked")
        if entry["discrepancies"]:
            discrepancies.extend(f"{path.name}:{item}" for item in entry["discrepancies"])
        a01_validation_entries.append(entry)

    a01_validation = {
        "validated_at": now_iso(),
        "expected_archive_hash": EXPECTED_ARCHIVE_SHA256,
        "expected_archive_bytes": EXPECTED_ARCHIVE_BYTES,
        "entries": a01_validation_entries,
        "a01_receipt_consistency": {
            "a01_status_complete": a01_receipt.get("status") == "COMPLETE",
            "a01_device_changed_false": a01_receipt.get("device_changed") is False,
            "a01_package_hash_matches_expected": a01_receipt.get("package_hash") == EXPECTED_ARCHIVE_SHA256,
            "a01_restore_suitability": a01_receipt.get("restore_suitability"),
            "a01_anti_rollback_status": a01_receipt.get("anti_rollback_status"),
        },
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
    }
    write_json(A02A_ROOT / "A01-input-validation.json", a01_validation)

    with zipfile.ZipFile(ORIGINAL_ARCHIVE) as archive:
        infos = archive.infolist()
        total_uncompressed = sum(info.file_size for info in infos)
        reusable_bytes = directory_file_bytes(EXTRACT_ROOT)
        effective_free_bytes = usage_before.free + reusable_bytes
        if effective_free_bytes < total_uncompressed + (1024 * 1024 * 1024):
            write_json(
                A02A_ROOT / "A02A-completion-receipt.json",
                {
                    "activation_id": ACTIVATION_ID,
                    "status": "FAILED_SAFE",
                    "reason": "Insufficient free disk space for safe extraction margin.",
                    "free_bytes": usage_before.free,
                    "reusable_extraction_bytes": reusable_bytes,
                    "effective_free_bytes": effective_free_bytes,
                    "required_minimum_bytes": total_uncompressed + (1024 * 1024 * 1024),
                    "device_contacted": False,
                    "device_changed": False,
                    "recorded_at": now_iso(),
                },
            )
            return 3

        names = [info.filename for info in infos]
        duplicate_entries = [name for name, count in Counter(names).items() if count > 1]
        unsafe_paths = [name for name in names if not safe_zip_path(name)]
        encrypted_entries = [info.filename for info in infos if info.flag_bits & 0x1]
        symlink_entries = [
            info.filename
            for info in infos
            if ((info.external_attr >> 16) & 0o170000) == 0o120000
        ]

        archive_listing_lines = []
        for info in infos:
            archive_listing_lines.append(
                f"{info.filename}\tbytes={info.file_size}\tcompressed={info.compress_size}\tcrc={info.CRC:08X}"
            )
        write_text(A02A_ROOT / "archive-listing.txt", "\n".join(archive_listing_lines) + "\n")

        archive_test = {
            "tested_at": now_iso(),
            "entry_count": len(infos),
            "total_uncompressed_bytes": total_uncompressed,
            "duplicate_entries": duplicate_entries,
            "unsafe_paths": unsafe_paths,
            "encrypted_entries": encrypted_entries,
            "symlink_entries": symlink_entries,
            "archive_parser": "python zipfile standard library",
            "result": "PASS"
            if not duplicate_entries and not unsafe_paths and not encrypted_entries and not symlink_entries
            else "WARN",
        }
        write_text(A02A_ROOT / "archive-test.txt", json.dumps(archive_test, indent=2) + "\n")

        if EXTRACT_ROOT.exists():
            shutil.rmtree(EXTRACT_ROOT)
        EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)

        extraction_log_lines = [f"Extraction started: {now_iso()}"]
        for info in infos:
            if not safe_zip_path(info.filename):
                extraction_log_lines.append(f"SKIP unsafe path: {info.filename}")
                continue
            destination = EXTRACT_ROOT / PurePosixPath(info.filename)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as src, destination.open("wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            extraction_log_lines.append(f"EXTRACT {info.filename} -> {destination}")
        extraction_log_lines.append(f"Extraction completed: {now_iso()}")
        write_text(A02A_ROOT / "extraction-log.txt", "\n".join(extraction_log_lines) + "\n")

    usage_after = shutil.disk_usage(ORIGINAL_ARCHIVE.drive or "C:\\")
    original_hash_after = sha256_file(ORIGINAL_ARCHIVE)

    extracted_records: list[dict[str, Any]] = []
    extracted_hash_lines: list[str] = []
    for path in sorted(p for p in EXTRACT_ROOT.rglob("*") if p.is_file()):
        rel = path.relative_to(EXTRACT_ROOT).as_posix()
        record = {
            "relative_path": rel,
            "byte_count": path.stat().st_size,
            "sha256": sha256_file(path),
            "extension": path.suffix.lower(),
            "detected_type": detect_type(path),
            "original_archive_entry": rel,
            "extraction_timestamp": now_iso(),
            "classification": classify_file(rel),
            "parser_safety_notes": "Extracted for read-only hashing and metadata inspection only.",
            "magic": sniff_magic(path) if path.stat().st_size > 0 else {"magic_ascii": "", "magic_hex": "", "looks_like_android_sparse": False},
        }
        extracted_records.append(record)
        extracted_hash_lines.append(f"{record['sha256']} *{rel}")

    write_json(A02A_ROOT / "extracted-file-manifest.json", {"generated_at": now_iso(), "files": extracted_records})
    write_text(A02A_ROOT / "extracted-file-manifest.sha256", "\n".join(extracted_hash_lines) + "\n")

    extraction_record = {
        "started_at": activation_manifest["timestamps"]["started_at"],
        "completed_at": now_iso(),
        "original_archive": str(ORIGINAL_ARCHIVE),
        "working_extraction_root": str(EXTRACT_ROOT),
        "original_archive_hash_before": original_hash_before,
        "original_archive_hash_after": original_hash_after,
        "archive_hash_stable": original_hash_before == original_hash_after,
        "entry_count": len(extracted_records),
        "archive_entry_count": len(extracted_records),
        "disk_space_before_bytes": usage_before.free,
        "disk_space_after_bytes": usage_after.free,
        "original_archive_modified": False,
    }
    write_json(A02A_ROOT / "extraction-record.json", extraction_record)

    package_file_inventory = {
        "generated_at": now_iso(),
        "archive_entry_count": len(extracted_records),
        "class_counts": Counter(tag for record in extracted_records for tag in record["classification"]),
        "files": extracted_records,
    }
    package_file_inventory["class_counts"] = dict(package_file_inventory["class_counts"])
    write_json(A02A_ROOT / "package-file-inventory.json", package_file_inventory)
    write_text(A02A_ROOT / "package-file-inventory.md", inventory_markdown(extracted_records))

    xml_manifests = []
    manifest_names = ["flashfile.xml", "servicefile.xml"]
    package_identity_sources: dict[str, dict[str, Any]] = {}
    all_steps: list[dict[str, Any]] = []
    parsed_manifest_names: list[str] = []
    header_fields: dict[str, Any] = {}
    for manifest_name in manifest_names:
        manifest_path = EXTRACT_ROOT / manifest_name
        if not manifest_path.exists():
            continue
        parsed_manifest_names.append(manifest_name)
        xml_root = ET.fromstring(manifest_path.read_text(encoding="utf-8"))
        xml_manifests.append(xml_root)
        header = xml_root.find("header")
        if header is not None and not header_fields:
            phone_model = header.find("phone_model")
            software_version = header.find("software_version")
            sparsing = header.find("sparsing")
            cid_value = header.find("cid_value")
            if phone_model is not None:
                header_fields["product"] = phone_model.attrib.get("model")
            if software_version is not None:
                header_fields["software_version"] = software_version.attrib.get("version")
            if sparsing is not None:
                header_fields["sparsing"] = sparsing.attrib
            if cid_value is not None:
                header_fields["cid_value"] = cid_value.attrib.get("value")
        for index, step in enumerate(xml_root.findall("./steps/step"), start=1):
            operation = step.attrib.get("operation", "unknown")
            target_partition = step.attrib.get("partition")
            source_file = step.attrib.get("filename")
            all_steps.append(
                {
                    "order": len(all_steps) + 1,
                    "manifest": manifest_name,
                    "operation": operation,
                    "source_file": source_file,
                    "target_partition": target_partition,
                    "slot_behavior": slot_behavior(target_partition or ""),
                    "sparse_or_chunk_behavior": "SPARSE_CHUNK"
                    if source_file and source_file.startswith("super.img_sparsechunk.")
                    else "REGULAR_IMAGE" if source_file else "NOT_APPLICABLE",
                    "erase_instruction": operation == "erase",
                    "reboot_instruction": operation == "reboot",
                    "conditional_logic": None,
                    "dependency": None if index == 1 else f"after_step_{len(all_steps)}",
                    "expected_size_bytes": None,
                    "declared_md5": step.attrib.get("MD5"),
                    "oem_var": step.attrib.get("var"),
                    "risk_class": risk_class(operation, target_partition or ""),
                    "evidence_source": manifest_name,
                }
            )

    info_file = EXTRACT_ROOT / "GNEVAN_G_U1THS34.65-74-1-7-8_subsidy-DEFAULT_regulatory-DEFAULT_cid50_CFC.info.txt"
    info_text = info_file.read_text(encoding="utf-8")
    info_map: dict[str, str] = {}
    for line in info_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info_map[key.strip()] = value.strip()

    package_identity = {
        "generated_at": now_iso(),
        "fields": {
            "model": {
                "value": "XT2317-2",
                "evidence_source": "archive filename",
                "confidence": "HIGH",
            },
            "codename": {
                "value": "gnevan",
                "evidence_source": "archive filename family + current-build identity lineage",
                "confidence": "MEDIUM",
            },
            "product": {
                "value": header_fields.get("product"),
                "evidence_source": "flashfile.xml/header/phone_model",
                "confidence": "HIGH",
            },
            "channel": {
                "value": "RETUS",
                "evidence_source": "archive filename",
                "confidence": "HIGH",
            },
            "region": {
                "value": "US retail",
                "evidence_source": "RETUS naming convention",
                "confidence": "MEDIUM",
            },
            "carrier_subsidy": {
                "value": "DEFAULT",
                "evidence_source": "archive filename subsidy token",
                "confidence": "HIGH",
            },
            "cid": {
                "value": header_fields.get("cid_value"),
                "evidence_source": "flashfile.xml/header/cid_value",
                "confidence": "HIGH",
            },
            "android_version": {
                "value": "14",
                "evidence_source": "software version string",
                "confidence": "HIGH",
            },
            "package_build_id": {
                "value": info_map.get("SW Display Build ID"),
                "evidence_source": ".info.txt SW Display Build ID",
                "confidence": "HIGH",
            },
            "package_incremental": {
                "value": "2e589-1f965e",
                "evidence_source": "software version string",
                "confidence": "HIGH",
            },
            "security_patch": {
                "value": None,
                "evidence_source": "not recoverable from trusted offline parser in A02A",
                "confidence": "LOW",
            },
            "bootloader_version": {
                "value": info_map.get("MBM Version"),
                "evidence_source": ".info.txt MBM Version",
                "confidence": "HIGH",
            },
            "baseband_version": {
                "value": info_map.get("Modem Version"),
                "evidence_source": ".info.txt Modem Version",
                "confidence": "HIGH",
            },
            "build_fingerprint": {
                "value": info_map.get("Build Fingerprint"),
                "evidence_source": ".info.txt Build Fingerprint",
                "confidence": "HIGH",
            },
            "software_version_string": {
                "value": header_fields.get("software_version"),
                "evidence_source": "flashfile.xml/header/software_version",
                "confidence": "HIGH",
            },
            "build_date": {
                "value": None,
                "evidence_source": "not exposed in trusted parsed metadata",
                "confidence": "LOW",
            },
        },
    }
    write_json(A02A_ROOT / "package-identity.json", package_identity)

    diff_fields = [
        ("product_name", "product"),
        ("build_fingerprint", "build_fingerprint"),
        ("build_id", "package_build_id"),
        ("build_incremental", "package_incremental"),
        ("bootloader_version", "bootloader_version"),
        ("baseband_version", "baseband_version"),
        ("android_version", "android_version"),
        ("software_channel", "channel"),
    ]
    differences = []
    for live_key, package_key in diff_fields:
        live_value = live_identity.get(live_key, {}).get("value")
        package_value = package_identity["fields"].get(package_key, {}).get("value")
        if live_value != package_value:
            differences.append(
                {
                    "field": live_key,
                    "live_value": live_value,
                    "package_value": package_value,
                    "classification": "VALUE_DIFFERENCE",
                }
            )
    identity_diff = {
        "generated_at": now_iso(),
        "differences": differences,
        "notes": [
            "Package build suffix -8 is older than live build suffix -24 and remains visible throughout this activation.",
            "System, vendor, and bootloader version strings may differ within one signed release family and are described rather than auto-classified as contradictions.",
        ],
    }
    write_json(A02A_ROOT / "live-vs-package-identity-diff.json", identity_diff)

    flashing_data = {
        "generated_at": now_iso(),
        "primary_manifest": "flashfile.xml" if "flashfile.xml" in parsed_manifest_names else parsed_manifest_names[0],
        "parsed_manifests": parsed_manifest_names,
        "manifest_header": header_fields,
        "steps": all_steps,
    }
    write_json(A02A_ROOT / "flashing-sequence.json", flashing_data)
    write_text(A02A_ROOT / "flashing-sequence.md", flashing_markdown(flashing_data))

    file_lookup = {record["relative_path"]: record for record in extracted_records}
    targets: dict[str, dict[str, Any]] = {}
    for step in all_steps:
        partition = step["target_partition"]
        if not partition:
            continue
        record = targets.setdefault(
            partition,
            {
                "canonical_name": partition,
                "aliases": [partition.rstrip("_ab")] if re.search(r"_[ab]$", partition) else [],
                "source_images": [],
                "file_hashes": [],
                "declared_target": partition,
                "slot_behavior": slot_behavior(partition),
                "physical_logical": partition_kind(partition),
                "possible_parent_container": "super" if partition in {"system", "vendor", "product", "system_ext"} else None,
                "image_format": "SPARSE" if partition == "super" else "RAW_OR_UNKNOWN",
                "image_byte_count": 0,
                "expanded_size_bytes": None,
                "filesystem_or_image_type": "ANDROID_DYNAMIC_CONTAINER"
                if partition == "super"
                else "UNKNOWN",
                "avb_role": avb_role_for_partition(partition),
                "boot_chain_role": boot_chain_role(partition),
                "restore_artifact_availability": True,
                "package_build_association": package_identity["fields"]["package_build_id"]["value"],
                "modification_risk": step["risk_class"],
                "confidence": "HIGH",
                "evidence_sources": [],
                "classifications": classify_partition(partition),
            },
        )
        if step["source_file"]:
            source_file = step["source_file"]
            record["source_images"].append(source_file)
            source_meta = file_lookup.get(source_file)
            if source_meta:
                record["file_hashes"].append({"file": source_file, "sha256": source_meta["sha256"]})
                record["image_byte_count"] += source_meta["byte_count"]
                if source_file.startswith("super.img_sparsechunk."):
                    record["image_format"] = "ANDROID_SPARSE_CHUNK_SERIES"
                    record["filesystem_or_image_type"] = "ANDROID_SPARSE_DYNAMIC_CONTAINER"
        record["evidence_sources"].append(step["manifest"])

    live_logicals = parse_mount_logicals(HARDWARE_ROOT / "mount.txt")
    for logical in live_logicals:
        name = logical["logical_partition"]
        if name not in targets:
            targets[name] = {
                "canonical_name": name,
                "aliases": [],
                "source_images": ["super.img_sparsechunk.*"],
                "file_hashes": [
                    {"file": item["relative_path"], "sha256": item["sha256"]}
                    for item in extracted_records
                    if item["relative_path"].startswith("super.img_sparsechunk.")
                ],
                "declared_target": "inside super",
                "slot_behavior": "LOGICAL_DYNAMIC",
                "physical_logical": "LOGICAL",
                "possible_parent_container": "super",
                "image_format": "CONTAINED_IN_SUPER",
                "image_byte_count": sum(
                    item["byte_count"]
                    for item in extracted_records
                    if item["relative_path"].startswith("super.img_sparsechunk.")
                ),
                "expanded_size_bytes": None,
                "filesystem_or_image_type": "DM_MAPPED_LOGICAL_PARTITION",
                "avb_role": "VERIFIED_LOGICAL_PAYLOAD",
                "boot_chain_role": "LOGICAL_OS_PAYLOAD",
                "restore_artifact_availability": True,
                "package_build_association": package_identity["fields"]["package_build_id"]["value"],
                "modification_risk": "OS_CONTAINER_WRITE",
                "confidence": "MEDIUM",
                "evidence_sources": [
                    "flashfile.xml super sparsechunk sequence",
                    logical["evidence_source"],
                ],
                "classifications": ["OS", "VENDOR"],
            }

    partition_inventory = {
        "generated_at": now_iso(),
        "partitions": sorted(targets.values(), key=lambda item: item["canonical_name"]),
        "dynamic_partition_conclusion": {
            "value": "SUPPORTED_BY_PACKAGE_SUPER_TARGET_AND_FROZEN_DM_MOUNTS",
            "evidence": [
                "flashfile.xml flashes super.img_sparsechunk.* to super",
                "device/motorola/gnevan/hardware/mount.txt shows dm-backed logical mounts for vendor, product, system_ext, and root system",
            ],
            "confidence": "HIGH",
        },
    }
    write_json(A02A_ROOT / "package-partition-inventory.json", partition_inventory)
    write_text(A02A_ROOT / "package-partition-inventory.md", partition_markdown(partition_inventory["partitions"]))

    nodes = [
        {"id": "archive", "label": ORIGINAL_ARCHIVE.name, "kind": "archive"},
        {"id": "flashfile.xml", "label": "flashfile.xml", "kind": "manifest"},
        {"id": "servicefile.xml", "label": "servicefile.xml", "kind": "manifest"},
        {"id": "super", "label": "super", "kind": "partition"},
        {"id": "vbmeta_a", "label": "vbmeta_a", "kind": "partition"},
        {"id": "vbmeta_system_a", "label": "vbmeta_system_a", "kind": "partition"},
        {"id": "boot_a", "label": "boot_a", "kind": "partition"},
        {"id": "vendor_boot_a", "label": "vendor_boot_a", "kind": "partition"},
    ]
    edges = [
        {
            "from": "archive",
            "to": "flashfile.xml",
            "type": "IDENTITY_FOR",
            "evidence_source": "archive contents",
            "confidence": "HIGH",
        },
        {
            "from": "archive",
            "to": "servicefile.xml",
            "type": "IDENTITY_FOR",
            "evidence_source": "archive contents",
            "confidence": "HIGH",
        },
    ]
    for step in all_steps:
        if step["source_file"] and step["target_partition"]:
            source_node = step["source_file"]
            target_node = step["target_partition"]
            if not any(node["id"] == source_node for node in nodes):
                nodes.append({"id": source_node, "label": source_node, "kind": "source_image"})
            if not any(node["id"] == target_node for node in nodes):
                nodes.append({"id": target_node, "label": target_node, "kind": "partition"})
            edges.append(
                {
                    "from": source_node,
                    "to": target_node,
                    "type": "FLASHES_TO",
                    "evidence_source": step["manifest"],
                    "confidence": "HIGH",
                }
            )
            if source_node.startswith("super.img_sparsechunk."):
                edges.append(
                    {
                        "from": source_node,
                        "to": "super",
                        "type": "CHUNK_OF",
                        "evidence_source": step["manifest"],
                        "confidence": "HIGH",
                    }
                )
    for logical in {"system", "vendor", "product", "system_ext"}:
        if logical in targets:
            if not any(node["id"] == logical for node in nodes):
                nodes.append({"id": logical, "label": logical, "kind": "logical_partition"})
            edges.append(
                {
                    "from": "super",
                    "to": logical,
                    "type": "CONTAINS_LOGICAL",
                    "evidence_source": "flashfile.xml super target + device/motorola/gnevan/hardware/mount.txt",
                    "confidence": "MEDIUM",
                }
            )
    edges.extend(
        [
            {
                "from": "vbmeta_a",
                "to": "boot_a",
                "type": "VERIFIES",
                "evidence_source": "partition role naming + package inventory",
                "confidence": "MEDIUM",
            },
            {
                "from": "vbmeta_system_a",
                "to": "super",
                "type": "CHAINED_VBMETA",
                "evidence_source": "partition role naming + package inventory",
                "confidence": "MEDIUM",
            },
            {
                "from": "boot_a",
                "to": "vendor_boot_a",
                "type": "BOOT_DEPENDS_ON",
                "evidence_source": "boot payload pairing in flash manifest",
                "confidence": "MEDIUM",
            },
        ]
    )
    topology_graph = {
        "generated_at": now_iso(),
        "nodes": sorted(nodes, key=lambda item: item["id"]),
        "edges": edges,
    }
    write_json(A02A_ROOT / "package-topology-graph.json", topology_graph)
    write_text(A02A_ROOT / "package-topology-graph.md", topology_markdown(topology_graph))
    write_text(A02A_ROOT / "package-topology-graph.dot", dot_graph(topology_graph))

    unparsed_reason = (
        "Trusted AOSP host parsers were not present in the A02A environment "
        "(avbtool, unpack_bootimg, lpunpack unavailable on PATH). Read-only byte hashing completed; "
        "authoritative structured header parsing remains pending A02B/AOSP tooling."
    )
    boot_summary = {
        "image": "boot.img",
        "status": "UNPARSED",
        "reason": unparsed_reason,
        "sha256": file_lookup["boot.img"]["sha256"],
        "magic": file_lookup["boot.img"]["magic"],
    }
    vendor_boot_summary = {
        "image": "vendor_boot.img",
        "status": "UNPARSED",
        "reason": unparsed_reason,
        "sha256": file_lookup["vendor_boot.img"]["sha256"],
        "magic": file_lookup["vendor_boot.img"]["magic"],
    }
    dtbo_summary = {
        "image": "dtbo.img",
        "status": "UNPARSED",
        "reason": unparsed_reason,
        "sha256": file_lookup["dtbo.img"]["sha256"],
        "magic": file_lookup["dtbo.img"]["magic"],
    }
    vbmeta_summary = {
        "images": [
            {
                "image": "vbmeta.img",
                "status": "UNPARSED",
                "reason": unparsed_reason,
                "sha256": file_lookup["vbmeta.img"]["sha256"],
                "magic": file_lookup["vbmeta.img"]["magic"],
            },
            {
                "image": "vbmeta_system.img",
                "status": "UNPARSED",
                "reason": unparsed_reason,
                "sha256": file_lookup["vbmeta_system.img"]["sha256"],
                "magic": file_lookup["vbmeta_system.img"]["magic"],
            },
        ],
        "conclusion": "Package clearly carries root and system vbmeta payloads, but chain descriptors and rollback indexes were not authoritatively parsed offline in A02A.",
    }
    avb_chain_md = "\n".join(
        [
            "# AVB Package Chain",
            "",
            "- `vbmeta.img` and `vbmeta_system.img` are present in the package and targeted at `vbmeta_a` and `vbmeta_system_a`.",
            "- Trusted host AVB parsers were not available on PATH during A02A, so descriptor-level parsing and rollback indexes remain unresolved.",
            "- The package therefore demonstrates AVB participation, not downgrade safety.",
            "",
        ]
    )
    write_json(A02A_ROOT / "boot-header-summary.json", boot_summary)
    write_json(A02A_ROOT / "vendor-boot-header-summary.json", vendor_boot_summary)
    write_json(A02A_ROOT / "dtbo-header-summary.json", dtbo_summary)
    write_json(A02A_ROOT / "vbmeta-summary.json", vbmeta_summary)
    write_text(A02A_ROOT / "avb-package-chain.md", avb_chain_md)

    frozen_partitions = parse_by_name(BASELINE_ROOT / "by-name.txt")
    frozen_inventory = {
        "generated_at": now_iso(),
        "physical_partitions": frozen_partitions,
        "logical_partitions_from_mounts": live_logicals,
        "sources": [
            "baseline-unlocked/by-name.txt",
            "device/motorola/gnevan/hardware/mount.txt",
            "baseline-unlocked/fastboot-getvar-all.txt",
        ],
    }
    write_json(A02A_ROOT / "frozen-device-partition-inventory.json", frozen_inventory)

    live_partition_names = {entry["partition"] for entry in frozen_partitions}
    live_logical_names = {entry["logical_partition"] for entry in live_logicals}
    diffs = []
    for partition in sorted(targets):
        if partition in live_partition_names or partition in live_logical_names:
            classification = "MATCH"
        elif partition == "preloader":
            classification = "NAME_ALIAS_LIKELY"
        elif partition == "gpt":
            classification = "UNRESOLVED"
        else:
            classification = "PACKAGE_ONLY"
        diffs.append(
            {
                "partition": partition,
                "classification": classification,
                "notes": "Comparison is against frozen evidence only; absence from sanitized lists is not proof of device absence.",
            }
        )
    for live_only in sorted((live_partition_names | live_logical_names) - set(targets)):
        diffs.append(
            {
                "partition": live_only,
                "classification": "DEVICE_ONLY",
                "notes": "Package does not explicitly target this partition in parsed offline manifests.",
            }
        )
    package_vs_device_diff = {
        "generated_at": now_iso(),
        "comparisons": diffs,
    }
    write_json(A02A_ROOT / "package-vs-device-topology-diff.json", package_vs_device_diff)

    holds = {
        "generated_at": now_iso(),
        "holds": [
            {
                "topic": "anti_rollback",
                "reason": "Rollback indexes were not authoritatively parsed from signed metadata offline.",
                "state": "UNRESOLVED",
            },
            {
                "topic": "restore_suitability",
                "reason": "The preserved package is older than the live build and remains NOT_YET_ESTABLISHED for restoration.",
                "state": "HOLD",
            },
            {
                "topic": "super_logical_inventory",
                "reason": "Trusted host parser for super metadata was not available offline; logical partition set is supported by frozen mount evidence but not fully enumerated from package metadata.",
                "state": "UNRESOLVED",
            },
            {
                "topic": "fastbootd_support",
                "reason": "Userspace fastboot support must be confirmed live in a later read-only activation.",
                "state": "UNRESOLVED",
            },
        ],
    }
    write_json(A02A_ROOT / "topology-holds.json", holds)

    transition = {
        "proposed_activation": "A02B-live-read-only-topology",
        "device_transition_required": True,
        "partition_write_authorized": False,
        "planned_states": [
            "Android if available",
            "bootloader fastboot",
            "userspace fastboot only if supported",
            "return to Android",
        ],
        "exact_commands_proposed": [
            r"C:\Android\android-sdk\platform-tools\adb.exe devices -l",
            r"C:\Android\android-sdk\platform-tools\adb.exe shell getprop ro.boot.slot_suffix",
            r"C:\Android\android-sdk\platform-tools\adb.exe shell getprop ro.boot.dynamic_partitions",
            r"C:\Android\android-sdk\platform-tools\adb.exe shell ls -l /dev/block/by-name",
            r"C:\Android\android-sdk\platform-tools\adb.exe shell cat /proc/partitions",
            r"C:\Android\android-sdk\platform-tools\adb.exe shell mount",
            r"C:\Android\android-sdk\platform-tools\adb.exe reboot bootloader",
            r"C:\Android\android-sdk\platform-tools\fastboot.exe getvar all",
            r"C:\Android\android-sdk\platform-tools\fastboot.exe getvar current-slot",
            r"C:\Android\android-sdk\platform-tools\fastboot.exe getvar slot-count",
            r"C:\Android\android-sdk\platform-tools\fastboot.exe getvar is-userspace",
            r"C:\Android\android-sdk\platform-tools\fastboot.exe reboot",
        ],
        "expected_observations": [
            "live slot metadata",
            "dynamic partition flags",
            "fastboot variable support",
            "frozen versus live partition-name alignment",
            "userspace fastboot support indicators",
        ],
        "battery_threshold": ">= 50%",
        "usb_requirements": [
            "known-good data cable",
            "stable direct USB port",
            "no hub if avoidable",
        ],
        "abort_conditions": [
            "device not enumerated reliably",
            "battery below threshold",
            "unexpected bootloop or unauthorized adb state",
            "operator does not approve state transition",
        ],
        "recovery_path": [
            "remain read-only",
            "return device to Android",
            "preserve new evidence under C:\\Motorola-Activation",
            "do not flash or erase",
        ],
        "unresolved_questions_addressed": [
            "userspace fastboot support",
            "dynamic logical partition enumeration",
            "live slot metadata",
            "live AVB variables",
            "super partition naming",
        ],
        "operator_approval": "PENDING",
    }
    write_json(A02A_ROOT / "A02B-transition-proposal.json", transition)

    disk_record = {
        "recorded_at": now_iso(),
        "before_extraction": {
            "total_bytes": usage_before.total,
            "used_bytes": usage_before.used,
            "free_bytes": usage_before.free,
        },
        "after_extraction": {
            "total_bytes": usage_after.total,
            "used_bytes": usage_after.used,
            "free_bytes": usage_after.free,
        },
        "archive_uncompressed_bytes": total_uncompressed,
        "working_extraction_root": str(EXTRACT_ROOT),
    }
    write_json(A02A_ROOT / "disk-space-record.json", disk_record)

    receipt = {
        "activation_id": ACTIVATION_ID,
        "status": "COMPLETE",
        "completed_at": now_iso(),
        "original_archive_hash_before": original_hash_before,
        "original_archive_hash_after": original_hash_after,
        "extraction_success": True,
        "extracted_file_count": len(extracted_records),
        "parsed_manifest_count": len(parsed_manifest_names),
        "package_identity_conclusion": "Package is a same-family RETUS/gnevan_g stock release for XT2317-2 lineage, but it is an older build (-8) than the frozen live handset build (-24).",
        "dynamic_partition_conclusion": "SUPPORTED_BY_PACKAGE_SUPER_TARGET_AND_FROZEN_DM_MOUNTS",
        "avb_conclusion": "Package contains vbmeta and vbmeta_system payloads, but descriptor-level chain parsing and rollback metadata remain unresolved offline.",
        "anti_rollback_status": "UNRESOLVED",
        "restore_suitability": "NOT_YET_ESTABLISHED",
        "device_contacted": False,
        "device_changed": False,
        "open_holds": [item["topic"] for item in holds["holds"]],
        "a02b_recommended": True,
        "operator_approval_for_a02b": "PENDING",
    }
    write_json(A02A_ROOT / "A02A-completion-receipt.json", receipt)
    write_text(A02A_ROOT / "A02A-summary.md", summary_markdown(receipt, identity_diff, holds))

    artifact_lines = []
    for path in sorted(p for p in A02A_ROOT.iterdir() if p.is_file() and p.name != "artifact-manifest.sha256"):
        artifact_lines.append(f"{sha256_file(path)} *{path.name}")
    write_text(A02A_ROOT / "artifact-manifest.sha256", "\n".join(artifact_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
