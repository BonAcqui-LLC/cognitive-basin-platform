# APTD current evidence

**Reconciliation date:** 2026-08-31

**Scope:** Public and locally reported evidence relevant to APTD host continuity

**Overall physical status:** NOT YET DEMONSTRATED

This record separates a design specification, bounded public software evidence, an honest negative result, and locally reported work that has not cleared publication. A software continuity result must not be presented as a completed physical APTD.

## Evidence ledger

| Evidence layer | Status | Supported conclusion | Explicit limitation |
|---|---|---|---|
| [APTD paper v1.0](https://fractalish.com/research/aptd/) | SPECIFICATION / WORKING DESIGN | Defines the Autonomic Persistence and Transition Device architecture and acceptance boundary | Does not demonstrate a physical APTD |
| Baby AI / FormationCore authority-history line | PUBLIC / BOUNDED SOFTWARE EVIDENCE | Retained history and current authority can be separated in bounded software behavior | Is not physical perception or embodiment |
| [R-001 allocator continuity](https://github.com/persistentiterations/AI/releases/tag/BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1) | PUBLIC / FROZEN / BOUNDED | Identifier allocation survives the declared reload path | Does not establish complete provenance or authoritative-history continuity |
| [Original M2 commit](https://github.com/persistentiterations/AI/commit/9de9a791ad00d425c89bcece91e1360e8feb2502) | PUBLIC / NEGATIVE RESULT / HOLD | Exposes provenance and historical-completeness failures | Does not establish trustworthy M2 continuity |
| Narrow provenance/completeness repair, commit `89c4a00876bb2027ef8009d61e87a418a0b3aa8e` | LOCAL-REPORTED / PUBLICATION-HOLD | Reports fail-closed handling for missing provenance and required historical objects | Commit and repair tag are absent from the public remote; freeze evidence does not reconcile |
| Repaired M2 PASS | LOCAL-REPORTED PASS / PUBLICATION-HOLD | Reports a fresh M2 pass after the narrow repair | Does not qualify as public, verified, or frozen evidence |
| Fractalish v4 module surfaces | PUBLIC SOURCE / PROTOTYPE OR FUNCTIONAL RESPONSIBILITY | Provide module-level experiments and historical functional decomposition | Are not the FormationCore authority/history core and are not all production services |
| Motorola physical loop | EXPERIMENTAL SUBSTRATE / NOT YET DEMONSTRATED | Supplies an intended bounded device class for future tests | No complete authenticated world-to-formation-to-governed-consequence loop has been demonstrated |

## Public negative result retained

The public evidence path is intentionally legible:

```text
R-001 allocator continuity
-> original M2 attempt
-> FAIL / HOLD: provenance and historical-completeness gaps
-> narrow local repair
-> locally reported fresh M2 PASS
-> PUBLICATION-HOLD pending a reconciled public evidence package
```

The original failed M2 remains inspectable at:

- Branch: [`hostile-qualification-v0_1`](https://github.com/persistentiterations/AI/tree/hostile-qualification-v0_1)
- Commit: [`9de9a791ad00d425c89bcece91e1360e8feb2502`](https://github.com/persistentiterations/AI/commit/9de9a791ad00d425c89bcece91e1360e8feb2502)
- Report: [`BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_REPORT.md`](https://github.com/persistentiterations/AI/blob/9de9a791ad00d425c89bcece91e1360e8feb2502/BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_REPORT.md)
- Receipt: [`BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_RECEIPT.json`](https://github.com/persistentiterations/AI/blob/9de9a791ad00d425c89bcece91e1360e8feb2502/BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_RECEIPT.json)
- Tests: [`baby_ai/tests/test_m2_continuity.py`](https://github.com/persistentiterations/AI/blob/9de9a791ad00d425c89bcece91e1360e8feb2502/baby_ai/tests/test_m2_continuity.py)

The failure showed that integrity of surviving records is not the same as completeness of required history: missing required provenance did not fail closed, and deletion of a required historical scar could silently permit a later transition.

## Why the later repair and M2 remain on publication HOLD

Reconciliation did not support upgrading the later result to `PUBLIC / VERIFIED / FROZEN`:

1. The public branch still resolves to the original failed-M2 commit `9de9a791ad00d425c89bcece91e1360e8feb2502`.
2. The locally observed repair commit `89c4a00876bb2027ef8009d61e87a418a0b3aa8e` is absent from the public remote.
3. The locally observed annotated tags `BABY_AI_PROVENANCE_CONTINUITY_REPAIR_v0_1` and `BABY_AI_AUTHORITATIVE_HISTORY_CONTINUITY_M2_v0_1` are absent from the public remote.
4. Current-authority documentation still designates the public R-001 freeze, while the committed repair report describes a pre-commit/pre-push state.
5. The committed freeze manifest has an empty `modified_files` mapping; its current hashes reflect a CRLF checkout rather than canonical repository blobs, and its prior hashes were not reproducible from the stated base.
6. Later PASS receipts and witnesses are ignored or untracked; one receipt describes itself as committed although it is not tracked.
7. Local summaries that describe the repair as pushed or remote-verified conflict with the observed public refs.

These are manifest, receipt, authority, and publication-state inconsistencies. They mean that the evidence package did not clear publication. They do **not** justify the separate claim that the narrow repair code itself failed.

Promotion requires a non-rewriting public history in which the exact commit and annotated tags are visible, the failed M2 remains reachable, the manifest binds canonical artifacts reproducibly, receipts agree with tracked state, and the declared verification can be rerun from public sources.

## Architecture boundary

APTD means **Autonomic Persistence and Transition Device** from paper v1.0 forward. Earlier dated artifacts retain **ATAL Portable Training Devices** as their historical expansion.

APTD is the runtime/physical boundary beneath a cognition layer. It authenticates observation, constrains qualification and persistence, validates continuity before authority is trusted, governs proposed transitions, and records consequence. It is not the intelligence and does not give a model root execution authority.

FormationCore is the relevant authority/history evidence line. Fractalish v4 labels and module prototypes describe functional responsibilities; their names or presence do not transfer FormationCore authority to those modules.

No new APTD implementation, module implementation, Motorola integration, or physical-device experiment was added by this documentation tranche.
