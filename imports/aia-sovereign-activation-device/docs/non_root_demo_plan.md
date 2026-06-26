# Non-Root Demo Plan

## Goal

Reach the first truthful Motorola stock-OS demonstration before any custom-ROM work.

## Phase A: Tooling unblock

Status: complete

1. Android platform tools are present and verified at `C:\Android\android-sdk\platform-tools\adb.exe`.
2. The Motorola handset is connected with USB debugging enabled.
3. `tools/device_audit.ps1` produced the raw gitignored JSON receipt.

Exit criterion:
exact model, build fingerprint, lock state, storage, RAM, and unlock-related properties are recorded.

## Phase B: Android shell build

Status: complete

1. SDK components were verified locally.
2. Build tooling was stabilized with Gradle 8.7 and a workspace-local JDK 17.
3. The debug APK now builds successfully.

Exit criterion:
debug APK exists and can be reopened locally.

## Phase C: Stock-device install

Status: complete

1. The debug APK was installed with `adb install -r`.
2. The app was relaunched after install and again after force-stop.
3. Package, version, permissions, launch timing, memory, UI hierarchy, persistence, export, and tamper evidence were captured.
4. The launcher now renders real governed states rather than only placeholder anchors.

Exit criterion:
the app runs on stock firmware without root or bootloader changes.

## Phase D: Activation-runtime bridge

Status: partial, first tranche complete

1. The current bridge is a deterministic local Kotlin runtime with a bounded provider interface.
2. The app preserves canonical ternary states internally and exposes explicit recovery routes.
3. Direct fixture parity with `cognitive-basin-platform` still needs to grow.

Exit criterion:
the demo can process a bounded activation request and return a guarded state without overclaiming legal or device authority.

## Phase E: Benchmark and receipts

Collect:

- startup latency
- memory pressure
- thermal behavior during repeated use
- battery impact during short demo sessions
- feasibility notes for transcription and compact local-model inference

Exit criterion:
a benchmark note exists with measured values or explicit blocked reasons.

Status: partial

The repo now contains initial latency, memory, storage, thermal, battery, and export-size evidence. Audio and local-model feasibility remain intentionally deferred.

## Hard stop

Do not proceed to bootloader unlock, flashing, root, or partition edits until:

- the device audit exists
- the stock-device demo is verified
- the benchmark note exists
- the custom-OS go/no-go report is revisited with fresh evidence
