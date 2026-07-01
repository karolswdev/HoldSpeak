# HS-70-04 — Dictation mode, made whole

- **Status:** todo
- **Priority:** MED
- **Depends on:** HS-70-01
- **Evidence:** _(added at close)_

## Goal

The **Dictation** destination cleanly contains the entire dictation mode:
voice typing, the dictation journal, the learning digest + corrections, and
activity pre-briefing. A user in Dictation is not sent hunting across separate
top-level pages for parts of the same mode.

## Scope

- Confirm the Dictation cockpit (`/dictation`, the Phase-54 ES-module surface)
  already carries voice typing + the journal + learning + corrections; fix any
  seam where a piece reads as "elsewhere."
- **Fold `/activity` (activity pre-briefing / nudges) into Dictation.** The
  nudges feed the "Dictate with this" loop (Phase 53), so they belong to the
  dictation mode, not a separate top-level ambient page. Present them as a
  section/sub-view of Dictation. Preserve the Phase-53 selection-pin →
  runner → rewriter behavior byte-for-byte (this is IA, not a pipeline change).
- `/activity` the standalone route redirects into the Dictation surface (no
  404; update the route pre-flight).
- The Dictation empty state (HS-70-07) tells a new user the one move: hold your
  key and speak.
- Naming: canonical names throughout (the dictation journal, the correction
  memory, the learning digest, activity pre-briefing / nudge cards).

## Proof required

Screenshots of Dictation showing all its parts reachable within the one mode
(typing, journal, learning digest, corrections, pre-briefing nudges).
`/activity` redirect proven. The Phase-53 "Dictate with this" loop still works
(the existing dogfood, unchanged output). Empty-state screenshot.

## Done

_(filled at close)_
