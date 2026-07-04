# HSM-23-03 — The readiness / doctor panel in Settings

- **Project:** holdspeak-mobile
- **Phase:** 23
- **Status:** done — see [`evidence-story-03.md`](./evidence-story-03.md).
  `StoreHealthProbe` + `SetupStatus.sections` + the READINESS section in Settings
  (both halves proven live: the real hub's 23 doctor sections incl. its genuine warn,
  and a real future-version store rendering the amber refusal); the home banner names
  `.tooNew` instead of "Store unavailable".
- **Depends on:** HSM-23-01/02 (the mechanism it surfaces); `SetupStatus` +
  `HTTPDesktopClient.setupStatus()` (HSM-21-04) for the hub half.
- **Unblocks:** the iPad can finally tell you it is healthy — the audit's third theme-6
  bullet.
- **Owner:** unassigned

## Problem

The schema-safety mechanism is invisible, and store failures are indistinguishable:

- `StorageError.tooNew` reaches the user as a generic
  `"Store unavailable: …"` string (`MeetingCaptureApp.swift:214-215`) — the one moment
  the store *protected* their data reads like a crash.
- Three call sites `try?`-swallow open errors entirely (`DeskHome.swift:239`,
  `ReviewUI.swift:38`, `MeetingCaptureApp.swift:406`): nil store, no signal.
- No view reports store health (`integrityCheck()`), schema version (`userVersion()`),
  app version, mic permission, or model presence. The hub's `/api/setup/status` already
  serves a rich `sections` doctor block the Swift `SetupStatus` currently drops.

## The design

A **Readiness** section in `AppSettings.swift`'s `SettingsView` (the app's one Settings
surface), two halves, labels not manuals ([[feedback_no_prose_in_ui]]):

1. **This iPad:** store health (integrity ok / schema vN / the refuse-newer state when
   the open threw `.tooNew`, named as protection with the stored-vs-build versions), mic
   permission, model presence, app version. Reuse the live checks; no new plumbing.
2. **Your desktop (when paired):** the hub's doctor rollup — extend `SetupStatus` to
   decode the `sections` block it currently drops and render per-section state chips.

Distinguish `.tooNew` at the open call sites so the panel (and the open-failure banner)
states the truth instead of "Store unavailable".

## Scope

- **In:** the Settings section; the `SetupStatus.sections` decode + tests; typed
  `.tooNew` handling at the app's open sites; sim proof of both halves.
- **Out:** repair/restore actions (report, not repair); any new hub route (the doctor
  block already ships).

## Test plan

- `swift test` (new SetupStatus sections decode tests; ContractsTests green).
- Sim proofs: the Readiness section healthy; the `.tooNew` state rendered from a seeded
  future-version store file.
