# Stock APK Acceptance

Date: 2026-06-17

## Build and install

- package: `llc.bonacqui.aia`
- version: `0.1.1-stockos`
- APK: `android/app/build/outputs/apk/debug/app-debug.apk`
- replace-install: successful
- cold launch after force-stop: successful

## Verified on-device flows

1. Supported scenario produced `SUPPORTED / EXTEND`.
2. Ambiguous scenario produced `UNRESOLVED / HOLD`.
3. Contradiction scenario produced `CONTRADICTED / RETRACT`.
4. Three sessions persisted locally and remained readable after force-stop and relaunch.
5. Session export succeeded to app-specific external storage.
6. Export verification and re-import succeeded.
7. Tampered export verification failed as expected.

## Deferred acceptance

- airplane-mode repetition was not rerun in this pass
- full reboot persistence was not rerun in this pass

Those steps are user-disruptive rather than technically blocked.
