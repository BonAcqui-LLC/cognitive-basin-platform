# Cognitive Basin Mobile Mapping

Date: 2026-06-17

## Scope

This note records how the current Android runtime maps the canonical Cognitive Basin ternary contract onto the first stock-device Kotlin implementation.

## Canonical internal states preserved

- epistemic: `SUPPORTED`, `UNRESOLVED`, `CONTRADICTED`
- action: `EXTEND`, `HOLD`, `RETRACT`

The Android app preserves those names internally in [AiaRuntime.kt](/C:/Users/moop/Documents/AIA/android/app/src/main/java/ai/fractalish/aia/runtime/AiaRuntime.kt) and does not replace them with informal equivalents.

## Mobile runtime mapping

- purpose text enters `classifyActivation`
- bounded requested capabilities are attached by activation type
- `guardianPass` may inject forced-HOLD findings before final resolution
- deterministic evidence, missing evidence, and contradictory evidence drive the governed result
- contradiction scars and recovery routes are persisted as part of the session record

## Current activation coverage

- `AIA_DEMO_GUIDANCE`
- `AIA_CIVIL_RIGHTS_SESSION`
- `BASINLAB_DIAGNOSTIC`
- `DEVICE_INTEGRITY_REVIEW`

## Golden traces in this repo

Tracked deterministic traces live under [tests/golden-traces](/C:/Users/moop/Documents/AIA/tests/golden-traces):

- `supported_trace.json`
- `hold_trace.json`
- `contradiction_trace.json`
- `device_review_trace.json`

These traces intentionally mirror the three governed outcomes already verified on hardware plus the device-review path.

## Current conformance judgment

The current Android implementation is structurally aligned with the platform canon in the following ways:

- ternary epistemic and action states are preserved
- HOLD is a first-class result, not an error branch
- contradiction produces a preserved scar and recovery route
- export and replay preserve governed end state and supporting evidence

Known differences still to close:

- no direct fixture import pipeline from `cognitive-basin-platform` yet
- no automated differential test runner yet
- Android runtime currently derives traces from local deterministic scenarios rather than an exported canonical fixture pack
