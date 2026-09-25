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

## Scope

- **In:** the transcription status through the wire adapter; the Arrival badge shows the existing FAILED idiom for `import_failed`; the fence from the producer through the wire adaptation to the rendered badge; the rig case at 1440 and 393.
- **Out:** a new badge, a new word, a Retry verb; everything the phase status lists as out.

## Acceptance criteria

- [x] The wire adapter carries the transcription status (`web/src/desk/api.ts:463`); a meeting with `import_failed` reaches the face with that status. **Paid as corrected by Astra:** the status travels as `intel_status`, and the adapter already carried it (`api.ts:498`); proved by the fence link (2) (`web/src/desk/chair/__tests__/importFailedBadge.philo601.test.tsx`), green on base and branch. No adapter change.
- [x] The Arrival badge for an `import_failed` meeting is the existing FAILED idiom (the same species and word as the failed intel job at `ChairHome.tsx:265`). No new word. No canvas. (`web/src/desk/chair/intelBadge.ts:26`.)
- [x] `import_failed` does not become SAVED: it is mapped to FAILED (`intelBadge.ts:26`) and the covered-states table in the vitest names the eleven states the badge maps. **Narrowed in round 2 (Astra's check on built, finding 2):** this box does NOT claim that no state falls to SAVED silently. `importing`, `refused` and `live` still fall back to SAVED (`intelBadge.ts`, `map[s] ?? "SAVED"`): inherited holes, assigned in BACKLOG "PHILO-6 follow-ups" row 1.
- [x] **Round 2 — the expanded row names what failed** (Astra's check on built, finding 2: the FAILED badge also opens the status well, headed `SUMMARY`, so the row read `SUMMARY · FAILED` for a failed import). The well head reads `IMPORT` for `import_failed` and the cause line is the import worker's (`intel_status_detail`); a summary failure keeps `SUMMARY` (`web/src/desk/chair/ChairHome.tsx:2176-2181,2237`). Existing species (the status well, the FAILED idiom, the `LAST ERROR ·` fact); no new word beyond the head noun. Fence: the complete rendered row (badge FAILED + well head IMPORT + the import's cause + no `SUMMARY`) (`web/src/desk/chair/__tests__/importFailedRow.philo601r2.test.tsx`), red on a `git archive f6c0c0d1` copy (`expected 'SEP 24Architecture boundary review — …' to contain 'IMPORT'`, `Received: "…FAILEDSUMMARYFAILED"`), green on the branch (`docs/internal/philo/phase-6/badge/round-2/`). Rig re-shot: `assets/story-01-shots/20260925T035149Z-…-1440` and `20260925T035156Z-…-393`, both VERDICT pass (`'IMPORT' is readable`; the badge FAILED is a setup check on the same evaluator).
- [x] **Round 3 — the import cause is a short class, never the worker's temp file** (Astra's round-two check, finding 3; UX-CANON A.3). Round two's well showed a paragraph naming `TMPLYES_VQF.VTT`, the worker's temp file. Fixed at the producer: every import failure carries a short `cause` (`holdspeak/meeting_import.py` `MeetingImportError`, `holdspeak/transcript_parse.py` `TranscriptParseError`, 17 raises classed: `NO TRANSCRIPT LINES`, `EMPTY OR BINARY FILE`, `NOT A WEBVTT FILE`, `UNSUPPORTED TYPE`, `FFMPEG NOT INSTALLED`, `AUDIO DID NOT DECODE`, `AUDIO TOO SHORT`, `NO SPEECH FOUND`, `FILE NOT FOUND`, `FILE NOT READABLE`); the worker stores the cause as `intel_status_detail` and logs the full message (`holdspeak/services/meeting_service.py:318-326`; an unexpected exception stores `UNEXPECTED ERROR`). No file name in the cause: the row's title already carries the file's stem (`meeting_service.py:190`). The face is unchanged (`ChairHome.tsx:2181`): `LAST ERROR · NO TRANSCRIPT LINES` (31 chars). Fences: `tests/unit/test_philo6_01_import_badge.py::test_the_import_cause_is_short_and_names_no_temp_file` (red on a `git archive 27ee9559` copy: `No cues could be parsed from tmp9zn5e812.vtt. …`) and the rendered `importFailedRow.philo601r2.test.tsx` (red on the round-two fixture: `Received: "LAST ERROR · No cues could be parsed from upload.vtt. …"`); green on the branch (`docs/internal/philo/phase-6/brief/round-3/`). Rig re-run: `assets/story-01-shots/20260925T043228Z-…-1440` and `20260925T043240Z-…-393`, both VERDICT pass; the observation's API reads record `intel_status.detail = NO TRANSCRIPT LINES`; both after.png viewed: `FAILED  LAST ERROR · NO TRANSCRIPT LINES` under `IMPORT`. The trigger is an INSPECTION AFTER SCROLL, not an owner-action transition (Astra's ruling; the case's `words` say so).
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
- 2026-09-24 night — ROUND 2 after Astra's check on built (BOUNCE; `checks/lane-a-built-astra.md`): the expanded well names the import (`IMPORT`, the import's cause); the "unmapped states" box narrowed to what is true, the holes in BACKLOG "PHILO-6 follow-ups"; the retracted adapter diagnosis removed from the Problem (the correction note stays). The rig case now observes the well head (`readable_text IMPORT`) with the badge as a setup check; its trigger is the pointer on the well head (the rig has no scroll verb; at 393 the open well sits below the sticky capture bar; the head has no handler). Reds and greens: `docs/internal/philo/phase-6/badge/round-2/`. Parked runs: `assets/story-01-shots/attempts/README.md`.
- 2026-09-24 night — ROUND 3 after Astra's round-two check (BOUNCE; `checks/lane-a-built-astra.md` "Round two"): the import cause is a short class at the producer (no temp name, no path, no sentence); the integration pins re-pointed to the classes (`tests/integration/test_web_transcript_import_api.py`, `test_web_meeting_import_api.py`); the rig case re-run at 1440 and 393 with the trigger stated as an inspection after scroll. Evidence: `evidence-story-01.md` "Round 3".
