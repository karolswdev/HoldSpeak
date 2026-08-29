# HS-147-06 — The record book (docs)

- **Project:** holdspeak
- **Phase:** 147
- **Status:** ready
- **Depends on:** HS-147-01, HS-147-02, HS-147-03, HS-147-04
- **Unblocks:** HS-147-07
- **Owner:** unassigned

## Problem

The dedicated docs story (house law: after features, before
closeout, touching ENTRY points). A cold reader must be able to see
an event on the rail, tap once, and understand what will happen,
what follows the feed, and where the meeting lands.

## Scope

### In

- USER_GUIDE: the one-tap flow in the Calendars/Recording sections —
  RECORD THIS, the ARMED chip, CANCEL?, what happens when the
  meeting moves or is cancelled (the honest follow, in user words),
  where the recorded meeting appears and its origin line. Labels
  quoted from the shipped UI.
- ARCHITECTURE: the event-linked recording pipeline section with
  verified anchors (link columns, arm computation, reconciliation
  R1–R3 + X1, the fire seam carrying provenance).
- The Phase 146 calendar book sections updated where this phase
  changes their truth (snapshot UID determinism; the settings
  editor's IMPORT SCREENSHOT refusal surfacing).
- Entry points (README surface if the feature is pitch-worthy —
  judge honestly), doc-drift guards updated where claims change.
- Voice rules: why-ledes, canonical feature names, no roadmap
  vocabulary in user-facing docs.

### Out

- Internal orchestration docs; the final summary (07).

## Acceptance criteria

1. A cold reader can run the whole loop from the docs alone: see an
   event, arm it, cancel it, find the meeting.
2. Every documented label matches the shipped UI verbatim; anchors
   verified against the merged stories.
3. Doc-drift guards green; zero stale single-behavior claims left
   from before this phase.

## Test plan

`uv run pytest -q tests/ -k doc_drift` (and kin), manual
read-through against live shots from stories 02/04.
