# PHILO-6-01 - The honest import badge

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** exit 3 (no SAVED on a failed import)
- **Owner:** Muad'Dib (Opus 5.5); Astra checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", the failed-import row (ledger row 3); Astra's check of the drafts, finding 2 row 1
- **Canvas:** none (the existing FAILED idiom)

## Problem

A failed import shows SAVED on the Arrival. The producer marks it: `MeetingService` sets the transcription status `import_failed` (`holdspeak/services/meeting_service.py:315`). Then the face loses it in two places:

- The wire adapter `fromWireMeeting` (`web/src/desk/api.ts:463`) drops the transcription status, so the Meeting the face holds never carries `import_failed`.
- `arrivalIntelBadge` (`web/src/desk/chair/ChairHome.tsx:258-266`) knows only the intel job states (`:265` returns FAILED for a failed job); at `:266` it hands over to `intelBadge(meeting.intelStatus)`, and `intelBadge` returns SAVED for every state it does not map (`web/src/desk/chair/intelBadge.ts:26`).

A change to the helper alone cannot repair the face (Astra, finding 2): the status never reaches it.

## Scope

- **In:** the transcription status through the wire adapter; the Arrival badge shows the existing FAILED idiom for `import_failed`; the fence from the producer through the wire adaptation to the rendered badge; the rig case at 1440 and 393.
- **Out:** a new badge, a new word, a Retry verb; everything the phase status lists as out.

## Acceptance criteria

- [ ] The wire adapter carries the transcription status (`web/src/desk/api.ts:463`); a meeting with `import_failed` reaches the face with that status.
- [ ] The Arrival badge for an `import_failed` meeting is the existing FAILED idiom (the same species and word as the failed intel job at `ChairHome.tsx:265`). No new word. No canvas.
- [ ] Unmapped states do not become SAVED silently: `intelBadge.ts:26` stays SAVED only for a state that is saved; the fence names the states it covers.
- [ ] Fence: producer → wire adaptation → rendered badge. The meeting is minted through the REAL producer (`meeting_service.py:315`, a failed import), its wire JSON is adapted by the real `fromWireMeeting`, and the rendered Arrival row shows FAILED. Red pre-fix on a `git archive origin/main` copy (today: SAVED). A hand-written wire object that already carries the field proves nothing.
- [ ] Rig: an empty VTT import (the story-03 glass review's case) at 1440 and 393; the Arrival row shows FAILED; shots retained.

## Effort (council-style estimate, not a promise)

0.5 day

## Test plan

- **Unit:** a pytest that mints `import_failed` through the real import path and reads the wire JSON; a vitest that adapts that JSON through `fromWireMeeting` and renders the Arrival row (red pre-fix, SAVED; green, FAILED).
- **Integration:** the rig case (an empty VTT import) through `scripts/graph_walk.py` at 1440 and 393, `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 1: the wire adapter drops the status; canvas-free).
