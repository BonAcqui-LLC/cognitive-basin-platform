# SERA Mobile Metrics

Date: 2026-06-17

## What the current runtime records

- activation duration
- memory before activation
- memory after activation
- battery percentage at activation time
- thermal status
- provider call count
- provider failure count
- rule lookup count
- HOLD count
- contradiction count

## What was measured externally in this tranche

- cold launch after force-stop: `1764 ms`
- current live app memory sample: `TOTAL PSS 87458`, `TOTAL RSS 192712`
- session file sizes: `2166`, `2568`, and `2696` bytes
- export size: `3847` bytes
- tampered export size: `3829` bytes

## Known limits

- the current runtime leaves `export_size_bytes` and `persistence_size_bytes` unset in the in-app SERA struct
- CPU load sampling remains coarse in this tranche
- battery delta across a long repeated-use run was not captured because the battery was already low during testing
