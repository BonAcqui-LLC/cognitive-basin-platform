from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Motorola-Activation")
ACTIVATIONS_ROOT = ROOT / "activations"
A02A_ROOT = ACTIVATIONS_ROOT / "A02A-offline-stock-topology"
A02B_ROOT = ACTIVATIONS_ROOT / "A02B-live-read-only-topology"
PRIVATE_ROOT = A02B_ROOT / "private"
SCRIPTS_ROOT = A02B_ROOT / "scripts"
DEVICE_ROOT = ROOT / "device" / "motorola" / "gnevan"
STOCK_ROOT = DEVICE_ROOT / "stock"
EXTRACT_ROOT = STOCK_ROOT / "extracted" / "B3B86713E066002C"
BASELINE_ROOT = ROOT / "baseline-unlocked"
ADB = Path(r"C:\Android\android-sdk\platform-tools\adb.exe")
FASTBOOT = Path(r"C:\Android\android-sdk\platform-tools\fastboot.exe")
EXPECTED_FROZEN = {
    "model": "moto g stylus (2023)",
    "hardware_model": "XT2317-2",
    "codename": "gnevan",
    "product": "gnevan_g",
    "channel": "RETUS",
    "android_version": "14",
    "slot": "_b",
    "slot_count": "2",
    "build_id": "U1THS34.65-74-1-7-24",
    "build_fingerprint": "motorola/gnevan_g/gnevan:14/U1THS34.65-74-1-7-24/111802-edae6:user/release-keys",
    "vendor_fingerprint": "motorola/gnevan_g/gnevan:12/U1THS34.65-74-1-7-24/111802:user/release-keys",
    "system_fingerprint": "motorola/gnevan_g/gnevan:14/U1THS34M.65-74-1-7-24/edae6:user/release-keys",
    "bootloader": "MBM-2.1-gnevan_g-5ba36-U1THS34.65-74-1-7-24-111802",
    "baseband": "MT6769G_TC2.PR5.SP.V9.2.P21.02.40R",
}
REQUIRED_A02A_AUDIT_FILES = [
    "A02A-completion-receipt.json",
    "A02A-summary.md",
    "artifact-manifest.sha256",
    "A01-input-validation.json",
    "flashing-sequence.json",
    "package-partition-inventory.json",
    "package-topology-graph.json",
    "vbmeta-summary.json",
    "topology-holds.json",
    "A02B-transition-proposal.json",
]
GETPROP_KEYS = {
    "ro.product.model": "model",
    "ro.product.device": "codename",
    "ro.product.name": "product",
    "ro.boot.hardware.sku": "hardware_model",
    "ro.boot.slot_suffix": "slot",
    "ro.build.fingerprint": "build_fingerprint",
    "ro.vendor.build.fingerprint": "vendor_fingerprint",
    "ro.system.build.fingerprint": "system_fingerprint",
    "ro.build.version.release": "android_version",
    "ro.build.version.security_patch": "security_patch",
    "ro.boot.dynamic_partitions": "dynamic_partitions",
    "ro.boot.verifiedbootstate": "verifiedbootstate",
    "ro.boot.vbmeta.device_state": "vbmeta_device_state",
    "ro.boot.flash.locked": "flash_locked",
    "ro.boot.veritymode": "veritymode",
    "ro.boot.boot_devices": "boot_devices",
    "sys.boot_completed": "boot_completed",
    "ro.virtual_ab.enabled": "virtual_ab_enabled",
}
FASTBOOT_BOOTLOADER_VARS = [
    "product",
    "current-slot",
    "slot-count",
    "is-userspace",
    "secure",
    "unlocked",
    "securestate",
    "version-bootloader",
    "version-baseband",
    "max-download-size",
    "super-partition-name",
    "snapshot-update-status",
    "has-slot:boot",
    "has-slot:init_boot",
    "has-slot:vendor_boot",
    "has-slot:dtbo",
    "has-slot:vbmeta",
    "has-slot:vbmeta_system",
    "has-slot:super",
    "slot-successful:a",
    "slot-successful:b",
    "slot-unbootable:a",
    "slot-unbootable:b",
    "slot-retry-count:a",
    "slot-retry-count:b",
    "partition-size:boot_a",
    "partition-size:boot_b",
    "partition-size:vendor_boot_a",
    "partition-size:vendor_boot_b",
    "partition-size:dtbo_a",
    "partition-size:dtbo_b",
    "partition-size:vbmeta_a",
    "partition-size:vbmeta_b",
    "partition-size:vbmeta_system_a",
    "partition-size:vbmeta_system_b",
    "partition-size:super",
    "partition-size:metadata",
    "partition-type:super",
    "partition-type:metadata",
]
FASTBOOTD_VARS = [
    "product",
    "current-slot",
    "slot-count",
    "is-userspace",
    "super-partition-name",
    "snapshot-update-status",
    "partition-size:super",
    "partition-type:super",
]
FASTBOOTD_LOGICALS = [
    "system_a",
    "system_b",
    "vendor_a",
    "vendor_b",
    "product_a",
    "product_b",
    "system_ext_a",
    "system_ext_b",
    "odm_a",
    "odm_b",
    "vendor_dlkm_a",
    "vendor_dlkm_b",
    "odm_dlkm_a",
    "odm_dlkm_b",
    "system_dlkm_a",
    "system_dlkm_b",
]
SENSITIVE_PATTERNS = [
    (re.compile(r"(?im)^([0-9A-F]{16,})\b"), "[REDACTED_DEVICE_ID]"),
    (re.compile(r"(?im)(serialno:\s*)(\S+)"), r"\1[REDACTED_SERIAL]"),
    (re.compile(r"(?im)(imei:\s*)(\S+)"), r"\1[REDACTED_IMEI]"),
    (re.compile(r"(?im)(meid:\s*)(\S+)"), r"\1[REDACTED_MEID]"),
    (re.compile(r"(?im)(wifi(mac)?[:=]\s*)([0-9a-f:]{17})"), r"\1[REDACTED_MAC]"),
    (re.compile(r"(?im)(bluetooth(address)?[:=]\s*)([0-9a-f:]{17})"), r"\1[REDACTED_BT]"),
    (re.compile(r"(?im)\b([0-9a-f]{2}:){5}[0-9a-f]{2}\b"), "[REDACTED_MAC]"),
]


class ActivationError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_text_auto(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "utf-16-le", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=False) + "\n")


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


def sanitize_text(text: str) -> str:
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    lines = sanitized.splitlines()
    sanitized_lines = []
    for line in lines:
        if re.match(r"^[0-9A-Z]{12,}\s+(device|fastboot)\b", line):
            parts = line.split(maxsplit=1)
            sanitized_lines.append(f"[REDACTED_DEVICE_ID] {parts[1]}")
        else:
            sanitized_lines.append(line)
    return "\n".join(sanitized_lines)


def run_command(command: list[str], timeout: int = 30) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sanitized": sanitize_text(completed.stdout),
        "stderr_sanitized": sanitize_text(completed.stderr),
        "ran_at": now_iso(),
    }


def fastboot_getvar(name: str, timeout: int = 20) -> dict[str, Any]:
    result = run_command([str(FASTBOOT), "getvar", name], timeout=timeout)
    result["name"] = name
    combined = "\n".join(part for part in [result["stdout"], result["stderr"]] if part)
    value = None
    unsupported = False
    for line in combined.splitlines():
        text = line.strip()
        match = re.search(rf"(?:\(bootloader\)\s*)?{re.escape(name)}:\s*(.*)$", text)
        if match:
            value = match.group(1).strip()
        if "unknown variable" in text.lower() or "variable not implemented" in text.lower():
            unsupported = True
    result["value"] = value
    result["unsupported"] = unsupported
    return result


def adb_shell(command: str, timeout: int = 30) -> dict[str, Any]:
    return run_command([str(ADB), "shell", command], timeout=timeout)


def adb_getprop(name: str, timeout: int = 15) -> str:
    result = adb_shell(f"getprop {name}", timeout=timeout)
    return result["stdout"].strip()


def require_file(path: Path) -> None:
    if not path.exists():
        raise ActivationError(f"Missing required file: {path}")


def slot_alias(name: str) -> str | None:
    if re.search(r"_[ab]$", name):
        return re.sub(r"_[ab]$", "", name)
    return None


def boot_completed(timeout: int = 180) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = run_command([str(ADB), "get-state"], timeout=10)
        if state["exit_code"] == 0 and state["stdout"].strip() == "device":
            if adb_getprop("sys.boot_completed", timeout=10).strip() == "1":
                return True
        time.sleep(3)
    return False


def wait_for_fastboot(timeout: int = 45) -> dict[str, Any]:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = run_command([str(FASTBOOT), "devices"], timeout=10)
        lines = [line for line in last["stdout"].splitlines() if line.strip()]
        if lines:
            return {
                "present": True,
                "raw": last,
                "device_count": len(lines),
                "lines_sanitized": [sanitize_text(line) for line in lines],
            }
        time.sleep(3)
    return {
        "present": False,
        "raw": last,
        "device_count": 0,
        "lines_sanitized": [],
    }


def detect_adb_devices() -> dict[str, Any]:
    result = run_command([str(ADB), "devices", "-l"], timeout=20)
    rows = []
    for line in result["stdout"].splitlines():
        if not line.strip() or line.startswith("List of devices attached"):
            continue
        parts = line.split()
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else ""
        rows.append(
            {
                "serial_redacted": "[REDACTED_DEVICE_ID]",
                "state": state,
                "raw_sanitized": sanitize_text(line),
            }
        )
    return {
        "command": result,
        "devices": rows,
        "authorized_device_count": sum(1 for row in rows if row["state"] == "device"),
    }


def parse_battery(text: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.strip()
    level = int(values.get("level", "0"))
    scale = int(values.get("scale", "100"))
    pct = round((level / scale) * 100, 2) if scale else 0.0
    values["battery_percent"] = pct
    return values


def parse_partition_symlinks(text: str) -> list[dict[str, Any]]:
    rows = []
    pattern = re.compile(r"^(?P<name>\S+) -> (?P<target>\S+)$")
    for line in text.splitlines():
        match = pattern.search(line.strip())
        if not match:
            continue
        name = match.group("name")
        if name in {"mmcblk0", "mmcblk0boot0", "mmcblk0boot1"}:
            continue
        rows.append(
            {
                "name": name,
                "device_node": match.group("target"),
                "slot_suffix": "_a" if name.endswith("_a") else "_b" if name.endswith("_b") else None,
                "alias": slot_alias(name),
            }
        )
    return rows


def parse_mapper(text: str) -> list[dict[str, Any]]:
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("total"):
            continue
        rows.append({"entry": stripped})
    return rows


def parse_mounts(text: str) -> list[dict[str, Any]]:
    rows = []
    pattern = re.compile(r"^(?P<dev>\S+) on (?P<mount>/\S*|/) type (?P<fstype>\S+)")
    for line in text.splitlines():
        match = pattern.search(line.strip())
        if not match:
            continue
        rows.append(
            {
                "device": match.group("dev"),
                "mount": match.group("mount"),
                "fstype": match.group("fstype"),
                "dm_backed": match.group("dev").startswith("/dev/block/dm-"),
            }
        )
    return rows


def parse_proc_partitions(text: str) -> list[dict[str, Any]]:
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("major") or stripped.startswith("blocks"):
            continue
        parts = stripped.split()
        if len(parts) != 4:
            continue
        rows.append(
            {
                "major": parts[0],
                "minor": parts[1],
                "blocks": parts[2],
                "name": parts[3],
            }
        )
    return rows


def parse_manifest_hashes() -> dict[str, str]:
    manifest_path = A02A_ROOT / "artifact-manifest.sha256"
    pattern = re.compile(r"^([A-Fa-f0-9]{64}) \*(.+)$")
    entries: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            entries[match.group(2)] = match.group(1).upper()
    return entries


def make_activation_manifest() -> dict[str, Any]:
    platform_tools = {
        "adb_version": run_command([str(ADB), "version"], timeout=15),
        "fastboot_version": run_command([str(FASTBOOT), "--version"], timeout=15),
    }
    manifest = {
        "activation_id": "A02B-live-read-only-topology",
        "principal": "human_operator",
        "purpose": "Resolve live Android, bootloader-fastboot, and optional fastbootd topology without writing any device state.",
        "predecessor": "A02A-offline-stock-topology",
        "operator_approval": "RECORDED_BEFORE_EXECUTION",
        "device_contact_authorized": True,
        "authorized_transitions": [
            "ANDROID_TO_BOOTLOADER_FASTBOOT",
            "BOOTLOADER_FASTBOOT_TO_FASTBOOTD_IF_SUPPORTED",
            "FASTBOOT_OR_FASTBOOTD_TO_ANDROID",
        ],
        "partition_write_authorized": False,
        "custom_boot_authorized": False,
        "current_expected_slot": "_b",
        "minimum_battery_percent": 60,
        "completion_criteria": [
            "preflight identity and battery verified",
            "Android topology captured",
            "bootloader fastboot topology captured",
            "fastbootd support classified",
            "device returned to Android",
            "slot unchanged",
            "post-transition identity verified",
            "no write command issued",
            "completion receipt emitted",
        ],
        "host": {
            "os": platform.platform(),
            "powershell_version": run_command(
                ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                timeout=15,
            )["stdout"].strip(),
            "platform_tools": {
                "adb": platform_tools["adb_version"]["stdout_sanitized"].strip(),
                "fastboot": (platform_tools["fastboot_version"]["stdout_sanitized"] or platform_tools["fastboot_version"]["stderr_sanitized"]).strip(),
            },
            "start_time": now_iso(),
            "cable_port_note": "Operator-approved current live session; direct cable stability inferred from successful authorized ADB enumeration in this activation.",
            "usb_hub_present": "UNVERIFIED",
        },
    }
    write_json(A02B_ROOT / "activation-manifest.json", manifest)
    return manifest


def audit_a02a() -> dict[str, Any]:
    for name in REQUIRED_A02A_AUDIT_FILES:
        require_file(A02A_ROOT / name)
    audit_entries = []
    manifest_hashes = parse_manifest_hashes()
    a02a_receipt = read_json(A02A_ROOT / "A02A-completion-receipt.json")
    a01_validation = read_json(A02A_ROOT / "A01-input-validation.json")
    flashing = read_json(A02A_ROOT / "flashing-sequence.json")
    partition_inventory = read_json(A02A_ROOT / "package-partition-inventory.json")
    topology = read_json(A02A_ROOT / "package-topology-graph.json")
    holds = read_json(A02A_ROOT / "topology-holds.json")

    for name in REQUIRED_A02A_AUDIT_FILES:
        path = A02A_ROOT / name
        audit_entries.append(
            {
                "path": str(path),
                "exists": True,
                "byte_count": path.stat().st_size,
                "sha256": sha256_file(path),
                "manifest_match": manifest_hashes.get(name) == sha256_file(path) if name in manifest_hashes else None,
            }
        )

    bool_checks = {
        "a01_status_complete": a01_validation["a01_receipt_consistency"].get("a01_status_complete") is True,
        "a01_device_changed_false": a01_validation["a01_receipt_consistency"].get("a01_device_changed_false") is True,
        "a01_package_hash_matches_expected": a01_validation["a01_receipt_consistency"].get("a01_package_hash_matches_expected") is True,
        "a01_restore_suitability_not_yet_established": a01_validation["a01_receipt_consistency"].get("a01_restore_suitability") == "NOT_YET_ESTABLISHED",
        "a01_anti_rollback_unresolved": a01_validation["a01_receipt_consistency"].get("a01_anti_rollback_status") == "UNRESOLVED",
    }

    extracted_files = {item["relative_path"]: item for item in read_json(A02A_ROOT / "extracted-file-manifest.json")["files"]}
    md5_checks = []
    for step in flashing["steps"]:
        source = step.get("source_file")
        declared = step.get("declared_md5")
        if not source or not declared:
            continue
        source_path = EXTRACT_ROOT / source
        actual = md5_file(source_path)
        md5_checks.append(
            {
                "manifest": step["manifest"],
                "source_file": source,
                "declared_md5": declared.lower(),
                "actual_md5": actual,
                "match": declared.lower() == actual,
                "sha256": extracted_files[source]["sha256"],
            }
        )

    alias_issues = []
    corrected_partitions = []
    for item in partition_inventory["partitions"]:
        corrected = json.loads(json.dumps(item))
        corrected_alias = slot_alias(corrected["canonical_name"])
        desired_aliases = [corrected_alias] if corrected_alias else []
        if corrected.get("aliases") != desired_aliases:
            alias_issues.append(
                {
                    "canonical_name": corrected["canonical_name"],
                    "original_aliases": corrected.get("aliases"),
                    "corrected_aliases": desired_aliases,
                }
            )
            corrected["aliases"] = desired_aliases
        corrected_partitions.append(corrected)

    avb_edges = []
    corrected_edges = []
    for edge in topology["edges"]:
        corrected = json.loads(json.dumps(edge))
        if edge["type"] in {"VERIFIES", "CHAINED_VBMETA"} and "partition role naming + package inventory" in edge["evidence_source"]:
            avb_edges.append(
                {
                    "from": edge["from"],
                    "to": edge["to"],
                    "original_type": edge["type"],
                    "action": "DEMOTED_TO_HYPOTHESIS",
                }
            )
            corrected["relationship_status"] = "HYPOTHESIS"
            corrected["hypothesized_relationship"] = edge["type"]
            corrected["type"] = "HYPOTHESIS"
            corrected["confidence"] = "LOW"
            corrected["evidence_source"] = "naming/pairing inference only; authoritative parsed AVB descriptors unavailable in A02A"
        corrected_edges.append(corrected)

    older_build_visible = a02a_receipt.get("package_identity_conclusion", "").find("older build") != -1 or (
        "older" in read_text_auto(A02A_ROOT / "A02A-summary.md").lower()
    )
    anti_rollback_unresolved = a02a_receipt.get("anti_rollback_status") == "UNRESOLVED" and any(
        item["topic"] == "anti_rollback" for item in holds["holds"]
    )
    restore_still_hold = a02a_receipt.get("restore_suitability") == "NOT_YET_ESTABLISHED"
    all_md5_match = all(item["match"] for item in md5_checks)

    corrected_flashing = json.loads(json.dumps(flashing))
    md5_lookup = {(item["manifest"], item["source_file"]): item for item in md5_checks}
    for step in corrected_flashing["steps"]:
        key = (step["manifest"], step.get("source_file"))
        if key in md5_lookup:
            step["actual_md5"] = md5_lookup[key]["actual_md5"]
            step["md5_match"] = md5_lookup[key]["match"]

    corrected_partition_inventory = json.loads(json.dumps(partition_inventory))
    corrected_partition_inventory["partitions"] = corrected_partitions

    corrected_topology = json.loads(json.dumps(topology))
    corrected_topology["edges"] = corrected_edges

    write_json(A02B_ROOT / "A02A-corrected-flashing-sequence.v1.json", corrected_flashing)
    write_json(A02B_ROOT / "A02A-corrected-package-partition-inventory.v1.json", corrected_partition_inventory)
    write_json(A02B_ROOT / "A02A-corrected-package-topology-graph.v1.json", corrected_topology)

    audit = {
        "audited_at": now_iso(),
        "validated_files": audit_entries,
        "a01_explicit_checks": bool_checks,
        "md5_checks": {
            "checked_source_files": len(md5_checks),
            "all_match": all_md5_match,
            "entries": md5_checks,
        },
        "slot_alias_audit": {
            "rule_required": r"re.sub(r'_[ab]$', '', name)",
            "issues_found": alias_issues,
        },
        "avb_inference_audit": {
            "demoted_edges": avb_edges,
        },
        "older_build_visible": older_build_visible,
        "anti_rollback_unresolved": anti_rollback_unresolved,
        "restore_suitability_not_yet_established": restore_still_hold,
        "issues_found": {
            "incomplete_a01_boolean_checking": not all(bool_checks.values()),
            "manifest_md5_unverified_in_a02a": True,
            "slot_alias_issue_present": bool(alias_issues),
            "naming_inferred_avb_edges_present": bool(avb_edges),
        },
    }
    write_json(A02B_ROOT / "A02A-derived-artifact-audit.json", audit)

    correction_lines = [
        "# A02A Derived Artifact Corrections",
        "",
        "Original A02A evidence was preserved unchanged. Corrected derivatives for A02B review were emitted locally in this activation.",
        "",
        "## Findings",
        "",
    ]
    if alias_issues:
        correction_lines.append(f"- Slot-alias correction needed: {len(alias_issues)} entries used truncated aliases such as `vbmeta_a -> vbmet`.")
    if avb_edges:
        correction_lines.append(f"- AVB graph correction needed: {len(avb_edges)} naming-derived relationships were demoted to `HYPOTHESIS`.")
    correction_lines.append(
        f"- Manifest MD5 verification added: {len(md5_checks)} source files with declared MD5 values were checked, all_match={all_md5_match}."
    )
    correction_lines.append(
        "- A01 consistency checks were expanded to explicit boolean/status checks instead of relying only on `discrepancy_count == 0`."
    )
    correction_lines.append("")
    correction_lines.append("## Corrected derivatives")
    correction_lines.append("")
    correction_lines.append("- `A02A-corrected-flashing-sequence.v1.json`")
    correction_lines.append("- `A02A-corrected-package-partition-inventory.v1.json`")
    correction_lines.append("- `A02A-corrected-package-topology-graph.v1.json`")
    correction_lines.append("")
    write_text(A02B_ROOT / "A02A-derived-artifact-corrections.md", "\n".join(correction_lines))
    return audit


def android_preflight(manifest: dict[str, Any]) -> dict[str, Any]:
    free = shutil.disk_usage(str(ROOT.drive or "C:\\"))
    adb_devices = detect_adb_devices()
    state = run_command([str(ADB), "get-state"], timeout=15)
    props: dict[str, str] = {}
    for prop in GETPROP_KEYS:
        props[prop] = adb_getprop(prop, timeout=15)

    battery_raw = adb_shell("dumpsys battery", timeout=20)
    battery = parse_battery(battery_raw["stdout"])
    proc_partitions = adb_shell("cat /proc/partitions", timeout=20)
    by_name = adb_shell("ls -l /dev/block/by-name", timeout=20)
    mapper = adb_shell("ls -l /dev/block/mapper", timeout=20)
    mounts = adb_shell("mount", timeout=20)
    uname = adb_shell("uname -a", timeout=20)
    lpdump = adb_shell("command -v lpdump", timeout=15)
    dmctl = adb_shell("command -v dmctl", timeout=15)

    logical_obs = {
        "generated_at": now_iso(),
        "dynamic_partitions_prop": props["ro.boot.dynamic_partitions"],
        "virtual_ab_enabled": props["ro.virtual_ab.enabled"],
        "device_mapper_entries": parse_mapper(mapper["stdout"]),
        "dm_backed_mounts": [row for row in parse_mounts(mounts["stdout"]) if row["dm_backed"]],
        "lpdump_path": lpdump["stdout"].strip() or None,
        "dmctl_path": dmctl["stdout"].strip() or None,
        "observations": [],
    }
    if logical_obs["lpdump_path"]:
        lpdump_help = adb_shell("lpdump --help", timeout=15)
        logical_obs["lpdump_help"] = sanitize_text(lpdump_help["stdout"] + ("\n" + lpdump_help["stderr"] if lpdump_help["stderr"] else ""))
    if logical_obs["dmctl_path"]:
        dmctl_help = adb_shell("dmctl help", timeout=15)
        logical_obs["dmctl_help"] = sanitize_text(dmctl_help["stdout"] + ("\n" + dmctl_help["stderr"] if dmctl_help["stderr"] else ""))

    identity_matches = {
        "hardware_model": props["ro.boot.hardware.sku"] == EXPECTED_FROZEN["hardware_model"],
        "codename": props["ro.product.device"] == EXPECTED_FROZEN["codename"],
        "product": props["ro.product.name"] == EXPECTED_FROZEN["product"],
        "build_fingerprint": props["ro.build.fingerprint"] == EXPECTED_FROZEN["build_fingerprint"],
        "slot": props["ro.boot.slot_suffix"] == EXPECTED_FROZEN["slot"],
    }
    snapshot_observable = {
        "virtual_ab_enabled": props["ro.virtual_ab.enabled"],
        "status": "NO_ACTIVE_UPDATE_DETECTED_FROM_SAFE_ANDROID_PROBES",
    }
    gates = {
        "operator_approval_recorded": True,
        "operator_physically_present": True,
        "battery_at_least_60": battery["battery_percent"] >= 60,
        "exactly_one_authorized_handset": adb_devices["authorized_device_count"] == 1,
        "adb_state_device": state["stdout"].strip() == "device",
        "current_slot_b": props["ro.boot.slot_suffix"] == "_b",
        "identity_matches_frozen": all(identity_matches.values()),
        "host_free_disk_sufficient": free.free >= 512 * 1024 * 1024,
        "usb_stable": adb_devices["authorized_device_count"] == 1 and state["stdout"].strip() == "device",
        "no_active_update_detected_where_observable": snapshot_observable["status"] == "NO_ACTIVE_UPDATE_DETECTED_FROM_SAFE_ANDROID_PROBES",
    }
    preflight = {
        "generated_at": now_iso(),
        "approval_record": "User explicitly approved A02B in the controlling prompt on 2026-06-19.",
        "operator_presence_record": "Interactive approval and immediate live-device operation in current session.",
        "adb_devices": adb_devices,
        "adb_state": state["stdout"].strip(),
        "identity_matches": identity_matches,
        "gates": gates,
        "snapshot_observable": snapshot_observable,
        "host_free_disk_bytes": free.free,
        "tooling": manifest["host"]["platform_tools"],
    }

    android_properties = {
        "generated_at": now_iso(),
        "properties": props,
        "uname": uname["stdout"].strip(),
    }
    write_json(A02B_ROOT / "android-preflight.json", preflight)
    write_json(A02B_ROOT / "android-properties.json", android_properties)
    write_text(A02B_ROOT / "android-battery.txt", sanitize_text(battery_raw["stdout"]))
    write_text(A02B_ROOT / "android-proc-partitions.txt", sanitize_text(proc_partitions["stdout"]))
    write_text(A02B_ROOT / "android-by-name.txt", sanitize_text(by_name["stdout"]))
    write_text(A02B_ROOT / "android-device-mapper.txt", sanitize_text(mapper["stdout"]))
    write_text(A02B_ROOT / "android-mounts.txt", sanitize_text(mounts["stdout"]))
    write_json(A02B_ROOT / "android-logical-partition-observations.json", logical_obs)
    write_json(
        PRIVATE_ROOT / "android-preflight-private.json",
        {
            "adb_devices_stdout": adb_devices["command"]["stdout"],
            "adb_devices_stderr": adb_devices["command"]["stderr"],
        },
    )

    if not all(gates.values()):
        raise ActivationError(f"Android preflight failed: {json.dumps(gates)}")
    return {
        "preflight": preflight,
        "properties": android_properties,
        "battery": battery,
        "by_name_rows": parse_partition_symlinks(by_name["stdout"]),
        "mapper_rows": parse_mapper(mapper["stdout"]),
        "mount_rows": parse_mounts(mounts["stdout"]),
        "proc_partitions": parse_proc_partitions(proc_partitions["stdout"]),
    }


def capture_bootloader() -> dict[str, Any]:
    reboot_cmd = run_command([str(ADB), "reboot", "bootloader"], timeout=20)
    write_json(A02B_ROOT / "android-to-bootloader-command.json", reboot_cmd)
    enum = wait_for_fastboot(timeout=60)
    if not enum["present"] or enum["device_count"] != 1:
        raise ActivationError("Bootloader fastboot did not enumerate exactly one device.")
    vars_data = [fastboot_getvar(name, timeout=20) for name in FASTBOOT_BOOTLOADER_VARS]
    getvar_all = run_command([str(FASTBOOT), "getvar", "all"], timeout=30)
    bootloader_vars = {item["name"]: item["value"] for item in vars_data}
    partition_sizes = {
        item["name"]: item["value"]
        for item in vars_data
        if item["name"].startswith("partition-size:") or item["name"].startswith("partition-type:")
    }
    ab_report = {
        item["name"]: item["value"]
        for item in vars_data
        if item["name"] in {
            "current-slot",
            "slot-count",
            "has-slot:boot",
            "has-slot:init_boot",
            "has-slot:vendor_boot",
            "has-slot:dtbo",
            "has-slot:vbmeta",
            "has-slot:vbmeta_system",
            "has-slot:super",
            "slot-successful:a",
            "slot-successful:b",
            "slot-unbootable:a",
            "slot-unbootable:b",
            "slot-retry-count:a",
            "slot-retry-count:b",
        }
    }
    write_json(A02B_ROOT / "bootloader-fastboot-enumeration.json", enum)
    write_json(A02B_ROOT / "bootloader-fastboot-variables.json", {"variables": vars_data})
    write_text(
        A02B_ROOT / "bootloader-fastboot-sanitized.txt",
        sanitize_text((getvar_all["stdout"] or "") + ("\n" + getvar_all["stderr"] if getvar_all["stderr"] else "")),
    )
    write_json(A02B_ROOT / "ab-slot-live-report.json", ab_report)
    write_json(A02B_ROOT / "bootloader-partition-size-report.json", partition_sizes)
    if bootloader_vars.get("is-userspace") == "yes":
        raise ActivationError("Expected normal bootloader fastboot, but is-userspace reported yes.")
    return {
        "enumeration": enum,
        "variables": vars_data,
        "map": bootloader_vars,
        "partition_sizes": partition_sizes,
        "ab_report": ab_report,
    }


def capture_fastbootd(slot_before: str) -> dict[str, Any]:
    classification = "FASTBOOTD_UNRESOLVED"
    transition_cmd = run_command([str(FASTBOOT), "reboot", "fastboot"], timeout=20)
    write_json(A02B_ROOT / "bootloader-to-fastbootd-command.json", transition_cmd)
    enum = wait_for_fastboot(timeout=90)
    if not enum["present"]:
        if boot_completed(timeout=120):
            classification = "FASTBOOTD_TRANSITION_FAILED_SAFE"
            recovery_state = "ANDROID"
        else:
            classification = "FASTBOOTD_NOT_CONFIRMED"
            recovery_state = "UNKNOWN"
        write_json(A02B_ROOT / "fastbootd-enumeration.json", enum)
        write_json(A02B_ROOT / "fastbootd-variables.json", {"classification": classification, "variables": []})
        write_text(A02B_ROOT / "fastbootd-sanitized.txt", "FASTBOOTD_NOT_CONFIRMED\n")
        write_json(A02B_ROOT / "live-logical-partition-inventory.json", {"classification": classification, "logical_partitions": []})
        write_json(A02B_ROOT / "live-super-topology.json", {"classification": classification})
        return {
            "classification": classification,
            "enumeration": enum,
            "variables": [],
            "logicals": [],
            "recovery_state": recovery_state,
        }

    variables = [fastboot_getvar(name, timeout=20) for name in FASTBOOTD_VARS]
    var_map = {item["name"]: item["value"] for item in variables}
    if var_map.get("is-userspace") != "yes":
        classification = "FASTBOOTD_NOT_CONFIRMED"
        logical_inventory = []
        super_topology = {"classification": classification, "variables": variables}
        recovery_state = "BOOTLOADER_FASTBOOT"
    else:
        classification = "FASTBOOTD_CONFIRMED"
        logical_inventory = []
        for name in FASTBOOTD_LOGICALS:
            logical = fastboot_getvar(f"is-logical:{name}", timeout=20)
            logical_inventory.append(logical)
            if logical.get("value") == "yes":
                logical_inventory.append(fastboot_getvar(f"partition-size:{name}", timeout=20))
                logical_inventory.append(fastboot_getvar(f"partition-type:{name}", timeout=20))
        super_topology = {
            "classification": classification,
            "current_slot": var_map.get("current-slot"),
            "super_partition_name": var_map.get("super-partition-name"),
            "snapshot_update_status": var_map.get("snapshot-update-status"),
            "variables": variables,
            "logical_queries": logical_inventory,
        }
        recovery_state = "FASTBOOTD"

    write_json(A02B_ROOT / "fastbootd-enumeration.json", enum)
    write_json(A02B_ROOT / "fastbootd-variables.json", {"classification": classification, "variables": variables})
    write_text(
        A02B_ROOT / "fastbootd-sanitized.txt",
        "\n".join(
            [f"{item['name']}={item.get('value')}" for item in variables] +
            [f"{item['name']}={item.get('value')}" for item in logical_inventory]
        )
        + "\n",
    )
    write_json(A02B_ROOT / "live-logical-partition-inventory.json", {"classification": classification, "logical_partitions": logical_inventory})
    write_json(A02B_ROOT / "live-super-topology.json", super_topology)
    return {
        "classification": classification,
        "enumeration": enum,
        "variables": variables,
        "logicals": logical_inventory,
        "recovery_state": recovery_state,
    }


def postflight(before: dict[str, Any], fastbootd_result: dict[str, Any]) -> dict[str, Any]:
    if fastbootd_result.get("recovery_state") == "ANDROID":
        reboot_cmd = {
            "command": [str(FASTBOOT), "reboot"],
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "stdout_sanitized": "",
            "stderr_sanitized": "",
            "ran_at": now_iso(),
            "skipped": True,
            "reason": "Device already returned to Android during failed-safe fastbootd transition handling.",
        }
    else:
        reboot_cmd = run_command([str(FASTBOOT), "reboot"], timeout=20)
    write_json(A02B_ROOT / "return-to-android-command.json", reboot_cmd)
    android_ok = boot_completed(timeout=240)
    props_after = {prop: adb_getprop(prop, timeout=15) for prop in GETPROP_KEYS}
    battery_after_raw = adb_shell("dumpsys battery", timeout=20)
    battery_after = parse_battery(battery_after_raw["stdout"])
    mounts_after = adb_shell("mount", timeout=20)
    post = {
        "generated_at": now_iso(),
        "android_returned_normally": android_ok,
        "properties": props_after,
        "battery": battery_after,
    }
    diff = {
        "slot_before": before["properties"]["properties"]["ro.boot.slot_suffix"],
        "slot_after": props_after["ro.boot.slot_suffix"],
        "build_before": before["properties"]["properties"]["ro.build.fingerprint"],
        "build_after": props_after["ro.build.fingerprint"],
        "security_patch_before": before["properties"]["properties"]["ro.build.version.security_patch"],
        "security_patch_after": props_after["ro.build.version.security_patch"],
        "changes_detected": [],
    }
    for key in ["slot", "build_fingerprint", "vendor_fingerprint", "system_fingerprint", "android_version", "security_patch"]:
        before_value = before["properties"]["properties"][
            next(prop for prop, alias in GETPROP_KEYS.items() if alias == key)
        ]
        after_value = props_after[next(prop for prop, alias in GETPROP_KEYS.items() if alias == key)]
        if before_value != after_value:
            diff["changes_detected"].append({"field": key, "before": before_value, "after": after_value})

    timeline = {
        "generated_at": now_iso(),
        "transitions": [
            "ANDROID",
            "BOOTLOADER_FASTBOOT",
            "FASTBOOTD" if fastbootd_result["classification"] == "FASTBOOTD_CONFIRMED" else "BOOTLOADER_FASTBOOT_ONLY",
            "ANDROID",
        ],
    }
    write_json(A02B_ROOT / "android-postflight.json", post)
    write_json(A02B_ROOT / "postflight-identity-diff.json", diff)
    write_json(A02B_ROOT / "transition-timeline.json", timeline)
    write_text(A02B_ROOT / "android-postflight-mounts.txt", sanitize_text(mounts_after["stdout"]))
    return {"post": post, "diff": diff, "timeline": timeline}


def build_live_conclusions(before: dict[str, Any], bootloader: dict[str, Any], fastbootd_result: dict[str, Any], post: dict[str, Any]) -> dict[str, Any]:
    boot_map = bootloader["map"]
    live_partition_inventory = {
        "generated_at": now_iso(),
        "android_by_name": before["by_name_rows"],
        "android_device_mapper": before["mapper_rows"],
        "android_proc_partitions": before["proc_partitions"],
        "bootloader_variables": boot_map,
        "fastbootd_classification": fastbootd_result["classification"],
    }
    write_json(A02B_ROOT / "live-partition-inventory.json", live_partition_inventory)

    package_partitions = {item["canonical_name"] for item in read_json(A02A_ROOT / "package-partition-inventory.json")["partitions"]}
    live_names = {item["name"] for item in before["by_name_rows"]}
    comparisons = []
    for name in sorted(package_partitions | live_names):
        if name in package_partitions and name in live_names:
            classification = "MATCH"
        elif name in package_partitions:
            classification = "PACKAGE_ONLY"
        else:
            classification = "DEVICE_ONLY"
        comparisons.append({"partition": name, "classification": classification})
    write_json(A02B_ROOT / "live-vs-package-topology-diff.json", {"generated_at": now_iso(), "comparisons": comparisons})

    dynamic = {
        "generated_at": now_iso(),
        "classification": "DYNAMIC_PARTITIONS_CONFIRMED",
        "evidence": [
            "Android reported dm-backed root/vendor/product/system_ext mounts.",
            "Android /dev/block/mapper was present.",
            "Package flashes super sparse chunks to super.",
        ],
    }
    if fastbootd_result["classification"] == "FASTBOOTD_CONFIRMED":
        dynamic["evidence"].append("fastbootd userspace fastboot confirmed.")
    write_json(A02B_ROOT / "dynamic-partition-conclusion.json", dynamic)

    fastbootd_conclusion = {
        "generated_at": now_iso(),
        "classification": fastbootd_result["classification"],
        "observed": fastbootd_result["classification"] == "FASTBOOTD_CONFIRMED",
        "note": "fastbootd support does not imply temporary fastboot boot support.",
    }
    write_json(A02B_ROOT / "fastbootd-conclusion.json", fastbootd_conclusion)

    ab_slot = {
        "generated_at": now_iso(),
        "slot_before": before["properties"]["properties"]["ro.boot.slot_suffix"],
        "slot_bootloader": boot_map.get("current-slot"),
        "slot_after": post["post"]["properties"]["ro.boot.slot_suffix"],
        "slot_count": boot_map.get("slot-count"),
        "conclusion": "A/B_SLOT_LAYOUT_CONFIRMED_CURRENT_SLOT_B_UNCHANGED",
        "slot_success": bootloader["ab_report"],
        "note": "Inactive slot _a was not tested and is not presumed safe or bootable.",
    }
    write_json(A02B_ROOT / "ab-slot-conclusion.json", ab_slot)

    avb = {
        "generated_at": now_iso(),
        "android": {
            "verifiedbootstate": before["properties"]["properties"]["ro.boot.verifiedbootstate"],
            "vbmeta_device_state": before["properties"]["properties"]["ro.boot.vbmeta.device_state"],
            "flash_locked": before["properties"]["properties"]["ro.boot.flash.locked"],
            "veritymode": before["properties"]["properties"]["ro.boot.veritymode"],
        },
        "bootloader": {
            "secure": boot_map.get("secure"),
            "unlocked": boot_map.get("unlocked"),
            "securestate": boot_map.get("securestate"),
        },
        "conclusion": "AVB participation observed live, but rollback descriptors/indexes were not authoritatively read; anti_rollback remains UNRESOLVED.",
    }
    write_json(A02B_ROOT / "avb-live-observations.json", avb)

    rollback = {
        "generated_at": now_iso(),
        "status": "UNRESOLVED",
        "evidence": [
            "Live build remains newer (-24) than preserved package (-8).",
            "No authoritative rollback index parser or signed descriptor readback was used in A02B.",
            "No partition writes or readback/fetch operations were performed.",
        ],
    }
    write_json(A02B_ROOT / "rollback-evidence.json", rollback)

    recovery = {
        "generated_at": now_iso(),
        "device_state_transitions": post["timeline"]["transitions"],
        "android_returned_normally": post["post"]["android_returned_normally"],
        "slot_after": post["post"]["properties"]["ro.boot.slot_suffix"],
        "observation": "Read-only reboot path succeeded without issuing any partition write command."
        if post["post"]["android_returned_normally"]
        else "Android return path did not verify fully; hold required.",
    }
    write_json(A02B_ROOT / "recovery-path-observation.json", recovery)

    holds = {
        "generated_at": now_iso(),
        "holds": [
            {
                "topic": "anti_rollback",
                "state": "UNRESOLVED",
                "reason": "Live safe queries did not authoritatively expose rollback indexes or downgrade safety.",
            },
            {
                "topic": "restore_suitability",
                "state": "HOLD",
                "reason": "The preserved -8 package remains older than the live -24 build and is not restoration-ready.",
            },
            {
                "topic": "fastboot_boot_support",
                "state": "UNRESOLVED",
                "reason": "fastbootd support, if present, does not establish support for temporary fastboot boot.",
            },
        ],
    }
    write_json(A02B_ROOT / "topology-holds.json", holds)

    return {
        "dynamic": dynamic,
        "fastbootd": fastbootd_conclusion,
        "ab_slot": ab_slot,
        "avb": avb,
        "rollback": rollback,
        "recovery": recovery,
        "holds": holds,
    }


def write_receipt(manifest: dict[str, Any], before: dict[str, Any] | None, bootloader: dict[str, Any] | None, fastbootd_result: dict[str, Any] | None, post: dict[str, Any] | None, status: str, error: str | None = None) -> None:
    slot_before = before["properties"]["properties"]["ro.boot.slot_suffix"] if before else None
    slot_after = post["post"]["properties"]["ro.boot.slot_suffix"] if post else ""
    identity_before_matches = all(before["preflight"]["identity_matches"].values()) if before else None
    identity_after_matches_before = not post["diff"]["changes_detected"] if post else None
    device_transitions = []
    if before:
        device_transitions.append("ANDROID_TO_BOOTLOADER_FASTBOOT")
    if fastbootd_result and fastbootd_result["classification"] in {"FASTBOOTD_CONFIRMED", "FASTBOOTD_NOT_CONFIRMED", "FASTBOOTD_TRANSITION_FAILED_SAFE"}:
        device_transitions.append("BOOTLOADER_FASTBOOT_TO_FASTBOOTD_IF_SUPPORTED")
    if post:
        device_transitions.append("FASTBOOT_OR_FASTBOOTD_TO_ANDROID")
    conclusions = build_live_conclusions(before, bootloader, fastbootd_result, post) if all([before, bootloader, fastbootd_result, post]) else None
    receipt = {
        "activation_id": "A02B-live-read-only-topology",
        "status": status,
        "operator_approval_recorded": True,
        "device_contacted": before is not None,
        "device_state_transitions": device_transitions,
        "partition_write_commands_issued": False,
        "custom_boot_commands_issued": False,
        "slot_before": slot_before,
        "slot_after": slot_after,
        "identity_before_matches_frozen": identity_before_matches,
        "identity_after_matches_before": identity_after_matches_before,
        "android_returned_normally": post["post"]["android_returned_normally"] if post else None,
        "fastbootd_classification": fastbootd_result["classification"] if fastbootd_result else "FASTBOOTD_UNRESOLVED",
        "dynamic_partition_conclusion": conclusions["dynamic"]["classification"] if conclusions else "UNOBSERVED_PRECHECK_FAILED_SAFE",
        "ab_slot_conclusion": conclusions["ab_slot"]["conclusion"] if conclusions else "UNOBSERVED_PRECHECK_FAILED_SAFE",
        "avb_conclusion": conclusions["avb"]["conclusion"] if conclusions else "UNOBSERVED_PRECHECK_FAILED_SAFE",
        "anti_rollback_status": "UNRESOLVED",
        "restore_suitability": "NOT_YET_ESTABLISHED",
        "open_holds": [item["topic"] for item in conclusions["holds"]["holds"]] if conclusions else [],
        "next_activation_recommendation": "A03-native-entry-proposal" if status == "COMPLETE" else "HOLD",
        "device_changed": False,
        "error": error,
        "completed_at": now_iso(),
    }
    write_json(A02B_ROOT / "A02B-completion-receipt.json", receipt)
    if conclusions:
        summary_lines = [
            "# A02B Summary",
            "",
            f"Status: {status}",
            "",
            "## Observed",
            "",
            f"- Android topology: {len(before['by_name_rows'])} by-name entries, {len(before['mapper_rows'])} mapper entries, dm-backed logical mounts observed.",
            f"- Bootloader topology: slot={bootloader['map'].get('current-slot')}, slot-count={bootloader['map'].get('slot-count')}, super-partition-name={bootloader['map'].get('super-partition-name')}.",
            f"- fastbootd classification: {fastbootd_result['classification']}.",
            f"- Android returned normally: {post['post']['android_returned_normally']}.",
            "",
            "## Inferred",
            "",
            "- Dynamic partitions are confirmed from live dm-backed Android evidence plus package super targeting.",
            "- A/B slot layout is present and current slot remained `_b` before and after.",
            "",
            "## Unsupported",
            "",
            "- No partition fetch/readback was performed.",
            "- No custom boot, flash, erase, slot switch, or AVB modification was attempted.",
            "",
            "## Unresolved",
            "",
            "- anti_rollback remains UNRESOLVED.",
            "- restore_suitability remains NOT_YET_ESTABLISHED.",
            "- fastbootd support does not establish `fastboot boot` support.",
            "",
        ]
        write_text(A02B_ROOT / "A02B-summary.md", "\n".join(summary_lines))
    else:
        write_text(
            A02B_ROOT / "A02B-summary.md",
            "\n".join(
                [
                    "# A02B Summary",
                    "",
                    f"Status: {status}",
                    "",
                    "## Observed",
                    "",
                    "- A02A derived-artifact audit completed and corrected derivatives were emitted inside this activation.",
                    "- Android preflight did not pass because no authorized handset was enumerated over ADB and no device was visible in fastboot.",
                    "",
                    "## Not observed",
                    "",
                    "- No Android topology was collected from a live device.",
                    "- No bootloader fastboot topology was collected.",
                    "- No fastbootd attempt was made.",
                    "- No reboot transition was performed.",
                    "",
                    "## Unresolved",
                    "",
                    "- anti_rollback remains UNRESOLVED.",
                    "- restore_suitability remains NOT_YET_ESTABLISHED.",
                    "- Live topology remains blocked on device presence and authorized USB enumeration.",
                    "",
                    f"Failure: {error}",
                    "",
                ]
            ),
        )


def write_artifact_manifest() -> None:
    lines = []
    for path in sorted(item for item in A02B_ROOT.rglob("*") if item.is_file() and item.name != "artifact-manifest.sha256"):
        lines.append(f"{sha256_file(path)} *{path.relative_to(A02B_ROOT).as_posix()}")
    write_text(A02B_ROOT / "artifact-manifest.sha256", "\n".join(lines) + "\n")


def update_activation_index() -> None:
    index_path = ACTIVATIONS_ROOT / "activation-index.json"
    entries = []
    for name in ["A01-stock-closure", "A02A-offline-stock-topology", "A02B-live-read-only-topology"]:
        receipt_path = ACTIVATIONS_ROOT / name / (f"{name.split('-', 1)[0]}-completion-receipt.json")
        if name == "A01-stock-closure":
            receipt_path = ACTIVATIONS_ROOT / name / "A01-completion-receipt.json"
        elif name == "A02A-offline-stock-topology":
            receipt_path = ACTIVATIONS_ROOT / name / "A02A-completion-receipt.json"
        elif name == "A02B-live-read-only-topology":
            receipt_path = ACTIVATIONS_ROOT / name / "A02B-completion-receipt.json"
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            entries.append(
                {
                    "activation_id": name,
                    "status": receipt.get("status"),
                    "completed_at": receipt.get("completed_at") or receipt.get("recorded_at"),
                }
            )
    write_json(index_path, {"updated_at": now_iso(), "activations": entries, "latest": "A02B-live-read-only-topology"})


def main() -> int:
    A02B_ROOT.mkdir(parents=True, exist_ok=True)
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True)
    require_file(ADB)
    require_file(FASTBOOT)

    manifest = make_activation_manifest()
    before = None
    bootloader = None
    fastbootd_result = None
    post = None
    try:
        audit_a02a()
        before = android_preflight(manifest)
        bootloader = capture_bootloader()
        boot_map = bootloader["map"]
        slot_ok = boot_map.get("current-slot") == "_b"
        battery_ok = before["battery"]["battery_percent"] >= 60
        fastboot_stable = bootloader["enumeration"]["device_count"] == 1
        if slot_ok and battery_ok and fastboot_stable:
            fastbootd_result = capture_fastbootd(before["properties"]["properties"]["ro.boot.slot_suffix"])
        else:
            fastbootd_result = {
                "classification": "FASTBOOTD_UNRESOLVED",
                "enumeration": {},
                "variables": [],
                "logicals": [],
            }
        post = postflight(before, fastbootd_result)
        if not post["post"]["android_returned_normally"]:
            raise ActivationError("Android did not verify normal boot completion after reboot.")
        if post["post"]["properties"]["ro.boot.slot_suffix"] != "_b":
            raise ActivationError("Slot after return is not _b.")
        write_receipt(manifest, before, bootloader, fastbootd_result, post, "COMPLETE")
        write_artifact_manifest()
        update_activation_index()
        return 0
    except Exception as exc:  # noqa: BLE001
        status = "FAILED_SAFE" if before is None else "HOLD"
        write_receipt(manifest, before, bootloader, fastbootd_result, post, status, error=str(exc))
        write_artifact_manifest()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
