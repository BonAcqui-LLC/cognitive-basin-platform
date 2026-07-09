# AIA Sovereign Activation Device

Private repository for the first verified stock-Android AIA vertical slice on Motorola hardware.

This repo now reflects the combined authority of `AIA Large portion of text could not be pasted v1.0.txt` and the superseding correction in `AIA Large portion of text could not be pasted v1.1.txt`. The v1.1 continuation corrected the device identity to the LTE Moto G Stylus (2023) family and required persistent device identifiers to remain only in gitignored raw receipts.

## Current state

- stock Android app under [android](/C:/Users/moop/Documents/AIA/android) builds as `llc.bonacqui.aia` version `0.1.1-stockos`
- debug APK has been built, replace-installed, cold-launched, and package-verified on the audited handset
- deterministic governed activation paths for `SUPPORTED / EXTEND`, `UNRESOLVED / HOLD`, and `CONTRADICTED / RETRACT` are exercised on-device
- local session persistence, portable export, export re-import verification, and tamper detection are working on hardware
- repository evidence, threat posture, and acceptance status are recorded under [docs](/C:/Users/moop/Documents/AIA/docs), [reports](/C:/Users/moop/Documents/AIA/reports), and [receipts](/C:/Users/moop/Documents/AIA/receipts)

## Verified handset facts

- product model: `moto g stylus (2023)`
- retail SKU: `XT2317-2`
- device / product: `gnevan` / `gnevan_g`
- classification: LTE Moto G Stylus (2023), MediaTek, not `genevn` and not the 5G sibling
- Android version: `14` (`sdk 34`, first API level `33`)
- build id: `U1THS34.65-74-1-7-22`
- hardware: `mt6768`
- ABI: `arm64-v8a`
- display: `720x1600`
- verified boot state: `green`
- bootloader state: `flash_locked=1`
- vbmeta state: `locked`
- active slot: `_a`

## Implemented vertical slice

- source receipt ledger under [receipts/source_receipts.json](/C:/Users/moop/Documents/AIA/receipts/source_receipts.json) and [docs/source_receipts.md](/C:/Users/moop/Documents/AIA/docs/source_receipts.md)
- raw gitignored device audit captured by [tools/device_audit.ps1](/C:/Users/moop/Documents/AIA/tools/device_audit.ps1)
- package identity decision in [docs/adrs/ADR-package-identity.md](/C:/Users/moop/Documents/AIA/docs/adrs/ADR-package-identity.md)
- Cognitive Basin mobile mapping in [docs/cognitive_basin_mobile_mapping.md](/C:/Users/moop/Documents/AIA/docs/cognitive_basin_mobile_mapping.md)
- stock acceptance evidence in [reports/stock_apk_acceptance.md](/C:/Users/moop/Documents/AIA/reports/stock_apk_acceptance.md)
- custom-OS destructive posture remains blocked in [reports/custom_os_go_no_go.md](/C:/Users/moop/Documents/AIA/reports/custom_os_go_no_go.md)

## Boundaries

- no bootloader unlock, root, flashing, factory reset, partition edits, or recovery installation were performed
- no Google Play Services, Firebase, analytics SDK, advertising SDK, or tracking SDK were added
- no `INTERNET` permission is requested by the current APK
- persistent device identifiers are intentionally redacted from tracked docs and remain only in gitignored raw receipts

## Next focus

1. Tighten the first-screen mobile ergonomics so fewer controls sit below the fold.
2. Expand golden traces and compare them directly against selected `cognitive-basin-platform` fixtures.
3. Add the user-started microphone boundary only after the current typed vertical slice remains stable.
4. Re-run disruptive acceptance steps such as airplane-mode and full reboot verification only when operator timing permits.
