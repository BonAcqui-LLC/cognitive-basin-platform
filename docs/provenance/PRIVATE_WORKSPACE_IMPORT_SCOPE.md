# Private Workspace Import Scope

This tranche extends the existing imported-work branch so the private `cognitive-basin-platform` repository represents the missing CNTM, AIA, and Motorola activation lines without collapsing their claim boundaries.

## Imported

- `imports/aia-sovereign-activation-device/`
  - structural snapshot of the accepted stock-Android AIA workspace
  - includes Android source, docs, reports, tests, tools, and safe receipts
- `imports/cntm-natural-math-canonical-library/`
  - curated snapshot of the CNTM/Natural Math canonical library
  - includes governance, core Natural Math, CNTM, Morphological Coding, Cognitive Basin, SymLan, and frozen-test materials
- `evidence/motorola-activation/`
  - read-only Motorola activation evidence
  - includes A01, A02A, A02B artifacts, the frozen unlocked baseline, sanitized evidence, hardware reports, manifests, and selected safe stock-identity files

## Excluded

- AIA raw device identifiers and generated mobile evidence
  - `receipts/device_audit.json`
  - `receipts/raw/`
  - `artifacts/`
  - Android build output and local SDK properties
- CNTM duplicate/version/archive buckets and local private provenance
  - `90_CANDIDATE_VERSIONS/`
  - `91_DUPLICATES/`
  - `92_CONFLICTING_VERSIONS/`
  - `99_ARCHIVES/`
  - `manifests/local_provenance_private.json`
  - `10_TESTS_AND_FROZEN_RESULTS/archive.zip`
  - `CNTM_Natural_Math_Canonical_Library.zip`
- Motorola firmware and private receipts
  - stock package zip under `device/motorola/gnevan/stock/original/`
  - extracted partition images under `device/motorola/gnevan/stock/extracted/`
  - A02B private preflight receipt bucket
  - Python bytecode caches

## Interpretation Boundaries

- AIA is imported as a structural snapshot because the source workspace has no committed Git history yet.
- CNTM is imported as curated provenance and reference material, not as authoritative active runtime code for the platform.
- A small number of CNTM destination filenames are shortened for Windows/Git path compatibility.
  - provenance remains in the inventory via source-path to proposed-destination mapping
- Motorola activation evidence remains read-only provenance.
  - imported A02B status is `FAILED_SAFE`
  - `anti_rollback` remains `UNRESOLVED`
  - `restore_suitability` remains `NOT_YET_ESTABLISHED`
- Existing public-release guidance remains provenance only; this tranche is for the private platform repository.
