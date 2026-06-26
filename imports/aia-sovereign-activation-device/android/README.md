# Android Vertical Slice Notes

This directory now builds and installs a verified stock-Android AIA vertical slice.

Current app facts:

- package: `llc.bonacqui.aia`
- version: `0.1.1-stockos`
- compile / target SDK: `34`
- min SDK: `29`
- language and UI stack: Kotlin with AppCompat / XML layout
- current runtime: deterministic local Cognitive Basin governance slice with persistence and export

Verified outcomes on the audited Motorola handset:

- APK builds successfully with Gradle 8.7 and JDK 17
- replace-install succeeds over `adb`
- app cold-launches after force-stop
- governed demo states, persistence, export verification, and tamper detection work on-device

Still intentionally out of scope in this tranche:

- root or privileged Android behavior
- background audio capture
- mandatory remote provider dependency
- destructive custom-ROM operations
