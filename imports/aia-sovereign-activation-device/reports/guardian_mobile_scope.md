# Guardian Mobile Scope

Date: 2026-06-17

## Implemented Guardian checks

- absent jurisdiction for civil-rights demo paths
- unsupported certainty
- external action request
- capability expansion request such as unlock, root, or flash
- unsupported completion claim
- malformed activation manifest
- demonstration-rule-pack warning

## Current behavior

- Guardian findings are persisted with the session
- forced-HOLD findings contribute to missing-evidence handling when no direct contradiction exists
- Guardian content is included in exported session packages

## Still missing

- stale-rule-pack invalidation against a signed authoritative corpus
- model-output provenance checks against a real provider call path
- capability-escalation enforcement across future microphone and provider adapters
