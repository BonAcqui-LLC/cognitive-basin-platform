# Threat Model

Recorded on 2026-06-17 for the stock-device-first AIA path.

## Assets to protect

- operator sovereignty
- device integrity and recoverability
- private AIA and Synaptient materials
- source provenance and evidence receipts
- local session history and future SessionGlyph chains
- any future secrets, signing keys, or model credentials

## Primary threats

### T1. False completion claims

Risk:
Declaring the Motorola build, APK install, benchmark, or custom-OS readiness complete without reopened evidence.

Current control:

- stock build, install, cold-launch, and package receipts now exist
- source-receipt ledger
- custom-OS `NO-GO` report

### T2. Destructive handset action before audit

Risk:
Bootloader unlock, flash, reset, root, or partition modification before exact variant and lock state are known.

Current control:

- no destructive commands were run
- audit script is read-only
- destructive stage blocked in writing

### T3. Prompt or document injection through imported materials

Risk:
Copied concept docs or chat transcripts include unsafe autonomy, overclaiming, or contradictory directives.

Current control:

- active canon separated from conceptual references
- supersession map distinguishes build-driving authority from adjacent theory
- current app scaffold surfaces `HOLD` by default

### T4. Secret leakage into the repository

Risk:
Tokens, browser profiles, API keys, or personal data get copied into the device repo.

Current control:

- no secrets stored here
- upstream EphUX baseline already includes secret redaction intent and bounded local-token use

### T5. Network or provider dependency inversion

Risk:
The "sovereign local" demo silently depends on external providers or unstable remote services.

Current control:

- current APK does not request `INTERNET`
- provider state is deterministic-fixture-only in the shipped slice
- stock-demo plan requires explicit benchmark and local-runtime receipts before sovereignty claims

### T6. Untrusted ROM or binary foundation

Risk:
Using unverifiable community binaries as the base for an AIA build.

Current control:

- custom-OS stage currently `NO-GO`
- stock Motorola verification is required first

### T7. Excessive on-device authority

Risk:
Future runtime receives unrestricted filesystem, signing, modem, or bootloader authority.

Current control:

- launcher shell has no privileged Android capabilities
- future system integration is deferred behind explicit approvals

## Residual risks

- first-screen ergonomics are still tight on the 720x1600 handset
- exact unlock eligibility and full partition map are still unverified
- airplane-mode and full reboot acceptance were intentionally deferred because they are user-disruptive
- no benchmark path has been proven for local transcription or local-model operation

## Required evidence to lower risk

1. deeper golden-trace comparison against canonical platform fixtures
2. broader latency and repeated-use measurements
3. explicit audio-boundary verification
4. operator-approved disruptive acceptance for airplane-mode and reboot persistence
