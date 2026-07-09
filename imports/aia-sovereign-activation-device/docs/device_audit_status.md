# Device Audit Status

Status date: 2026-06-17

## Current result

Device audit completed successfully, and the later stock-APK tranche confirmed the exact handset class needed for the repo.

## Evidence gathered

- `adb.exe` verified at `C:\Android\android-sdk\platform-tools\adb.exe`
- connected handset observed by `adb devices -l` with product `gnevan_g`, device `gnevan`, and model token `moto_g_stylus__2023_`
- raw JSON receipt written to gitignored `C:\Users\moop\Documents\AIA\receipts\device_audit.json`
- superseding v1.1 directive required the LTE / 5G correction and redaction of persistent identifiers from tracked artifacts

## Key findings

- exact retail SKU: `XT2317-2`
- product model: `moto g stylus (2023)`
- product class: LTE Moto G Stylus (2023), not the Qualcomm `genevn` 5G sibling
- Android release: `14`
- SDK level: `34`
- first API level: `33`
- build fingerprint: `motorola/gnevan_g/gnevan:14/U1THS34.65-74-1-7-22/cfc16b-d0a3d:user/release-keys`
- build id: `U1THS34.65-74-1-7-22`
- manufacturer / brand: `motorola`
- hardware platform: `mt6768`
- ABI: `arm64-v8a`
- reported carrier channel: `retus`
- bootloader string: `MBM-2.1-gnevan_g-5ba36-U1THS34.65-74-1-7-22-cfc16b`
- lock state: `flash_locked=1`
- verified boot state: `green`
- vbmeta state: `locked`
- active slot suffix: `_a`
- physical display size: `720x1600`
- observed memory total: `3829792 kB`

## Remaining unknowns

- explicit `ro.oem_unlock_supported` value, which was not populated in the receipt
- full partition inventory and super-partition mapping
- realistic compact local-model ceiling once deterministic-only measurements are extended

## Redaction note

Tracked docs in this repository intentionally omit the device serial and similar persistent identifiers. Those values remain only in gitignored raw receipts.

## Prepared next step

The next technical milestone is no longer build-and-reopen verification. That milestone has passed. The remaining work is refinement:

1. widen the golden-trace comparison against `cognitive-basin-platform`
2. improve first-screen ergonomics on the handset
3. add the explicit microphone boundary without making audio a hidden dependency
