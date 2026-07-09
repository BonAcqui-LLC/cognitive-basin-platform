# ADR: Package Identity

Date: 2026-06-17

Status: accepted

## Decision

Use `llc.bonacqui.aia` as the stable Android package namespace and application id for the stock-OS vertical slice.

## Why

- `llc.bonacqui` is a BonAcqui-controlled namespace
- the earlier placeholder namespace was temporary and did not reflect the desired ownership boundary
- the v1.1 directive explicitly preferred a stable BonAcqui-controlled namespace
- keeping the current package id avoids needless churn after the first verified install

## Consequences

- the launcher activity resolves as `llc.bonacqui.aia/.MainActivity`
- app-local storage, exports, and package verification all align to the same stable identity
- future release signing can preserve continuity without renaming the application id again
