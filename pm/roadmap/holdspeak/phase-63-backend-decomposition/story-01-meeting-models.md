# HS-63-01 — The meeting models

- **Project:** holdspeak
- **Phase:** 63
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-63-02, HS-63-05
- **Owner:** unassigned

## Problem
Five pure dataclasses (Bookmark, TranscriptSegment, IntelSnapshot,
MeetingSaveResult, MeetingState) and their helpers live inside the
1,674-line `meeting_session.py`, entangled with the session machinery.

## Scope
- **In:** `holdspeak/meeting/models.py` — the dataclasses + the module
  helpers they use, moved verbatim; `meeting_session.py` re-exports every
  public name (it stays the canonical import point for the 38 test files
  and all production imports). `holdspeak/meeting/__init__.py`.
- **Out:** MeetingSession itself (HS-63-02); behavior changes.

## Acceptance criteria
- [ ] The models live in `holdspeak/meeting/models.py`, bodies verbatim.
- [ ] Every existing import keeps working; ZERO test edits.
- [ ] Full suite green, count unchanged.

## Test plan
- The full suite is the proof (38 files import these names).
