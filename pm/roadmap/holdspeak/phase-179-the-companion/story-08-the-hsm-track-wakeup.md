# HS-179-08 — The HSM track wake-up

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-01
- **Unblocks:** HS-179-02, HS-179-03
- **Owner:** unassigned

## Problem

The HSM track is dormant. The iPad app under `apple/App/` speaks the
pre-Constitution API: `DeskPrimitive.swift` (15 primitive kinds),
`DeskHome.swift`, `DeskPhysicsCanvas.swift`, and `Sync.swift` (11 sync
kinds) are from before Phase 95 (the Desk OS pivot). The Swift sources
need updating to the current API contract (the Room, the portfolio, the
auth model) before any companion view can be built.

## Scope

- In:
  - Audit the existing Swift sources (`apple/App/`, `apple/Sources/`)
    against the current API contract (the Room sections, the portfolio
    aggregate, the auth header).
  - Update `Sync.swift` to the current sync kind set (or replace with
    the portfolio/Room API client).
  - Update `DeskPrimitive.swift` to the current primitive set (or
    replace with the companion's data model).
  - Remove or archive the 2.5D diorama code
    (`DeskPhysicsCanvas.swift`, `DeskHome.swift`) that the companion
    does not use (the companion is a list/drill-down UI, not the
    diorama).
  - Ensure the Xcode project builds and the SwiftUI previews render
    with seeded data.
- Out:
  - The companion views themselves (HS-179-03, -04, -05 own those).
  - New features.
  - The diorama (retired for the companion; the web desk may revisit
    it separately).

## Acceptance criteria

- [ ] The Xcode project builds with zero errors targeting iOS 17+.
- [ ] The data model matches the current API contract (the Room
      sections, the portfolio aggregate, the auth model).
- [ ] SwiftUI previews render with seeded data.
- [ ] Archived code is removed or moved to a `Legacy/` group (not
      deleted; Article X -- never delete, park instead).

## Test plan

- Unit: Xcode unit tests for the data model parsing.
- Integration: the Swift API client fetches from a running hub.
- Manual: Xcode build succeeds; previews render.

## Notes / open questions

- The standing rule "never delete -- park instead" (memory:
  feedback_never_delete_park_instead.md) applies to the diorama code.
  Move it to a `Legacy/` group, not the trash.
- The `Package.swift` (DOC_AUDIT_2026-08.md:84) references
  `swift test` -- ensure the tests still run after the wake-up.
