# Current State

Verified baseline date: 2026-06-17

Canonical repository:
`C:\Users\moop\cognitive-basin-platform`

Intentional worktrees:
- `C:\Users\moop\cognitive-basin-platform` on `main`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\basinlab-persistence-memory-codex`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-local-integration-codex`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-product-surface-codex`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\provider-sandbox-codex`

Repository identity:
- remote `main`: `ab8714eb0120859a1c5d30f0e2f1a197da76aca8`
- canonical local `main`: fast-forwarded to `ab8714eb0120859a1c5d30f0e2f1a197da76aca8`
- verified product-surface main CI: run `27717532798`, workflow `ci-non-deploying`, conclusion `success`
- secondary EphUX path is a real Git worktree sharing `C:\Users\moop\cognitive-basin-platform\.git`

Local verification:
- repository tests: `118 passed`
- EphUX acceptance: `12/12` scenarios passed
- ProviderLab acceptance: `7/7` scenarios passed
- SandboxLab acceptance: `19/19` scenarios passed
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
- governed provider router with auditable usage ledger
- secret-safe provider and local-model inventory
- bounded compact-reasoner packet flow
- runner receipts with explicit `ENFORCED` / `BEST_EFFORT` / `UNSUPPORTED` control classification
- adversarial sandbox acceptance matrix

Audit artifacts for product-surface merge commit `ab8714eb0120859a1c5d30f0e2f1a197da76aca8`:
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-product-main-audit-ab8714e\cognitive-basin-platform-ab8714e-source.zip`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-product-main-audit-ab8714e\cognitive-basin-platform-full.bundle`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-product-main-audit-ab8714e\ephux-product-acceptance-package.zip`
- `C:\Users\moop\Downloads\Articles on X.com\Fractalish.com\build\ephux-product-main-audit-ab8714e\ephux-local-pwa-dev-package.zip`
