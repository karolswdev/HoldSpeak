# 04 — THE SOBER EYE

A first-contact walk of HoldSpeak by someone with no history with the product.
Five jobs, a stopwatch, a move counter, and no documentation until the walk ended.

- **Build walked:** `backend_commit=93f9524f682aacf2fdb6138fa259506a338a1e2f`,
  `frontend_build=f818c13f80fd4d93` (web bundle rebuilt from `main` before booting).
- **Boot:** `HOME=<isolated> HOLDSPEAK_WEB_PORT=8899 .venv/bin/holdspeak web --no-open`,
  fresh database at `<HOME>/.local/share/holdspeak/holdspeak.db`.
- **Browser:** Playwright Chromium, 1440x900.
- **Microphone:** never used. Job 1 stopped at the point the product needed it, as briefed.
  Audio entered only through the Meetings file-import path, with
  `tests/fixtures/core_path_smoke_16k.wav`.
- **Model:** the LAN llama.cpp server at `http://192.168.1.43:8080/v1`
  (`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`), typed in by hand from the engine screen.

### Two honesty notes about the harness, up front

1. **I read `README.md` before the walk**, because the brief told me to boot the
   product the way README describes. That makes me *better* informed than a real
   newcomer, so every failure below is a lower bound, not an upper one.
2. **Seconds are machine time, not human time.** They measure how long the product
   took plus my scripted waits; they exclude the seconds a person spends reading a
   screen and deciding. Treat **moves** as the honest metric and seconds as a floor.
3. Two of my early clicks hit the wrong element because Playwright's text matcher
   picked a container instead of the button. Those are *my* errors and are **not**
   counted as moves or charged to the product. They are called out where relevant.

---

## THE MINUTE-ONE NARRATIVE

I opened `http://127.0.0.1:8899` and got a black page with two things on it:

> **Meetings: principal_right_required**
> [ Retry ]

That is the whole product at first contact. `01-job0-first-contact.png`.

I did not know what "principal" meant, or what a "right" was, or why a page about
*Meetings* was the thing reporting it. I clicked **Retry**, because it was the only
thing there. Nothing changed. `02-job0-after-retry.png`. I clicked it again.
Nothing changed. The console was filling with `401 (Unauthorized)` and
`WebSocket handshake: Unexpected response code: 403`.

**What I thought it was:** a server that had started but not finished starting,
or a permissions bug. It is neither. The runtime requires a token on the query
string — `?token=<32 chars>` — even on loopback:

```
$ curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8899/api/meetings
401
$ curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8899/api/meetings?token=aJtCG-…"
200
```

The token is generated on first boot and persisted, oddly, under the `meeting`
section of `~/.config/holdspeak/config.json` as `web_auth_token`
(`holdspeak/config/meeting.py:81`). The runtime prints a correct, tokened URL to
the terminal (`holdspeak/web_runtime.py:572`) and a real newcomer running plain
`holdspeak` would have a browser opened on it. So **the black screen is not what
the happy path looks like** — and I say that plainly.

**But the product authors the dead end itself.** One line *below* that correct
tokened URL, the first-run nudge prints this:

```
HoldSpeak web runtime is running at: http://127.0.0.1:8899?token=aJtCG-Lh5z5vYUw6MzNCGyTYGqI-uNhQ
  → Welcome! Say your first words on the Desk: open http://127.0.0.1:8899/
```

`holdspeak/web_runtime.py:430` prints `{url}/` raw; line 438 prints `{url}/setup`
raw. Neither is wrapped in `authenticated_browser_url()`, which every other
printed URL in the same block *is* (lines 568–577). I verified both dead ends in
a fresh browser context:

| URL the product printed | What renders |
| --- | --- |
| `http://127.0.0.1:8899/` | `Meetings: principal_right_required` + Retry (`33-job4-fresh-tab-bare-url.png`) |
| `http://127.0.0.1:8899/setup` | `Meetings: principal_right_required` + Retry (`34-job4-fresh-tab-setup-url.png`) |

The token lives in **tab-scoped** storage (`holdspeak/web_auth.py:120`), so this
is also what a bookmark hits, what a second tab hits, and what the user hits
tomorrow morning if they closed the tab. The recovery — re-read the terminal
scrollback for a 32-character secret — is not on any screen.

With the tokened URL, the product is a different thing entirely. One card, centred:

> VOICE TYPING
> **Dictate one sentence**
> Speak. Then edit and keep your text.
> [ Click to speak ]
> *Transcribed text appears here. You can also type.*
> [ Copy ] [ Keep as Note ] [ Continue later ]

`03-job1-arrival.png`. That is a genuinely good first screen: one job, one verb,
six words of instruction, no dashboard. It is the best thing I saw all walk.

---

## PER-JOB SCORECARD

### Job 1 — Speak and have the words become text: **FAILED**

| | |
| --- | --- |
| Moves | 1 (Click to speak) |
| Seconds | 4 to the failure |
| Shot | `04-job1-click-to-speak.png` |

I clicked **Click to speak**. Four seconds later the button relabelled itself
**Click to retry** and this appeared:

> ⚠︎ **Dictation did not finish. Your draft remains editable. Retry the capture.**

**The word that was missing is "microphone."** The browser had no microphone.
The product does not say so. It reports that a *capture* did not *finish* and
invites me to do the identical thing again. A person whose mic is muted, whose
permission dialog they dismissed, or who is on a machine with no input device
gets the same sentence and the same loop. "Retry the capture" is advice that
cannot work.

A new verb also appeared: **I need help**. I clicked it, because a newcomer
would. It does not give help. It closes the card and drops you into the full
Desk (`05-job1-i-need-help.png`) — a rename candidate at minimum, since it is
the "leave this card" verb wearing a support label.

Stopped here, as briefed.

### Job 2 — Have a meeting summarised: **PARTLY** (and only because I reloaded twice)

| | |
| --- | --- |
| Moves | 13 |
| Seconds | ~720 (15:26 → 15:38 wall) |
| Shots | `06`–`11`, `16`–`21` |

**Getting the meeting in was good.** Meetings dock tile → **Import** → a drop zone
that names its own formats (`.WAV .MP3 .M4A .OGG .FLAC .VTT .SRT .TXT`) → browse →
**Import**. Under three seconds later the meeting was listed and Whisper had
already transcribed it on the hub: *"The quick brown fox jumps over the lazy dog."*
Four moves, one of the cleanest paths in the product. `07`, `08`, `09`.

**Then the job stopped dead.** I opened the meeting (`10-job2-meeting-open.png`).
The card said `SEP 20 · SUMMARY OFF`. The footer said
`NO SUMMARY ROUTE · NO ASSIGNMENT`. The verbs available to me were **MD**,
**SRT**, and **Delete** — two exports and a destruction. **There was no verb that
asked for a summary anywhere on the meeting.**

I tried the **REVIEW** tab (`11-job2-review-tab.png`). Its headline is the word
**"Not run"**, under it `NOTHING ACCEPTED YET · PROPOSALS · NOT RUN`, then
`COVERAGE`, `MTG Transcript`, `1 TURN NOT YET READ`, `⚠ NOT READ`. A screen whose
headline is *Not run* and which offers no way to run it. The only enabled verb is
**Open transcript**; **Accept reviewed** is greyed.

I tried the window gear (`17-job2-meetings-gear.png`): `ACTIONS · Nothing here`,
`SPEAKERS · Nothing here`, `PROJECTS · Nothing here`, then `QUEUES / STATUS / QUEUED`.
Three stacked empty sections filling a window.

So I went and did Job 5 first (below), because the Desk was asking me to. After
setting the engine, I came back — and **the meeting card had not changed**. Still
`SUMMARY OFF`. Still `NO SUMMARY ROUTE · NO ASSIGNMENT`. Still no verb
(`16-job2-outcomes-after-engine.png`).

**Only a full browser reload produced the verb.** After F5, the same window read
`1 meeting needs a summary`, the row carried a `192.168.1.43 · LAN` badge, and a
**Run summary** button existed (`18-job2-after-reload.png`). It had not existed
sixty seconds earlier on the same data. A newcomer does not reload a desktop-style
app; they conclude the product cannot do it.

**Then the second silence.** I clicked **Run summary**. Nothing happened. No
spinner, no state change, no toast — for sixty-five seconds of watching. The hub
log says the work completed in about two seconds:

```
15:34:51 | holdspeak.intel_queue | Processed 1 deferred intel job(s)
```

The screen never said so. A second reload showed `● RAN` and an **Open** verb
(`20`). Opening it finally gave me the summary (`21-job2-summary-read.png`):

> SUMMARY  `192.168.1.43 · LAN`
> No substantive meeting content detected.

Honest output for a nine-word pangram. And **the provenance half of this job is
excellent** — "which machine ran it" is answered four separate ways on one screen:
the menu bar reads `→ 192.168.1.43:8080`, the title row, the summary block and the
window footer each carry `192.168.1.43 · LAN`. I never had to wonder. That is the
strongest thing in the product after the first-run card.

One more thing the log explains: the import deliberately does not queue the
intelligence run — `holdspeak/meeting_import.py:408` logs
`intel_enqueued=False` as a constant. So an imported meeting is *designed* never
to summarise itself, which is defensible — but the screen that results says
`SUMMARY OFF` and offers no verb, so the design reads as a bug.

**Confusions, in the order they hit me:** what is a "summary route"; what is an
"assignment"; what does `OFF` mean on a meeting; why does the headline say
`Nothing needs you` while the footer says `NO SUMMARY ROUTE`; why does `Not run`
have no run verb; did Run summary work.

### Job 3 — Write a thought and keep it: **PARTLY** (the button named for the job is the wrong door)

| | |
| --- | --- |
| Moves | 13 |
| Seconds | ~300 (15:38 → 15:43) |
| Shots | `22`–`32` |

There is a button on the Desk labelled **Write a thought**. I clicked it. It does
not open a place to write a thought. It opens the **Speak** window
(`22-job3-write-a-thought.png`), which is a dictation-routing console:

> TALK ◉ OPEN   LEVEL ▮▮▮▮
> *Talk, or type here*
> **LANDS IN · Codex CLI**   [↻ FOCUSED APP] [DRY RUN]
> **DICTATION · ⚠ NOT SET**  [Choose]
> ▸ Details
> THIS DEVICE            [Review] [Export]

Three things a newcomer stumbles on immediately. **"LANDS IN · Codex CLI"** — I
had not mentioned Codex, do not have Codex, and did not ask for my thought to go
anywhere. The product has decided my words will land in a coding agent.
**"DICTATION · ⚠ NOT SET"** with a **Choose** verb — a warning triangle for
something I have not been told I need. And **no verb that keeps anything**. The
two verbs are **Review** and **Export**.

I typed my thought into the box. No keep verb appeared. I expanded **Details**
and got telemetry (`26`): `PIPELINE LIVE / RUNS ON CODEX CLI / MIC CLOSED /
LANDED — / BUDGET 600 MS / STATE IDLE LISTENING BUSY LANDED REFUSED`. I clicked
**Review** (`27`): it switched to the JOURNAL tab, which said **NOTHING SPOKEN**.
My thought was not there. I opened the **Object** menu (`28`): every item —
Open, Get Info, Ask this project, Ask AI, Continue in thread, Edit, Rename,
Duplicate, Move to Zone, Delete, Delete — was greyed, with the footer
"Select an object". No "New note."

I found it on my ninth move, in the **Desk** menu (`29-job3-desk-menu.png`):

> **New Note ⌘N** · New Decision ⌘⇧N · New Knowledge · New Agent · New Workflow ·
> New Workbench · New Zone · New Thread · New Project

A proper note editor opened — title, rich-text body, tags, Cancel, **Save**
(`30`, `31`). I saved.

**And nothing happened on screen.** No toast, no note object on the Desk, no
Thoughts section on the arrival, no change anywhere (`32-job3-note-saved.png`).
I only know it worked because I asked the API:

```
$ curl "http://127.0.0.1:8899/api/notes?token=…"
{"notes":[{"id":"note_048357bd3da0","title":"Sober eye walk note", …}]}
```

So: the job is possible, but the verb advertised for it goes somewhere else, and
the verb that does it gives no receipt.

### Job 4 — Find them again after closing and reopening: **DONE** (in the same tab only)

| | |
| --- | --- |
| Moves | 4 |
| Seconds | ~20 |
| Shots | `33`–`37` |

I killed the hub and restarted it against the same HOME. In the **same browser
tab**, a reload restored everything: the Desk layout, the open windows, the
meeting on the arrival with its `● RAN` and `192.168.1.43 · LAN` badges, zero
moves needed (`35`). ⌘K, typing "sober", one click found the note and opened it
with its full text and a `Filed · Desk root` line (`36`, `37`). Durable and
findable — the job the product promises hardest, and it delivers it.

Two blemishes. First, ⌘K for "sober" also returned `Context · PROGRAM`,
`HoldSpeak Mobile Runtime — Roadmap · ROADMAP` and `Models · SETTINGS` — three
seeded items with no plausible relation to the query. Second, and larger: **this
only works in the tab that already holds the token.** A person who closed the tab
and reopened the product at the URL it prints gets the black
`principal_right_required` screen and finds nothing at all.

### Job 5 — Set up the engine from the screen alone: **DONE**

| | |
| --- | --- |
| Moves | 5 |
| Seconds | ~50 |
| Shots | `12`–`15` |

The Desk asks for this directly: `SETUP / No engine for summaries / [Choose an engine]`.
That is a good front door. It opens a **Models** window (`12-job5-choose-engine.png`)
that has clearly had care spent on it: it names the machine (`THIS MAC · M‑SERIES`),
timestamps its scan (`CHECKED 3:30 PM`), offers two downloads with their sizes
(Quick local Qwen 2.6 GB, Tiny local Qwen 508 MB), and shows a seven-row
assignment table — Thoughts & notes, Chat, Writing & dictation, Speech recognition,
Meetings, Agents & tools, Background — each with its own engine dropdown and a
`THIS DEVICE` badge.

**Add an engine** → a **Server address** field → I typed the LAN URL → **Check**
→ instantly `● READY  Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf` and a new verb,
**Use this for summaries** (`14`). One click and the Desk's setup row was gone
(`15`). Five moves, under a minute, no documentation needed. This is the best
flow in the product.

Three things still snagged:

- **The placeholder in the Server address field is the owner's own private LAN
  address**, `http://192.168.1.43:8080/v1`, hardcoded at
  `web/src/features/concierge/ConciergeCore.tsx:522`. Every user of this build
  sees a stranger's home IP presented as the example.
- **The found engine never joined THE SET.** After Check said READY, all seven
  rows still read `Quick local Qwen · ○ WAITING` and the footer still read
  `7 GROUPS · 1 ENGINE · 7 WAITING`. Two competing commitments sit on one screen:
  `Use this for summaries` (the one that worked) and `Use these` (permanently
  greyed, pointing at a model I had not downloaded, with no text saying why it
  is disabled).
- **`Speech recognition → Quick local Qwen`.** A text LLM is proposed as the
  speech-recognition engine. Whisper had already transcribed my meeting by then.
  A newcomer reading that row learns something untrue about the product.

---

## THE NOUN COUNT AT FIRST CONTACT

Every distinct label a newcomer meets in the first two minutes — the first-run
card, then the Desk behind it. **38 labels.**

**First-run card (7):** VOICE TYPING · Dictate one sentence · Click to speak ·
Copy · Keep as Note · Continue later · I need help

**Menu bar (7):** HoldSpeak · Desk · Object · Go · Window · THIS DEVICE · Search ⌘K

**Arrival (9):** 1 need you · NO CALENDAR · Connect calendar · SETUP ·
No engine for summaries · Choose an engine · BRIEF · Generate · No brief yet

**Talk bar (4):** TALK · Write a thought · Record meeting · Schedule

**Dock (11):** Intelligence · Speak · Meetings · Agents · Settings · Floor ·
Desk memory · Delivery · Panes · Hide the menus · Places

Of those 38, exactly **five** did anything for the five jobs: Click to speak,
Meetings, Choose an engine, Write a thought (wrongly), and Search ⌘K. The Desk
menu's **New Note** — the item I actually needed for Job 3 — is not among the 38;
it is one level down, behind a menu named after the workspace.

Two arithmetic problems in that list. The headline says **"1 need you"** while
two unmet asks are visible directly beneath it (no calendar, no engine); after I
set the engine it flipped to "Nothing needs you" with the calendar row still
unconnected on screen. And in the Meetings window, `No meetings yet` appears
twice at once — as the headline and as the empty state, one above the other
(`06-job2-meetings-window.png`).

---

## RANKED PAIN LIST

Ranked by what actually cost me time and confidence.

**1. `principal_right_required` on a black page — the Desk, first contact.**
The screen was `Meetings: principal_right_required` with a Retry that can never
succeed. The product prints two URLs in its own welcome nudge that land here
(`holdspeak/web_runtime.py:430`, `:438`), and the token lives in tab-scoped
storage, so a bookmark, a second tab, or tomorrow morning all land here too.
Nothing on the screen names the cause or the fix. Word: **principal_right_required**.

**2. The two invisible reloads — Meetings window.**
Setting the engine did not make **Run summary** appear; a page reload did.
Clicking **Run summary** did not show the result; a second reload did. The work
took two seconds (`Processed 1 deferred intel job(s)`) and the screen stayed
silent for sixty-five. Between those two silences sits the whole meeting job.
Words: **SUMMARY OFF**, **Not run**.

**3. "Write a thought" opens a dictation router — Talk bar → Speak window.**
The button named for the job leads to `LANDS IN · Codex CLI`, `DICTATION · ⚠ NOT SET`,
and the verbs Review and Export. It took nine moves to discover that the real
answer is **Desk → New Note ⌘N**. Words: **LANDS IN · Codex CLI**.

**4. No verb where the screen states a missing outcome.**
`SUMMARY OFF` (no verb), `Not run` as a headline (no verb), `NO SUMMARY ROUTE ·
NO ASSIGNMENT` (not clickable), `Accept reviewed` greyed with no reason,
`Use these` greyed with no reason. Five places where the product tells me
something is undone and offers nothing to do about it. Word: **Not run**.

**5. Saving gives no receipt.**
The note saved correctly and the screen showed nothing at all — no toast, no
object, no arrival entry. I had to query the API to learn it had worked. Word:
(there is none — that is the complaint).

**6. Vocabulary that assumes the implementation.**
`principal_right_required`, `NO SUMMARY ROUTE`, `NO ASSIGNMENT`, `PROPOSALS`,
`COVERAGE`, `MTG`, `1 TURN NOT YET READ`, `BUDGET 600 MS`, `STATE IDLE LISTENING
BUSY LANDED REFUSED`, `DRY RUN`, `BLOCKS`, `LEARNED`. None of these are defined
anywhere I could reach from the screen.

**7. The mic error that never says "microphone."**
"Dictation did not finish. Your draft remains editable. Retry the capture."
Retrying cannot fix a missing microphone. Word: **capture**.

**8. A stranger's home IP as the shipped example.**
`http://192.168.1.43:8080/v1` as the Server address placeholder
(`ConciergeCore.tsx:522`).

---

## THE PROMISE GAP

**`docs/WHAT_IS_HOLDSPEAK.md` is not the problem.** It is unusually honest and it
predicted most of what I hit: *"It does not certify that each workflow works on
your installation. The project is still before first-use acceptance."* ·
*"Capture and intelligence are separate stages. Having a transcript does not mean
a summary has been generated."* · *"The first meeting-result acceptance remains
open at this snapshot."* · *"This is a suggested learning order. It is not an
implemented onboarding wizard."* If I had read that first I would have been
surprised by less. The gap is almost entirely with `README.md`.

| README says | What happened |
| --- | --- |
| "Open the local URL that HoldSpeak prints." (README:29) | It prints three. Two of them — the Welcome nudge and the Setup nudge — are tokenless and render `principal_right_required`. |
| "Select **Dictate one sentence** … Select **Copy** or **Keep as Note**." (README:30-33) | The card is real and good. Both verbs are unreachable without a microphone, and the failure never says "microphone". |
| "The **arrival** shows work that needs you, unfinished **Thoughts**, a brief, and recent Meetings." (README:62) | Meetings and the brief slot appeared. **No Thoughts section ever appeared**, before or after I saved a note. |
| "Review a meeting. Record or import a meeting. Review the transcript, **decisions, action items, and artifacts**." (README:45) | Transcript: yes, fast, clean. Decisions / action items: `Nothing here`. The ARTIFACTS tab was never populated. |
| "Teach a dictation correction: Select **Wrong** on a result, correct the words or the route, then **Teach**." (README:43) | I never saw a **Wrong** verb on any screen. Gated behind a successful dictation, i.e. behind the microphone. |
| "Open **Settings > Models** to use the **Concierge** … Check the engine and host for each group before you select **Use these**." (README:76-79) | The Concierge is real and good, and I reached it from the Desk rather than Settings. But **Use these** was greyed for the entire session with no explanation, and the engine I successfully added never entered the seven-group table. The verb that worked was **Use this for summaries**, which README does not mention. |
| "The [MCP sidecar] exposes **222 tools across 40 families**." (README:117) · "**14 built-in plugins**." (README:121) | Nothing in this sentence touched any of the five jobs. It is a number aimed at a reader who is not trying to get work done. |
| "Find earlier work: Search Notes, Meetings, Decisions, Threads … from one Desk memory window." (README:51) | **True.** ⌘K found the note across a hub restart in four moves. The one promise the product over-delivers on. |

The shape of the gap: **README describes a product whose jobs are wired end to
end. What exists is a set of well-built rooms with the doors between them
missing.** Import is excellent and stops. The Concierge is excellent and does not
reach the table below it. The note editor is excellent and reports nothing. The
search is excellent and is the only thing that closed a loop unaided.

---

## WHAT YOU WOULD DELETE

Interfaces I met that did nothing for any of the five jobs.

**Delete outright:**

- **The Meetings window gear pane** (`17-job2-meetings-gear.png`). Three stacked
  `Nothing here` sections — ACTIONS, SPEAKERS, PROJECTS — filling a window, plus a
  QUEUES/STATUS row. It cost me a move and taught me nothing.
- **The `▸ Details` telemetry block in Speak** (`26`). `PIPELINE LIVE / RUNS ON
  CODEX CLI / MIC CLOSED / LANDED — / BUDGET 600 MS / STATE IDLE LISTENING BUSY
  LANDED REFUSED`. This is a debugger, on the face, one click from a button
  labelled "Write a thought".
- **The duplicate `Delete` in the Object menu** (`28`). It appears twice in one menu.
- **`NO SUMMARY ROUTE · NO ASSIGNMENT`** as a footer badge. It is three
  implementation words for a state the same window already says twice
  (`SUMMARY OFF`, `1 meeting needs a summary`).
- **The `OFF` badge on a meeting row.** It survives after the engine is
  configured and means nothing a reader can act on.
- **`I need help`.** It gives no help. It is the "close this card" verb.
- **The dock tiles I never had a reason to touch across all five jobs:**
  Agents, Floor, Delivery, Panes, Places, Hide the menus. Six of eleven dock
  slots earned nothing in a complete first session. I am not claiming they do
  nothing — I am reporting that a new user doing the five core jobs never needs
  them, and they are the majority of the dock.
- **"222 tools across 40 families" from README.** It is a specification count in
  a document a new user reads to find out whether the product can summarise a
  meeting.

**Rename, don't delete:**

- **`principal_right_required`** → something that names the cause and the fix.
- **`Not run`** (REVIEW tab headline) → it should be a verb, not a state.
- **`Write a thought`** → it opens Speak, so call it what it opens; or wire it to
  the note editor that the Desk menu already has.
- **`I need help`** → `Skip` or `Go to the Desk`.
- **`Retry the capture`** → name the microphone.
- **`Speech recognition`** row in the Concierge → it is not offering a
  speech-recognition engine; it is offering an LLM.
- **`LANDS IN · Codex CLI`** → on a first run with no coding agent configured,
  this should not be the default destination for a person's first sentence.

---

## SHOT INDEX

All under `assets/sober-eye/`.

| # | File | What it shows |
| --- | --- | --- |
| 01 | `01-job0-first-contact.png` | The product at first contact: `principal_right_required` |
| 02 | `02-job0-after-retry.png` | After Retry: unchanged |
| 03 | `03-job1-arrival.png` | The first-run card, with the token |
| 04 | `04-job1-click-to-speak.png` | Job 1 failure: "Dictation did not finish" |
| 05 | `05-job1-i-need-help.png` | "I need help" drops into the full Desk |
| 06 | `06-job2-meetings-window.png` | Meetings: `No meetings yet` twice |
| 07–08 | `07`, `08` | Import drop zone; file selected |
| 09 | `09-job2-after-import.png` | Meeting landed; `NO SUMMARY ROUTE · NO ASSIGNMENT` |
| 10 | `10-job2-meeting-open.png` | Open meeting: `SUMMARY OFF`, verbs are MD/SRT/Delete |
| 11 | `11-job2-review-tab.png` | REVIEW: headline `Not run`, no run verb |
| 12–15 | `12`–`15` | Job 5: the Concierge, Add an engine, READY, applied |
| 16 | `16-job2-outcomes-after-engine.png` | Engine set, meeting card unchanged |
| 17 | `17-job2-meetings-gear.png` | Three `Nothing here` sections |
| 18 | `18-job2-after-reload.png` | **Run summary** appears only after reload |
| 19 | `19-job2-run-summary.png` | 65s after clicking Run summary: no change |
| 20–21 | `20`, `21` | `● RAN` after second reload; the summary with LAN provenance |
| 22–27 | `22`–`27` | Job 3: Speak window, Codex CLI, Details, Review → NOTHING SPOKEN |
| 28–29 | `28`, `29` | Object menu all greyed; **New Note ⌘N** found in the Desk menu |
| 30–32 | `30`–`32` | Note editor, filled, saved — and the silent result |
| 33–34 | `33`, `34` | Both printed URLs in a fresh tab: `principal_right_required` |
| 35–37 | `35`–`37` | After hub restart: desk restored, ⌘K finds the note, note reopened |
