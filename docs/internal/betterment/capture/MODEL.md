# Capture: the code map (2026-10-17)

Read from the code of the owner's desk head (`217001b2e`). Paths are
relative to the repository root. This map is short on purpose: it names
what each part is in data, the faults that explain the walls in `RECON.md`,
and the constraints a build must keep.

## 1. What each part is

| Part | In data | Main code | MCP |
|---|---|---|---|
| Speak (browser Talk) | One websocket per utterance; audio is kept in memory, then one transcription pass, then the dictation pipeline (classify, rewrite, journal row) | `holdspeak/web/routes/system/voice_stream.py`, `holdspeak/dictation_runner.py`, `web/src/pages/cores/dictation/SpeakFace.tsx` (1,019 lines) | `dictation_get`, `dictation_list` |
| Speak (hotkey) | `pynput` listener on Right Option; the runtime records, transcribes and types into the focused app | `holdspeak/hotkey.py` (last change 2026-03-25), `holdspeak/runtime/dictation_capture.py` | none |
| Menu-bar glyph and HUD | An `NSStatusItem` and a floating panel in a child process; eleven states (`Ready`, `Listening`, `Recording`, `Transcribing`, `Meeting live`, `Saving`, `Armed`, `Needs attention`, …) | `holdspeak/desktop_presence.py:45-56`, `holdspeak/desktop_presence_cocoa.py` | none |
| Voice commands | A keyword mapped to one of four behaviors: open URL, launch app, shell command, type text; off by default | `web/src/pages/cores/CommandsCore.tsx`, `holdspeak/plugins/voice_macro_connector.py`, fired at `voice_stream.py:285-310` | none |
| Meeting | A row with segments (speaker, text, times), a summary, topics, action items, decisions as proposals, artifacts, an intel job and a run receipt | `holdspeak/meeting_session/`, `holdspeak/services/meeting_service.py`, `web/src/pages/cores/history/` | `meeting_*` (10), `proposal_confirm`, `proposal_dismiss` |
| Import | A file (audio or `.txt`/`.vtt`/`.srt`) becomes a meeting; a transcript skips speech-to-text | `holdspeak/web/routes/meeting_import.py`, `holdspeak/meeting_import.py`, `holdspeak/transcript_parse.py` | `meeting_import` |
| Record | Two PortAudio input streams (mic and BlackHole), PCM journaled to disk while it runs | `holdspeak/meeting_recorder.py`, `holdspeak/meeting_capture_journal.py`, `holdspeak/runtime/meeting_glue.py`, `holdspeak/runtime/meeting_stop.py` | `meeting_start_capture`, `meeting_stop_capture` |
| Summary | One deferred intel job per meeting on the "Meeting summaries" engine; may read project memory | `holdspeak/intel_queue.py`, `holdspeak/intel/engine.py`, `holdspeak/intel/parsing.py` | `meeting_run_intelligence` |
| Meeting plugins | 19 built-in plugins (14 readers, 5 actuators) routed by an intent score, each writing an artifact | `holdspeak/plugins/`, `holdspeak/meeting_plugins.py`, `holdspeak/db/intel.py:342` | `plugin_job_*` (4) |
| Aftercare | A computed digest: open items by owner, decisions, "since last meeting", a follow-up draft | `holdspeak/meeting_aftercare.py`, `holdspeak/web/routes/meetings/aftercare.py` | none (inside `meeting_get`? not checked) |
| Scheduled recording | A row with a one-shot or cron time, a calendar event link, a state (`idle`, `armed`, …), fired by a conductor | `holdspeak/services/scheduled_recording_service.py`, `holdspeak/scheduled_recording_conductor.py`, `web/src/desk/needs/arming.ts` | `scheduled_recording_*` (5) |
| Calendar snapshot | A screenshot read by a vision engine into events, written as an ICS file and read as a calendar source | `holdspeak/web/routes/calendar_snapshot.py`, `holdspeak/services/calendar_snapshot_service.py` (844 lines) | none |
| Capture window | Four buttons inside the chair home | `web/src/desk/chair/ChairHome.tsx` (3,168 lines, shared with Brief and The week), `web/src/desk/chair/chairWindows.ts:36-41` | none |

## 2. Speak blocks the hub

The browser's Talk ends in one async websocket handler. Two synchronous
calls run inside it, on the event loop:

- the transcription: `raw_text = transcribe(audio)`
  (`holdspeak/web/routes/system/voice_stream.py:245`), which in production is
  Whisper (`holdspeak/runtime/dictation_capture.py:343`);
- the pipeline: `await process_transcript(...)` (`voice_stream.py:337`), but
  `process_transcript` is `async` only in name. It returns
  `run_pipeline_corrections_only(...)` directly
  (`holdspeak/dictation_runner.py:294`), which makes the intent classify and
  rewrite calls to the engine.

While either runs, no other request is served. Measured in the rig: 65 s of
no answers (`RECON.md` §5). The HTTP dictation route does it right with
`asyncio.to_thread` (`holdspeak/web/routes/dictation/pipeline.py:976`,
`:995`). This is the same fault class as the Stop hang (§5): slow or native
work on the event loop.

Other Speak facts:

- Speak's head reads speech readiness from the local-AI status
  (`web/src/desk/firstrun/SpeechSetup.tsx:55-61`), while Settings ▸ Engines
  shows a job named "Speech to text" that the Default engine sets to a chat
  model (`RECON.md` §1). Two sources of truth for one fact.
- The floor TALK and the Capture TALK do not check speech readiness; the
  Speak window's Talk does (`SpeakFace.tsx:353`). Three Talk buttons, two
  rules.
- Voice typing needs a chat engine for "Dictation clean-up". Without one,
  Speak shows `Engine · Not set` as a fault, although raw words could land.

## 3. The summary reads the future

- `_meeting_memory` (`holdspeak/intel_queue.py:433-466`) reads memory for
  the meeting's first project, with the meeting's own title and transcript
  as the query, and leaves out only the meeting itself.
- `memory_context` (`holdspeak/services/memory_grounding.py:206-290`) has no
  time bound. Nothing drops a source that started after this meeting.
- The prompt then says "Earlier work on this project is in the block below.
  Use it in the summary to say what changed"
  (`holdspeak/intel/parsing.py:103-104`). The model obeys, so a later
  decision is written as history.
- The excerpts carry no dates, so the model cannot tell order itself.
- The run receipt keeps the host, the outcome and a selection hash, not the
  sources read (`RECON.md` §2). He cannot see why the summary said it.
- A meeting on no project reads no memory, so the fault shows only once
  meetings are filed to a project: the moment the desk starts to be useful.

## 4. Why no plugin output reaches a face

Two independent faults stop every model plugin on saved and imported
meetings. Either one is enough.

1. **A planned route empties the plugin chain.** Every summary job now
   carries `planned_route_json` (the engine selection). When it is set, the
   claim plans no plugins: `plugin_members, plugin_route = (), {}`
   (`holdspeak/db/intel.py:1634-1635`). The comment at `:1667` calls an empty
   chain "the ordinary case on the owner's desk". In the rig, all three jobs
   had `"plugin_members":[]`.
2. **The plugin host reads the old engine config.** The `llm` capability
   comes from `resolve_llm_capability(config.meeting)`
   (`holdspeak/intel/providers.py:179-208`, used at
   `holdspeak/web_runtime.py:260` and `holdspeak/meeting_plugins.py:75`),
   which checks `meeting.intel_provider` (default `local`) and a GGUF file
   path. It does not read Engines. With the LAN engine set in Engines, the
   CLI reroute gave `blocked: Missing capabilities: llm` for every model
   plugin.

And a third, softer fault: routing. The intent scores for an architecture
review that names an ADR were `architecture 0.44`, `comms 0.44`, under the
threshold `0.6` (`holdspeak/plugins/router.py:20`). With the `balanced`
profile the chain is `project_detector, requirements_extractor,
action_owner_enforcer, decision_capture`; the ADR, diagram and stakeholder
plugins appear only under the `architect` profile or a manual intent.

The face is ready for outputs: the ARTIFACTS wing lists whatever artifacts
exist (`web/src/pages/cores/history/ArtifactsLibrary.tsx`). Today it shows
only `summary_items`, a copy of Outcomes.

## 5. The Stop hang: what the code says

The incident (`docs/internal/MEETING-STOP-NATIVE-2026-10-16/RECOVERY.md`):
the web thread waited in PortAudio `FinishStoppingStream →
AudioOutputUnitStop → AudioDeviceStop → HALB_Mutex::Lock`; a CoreAudio IO
thread waited in PortAudio's `startStopCallback → AudioUnitGetProperty` for
the same HAL mutex. That is a lock-order wait between the thread that stops
the unit and the device's own IO thread.

What the code adds to it:

- **Blocking work on the real-time audio thread.** Each mic and system
  callback takes the recorder lock and, inside it, writes the PCM to the
  journal (`holdspeak/meeting_recorder.py:489-501`, `:506-535`). The journal
  write takes a second lock and, every `checkpoint_bytes`, `fsync`s both
  track files, writes the manifest, `fsync`s it and renames it
  (`holdspeak/meeting_capture_journal.py:54-71`, `:128-155`). A CoreAudio IO
  thread must never wait on a disk or a Python lock. A long IO cycle widens
  the window in which Stop meets an IO thread that is mid-cycle.
- **Two devices stop at once.** Mic and BlackHole are two streams on two
  devices (`meeting_recorder.py:611-656`). Since #1237 each stops on its own
  daemon thread.
- **`stop()`, not `abort()`.** `stream.stop()` is PortAudio's
  `Pa_StopStream`, which waits for queued buffers to play out;
  `Pa_AbortStream` does not wait.
- **PortAudio is old.** `sounddevice 0.5.3` with `PortAudio V19.7.0-devel`
  (the rig's venv).

What is fixed: Stop no longer runs on the event loop; native stop and close
run on daemon threads with a one-second budget; the audio is saved even if
the device never closes (`MEETING-STOP-NATIVE-2026-10-16/BUILD.md`).

What is left: a wedged daemon thread keeps the CoreAudio client in the hub
process, so the recorder refuses reuse with "Audio device did not close.
Restart HoldSpeak to record." (`meeting_recorder.py:313-316`). Only a
process exit frees it.

**Root cause, bounded.** The hang is inside CoreAudio's stop path, between
the stopping thread and the device IO thread. Our code makes it more likely
(blocking I/O and locks in the IO callback, `stop()` that drains) and makes
it costly (the audio client lives in the hub process, so a wedge needs a hub
restart). Why CoreAudio held the mutex is **unknown**: I could not reproduce
it without a microphone, and I did not find a PortAudio report that matches
the exact pair of stacks.

## 6. Other faults found on the way

- **Import asks no date.** The route takes `started_at_ms`
  (`holdspeak/web/routes/meeting_import.py:75`); the face never sends it, so
  an imported meeting is dated "now minus its length"
  (`holdspeak/meeting_import.py:319-322`). Every later step that orders
  meetings (aftercare, memory, the week) then sees the wrong order.
- **"Since the last meeting" means any meeting.** `_previous_meeting`
  (`holdspeak/meeting_aftercare.py:157-181`) takes the latest meeting before
  this one across the whole desk, not the same project or calendar series.
- **No live face draws aftercare's "since last meeting".** The only live
  reader of the route reads counts (`web/src/desk/intelligenceAttention.ts:128`);
  the faces that drew the diff are in `_parked/` folders.
- **Calendar confirm crashes on a capital weekday.**
  `holdspeak/web/routes/calendar_snapshot.py:176` does not lower-case the
  weekday; the resolver indexes `WEEKDAY_MAP` with it
  (`holdspeak/services/calendar_snapshot_service.py:260`) and the route
  answers 500.
- **No face lists armed recordings.** The only consumer of the schedule
  store is the arming row (`web/src/desk/needs/arming.ts`) and Today's NEXT
  card.
- **A failed scheduled fire is silent.** An exception in the countdown
  thread (`holdspeak/scheduled_recording_conductor.py:559-610`) ends the
  thread with no receipt; the schedule stays `arming` and no face says the
  meeting was not recorded (seen in the rig, `RECON.md` §6).
- **Write a thought creates a record on press**, before any text
  (`RECON.md` §8).

## 7. Duplicates and overlaps

| One job | Homes today |
|---|---|
| Start a recording | Dock orb, Capture ▸ Record meeting, Meetings ▸ Record meeting, Meetings ▸ RECORD wing ▸ Record meeting, Today ▸ Record now, Today ▸ NEXT ▸ Record, Desk ▸ New Meeting |
| Talk | Floor TALK, Capture TALK, Speak ▸ Talk, the hotkey |
| Schedule a recording | Today ▸ Record when it starts, Capture ▸ Schedule (blank form), Settings ▸ Meetings ▸ auto-record |
| Get a meeting's text out | Meeting ▸ Send, More ▸ Export MD / Export SRT, aftercare's Slack export route |
| Read a meeting's products | Outcomes, ARTIFACTS (a copy of Outcomes) |

## 8. Constraints a build must keep

- The meeting pipeline is the keep list: import → summary → decisions and
  owners → confirm, list ▸ detail with Back. Do not move it.
- Audio durability: the journal and same-ID recovery after a kill
  (`MODULE-FOLLOWUP.md`) must stay. Moving journal writes off the IO thread
  must keep "accepted chunk is on disk before the Stop snapshot".
- The audio floor: one owner of the microphone at a time (hotkey, browser,
  meeting) — `holdspeak/runtime/plugin_queue.py:18-22` names it.
- Egress: plugins that propose an outside effect stay proposal-only
  (`allow_actuators=False`, `holdspeak/meeting_plugins.py:79`); Send is the
  Send well's (`../send/`).
- The stored names `meeting`, `intel`, `artifact`, `dictation` stay in code
  and MCP. Only the words on the face change.
