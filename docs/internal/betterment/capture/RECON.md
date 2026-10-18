# Capture: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. It covers
INVENTORY rows 1 to 7: Speak, the hotkey and the menu-bar glyph, Voice
commands, Meetings, Record, Scheduled recording and the calendar, and the
Capture window. I walked the jobs as a first-time user at 1440x900 and
393x852. I fixed nothing. The shots are in `shots/` (69 files). The rig is
in the footnote.[^rig]

The rig cannot open a microphone, and it has no native hotkey. So I walked
capture through the **import** path with three real transcripts, and I
walked Speak and Record up to the point where they need the microphone. The
"Could not walk" section at the end lists every gap.

The seed: one project, *Payments ledger cutover*, and three meetings of this
week with real transcripts, all linked to the project:

| Meeting | When (as imported) | How |
|---|---|---|
| Payments platform sync (Mira, Theo, Jun, me) | Thu 15 Oct 10:00 | hub import route, with a start time |
| Architecture review: idempotent retries | Fri 16 Oct 11:00 | hub import route, with a start time |
| 1:1 with Theo | Sat 17 Oct 20:22 (it was Thursday) | the face's Import, which asks no date |

The summaries ran for real on the LAN engine (qwen3.8-27b). The sync
transcript says the retry decision is *deferred* to Friday. Friday's review
*makes* it.

## The jobs I walked

1. **Get a meeting into the machine** (import, as the stand-in for Record).
2. **Read what the meeting decided and who owes what.**
3. **Get the meeting's written products**: the ADR draft, the architecture
   diagram, the stakeholder update that the README promises.
4. **See what changed since the last meeting.**
5. **Speak**: say a sentence and have it land as text.
6. **Record the next meeting on my calendar without remembering to.**
7. **Say a phrase that runs an action** (Voice commands).
8. **Get something down now** (the Capture window).

## 1. Get a meeting in

- **Meetings, empty**: `No meetings yet`, `Record meeting`, `Import`, a line
  `Record or import a meeting`, footer `RECORDS`
  (`20-meetings-empty-*.png`).
- **Import** does not open a file picker. It switches to the RECORD wing:
  `Record or import`, `Close`, `REC`, `Record a meeting now`, `Record
  meeting`, a drop zone `Drop it here, or browse` and the list `.WAV .MP3
  .M4A .OGG .FLAC .VTT .SRT .TXT` (`21-import-press-*.png`).
- After a file: `one-on-one-theo.txt`, `DROP ANOTHER FILE TO REPLACE IT`,
  `TITLE`, `SPEAKER`, `TAGS`, `COMMA SEPARATED`, `Import`
  (`22-import-file-chosen-1440.png`, `22-import-form-*.png`). There is **no
  date field**. The hub route takes a start time, but the face never sends
  one.[^date] My Thursday 1:1 became a Saturday meeting.
- One second after `Import`: the row `1:1 with Theo · Oct 17 · 1 min · 119
  words · Not run`, the head `1 meeting needs a summary`, a blue `Choose
  engine`, a chip `No engine for summaries` on the row and again in the
  footer (`23-imported-t01s-1440.png`).
- `Choose engine` opened **Settings ▸ Engines** in a second window: `No
  engine yet`, `Find on LAN`, `Add an engine`, and also `Speech is not set
  up · Set up speech · 144 MB` (`24-choose-engine-1440.png`).
- `Find on LAN` found the engine in 3.1 s. `Use it` added it, but every job
  still said `no engine` (`25-lan-*.png`). `Default engine` then the LAN row
  gave every job the engine except **Meeting summaries, which still said
  `no engine`**, and **Speech to text, which now said `Qwen3.8 27B`**, a chat
  model (`26-default-engine-assigned-1440.png`). The meetings started their
  summaries anyway, at once, all three (`27-summaries-running-*.png`).
- Summary times: 44 s, 87 s and 136 s, one after the other on the one LAN
  engine. The list then read `All summaries done`, each row `5 to review` or
  `6 to review`, and `This week · 3 meetings · 3 summaries · 17 to review`
  (`40-meetings-list-*.png`).

## 2. Read what the meeting decided

The meeting opens **in** the Meetings window, with `Back`
(`41-meeting-outcomes-*.png`). The face is good:

- `6 to review · OCT 16 · SUMMARISED · 87 S · 4 PEOPLE`, a SUMMARY panel,
  two topic chips in capitals, `Decisions · 2` each with `Confirm · More`,
  `Who owes what · 4` with owner and date chips (`THEO · NO DATE`, `JUN · BY
  WEDNESDAY`), `TRANSCRIPT · 12`, footer `192.168.1.43 · LAN`, `RAN · 20:26`,
  `Send`, `More`.
- The extraction was right: both decisions, all four actions, the right
  owners. The ADR and the stakeholder update came out as **actions for a
  person** ("Write the ADR…", owner Jun; "Write the stakeholder update…",
  owner Me), not as drafts.
- `Confirm all 1` sits over a list of four actions
  (`41-meeting-outcomes-1440.png`). I did not find what the 1 counts.
- `More` holds `Open transcript · Decide · Add to Project · Export MD ·
  Export SRT · Park` (`43-meeting-more-1440.png`).
- Speaker beads read `J M M T`: "Me" and "Mira" are both `M`.

### The summary cites meetings from the future

The Thursday sync's summary, made after the other two existed:

> "Theo will profile the slow reconciliation job by Thursday, **building on
> the earlier 1:1 finding** that the 10k batch size causes disk spills. The
> duplicate-charge issue … was deferred to Friday's architecture review,
> **where it was subsequently resolved by adopting Option A** (client-sent
> dedupe key) and a phased web-then-mobile rollout."
> (`45-sync-summary-cites-later-1440.png`)

The Friday review's summary does the same: "This builds on the earlier
reconciliation slowness finding and the dedupe pairing work with Jun"
(`41-meeting-outcomes-*.png`). Both "earlier" facts come from the 1:1,
which the desk dates Saturday. This reproduces the daily walk's finding
(`../daily/RECON.md` §7). The cause is in `MODEL.md` §3: the summary reads
the project's memory with no time limit, and the prompt calls it all
"earlier work". The meeting's run record does not show what it read.

## 3. The meeting's written products

- **ARTIFACTS** wing: a four-step rail `Record ✓ · Summary ✓ · 3 Decide · 4
  Send follow-up`, then `1 ARTIFACT`: `ART 01 · SUMMARY ITEMS`, the same
  decisions and actions as Outcomes in a narrow card
  (`42-meeting-artifacts-*.png`).
- No ADR draft, no architecture diagram, no stakeholder update, on any face.
  The hub agrees: `/api/meetings/<id>/plugin-runs` is empty for all three
  meetings.
- I forced the plugins through the CLI (`holdspeak intel --reroute … --profile
  architect --override-intents architecture,comms`). The chain was right
  (`mermaid_architecture`, `adr_drafter`, `stakeholder_update_drafter`,
  `decision_announcement_drafter`), but every model plugin came back
  `blocked: Missing capabilities: llm`. Only `project_detector` (no model)
  ran. The cause is in `MODEL.md` §4: two separate reasons stop every model
  plugin.

## 4. What changed since the last meeting

- The hub computes it: `/api/meetings/<id>/aftercare` returns
  `since_last_meeting` with the previous meeting and new actions.
- No face draws it. The only live reader of the aftercare route reads its
  counts for a desk card (`web/src/desk/intelligenceAttention.ts:128`); the
  "since last meeting" faces are all parked. The Room fetches the project's
  version; I did not see it drawn (projects cluster).
- "The last meeting" is the last meeting **of any kind** before this one,
  not the last one of the same series or project.[^prev]

## 5. Speak

- **Speak window** (dock, ⌃1; not in the phone's Go): `Set up speech to
  start · HOLD ⌥R ANYWHERE`, a strip `Speech is not set up ·
  HUGGINGFACE.CO · Set up speech · 144 MB`, the TALK plate with `Not ready`,
  a dimmed `Talk`, `OPEN`, `LEVEL`, a text well `Talk, or type here`, `LANDS
  IN · ↻ FOCUSED APP · DRY RUN`, then `Engine · Not set · Choose`, `Details`,
  and a footer `Review · Export` (`10-speak-open-1440.png`).
- The Recon's chip words (`HOLD NONE ANYWHERE`, `LISTENER FAILED`) are gone.
  New ones took their place: `OPEN`, `LEVEL`, `LANDS IN`, `DRY RUN`,
  `HUGGINGFACE.CO`; in Details `PIPELINE · LIVE · RUNS ON · — · MIC · CLOSED ·
  LANDED · BUDGET · 600 MS · STATE · IDLE LISTENING BUSY LANDED REFUSED`
  (`14-speak-details-1440.png`); in the ⚙︎ wing `ENGINE · Model missing ·
  Pipeline + delivery · RAW · READINESS · More diagnostics`
  (`12-speak-settings-1440.png`).
- Voice typing asks for a **chat engine** (`Engine · Not set`). After the
  LAN engine: `Engine · Qwen3.8 27B · 192.168.1.43 · LAN · Ready`, while the
  head still says `Set up speech to start`. Two answers to "can I talk".
- I typed a sentence, ticked `DRY RUN`, pressed ⌘Enter. Nothing happened in
  15 s. The face has no visible verb for typed text
  (`13-speak-typed-dryrun-1440.png`, `13-speak-dryrun-result-1440.png`).
- **Journal** `Nothing said yet`, **Blocks** `Global · Project · New block`,
  **Learned** `NOTHING LEARNED` (`11-speak-*.png`).
- **TALK on the desk floor and in Capture works when Speak's Talk is
  dimmed.** One press held the browser mic (fake device): the menu bar
  showed `MIC HELD`, the button turned brown, its name became `Stop
  listening` (`32-capture-talk-1440.png`, `32-talk-held-3s-1440.png`).
  Nothing else on the face said "listening".

### The hub stops answering after Talk

When the browser went away while TALK was held, **the whole hub stopped
answering for about 65 seconds**. A plain `GET /` timed out at 60 s, the
next took 5.4 s, and the log said `intent-router classify failed`
twice.[^stall] I saw the same stall once by accident, earlier in the walk.
The cause is in `MODEL.md` §2: the browser's Talk path runs the
transcription and the dictation pipeline (the engine calls) on the hub's
event loop. It is the same kind of fault as the meeting Stop hang.

## 6. Record the next meeting on my calendar

- The calendar reached the desk through `POST /api/calendar/snapshot/confirm`
  (two events tonight). The vision step that reads a calendar screenshot
  could not run: the LAN model has no vision.[^cal]
- **Today ▸ Day**: `Saturday · 2 MEETINGS AHEAD`, `NEXT · IN 35 MIN ·
  Platform design follow-up`, steps `Prep · Record · Summary · Send
  follow-up`, `Record when it starts` (`50-today-calendar-1440.png`). **One
  press** armed it: `Armed for 21:14` (`51-today-record-armed-1440.png`).
  This is the best capture press on the desk.
- Nowhere else shows it. The Meetings ▸ RECORD wing shows the import panel
  only (`52-meetings-record-wing-*.png`). No face lists armed recordings.
  The phone's Go has no Today.
- **Capture ▸ Schedule** opens a form with no link to the calendar: `Title`
  (`Scheduled recording`), `Mode · ONCE`, `When` (a date-time field),
  `Duration · 60 MIN`, `Cancel · Schedule` (`34-capture-schedule-*.png`).
- At 21:14 the armed recording did **not** start, and nothing said so. The
  fire thread crashed, the schedule stayed in state `arming` with no
  receipt, and at 21:16 Today simply showed the next meeting
  (`53-today-after-fire-1440.png`). The crash came from a rig gap (the rig
  has no voice session), but the product lesson holds: a failed fire is
  silent.[^fire]

## 7. Say a phrase that runs an action

- Search "voice command" finds nothing. Search "commands" finds `Commands ·
  PROGRAM` (`60-search-voice-commands-*.png`).
- **Commands**: `Add command · COMMANDS OFF · Enable in Settings · Command
  board · No voice commands` (`61-voice-commands-*.png`).
- **Add command**: `Spoken keyword`, `Command behavior · Open URL · Launch
  app · Shell command · Type text`, `Payload`, `Save command`, `Test without
  saving` (`62-voice-command-add-*.png`). None of the choices is a desk verb:
  a phrase cannot record a meeting, make a note or ask a question.

## 8. Get something down now (Capture)

- Desktop: **Window ▸ Desk ▸ Capture** (`30-window-*.png`). Phone: Go ▸
  Apps ▸ Capture (`31-phone-go-393.png`).
- The window: `TALK · Write a thought · Record meeting · Schedule`
  (`31-capture-alone-*.png`). On the phone, the four buttons float in the
  middle of an empty screen.
- `Record meeting` and the dock's orange orb (`Record a meeting`) both
  answer `NOT RECORDING · NO RECORDER ON THIS HUB · OK` in the rig
  (`33-capture-record-*.png`, `36-record-orb-press-*.png`). That is the
  rig's refusal, not the product's.
- `Write a thought` makes a record at once (`New thought · Saved 8:39 PM`)
  before a word is typed: the hub then held an empty note titled `Thought`.
  A second press, on the phone, opened the same empty record
  (`35-capture-thought-*.png`). The record is a "thought"; the product model
  calls it a Note.
- The phone dock is four unlabeled glyphs (`◈ ● ▣ ♧`) and the orb.

## Friction log

"Presses" counts presses and typed fields. "Wait" is measured machine time.
"Est." is my estimate for a first-time user who reads the screen.

| # | Job step | Presses | Wait / est. | What he expects | Where he stops |
|---|---|---|---|---|---|
| 1 | Find Import | 2 (Meetings, Import) | 2 s / 15 s | A file picker | A wing switch, then a drop zone |
| 2 | Import a transcript | 3 + title | 1 s / 30 s | The meeting with its real date | No date field; Thursday's meeting is dated Saturday |
| 3 | Get a summary | 4 (`Choose engine`, `Find on LAN`, `Use it`, `Default engine` + row) | 3 s + 44 s / 2 min | One press: "use the LAN engine" | `Use it` assigns nothing; `Meeting summaries · no engine` while summaries run |
| 4 | Read decisions and owners | 1 (open row) | 3 s / 30 s | The decisions, the owners | Works. `Confirm all 1` over four rows |
| 5 | Trust the summary | 0 | – / stuck | A summary of this meeting | It reports outcomes from later meetings as "earlier" |
| 6 | Get the ADR draft and stakeholder update | 1 (ARTIFACTS) | 2 s / 30 s | Drafts he can edit and send | One artifact that repeats Outcomes; the drafts are tasks for him |
| 7 | See what changed since last time | – | – / stuck | A "since last" panel | Computed by the hub, drawn nowhere |
| 8 | Speak a sentence | 1 (TALK) | – | Words appear | Speech not set up; Speak's Talk is dimmed while the floor TALK holds the mic |
| 9 | End a Talk | 1 | 65 s hub stall (browser gone) | Nothing else breaks | The whole desk stops answering |
| 10 | Record the next calendar meeting | 1 (`Record when it starts`) | 2 s / 5 s | Armed | Works. Only Today shows it |
| 11 | Schedule one by hand | 5 + typing | – / 40 s | Pick from the calendar | A blank form with a date field |
| 12 | Make a voice command that records | 3 + typing | – / stuck | "Record meeting" as a behavior | Only URL, app, shell, type text |
| 13 | Write a thought from Capture | 1 | 1 s | An empty note to type in | An empty record named `Thought` is saved before a word is typed |

## Could not walk (unknown)

- **Real audio.** The rig forbids the microphone. Record, Stop, the live
  transcript, the meeting HUD and the Stop hang were not walked. The Stop
  hang's root cause is bounded from code and the incident sample only
  (`MODEL.md` §5).
- **The hotkey (Right Option) and the menu-bar glyph.** The rig has no
  native listener and no Cocoa presence. Read from code only.
- **Speech setup.** The rig has no Whisper model, and downloading 144 MB
  was out of scope. "Ready to talk", the Journal with rows, Learned, and a
  correction were not seen. TALK ran on a transcription double.
- **The calendar screenshot read** (needs a vision engine) and **EventKit**
  (switched off in the rig).
- **Auto-record** (`all_calendar`, `room_linked`) was not switched on.
- Two `503 (Service Unavailable)` lines reached the browser console when a
  meeting opened. I did not find which request.

[^rig]: Isolated hub `scripts/graph_walk.py serve --scheduler
    --transcribe-double "…"` on port 8865 with `_isolated_hub_env` (scratch
    `HOME` from `mktemp -d`, every isolation switch from `CLAUDE.md`), run
    from the code of the owner's desk worktree
    (`wt-daily-delight-delivery-20261017`, `217001b2e`). Scripts:
    `capture/rig/start_hub.py`, `walk.py`, `clear.sh`, `poll.sh`, steps
    `s00.py`…`s29.py`; transcripts in `capture/rig/seed/`. Real LAN engine
    `qwen3.8-27b` at `192.168.1.43:8080`; nothing faked except the
    transcription double. Chromium headless via Playwright, 1440x900 and
    393x852 (mobile, touch, scale 2), with Chromium's fake media device.
    Hub stopped and scratch HOME removed afterwards.
[^date]: `holdspeak/web/routes/meeting_import.py:75` accepts
    `started_at_ms`; with none, `holdspeak/meeting_import.py:319-322` sets
    the start to "now minus the duration".
[^prev]: `holdspeak/meeting_aftercare.py:157-181` takes the meeting with
    the greatest `started_at` before this one, across all meetings.
[^stall]: `capture/rig/poll.sh` polled `GET /` every 0.5 s; the log is
    `capture/rig/poll-abandon.txt`: `20:34:16 000 60.006445`, then `20:35:17
    200 5.425783`. The step file is `capture/rig/s15.py`.
[^cal]: The confirm route answers 500 (`KeyError: 'Monday'`) when the
    weekday is capitalised: `holdspeak/web/routes/calendar_snapshot.py:176`
    does not lower-case it, while the extract path does
    (`holdspeak/services/calendar_snapshot_service.py:167`).
[^fire]: `holdspeak/web_server.py:1751` passes `self.voice_session.active_owner`;
    the rig's `voice_session` is `None`, so `scheduled_recording_conductor.py:610`
    raised `AttributeError` inside thread `sr-countdown-sr_57a41788c0da`. No
    receipt was written (`last_outcome` empty, `state` `arming`). On his
    desk `voice_session` exists, so this exact crash is a rig gap; whether a
    real fire records was not walked.
