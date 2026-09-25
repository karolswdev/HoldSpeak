# PHILO-6-01 - The honest import badge

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** done
- **Depends on:** -
- **Unblocks:** exit 3 (no SAVED on a failed import)
- **Owner:** Muad'Dib (Opus 5.5); Astra checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", the failed-import row (ledger row 3); Astra's check of the drafts, finding 2 row 1
- **Canvas:** none (the existing FAILED idiom)

## Problem

**Diagnosis corrected by Astra's charter check (2026-09-24 night; retracting its own earlier adapter finding):** the producer writes `intel_status` (`meeting_service.py:335`), NOT `transcription_status`; the wire adapter already adapts both its string and nested `.state` forms (`api.ts:498`); `ChairHome.tsx:266` passes it to `intelBadge`, whose fallback (`intelBadge.ts:26`) returns SAVED for `import_failed`. The retained observation `phase-5-…/assets/story-03-shots/none/browser/20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440/observation.json:126` shows `intel_status.state=import_failed` with `transcription_status=active`. The repair is the badge mapping (FAILED for `import_failed`), fenced producer → adapter → rendered badge; NO transcription-field change and NO adapter repair.


A failed import shows SAVED on the Arrival. The producer marks it: `MeetingService` sets the transcription status `import_failed` (`holdspeak/services/meeting_service.py:315`). Then the face loses it in two places:

- The wire adapter `fromWireMeeting` (`web/src/desk/api.ts:463`) drops the transcription status, so the Meeting the face holds never carries `import_failed`.
- `arrivalIntelBadge` (`web/src/desk/chair/ChairHome.tsx:258-266`) knows only the intel job states (`:265` returns FAILED for a failed job); at `:266` it hands over to `intelBadge(meeting.intelStatus)`, and `intelBadge` returns SAVED for every state it does not map (`web/src/desk/chair/intelBadge.ts:26`).

A change to the helper alone cannot repair the face (Astra, finding 2): the status never reaches it.

## Scope

- **In:** the transcription status through the wire adapter; the Arrival badge shows the existing FAILED idiom for `import_failed`; the fence from the producer through the wire adaptation to the rendered badge; the rig case at 1440 and 393.
- **Out:** a new badge, a new word, a Retry verb; everything the phase status lists as out.

## Acceptance criteria

- [x] The wire adapter carries the transcription status (`web/src/desk/api.ts:463`); a meeting with `import_failed` reaches the face with that status. **Paid as corrected by Astra:** the status travels as `intel_status`, and the adapter already carried it (`api.ts:498`); proved by the fence link (2) (`web/src/desk/chair/__tests__/importFailedBadge.philo601.test.tsx`), green on base and branch. No adapter change.
- [x] The Arrival badge for an `import_failed` meeting is the existing FAILED idiom (the same species and word as the failed intel job at `ChairHome.tsx:265`). No new word. No canvas. (`web/src/desk/chair/intelBadge.ts:26`.)
- [x] Unmapped states do not become SAVED silently: `intelBadge.ts:26` stays SAVED only for a state that is saved; the fence names the states it covers. The covered-states table in the vitest names eleven states; `import_failed` was the one terminal failure state falling to SAVED. Disclosed, not mapped: `importing`, `refused`, `live` (not terminal failures of the import path; `evidence-story-01.md` "Not claimed").
- [x] Fence: producer -> wire adaptation -> rendered badge. The producer link mints the failed import through the real route and worker and holds the vitest fixture equal to that wire (`tests/unit/test_philo6_01_import_badge.py`); the real `fromWireMeeting` adapts it; the rendered Arrival row shows FAILED. Red pre-fix on a `git archive origin/main` copy (`Received: "SAVED"`, `docs/internal/philo/phase-6/badge/red.txt`); green on the branch (`green.txt`).
- [x] Rig: an empty VTT import at 1440 and 393; the Arrival row shows FAILED; shots retained (`assets/story-01-shots/20260925T023753Z-…-1440`, `20260925T023803Z-…-393`, both VERDICT pass).

## Effort (council-style estimate, not a promise)

0.5 day

## Test plan

- **Unit:** a pytest that mints `import_failed` through the real import path and reads the wire JSON; a vitest that adapts that JSON through `fromWireMeeting` and renders the Arrival row (red pre-fix, SAVED; green, FAILED).
- **Integration:** the rig case (an empty VTT import) through `scripts/graph_walk.py` at 1440 and 393, `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 1: the wire adapter drops the status; canvas-free).
- 2026-09-24 night — DONE (Muad'Dib lane, Opus 5.5): the badge mapping only (`intelBadge.ts:26`); fence red on `origin/main`, green on the branch; the rig at 1440 and 393 PASS. Evidence: `evidence-story-01.md`.
