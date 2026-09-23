# Evidence - PHILO-2-05

- **Story:** PHILO-2-05 - The live pass, Astra
- **Status:** done
- **Date:** 2026-09-22

## Proof

### Captured run — 2026-09-23T02:58:50Z

- **Command:** `zsh -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --extra dev --extra test pytest -q tests/unit/test_graph_walk_calibration.py 2>&1 | tee docs/internal/philo/graph/astra-inputs/calibration-tests.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 55e86372fba214fd8b7f190583640ed68b7c17df

```text
..............................................................           [100%]
62 passed in 95.07s (0:01:35)
```

### Captured run — 2026-09-23T03:01:08Z

- **Command:** `zsh -c HOME=$(mktemp -d) uv run --extra dev --extra test python scripts/philo_graph_validate.py docs/internal/philo/graph/live-astra.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 55e86372fba214fd8b7f190583640ed68b7c17df

```text
OK docs/internal/philo/graph/live-astra.json
```

### Captured run — 2026-09-23T03:01:08Z

- **Command:** `python3 docs/internal/philo/graph/astra-inputs/verify-live-astra.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 55e86372fba214fd8b7f190583640ed68b7c17df

```text
OK 96 raw runs match graph rows and provenance; input hashes match; original atlas and rig unchanged; runtime atlas has only 7 authorized address resolutions.
OK all 73 cases and applicable viewport slots accounted for; J1–J11 precede beyond; J6 real and other runs non-real; 2 incident runs retained and excluded, with complete serial replacements. Raw verdicts: {'pass': 40, 'fail': 7, 'blocked': 48, 'not_run': 1}
```

### Captured run — 2026-09-23T03:01:53Z

- **Command:** `python3 -c from pathlib import Path; report = Path("docs/internal/philo/graph/live-astra.md").read_text(); print("## JOBS" + report.split("## JOBS", 1)[1].split("## COVERAGE", 1)[0])`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 55e86372fba214fd8b7f190583640ed68b7c17df

```text
## JOBS

**J1 — Get past the gate: PARTIAL — typed/deferred paths PASS; voice BLOCKED.** Expected: Reach the Desk, or keep the dictated words with a receipt. Observed: Continue later reaches the Desk at 1440 and 393. Typing one sentence and saving produces a 201 note row and opens First dictation; Keep as a note shows its receipt at both widths. The draft-custody rig FAIL is a stale gate-text assertion after navigation, not observed text loss. The speech-ready PASS checks assigned only. Browser voice and its failure states block at unsupported boundary adapters; no spoken result or restart custody is claimed.

Runs: [20260923T014303Z-case.j1.first_words_continue_later.idle-astra-1440](observations/astra/20260923T014303Z-case.j1.first_words_continue_later.idle-astra-1440/observation.json); [20260923T014347Z-case.j1.first_words_continue_later.idle-astra-393](observations/astra/20260923T014347Z-case.j1.first_words_continue_later.idle-astra-393/observation.json); [20260923T014513Z-case.j1.first_words_continue_later.draft_custody-astra-1440](observations/astra/20260923T014513Z-case.j1.first_words_continue_later.draft_custody-astra-1440/observation.json); [20260923T014604Z-case.j1.first_words_continue_later.draft_custody-astra-393](observations/astra/20260923T014604Z-case.j1.first_words_continue_later.draft_custody-astra-393/observation.json); [20260923T014650Z-case.j1.speech_readiness.ready-astra-1440](observations/astra/20260923T014650Z-case.j1.speech_readiness.ready-astra-1440/observation.json); [20260923T014703Z-case.j1.first_words_speak.kept-astra-1440](observations/astra/20260923T014703Z-case.j1.first_words_speak.kept-astra-1440/observation.json); [20260923T014732Z-case.j1.first_words_speak.kept-astra-393](observations/astra/20260923T014732Z-case.j1.first_words_speak.kept-astra-393/observation.json); [20260923T014747Z-case.j1.first_words_keep_as_note.kept-astra-1440](observations/astra/20260923T014747Z-case.j1.first_words_keep_as_note.kept-astra-1440/observation.json); [20260923T014757Z-case.j1.first_words_keep_as_note.kept-astra-393](observations/astra/20260923T014757Z-case.j1.first_words_keep_as_note.kept-astra-393/observation.json); [20260923T014812Z-case.j1.first_words_speak.permission_denied-astra-1440](observations/astra/20260923T014812Z-case.j1.first_words_speak.permission_denied-astra-1440/observation.json); [20260923T014822Z-case.j1.first_words_speak.permission_denied-astra-393](observations/astra/20260923T014822Z-case.j1.first_words_speak.permission_denied-astra-393/observation.json); [20260923T014831Z-case.j1.first_words_speak.unreachable_hub-astra-1440](observations/astra/20260923T014831Z-case.j1.first_words_speak.unreachable_hub-astra-1440/observation.json); [20260923T014840Z-case.j1.first_words_speak.unreachable_hub-astra-393](observations/astra/20260923T014840Z-case.j1.first_words_speak.unreachable_hub-astra-393/observation.json); [20260923T014851Z-case.j1.first_words_speak.mic_unsupported-astra-1440](observations/astra/20260923T014851Z-case.j1.first_words_speak.mic_unsupported-astra-1440/observation.json); [20260923T014900Z-case.j1.first_words_speak.mic_unsupported-astra-393](observations/astra/20260923T014900Z-case.j1.first_words_speak.mic_unsupported-astra-393/observation.json)

**J2 — See what the Desk asks of me: PARTIAL — observed summary-only row; variants BLOCKED.** Expected: One truthful SETUP row; the headline counts needs, not offers. Observed: The visible No engine for summaries row is observed at both widths. The speech.transcribe task override is assigned to a migrated Whisper profile, but its binding readiness is unavailable; the separate speech_recognition group row has no assignment. This proves the face text and assignment-presence state, not speech health. The both-missing recipe never removes the existing speech assignment, so its two FAIL verdicts do not establish a false product row. The summary-only variant sends an invalid assignment payload; read-error and pending variants require unsupported route_failure adapters. The full truth table is unverified.

Runs: [20260923T014914Z-case.j2.arrival_load.engines_both_missing-astra-1440](observations/astra/20260923T014914Z-case.j2.arrival_load.engines_both_missing-astra-1440/observation.json); [20260923T014949Z-case.j2.arrival_load.engines_both_missing-astra-393](observations/astra/20260923T014949Z-case.j2.arrival_load.engines_both_missing-astra-393/observation.json); [20260923T015104Z-case.j2.arrival_load.summary_missing_only-astra-1440](observations/astra/20260923T015104Z-case.j2.arrival_load.summary_missing_only-astra-1440/observation.json); [20260923T015113Z-case.j2.arrival_load.summary_missing_only-astra-393](observations/astra/20260923T015113Z-case.j2.arrival_load.summary_missing_only-astra-393/observation.json); [20260923T015124Z-case.j2.arrival_load.read_unknown-astra-1440](observations/astra/20260923T015124Z-case.j2.arrival_load.read_unknown-astra-1440/observation.json); [20260923T015133Z-case.j2.arrival_load.read_unknown-astra-393](observations/astra/20260923T015133Z-case.j2.arrival_load.read_unknown-astra-393/observation.json); [20260923T015144Z-case.j2.arrival_load.read_pending-astra-1440](observations/astra/20260923T015144Z-case.j2.arrival_load.read_pending-astra-1440/observation.json); [20260923T015154Z-case.j2.arrival_load.read_pending-astra-393](observations/astra/20260923T015154Z-case.j2.arrival_load.read_pending-astra-393/observation.json)

**J3 — Give the Desk a summary engine: BLOCKED in dedicated cases; real configuration observed during J6.** Expected: Check the address, see READY, assign it for summaries; hide SETUP only if speech is also ready. Observed: The dedicated Check/UI chains have no recorded replay; the assignment-route case sends an invalid request and receives HTTP 400. J6 setup independently shows the production Models flow with Qwen3.6 35B A3B, UD-Q5_K_XL, 192.168.1.43 · LAN, READY, and the summary assignment. That narrower setup observation does not verify J3 refusal, missing-speech, deletion, or unbinding variants.

Runs: [20260923T015218Z-case.j3.route_assignments_set.assigned_ready-astra-1440](observations/astra/20260923T015218Z-case.j3.route_assignments_set.assigned_ready-astra-1440/observation.json); [20260923T020409Z-case.j6.run_summary.intel_queued-astra-1440](observations/astra/20260923T020409Z-case.j6.run_summary.intel_queued-astra-1440/observation.json); [20260923T020457Z-case.j6.run_summary.intel_queued-astra-393](observations/astra/20260923T020457Z-case.j6.run_summary.intel_queued-astra-393/observation.json)

**J4 — Have one meeting on the Desk: BLOCKED for completed meeting.** Expected: Record/Stop or Import produces a completed meeting with its length, no error, and no automatic summary. Observed: Import returns HTTP 202 and meeting 33e5e08c, but the captured after-row is still importing, with duration 0 and segment_count 0. The raw import PASS means accepted upload only. Record start blocks on its audio adapter; Stop has no recording setup and yields no meeting. No-error completion, measured length, and the no-automatic-summary owner contract remain unverified.

Runs: [20260923T015356Z-case.j4.record_start.capture_recording-astra-1440](observations/astra/20260923T015356Z-case.j4.record_start.capture_recording-astra-1440/observation.json); [20260923T015405Z-case.j4.record_start.capture_recording-astra-393](observations/astra/20260923T015405Z-case.j4.record_start.capture_recording-astra-393/observation.json); [20260923T015415Z-case.j4.meeting_stop.capture_finalized-astra-1440](observations/astra/20260923T015415Z-case.j4.meeting_stop.capture_finalized-astra-1440/observation.json); [20260923T015710Z-case.j4.meetings_import.imported-astra-1440](observations/astra/20260923T015710Z-case.j4.meetings_import.imported-astra-1440/observation.json); [20260923T015723Z-case.j4.meeting_stop.transcription_absent-astra-1440](observations/astra/20260923T015723Z-case.j4.meeting_stop.transcription_absent-astra-1440/observation.json); [20260923T015909Z-case.j4.meeting_stop.transcription_absent-astra-393](observations/astra/20260923T015909Z-case.j4.meeting_stop.transcription_absent-astra-393/observation.json); [20260923T020054Z-case.j4.record_only.no_speech_head-astra-1440](observations/astra/20260923T020054Z-case.j4.record_only.no_speech_head-astra-1440/observation.json); [20260923T020108Z-case.j4.record_only.no_speech_head-astra-393](observations/astra/20260923T020108Z-case.j4.record_only.no_speech_head-astra-393/observation.json)

**J5 — Know where the summary will run: BLOCKED.** Expected: The meeting shows the planned host beside Run summary before the click. Observed: Route-disclosure cases have no lawful Check replay. The no-engine face variant cannot reach its meeting/Run selector after import. J6 records a planned LAN route in protocol data and an engine window, but no reviewed shot proves a planned-host label beside the meeting Run summary control before the click.

Runs: [20260923T020136Z-case.j5.meeting_open.no_engine_no_verb-astra-1440](observations/astra/20260923T020136Z-case.j5.meeting_open.no_engine_no_verb-astra-1440/observation.json); [20260923T020205Z-case.j5.meeting_open.no_engine_no_verb-astra-393](observations/astra/20260923T020205Z-case.j5.meeting_open.no_engine_no_verb-astra-393/observation.json)

**J6 — Get the summary: BLOCKED technically; OWNER USEFULNESS UNVERIFIED.** Expected: The real LAN engine runs; the executed host and summary text are recorded; technical completion and owner usefulness are separate. Observed: TECHNICAL: the real LAN address was checked/configured and a queued job was observed. The first queue run logged a missing openai package; the declared test extra was then installed. Running/ready recipes block on a duplicate HTTP 409 already-queued request; summary-text and host-named recipes block at their Run control. The no-transcript refusal returns HTTP 409 correctly; the no-assignment recipe reaches that same earlier refusal and fails its needs_attention predicate. No terminal summary text, verbatim live transcript, or executed-host receipt was captured. OWNER USEFULNESS: unverified independently of technical completion. The unchanged fixture is a pangram, not an architect meeting; its source phrase is not a live transcript, and it lacks the expected HOLDSPEAK-SYNTH-1 token. No summary text exists in this evidence to quote or assess.

Runs: [20260923T020409Z-case.j6.run_summary.intel_queued-astra-1440](observations/astra/20260923T020409Z-case.j6.run_summary.intel_queued-astra-1440/observation.json); [20260923T020457Z-case.j6.run_summary.intel_queued-astra-393](observations/astra/20260923T020457Z-case.j6.run_summary.intel_queued-astra-393/observation.json); [20260923T020613Z-case.j6.run_summary.intel_running-astra-1440](observations/astra/20260923T020613Z-case.j6.run_summary.intel_running-astra-1440/observation.json); [20260923T020712Z-case.j6.run_summary.intel_ready-astra-1440](observations/astra/20260923T020712Z-case.j6.run_summary.intel_ready-astra-1440/observation.json); [20260923T020804Z-case.j6.run_summary.intel_failed-astra-1440](observations/astra/20260923T020804Z-case.j6.run_summary.intel_failed-astra-1440/observation.json); [20260923T020847Z-case.j6.run_summary.intel_failed-astra-393](observations/astra/20260923T020847Z-case.j6.run_summary.intel_failed-astra-393/observation.json); [20260923T020908Z-case.j6.run_summary.intel_retry-astra-1440](observations/astra/20260923T020908Z-case.j6.run_summary.intel_retry-astra-1440/observation.json); [20260923T020948Z-case.j6.route_intelligence_run.refusal-astra-1440](observations/astra/20260923T020948Z-case.j6.route_intelligence_run.refusal-astra-1440/observation.json); [20260923T021023Z-case.j6.route_intelligence_run.no_assignment-astra-1440](observations/astra/20260923T021023Z-case.j6.route_intelligence_run.no_assignment-astra-1440/observation.json); [20260923T021638Z-case.j6.run_summary.summary_text-astra-1440](observations/astra/20260923T021638Z-case.j6.run_summary.summary_text-astra-1440/observation.json); [20260923T021743Z-case.j6.run_summary.summary_text-astra-393](observations/astra/20260923T021743Z-case.j6.run_summary.summary_text-astra-393/observation.json); [20260923T021848Z-case.j6.run_summary.host_named-astra-1440](observations/astra/20260923T021848Z-case.j6.run_summary.host_named-astra-1440/observation.json)

**J7 — Find it again after a restart: BLOCKED before invocation.** Expected: The same summary is retained and can be found in at most two moves after hub restart. Observed: Both recipes need a successful provider reply for the fixture meeting outside J6, but the atlas supplies neither the replay boundary nor a recorded reply. No synthetic retained summary was inserted. Restart persistence and two-move retrieval remain unexercised.

Runs: None; preflight block or declared unreachable.

**J8 — Type by voice into another app: UNEXERCISED — declared unreachable.** Expected: Hold Option-R, speak, release; words appear at the other application cursor. Observed: The atlas requires a native focused-application harness; the browser rig cannot press the global chord or write to another app. The lane forbids microphone/native keystroke workarounds. No delivered words are claimed.

Runs: None; preflight block or declared unreachable.

**J9 — Open what the Desk remembered: PARTIAL — sweep and Open PASS; doorless/recovery variants BLOCKED.** Expected: A real sweep produces its receipt; Desk memory Open reaches Rhythm; a doorless receipt has no Open. Observed: The real scheduler produces a new SWEEP pipeline receipt; its clock provenance records a 10-second wait and one conductor tick, with no clock move. Run now also produces the expected receipt. Desk memory shows SWEEP and Open reaches Rhythm at 1440 and 393. The doorless case requires an unsupported remote_origin_call adapter; stale/acknowledge/dismiss/restore variants lack recorded provider replies. A separate product finding records Rhythm UTC-like HH:MM times beside the Desk local clock without a zone. The initial scheduler sweep does not verify a subsequent interval branch.

Runs: [20260923T022155Z-case.j9.timer_sweep.receipt_resolved-astra-1440](observations/astra/20260923T022155Z-case.j9.timer_sweep.receipt_resolved-astra-1440/observation.json); [20260923T022223Z-case.j9.route_run_now.receipt_resolved-astra-1440](observations/astra/20260923T022223Z-case.j9.route_run_now.receipt_resolved-astra-1440/observation.json); [20260923T022236Z-case.j9.shade_open.door_present-astra-1440](observations/astra/20260923T022236Z-case.j9.shade_open.door_present-astra-1440/observation.json); [20260923T022253Z-case.j9.shade_open.door_present-astra-393](observations/astra/20260923T022253Z-case.j9.shade_open.door_present-astra-393/observation.json); [20260923T022312Z-case.j9.shade_receipt_open.rhythm_face-astra-1440](observations/astra/20260923T022312Z-case.j9.shade_receipt_open.rhythm_face-astra-1440/observation.json); [20260923T022332Z-case.j9.shade_receipt_open.rhythm_face-astra-393](observations/astra/20260923T022332Z-case.j9.shade_receipt_open.rhythm_face-astra-393/observation.json); [20260923T022350Z-case.j9.shade_open.door_absent-astra-1440](observations/astra/20260923T022350Z-case.j9.shade_open.door_absent-astra-1440/observation.json); [20260923T022409Z-case.j9.shade_open.door_absent-astra-393](observations/astra/20260923T022409Z-case.j9.shade_open.door_absent-astra-393/observation.json); [20260923T022437Z-case.j9.shade_acknowledge.acknowledged-astra-1440](observations/astra/20260923T022437Z-case.j9.shade_acknowledge.acknowledged-astra-1440/observation.json); [20260923T022456Z-case.j9.shade_acknowledge.acknowledged-astra-393](observations/astra/20260923T022456Z-case.j9.shade_acknowledge.acknowledged-astra-393/observation.json); [20260923T022518Z-case.j9.shade_dismiss.dismissed-astra-1440](observations/astra/20260923T022518Z-case.j9.shade_dismiss.dismissed-astra-1440/observation.json); [20260923T022537Z-case.j9.shade_dismiss.dismissed-astra-393](observations/astra/20260923T022537Z-case.j9.shade_dismiss.dismissed-astra-393/observation.json); [20260923T022551Z-case.j9.route_presentation_restore.restored-astra-1440](observations/astra/20260923T022551Z-case.j9.route_presentation_restore.restored-astra-1440/observation.json)

**J10 — Get a brief, and another: PARTIAL — empty/same-day/reload PASS; populated/shelf BLOCKED; next day UNEXERCISED.** Expected: Generate displays the brief; reload and Generate again retain the returned brief; next day produces the appropriate new result. Observed: No brief yet, Generate, and reload show the empty brief at both widths. The serial same-day replacements hold their full 180-second bounds; direct inspection confirms returned IDs equal retained IDs, not just equal headline text. The separate protocol case and both retained-after-reload protocol runs agree. Populated and shelf acknowledge/defer/refuse recipes all stop on the real POST /api/decisions closure error (HTTP 500) before their intended trigger; this is a decision-route defect, not a failed Generate result. People state is unavailable as declared. Load-failure adapters are absent; next-day clock advance is unreachable. The two incident runs are preserved and excluded from serial proof.

Runs: [20260923T022613Z-case.j10.brief_latest.absent-astra-1440](observations/astra/20260923T022613Z-case.j10.brief_latest.absent-astra-1440/observation.json); [20260923T022631Z-case.j10.brief_latest.absent-astra-393](observations/astra/20260923T022631Z-case.j10.brief_latest.absent-astra-393/observation.json); [20260923T022649Z-case.j10.arrival_generate_brief.populated-astra-1440](observations/astra/20260923T022649Z-case.j10.arrival_generate_brief.populated-astra-1440/observation.json); [20260923T022704Z-case.j10.arrival_generate_brief.populated-astra-393](observations/astra/20260923T022704Z-case.j10.arrival_generate_brief.populated-astra-393/observation.json); [20260923T022719Z-case.j10.arrival_generate_brief.generated_empty-astra-1440](observations/astra/20260923T022719Z-case.j10.arrival_generate_brief.generated_empty-astra-1440/observation.json); [20260923T022737Z-case.j10.arrival_generate_brief.generated_empty-astra-393](observations/astra/20260923T022737Z-case.j10.arrival_generate_brief.generated_empty-astra-393/observation.json); [20260923T022755Z-case.j10.arrival_reload.reload_persisted-astra-1440](observations/astra/20260923T022755Z-case.j10.arrival_reload.reload_persisted-astra-1440/observation.json); [20260923T022817Z-case.j10.arrival_reload.reload_persisted-astra-393](observations/astra/20260923T022817Z-case.j10.arrival_reload.reload_persisted-astra-393/observation.json); [20260923T022840Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440 [EXCLUDED: overlap/interrupted]](observations/astra/20260923T022840Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440/observation.json); [20260923T023002Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393 [EXCLUDED: overlap/interrupted]](observations/astra/20260923T023002Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393/observation.json); [20260923T023227Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440](observations/astra/20260923T023227Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440/observation.json); [20260923T023602Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393](observations/astra/20260923T023602Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393/observation.json); [20260923T023923Z-case.j10.route_generate_again.same_day_same_id-astra-1440](observations/astra/20260923T023923Z-case.j10.route_generate_again.same_day_same_id-astra-1440/observation.json); [20260923T023953Z-case.j10.arrival_generate_again.retained_after_reload-astra-1440](observations/astra/20260923T023953Z-case.j10.arrival_generate_again.retained_after_reload-astra-1440/observation.json); [20260923T024014Z-case.j10.arrival_generate_aga
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

## Seal scope and ledger

This evidence seals Astra's independent live audit at source
`f575a5829b179548a2729dd58eb291f7d812b8c7`. The graph and report are
`docs/internal/philo/graph/live-astra.json` and `live-astra.md`. There are
96 immutable raw records, 102 PNGs, 59 invoked atlas cases, 12 cases blocked
before invocation, and 2 declared unreachable. Raw verdicts are 40 pass,
7 fail, 48 blocked and 1 interrupted. The report separates these raw predicates
from J1–J11 owner outcomes and lists every unexercised case and state reason.

The schema/atlas fence previously collected and passed 63 tests; its actual
collection and run output ships under `graph/astra-inputs/`. The 62 calibration
tests, final graph validator, artifact consistency check and complete JOBS block
are captured above. No full-product-suite green claim is made.

J6 uses the real LAN address with the explicitly authorized seven `/v1` address
resolutions. Its configured engine identity is recorded, but no terminal summary
text or executed-host receipt was captured. Technical completion and owner
usefulness remain separately unverified. The declared test extra paid a missing
openai dependency after the first attempt; that attempt is preserved.

A J10 worker incorrectly treated an orchestration wrapper return as rig exit
and briefly ran two own hubs. Astra stopped the phone invocation and reran both
widths serially. Both original records remain unchanged and excluded from
strict serial proof; the interrupted raw record remains incomplete. The
incident ledger names the exact runs, process evidence and replacements.

The pass has 3 product findings and 9 tooling gaps, ranked by owner cost and
assigned to PHILO-2-06 for adjudication; repairs belong to its authorized
follow-up/Phase 3 scope. Product source, shared atlas, rig, and Phase 1 metadata
are unchanged. The owner's DB, keychain, microphone, and native keyboard were
not used. Incidental shared-tracker/process-metadata exposure is disclosed in
the report and not used as evidence.

The owner lane instruction and all-four-seals rule defer Muad'Dib's check to
PHILO-2-06. This story completion means independent audit delivery, not other-
brain ratification, merge approval, or successful completion of all owner jobs.
