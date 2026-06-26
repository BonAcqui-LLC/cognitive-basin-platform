# Stock APK Vertical Slice Plan

Date: 2026-06-17

## Objective

Deliver a truthful stock-Android AIA slice that builds, installs, reopens, governs bounded activations, persists sessions locally, exports verifiable session packages, and avoids destructive device operations.

## Completed

- audited the connected Motorola handset and corrected the device family to LTE `gnevan`
- stabilized build tooling with Android SDK components, Gradle 8.7, and JDK 17
- built `llc.bonacqui.aia` debug APK
- replace-installed the APK over ADB and cold-launched it after force-stop
- exercised supported, HOLD, contradiction, persistence, export, import, and tamper paths on-device
- recorded receipts, mappings, redaction rules, and destructive-stage `NO-GO`

## Remaining tranche work

1. tighten first-screen ergonomics on the 720x1600 device
2. expand golden traces and compare directly with selected platform fixtures
3. add an explicit microphone boundary without storing raw audio
4. run operator-approved disruptive acceptance such as airplane-mode and full reboot persistence

## Non-goals for this tranche

- custom-ROM work
- bootloader unlock
- root
- background microphone
- mandatory remote provider integration
