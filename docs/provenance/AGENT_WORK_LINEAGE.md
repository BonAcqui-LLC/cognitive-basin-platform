# Agent Work Lineage

This branch preserves externally produced project work in a way that keeps provenance visible and keeps the existing Cognitive Basin platform history intact.

## Destination

- Repository: `BonAcqui-LLC/cognitive-basin-platform`
- Verified clone root: `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\cognitive-basin-platform-import-2026-06`
- Integration branch: `integration/agent-work-handoff-2026-06`
- Verified upstream baseline: `origin/main` at `998364174143df69deb2cbae049d9f9de1886dce`

## Imported Or Preserved Sources

### AutoClaw / Z.ai

- Primary source repository: `C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE`
- Source branch: `main`
- Source HEAD: `ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9`
- Preserved frozen reference tag target: `natural-math-v5-reference-1.0` -> `28ffa5974b5fd157982f36fdb1189ac9d1fb6acb`
- Verified frozen Natural Math source hash: `E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B`
- Import treatment: history-preserving subtree under `imports/autoclaw-natural-math-workspace/`
- Distinguishing rule: imported AutoClaw history remains under an import prefix and is not silently presented as the active platform runtime
- External provenance bundle: `C:\_MASTER_LIBRARY_Handoff\autoclaw_workspace_handoff.zip`
- External provenance ZIP SHA256: `758F59126E14743ADEEF9DC0097043F891AA239774DF185C950D03FA7688198C`
- Additional Z.ai historical artifacts: `z.ai.nm-ai-prompt.txt`, `Z.ai AutoClaw Library Curation.docx`

### Grok

- Concrete import source: `C:\Users\moop\Downloads\Grok\intake-deploy`
- Selected implementation artifacts: `worker.js`, `wrangler.toml`
- Selected historical evidence source: `C:\Users\moop\FractalishBuild\fractalish-ai`
- Import treatment: concrete worker under `imports/grok-guardian-intake/`; selected evidence under `evidence/grok/fractalish-ai/`
- Non-import rule: do not blindly ingest the full `fractalish-ai` snapshot because it overlaps current platform areas and lacks a clean local Git lineage

### Kimi

- Selected evidence sources:
  - `C:\Users\moop\Downloads\Articles on X.com\Kimi SGTM Research report.md`
  - `C:\Users\moop\Downloads\Articles on X.com\Natural Math\Kimi_Orientation.txt`
  - `C:\Users\moop\Downloads\Articles on X.com\F R A C T A L I S H - - - A I - - - FRACTALISH-AI\Kimi_Signal_Jamming_Morphology_Hypothesis.csv`
- Import treatment: preserve as historical evidence under `evidence/kimi/`
- Finding boundary: no Kimi code baseline was identified for this tranche

## Deferred Or Excluded Sources

- AIA repository: deferred as `CONFLICT - REVIEW REQUIRED`
- `ALL_TOKENS_KEYS_FOR_GROK.txt`: excluded as secret
- Z.ai account PDFs and local OpenClaw runtime/config state: excluded as personal or generated local state
- Local Kimi webbridge executable: excluded as unrelated installation tooling
- AutoClaw handoff ZIP contents: not duplicated into normal Git history when preserved Git history and handoff documents already cover the same material

## Source Integrity Notes

- The AutoClaw source repository currently has local modified generated files in `05_RESULTS/extension_harness/*` and `06_REPORTS/stage_2_performance_report.md`
- This branch preserves the committed AutoClaw lineage only; it does not absorb those live uncommitted deltas
- Repository-level validation must therefore report both:
  - the preserved commit lineage; and
  - the fact that the live source worktree contains additional uncommitted generated artifacts outside the imported history
