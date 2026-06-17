# Current State

Verified baseline date: 2026-06-17

Canonical repository:
`C:\Users\moop\cognitive-basin-platform`

Intentional worktrees:
- `C:\Users\moop\cognitive-basin-platform` on `main`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\basinlab-persistence-memory-codex`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-local-integration-codex`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-product-surface-codex`

Repository identity:
- remote `main`: `114a2c1f84296c3d0db009b6f984ee9e49d2695d`
- canonical local `main`: fast-forwarded to `114a2c1f84296c3d0db009b6f984ee9e49d2695d`
- verified main CI: run `27713166589`, workflow `ci-non-deploying`, conclusion `success`
- secondary EphUX path is a real Git worktree sharing `C:\Users\moop\cognitive-basin-platform\.git`

Local verification:
- repository tests: `112 passed`
- EphUX acceptance: `12/12` scenarios passed
- required API routes: all present and probed successfully
- package layout: canonical implementation under `python/...`, top-level wrappers retained as thin compatibility shims
- browser verification: local shell opened in the in-app browser, created a persisted session, and passed a mobile-width reload check

Verified local product surfaces:
- loopback-only EphUX HTTP service
- local Guardian Intake
- local Activation flow
- installable PWA shell without embedded token secrets
- persisted session list and reopen flow
- portable session export/import with hash validation and overwrite protection
- human review event controls with provenance capture
- persisted BasinLab session backend
- governed commit denial path
- HTML report generation
- development browser extension scaffold

Audit artifacts for `114a2c1f84296c3d0db009b6f984ee9e49d2695d`:
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\phase0-main-audit-114a2c1\cognitive-basin-platform-114a2c1-source.zip`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\phase0-main-audit-114a2c1\cognitive-basin-platform-full.bundle`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\phase0-main-audit-114a2c1\ephux-acceptance\ephux-local-acceptance-summary.json`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\phase0-main-audit-114a2c1\endpoint-inventory.json`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\phase0-main-audit-114a2c1\main-ci-runs.json`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\phase0-main-audit-114a2c1\capability-registry-114a2c1.json`
