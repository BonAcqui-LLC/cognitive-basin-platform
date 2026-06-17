# FAILURES.md
# Record of observed failures, defects, and drift — 2026-06-16

This file records concrete evidence of prior defects. Used for recovery route construction and to prevent repetition. No blame — engineering data.

## M0 Discoveries (initial)
- Prior "EphUX_Cloudflare_Backup_2026-06-16-verified" and similar named as verified but directive requires re-hash + re-parse + live comparison. Classification: UNVERIFIED until proven.
- Directive explicitly lists prior limitations as known hypothesis (to re-verify):
  - Authentication not actually implemented.
  - PWDither prompt-level only.
  - Intake scanning mostly hard-coded status language.
  - Raw content mislabeled as sanitized.
  - One-time KV consumption non-atomic.
  - Basin and stabilization not implemented.
  - Several extension paths simulated success or generated fake fallback links.
  - /health and /schema absent.
  - Prior backups and verification reports defective.
- These are treated as observations to confirm with fresh evidence, not as settled fact until live probes + source downloads + parse succeed.
- Placeholder language (PASTE, TODO, MOCK SUCCESS, etc.) forbidden in final artifacts. Will scan all candidate sources for them.
- Low disk space on C: observed — risk for large copies. Mitigation: targeted reads, hashes, quarantine of suspicious archives.

## Pattern to record
- Date
- Observed failure (with exact file/line or command output if possible)
- Impact (drift, security, cost, correctness)
- Recovery action taken
- Evidence hash / link

(Empty for new recovery; will populate from scans.)
