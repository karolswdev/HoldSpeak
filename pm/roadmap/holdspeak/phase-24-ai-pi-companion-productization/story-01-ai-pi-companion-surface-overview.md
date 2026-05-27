# HS-24-01 — AI PI Companion Surface: Read-Only Session Overview

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

Phase 23 made AI PI truthful, but the user still has to infer too much from a
small display, logs, or `/api/companion/status`. The existing HoldSpeak web
portal already owns local runtime visibility for meetings and dictation, so the
AI PI companion should appear there as a first-class surface rather than as a
separate app.

## Outcome

The existing HoldSpeak web portal gets a read-only Companion page that shows
what AI PI currently knows about waiting agent sessions, selected reply target,
delivery confidence, runtime readiness, and blockers.

## Scope

### In

- Add `Companion` to the existing portal navigation.
- Add `/companion` as a built Astro route served by the FastAPI runtime.
- Reuse `/api/companion/status`; do not add mutation APIs yet.
- Show selected target, all waiting sessions, confidence, transport, freshness,
  blockers, and basic AI PI/runtime status.
- Add smoke coverage for the new page.

### Out

- Select/dismiss/pin controls.
- State mutation endpoints.
- Firmware UI changes.
- Push/event transport.

## Acceptance Criteria

- [x] `/companion` renders inside the existing HoldSpeak portal shell.
- [x] The page shows selected target and waiting-session overview from
      `/api/companion/status`.
- [x] The page shows reply readiness and blockers without requiring logs.
- [x] The page is read-only; controls are deferred to HS-24-02.
- [x] Tests/build evidence is recorded before closeout.

## Closeout

Implemented 2026-05-26. See [evidence-story-01.md](./evidence-story-01.md).
