# Capture: the recipe

Each slice is one PR in the fast cycle (`CLAUDE.md`): branch from `main`,
`scripts/quick_check.sh`, merge. The order puts the desk-freezing fault
first and the trust fault second, so each merge leaves capture better and
never half-broken. Tests follow the test diet: T1 a hub test, T2 one vitest
file per app (`web/src/**/__tests__/<app>.app.test.tsx`), T3 the desk sweep,
T4 a real browser only for drag, focus, keys, touch or geometry. Engine
answers in tests are recorded real answers, never typed ones.

Design: `DESIGN.md`. Code map: `MODEL.md`.

---

## C1. Talk never freezes the desk

- **Goal**: while he Talks, every other window keeps answering.
- **Files**: `holdspeak/web/routes/system/voice_stream.py`,
  `holdspeak/dictation_runner.py`,
  `tests/integration/test_desk_speak.py` (new).
- **Changes**: in `ws_dictation_stream`, run `transcribe(audio)` with
  `await asyncio.to_thread(...)`. Make `process_transcript` run
  `run_pipeline_corrections_only` with `asyncio.to_thread`, as
  `web/routes/dictation/pipeline.py:976` does. Keep the session fence, the
  macro election and the journal row exactly as they are. A client that
  disconnects mid-utterance ends the work without a final send.
- **Done when**: with a transcription double that sleeps 5 s and a
  clean-up engine that sleeps 5 s, `GET /` answers in under 200 ms during
  the whole utterance, at both widths' rigs. The browser-gone case (`RECON.md`
  §5) no longer stalls the hub.
- **Tests**: T1, `test_desk_speak.py`: open the socket, stream PCM, send
  `end`, and in parallel poll a cheap route; assert each answer < 0.5 s; and
  the same with the socket dropped mid-stream.
- **Not in this slice**: any face change; the hotkey path.

## C2. A summary tells only what came before

- **Goal**: a meeting's summary never reports a later meeting as history,
  and he can see what it read.
- **Files**: `holdspeak/intel_queue.py` (`_meeting_memory`),
  `holdspeak/services/memory_grounding.py` (`memory_context`, `memory_for`),
  `holdspeak/intel/parsing.py`, the run-receipt writer in `holdspeak/db/intel.py`,
  `web/src/pages/cores/history/MeetingDetail.tsx`,
  `tests/integration/test_desk_meetings.py`,
  `web/src/desk/__tests__/meetings.app.test.tsx`.
- **Changes**: add `before: datetime | None` to `memory_context` and
  `memory_for`; drop any block whose source time is at or after it (a
  meeting's `started_at`, a note's or decision's `created_at`). Pass the
  meeting's `started_at` from `_meeting_memory`. Put the source date at the
  front of each excerpt line. Prompt words: "Work on this project before
  this meeting (each line has its date)". Store the excerpt refs on the run
  receipt; the face shows them as a folded **Looked at · N** under the
  transcript fold, each a link with its date.
- **Done when**: import the three seed transcripts (`capture/rig/seed/`)
  with their dates, summarise the Thursday sync last; its summary and its
  Looked at name nothing from Friday or later. Friday's Looked at lists the
  Thursday sync with "Thu 15 Oct". 1440 and 393.
- **Tests**: T1, a hub test with two dated meetings in one project and a
  recorded engine answer: assert the memory block sent to the engine holds
  no ref of the later meeting, and the receipt lists the refs. T2: the
  Looked at fold renders the refs with dates from a recorded hub answer.
- **Not in this slice**: Ask's or Thread's memory reads (`../asking/`).

## C3. Import asks when it was

- **Goal**: an imported meeting gets its real date.
- **Files**: the import form in `web/src/pages/cores/history/` (the RECORD
  wing's import panel), `holdspeak/transcript_parse.py` (a header or name
  date, if present), `holdspeak/web/routes/meeting_import.py`,
  `tests/integration/test_desk_meetings.py`, `web/src/desk/__tests__/meetings.app.test.tsx`.
- **Changes**: the form shows **When was this?** (date and time), filled
  from, in order: a date in a VTT/SRT header, a date in the file name, the
  browser `File.lastModified`. Send it as `started_at_ms`. **Import** opens
  the file picker at once (no wing switch); a drop on the Meetings window
  does the same.
- **Done when**: importing `one-on-one-theo.txt` modified on Thursday
  lists it under Thursday; one press on Import opens the picker. 1440 and
  393.
- **Tests**: T1 (the route stores the given start), T2 (the field fills
  from a file's `lastModified`; Import calls the picker). T4 only if the
  drop needs a real drag.
- **Not in this slice**: the Record wing's new layout (C7).

## C4. Meeting plugins run on Engines

- **Goal**: the meeting's model plugins run on the engine he chose, on
  saved, imported and recorded meetings.
- **Files**: `holdspeak/intel/providers.py` (`resolve_llm_capability`),
  `holdspeak/meeting_plugins.py`, `holdspeak/web_runtime.py:260`,
  `holdspeak/db/intel.py` (`:1634-1637`, `_plan_installed_plugin_members`),
  `tests/integration/test_meeting_plugins_engines.py` (new).
- **Changes**: the `llm` capability is true when the "Meeting summaries"
  job resolves to an engine in Engines (the same resolution the summary
  uses), not when the old `meeting.intel_provider` file exists. A job with
  a `planned_route_json` plans its plugin members on that same route
  instead of setting them to `()`. Keep the HS-201 rule that no transcript
  goes to a destination he was not shown: the planned route **is** that
  destination.
- **Done when**: the architecture review import, with the LAN engine set in
  Engines only, ends with `plugin-runs` showing `requirements_extractor`
  and `decision_capture` as `success`, and no `Missing capabilities: llm`.
- **Tests**: T1 with a recorded engine answer per plugin; assert runs and
  artifacts are stored. Existing `tests/unit/test_meeting_plugins*.py` stay
  green (named in the PR).
- **Not in this slice**: which plugins run (C5) and the face.

## C5. The meeting prepares its Results

- **Goal**: after a meeting, the follow-up and the drafts it asked for are
  waiting in the meeting window, ready to send.
- **Files**: `holdspeak/meeting_plugins.py` (a "prepared" plan),
  `holdspeak/plugins/router.py` (action-triggered members),
  `web/src/pages/cores/history/MeetingDetail.tsx`,
  `web/src/pages/cores/history/MeetingRecord.tsx` (wings),
  `web/src/pages/cores/history/ArtifactsLibrary.tsx` (park),
  `web/src/desk/__tests__/meetings.app.test.tsx`.
- **Changes**: after the summary, plan Results from what the meeting said:
  the follow-up always (`decision_announcement_drafter` or the existing
  follow-up draft); `adr_drafter` when an action or decision names an ADR;
  `stakeholder_update_drafter` when an action names an update to people
  outside the meeting; `mermaid_architecture` when the profile or an action
  asks for a diagram. Outcomes gets **Prepared · N**: each Result rendered,
  with *Open as note*, *Copy*, *Send…*; "Writing… N s" while it runs; a
  reason and *Write again* when it fails. An action that a Result serves
  shows **Draft ready ›**. **Prepare…** lists the other kinds and runs one
  on press. Park the ARTIFACTS wing.
- **Done when**: importing the architecture review shows Prepared with the
  follow-up, an ADR draft and the support update within 3 minutes on the
  LAN engine; *Send…* opens the Send well with the draft; nothing is sent
  without a press. 1440 and 393; the sweep passes.
- **Tests**: T2 Meetings app test from a recorded hub answer (rows, verbs,
  Draft ready link, failure text). T1 for the plan (an "ADR" action
  schedules `adr_drafter`). T3 sweep.
- **Not in this slice**: the Send well itself (`../send/`); Results in
  Today (`../daily/`).

## C6. Since last time

- **Goal**: the meeting window says what changed since the last meeting of
  the same kind.
- **Files**: `holdspeak/meeting_aftercare.py` (`_previous_meeting`),
  `web/src/pages/cores/history/MeetingDetail.tsx`, `web/src/desk/__tests__/meetings.app.test.tsx`,
  `tests/unit/test_meeting_aftercare*.py`.
- **Changes**: the previous meeting is the last one of the same calendar
  series; else the same project; else the same set of people; else none.
  Under the summary, one folded line "Since <title>, <date>: …" with closed,
  still open and new, each a link. No previous meeting: no line.
- **Done when**: Friday's review says "Since Payments platform sync, Thu 15
  Oct"; the Thursday sync shows no line.
- **Tests**: T1 (the previous-meeting rule with three meetings), T2 (the
  line renders from a recorded aftercare answer).
- **Not in this slice**: the Room's project-level version (`../projects/`).

## C7. One home for recording

- **Goal**: every recording, armed or manual, is in one place, and the
  calendar is the way to schedule.
- **Files**: the Meetings RECORD wing in `web/src/pages/cores/history/`,
  `web/src/desk/chair/ChairHome.tsx` (Capture), `web/src/desk/components/ScheduleCreateWindow.tsx`
  (moves under *Another time…*), `web/src/desk/store/scheduledRecordingSlice.ts`,
  `holdspeak/web/routes/calendar_snapshot.py:176`, the Meetings and Capture
  app tests, `tests/integration/test_desk_meetings.py`.
- **Changes**: Meetings ▸ Record shows *Record*, *Import*, **Coming up**
  (next calendar meetings with *Record when it starts*; armed ones with
  *Records at HH:MM · Cancel*), *Another time…* (the manual form in place)
  and the auto-record switch. Today's arming and this list read one store.
  Capture's *Schedule* is replaced by the next two Coming-up rows. A fire
  that raises writes a `failed` receipt with its reason
  (`holdspeak/scheduled_recording_conductor.py:559`), and the row shows
  **Did not record · HH:MM · reason** with *Record now*. Lower-case the
  weekday in the calendar confirm route.
- **Done when**: arming in Today shows the row armed in Meetings ▸ Record
  and in Capture within 2 s, and *Cancel* in either disarms both. 1440 and
  393.
- **Tests**: T2 `meetings.app.test.tsx` and `chair.app.test.tsx`; T1 for the weekday fix and for a fire that raises (receipt written, state not stuck in `arming`); T3
  sweep.
- **Not in this slice**: EventKit; the calendar snapshot face.

## C8. Speak and Capture in plain words

- **Goal**: Talk works the same everywhere and every word on Speak and
  Capture is one he would use.
- **Files**: `web/src/pages/cores/dictation/SpeakFace.tsx`,
  `web/src/desk/firstrun/SpeechSetup.tsx`, `web/src/desk/chair/ChairHome.tsx`,
  the floor TALK component, the menu-bar chip, the Speak and Capture app
  tests.
- **Changes**: one Talk rule (when speech is not set up, any Talk opens the
  setup in place, then listens). `Listening · Stop` on the button and the
  menu bar in place of `MIC HELD`. The words table in `DESIGN.md` §4.
  Details and ⚙︎ diagnostics behind RAW. A visible *Try it here* for typed
  text. Capture: three large buttons, *New note* that makes its record on
  the first character, Coming up under them (from C7).
- **Done when**: on a desk with no speech model, the floor TALK, Capture
  TALK and Speak Talk all open the same setup; no face shows `LANDS IN`,
  `DRY RUN`, `MIC HELD`, `OPEN`, `LEVEL` or `Write a thought`; a press on New
  note with no typing leaves no record. 1440 and 393.
- **Tests**: T2 `speak.app.test.tsx` and `chair.app.test.tsx` (Capture lives in the chair); T3 sweep (readable, 12 px,
  clipped).
- **Not in this slice**: the one speech-readiness source in Engines
  (`../engines/`); voice commands (C11).

## C9. A clean audio callback

- **Goal**: Stop meets a quiet audio thread, so the device closes more
  often and faster.
- **Files**: `holdspeak/meeting_recorder.py`,
  `holdspeak/meeting_capture_journal.py`,
  `tests/unit/test_meeting_native_stop.py`,
  `tests/unit/test_meeting_capture_durability.py`.
- **Changes**: the mic and system callbacks copy the samples into a bounded
  queue and return; they take no lock that a disk write holds. A writer
  thread drains the queue into the journal and does the checkpoints. Stop
  seals the queue, waits for the writer to flush what was accepted, then
  snapshots. Streams end with `abort()` instead of `stop()`. Keep the
  "accepted chunk is on disk before the Stop snapshot" rule and same-ID
  recovery.
- **Done when**: the existing native-stop and durability tests pass, plus a
  new one: a journal write that blocks for 2 s never delays a callback by
  more than 5 ms.
- **Tests**: T1 (unit) in the two named files, with stream doubles. The
  owner's real-metal walk (Record 2 minutes, Stop) after merge.
- **Not in this slice**: the capture process (C10).

## C10. Meetings record in their own process (decision 1)

- **Goal**: a stuck audio device never needs a HoldSpeak restart.
- **Files**: `holdspeak/meeting_recorder.py` (a process front),
  a new `holdspeak/capture_process.py`, `holdspeak/runtime/meeting_glue.py`,
  `holdspeak/runtime/meeting_stop.py`,
  `tests/integration/test_meeting_capture_process.py` (new),
  `tests/integration/test_meeting_stop_and_conflicts.py`.
- **Changes**: the recorder runs in a child process started at Record; it
  owns both streams and the journal, and reports levels and state over a
  pipe. Stop asks it to stop; after 1 s the desk ends it. The journal on
  disk is the source of the saved audio, as recovery already uses. The
  audio floor is released when the child has exited. The "Restart HoldSpeak
  to record" refusal is removed.
- **Done when**: with a stream double that hangs in `stop()`, Stop returns
  in under 1.5 s, the meeting is saved with all accepted audio, and the
  next Record starts and records.
- **Tests**: T1 integration with the hanging double; the existing Stop and
  kill-recovery integration files stay green. Owner real-metal walk.
- **Not in this slice**: system audio without BlackHole (parked: CoreAudio
  process taps need macOS 14.2+ and their own design).

## C11. Voice commands run desk verbs (decision 3)

- **Goal**: "start recording" starts a recording.
- **Files**: `holdspeak/plugins/voice_macro_connector.py`,
  `web/src/pages/cores/CommandsCore.tsx` (into a Speak wing),
  `web/src/desk/applications.ts` (Commands row → Speak wing),
  the verb registry `web/src/desk/verbRegistry.ts` (read only),
  `web/src/desk/__tests__/speak.app.test.tsx`, `tests/integration/test_desk_speak.py`.
- **Changes**: a new behavior **Desk verb**, which runs a verb through the
  same operation path as its MCP tool (record, stop, new note, ask, open an
  app). Five phrases ship on. Verbs that send, configure or grant authority
  are not offered. Commands becomes Speak ▸ Voice commands; the old window
  id opens the wing.
- **Done when**: with commands on, a Talk that transcribes to "start
  recording" starts a recording (in the rig: the named refusal), and "new
  note" opens a new note. 1440 and 393.
- **Tests**: T1 (a transcript fires the verb through the operation path),
  T2 Speak app test (the wing, the five defaults).
- **Not in this slice**: the hotkey's own command path, unless it shares
  the same dispatcher.

## C12. The glyph tells the truth

- **Goal**: the menu-bar glyph shows recording time and Stop, and says when
  the desk is gone.
- **Files**: `holdspeak/desktop_presence.py`,
  `holdspeak/desktop_presence_cocoa.py`, `tests/unit/test_desktop_presence*.py`.
- **Changes**: the `meeting_live` state carries the elapsed time; the glyph
  menu has *Stop* (the same stop operation); on hub disconnect the label
  becomes "Desk not running" (the open item in
  `COHESIVE-DESK-ENTRY-2026-10-16` README:79-81).
- **Done when**: unit tests show the label for each state; the owner's
  real-metal walk sees Recording · mm:ss and Stop.
- **Tests**: T1 (unit, the view model). No browser.
- **Not in this slice**: a new HUD design.

---

## Parked (not in this recipe)

- System audio without BlackHole (CoreAudio process taps).
- Live in-meeting plugin windows (the MIR live path) on the face.
- Reading a calendar screenshot without a vision engine.
- EventKit calendar walk (the rig switches it off; needs the owner's Mac).
