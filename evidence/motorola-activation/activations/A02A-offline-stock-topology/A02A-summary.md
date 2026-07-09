# A02A Summary

Status: COMPLETE
Original archive hash before: B3B86713E066002C37877ECF8ABFF525BF147D1EC3207CA04FF0397DDC5E604D
Original archive hash after: B3B86713E066002C37877ECF8ABFF525BF147D1EC3207CA04FF0397DDC5E604D
Extraction success: True
Extracted file count: 87
Parsed manifest count: 2
Dynamic partition conclusion: SUPPORTED_BY_PACKAGE_SUPER_TARGET_AND_FROZEN_DM_MOUNTS
AVB conclusion: Package contains vbmeta and vbmeta_system payloads, but descriptor-level chain parsing and rollback metadata remain unresolved offline.
Restore suitability: NOT_YET_ESTABLISHED

## Identity conclusion

Package is a same-family RETUS/gnevan_g stock release for XT2317-2 lineage, but it is an older build (-8) than the frozen live handset build (-24).

## Key differences

- build_fingerprint: live=motorola/gnevan_g/gnevan:14/U1THS34.65-74-1-7-24/111802-edae6:user/release-keys package=motorola/gnevan_g/gnevan:14/U1THS34.65-74-1-7-8/2e589-1f965e:user/release-keys
- build_id: live=U1THS34.65-74-1-7-24 package=U1THS34.65-74-1-7-8
- build_incremental: live=111802-edae6 package=2e589-1f965e
- bootloader_version: live=MBM-2.1-gnevan_g-5ba36-U1THS34.65-74-1-7-24-111802 package=MBM-2.1-gnevan_g-5ba36-U1THS34.65-74-1-7-8-2e589
- baseband_version: live=MT6769G_TC2.PR5.SP.V9.2.P21.02.40R package=MT6769G_TC2.PR5.SP.V9.2.P17.02.35R

## Open holds

- anti_rollback: Rollback indexes were not authoritatively parsed from signed metadata offline.
- restore_suitability: The preserved package is older than the live build and remains NOT_YET_ESTABLISHED for restoration.
- super_logical_inventory: Trusted host parser for super metadata was not available offline; logical partition set is supported by frozen mount evidence but not fully enumerated from package metadata.
- fastbootd_support: Userspace fastboot support must be confirmed live in a later read-only activation.
