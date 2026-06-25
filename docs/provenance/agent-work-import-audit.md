# Agent Work Import Audit

This inventory covers the verified AutoClaw workspace and handoff bundle, selected Z.ai planning artifacts, the Grok intake worker, selected Grok Build evidence artifacts, selected Kimi research artifacts, the inspected-but-deferred AIA workspace, and the separately recorded empty Kimi workspace directory.

## Decision Summary

- **CONFLICT - REVIEW REQUIRED:** 2
- **EXCLUDE - GENERATED CACHE:** 1
- **EXCLUDE - PERSONAL:** 3
- **EXCLUDE - SECRET:** 1
- **EXCLUDE - UNRELATED:** 1
- **HISTORICAL EVIDENCE:** 17
- **IMPORT:** 151
- **SOURCE NOT FOUND:** 1

## Key Findings

- AutoClaw is the only candidate source with a verified standalone Git lineage ready for history-preserving import.
- The external AutoClaw handoff bundle should be preserved as provenance, but the zip archive itself should stay out of normal Git history.
- The Grok intake worker is a small concrete implementation that is absent from the destination repo and safe to import after cache/secret exclusion.
- Z.ai contributed planning and curation artifacts plus the verified AutoClaw workspace; local account/config/runtime files are excluded.
- Kimi contributed project-relevant research and orientation documents, but no Kimi code baseline was located.
- The larger `fractalish-ai` snapshot appears historically valuable but overlaps with the existing platform; this tranche imports only selected evidence/report artifacts and records the rest as conflict-review.
- The AIA Android/device repo is project-relevant but not clearly attributable to the requested agent set, so it is deferred rather than silently mixed into this agent-work import.
