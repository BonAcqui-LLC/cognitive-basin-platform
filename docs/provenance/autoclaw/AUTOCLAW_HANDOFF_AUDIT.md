# AUTOCLAW Handoff Audit

Generated: 2026-06-24T05:29:25.745208+00:00

## Repository State

- Repository root: `C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE`
- Branch: `main`
- HEAD: `ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9`
- Working tree clean at start: True
- Working tree unchanged after audit: True
- Tracked files: 140
- Untracked files: 0
- Ignored files: 22
- Remotes configured: 0
- Python: Python 3.12.10
- OS: Windows 10 (10.0.19045)

## Frozen Baseline

- Frozen source path: `C:\_MASTER_LIBRARY\01_CANON\01_NATURAL_MATH_V5\Natural Math v5 - Status Frozen Int.txt`
- Frozen source SHA256: `E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B`
- Expected SHA256 matched: `True`
- Local tag: `natural-math-v5-reference-1.0` -> `28ffa5974b5fd157982f36fdb1189ac9d1fb6acb`
- Current workspace differs from tagged baseline: `True`
- Reference implementation differs from tagged baseline: `False`
- Changed reference-implementation files since tag: none

## Local Tags

- `natural-math-v5-reference-1.0	tag	3e3293b2360e37128edb71f4f53fceb228c2346e	28ffa5974b5fd157982f36fdb1189ac9d1fb6acb`

## External Evidence Hashes

- `integer_fixtures`: `0E6BE599491AF2199A40DCA5D511C614E46A2679BD3B848CE7669E3FE300090F`
- `cluster_fixtures`: `031B21ECD272ECB8E47A7AA517C6DFD9B4E97B3507254F2228B6EFC101AF0BC2`
- `integer_runner`: `31BF301873B9FB872C4EFA24237DD3FE24238644441FABC54235122201553965`
- `cluster_runner`: `F823FA9EC81645E85719DBAFE6265440C4A9777790B7A3B73389244315838E5D`

## Stage Findings

- Stage 0: reports only
- Stage 1: implemented
- Stage 1.1: implemented
- Stage 2: implemented
- Stage 3: not found

## Local Flow Trail Memory Search

```text
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\06_REPORTS\stage_2_completion.md:75:| PROPOSE_LOCAL_MOVE_PREFERENCE | Behavioral | `propose_local_move_preference` | âœ… |
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\06_REPORTS\baby_ai_layered_build_map.md:27:â”‚ Stage 3: Natural Math v5.1 Local Flow Trail Memory           â”‚
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\04_TESTS\extension_harness\test_core.py:45:        PROPOSE_LOCAL_MOVE_PREFERENCE, OBSERVATION_HOOKS, BEHAVIORAL_HOOKS,
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\04_TESTS\extension_harness\test_core.py:365:        PROPOSE_LOCAL_MOVE_PREFERENCE, HookContractError,
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\04_TESTS\extension_harness\test_core.py:369:    validate_hook_result(proposal, PROPOSE_LOCAL_MOVE_PREFERENCE, ext_id)
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\04_TESTS\extension_harness\test_core.py:372:        validate_hook_result(bad, PROPOSE_LOCAL_MOVE_PREFERENCE, ext_id)
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS\extension_harness\protocol.py:24:PROPOSE_LOCAL_MOVE_PREFERENCE = "PROPOSE_LOCAL_MOVE_PREFERENCE"
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS\extension_harness\protocol.py:45:BEHAVIORAL_HOOKS = frozenset({PROPOSE_LOCAL_MOVE_PREFERENCE})
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS\extension_harness\types.py:23:    PROPOSE_LOCAL_MOVE_PREFERENCE,
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS\extension_harness\types.py:58:    PROPOSE_LOCAL_MOVE_PREFERENCE = PROPOSE_LOCAL_MOVE_PREFERENCE
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS\extension_harness\types.py:76:        PROPOSE_LOCAL_MOVE_PREFERENCE: "propose_local_move_preference",
C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS\extension_harness\__init__.py:24:    PROPOSE_LOCAL_MOVE_PREFERENCE,
```

Interpretation: no `trail_edges`, `trail_deposit`, `trail_decay`, or `natural_math_v5_1_local_flow_trail_memory` implementation was found. `PROPOSE_LOCAL_MOVE_PREFERENCE` exists as a defined/validated hook surface but is not dispatched by the harness adapters and is therefore inactive in practice.

## Zip Verification

- Zip path: `C:\_MASTER_LIBRARY_Handoff\autoclaw_workspace_handoff.zip`
- Zip SHA256: `758F59126E14743ADEEF9DC0097043F891AA239774DF185C950D03FA7688198C`
- Zip opens successfully: `True`
- Zip contains `.git`: `True`
- Zip entry count: `361`

## Notes

- Repository-writing test scripts were executed through temporary redirected copies under the handoff temp directory so the original AutoClaw workspace stayed unchanged.
- Existing `__pycache__` / `.pyc` ignored artifacts were preserved in-place but excluded from the handoff zip.
