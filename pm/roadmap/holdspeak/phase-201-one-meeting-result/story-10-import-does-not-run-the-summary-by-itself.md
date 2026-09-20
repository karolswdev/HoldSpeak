# HS-201-10 - Import does not run the summary by itself

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** Fedaykin (lane B, wt-201-b)

## Problem

Import runs the summary by itself: holdspeak/meeting_import.py:362-378 enqueues an intel job with only a transcript hash, no route bundle, no selection hash. The rehearsal saw contact with 192.168.1.43 before any gesture, `run_receipt: null`, and no "Run summary" verb ever rendered, so the disclosure contract of stories 03 and 04 is unreachable on the only path a stranger without a microphone can take. Also from Import: `1 MIN` for a 2.79 s file beside `5 S`; the meeting dated by the file's mtime (JUN 03, web/src/meetings/ImportSection.tsx:38); `transcription_status` stuck at `active` after a final transcript. Article III at the point of decision; Article VI; tenet 3.

## Scope

- **In:** Import transcribes and stops; it enqueues no summary; the meeting shows "Run summary" with its disclosed route like a recorded meeting; a fence proves no provider contact after Import without a gesture; the row length is truthful in seconds or minutes as fits; an imported meeting is dated now (its start is the import moment; the file date shown as a fact if wanted); `transcription_status` reaches its final state.
- **Out:** the Record path (fenced by lane A); auto-summary as a setting (parked).

## Acceptance criteria

- [x] Isolated HOME with an engine assigned: Import a WAV → transcript saved, NO intel job, NO provider contact (fence red first on today's code), "Run summary" rendered with the planned host.
- [x] Click Run summary → the receipt names the host; the summary renders (the existing story-04 rig extended to the Import path).
- [x] Row length truthful for a 3 s file; date is today; `transcription_status` final.
- [x] Shots at 1440 and 393 in assets/story-10-shots/.

## Test plan

- **Unit:** pytest on meeting_import (no enqueue), on status finalisation; vitest on the length token and the date.
- **Integration:** the e2e above.
- **Manual / device:** shots.

## Notes / open questions

Lane B (Opus). Files: holdspeak/meeting_import.py, holdspeak/meeting_session/** only where status finalisation lives, web/src/meetings/ImportSection.tsx, web/src/pages/cores/history/helpers.ts (length token). Do not touch the Concierge or ChairHome.tsx.

## Delivery

- `holdspeak/meeting_import.py:94` `_import_moment()` (the start is the import
  moment, never the file's mtime) and `:346` `_persist_import` (no enqueue; the
  `disabled` summary state the ledger draws `Run summary` on;
  `transcription_status` reaches `complete`, the constant at `:68`).
- `holdspeak/commands/import_recording.py:63`, `:101` — the CLI says `Summary:`
  and no longer claims a queued run.
- `web/src/pages/cores/history/helpers.ts:130` `durationToken` (`3 S`, not
  `1 MIN`); `web/src/pages/cores/history/MeetingHeader.tsx:29` (the `|| "1 MIN"`
  floor removed); `web/src/pages/cores/history/ImportSection.tsx:39` and
  `web/src/desk/components/GlassDropLayer.tsx:79` — neither Import door sends
  the file's mtime any more.
- Fences: `tests/unit/test_hs201_import_no_auto_summary.py` (six, all red first),
  `tests/e2e/test_hs201_summary_producer_chain.py` (the import leg, `stub` and a
  real `lan` run on 192.168.1.43),
  `tests/e2e/test_hs201_summary_face_glass.py` (the browser walk through the
  Import door), `web/src/pages/cores/history/__tests__/importLengthAndDate.test.tsx`
  and `.../importSectionStart.test.tsx`, plus the census pin at
  `tests/unit/test_phase143_intel_queue_inventory.py:121` (import is no longer an
  enqueue writer).
- Shots: `assets/story-10-shots/import-row-length-{1440,393}.png`,
  `import-done-{1440,393}.png`, `import-after-run-{1440,393}.png`.

Not covered: the RECORD path's own `transcription_status` still rests at
`active` after Stop (out of scope — lane A fences Record), and
`services/sync_service.py:371` still collapses any non-`record_only`
transcription state to `active` on sync ingest, so a synced import would lose
the `complete` word.
