# Device Resource Envelope

Date: 2026-06-17

## Measured handset

- model: `moto g stylus (2023)`
- SKU: `XT2317-2`
- device / product: `gnevan` / `gnevan_g`
- hardware: `mt6768`
- Android: `14` (`sdk 34`)

## Resource measurements

- physical RAM (`MemTotal`): `3829792 kB`
- available memory during current observation: `1720220 kB`
- swap total: `2872340 kB`
- swap free: `2196244 kB`
- user storage total: `50424800 kB`
- user storage free: `30422940 kB`
- thermal status: `0`
- sampled temperatures included CPU/GPU/NPU around `37.0 C`, battery around `21.25-25.75 C`, skin around `24.704-26.699 C`
- battery at verification sample: `7%`, USB powered, status `2` (charging)

## Interpretation

- treat this handset as constrained hardware despite swap and RAM-boost style mechanisms
- physical RAM is roughly 3.65 GiB, so heavier on-device language models should not be assumed viable
- deterministic governance and export flows fit comfortably inside the current thermal and memory envelope
- low battery during testing means longer-run throughput measurements should be repeated under healthier charge conditions

## Measurement boundaries

- swap and zRAM are recorded separately and are not treated as physical RAM
- some deeper kernel-facing measurements, including direct zRAM internals and pressure files, were permission-limited over normal ADB shell
- no local-model benchmark was selected in this tranche
