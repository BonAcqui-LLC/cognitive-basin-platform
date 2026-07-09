# Read Me First

Read these files in order before doing any work:

1. `00_CONTROL/00_AGENT_CONSTITUTION.md`
2. `00_CONTROL/01_PROJECT_ORIENTATION.md`
3. `00_CONTROL/02_SOURCE_AUTHORITY.md`
4. `00_CONTROL/03_LIBRARY_MAP.md`
5. `00_CONTROL/04_BUILD_READINESS.md`
6. `00_CONTROL/05_DO_NOT_MODIFY.md`
7. `00_CONTROL/06_KNOWN_CONFLICTS.md`
8. `00_CONTROL/07_MISSING_MATERIALS.md`
9. `02_VALIDATION_EVIDENCE/NATURAL_MATH_V5/MATH_EVIDENCE_AUDIT.md`
10. `05_MANIFESTS/REPOSITORY_LEDGER.md`

Operating rules:

- Everything outside `06_AUTOCLAW_WORKSPACE` is read-only.
- AutoClaw may write only inside `06_AUTOCLAW_WORKSPACE`.
- Natural Math v5 is frozen.
- Extensions must be separately versioned.
- Conflicting sources must not be blended silently.
- No deployment or publication is permitted.
- No credentials, external accounts, or connectors may be accessed.
- No baby-AI implementation may begin until AutoClaw produces:
  - its own source inventory;
  - a conflict report;
  - a frozen-v5 evidence verification;
  - a current code-baseline report;
  - a proposed build map.

Authoritative library root: `C:\_MASTER_LIBRARY`
