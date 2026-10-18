# Capture: betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk, 69 shots,
2026-10-17) and `MODEL.md` (the code map). It covers INVENTORY rows 1 to 7:
Speak, the hotkey and the menu-bar glyph, Voice commands, Meetings, Record,
Scheduled recording and the calendar, and Capture. It uses the names in
`../PLAN.md` §2. Sending belongs to `../send/`; Today, Needs you and People
belong to `../daily/`; Engines to `../engines/`.

## 1. The job

The owner leads three people and sits in a platform sync, three 1:1s and an
architecture review every week. He wants HoldSpeak to get what was said and
decided into the machine **without him thinking about it**: the meetings on
his calendar record themselves, Stop is instant, and a minute after a
meeting ends he has a summary of **that** meeting, the decisions and
promises to keep, and the things the meeting asked for already drafted (the
follow-up, the ADR, the update to the support team). Between meetings he
holds a key, talks, and the words land where he is typing. He closes the
meeting window when everything in it is kept, dropped or sent.

## 2. What it is today

The full walk is in `RECON.md`. Capture is the strongest part of the
product: an imported transcript became a correct summary with the right
decisions and owners in 44 to 136 seconds, inside the Meetings window, with
`Back`. The walls are around it.

| Step | What happens | Shot |
|---|---|---|
| Import a meeting | `Import` switches wings to a drop zone. The form asks title, speaker, tags, **no date**: Thursday's 1:1 became Saturday's. | `21-*`, `22-*` |
| Get a summary | Four presses across two windows. `Use it` assigns nothing. Settings says `Meeting summaries · no engine` while three summaries run. | `24-*` to `27-*` |
| Read the outcomes | Good: two decisions, four owners, `Confirm · More`. `Confirm all 1` sits over four rows. | `41-meeting-outcomes-*` |
| Trust the summary | Thursday's summary says the retry question "was subsequently resolved by adopting Option A" — a decision made on Friday — and cites "the earlier 1:1", dated Saturday. | `45-sync-summary-cites-later-1440.png` |
| Get the ADR draft and the stakeholder update | They arrive as **tasks** for Jun and for him. ARTIFACTS holds one card that repeats Outcomes. Zero plugins ran on any meeting. | `42-meeting-artifacts-*` |
| See what changed since last time | The hub computes it; no face draws it. | — |
| Speak | `Set up speech to start` and `Engine · Ready` at once. Speak's Talk is dimmed, the floor TALK works. Words: `OPEN`, `LEVEL`, `LANDS IN`, `DRY RUN`, `HUGGINGFACE.CO`, and a Details panel of capitals. | `10-*` to `14-*`, `32-*` |
| End a Talk | When the browser went away mid-Talk, **the whole desk stopped answering for 65 s**. | `RECON.md` §5 |
| Record the next calendar meeting | **One press**, `Record when it starts` → `Armed for 21:14`. Then no face lists it, and when the fire failed in the rig, nothing said so. Capture ▸ Schedule is a blank form with no calendar. | `50-*`, `51-*`, `53-*`, `34-*`, `52-*` |
| Say a phrase to act | Search-only app, off by default; behaviors are URL, app, shell, type text; no desk verb. | `60-*` to `62-*` |
| Get something down now | Capture works; `Write a thought` saves an empty record on press; phone buttons float mid-screen. | `31-*`, `35-*` |

## 3. Why it fails

1. **Slow and native work runs in the desk's one loop.** The meeting Stop
   hang froze every window because Stop called CoreAudio on the hub's event
   loop; that is fixed, but a stuck audio device still needs a HoldSpeak
   restart, because the audio client lives in the hub process. Talk has the
   same fault today: its transcription and its engine calls run on the loop,
   and one Talk froze the desk for 65 s. The audio callback itself writes
   and `fsync`s files under a lock on CoreAudio's real-time thread.
   Capture is treated as part of the hub, not as a worker the hub can drop.
   (`MODEL.md` §2, §5)
2. **The meeting's products are wired to a dead path.** The README promises
   14 plugins with an ADR draft, a diagram and a stakeholder update. None
   runs: a summary job with an engine route plans an empty plugin chain, and
   the plugin host checks the *old* engine config, not Engines. The routing
   score for a clear architecture review stays under its threshold. So the
   things a meeting asks for come back as tasks for him, and the ARTIFACTS
   wing shows a copy of Outcomes. (`MODEL.md` §4; `42-*`)
3. **Time is not a fact of capture.** Import has no date. The summary reads
   the project's memory with no time limit and the prompt calls it all
   "earlier work", so a summary reports the future as history. "Since the
   last meeting" means any meeting on the desk. The run record does not
   show what was read, so he cannot catch it. A summary he cannot trust is
   worse than none. (`MODEL.md` §3, §6; `45-*`)
4. **One job, many doors, two truths.** Seven Record buttons; three Talk
   buttons with two readiness rules; speech readiness from two sources
   (Speak says not set up, Engines gives "Speech to text" a chat model);
   scheduled recordings set in three places and listed in none; Voice
   commands that cannot reach a single desk verb. (`MODEL.md` §7)
5. **The faces still talk in machine words** on Speak (`LANDS IN`, `DRY
   RUN`, `PIPELINE · LIVE · BUDGET · 600 MS`), in Meetings (`SUMMARISED`,
   `ART 01 · SUMMARY ITEMS`, `Confirm all 1`) and in the menu bar (`MIC
   HELD`). Capture says "thought" where the product says Note.

## 4. The design

### The concept

**A meeting is what was said, when it was said, and what it leaves
behind:** a summary of that meeting and what came before it, the decisions
and promises to keep, and the **Results it prepared** for him (the
follow-up, an ADR draft, a stakeholder update, a diagram), each one ready to
Send. **Speak** puts his words where he types. **Capture** is never allowed
to stop the desk.

### The words

| He sees | It replaces |
|---|---|
| **Record**, **Stop** (one verb everywhere) | Record meeting, Record a meeting now, REC, Record now, New Meeting |
| **Import** (opens the file picker at once) | Import → wing switch → Drop it here, or browse |
| **When was this?** (date and time, filled from the file) | — (no date asked) |
| **Records at 21:14** · **Cancel** | Armed for 21:14 |
| **Coming up** (armed recordings, in Meetings ▸ Record) | — (listed nowhere) |
| **Summary · 87 s · LAN** | SUMMARISED · 87 S · 192.168.1.43 · LAN · RAN · 20:26 |
| **Looked at** (a fold: the meetings and notes the summary read, with dates) | — |
| **Since 1:1 with Theo, Thu 15 Oct** (a line, then what changed) | since_last_meeting (hub only) |
| **To keep · 6**, **Keep**, **Keep all 4**, **Drop** (`../daily/` words) | 6 to review, Confirm, Confirm all 1 |
| **Prepared** (the meeting's Results), **Draft ready** on the action it serves | ARTIFACTS, ART 01 · SUMMARY ITEMS, plugin, artifact |
| **Prepare…** (ask for one more Result) | — (CLI `--reroute` only) |
| **Talk**, **Listening · Stop** | TALK, MIC HELD, Stop listening |
| **Set up speech · 144 MB** (once, where you pressed Talk) | Set up speech to start, Speech is not set up, HUGGINGFACE.CO |
| **Types into: the app in front** · **Try it here** | LANDS IN · FOCUSED APP · DRY RUN · Agent · This field |
| **Voice commands** (a Speak wing) | Commands (Search only), COMMANDS OFF, Command board |
| **New note** | Write a thought, New thought |

Names we stop using on the face: thought, artifact, plugin, intel, MIR,
pipeline, budget, floor, armed, dry run, `RECORDS`. The code keeps them.

### The meeting window (desktop, 1440)

The list ▸ detail with Back stays exactly as it is. One wing: **Outcomes**.

```
┌ Architecture review: idempotent retries ───────────────────── [Back] ┐
│ Fri 16 Oct, 11:00 · 1 min · Jun, Mira, Theo, me    To keep · 6       │
│                                                                      │
│ SUMMARY                                                              │
│ The team chose Option A, a client dedupe key, over a server dedupe   │
│ table, so that two real payments of one amount are never blocked …   │
│ ▸ Since Payments platform sync, Thu 15 Oct: the retry question is    │
│   decided · Jun's options page is done · 2 promises still open       │
│                                                                      │
│ DECIDED · 2                                          [ Keep all 2 ]  │
│  Adopt idempotent retries with a client dedupe key   [Keep] [More]   │
│  Roll out web first, then mobile                     [Keep] [More]   │
│                                                                      │
│ WHO OWES WHAT · 4                                    [ Keep all 4 ]  │
│  Jun   Write the ADR · by Wed       Draft ready ›    [Keep] [More]   │
│  Theo  Update the reconciliation job                 [Keep] [More]   │
│  Mira  Own the rollout plan                          [Keep] [More]   │
│  Me    Tell support duplicates stop  Draft ready ›   [Keep] [More]   │
│                                                                      │
│ PREPARED · 3                                          [ Prepare… ]   │
│  Follow-up to Jun, Mira, Theo        [Open as note] [Copy] [Send…]   │
│  ADR-014 Idempotent retries (draft)  [Open as note] [Copy] [Send…]   │
│  Update for the support team         [Open as note] [Copy] [Send…]   │
│                                                                      │
│ ▸ Transcript · 12 lines        ▸ Looked at · 2 notes, 1 decision     │
├──────────────────────────────────────────────────────────────────────┤
│ Summary · 87 s · LAN Qwen3.8 27B                    [Send] [More]    │
└──────────────────────────────────────────────────────────────────────┘
```

- **Since …** is one line under the summary, folded. It names the previous
  meeting of the same calendar series; else the last one in the same
  project; else the last one with the same people. Unfolded, it lists what
  closed, what is still open and what is new, each a link. No previous
  meeting: the line is not drawn.
- **Prepared** holds the meeting's Results. Each is a rendered draft (no
  `##`, no ids). *Open as note* files it in Notes; *Send…* opens the Send
  well (`../send/`) with the draft in it. Nothing leaves without his press.
  While a Result is being written, its row says "Writing… 24 s" in place.
  A failed one says why ("the LAN engine did not answer in 60 s") with
  *Write again*.
- **Draft ready ›** on an action row opens the Result that serves it. The
  promise "Jun writes the ADR" stays Jun's; the draft is a start for him.
- **Prepare…** lists what this meeting can still prepare, in plain words:
  *ADR draft, Architecture diagram, Update for stakeholders, Follow-up,
  Incident timeline, Requirements list, Risks, Milestones*. One press runs
  it on the Meeting summaries engine and adds a row. Kinds that need a
  connection (a GitHub issue, a Jira ticket) are not here; they are Send
  destinations.
- **Looked at** lists each meeting, note and decision the summary read,
  with its date. All of them are before this meeting.
- The footer is one engine line and the two verbs. The 4-step rail (`Record
  · Summary · Decide · Send follow-up`) moves to Today's meeting card, where
  it already lives (`50-*`); the window does not repeat it.

### The meeting window (phone, 393)

```
┌‹ Back  Architecture review ┐
│ Fri 16 Oct · To keep · 6    │
│ SUMMARY                     │
│ The team chose Option A …   │
│ ▸ Since Platform sync       │
│ DECIDED · 2   [Keep all 2]  │
│ ┌─────────────────────────┐ │
│ │ Adopt idempotent retries│ │
│ │ [Keep]          [More]  │ │
│ └─────────────────────────┘ │
│ WHO OWES WHAT · 4 [Keep all]│
│ PREPARED · 3                │
│ ┌─────────────────────────┐ │
│ │ ADR-014 (draft)         │ │
│ │ [Open] [Send…]  [More]  │ │
│ └─────────────────────────┘ │
│ ▸ Transcript  ▸ Looked at   │
├─────────────────────────────┤
│ LAN · 87 s   [Send] [More]  │
└─────────────────────────────┘
```

### Meetings ▸ Record (the one home for recording)

```
┌ Meetings ───────────────── MEETINGS  RECORD ─┐
│                                               │
│   [ ● Record ]      [ Import ]               │
│                                               │
│ COMING UP                                     │
│  21:15  Platform design follow-up             │
│         Records at 21:14          [Cancel]    │
│  22:00  1:1 with Mira    [Record when it starts]│
│  Mon 09:30  1:1 with Mira [Record when it starts]│
│  ▸ Another time…                              │
│                                               │
│ Record every meeting on my calendar   ( Off ) │
└───────────────────────────────────────────────┘
```

- **Coming up** is the calendar's next meetings, each with *Record when it
  starts*, and the armed ones with *Cancel*. It is the same list Today's
  NEXT card arms from, so a press in either place shows in both.
- A fire that fails never goes quiet. The row says **Did not record ·
  21:14 · <the reason in words>** with *Record now*, and the same line goes
  to Needs you while the meeting is still running.
- *Another time…* unfolds the manual form (title, date and time, length) in
  place, for a meeting that is not on the calendar.
- **Record every meeting on my calendar** is the auto-record setting, moved
  here from Settings ▸ Meetings (Settings keeps a link to it).
- **Import** opens the file picker at once; dropping a file on the Meetings
  window does the same. The form then shows **When was this?**, filled from
  the file (the date in a VTT or SRT header, a date in the file name, else
  the file's modified time) and the title from the file name. *Import*
  imports.
- **Capture ▸ Schedule** and the dock orb's long press open this wing. The
  orb's press records at once, as today.

Phone: the same order, one column; Record and Import are full-width
buttons; each Coming-up row puts its verb under the title.

### While recording, and Stop

- The recording runs in **its own capture process**, which owns the
  microphone and the system audio and writes the journal. The desk talks to
  it. The desk never calls the audio driver itself (decision 1).
- **Stop** answers in under a second, every time. The capture process gets
  one second to close its devices; if a device does not close, the desk
  ends that process. The audio is already on disk. The next Record starts a
  new process and works; there is no "Restart HoldSpeak to record".
- Inside the capture process, the audio callback only copies samples into a
  queue. A writer thread does the file writes and `fsync`s. Streams end with
  `abort()`, which does not wait for buffers to drain.
- The menu-bar glyph shows **Recording · 12:40** and its menu has *Stop*.
  When the desk is gone, the glyph says so ("Desk not running") instead of
  keeping the last activity.

### Speak

```
┌ Speak ─────────────── SPEAK  JOURNAL  LEARNED  VOICE COMMANDS ┐
│ Ready to talk · hold ⌥R anywhere                              │
│ ┌ TALK ─────────────────────────────────────────── Ready ─┐   │
│ │ [ Talk ]   ▁▂▃▅▃▂▁                                       │   │
│ │ Talk, or type here                                       │   │
│ │ Types into: the app in front ▾      [ Try it here ]      │   │
│ └──────────────────────────────────────────────────────────┘   │
│ Clean-up runs on LAN Qwen3.8 27B                              │
│ ▸ Details (behind RAW)                                        │
└───────────────────────────────────────────────────────────────┘
```

- **One Talk rule.** Every Talk (the floor, Capture, Speak, the hotkey)
  works when speech is set up. When it is not, the press opens *Set up
  speech · 144 MB* in place, once, and then listens. No Talk is ever dimmed
  in one place and live in another.
- **One speech truth.** Speak reads speech readiness from the same answer
  as Settings ▸ Engines. Engines never gives "Speech to text" to a chat
  model (`../engines/` owns that fix; this design depends on it).
- **No engine is not a fault for Speak.** Without a clean-up engine, the
  words land as said, and the line reads "Clean-up: off · Choose engine".
- **Listening** shows on the button and in the menu bar as *Listening ·
  Stop*, and on the glyph. Talk's transcription and clean-up run off the
  desk's loop, so other windows answer while it works.
- *Try it here* replaces `DRY RUN`: it puts the result in the box instead of
  typing it into the app. The typed text has a visible verb.
- `Details` (pipeline, budget, states) and the ⚙︎ wing's `RAW · READINESS`
  move behind RAW.
- **Voice commands** become a Speak wing (decision 3). A phrase can run a
  **desk verb**: *Record*, *Stop*, *New note*, *Ask …*, *Open Today*. Five
  phrases ship on: "start recording", "stop recording", "new note", "ask
  HoldSpeak", "open today". The old four behaviors (URL, app, shell, type
  text) stay under *Other*. No phrase can Send, change settings or grant
  authority; those stop for his press, as everywhere.

### Capture (phone first)

```
┌‹ Back  Capture             ┐
│ ┌─────────────────────────┐ │
│ │        ● Talk           │ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │        New note         │ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │        Record           │ │
│ └─────────────────────────┘ │
│ COMING UP                   │
│ 21:15 Platform design f/u   │
│ Records at 21:14  [Cancel]  │
│ 22:00 1:1 with Mira [Record │
│       when it starts]       │
└─────────────────────────────┘
```

- Three large buttons from the top, then the next two calendar meetings
  with their record verb. *Schedule* is gone; *Coming up* replaces it.
- **New note** opens an empty note and makes the record on the first
  character, not on the press.
- Desktop: the same window, 3 buttons in a row and the two Coming-up lines.

### What one press does

| Verb | Where | What happens |
|---|---|---|
| **Record** | Orb, Capture, Meetings ▸ Record, Today, a person's window | Starts the capture process; the glyph shows Recording; the orb turns into Stop |
| **Stop** | Orb, glyph menu, the live meeting | Ends capture in under 1 s; the meeting opens in Meetings with "Summary · writing…" |
| **Import** | Meetings, Meetings ▸ Record, drop on Meetings | Opens the file picker; then the one-line form with When was this?; then the meeting row |
| **Record when it starts** | Today, Meetings ▸ Record, Capture | Arms that calendar meeting; the row reads Records at HH:MM with Cancel |
| **Cancel** | An armed row | Disarms it; the row goes back to Record when it starts |
| **Keep** / **Drop** / **Keep all N** | Outcomes | As `../daily/` defines them: a kept promise or decision goes to Needs you and People |
| **Open as note** | A Prepared row | Files the draft in Notes, opens it |
| **Copy** | A Prepared row | Copies the rendered text |
| **Send…** | A Prepared row, the footer | Opens the Send well with this draft (`../send/`) |
| **Prepare…** | Outcomes | Lists the Results this meeting can still prepare; one press writes one |
| **Write again** | A failed Prepared row | Runs it again at once |
| **Talk** | Floor, Capture, Speak, hotkey | Listens; if speech is not set up, sets it up first in place |
| **Try it here** | Speak | Puts the result in the box, types nothing |
| **New note** | Capture | Opens an empty note |

### What is removed or parked (nothing is deleted)

- The **ARTIFACTS** wing and its `summary_items` card: parked
  (`web/src/pages/cores/history/_parked/`). The artifacts store stays; its
  Results show under Prepared.
- **Capture ▸ Schedule** (the blank form): its form moves under *Another
  time…* in Meetings ▸ Record.
- **The Meetings ▸ RECORD drop zone page**: replaced by the direct picker and
  the Record wing above.
- Speak's `Details`, the ⚙︎ wing's diagnostics, the Journal's raw fields:
  behind RAW.
- The **Commands** app as a separate window: becomes the Speak ▸ Voice
  commands wing. Its data and route stay.
- The **Calendar snapshot** review face: behind RAW, as `../PLAN.md` rules
  for builder tools. Its import stays reachable from Settings ▸ Accounts ▸
  Calendar.
- The 4-step rail inside the meeting window: it stays on Today's card only.

### What has to change underneath (`MODEL.md`)

- Talk's transcription and clean-up run with `asyncio.to_thread`, like the
  HTTP dictation route.
- The summary's memory read takes a time bound: only sources that started
  before this meeting started. Each excerpt carries its date. The run
  receipt stores the refs it read (*Looked at*).
- Import sends `started_at_ms` from *When was this?*.
- The plugin host takes its `llm` capability from the Meeting summaries
  engine in Engines. A job with a planned route plans its plugin members on
  the same route instead of dropping them.
- Prepared Results are chosen by what the meeting said, not only by an
  intent score: an action that asks for a draft ("write the ADR", "write
  the stakeholder update", "send a follow-up") schedules that Result; the
  follow-up is always prepared. *Prepare…* runs any other one on press.
- Aftercare's previous meeting is the same series, else the same project,
  else the same people.
- The recorder moves into a capture process; its callbacks only enqueue.

## 5. Decisions for the owner

1. **Meetings record in their own capture process.** A stuck audio device
   then never freezes the desk and never needs a HoldSpeak restart. It adds
   one small helper process while a meeting records. Recommended: yes. The
   in-process fixes (callback only enqueues, `abort()`, Talk off the loop)
   ship first either way.
2. **A meeting prepares its Results by itself after the summary**: the
   follow-up always, and each draft that one of its actions asks for (ADR,
   stakeholder update, diagram). Each costs engine time (30 to 90 s on the
   LAN engine) and never sends anything. Recommended: yes, automatic for
   those; every other kind on *Prepare…*.
3. **Voice commands reach desk verbs, with five phrases on by default**
   ("start recording", "stop recording", "new note", "ask HoldSpeak", "open
   today"). No phrase can send, change settings or grant authority.
   Recommended: yes.

## 6. How we know it worked

He imports Friday's architecture review (or records it). Then:

- **Within 3 presses and under 3 minutes**, in one window, he reads a
  summary that mentions nothing that happened after the meeting, keeps the
  two decisions and four promises, and opens the ADR draft and the update
  for the support team as notes, ready to send. *Looked at* shows only
  older sources, with dates.
- The Thursday sync's window says "Since …" nothing (it has no earlier
  meeting in its series), and Friday's says what changed since Thursday.
- He presses **Stop** on a real meeting and the meeting is saved in under
  a second; he presses **Record** again at once and it records, with no
  restart.
- While he Talks for 30 seconds, any other window answers in under a
  second.
- He arms tomorrow's 1:1 with Mira in **1 press** from Today or Meetings ▸
  Record, and sees it under Coming up in both.
- He says "start recording" and a recording starts.
