# CURRENT_STATE.md
# Fresh evidence-based recovery session — 2026-06-16
# Milestone: M0 — Evidence acquisition and live audit

**Status classification rules (per directive):** Use only DISCOVERED, SPECIFIED, IMPLEMENTED, PARSED, COMPILED, UNIT TESTED, ... PARTIAL, STUB, BLOCKED, DEFERRED, NOT BUILT. Never use vague "complete".

## Session
- Date: 2026-06-16
- Recovery root: C:\Users\moop\Cognitive-Basin-Recovery-2026-06-16
- Machine: DESKTOP-8GIRJ9B (Windows 10/11 PowerShell)
- Shell: PowerShell 5.1
- This is a **completely new engineering iteration**. Prior Grok Build conversation drift assumed. Prior completion reports, manifests, and backups are treated as untrusted evidence only.
- Full project scope retained: Cognitive Basin / Fractalish (PERCEPT → ATAL → RIGOR → CIRCUIT → GUARD → SERA), EphUX, Activation Kernel, Guardian Intake, Natural Math, Synaptient, BasinLab, etc. No scope reduction for cost.
- Production systems (Cloudflare routes, DNS, secrets, KV data, custom domains) **will not be altered** without explicit approval.

## Observed Local Structure (M0 partial)
- Recovery dirs created: evidence/, manifests/, logs/, canon/, repositories/, quarantine/, ops/manifests/, docs/
- Git repo initialized (empty, .gitignore committed baseline next)
- .gitignore created prior to any project source ingestion (excludes credentials, large binaries, personal dirs, prior EphUX rebuild dirs, node_modules, .wrangler, env files, etc.)
- Canonical library root created: C:\Users\moop\Cognitive-Basin-Canonical-Library (per directive)

## Live Cloudflare Read-Only Audit (M0 complete for core)
- workers_list: 25+ workers. Relevant: ephux (id 36bb88d1579f4890abc71b7b941acb9a, mod 2026-05-18), ephux-activation-kernel (id 1158d88092364f77ae979ffefc0c480f, mod 2026-06-15), ephux-guardian-intake (id eac17b42ad3345b6a8b2f3679c52a585, mod 2026-06-15).
- workers_get_worker_code: full source retrieved for all three (written to evidence/live-deployed-2026-06-16/*.js and hashed locally).
  - ephux: static www redirect + ASSETS fetch for pages (905 bytes, matches hypothesis).
  - ephux-activation-kernel: Activation Doctrine (purpose anchoring, path integrity with Supported/Unsupported/Indeterminate + integrity_classification, structured continuity, pruning, uncertainty), pre-filter high-risk signals (ignore previous, exfil, jailbreak, tool poisoning), KV log to INTAKE_KV (7d), strict JSON output enforcement + Indeterminate fallback, PWDither dither_spec sketch, receptor_event_suggestions. Uses @cf/meta/llama-3.2-3b-instruct. AI + controller.
  - ephux-guardian-intake: /intake (token + receptorEvent with basic "possible prompt injection" flag, "sanitized_content" placeholder + note "full sanitization + R2 in prod"), one-time /view/{token} consume+display, email handler. KV one-time. Comment: "Original raw content never reached any AI".
- kv_namespaces_list: GUARDIAN_INTAKE_KV (id b777366e906f424ba033590cbddf3f08 — exact hypothesis match) + SYNAPTIENT_REGISTRY, WB_SUBSCRIBERS, ENTRO_SUBSCRIBERS.
- r2_buckets_list: 403 "Please enable R2 through the Cloudflare Dashboard" — R2 not enabled (confirmed, no paid product activated).
- workers_get_worker: metadata confirmed for the three (no production routes/DNS/KV data mutated).
- No production changes. All staging/isolated if ever needed in future.
- Hypothesis from section 8 largely matched on names/IDs/sizes for core items; implementation details (pre-filter, ternary in output, doctrine text) observed live.

## Key Local Artifacts (M0 discovery + classification)
- ephux-next/: substantial tree (baseline-immutable with extension + workers + handoff docs + whitepaper, basin-lab/ Python, release/, stabilization/ copies, reports/). Not a small extension — contains architecture source.
- basin-lab/core/contracts.py + controller.py (CANONICAL): Pure Python stdlib. EpistemicState (SUPPORTED / UNRESOLVED / CONTRADICTED), ActionState (RETRACT / HOLD / EXTEND — explicit ternary action with HOLD consuming budget + recording ignored, RETRACT creating FailureScar), BasinState, ClaimRecord, ArtifactManifest, RegionRecord, BasinController implementing start_activation(purpose, module="RIGOR"), RIGOR classification driving state transitions, scars. Direct evidence of the architecture layers and "ternary state" "HOLD" "recovery" concepts. Author attribution preserved (James/Melissa Clow work).
- baseline-immutable/.../guardian_whitepaper_text.txt (CANONICAL): Explicitly maps Guardian Intake zones to PERCEPT → ATAL → RIGOR → CIRCUIT → FractalMemoryMap → GUARD → SERA. "Project family: Guardian / Fractalish AI / Cognitive Basin". High-relevance source.
- EphUX_* backups and verified/: HISTORICAL / UNVERIFIED. Hashes recorded. Contents include older/smaller versions of the three workers + restoration JSONs. Different SHA from live.
- FractalishBuild/: large, targeted search only (avoid bulk due to disk).
- Documents/Codex/: high volume .md notes — targeted keyword search performed via tools; more canon likely present.
- .grok sessions: historical prompts only, untrusted for completion claims.

## Implementation State (evidence-linked, no placeholders claimed)
- PERCEPT, ATAL, RIGOR, CIRCUIT, GUARD, SERA: PARTIAL (Python contracts + controller + whitepaper define the flow and objects; live activation-kernel + intake realize surface receptor/guard/ternary/Activation Doctrine; full stack, FractalMemoryMap, Basin state machine, SERA lifecycle not located as complete executable in one place).
- Ternary (epistemic + action separate), HOLD, RETRACT/EXTEND, scars, budget, receptor events: DISCOVERED in contracts/controller + present in kernel output schema + intake.
- Natural Math Basic Persistent Growth System: NOT BUILT in code located so far (notes may exist in Codex; treat simulation architecture).
- PWDither, atomic token, full auth: STUB (sketches + notes only in doctrine/fewshots; "not actually implemented" hypothesis holds in observed source).
- Completion Integrity Guard: NOT BUILT (this M0 process with reopen+hash+parse+no-placeholder + manifest + live probe is the first enforcement step).
- Prior backups/"verified"/reports: UNVERIFIED / DEFECTIVE until this audit (different live vs backup SHAs, placeholder language risk, simulated elements per directive hypothesis).
- ephux-next basin-lab + release "ephux-cognitive-basin-lab-v0.1": PARTIAL / CURRENT_IMPLEMENTATION_PARTIAL (tests for BasinLab, core contracts).

## Evidence & Hashes (M0 baseline)
- Backup ZIPs: EphUX-Rebuild... 8BD64F4F5E64717AF6E399089493B2975C13A16EB9881E5D7658D5609EC7286F ; verified zip 4A5FD7FFEB168E89C80E5A4921DE73906569361E3885776B2F8903107E67DDAA
- Live sources written to evidence/live-deployed-2026-06-16/ and locally hashed (see manifests/artifact-manifest.json + terminal output for exact SHAs; full verbatim in MCP results).
- All entries satisfy: artifact exists on disk, can be reopened, source is the real fetched/deployed text (no fabricated), no prohibited placeholders in this recovery's new artifacts.
- Git status known at commit time.
- Production: untouched. Cost: zero new charges (R2 disabled confirmed).

## Key Local Artifacts Discovered (initial)
- C:\Users\moop\ephux-next\ (current candidate surface?)
- C:\Users\moop\EphUX_Cloudflare_Backup_2026-06-16\
- C:\Users\moop\EphUX_Cloudflare_Backup_2026-06-16-verified\
- C:\Users\moop\EphUX-Rebuild-2026-06-16\
- C:\Users\moop\EphUX_Full_Backup_20260616-152640\
- C:\Users\moop\FractalishBuild\ (very large — targeted search only)
- C:\Users\moop\Documents\Codex\ (large collection of .md notes — high probability of source canon)
- C:\Users\moop\Documents\New project\
- Multiple ZIPs and prior "verified" exports
- Existing .grok sessions with prior prompts (treated as historical, not authoritative)

## Cloudflare (read-only audit in progress)
- MCP servers connected: cloudflare-api, cloudflare-bindings, cloudflare-builds, cloudflare-docs, cloudflare-observability
- Known hypothesis (from prior notes, to be re-verified live):
  - Account: ae23bc612ecaa4ebbca2740eae4b5639
  - Zone: ephux.com (ID 044c2c969e6c79325c4ee967157c8ce8)
  - Workers: ephux (tiny), ephux-activation-kernel, ephux-guardian-intake
  - KV: GUARDIAN_INTAKE_KV
  - Routes exist for www.ephux.com, ephux.com, /activation*, /intake*
- **No production mutations performed or planned in this session without approval.**
- R2 noted as previously disabled — will confirm; do not enable without pricing + approval check.

## GitHub
- Audit pending (gh CLI check + repo list)

## Implementation State (honest, evidence only)
- PERCEPT / ATAL / RIGOR / CIRCUIT / GUARD / SERA layers: NOT BUILT (no code meeting the layer definitions has been located or verified yet)
- FractalMemoryMap, Association* objects, Basin state machine, TeamNarrative, Stabilization, HOLD fog: NOT BUILT
- Natural Math Basic Persistent Growth System: NOT BUILT (source notes may exist in Codex)
- Activation Kernel / Guardian Intake / EphUX Workers: DISCOVERED as prior deployed artifacts + local backup copies. Live source must be downloaded and compared. Prior "verified" claims treated as untrusted.
- Authentication / PWDither / Atomic token: NOT BUILT (prompt mentions only)
- Browser extension, dashboard, Synaptient: PARTIAL / STUB / UNKNOWN pending search
- Completion Integrity Guard: NOT IMPLEMENTED (this recovery process is the beginning of enforcing it)
- All prior "backups" and reports: UNVERIFIED / DEFECTIVE until re-audited with hashes, re-parsed source, live probes.

## Blockers / Observations
- Prior artifacts may contain placeholders (PASTE, TODO, MOCK, etc.), malformed JSON/TOML, fabricated manifests. Will scan explicitly.
- Low free space on C: (~13GB). Large copies (FractalishBuild) will be avoided; use targeted reads + hashes.
- Cost constraint acknowledged: free tiers, local execution, existing subs (Qwen, etc.) prioritized. No paid activation without recorded approval.
- No indiscriminate personal data ingestion.

## Evidence Links (to be populated)
- First artifact manifest: pending (hashes of zips + key files)
- Live Cloudflare observations: pending MCP calls
- GitHub observations: pending

Next update after M0 tool actions complete (hashes, inventories, Cloudflare read-only audit, GitHub inventory, initial canonical search, first commit).

This file will be updated before context limits, handoffs, deployments, or approval requests. No reliance on chat memory.
