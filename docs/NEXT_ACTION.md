# NEXT_ACTION.md
# Exact next commands and state for handoff — 2026-06-16 M0

## Immediate (M0 remaining)
1. Complete local inventory + hashes of all EphUX_* backups, ephux-next, FractalishBuild (targeted), Codex notes (search for keywords).
2. Complete read-only Cloudflare audit:
   - workers_list / workers_get_worker / workers_get_worker_code for all three known
   - kv_namespaces_list + get
   - Confirm routes, bindings, deployments, no R2 activation
   - Any Pages, Email Routing, DNS records (read only)
3. GitHub inventory (in progress):
   - gh 2.94.0 installed via winget.
   - Complete device auth now (one-time code: 22CF-33AE ; open https://github.com/login/device in browser and authorize).
   - After success: run `gh repo list --org BonAcqui-LLC --limit 100` + personal repos.
   - Record: name, visibility (private), default branch, updated, purpose from description/contents.
   - Check existence of BonAcqui-LLC/cognitive-basin-platform and cognitive-basin-canonical.
   - Plan creation (private only) after explicit approval in this recovery.
4. Compare deployed Worker source (downloaded via MCP) vs local copies vs backup zips (hashes + content diff where small).
5. Targeted canonical search:
   - Filename + content for "Cognitive Basin", "Fractalish", "PERCEPT", "ATAL", "RIGOR", "CIRCUIT", "GUARD", "SERA", "FractalMemoryMap", "Natural Math", "Basic Persistent Growth System", "TeamNarrative", "BasinLab", "PWDither", "Tri-Weavon", "ternary", "association brush|beacon|field", "contradiction scar", "recovery route", "HOLD fog", "Activation Kernel", "Guardian Intake"
   - Primary sources: Documents/Codex/*.md, ephux-next/, EphUX backups (unzip carefully to quarantine first), FractalishBuild (select files).
6. Create first evidence manifest (JSON + md) with:
   - SHA256 of every backup zip and key source file
   - Inventory of discovered source documents with provenance
   - Classification per directive (CANONICAL / HISTORICAL / DEFECTIVE / etc.)
7. Update all docs/*.md + ops/manifests/*.json
8. git commit -m "recovery: establish independent evidence baseline"
9. Transition to M1: build canonical library at C:\Users\moop\Cognitive-Basin-Canonical-Library (or inside recovery/canon)

## Exact commands to run next (if resuming)
```powershell
# From recovery root
Set-Location "C:\Users\moop\Cognitive-Basin-Recovery-2026-06-16"

# Targeted file discovery (safe)
Get-ChildItem -Path C:\Users\moop -Recurse -Include *.md,*.txt,*.toml,*.json -Depth 5 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch 'node_modules|\.git|AppData|Pictures|Videos|OneDrive|Downloads|Desktop' -and $_.Length -lt 500KB } |
  Select-String -Pattern 'Cognitive Basin|Fractalish|PERCEPT|ATAL|RIGOR|CIRCUIT|GUARD|SERA|Natural Math|FractalMemoryMap' -List |
  Select-Object -First 50 Path, LineNumber, Line

# Hash key backups
Get-FileHash "C:\Users\moop\EphUX_Cloudflare_Backup_2026-06-16-verified.zip" -Algorithm SHA256
# ... repeat for others

# GitHub (if gh present)
gh --version
gh repo list --limit 100
gh repo list BonAcqui-LLC --limit 50

# Continue Cloudflare (via MCP after search_tool)
```

## After M0 commit
- Begin M1: curate canonical library (copy only verified relevant small sources + index with provenance, author attribution to James/Melissa Clow / BonAcqui LLC)
- Create contracts/ and capability-registry.json skeleton
- Locate or create source for the 6 layers + understanding objects + memory contract
- Implement Completion Integrity Guard as first executable guard

Do not produce plans without acting. Update this file with exact next command before stopping or long operation.
