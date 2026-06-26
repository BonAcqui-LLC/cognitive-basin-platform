# AVB Package Chain

- `vbmeta.img` and `vbmeta_system.img` are present in the package and targeted at `vbmeta_a` and `vbmeta_system_a`.
- Trusted host AVB parsers were not available on PATH during A02A, so descriptor-level parsing and rollback indexes remain unresolved.
- The package therefore demonstrates AVB participation, not downgrade safety.
