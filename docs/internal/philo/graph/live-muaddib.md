# Live pass — Muad'Dib (PHILO-2-04)

PASS: live
BRAIN: muaddib (worker: Opus 5.5; held for SHIP, not committed)
SOURCE: f575a5829b179548a2729dd58eb291f7d812b8c7, dirty=true (untracked: this lane's brief file and the observation directories only; no tracked file changed)
CONTRACT: brief `docs/internal/philo/briefs/graph-audit-brief.md` sha256 ba5477fd07db…; lane brief `live-pass-lane-brief.md`; schema `graph.schema.json` sha256 bddbdcfac56b…; atlas `atlas.json` sha256 64af1de4364c… (73 cases, 71 applicable); rig `scripts/graph_walk.py` 1.1.0
RUNTIME: frontend build `index-BNDgWxUD.js` (index sha256 f872c6384eb2…), built once before the first run; one rig hub per run on 127.0.0.1 in a fresh mkdtemp HOME, database `<run HOME>/.local/share/holdspeak/holdspeak.db` verified under that HOME in every observation; clock = the real clock, no clock moved (`scheduler-wait` only, J9 timer and beyond sweeps); engine mode per run is in each observation and in the run lists below (`real` for every case that fills the LAN engine address, `replayed` for cases that declare a recorded reply, `none` otherwise). The runtime is the lane's command, `uv run --extra dev`: it lacks the `openai` client (finding fnd.live.lane_runtime_lacks_meeting_client).
GRAPH: `docs/internal/philo/graph/live-muaddib.json` (validator: `OK`)

## JOBS

Verdict words: pass / fail / blocked / unexercised. A rig verdict is the predicate's; where the rig verdict is atlas-caused I say so. DIAGNOSTIC facts (below) are off-rig and are NEVER counted as a verdict.

- **J1 Get past the gate.** Expected: the desk; or the spoken words kept with a receipt. Observed: Continue later reaches the arrival headline at 1440 and 393; typed words kept as a note with the receipt line 'Kept as a note.'; speech READY on a fresh desk (`speech.transcribe` effective.status `assigned`). The spoken branch never ran: the rig does not perform the browser audio substitution. Verdict: **pass** (Continue later, typed keep); **blocked** (voice branch). Runs: 20260923T014250Z-…idle-1440, 20260923T014304Z-…idle-393, 20260923T014459Z/…014508Z keep_as_note, 20260923T014434Z speech_readiness; blocked 014446Z/014452Z speak.kept. Draft custody FAIL x2 is atlas-caused (the click saved the draft as a note, 201).
- **J2 See what the desk asks of me.** Expected: one SETUP row naming what is missing; the head counts what asks; an offer does not count. Observed on the face in the J2 runs: one SETUP row 'No engine for summaries' with 'Choose an engine', head '1 need you', 'NO CALENDAR · Connect calendar' not counted. No case earned a pass: both-missing is unreachable on a fresh desk (atlas FAIL x2), summary-missing-only blocked on a 400 atlas body, read failures blocked (no route_failure substitution). Verdict: **unverified** (face matches the expectation in the shots; no rig pass). Runs: 20260923T014548Z, 014623Z, 014656Z, 014700Z, and the four read_unknown/read_pending runs.
- **J3 Give the desk a summary engine.** Expected: Choose an engine → Add → address → Check → Use this for summaries → READY; SETUP row gone only because speech was ready; with speech missing the row stays. Observed: every setup chain that filled `http://192.168.1.43:8080` ran through Check and Use this for summaries without error, and the J6 queued pass proves the assignment landed (route ready, host 192.168.1.43). No J3 case reached its own trigger by a correct recipe (13 blocked, 1 atlas FAIL). Verdict: **blocked**. Runs: the 14 J3 rows under RUNS.
- **J4 Have one meeting on the desk.** Expected: a meeting row with its length; no summary yet; no error; import stops without a summary. Observed: import answers 202 and mints the row by id (pass); at capture the row reads `importing`, duration 0.0, so the length is not proven by the rig. Record → Stop is **blocked** (the rig forbids the microphone; its stop is a stub). Verdict: **pass** (import, row by id) with the limit stated; **blocked** (record). Runs: 20260923T015444Z (pass), record/stop/record_only runs blocked, capture_finalized FAIL is rig-caused.
- **J5 Know where the summary will run.** Expected: the planned host, before the click. Observed: '192.168.1.43 · LAN' on the row beside Run summary, before the click, at 1440 and 393. Verdict: **pass**. Runs: 20260923T020019Z route_disclosed-393, planned_host_disclosed 1440 + 393 (pass); route_disclosed-1440 blocked by import timing; no_engine_no_verb x2 blocked (scope absent).
- **J6 Get the summary (real LAN engine).** Expected: the host that DID run it; the summary text; technical completion and usefulness separately. Rig: Run summary queues a job against host 192.168.1.43 (pass, 1440; 393 blocked by timing); the named refusal for an empty meeting passes; every case that needs the finished summary is **blocked** (atlas order/timing, and the lane runtime cannot run a summary). TECHNICAL completion — rig: **blocked**. DIAGNOSTIC (off-rig): with the lane runtime, 5/6 attempts failed in 600 s ('bound analysis did not publish'; cause in the hub log: 'openai package is not available'); with the product's client added (`--with openai`), the run finished in 1.46 s, receipt host 192.168.1.43 outcome succeeded, engine Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf, summary verbatim: "The recording contains only a placeholder sentence with no substantive meeting content." OWNER usefulness: **unverified** — the input is the fixture WAV, whose transcript is 'The quick brown fox jumps over the lazy dog.' (9 words, not meeting material; it carries no planted token); the summary is accurate about that input and says nothing a manager could use. Verdict: **blocked** (rig). Runs: 20260923T020312Z (pass), 020345Z, 020428Z, 020457Z, 020529Z, 020615Z, 020651Z, 020726Z (pass), 020735Z (fail, atlas race), 021252Z/021302Z/021306Z (blocked).
- **J7 Find it again after a restart.** Expected: the same summary in two moves or less. Rig: **blocked** x3 (the verb check after it was clicked; the restart adapter never fired). DIAGNOSTIC (off-rig, client added): stop the hub, start it on the same HOME and database: the Chair row reads 'RAN · 192.168.1.43 · LAN · Open'; one Open shows the same summary text. Verdict: **blocked** (rig). Runs: 20260923T024725Z, and the two reload_persisted runs.
- **J8 Type by voice into another app.** Expected: words at the cursor of another app. **Unexercised** (native hotkey and other-app delivery excluded by brief §7). Run: 20260923T025010Z-case.j8.hotkey_option_r.other_app_delivery-muaddib-1440 (not_applicable).
- **J9 Open what the desk remembered.** Expected: Desk memory → a receipt's Open → the Rhythm face; a doorless receipt shows no Open. Observed: the REAL scheduler minted a SWEEP receipt (pass); run-now minted one (pass); Desk memory shows it (pass x2); the receipt's Open opens Rhythm at 1440 and 393 (pass x2). The doorless receipt is **blocked** (remote_origin_call not implemented). The Rhythm face shows UTC times (finding). Verdict: **pass** (door present); **blocked** (doorless). Runs: 20260923T025016Z (timer), 025030Z (run-now), 025038Z/025045Z (door_present), 025052Z/025059Z (rhythm_face); blocked 025131Z…025305Z.
- **J10 Get a brief, and another.** Expected: the brief's words stay after a reload; Generate again returns, displays and retains the same brief same-day; next day proven or blocked. Observed: 'No brief yet' before; 'Nothing material changed.' after Generate (x2), after a reload (x2), after Generate again with the returned headline = the displayed one (x2), the second POST returns the id held before (pass), retained after another reload on the face (x2) and by id on the protocol (x2); people sections 'unavailable' (pass). Populated brief and the item shelf are **blocked** by the decisions 500 (product defect). Next day **unexercised** (no clock mechanism). Verdict: **pass** (same-day, empty brief); **blocked** (populated); **unexercised** (next day).
- **J11 Develop a thought.** Expected: a note, kept, with 'Kept · time'; nothing hidden. Observed: Write a thought opens the Thought window (x2); typed words reach the store via autosave (GET /api/notes holds the new row, x2); the foot reads 'KEPT' (no time) beside Change and Finish. Whether the face 'hides things' is the owner's judgement, not a rig predicate. The create-refused face is **blocked**. Verdict: **pass** (words kept); the 'Kept · time' wording is not on the face (KEPT only).

Run counts per job (pass / fail / blocked / not_run / not_applicable = total):
J1 5/2/9/0/0 = 16 · J2 0/2/6/0/0 = 8 · J3 0/1/13/0/0 = 14 · J4 1/1/6/0/0 = 8 · J5 3/0/3/0/0 = 6 · J6 2/1/9/0/0 = 12 · J7 0/0/3/0/0 = 3 · J8 0/0/0/0/1 = 1 · J9 6/0/9/0/0 = 15 · J10 14/0/7/0/2 = 23 · J11 4/0/2/0/0 = 6 · beyond 7/0/1/0/0 = 8 · **total 42/7/68/0/3 = 120 runs**.

## COVERAGE

Discovered 73 cases; applicable 71; unreachable 2 (J8 other-app delivery; J10 next day), each recorded once per declared width as not_applicable. Exercised (run at least once through the rig): 71/71 applicable. Every face case ran at 1440 and 393; protocol cases once at 1440. One case ran twice at the same width: J1 continue_later.idle at 1440 (cold-start block, then pass); both kept.

Exercised but never reaching a verdict (blocked), with reasons: boundary substitutions not implemented (browser_audio_device, browser_permission, transport_failure, browser_capability, route_failure, remote_origin_call; 20 runs); the recorded engine reply `.tmp/graph-walk/engine-replies/intel-failure.json` absent and named as `reply_path` (not `reply`) (8 runs); atlas precondition order and import timing around the Run summary verb (19 runs); setups that never open the engine window (6 runs); atlas request bodies that the assignment service refuses (6 runs); POST /api/decisions answering 500 (5 runs, a product defect); J4 transcription_absent stops a meeting that never started, so its scope is absent (2 runs); beyond.capture_recover names `{meeting_id}` that nothing captures (1 run); the cold-start 5 s precondition window (1 run). Total 68.

## FINDINGS (ranked by owner cost)

Product defects:
1. `fnd.live.decisions_route_dead` — POST /api/decisions answers 500 (`del ctx` then `_svc()` reads ctx; `holdspeak/web/routes/primitives/decisions.py:20,27`, since aa865f57). He cannot record a decision on the desk. Live, 5 runs.
2. `fnd.live.failed_summary_reads_nothing_needs_you` — a summary retrying after failures shows QUEUED and FAILED together under 'Nothing needs you'; the reason (client not installed) never reaches the face (`ChairHome.tsx:628,1949`; `intel_queue.py:513`). Off-rig diagnostic plus source.
3. `fnd.live.rhythm_shows_utc` — Rhythm/Settings times are the ISO string sliced (UTC) beside a local clock (`settingsPrefs.tsx:536`, `SettingsCore.tsx:1392`). Live shot.
4. `fnd.live.run_refused_as_no_transcript_while_transcribing` — protocol only: 409 'Meeting has no transcript' during an import.

Tooling debt: `fnd.live.lane_runtime_lacks_meeting_client` (the lane's `--extra dev` has no `openai`; J6/J7 cannot complete under it) · `fnd.live.atlas_import_timing_and_run_order` · `fnd.live.boundary_substitutions_missing` · `fnd.live.atlas_request_shapes_drift` · `fnd.live.atlas_predicates_and_states` (the 7 rig FAILs are all atlas- or rig-caused) · `fnd.live.passes_that_prove_less`.

Doc drift: `fnd.live.lane_brief_engine_address` (brief says `/v1`; the atlas value without it is what ran, and it worked).

Two sitting defects no longer reproduce: the sweep receipt's Open reaches Rhythm (J9), and the empty brief has a face ('Nothing material changed.', J10).

## ORPHANS

None new from the live pass. The live pass drove only atlas cases; orphan candidates stay with the static pass (`static-muaddib.*`).

## DIAGNOSTICS (off-rig; not observations, not verdicts)

Three short scripts used the rig's own `Hub` class (fresh mkdtemp HOME, same verified database guard, same gestures as the J3→J6 setup, fixture WAV through `POST /api/meetings/import`), to learn why the J5/J6/J7 recipes block and to give the council J6's technical facts. Their output is not in the tree; the facts:
- Engine Check: 'READY · Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf'; `meeting.deferred_analysis` and `speech.transcribe` both `assigned`.
- Import: 9-20 s to finish in a fresh HOME (the speech model is fetched from the Hugging Face Hub on first use: hub log 'Fetching 4 files … unauthenticated requests to the HF Hub'); then 1 segment, 2.79 s, 9 words, planned route host 192.168.1.43 (lan), and the Run summary verb is drawn.
- Run with the lane runtime: attempts 5/6 in 600 s, last_error 'Deferred intel failed: bound analysis did not publish'; hub log: 'MeetingIntelError: openai package is not available'; Chair row 'QUEUED · 192.168.1.43 · LAN · FAILED' under 'Nothing needs you'.
- Run with `--with openai`: requested 20:26:50.109, ready 20:26:51.572; receipt host 192.168.1.43 outcome succeeded; summary 'The recording contains only a placeholder sentence with no substantive meeting content.'; topics [], action items []; reached from the Chair row's Open in one move.
- Restart (stop + start on the same HOME): state ready, the same summary text and host; on the face after one Open.

## UNKNOWN

- J6 owner usefulness: unmeasured. No synthetic meeting material exists in the tree; the fixture is one pangram. The council needs a real or synthetic meeting before it can judge usefulness.
- Whether the owner's own install carries the `openai` client (the `meeting` extra). If it does not, finding 2 is his Tuesday; if it does, J6 very likely completes for him (diagnostic), unverified by the rig.
- GET /api/decisions and the desk's decisions face were not run live; that they fail is inferred from the same `_svc()` path.
- Whether the first-use speech-model download from the Hugging Face Hub is disclosed on the face (Article III) was not checked.
- The `beyond.sweep_held_remote` receipt's summary field is a raw JSON string ('{"outcome": "held_remote_runs_on"…'); whether Desk memory shows it raw was not checked.
- J3's own face states (Check refusal, UNREACHABLE chip, speech-missing row) have no live verdict.
- The lane brief asked to substitute `…:8080/v1`; the atlas carries `…:8080` and the rig cannot override it without an atlas edit (forbidden), so the atlas value ran.
- Astra's position on each finding: not read (sealed).

## RUNS

### j1
  - 20260923T014145Z-case.j1.first_words_continue_later.idle-muaddib-1440 (blocked, engine none)
  - 20260923T014250Z-case.j1.first_words_continue_later.idle-muaddib-1440 (pass, engine none)
  - 20260923T014304Z-case.j1.first_words_continue_later.idle-muaddib-393 (pass, engine none)
  - 20260923T014315Z-case.j1.first_words_continue_later.draft_custody-muaddib-1440 (fail, engine none)
  - 20260923T014359Z-case.j1.first_words_continue_later.draft_custody-muaddib-393 (fail, engine none)
  - 20260923T014434Z-case.j1.speech_readiness.ready-muaddib-1440 (pass, engine none)
  - 20260923T014446Z-case.j1.first_words_speak.kept-muaddib-1440 (blocked, engine none)
  - 20260923T014452Z-case.j1.first_words_speak.kept-muaddib-393 (blocked, engine none)
  - 20260923T014459Z-case.j1.first_words_keep_as_note.kept-muaddib-1440 (pass, engine none)
  - 20260923T014508Z-case.j1.first_words_keep_as_note.kept-muaddib-393 (pass, engine none)
  - 20260923T014525Z-case.j1.first_words_speak.permission_denied-muaddib-1440 (blocked, engine none)
  - 20260923T014528Z-case.j1.first_words_speak.permission_denied-muaddib-393 (blocked, engine none)
  - 20260923T014534Z-case.j1.first_words_speak.unreachable_hub-muaddib-1440 (blocked, engine none)
  - 20260923T014536Z-case.j1.first_words_speak.unreachable_hub-muaddib-393 (blocked, engine none)
  - 20260923T014539Z-case.j1.first_words_speak.mic_unsupported-muaddib-1440 (blocked, engine none)
  - 20260923T014541Z-case.j1.first_words_speak.mic_unsupported-muaddib-393 (blocked, engine none)
### j2
  - 20260923T014548Z-case.j2.arrival_load.engines_both_missing-muaddib-1440 (fail, engine none)
  - 20260923T014623Z-case.j2.arrival_load.engines_both_missing-muaddib-393 (fail, engine none)
  - 20260923T014656Z-case.j2.arrival_load.summary_missing_only-muaddib-1440 (blocked, engine none)
  - 20260923T014700Z-case.j2.arrival_load.summary_missing_only-muaddib-393 (blocked, engine none)
  - 20260923T014713Z-case.j2.arrival_load.read_unknown-muaddib-1440 (blocked, engine none)
  - 20260923T014718Z-case.j2.arrival_load.read_unknown-muaddib-393 (blocked, engine none)
  - 20260923T014722Z-case.j2.arrival_load.read_pending-muaddib-1440 (blocked, engine none)
  - 20260923T014726Z-case.j2.arrival_load.read_pending-muaddib-393 (blocked, engine none)
### j3
  - 20260923T014753Z-case.j3.concierge_add_engine.add_ready-muaddib-1440 (blocked, engine none)
  - 20260923T014808Z-case.j3.concierge_add_engine.add_ready-muaddib-393 (blocked, engine none)
  - 20260923T014822Z-case.j3.concierge_add_check.refused-muaddib-1440 (blocked, engine none)
  - 20260923T014836Z-case.j3.concierge_add_check.refused-muaddib-393 (blocked, engine none)
  - 20260923T014855Z-case.j3.concierge_check.engine_unreachable-muaddib-1440 (blocked, engine none)
  - 20260923T014912Z-case.j3.concierge_check.engine_unreachable-muaddib-393 (blocked, engine none)
  - 20260923T014932Z-case.j3.concierge_use_for_summaries.assigned_ready-muaddib-1440 (blocked, engine real)
  - 20260923T015000Z-case.j3.concierge_use_for_summaries.assigned_ready-muaddib-393 (blocked, engine real)
  - 20260923T015025Z-case.j3.speech_missing.row_stays-muaddib-1440 (blocked, engine real)
  - 20260923T015041Z-case.j3.speech_missing.row_stays-muaddib-393 (blocked, engine real)
  - 20260923T015105Z-case.j3.route_assignments_set.assigned_ready-muaddib-1440 (fail, engine none)
  - 20260923T015141Z-case.j3.profile_delete.profile_missing-muaddib-1440 (blocked, engine real)
  - 20260923T015202Z-case.j3.profile_delete.profile_missing-muaddib-393 (blocked, engine real)
  - 20260923T015223Z-case.j3.profile_unbind.binding_absent-muaddib-1440 (blocked, engine real)
### j4
  - 20260923T015248Z-case.j4.record_start.capture_recording-muaddib-1440 (blocked, engine none)
  - 20260923T015252Z-case.j4.record_start.capture_recording-muaddib-393 (blocked, engine none)
  - 20260923T015256Z-case.j4.meeting_stop.capture_finalized-muaddib-1440 (fail, engine none)
  - 20260923T015444Z-case.j4.meetings_import.imported-muaddib-1440 (pass, engine none)
  - 20260923T015457Z-case.j4.meeting_stop.transcription_absent-muaddib-1440 (blocked, engine none)
  - 20260923T015636Z-case.j4.meeting_stop.transcription_absent-muaddib-393 (blocked, engine none)
  - 20260923T015815Z-case.j4.record_only.no_speech_head-muaddib-1440 (blocked, engine none)
  - 20260923T015819Z-case.j4.record_only.no_speech_head-muaddib-393 (blocked, engine none)
### j5
  - 20260923T015831Z-case.j5.meeting_open.route_disclosed-muaddib-1440 (blocked, engine real)
  - 20260923T020019Z-case.j5.meeting_open.route_disclosed-muaddib-393 (pass, engine real)
  - 20260923T020047Z-case.j5.meeting_open.no_engine_no_verb-muaddib-1440 (blocked, engine none)
  - 20260923T020124Z-case.j5.meeting_open.no_engine_no_verb-muaddib-393 (blocked, engine none)
  - 20260923T020212Z-case.j5.meeting_open.planned_host_disclosed-muaddib-1440 (pass, engine real)
  - 20260923T020239Z-case.j5.meeting_open.planned_host_disclosed-muaddib-393 (pass, engine real)
### j6
  - 20260923T020312Z-case.j6.run_summary.intel_queued-muaddib-1440 (pass, engine real)
  - 20260923T020345Z-case.j6.run_summary.intel_queued-muaddib-393 (blocked, engine real)
  - 20260923T020428Z-case.j6.run_summary.intel_running-muaddib-1440 (blocked, engine real)
  - 20260923T020457Z-case.j6.run_summary.intel_ready-muaddib-1440 (blocked, engine real)
  - 20260923T020529Z-case.j6.run_summary.summary_text-muaddib-1440 (blocked, engine real)
  - 20260923T020615Z-case.j6.run_summary.summary_text-muaddib-393 (blocked, engine real)
  - 20260923T020651Z-case.j6.run_summary.host_named-muaddib-1440 (blocked, engine real)
  - 20260923T020726Z-case.j6.route_intelligence_run.refusal-muaddib-1440 (pass, engine none)
  - 20260923T020735Z-case.j6.route_intelligence_run.no_assignment-muaddib-1440 (fail, engine none)
  - 20260923T021252Z-case.j6.run_summary.intel_failed-muaddib-1440 (blocked, engine replayed)
  - 20260923T021302Z-case.j6.run_summary.intel_failed-muaddib-393 (blocked, engine replayed)
  - 20260923T021306Z-case.j6.run_summary.intel_retry-muaddib-1440 (blocked, engine replayed)
### j7
  - 20260923T024725Z-case.j7.hub_restart.intel_retained-muaddib-1440 (blocked, engine real)
  - 20260923T024753Z-case.j7.arrival_load.reload_persisted-muaddib-1440 (blocked, engine real)
  - 20260923T024830Z-case.j7.arrival_load.reload_persisted-muaddib-393 (blocked, engine real)
### j8
  - 20260923T025010Z-case.j8.hotkey_option_r.other_app_delivery-muaddib-1440 (not_applicable, engine none)
### j9
  - 20260923T025016Z-case.j9.timer_sweep.receipt_resolved-muaddib-1440 (pass, engine none)
  - 20260923T025030Z-case.j9.route_run_now.receipt_resolved-muaddib-1440 (pass, engine none)
  - 20260923T025038Z-case.j9.shade_open.door_present-muaddib-1440 (pass, engine none)
  - 20260923T025045Z-case.j9.shade_open.door_present-muaddib-393 (pass, engine none)
  - 20260923T025052Z-case.j9.shade_receipt_open.rhythm_face-muaddib-1440 (pass, engine none)
  - 20260923T025059Z-case.j9.shade_receipt_open.rhythm_face-muaddib-393 (pass, engine none)
  - 20260923T025131Z-case.j9.shade_open.door_absent-muaddib-1440 (blocked, engine none)
  - 20260923T025135Z-case.j9.shade_open.door_absent-muaddib-393 (blocked, engine none)
  - 20260923T025139Z-case.j9.shade_open.door_stale-muaddib-1440 (blocked, engine real)
  - 20260923T025210Z-case.j9.shade_open.door_stale-muaddib-393 (blocked, engine real)
  - 20260923T025249Z-case.j9.shade_acknowledge.acknowledged-muaddib-1440 (blocked, engine replayed)
  - 20260923T025253Z-case.j9.shade_acknowledge.acknowledged-muaddib-393 (blocked, engine replayed)
  - 20260923T025257Z-case.j9.shade_dismiss.dismissed-muaddib-1440 (blocked, engine replayed)
  - 20260923T025301Z-case.j9.shade_dismiss.dismissed-muaddib-393 (blocked, engine replayed)
  - 20260923T025305Z-case.j9.route_presentation_restore.restored-muaddib-1440 (blocked, engine replayed)
### j10
  - 20260923T025316Z-case.j10.brief_latest.absent-muaddib-1440 (pass, engine none)
  - 20260923T025324Z-case.j10.brief_latest.absent-muaddib-393 (pass, engine none)
  - 20260923T025331Z-case.j10.arrival_generate_brief.populated-muaddib-1440 (blocked, engine none)
  - 20260923T025335Z-case.j10.arrival_generate_brief.populated-muaddib-393 (blocked, engine none)
  - 20260923T025400Z-case.j10.arrival_generate_brief.generated_empty-muaddib-1440 (pass, engine none)
  - 20260923T025407Z-case.j10.arrival_generate_brief.generated_empty-muaddib-393 (pass, engine none)
  - 20260923T025415Z-case.j10.arrival_reload.reload_persisted-muaddib-1440 (pass, engine none)
  - 20260923T025425Z-case.j10.arrival_reload.reload_persisted-muaddib-393 (pass, engine none)
  - 20260923T025434Z-case.j10.arrival_generate_again.same_day_idempotent-muaddib-1440 (pass, engine none)
  - 20260923T025742Z-case.j10.arrival_generate_again.same_day_idempotent-muaddib-393 (pass, engine none)
  - 20260923T030057Z-case.j10.route_generate_again.same_day_same_id-muaddib-1440 (pass, engine none)
  - 20260923T030105Z-case.j10.arrival_generate_again.retained_after_reload-muaddib-1440 (pass, engine none)
  - 20260923T030115Z-case.j10.arrival_generate_again.retained_after_reload-muaddib-393 (pass, engine none)
  - 20260923T030124Z-case.j10.route_generate_again.retained_after_reload-muaddib-1440 (pass, engine none)
  - 20260923T030133Z-case.j10.route_generate_again.retained_after_reload-muaddib-393 (pass, engine none)
  - 20260923T030148Z-case.j10.arrival_generate_again.next_day-muaddib-1440 (not_applicable, engine none)
  - 20260923T030148Z-case.j10.route_brief_generate.load_failure-muaddib-1440 (blocked, engine none)
  - 20260923T030152Z-case.j10.arrival_generate_again.next_day-muaddib-393 (not_applicable, engine none)
  - 20260923T030152Z-case.j10.route_brief_generate.load_failure-muaddib-393 (blocked, engine none)
  - 20260923T030156Z-case.j10.brief_item_shelf.acknowledged-muaddib-1440 (blocked, engine none)
  - 20260923T030200Z-case.j10.brief_item_shelf.deferred-muaddib-1440 (blocked, engine none)
  - 20260923T030204Z-case.j10.brief_item_shelf.refused-muaddib-1440 (blocked, engine none)
  - 20260923T030207Z-case.j10.brief_people.unavailable-muaddib-1440 (pass, engine none)
### j11
  - 20260923T030221Z-case.j11.write_a_thought.window_open-muaddib-1440 (pass, engine none)
  - 20260923T030229Z-case.j11.write_a_thought.window_open-muaddib-393 (pass, engine none)
  - 20260923T030236Z-case.j11.thought_keep.kept-muaddib-1440 (pass, engine none)
  - 20260923T030245Z-case.j11.thought_keep.kept-muaddib-393 (pass, engine none)
  - 20260923T030253Z-case.j11.write_a_thought.create_refused-muaddib-1440 (blocked, engine none)
  - 20260923T030257Z-case.j11.write_a_thought.create_refused-muaddib-393 (blocked, engine none)
### beyond
  - 20260923T030311Z-case.beyond.capture_recover.recovered-muaddib-1440 (blocked, engine none)
  - 20260923T030314Z-case.beyond.sweep_held_remote.receipt_resolved-muaddib-1440 (pass, engine none)
  - 20260923T030328Z-case.beyond.sweep_held_remote.no_local_sweep-muaddib-1440 (pass, engine none)
  - 20260923T030548Z-case.beyond.projections_counts.needs_attention-muaddib-1440 (pass, engine none)
  - 20260923T030552Z-case.beyond.projections_counts.unseen-muaddib-1440 (pass, engine none)
  - 20260923T030556Z-case.beyond.projections_counts.acknowledged-muaddib-1440 (pass, engine none)
  - 20260923T030606Z-case.beyond.first_words_reload.retained_draft-muaddib-1440 (pass, engine none)
  - 20260923T030613Z-case.beyond.first_words_reload.retained_draft-muaddib-393 (pass, engine none)

