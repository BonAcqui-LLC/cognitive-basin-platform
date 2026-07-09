# System Architecture

## Objective

Deliver the first honest vertical slice that connects:

- AIA operator surface
- Cognitive Basin governance
- BasinLab session persistence
- Guardian intake
- EphUX/Flux-UX activation flow
- Completion Integrity
- SERA and SessionGlyph receipts
- eventual stock-device and later AOSP deployment path

## Current architecture decision

Build in four layers, keeping destructive ROM work out of scope until the lower layers are verified.

### Layer 1: Source and evidence spine

- source receipts in `receipts/source_receipts.json`
- architecture, threat, audit, and go/no-go docs in `docs/` and `reports/`
- device audit receipts written by `tools/device_audit.ps1`

This layer prevents myth-building and keeps the repo grounded in explicit evidence.

### Layer 2: Verified local canon import

Imported architectural authority comes from `cognitive-basin-platform`:

- Cognitive Basin pipeline semantics
- ternary epistemic and action governance
- BasinLab persistence and replay
- Completion Integrity claim gating
- Guardian intake pattern
- EphUX local activation flow
- Session and report discipline

This layer is already implemented elsewhere and is the baseline the Android shell should wrap or port, not reinvent.

### Layer 3: Stock-Android launcher shell

The `android/` app in this repo is intentionally modest but now operational:

- native launcher activity
- purpose-first typed activation surface
- deterministic governed runtime in Kotlin
- persisted session list and replay
- verifiable export and tamper check
- explicit device-review and demonstration activation paths

This remains the safest truthful first step for the Motorola demonstration path because it runs on stock OS without bootloader unlock.

### Layer 4: Future on-device runtime migration

Only after stock-device verification should the runtime advance toward:

- on-device persistence store
- local transcription adapter
- compact local-model orchestration
- guardian intake capture on device
- SymID and SessionGlyph persistence
- privileged system integration in a custom AOSP build

## Data-flow sketch

1. Operator opens the Android app.
2. The home surface reports local device, provider, and rule-pack state.
3. A typed purpose enters a bounded activation classifier.
4. Deterministic Kotlin governance routes the proposal through ternary Cognitive Basin semantics.
5. The governed outcome resolves to `SUPPORTED / EXTEND`, `UNRESOLVED / HOLD`, or `CONTRADICTED / RETRACT`.
6. Session evidence, contradictions, Guardian findings, and recovery routes are rendered in-app.
7. The session is persisted locally and can be exported as a verifiable package.

## Boundary decisions

- no cloud-provider dependency is assumed in the first stock-device demo
- no destructive Motorola operation is authorized from this repo
- no live legal-accuracy claim is authorized from placeholder rule packs
- no unrestricted shell or signing-key authority should ever be delegated to the runtime

## Immediate implementation gap

As of the current stock-device pass, the gap is no longer "can it build and reopen." The gap is refinement:

- broader golden-trace comparison against canonical platform fixtures
- tighter first-screen mobile ergonomics
- explicit microphone boundary without hidden audio storage
- deeper benchmark evidence before any on-device model expansion
