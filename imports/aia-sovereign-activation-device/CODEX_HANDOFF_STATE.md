# Codex Handoff State

Date: 2026-06-17

## Repository state

- repo path: `C:\Users\moop\Documents\AIA`
- branch: `master`
- commits: none yet
- worktree: intentionally dirty because this is the first authored tranche

## Verified build and install state

- current package: `llc.bonacqui.aia`
- current version: `0.1.1-stockos`
- current APK hash: `39531CC09BA4CE51E0AEDEA9FC3375F3E555AAE0D7303DC358C140E138D6020A`
- replace-install succeeded over verified `adb.exe`
- cold launch after force-stop succeeded on the connected handset

## Device identity

- exact measured SKU: `XT2317-2`
- handset family used here: LTE Moto G Stylus (2023)
- `gnevan` is correct for this repo
- `genevn` is the distinct 5G sibling and should not be mixed into ROM or source assumptions

## Important boundaries

- tracked docs must stay redacted for serial and similar persistent identifiers
- raw serial remains only in gitignored `receipts/device_audit.json`
- destructive custom-OS operations remain `NO-GO`
- audio remains deferred

## Practical next move

Use [NEXT_ACTION.md](/C:/Users/moop/Documents/AIA/NEXT_ACTION.md) as the entry point for the next tranche.
