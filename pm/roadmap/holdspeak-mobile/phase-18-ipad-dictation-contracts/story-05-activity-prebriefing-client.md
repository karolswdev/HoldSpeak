# HSM-18-05 — Activity pre-briefing, the source-cited nudge client

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** done — see [`evidence-story-05.md`](./evidence-story-05.md). The nudge cards
  (citations, Dismiss, "Dictate with this" → Armed) on the dictate surface, proven against
  a live hub computing real nudges from a real ledger; plus the hub hole the audit's
  pattern predicted — the remote dictation lane never consumed the Phase-53 selection pin
  (the local runner did) — fixed and test-locked, one-shot semantics preserved.
- **Depends on:** 18-01 (the dictate input the nudge feeds); the hub activity routes
  (`/api/activity/*`, `holdspeak/web/routes/activity/`).
- **Unblocks:** activity-nudge parity on the iPad.
- **Owner:** unassigned

## Problem

Activity pre-briefing has no iPad client at all — the app never calls any `/api/activity/*`
route. The hub serves the full loop (source-cited dismissible nudges; records; briefing; the
"Dictate with this" selection that grounds the next dictation in the picked record). On the
iPad none of it exists, so the user loses the one feature that makes dictation *informed*.

## The design

1. **An activity client** on `HTTPDesktopClient`: `nudges()` (source-cited cards),
   `selectNudge(id:)` (`/api/activity/nudges/select`, the grounding selection),
   `dismissNudge(id:)`, and the `records` / `briefing` reads.
2. **Nudge cards** rendered with their citations (the source chips), each dismissible, each
   with a primary **"Dictate with this"** action that calls `selectNudge` and then opens the
   18-01 dictate screen so the next `/api/dictation/remote` is grounded in the picked record.
   This is the proven Phase-53 loop, ported.
3. **Honest, never autonomous.** A nudge suggests; the user dismisses or acts. The dictate
   that follows carries the egress badge.

## Scope

- **In:** the `HTTPDesktopClient` activity methods; the nudge cards (citations, dismiss,
  "Dictate with this" → select → dictate); the records/briefing panel.
- **Out:** server-side activity ingestion (hub-owned, already shipped); on-device activity
  capture (iOS cannot read desktop activity — `n/a`, document it).
