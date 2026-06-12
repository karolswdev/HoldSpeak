# HS-63-01 — The meeting models

- **Project:** holdspeak
- **Phase:** 63
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-63-02, HS-63-05
- **Owner:** unassigned

## Problem
Five pure dataclasses (Bookmark, TranscriptSegment, IntelSnapshot,
MeetingSaveResult, MeetingState) and their helpers live inside the
1,674-line `meeting_session.py`, entangled with the session machinery.

## Scope
- **In:** `holdspeak/meeting_session/models.py` (the brief planned `holdspeak/meeting/`, but `holdspeak/meeting.py` (MeetingRecorder) owns that name — the module became a package instead, which keeps the import point) — the dataclasses + the module
  helpers they use, moved verbatim; `meeting_session.py` re-exports every
  public name (it stays the canonical import point for the 38 test files
  and all production imports). `holdspeak/meeting/__init__.py`.
- **Out:** MeetingSession itself (HS-63-02); behavior changes.

## Acceptance criteria
- [x] The models live in `holdspeak/meeting/models.py`, bodies verbatim.
- [x] Every existing import keeps working; ZERO test edits.
- [x] Full suite green, count unchanged.

      See `evidence-story-01.md`.

## Test plan
- The full suite is the proof (38 files import these names).
