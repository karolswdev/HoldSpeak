# meeting_import

Job: Import a recording or transcript as a normal Meeting. Baseline: `555728021` (PR1430). Reviewer task name: `review_meeting_import`. Evidence class: source inspection plus existing desk-sweep captures; no new execution or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts in Meetings with Import, a picker, or a file drop (`web/src/pages/cores/HistoryCore.tsx:323-374,419-445,503-529`), then collects metadata in the in-world import well (`web/src/pages/cores/history/ImportSection.tsx:52-70,95-169`). The route validates custody, creates an `importing` row, and returns 202 (`holdspeak/web/routes/meeting_import.py:58-126`; `holdspeak/services/meeting_service.py:225-296`). A worker parses VTT/SRT/TXT or transcribes audio, persists a normal Meeting, and announces completion (`holdspeak/services/meeting_service.py:338-410`; `holdspeak/meeting_import.py:568-652`). Search, detail and export parity exist (`tests/integration/test_meeting_import_parity.py:88-121`).

The audit keeps import separate from live capture and automatic summary. It does not define source/provenance, real-versus-synthetic time, file reacquisition, or a terminal operation receipt. It also leaves unsupported format versus failed intelligence unmapped.

FINDINGS:

1. **Source truth is lost.** `ParsedTranscript` distinguishes real timestamps, but `import_transcript` drops `has_real_timestamps` (`holdspeak/transcript_parse.py:66-70`; `holdspeak/meeting_import.py:803-812`). `MeetingState` has only generic `provenance`; the filename is log-only (`holdspeak/meeting_session/models.py:120-151`; `holdspeak/meeting_import.py:568-652`). The face renders every `start_time` normally (`web/src/pages/cores/history/TranscriptWell.tsx:55-74`). Cost: TXT’s synthetic positions can look factual and the source cannot be identified after return. This fails Tenet 6 and Article VI. Correction: persist `origin=import`, source name/format and `timestamp_basis=real|synthetic`; show it with the existing provenance species, without retaining bytes.

2. **Import recovery is not a complete job.** The form clears the file after 202, while the worker deletes its temporary copy (`web/src/pages/cores/history/ImportSection.tsx:52-70`; `holdspeak/services/meeting_service.py:400-410`). A failed row says `IMPORT FAILED`, but the generic danger branch returns `Retry`, whose click calls `onRunIntelligence` (`web/src/pages/cores/history/helpers.ts:98-110,427-465`; `web/src/pages/cores/history/CatalogRail.tsx:322-354`). Cost: no in-world path reacquires the source, and Retry can mean the wrong operation. This fails Tenets 2, 3 and 6. Correction: give `import_failed` a distinct Re-import/reselect affordance, retain the row, and return to it after retry; keep summary retry separate.

3. **Date semantics contradict one another.** The well pre-fills from a VTT/SRT header, filename, then `File.lastModified` and posts it (`web/src/pages/cores/history/importWhen.ts:1-7,41-53`; `ImportSection.tsx:36-62`), while a retained test expects no `started_at_ms` and the backend supplies its default when no date is sent (`web/src/pages/cores/history/__tests__/importSectionStart.test.tsx:1-5,32-54`; `holdspeak/meeting_import.py:121-132,319-323`). Cost: a copied file can be filed on its filesystem date; the value is already shown and editable, but the audit does not distinguish a suggested date from known meeting time. This fails Tenet 6. Correction: document the current visible, editable file-date suggestion and blank-date fallback, reconcile stale assertions, and label inferred versus supplied time consistently across HTTP, CLI and MCP. Do not add a second confirmation to a clear editable choice.

4. **Receipt coverage is unspecified.** `meeting.import` writes and invokes transcription, but its descriptor has no admission and returns only `{meeting_id,status: importing}` (`holdspeak/operations.py:405-434`; `holdspeak/operations.py:2479-2579`). Cost: the owner cannot inspect one durable terminal outcome for a consequential import. Audit the existing admission/operation boundary and the durable import row, then expose a terminal outcome beside that row. A missing descriptor admission does not by itself prove an authority defect or require a second kernel/approval system (Tenets 1 and 3).

## Convergence

Converge with `meeting_record` on `MeetingState`, the Meetings window, `desk_changed`, and row identity; import is a distinct intake adapter. Converge with `meeting_intelligence` on `MeetingWindow`, `Run summary`, route disclosure and egress (`holdspeak/meeting_import.py:600-639`), and disclose whether summary was automatically queued under the existing setting/consent or waits for a press; `holdspeak/meeting_import.py:628-639` already attempts automatic enqueue. Keep parsing success separate from summary success. Converge with `meeting_archive` on HistoryCore search/detail/export and restoration. `meeting_aftercare` consumes the same meeting id and source-linked segments; it must not own custody. Do not merge these families: capture owns microphone lifecycle, intelligence owns provider work, import owns parsing and custody.

## User experience

The existing 393 capture shows a compact first move: filled Record and adjacent Import (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-meetings-393-Record.png`, 393 viewport). The 1440 capture keeps the grammar (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-meetings-1440-Record.png`). Picker/drop plus one in-world form should suit Tuesday. I did not see import, completion or failure shots; source cannot certify beauty, accessibility, performance or delight. Lost provenance and weak recovery abandon a bad file.

CONDITIONS: Add the four contracts above to the implementation brief, name the first consumers, and capture import form, terminal success/failure, and re-import at 1440 and 393. Do not add a new application or wizard.

MISSED: 1) failed import → re-import and return (highest cost); 2) TXT synthetic timing and VTT/SRT speaker/date provenance; 3) restart during import and owner-only refusal; 4) missing ffmpeg/model failure distinction and the accepted-format matrix.

TUESDAY: A clean known file is likely quick; a failed or date-ambiguous file is not recoverable or trustworthy enough yet.

## Acceptance challenges

1. At 393, import a dated VTT with two named speakers; verify the row reaches terminal state, the record identifies the source and real cue times, then return to Meetings.
2. Import a WAV with a forced transcription failure; verify `IMPORT FAILED`, a distinct Re-import action, no summary retry, and recovery after a hub restart.
3. Import TXT with two lines; verify synthetic timing is labelled, summary follows the disclosed auto/manual policy rather than an invented no-auto rule, and the same Meeting opens after refresh.
4. Try PDF, MP3 without ffmpeg, and a model failure; verify distinct named refusal/failure states, no finished claim for a failed import, a retained failed row only where intake was accepted, and owner-only refusal before file custody.

UNKNOWN: No tests, builds, live walks, provider/native actions, DB rows, or owner acceptance were run in this review. The captures are existing desk-sweep evidence of the Record wing only, not import acceptance.
