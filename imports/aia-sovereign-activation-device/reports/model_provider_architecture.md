# Model Provider Architecture

Date: 2026-06-17

## Current provider posture

- shipped provider identity: `deterministic_fixture_provider`
- external provider state: disabled
- governing runtime: local deterministic Kotlin logic

## Boundaries

A provider may propose:

- activation type
- structured claims
- classification hints
- plain-language explanation

A provider may not decide:

- final governed state
- permissions
- export authorization
- evidence retention
- external actions
- legal authority
- system settings

## Current safety posture

- no `INTERNET` permission in the APK
- no API keys in the app
- no filesystem or shell authority exposed to a provider interface
- app remains fully demonstrable with no model provider available
