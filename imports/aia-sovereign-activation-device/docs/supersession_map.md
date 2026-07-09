# Supersession Map

## Directive authority

- active authority chain:
  - `AIA Large portion of text could not be pasted v1.0.txt`
  - `AIA Large portion of text could not be pasted v1.1.txt`
- v1.0 remains the foundation for the repository
- v1.1 supersedes earlier assumptions about device identity, explicitly distinguishes `gnevan` from `genevn`, and moves persistent identifiers into gitignored raw receipts only
- no later AIA supersession directive has been applied in this repository beyond v1.1

## Implementation authority

- current implementation canon for governed local behavior: `C:\Users\moop\cognitive-basin-platform`
- strongest build authorities within that repo:
  - `python/ephux_local/service.py`
  - `apps/ephux-local-ui/index.html`
  - `ops/manifests/capability-registry.json`
  - `ops/manifests/security-controls.json`
- rationale: these sources describe and implement the actual verified local BasinLab/EphUX/Guardian behavior already present today

## Dated status reports

- `docs/CURRENT_STATE.md` is authoritative as a dated report of what had been verified by 2026-06-17
- it does not supersede direct live observations such as the currently observed local `HEAD`
- where report text and live repo state differ, this repo records both and prefers explicit file receipts over assumption

## Conceptual versus build-driving material

Use as conceptual references only:

- `Cognitive_Basin_Thesis_v0_1.md`
- `Affective Telemetry & Arbitration Layer_Entire_Chat.txt`
- `SERA Viral Sentinel + Glyph Monitoring Spec (v0.2).txt`
- `Updated OS Kernel v3.1 (with Glyph + Viral Integration).txt`

Do not use those files alone to claim:

- a verified Android implementation
- a verified handset benchmark
- a verified AOSP port
- a safe destructive device procedure

## Legacy versus current EphUX implementation

- `evidence/legacy/` inside `cognitive-basin-platform` remains useful provenance
- current build authority for a stock-device demo should come from `python/ephux_local/service.py` and `apps/ephux-local-ui/`, not from legacy worker snippets

## Device-identity correction

- `gnevan` and `gnevan_g` map to the LTE Moto G Stylus (2023) on the measured handset
- `genevn` refers to the distinct Moto G Stylus 5G (2023) line and must not be used for ROM, kernel, or recovery assumptions here
- already captured evidence is preserved as-is; corrections are recorded through superseding documentation rather than renamed artifacts
