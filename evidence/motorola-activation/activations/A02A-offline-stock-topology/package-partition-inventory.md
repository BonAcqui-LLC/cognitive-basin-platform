# Package Partition Inventory

Partitions recorded: 25

| Partition | Kind | Slot | Sources | AVB Role | Boot Role | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| apex | LOGICAL | LOGICAL_DYNAMIC | super.img_sparsechunk.* | VERIFIED_LOGICAL_PAYLOAD | LOGICAL_OS_PAYLOAD | MEDIUM |
| boot_a | PHYSICAL | SLOTTED_SINGLE_TARGET | boot.img, boot.img | VERIFIED_PAYLOAD | KERNEL_BOOT_PAYLOAD | HIGH |
| dtbo_a | PHYSICAL | SLOTTED_SINGLE_TARGET | dtbo.img, dtbo.img | VERIFIED_PAYLOAD | KERNEL_BOOT_PAYLOAD | HIGH |
| efuse | PHYSICAL | UNSLOTTED | efuse.img | UNKNOWN | UNKNOWN | HIGH |
| gpt | PHYSICAL | UNSLOTTED | PGPT, PGPT | UNKNOWN | PARTITION_TABLE | HIGH |
| gz_a | PHYSICAL | SLOTTED_SINGLE_TARGET | gz.img, gz.img | UNKNOWN | UNKNOWN | HIGH |
| lk_a | PHYSICAL | SLOTTED_SINGLE_TARGET | lk.img, lk.img | UNKNOWN | BOOTLOADER_STAGE | HIGH |
| logo_a | PHYSICAL | SLOTTED_SINGLE_TARGET | logo.img, logo.img | UNKNOWN | UNKNOWN | HIGH |
| md1img_a | PHYSICAL | SLOTTED_SINGLE_TARGET | md1img.img, md1img.img | UNKNOWN | UNKNOWN | HIGH |
| metadata | PHYSICAL | UNSLOTTED |  | UNKNOWN | UNKNOWN | HIGH |
| nvdata | PHYSICAL | UNSLOTTED |  | UNKNOWN | UNKNOWN | HIGH |
| preloader | PHYSICAL | UNSLOTTED | preloader.img, preloader.img | UNKNOWN | PRE_BOOT_STAGE | HIGH |
| product | LOGICAL | LOGICAL_DYNAMIC | super.img_sparsechunk.* | VERIFIED_LOGICAL_PAYLOAD | LOGICAL_OS_PAYLOAD | MEDIUM |
| scp_a | PHYSICAL | SLOTTED_SINGLE_TARGET | scp.img, scp.img | UNKNOWN | UNKNOWN | HIGH |
| spmfw_a | PHYSICAL | SLOTTED_SINGLE_TARGET | spmfw.img, spmfw.img | UNKNOWN | UNKNOWN | HIGH |
| sspm_a | PHYSICAL | SLOTTED_SINGLE_TARGET | sspm.img, sspm.img | UNKNOWN | UNKNOWN | HIGH |
| super | PHYSICAL_DYNAMIC_CONTAINER | UNSLOTTED | super.img_sparsechunk.0, super.img_sparsechunk.1, super.img_sparsechunk.2, super.img_sparsechunk.3, super.img_sparsechunk.4, super.img_sparsechunk.5, super.img_sparsechunk.6, super.img_sparsechunk.7, super.img_sparsechunk.8, super.img_sparsechunk.9, super.img_sparsechunk.10, super.img_sparsechunk.11, super.img_sparsechunk.12, super.img_sparsechunk.13, super.img_sparsechunk.14, super.img_sparsechunk.15, super.img_sparsechunk.16, super.img_sparsechunk.17, super.img_sparsechunk.18, super.img_sparsechunk.19, super.img_sparsechunk.20, super.img_sparsechunk.21, super.img_sparsechunk.22, super.img_sparsechunk.23, super.img_sparsechunk.24, super.img_sparsechunk.25, super.img_sparsechunk.26, super.img_sparsechunk.27, super.img_sparsechunk.28, super.img_sparsechunk.29, super.img_sparsechunk.30, super.img_sparsechunk.31, super.img_sparsechunk.32, super.img_sparsechunk.33, super.img_sparsechunk.34, super.img_sparsechunk.35, super.img_sparsechunk.36, super.img_sparsechunk.37, super.img_sparsechunk.38, super.img_sparsechunk.39, super.img_sparsechunk.40, super.img_sparsechunk.41, super.img_sparsechunk.42, super.img_sparsechunk.43, super.img_sparsechunk.44, super.img_sparsechunk.45, super.img_sparsechunk.46, super.img_sparsechunk.47, super.img_sparsechunk.48, super.img_sparsechunk.49, super.img_sparsechunk.50, super.img_sparsechunk.51, super.img_sparsechunk.52, super.img_sparsechunk.53, super.img_sparsechunk.54, super.img_sparsechunk.55, super.img_sparsechunk.56, super.img_sparsechunk.57, super.img_sparsechunk.58, super.img_sparsechunk.59, super.img_sparsechunk.60, super.img_sparsechunk.61, super.img_sparsechunk.62, super.img_sparsechunk.63, super.img_sparsechunk.0, super.img_sparsechunk.1, super.img_sparsechunk.2, super.img_sparsechunk.3, super.img_sparsechunk.4, super.img_sparsechunk.5, super.img_sparsechunk.6, super.img_sparsechunk.7, super.img_sparsechunk.8, super.img_sparsechunk.9, super.img_sparsechunk.10, super.img_sparsechunk.11, super.img_sparsechunk.12, super.img_sparsechunk.13, super.img_sparsechunk.14, super.img_sparsechunk.15, super.img_sparsechunk.16, super.img_sparsechunk.17, super.img_sparsechunk.18, super.img_sparsechunk.19, super.img_sparsechunk.20, super.img_sparsechunk.21, super.img_sparsechunk.22, super.img_sparsechunk.23, super.img_sparsechunk.24, super.img_sparsechunk.25, super.img_sparsechunk.26, super.img_sparsechunk.27, super.img_sparsechunk.28, super.img_sparsechunk.29, super.img_sparsechunk.30, super.img_sparsechunk.31, super.img_sparsechunk.32, super.img_sparsechunk.33, super.img_sparsechunk.34, super.img_sparsechunk.35, super.img_sparsechunk.36, super.img_sparsechunk.37, super.img_sparsechunk.38, super.img_sparsechunk.39, super.img_sparsechunk.40, super.img_sparsechunk.41, super.img_sparsechunk.42, super.img_sparsechunk.43, super.img_sparsechunk.44, super.img_sparsechunk.45, super.img_sparsechunk.46, super.img_sparsechunk.47, super.img_sparsechunk.48, super.img_sparsechunk.49, super.img_sparsechunk.50, super.img_sparsechunk.51, super.img_sparsechunk.52, super.img_sparsechunk.53, super.img_sparsechunk.54, super.img_sparsechunk.55, super.img_sparsechunk.56, super.img_sparsechunk.57, super.img_sparsechunk.58, super.img_sparsechunk.59, super.img_sparsechunk.60, super.img_sparsechunk.61, super.img_sparsechunk.62, super.img_sparsechunk.63 | VERIFIED_LOGICAL_CONTAINER | DYNAMIC_SYSTEM_CONTAINER | HIGH |
| system | LOGICAL | LOGICAL_DYNAMIC | super.img_sparsechunk.* | VERIFIED_LOGICAL_PAYLOAD | LOGICAL_OS_PAYLOAD | MEDIUM |
| system_ext | LOGICAL | LOGICAL_DYNAMIC | super.img_sparsechunk.* | VERIFIED_LOGICAL_PAYLOAD | LOGICAL_OS_PAYLOAD | MEDIUM |
| tee_a | PHYSICAL | SLOTTED_SINGLE_TARGET | tee.img, tee.img | UNKNOWN | TRUSTZONE_STAGE | HIGH |
| userdata | PHYSICAL | UNSLOTTED |  | UNKNOWN | UNKNOWN | HIGH |
| vbmeta_a | PHYSICAL | SLOTTED_SINGLE_TARGET | vbmeta.img, vbmeta.img | ROOT_VBMETA | AVB_METADATA | HIGH |
| vbmeta_system_a | PHYSICAL | SLOTTED_SINGLE_TARGET | vbmeta_system.img, vbmeta_system.img | SUB_CHAIN_VBMETA | AVB_METADATA | HIGH |
| vendor | LOGICAL | LOGICAL_DYNAMIC | super.img_sparsechunk.* | VERIFIED_LOGICAL_PAYLOAD | LOGICAL_OS_PAYLOAD | MEDIUM |
| vendor_boot_a | PHYSICAL | SLOTTED_SINGLE_TARGET | vendor_boot.img, vendor_boot.img | VERIFIED_PAYLOAD | KERNEL_BOOT_PAYLOAD | HIGH |
