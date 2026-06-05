# HS-41-07 — Closeout

- **Project:** holdspeak
- **Phase:** 41
- **Status:** backlog
- **Depends on:** HS-41-01 … HS-41-06
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 41 closes when presence is proven by real use on both platforms (to the
extent the hardware allows), the focus invariant is verified, and the tracking
docs are reconciled.

## Scope

- In:
  - **Dogfood:** enable presence, dictate, and confirm the surface tracks state
    **and never steals focus** (injected text still lands in the target app).
    Capture macOS (and Linux where a box is available; otherwise structural).
  - Invariant re-verification: flag-off byte-identical; no GUI dep in the default
    suite; bundle rebuilt, only `web/src` committed; PR #17 closed as superseded.
  - `final-summary.md`; README phase row → done + pointer advanced; HANDOVER
    refreshed.
  - Push + open a PR to `main`; merge when CI green.
- Out:
  - New surfaces — closeout is verification + record only.

## Acceptance criteria

- [ ] Real dogfood captured (state tracks; **focus not stolen**).
- [ ] Full suite green; flag-off byte-identity re-asserted; no `_built/` tracked.
- [ ] `final-summary.md` exists; status frozen; README → done; HANDOVER updated;
      PR opened/merged; codex PR #17 closed.
