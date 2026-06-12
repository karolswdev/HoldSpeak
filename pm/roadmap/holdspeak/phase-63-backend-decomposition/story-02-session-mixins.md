# HS-63-02 — MeetingSession mixins

- **Project:** holdspeak
- **Phase:** 63
- **Status:** done
- **Depends on:** HS-63-01
- **Unblocks:** HS-63-05
- **Owner:** unassigned

## Problem
MeetingSession mixes the transcribe loop, intel analysis, persistence,
and item/title/tag mutations with its lifecycle in one 1,400-line class.

## Scope
- **In:** `holdspeak/meeting_session/` (the HS-63-01 package) gains `transcribe_loop.py` (the loop +
  overlap + chunk transcription), `intel_analysis.py` (the intel cadence +
  analysis + bookmark refinement), `persistence.py` (save), and
  `mutations.py` (action items, title, tags) as mixin classes with
  verbatim bodies; `meeting_session.py` keeps __init__, lifecycle
  (start/stop/bookmarks), device attach, and broadcasts, composing the
  mixins; lands under the guard budget.
- **Out:** WebRuntime (HS-63-03/04); behavior changes.

## Acceptance criteria
- [x] Each mixin is single-concern and under budget; bodies verbatim
      (locks travel with their methods).
- [x] `meeting_session.py` is the thin lifecycle + assembly module.
- [x] ZERO test edits (no monkeypatched globals exist on this module);
      full suite green.

      See `evidence-story-02.md`.

## Test plan
- The full suite; the meeting/intel/diarization slices read specifically.
