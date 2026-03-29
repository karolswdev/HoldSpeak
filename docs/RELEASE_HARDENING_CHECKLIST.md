# HoldSpeak Release Hardening Checklist

Use this checklist before calling a build "production-ready."

## 1) Platform E2E

- [ ] Linux X11: global hotkey press/release transcribes and injects text.
- [ ] Linux Wayland: focused hold-to-talk + clipboard/manual paste fallback works.
- [ ] macOS: global hotkey works and accessibility/text input permissions are validated.
- [ ] Meeting mode on Linux: monitor-source system audio + mic both captured.
- [ ] Meeting mode on macOS: BlackHole + mic both captured.
- [x] Quit while meeting is active: meeting is finalized and persisted.

## 2) Lifecycle / Shutdown

- [x] Background workers stop cleanly (no orphan loops on exit).
- [x] Active meeting stop path waits for final save result.
- [x] No pending write operations are abandoned during app close.

## 3) Settings Coverage

- [x] TUI settings expose hotkey/model + key meeting/intel/export options.
- [x] Changing settings in-app updates runtime behavior without restart where applicable.
- [x] Config validation prevents invalid numeric values (queue poll, thresholds).

## 4) Persistence

- [x] New install creates valid config and DB schema.
- [x] Failure path falls back to JSON archive if DB write fails.

## 5) Diagnostics

- [ ] `holdspeak doctor` clean on supported baseline systems.
- [x] Doctor warnings include actionable next steps.
- [ ] Logs include enough context to debug startup, recording, and save failures.

## 6) Test Gates

- [x] Unit + integration suite green.
- [x] Linux smoke script green.
- [x] Meeting/web integration tests green when `[meeting]` extras are installed.
- [x] Any regressions in quit/settings/meeting-stop flows are blocked by tests.
