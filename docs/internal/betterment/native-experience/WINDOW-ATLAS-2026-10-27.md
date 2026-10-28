# The window atlas — 2026-10-27

P0 of the [Window Program](WINDOW-PROGRAM-2026-10-27.md). Every window and door, shot in
realistic states and scored with the program's eight-axis rubric (0–3 each: Grammar, Text,
Honest states, Friction, Delight, Density, Consistency, Phone; 24 is the top). Part A is the
application windows of `web/src/desk/applications.ts`; Part B is the object windows and the
doors.

## Pass 2 — 2026-10-27 evening

Lane ATLAS PASS 2, on main `0a6ac88f3` (waves 1–3, #1511–#1529). Every row below was scored
again from the new shots, not from the lanes' notes. The PNGs in
[atlas-2026-10-27/](atlas-2026-10-27/) have the same names as in pass 1, so the links in Parts A
and B now open the pass-2 shot.

**How:** one isolated hub (the desk sweep's `desk` fixture, every isolation switch), the sweep
seed plus: `POST /api/desk/seed`, 6 notes (one with a person, a Project, a PR and a Jira key in
the text, tagged to a meeting and filed in a Project), 9 decisions, 16 Plan items, 9 more
meetings (3 failed in total), 8 people, a knowledge base, a sequence, a workflow, a thread.
Wallpaper *In Jupiter's orbit* (`hs.desk.atmosphere`; no hub API). A local OpenAI-compatible
stub engine named *Studio engine* answers Ask and *Find the tasks*; it was switched to 503 for
"engine down" and shut down for Engines ▸ Check all. Live "during" uses a capture stand-in
(`/api/state` with five transcript segments). A second, bare hub gave the empty faces. 1440
shots are the window + 24 px of floor; 393 shots are the whole screen; all 1×, each under
300 KB (pngquant; the full-desk shots are cropped). Every shot was looked at.

**New states shot:** `live-ready-*` (the ready sheet), `live-transcript-*` (during),
`ask-streaming-*`, `ask-answer-top-*` (the answer scrolled to its top), `ask-empty-hub-1440`,
`note-tokens-*` (objects in the text, the place line), `note-peek-*`, `note-margin-*` (an Ask
card and *Found in this note*), `meetings--record-*`. Components' rail is `components-*`, the
floating dock is in every full-screen shot (`desk-*`, `flow-*`, `door-*`), the feedback sheet
is `door-feedback-*-1440`.

### Scores, pass 2 (G T H F De Dn C P; 24 is the top)

| Window | G | T | H | F | De | Dn | C | P | Pass 2 | Pass 1 |
| --- | - | - | - | - | - | - | - | - | --- | --- |
| Live meeting (ready, during) | 3 | 3 | 3 | 2 | 2 | 3 | 3 | 3 | **22** | 10 |
| New decision | 3 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | **21** | 21 |
| Decision record (Decisions reader) | 3 | 3 | 3 | 2 | 2 | 3 | 2 | 3 | **21** | 12 |
| Note | 3 | 2 | 3 | 3 | 3 | 3 | 2 | 2 | **21** | 21 |
| Menu bar + menus | 3 | 2 | 3 | 3 | 2 | 3 | 2 | 2 | **20** | 21 |
| Meetings | 3 | 2 | 2 | 3 | 2 | 3 | 3 | 2 | **20** | 21 |
| Projects | 3 | 3 | 2 | 2 | 2 | 2 | 3 | 3 | **20** | 21 |
| Decisions | 3 | 3 | 2 | 2 | 2 | 3 | 3 | 2 | **20** | 15 |
| Components | 3 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | **19** | 10 |
| Room ▸ History | 3 | 2 | 2 | 2 | 2 | 3 | 3 | 2 | **19** | 9 |
| Meeting (object window) | 3 | 2 | 2 | 3 | 2 | 2 | 3 | 2 | **19** | 18 |
| Automation (one open) | 3 | 2 | 2 | 3 | 2 | 3 | 2 | 2 | **19** | 20 |
| Window switcher | 2 | 3 | 3 | 3 | 1 | 3 | 2 | 2 | **19** | 17 |
| People | 2 | 2 | 2 | 3 | 2 | 3 | 2 | 2 | **18** | 15 |
| Person | 2 | 3 | 2 | 3 | 2 | 2 | 2 | 2 | **18** | 18 |
| Needs you | 3 | 1 | 2 | 3 | 2 | 3 | 2 | 2 | **18** | 19 |
| Capture | 2 | 3 | 1 | 3 | 2 | 2 | 2 | 2 | **17** | 17 |
| Speak (+ wings) | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** | 17 |
| Settings (frame + 8 panes) | 3 | 1 | 2 | 2 | 2 | 3 | 2 | 2 | **17** | 18 |
| Setup | 3 | 2 | 1 | 3 | 2 | 3 | 2 | 1 | **17** | 18 |
| New Project | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** | 17 |
| Decision (object window) | 3 | 2 | 2 | 3 | 1 | 2 | 2 | 2 | **17** | 8 |
| Floor: icon menu / blank floor | 2 | 3 | 2 | 3 | 2 | 3 | 2 | – | **17** | 16 |
| Today | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 1 | **16** | 16 |
| Room ▸ Now | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 1 | **16** | 18 |
| Room from the floor icon | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 1 | **16** | 15 |
| Project as a pullout (now opens the Room) | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 1 | **16** | 15 (3 as a dead door) |
| Activity (+ wings) | 3 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | **16** | 17 |
| Calendar snapshot | 2 | 3 | 2 | 2 | 1 | 2 | 2 | 2 | **16** | 15 |
| Engines | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | **16** | 18 |
| Meeting, failed summary | 3 | 0 | 2 | 3 | 2 | 2 | 2 | 2 | **16** | – |
| Knowledge | 2 | 3 | 2 | 2 | 1 | 2 | 2 | 2 | **16** | 16 |
| Archive | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **16** | 15 |
| Phone desk (393) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **16** | 15 |
| Mission control | 2 | 3 | 3 | 3 | 1 | 2 | 2 | – | **16** | 16 |
| Automations (list) | 3 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | **15** | 17 |
| Drawer | 1 | 2 | 3 | 3 | 2 | 1 | 1 | 2 | **15** | 15 |
| Mode / recipe | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **15** | 15 |
| Sequence | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **15** | 15 |
| Workflow | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **15** | 15 |
| ⌘K palette | 2 | 2 | 2 | 3 | 2 | 1 | 1 | 2 | **15** | 16 |
| Feedback sheet (1440 only) | 3 | 2 | 1 | 3 | 2 | 2 | 2 | – | **15** | 18 |
| Memory | 2 | 2 | 1 | 2 | 1 | 3 | 1 | 2 | **14** | 17 |
| Context | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | **14** | 16 |
| Processes | 3 | 1 | 2 | 2 | 1 | 2 | 2 | 1 | **14** | 15 |
| Agents | 2 | 1 | 1 | 2 | 2 | 3 | 1 | 2 | **14** | 17 |
| Note margin (new) | 2 | 0 | 2 | 3 | 2 | 2 | 1 | 2 | **14** | – |
| Project drawer | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | **13** | 15 |
| Agent's window | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 2 | **12** | 14 |
| Ask | 2 | 1 | 1 | 2 | 1 | 2 | 1 | 2 | **12** | 11 |
| Send preview | 1 | 0 | 3 | 3 | 1 | 2 | 1 | – | **11** | 11 |
| Artifact | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 2 | **11** | 11 |
| Shortcut sheet | 1 | 0 | 3 | 2 | 1 | 2 | 1 | – | **10** | 10 |

"–" = not shot at 393 (no keyboard, or the door is not on the phone). A pass-1 score that a
lane wrote after its fix is the "Pass 1" number. A lower pass-2 score is mostly a stricter look
at the same face, with a seeded engine and a fuller desk; the true regressions are listed
apart below. Still: **no window scores 2 or more on every axis** (Live comes closest: one 2 on
Friction, Delight).

### The ten worst now

1. **Shortcut sheet — 10.** `door-shortcuts-1440.png`. Unchanged: every word mono, caps
   headings APPS / NEW / WINDOWS / DESK, `^` where the menus write `⌃`, Esc listed twice, a centred
   overlay. "It is a terminal printout." `web/src/desk/components/window/ShortcutSheet.tsx`. Lane.
2. **Artifact — 11.** `artifact-1440.png`, `artifact-393.png`. Unchanged: no toolbar, the result
   in a card, Send as a heading over bordered destination cards with mono caps `FILE` and mono
   paths, "Filed · Desk root", a footer of Copy · More. The automation window shows the same result
   on the grammar. "Two faces for one result." `web/src/desk/pullouts/ArtifactPullout.tsx`,
   `web/src/desk/surface/send/SendWell.tsx`. Lane (with the Send preview).
3. **Send preview — 11.** `door-send-preview-1440.png`. Unchanged: mono caps `FILE`, `PREVIEW`,
   `FOLDER`, a mono path, card in card in card. `SendWell.tsx`. Same lane as 2.
4. **Ask — 12.** `ask-answer-1440.png`, `ask-answer-top-1440.png`, `ask-empty-1440.png`,
   `ask-recent-393.png`, `ask-enginedown-1440.png`, `ask-streaming-1440.png`, `ask-*-393.png`.
   Better bones (Ask D1: question at the top, the answer as a document, the rail), but:
   - "It answers and then shows me a list of links": when the answer lands the body is scrolled
     to *References* (17 rows), not to the answer; the question and answer are above the fold at
     1440 and 393. Shot `ask-answer-1440.png` (as it lands) against `ask-answer-top-1440.png`
     (scrolled by the rig).
   - "`What did we decide about project:proj-6d2a82a5e2dc?`" — a desk-grounded prompt shows a raw
     ref on the empty face, at both widths.
   - "I asked once and Recent lists it seven times": every ask of the same question is its own
     row, identical and cut (`Is the ledger cutover still o…` ×3 at 1440, ×7 at 393); the palette
     lists them as five *Thread* rows.
   - References repeat a row (*Freeze the ledger schema on Nov 12* as a proposal and a decision,
     *Friday team update* twice, *Ledger cutover sync* twice) and cite earlier Ask threads.
   - The engine down: "The engine did not answer · Try again" is plain words now, but the
     toolbar lamp stays green `● Studio engine` and nothing leads to Engines.
   - The answered face has no status bar; the asked face and the error face do.
   - Streaming: with a stub that streams one word per 0.35 s the face said `Reading your desk`
     and `Writing the answer · 6 s` with no words for 6.5 s (unknown: whether Ask streams to the
     face at all, or the desk read came first).
   - "Back to Thought" (the source band from a note) uses the retired word.
   Owner: `web/src/desk/components/AskPanel.tsx`, `askFace.tsx`, the prompt source. Lane.
5. **Agent's window — 12.** `lane-1440.png`. Toolbar now (Terminal), but 720 px of blank under
   "Claude Code is working · No steps reported yet", while the Agents list says this same run is
   `Session gone`. "Is it working or gone?" `web/src/desk/lane/LaneWindow.tsx`. Canvas (what a
   running agent's window shows).
6. **Project drawer — 13.** `drawer-project-1440.png`, `drawer-project-393.png`. W3-B's head is
   clean at 1440 (Icons), but its List view at 393 draws mono caps headers `NAME ▲ KIND WHEN
   STATE` and `NOTE · TODAY`; sources are a bordered box; the foot keeps Register · Get Info · a
   ghost Open. `web/src/desk/drawer/DrawerWindow.tsx`. Lane.
7. **Note margin — 14 (new face).** `note-margin-1440.png`, `note-margin-393.png`, and the README
   hero `desk-project-room.jpg`. The Ask card prints the answer's raw Markdown: `**Nov 14**`,
   `- Shadow traffic…`, `### Next step`. "Why are there asterisks in my note?" The Ask window
   renders the same text. `web/src/desk/thought-workspace/NoteMargin.tsx`. Lane (small).
8. **Agents — 14.** `agents-1440.png`, `agents-393.png`. Runs and installed tools still in one
   list (`Claude Code · 2.1.310 · Not connected` beside `Claude Code · Add the ledger freeze flag ·
   PR #412 open`); the status bar says `1 working` and no row says Working.
   `web/src/desk/conductor/ConductorWindow.tsx`. Lane.
9. **Processes — 14.** `processes-1440.png`, `processes-393.png`. `Owner-session · …`,
   `Node:inference-d380f9fc7c6dc84f`, `Egress operation 7ce37f`, `connection:github`; at 393 the
   second line still hangs left of the row's edge. `web/src/pages/cores/ProcessCore.tsx`. Lane.
10. **Memory — 14** (tied with Context, 14). `memory-1440.png`. The toolbar says `● Studio
    engine` and the line under it says `● No engine writes the desk pages · Choose engine`;
    the lists repeat Projects and People. "Which is it?" `web/src/pages/cores/MemoryCore.tsx`.
    Canvas (Memory against Ask), as pass 1 said.

### What regressed

Proven by the shots (a face that a lane said was healed and that is not on this desk):

- **Capture, empty** (`capture-empty-1440.png`): the window is shorter than its content, and
  `Nothing is coming up` (W2-ASKWELLS) is cut in half by the window's bottom edge. Owner: the fit
  of `chair:capture` (W3-A's fit-to-content or the window's default size).
- **Today at 393** (`today-393.png`, `today-since-393.png`): the status bar is two lines again
  (W1-KIT: "one 24 px line"), and under *To finish* each meeting row falls apart: the glyph on
  its own line, the name on the next, *Make the summary* as a separate row. `TodayView.tsx` +
  the kit StatusBar.
- **Engines at 393** (`engines-393.png`): the status bar's first fact is cut to `2 en…` to fit
  `huggingface.co` and *Set up speech*.
- **Automations** (`automations-1440.png` / `-393.png`): the same result reads `● New · 16 Oct`
  at 1440 and `● Done · 16 Oct` at 393.

Not regressions, but lanes' claims not seen here: the Meetings *Record* wing press at 1440
still leaves *Records* on screen (`meetings--record-1440.png` = `meetings-1440.png`); the
gear wing tab is a small bare `⚙` in the title bar (Meetings, Activity).

### Defects that remain, in the owner's words

- "There is a `⌂ This device` chip in my menu bar." The menu bar carries a dot + house + host
  word on every screen, both widths (`desk-1440.png`, every `door-*`). A.9 as amended rules out
  host/scope chips on working faces; the menu bar is the frame, not a window, but the owner's
  "relic" ruling reads on it. `web/src/desk/components/DeskMenuBar.tsx`.
- "Setup says no GitHub account was found; Accounts says GitHub works." (`setup-1440.png`
  against `settings-accounts-1440.png`.) `SetupCore.tsx` reads the CLI on this Mac; Accounts
  reads the checked connection.
- "YOLO, auto, preview, normal, OFF." Settings ▸ Agents, Speak, Notices, This Mac; `THIS DEVICE`
  orphan caption and `GO ▸ BUILDER · SEARCH` in This Mac. `settingsPrefs.tsx`.
- "Needs you is thirteen rows that say *Mentions cutover*." Watch hits are still named by the
  watch, each with *Open item*; `16 of 16 available`. `needsFace.ts`.
- "ERROR KEPT 2 SEGMENTS NOT DONE: SUMMARY, TOPICS, ACTION ITEMS." The failed meeting's summary
  line, both widths. `MeetingWindow.tsx`.
- "Open item dumps me in the project." Today ▸ *Open item* opens the Room's Now, seated low over
  Today, the item not shown (`flow-today-item-1440.png`).
- "*No engine*, but it ran on qwen." Automations' Engine column and the open automation's
  *With: Choose an engine* against results that name `qwen3.8-27b`.
- "None, None, None." People ▸ Next 1:1 for seven people.
- "Activity shouts `SWEEP 2 ROOMS`"; `Meeting saved · …` rows wrap to two lines at 1440.
- The palette: thread rows hold the whole answer (130 px rows), a desk decision row is four
  lines with a mono `10-27`, a stray *Hand to agent* under the top row.
- Mission control: flat grey, no names under thumbnails (unchanged).
- The Decision object window: the body repeats the title as its first line; the
  *Consequences* fold holds the *Why*.
- The Drawer: `Contents · 3` heading, inset two-line rows, a footer with one verb; the Archive's
  ghost Restore and Open on an empty list.
- The New Project Links placeholder is cut (`…or Confluenc`); the lone `Blocked` pill.
- The Room at 393: the Ask composer falls onto three rows (scope, engine, field, mic, Ask
  scattered).
- The feedback sheet after a pick: `● Not saved · Ledger rollback · Not supported` and no reason.

### Not reached, and why

- **Loading faces**: the route holds caught zero requests (the windows drew from reads the desk
  had already made). The five `*-loading-1440.png` files are pass-1 shots, restored unchanged.
- **An agent answer**: the seeded sessions read `Session gone`, so no ask card shows and there is
  no field to answer; `flow-agent-answer-1440.png` is the pass-1 shot.
- **The feedback sheet at 393**: the phone has no Desk menu in the menu bar; the door was not
  found. `phone-feedback-393.png` was not made.
- **Ask streaming words**: see Ask above (unknown).
- **Speak's Journal, Learned, Blocks with entries**: the rig has no journal recorder.
- **The note's peek card**: the hover on a token did not raise it in the rig (`note-peek-1440.png`
  shows the tokens without the card).
- Shots kept from pass 1 because their face is gone: `live--configure-meeting-393.png` (Live's
  gear wing moved to Settings ▸ Meetings, W2-LIVE), `today-since-send-1440.png` (the fold has no
  Send form now), `phone-three-next-393.png`, and the six `b-*.png` files (not shot by this pass).

### The docs' product images

- Regenerated: `docs/assets/readme/desk-meeting-review.jpg` (Today on the seeded desk, 1440×900,
  231 KB) and `docs/assets/readme/desk-project-room.jpg` (the Note tiled beside Ask, 198 KB);
  their README alt text now says what they show.
- Retired, not regenerated: `docs/assets/presence/*` (Presence is off); the drift ledger's S4.
- Left: `docs/demo.gif` (S3). Every other `docs/assets` image a live guide embeds is art
  (`pixellab/`).

## Part A — the application windows (lane ATLAS-A)

### How the shots were made

- One isolated hub (`tests/e2e/glass_infra._boot`, every isolation switch) in a scratch test
  that reused the desk sweep's helpers (`tests/e2e/test_desk_sweep.py`). The scratch test is
  removed.
- Wallpaper: *In Jupiter's orbit* (`hs.desk.atmosphere` in localStorage; the preference has no
  hub API, `web/src/desk/gl/atmospherePreference.ts`). Reduced motion on, 1× pixels.
- **Empty pass**: the fresh hub, onboarding done, nothing else.
- **Dense pass**: the sweep's seed (canvas week, Agents flight with a waiting ask, a failed
  summary, a decision to make, the Payments Room, a destination, a note, an automation with two
  results) plus more: 9 more meetings (two failed), 6 more decisions, 3 notes, 4 more people,
  10 more Room items. Totals on the face: 14 meetings, 8 decisions, 6 people, 4 projects.
- **Engine states**: Ask before any engine ("no engine"); then a local OpenAI-compatible stub
  engine (`tests/e2e/engine_stub_rig._StubHandler`) assigned to Answers (Ask), which answers a
  real Ask through the real hub; then the stub answering 503 (engine down); then the stub shut
  down and Engines ▸ Check all.
- **Loading**: the window's first read held in the page after the desk had drawn.
- **Flows**: presses counted by doing them in the browser (log below each row).
- Shots: [atlas-2026-10-27/](atlas-2026-10-27/), cropped to the window + 24 px of floor at
  1440; the whole phone screen at 393. Each shot was looked at.

### Scores at a glance

| Window | G | T | H | F | De | Dn | C | P | Sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Calendar snapshot (W1-TRUTH) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **15** |
| Room ▸ History (W1-FACES) | 3 | 2 | 2 | 2 | 2 | 3 | 2 | 2 | **18** |
| Live meeting (W1-TRUTH, W1-FACES; Lane / PR: W2-LIVE, W2-LIVE-2) | 3 | 2 | 3 | 2 | 2 | 2 | 2 | 3 | **19** |
| Speak (+ wings) (W1-FACES; Talk at 393, Learned: W3-B) | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| Components (W2-BUILDER) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **16** |
| Ask (W3-ASK-HUB) | 2 | 1 | 3 | 3 | 1 | 1 | 1 | 1 | **13** |
| Decision record (W1-TRUTH; Lane / PR: W3-A) | 3 | 2 | 2 | 2 | 1 | 2 | 2 | 3 | **17** |
| Memory (W2-ASKWELLS) | 3 | 2 | 2 | 2 | 1 | 3 | 2 | 2 | **17** |
| Context (W2-ASKWELLS) | 3 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **16** |
| Capture (W2-ASKWELLS) | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| Today (W2-ASKWELLS words) | 2 | 2 | 2 | 3 | 2 | 2 | 2 | 1 | **16** |
| Room ▸ Now (Ask: W2-ASKWELLS; Plan: W3-B) | 2 | 3 | 2 | 2 | 2 | 3 | 2 | 2 | **18** |
| People (W1-KIT; was 15 + W1-TRUTH; Lane / PR: W3-DELIGHT) | 2 | 2 | 1 | 3 | 3 | 3 | 2 | 3 | **19** (W3-DELIGHT; was 18) |
| Decisions (W1-TRUTH; Lane / PR: W3-DELIGHT) | 3 | 3 | 2 | 2 | 3 | 2 | 2 | 2 | **19** (W3-DELIGHT; was 18) |
| Engines (W1-TRUTH) | 3 | 2 | 3 | 2 | 2 | 2 | 2 | 2 | **18** |
| Processes | 3 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | **15** |
| Activity (W1-FACES) | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| Agents (ask card: W1-FACES) | 2 | 2 | 2 | 3 | 2 | 3 | 1 | 2 | **17** |
| Settings (frame + 8 panes) (W1-KIT; was 17) | 3 | 2 | 2 | 2 | 2 | 2 | 3 | 2 | **18** (W1-KIT; was 17) |
| Automations | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| New Project | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| Meetings (W1-KIT; was 18 + gear wing: W1-FACES; Lane / PR: W3-DELIGHT) | 3 | 2 | 2 | 3 | 3 | 3 | 3 | 3 | **22** (W3-DELIGHT; was 21) |
| Setup | 3 | 2 | 2 | 3 | 2 | 3 | 2 | 1 | **18** |
| Person | 2 | 3 | 2 | 3 | 2 | 2 | 2 | 2 | **18** |
| Automation (one open) | 2 | 2 | 3 | 3 | 2 | 2 | 2 | 2 | **18** |
| Projects | 3 | 3 | 2 | 2 | 2 | 3 | 3 | 3 | **21** (W1-KIT; was 19) |
| New decision | 3 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | **21** |

W3-DELIGHT (2026-10-27, canvas `canvases/delight-2026-10-27.html`): the kind hue on every dense list row and Needs-you row (a 20 px glyph on its kind's seat, the hover wash, the quiet selection of an unfocused list), the status-bar lamp that glows and pulses once on each save, the Note's task tick, the body's first-paint fade, Done settling a Needs-you row, and the object empty state (Meetings, Decisions, People). Delight rescored where it shows; Today stays 2 until its day light (slice 2).

No window scores 2 or more on every axis. The phone axis and the consistency axis are the
weakest across the board.

### What runs through many windows (fix once, heal many)

1. **The phone status bar eats the window.** At 393 the status bar wraps to two or three lines
   and puts a 44 px Button on its own row; content is cut under it (Today, Meetings, Setup,
   Speak, People, Engines). Owner: "half my phone is the footer". Owner: the status-bar species,
   `web/src/desk/surface/kit.tsx` (StatusBar) + `kit.css`. *Healed W1-KIT: one 24 px line, facts ellipsised, dense verbs at the right.*
2. **Column headers lie on the phone.** Meetings, People, Agents, Decisions, Processes,
   Engines, Automations and Setup draw four column headers over rows that have turned into two
   lines; the header cells no longer sit over anything. Owner: `web/src/desk/surface/objects/ObjectList.tsx`. *Healed W1-KIT: the header hides on a narrow surface; a dense Sort verb sits in the toolbar.*
3. **A press selects, nothing opens.** In Meetings and People a press on a row selects it; the
   meeting or person opens only on a double press or Enter
   (`ObjectList.tsx:12`, `:283`), and no collection toolbar carries an Open verb. Flow log:
   Dock ▸ Meetings ▸ press a row = 2 presses, 0 windows opened
   ([flow-meeting-1440](atlas-2026-10-27/flow-meeting-1440.png),
   [flow-person-1440](atlas-2026-10-27/flow-person-1440.png)). *Healed W1-KIT: one press opens a dense collection row; ⌘/shift-press, Space select; Enter opens. Setup keeps press-to-select (its open runs a fix).*
4. **Half the windows have no glyph in the title bar.** Today, Ask, Meetings, Agents, People,
   Decisions, Speak, Settings carry their object glyph; Projects, Memory, Engines, Setup,
   Context, Automations, Components, Activity, Processes, Live, Capture, Calendar snapshot do
   not. Owner: `web/src/desk/applications.ts` `surface.sprite` and the head in
   `web/src/desk/components/DeskWindow.tsx`. *Healed W1-KIT: every listed window wears a 20 px D glyph (nearest objects: Setup ▸ gear, Live and Calendar snapshot ▸ meeting, Activity ▸ note, Context and Components ▸ artifact, Automations, Processes and Engines ▸ cartridge, Capture ▸ the Record orb; the Room wears its project).*
5. **Three Ask wells.** Ask, Memory ("Ask your desk") and the Room ("Ask this project…") each
   draw their own composer, engine line and refusal. Owner: "which one do I use?"
   (`web/src/desk/components/AskPanel.tsx`, `web/src/pages/cores/MemoryCore.tsx`,
   `web/src/features/project-room/ProjectRoomCore.tsx`).
   **W2-ASKWELLS (2026-10-27):** one composer. Memory and the Room compose Ask's own row
   (`web/src/desk/components/askFace.tsx` AskComposer, AskEngineWord, AskSendButton); both
   hand the question to the Ask window, which runs it and keeps its answer, its
   not-answered line and its Recent. Their own wells are parked.
6. **Three loading faces.** Meetings and People show a faint grey ring (People also drops its
   toolbar while it waits), the Room shows a centred mono `Loading…`, Decisions and Projects
   show a toolbar over a blank body
   ([people](atlas-2026-10-27/people-loading-1440.png),
   [room](atlas-2026-10-27/room-loading-1440.png),
   [meetings](atlas-2026-10-27/meetings-loading-1440.png)). *Healed W1-KIT: the kit `Loading` (3 still ghost rows) in Meetings, People, Projects, Decisions and the Room.*
7. **The gear wings are the old desk.** The `⚙` wing of Meetings (*Meeting plumbing*),
   Activity (*Candidates and connectors*), Speak (*Configure dictation*) and Live (*Configure
   meeting*) keep the 2026-09 grammar: mono caps tokens (`QUEUED`, `CLI_ENRICHMENT`,
   `ENGINE`, `IDLE`, `TESTS ROUTING · NEVER TOUCHES THE LIVE MEETING`), rows that all say
   `actions` or `first-party`, spinners that never resolve.
8. **The agent ask card is mono caps.** `Asks you` (yellow mono chip) and `Asked 2 min ago`
   (mono bold) in a framed box, in Today and in Agents; its refusal is a red mono sentence with
   a `RETRY` caps Button ([flow-agent-answer](atlas-2026-10-27/flow-agent-answer-1440.png)).
   Owner: `web/src/desk/agents/AgentRow.tsx`, `web/src/desk/components/AgentLine.tsx`.
9. **Raw buttons in Settings.** Every number field (Working at once, Quiet from/until, Max
   nudges, Make at, the meeting retry fields) has two raw `<button>` steppers with 6 px `▲▼`
   glyphs (`web/src/desk/surface/gadgets.tsx:563`). Canon: every verb is the library Button;
   nothing under 12 px. *Healed W1-KIT: one "−  n  +" control of library Buttons.*
10. **The primary verb wanders.** Meetings makes *Choose engine* the blue verb over *Record
    meeting*; People puts its primary (*Open prep*) in the status bar; Agents' *Start an agent*
    is blue on an empty desk and plain on a full one; Projects' *New Project* is plain while
    Decisions' and People's *New* verbs are blue. *Healed W1-KIT: the make verb is the primary, always (rule in the kit Toolbar doc comment); Agents' ask verbs are plain.*
11. **Phone floor bleed.** In every 393 shot a desk-icon label (`Inbox`) shows in the strip
    between the sheet and the Dock (Part B owns the phone desk; noted here because every
    application shot shows it). **Healed, W3-A:** while a sheet stands the Go list under it is
    hidden (`screen.css`); the strip and the dock glass show the floor's plain material.

### The windows

Doors come from the manifest (`applications.ts`) and were checked in the Go menu shot
([flow-go-menu](atlas-2026-10-27/flow-go-menu-1440.png)) and the palette
([flow-palette](atlas-2026-10-27/flow-palette-1440.png)). "Builder" means the door is in Go ▸
Builder, which shows only with Settings ▸ This Mac ▸ Builder tools on; the shots opened those
windows through the hub.

#### Today — `intelligence:desk` (14)

Shots: [dense 1440](atlas-2026-10-27/today-1440.png) · [dense 393](atlas-2026-10-27/today-393.png) ·
[empty 1440](atlas-2026-10-27/today-empty-1440.png) · [empty 393](atlas-2026-10-27/today-empty-393.png) ·
[Since yesterday open](atlas-2026-10-27/today-since-1440.png) ·
[Send form inside the fold](atlas-2026-10-27/today-since-send-1440.png) ·
[Open item → Room](atlas-2026-10-27/flow-today-item-1440.png)

- **Jobs:** J2 (close a meeting's loops), J3 (prepare a 1:1), J4 (agent follow-through).
- **Doors in:** Dock tile 0 (phone 0), Go ▸ Today, ⌃1, ⌘K. **Out:** *Open item* opens the
  Room (not the item); *Open session*, *Open PR*, *Prep*, *Choose engine*, *Answer*.
- **Friction:** Dock ▸ Today ▸ *Open item* = 2 presses, and it lands in the Room's Now, not on
  the overdue milestone.
- **Scores:** G2 toolbar + status bar, but the agent ask is a framed card in the list and the
  1:1 is a card with a four-step stepper · T1 mono `Asks you` / `Asked 2 min ago`; the Since
  yesterday fold holds a Send form with `NEW DESTINATION`, `SYNCED`, `FILE` mono caps · H2 the
  dense day is true; the empty day says "Your meetings and calendar fill this." (a help
  sentence) and "Nothing this week"; the toolbar says `Needs you 32` over five rows · F3 one
  press to the day, two to an item · De2 timeline, glyphs and colour · Dn2 rows 38 px · C1 three
  verb weights in one list (blue *Open session*, grey *Open PR*, ghost *Open item*); the stepper
  is unlike Live's · P1 at 393 the status bar takes two lines and a button; row names cut
  (`Shard the reconciliation j…`); the ask card's verbs wrap.
- **Top defects (owner's words):** "Why is the agent question a yellow terminal box?" (AgentLine.tsx);
  "32 needs me but I see five" (`web/src/desk/pullouts/views/TodayView.tsx`); "Open item
  dumps me in the project, where is the item?"; "What is a destination form doing in Since
  yesterday?" (TodayView.tsx Since fold).
- **Fix needs:** a lane (ask card → a row; count = what is listed; Open item opens the item).
- **W2-ASKWELLS (2026-10-27), Today's words:** a DOM read of the seeded Today (rows, Since yesterday, This week, the 1:1) finds no mono and no caps left but the stepper's numbers, now sans; the rows Today leaves out are one quiet row `11 more in Needs you` (opens Needs you), so the toolbar's 14 adds up; the empty desk says `No meetings and no calendar yet.` + *Connect calendar* (no help sentence). Left: the phone status bar (KIT), *Open item* lands on the Room, not the item. Shots: `scratchpad/shots/w2-askwells/today{,-since}-*.png`.

#### Capture — `chair:capture` (14)

Shots: [dense 1440](atlas-2026-10-27/capture-1440.png) · [393](atlas-2026-10-27/capture-393.png) ·
[empty 1440](atlas-2026-10-27/capture-empty-1440.png)

- **Jobs:** J1 (capture a thought), J2 (record the next meeting).
- **Doors in:** phone Dock 1, Go ▸ Capture. No desktop Dock tile. **Out:** Talk, New note
  (the Thought window), Record.
- **Friction:** Go ▸ Capture ▸ Talk = 2 presses.
- **Scores:** G2 · T3 · H1 empty is a toolbar over a blank 30 px band, nothing says "nothing
  is coming up" · F2 · De1 bare · Dn2 · C1 *Record when it starts* is a ghost Button that reads
  as a label · P2.
- **Top defect:** "It is three words and a hole." Owner: `web/src/desk/chair/ChairHome.tsx`.
- **Fix needs:** a lane (one true empty line; the row verb visible as a verb).
- **W2-ASKWELLS (2026-10-27):** New note and Record carry their glyphs; *Record when it starts* is the library secondary Button (no ghost that reads as a label); read and empty, Coming up says `Nothing is coming up`; at 393 the three verbs are three 76 px tiles, the glyph over the word. Shots: `scratchpad/shots/w2-askwells/capture-{1440,393}.png`.

#### Speak — `surface-dictation` + Journal, Blocks, Learned, Commands, ⚙ Configure dictation (10)

Shots: [Speak 1440](atlas-2026-10-27/speak-1440.png) · [393](atlas-2026-10-27/speak-393.png) ·
[Journal](atlas-2026-10-27/speak--journal-1440.png) · [Blocks](atlas-2026-10-27/speak--blocks-1440.png) ·
[Learned](atlas-2026-10-27/speak--learned-1440.png) · [Commands](atlas-2026-10-27/speak--commands-1440.png) ·
[Configure dictation 393](atlas-2026-10-27/speak--configure-dictation-393.png)

- **Jobs:** USE_CASES "Dictate a coding request", "Correct and replay a phrase"; J1.
- **Doors in:** Dock 4 (desktop only), Go ▸ Speak, ⌃5, ⌘K, `/dictation`; Commands also from
  Go ▸ Voice commands (parked `surface-commands` → this wing). **Out:** Talk, Try it here, Copy,
  Review, Export, Choose engine, Manage in Settings.
- **Friction:** Dock ▸ Talk = 2 presses, but Talk says "Talk sets up speech first" on a desk
  without speech: the useful outcome needs Engines first.
- **Scores:** G1 the title reads "Speak" and the first wing reads "Speak"; the status bar holds
  a dotted level meter and a Button; on Journal/Blocks/Learned the toolbar's Review/Export move
  into the status bar · T1 Configure dictation: `ENGINE` mono caps caption, `No project` /
  `No blocks` mono amber, a lone *Open Settings* in a blank band · H1 Journal "Nothing said yet"
  as a plain line at the top left; Learned "Nothing learned"; the `Not ready` lamp is right ·
  F2 · De1 grey wells, no object · Dn2 · C1 Commands rows say "opens Ask HoldSpeak", the app is
  "Ask AI" · P1 toolbar on two rows, status bar on three with a 44 px Button.
- **Top defects:** "Speak, Speak." "Where did Review and Export go?" "The settings wing is the
  old terminal." Owner: `web/src/pages/cores/DictationCore.tsx`,
  `web/src/pages/cores/dictation/SpeakFace.tsx`.
- **Fix needs:** a lane (wing named for its job, one toolbar per wing, illustrated empty
  states; Configure dictation on the grid).
- **W1-FACES (2026-10-27):** the first wing is *Talk*; Review and Export sit in the Talk
  toolbar and Export, Search and Clear in the Journal's toolbar, never in the status bar; the
  status bar is one line on the phone (a 12-segment meter, the state, its fact); Commands say
  "opens Ask"; Configure dictation is the Settings label/control grid with *Manage in
  Settings* in its toolbar; Journal, Learned and Blocks draw the D mic over the true word and
  one quiet line. Left: Learned has no toolbar (it has no verb); the Talk toolbar still takes
  two rows at 393. Shots: `scratchpad/shots/w1-faces/speak-*`.
- **W3-B (2026-10-27):** the Talk toolbar is one row at every width: under 600 px the
  secondary verbs (Try it here, Copy, Review, Export) show their glyph, the word kept as the
  accessible name and hover title; the `Types into` caption folds. Learned gets a toolbar with
  *Export* (the wing's rules as Markdown) when it holds rules; an empty wing keeps its empty
  state and no toolbar. Shots: `scratchpad/shots/w3-b/after-speak-*`.

#### Ask — `ask:desk` (11)

Shots: [no engine 1440](atlas-2026-10-27/ask-noengine-1440.png) · [no engine 393](atlas-2026-10-27/ask-noengine-393.png) ·
[empty with engine](atlas-2026-10-27/ask-empty-1440.png) · [393](atlas-2026-10-27/ask-empty-393.png) ·
[About picker 1440](atlas-2026-10-27/ask-about-1440.png) · [About picker 393](atlas-2026-10-27/ask-about-393.png) ·
[answer 1440](atlas-2026-10-27/ask-answer-1440.png) · [answer 393](atlas-2026-10-27/ask-answer-393.png) ·
[thread](atlas-2026-10-27/ask-thread-1440.png) · [thread 393](atlas-2026-10-27/ask-thread-393.png) ·
[Recent](atlas-2026-10-27/ask-recent-1440.png) · [engine down](atlas-2026-10-27/ask-enginedown-1440.png) ·
[engine down 393](atlas-2026-10-27/ask-enginedown-393.png)

- **Jobs:** USE_CASES "Ask about project work", "Keep a useful answer"; J3.
- **Doors in:** Go ▸ Ask AI (⌘I in Go, Ctrl+I in the rig), ⌘K "Ask …" row, `/ask`. No Dock
  tile. **Out:** Save as note, Copy, Send…, Make it a task, Looked at (sources), Recent, Forget.
- **Friction:** Ctrl+I ▸ press the editor ▸ type ▸ Enter = 3 presses + typing (flow log).
  Narrowing About = 2 more presses + typing.
- **Scores:**
  - G2 toolbar and status bar are right; the composer is a 150 px blank well with a *Tools*
    fold, and the empty body is one centred bubble glyph over two grey bars.
  - T1 `No engine` in mono; the answer's `### Next step` renders as mono caps `NEXT STEP`; the
    engine-down line is red mono bold (`Studio engine did not answer`); the About picker's kind
    labels are mono (`Set`, `Project`, `Person`).
  - H2 no-engine and engine-down are stated, but the error names no way to Engines, and the
    seeded desk shows the same two generic prompts as the empty one. The status bar disappears
    on the error face.
  - F2 (above).
  - De1 grey, centred, sterile; a green "Y" avatar for the owner; no object of the desk in
    sight.
  - Dn1 at 1440 the composer takes a fifth of the window; at 393 it takes 40 % of the sheet and
    the answer is cut at its first heading.
  - C1 three Ask wells across the desk; Recent lists the same question four times as four
    threads; the picker rows are stacked bordered cards unlike any list.
  - P1 the About picker runs into the composer and a suggestion chip; the answer area is about
    300 px tall.
- **Top defects:** "It still looks like a chat demo." "The box I type in is bigger than the
  answer." "My desk is full and it suggests 'Summarize this week's meetings'." "Red monospace
  error, then nothing." Owner: `web/src/desk/components/AskPanel.tsx`,
  `web/src/desk/components/askFace.tsx`, `web/src/desk/components/about/AboutPicker.tsx`,
  `web/src/desk/components/ask-panel.css`; the answer material
  `web/src/desk/surface/Material.tsx`.
- **Fix needs:** a canvas (lane ASK, P1): composition, composer height, what the empty Ask
  offers on a full desk, About as a list view.
- **W3-ASK-HUB (2026-10-27), the hub gaps behind D1:** the answer's words arrive under the
  question as the engine writes them (`ask_text` frames by invocation id; the status bar keeps
  `Writing the answer · N s` with Stop); References say the hub's facts (`Note · just now`,
  `● Accepted`, a pull request's state); `Grounded in 4 records` in the verbs row opens each
  claim beside the record that supports it, and a reopened thread keeps them; an ask whose
  window closed keeps running, Recent shows it `● Writing…`, and its answer lands (only Stop
  ends a run). Shots: `scratchpad/shots/w3-ask-hub/{arriving,references,grounded-open,recovered-rail,recovered-arriving,recovered-landed}-1440.png`,
  `{references,grounded-open}-393.png`. Left: the phone still hides reference meta (D1's
  `@container` rule); a Jira item has no single-read tool, so it has no row to carry facts.
  Scores: H2→3 (the run says what it writes and comes back), F2→3 (a closed window loses
  nothing). Lane / PR: W3-ASK-HUB.

#### Meetings — `surface-meetings` + Record, ⚙ Meeting plumbing (18)

Shots: [dense 1440](atlas-2026-10-27/meetings-1440.png) · [393](atlas-2026-10-27/meetings-393.png) ·
[empty 1440](atlas-2026-10-27/meetings-empty-1440.png) · [empty 393](atlas-2026-10-27/meetings-empty-393.png) ·
[loading](atlas-2026-10-27/meetings-loading-1440.png) ·
[Meeting plumbing 393](atlas-2026-10-27/meetings--meeting-plumbing-393.png)

- **Jobs:** J2; USE_CASES "Import an existing discussion", "Review an architecture meeting".
- **Doors in:** Dock 1 (phone 2), Go ▸ Meetings, ⌃2, ⌘K, `/history`. **Out:** a meeting window
  (double press / Enter), Record meeting (Live), Import, Open actions, Choose engine.
- **Friction:** Dock ▸ press a row = 2 presses and nothing opens; the meeting needs a double
  press or Enter.
- **Scores:** G3 a real list view · T2 the gear wing: rows that all read `actions` + `2h ago`
  with `QUEUED` mono caps badges · H2 failed rows and "No engine for summaries" are true; the
  loading face is a faint ring · F2 · De2 · Dn3 31 px rows · C2 *Choose engine* is the blue
  verb, *Record meeting* is not · P2 header cells over two-line rows; the last row cut by the
  status bar.
- **Top defects:** "I clicked the meeting and nothing happened." "Why is Choose engine the big
  button?" "Meeting plumbing is a log dump." Owner: `web/src/pages/cores/HistoryCore.tsx`.
- **Could not verify:** the *Record* wing: the tab press left the Records face on screen at
  1440 (unknown whether the wing switched).
- **Fix needs:** a lane.
- **W1-FACES (2026-10-27), Meeting plumbing:** one list view; an action reads by its task with
  owner · meeting and *Open / Done* as a dot and a word; background work by its job (*Summary*,
  *Enrich with the CLI*) with *Waiting / Running / Failed / Done*; the filter now filters; no
  `QUEUED` token, no row that only says `actions`.

#### Agents — `conductor` (16)

Shots: [dense 1440](atlas-2026-10-27/agents-1440.png) · [393](atlas-2026-10-27/agents-393.png) ·
[empty 1440](atlas-2026-10-27/agents-empty-1440.png) · [empty 393](atlas-2026-10-27/agents-empty-393.png) ·
[answer refused](atlas-2026-10-27/flow-agent-answer-1440.png)

- **Jobs:** J4; USE_CASES "Reply to a coding agent".
- **Doors in:** Dock 3 (phone 4), Go ▸ Agents, ⌃4, `/conductor`. **Out:** Answer, Open (the
  agent's window), Start an agent.
- **Friction:** Dock ▸ press the answer field ▸ type ▸ Answer = 3 presses (refused in the rig:
  no live pane; the refusal face is the product's).
- **Scores:** G2 the ask card sits between the toolbar and the list · T1 mono caps ask card;
  the refusal "Not sent · a current registered session and pane identity are required — nothing
  was typed" in red mono with `RETRY` · H2 · F3 · De2 · Dn3 · C1 one list mixes runs (*Shard
  the reconciliation job · Working*) and installed tools (*Claude Code · 2.1.310 · Not
  connected*): the What column holds a version number; an unexplained orange square sits by
  the title · P2.
- **Top defects:** "Is Claude Code running or not? It is in the list twice." "Pane identity
  — what?" Owner: `web/src/desk/conductor/ConductorWindow.tsx`, `web/src/desk/agents/AgentRow.tsx`.
- **Fix needs:** a lane (runs list and installed tools apart; refusal in plain words).
- **W1-FACES (2026-10-27), the ask card (Agents and Today):** *Asks you* is a dot and a word,
  the age a quiet sans line, the card a soft plate (no ink frame, no stipple bar); the refusal
  is one quiet line with a dense *Try again*, and the pane-identity refusal reads "The desk
  cannot reach this agent's terminal · Nothing was sent". Not shot: in this rig the seeded
  sessions read *Session gone* (cause not known); proven by the vitest files.

#### Settings — `surface-settings`, panes You, Speak, Meetings, Notices, Accounts, Agents, Desk, This Mac (17)

Shots: [frame 1440](atlas-2026-10-27/settings-1440.png) · [frame 393](atlas-2026-10-27/settings-393.png) ·
[You](atlas-2026-10-27/settings-you-1440.png) · [Speak](atlas-2026-10-27/settings-speak-1440.png) ·
[Meetings](atlas-2026-10-27/settings-meetings-1440.png) · [Notices](atlas-2026-10-27/settings-notices-1440.png) ·
[Accounts](atlas-2026-10-27/settings-accounts-1440.png) · [Accounts 393](atlas-2026-10-27/settings-accounts-393.png) ·
[Agents](atlas-2026-10-27/settings-agents-1440.png) · [Desk](atlas-2026-10-27/settings-desk-1440.png) ·
[Desk 393](atlas-2026-10-27/settings-desk-393.png) · [This Mac](atlas-2026-10-27/settings-this-mac-1440.png)
(each pane also at 393 in the folder)

- **Jobs:** J6.
- **Doors in:** HoldSpeak menu ▸ Settings, Accounts (→ Accounts pane), Change places (→ Desk
  pane), ⌘K rows per field; parked Rhythm (`surface-cadence`) → Notices; `/settings`. **Out:**
  Engines ›, Setup ›, Meetings › Record, Add destination, Check.
- **Friction:** HoldSpeak ▸ Settings ▸ pane = 2 presses. Change places lands on the top of the
  Desk pane; Wallpaper is below Sounds, Presence and Speech: 2 presses + a scroll.
- **Scores:** G3 rail + label/control grid, save state in the status bar · T2 raw values
  `auto`, `preview`, `normal`, `OFF`, `YOLO`; an orphan caps caption `THIS DEVICE` with nothing
  under it; `GO ▸ BUILDER · SEARCH` caps hint; "1 sources" · H2 · F2 · De2 rail sprites,
  wallpaper stills · Dn2 raw `▲▼` stepper buttons at 6 px in every number field
  (`gadgets.tsx:563`) · C2 Accounts: an *Add Jira account* chip beside *Add account* Buttons;
  "Working at once" is both the caption and the label · P2 the rail becomes a list, the pane a
  page; Accounts host lines wrap alone.
- **Top defects:** "YOLO? auto? OFF in capitals?" "Change places should take me to the
  wallpaper." Owner: `web/src/pages/cores/SettingsCore.tsx`, `web/src/pages/cores/settingsPrefs.tsx`,
  `web/src/pages/cores/settingsWallpaper.tsx`, `web/src/desk/surface/gadgets.tsx`.
- **Fix needs:** a lane (enum labels in words, steppers as library Buttons, scope scrolls to
  its section).

#### Live meeting — `surface-live` + ⚙ Configure meeting (10)

Shots: [1440](atlas-2026-10-27/live-1440.png) · [393](atlas-2026-10-27/live-393.png) ·
[Configure meeting 393](atlas-2026-10-27/live--configure-meeting-393.png)

- **Jobs:** J2 (record).
- **Doors in:** Meetings ▸ Record meeting, Today ▸ Record now, Capture ▸ Record, `/live`. Not
  in Go. **Out:** Start meeting, Set up speech.
- **Friction:** Dock ▸ Meetings ▸ Record meeting ▸ Start meeting = 3 presses; on this desk
  speech is not set up, so the outcome is not reached.
- **Scores:** G1 a Record/Summary/Decide/Send follow-up stepper band over an empty transcript;
  the gear wing is the old grammar · T1 `ROUTING`, `PREVIEW`, `TESTS ROUTING · NEVER TOUCHES THE
  LIVE MEETING`, `IDLE`; "audio only" lowercase · H1 the status bar says `● Ready` (amber) next
  to "Speech not set up"; *Devices* spins forever in the gear wing; "Start a meeting to begin"
  · F2 · De1 · Dn2 · C1 the stepper differs from Today's · P1 the phone title bar shows only `▾`,
  no name.
- **Top defects:** "It says Ready and Speech not set up in one line." "Intent routing? Deferred
  plugin jobs?" "No title on the phone." Owner: `web/src/pages/cores/LiveCore.tsx`.
- **Not reached:** Live during a meeting (the rig has no capture runtime).
- **Fix needs:** a canvas (what Live is before, during and after; the gear wing's place).
- **W1-TRUTH (2026-10-27):** the status bar reads `● Speech not set up` (warn) and never `Ready` beside it; the phone title bar names `Live meeting` (a window with only a gear door folds to its name, `SurfaceWings name`); the stepper is Today's (kit `meetingSteps`: Prep · Record · Summary · Send follow-up). Shots: `scratchpad/shots/w1-truth/live-{1440,393}.png`.
- **W1-FACES (2026-10-27), gear wing only:** `Routing`, `Try a phrase` with one quiet
  sentence (no `TESTS ROUTING · …` caps), route facts in sentence case, the Summary state as a
  dot and a word, *Background work*, Devices says `Checking… N s` then `No answer` instead of
  a ring that turns forever. The canvas stays open.
- **W2-LIVE (2026-10-27), Lane / PR: W2-LIVE:** canvas
  `docs/internal/betterment/canvases/live-direction-2026-10-27.html` (A, "the transcript is the
  page", recommended; B, transcript and notes side by side). Built, slice 1: while it records
  the body is the transcript as a document (time mark from the wire's `start_time`, which the
  old stream never read, so every mark was empty; the speaker's name when the speaker changes;
  a bookmark as the ember mark; Listening at the foot); the status bar says the live state once
  (`Recording 12:04 · Summaries on <engine>` or `No engine for summaries`); Stop is the danger
  verb, Bookmark a toolbar verb, Settings the trailing verb (a glyph on the phone). The gear wing
  is gone: its parts are Settings ▸ Meetings ▸ Live meeting (`LiveMeetingTools`). Shots:
  `scratchpad/shots/w2-live/live-{before,during}-{1440,393}.png`,
  `settings-meetings-{1440,393}.png`. Left: Before's ready sheet (sources and engines as rows),
  After's rail at Summary in MeetingRecord, the phone status bar wraps to two rows while it
  records (four items).
- **W2-LIVE-2 (2026-10-27), Lane / PR: W2-LIVE-2, slice 2 (Before and After):** Before is the
  ready sheet (`LiveReady.tsx`): the meeting's name as a quiet line (sent with `PATCH
  /api/meeting` once the meeting is live; the hub's start takes no title), then *It will hear*
  (Microphone, System audio: the device from `/api/settings`, ● Ready) and *It will write*
  (Transcript: `Whisper base, on this Mac`, ● Ready or ● Not set up with *Set up speech · 144 MB*
  on the row; Summary: `<engine>, after the meeting`, ● Ready, ● Off, or ● No engine with
  *Choose engine*). "Start a meeting to begin" is gone; the steps band stays (the canvas keeps
  it); Set up speech left the toolbar. After: the meeting window already becomes the record (the
  same window, `MeetingWindow.tsx`); the record now has Today's rail under its toolbar
  (`recordSteps`: Summary now while he reads and decides, Send follow-up now when nothing waits),
  *Send follow-up…* as the primary, Settings as the trailing verb, and *Decide…* on every decided
  row (the record when it has one, else the decision's reader, else New decision). The phone
  status bar while recording is one line: no title (the title bar has it), the link only when it
  is not connected. Shots: `scratchpad/shots/w2-live2/live-before-{nospeech,ready}-{1440,393}.png`,
  `meeting-after-{1440,393}.png`. Left: the project line on the ready sheet (a meeting has no id
  before Start; Add to Project is on the record); the microphone level and an *Allow* verb (the
  hub sends no level or permission fact before a meeting); the section name stays *Decisions*
  (it holds proposed rows too, so *Decided* would not be true); the record's rows show their
  verbs on hover and focus (the ledger species), the canvas draws them always.

#### Setup — `surface-setup` (18)

Shots: [1440](atlas-2026-10-27/setup-1440.png) · [393](atlas-2026-10-27/setup-393.png)

- **Jobs:** J6; USE_CASES "Repair a broken installation".
- **Doors in:** HoldSpeak menu ▸ Setup, ⌘K, Settings ▸ This Mac ▸ Setup ›. **Out:** Use
  everything found, Check again, Open my desk, Set up speech.
- **Friction:** 1 press (*Use everything found*).
- **Scores:** G3 · T2 · H2 "From your calendar: Priya Karol" makes a person from the 1:1 title
  "1:1 Priya / Karol" · F3 · De2 · Dn3 · C2 · P1 toolbar on two rows, status bar on three with
  the `huggingface.co` chip alone on a line, "Your name" cut under the status bar.
- **Top defect:** "Priya Karol is not a person, that's me and Priya." Owner:
  `web/src/pages/cores/SetupCore.tsx`; the same name parse feeds People (below).
- **Fix needs:** a lane.

#### Context — `surface-constitutional-context` (14)

Shots: [1440](atlas-2026-10-27/context-1440.png) · [393](atlas-2026-10-27/context-393.png)

- **Jobs:** J4 (what every agent is told).
- **Doors in:** Go ▸ Builder ▸ Context (Builder tools only), ⌘K, `/context`. **Out:** Save.
- **Friction:** with Builder tools off: HoldSpeak ▸ Settings ▸ This Mac ▸ Builder tools ▸ Go ▸
  Builder ▸ Context = 6 presses.
- **Scores:** G2 · T2 · H1 empty says nothing about who receives it or whether it is on · F2 ·
  De1 a bare text area · Dn2 · C2 · P2.
- **Top defect:** "Is this sent to my agents right now?" Owner:
  `web/src/pages/cores/ConstitutionalContextCore.tsx`.
- **Fix needs:** a lane.
- **W2-ASKWELLS (2026-10-27):** the status bar always answers it: `● Every engine run reads this first` (the saved text is the first system message of every engine run, `holdspeak/intel/engine.py` `run_prompt`) or `Empty: no run reads it`; the editor is the page, edge to edge (no inset well). Left: Context has no door outside Builder tools. Shots: `scratchpad/shots/w2-askwells/context-{1440,393}.png`.

#### Automations — `surface-workbenches` (17) and one automation open (18)

Shots: [list 1440](atlas-2026-10-27/automations-1440.png) · [393](atlas-2026-10-27/automations-393.png) ·
[empty](atlas-2026-10-27/automations-empty-1440.png) · [one open](atlas-2026-10-27/automation-open-1440.png) ·
[one open 393](atlas-2026-10-27/automation-open-393.png)

- **Jobs:** J4.
- **Doors in:** Go ▸ Work ▸ Automations, ⌘K, `/workbenches`; Today ▸ "Friday team update has a
  new result" ▸ Open. **Out:** New automation, the automation window (Run now, Edit, Send…).
- **Friction:** Go ▸ Automations ▸ row (double press) ▸ Run now = 3–4 presses.
- **Scores (list):** G3 dense; the empty face is a page (prose line, template cards in a grid)
  · T2 empty templates in mono sub-lines, dashed ember "About: which meeting?" · H2 the row says
  Engine "No engine" while its newest result names `qwen3.8-27b` · F2 · De2 · Dn2 *When* wraps
  to two lines (42 px rows) · C2 · P2.
- **Scores (open):** G2 a 250 px empty band under the result · T2 `NEW` caps badge · H3 the
  failed run keeps its reason · F3 · De2 · Dn2 · C2 · P2.
- **Top defect:** "No engine, but it ran on qwen?" Owner:
  `web/src/pages/cores/WorkbenchesHomeCore.tsx`, `web/src/desk/components/WorkbenchAutomations.tsx`
  (list), the automation window `workbench:{id}`.
- **Not reached:** the brief's "runs wing" does not exist; the runs are the list inside the
  automation window.
- **Fix needs:** a lane.

#### Components — `surface-components` (10, builder tool)

Shots: [1440](atlas-2026-10-27/components-1440.png) · [393](atlas-2026-10-27/components-393.png)

- **Jobs:** J7 (refine the desk).
- **Doors in:** Go ▸ Builder ▸ Components, `/components`. **Out:** specimen groups.
- **Scores:** G0 nine bordered tab Buttons on two rows, a 21 px `Settings · You` headline, the
  specimen in a bordered card, two status strips · T1 `PRESET`, `PROPOSED`, `THIS MAC`, `LOCAL
  SPECIMEN` caps · H2 · F2 · De1 · Dn2 · C1 · P1.
- **Top defect:** "The catalog of our grammar breaks our grammar." Owner:
  `web/src/pages/cores/ComponentsCore.tsx`.
- **Fix needs:** a lane (wings for the groups, the specimen edge to edge).
- **W2-BUILDER (2026-10-27):** the nine groups are a rail (the Settings rail's 32 px rows and
  selection plate, a kit glyph each; drawn by the reference itself so no Settings pane style
  reaches a specimen); the pane opens with a toolbar (`Preset` + the example state, Reset at the
  right); the specimen runs on the paper; one status bar `Local specimen · <group> · <preset>`.
  `PRESET`, `PROPOSED`, `THIS MAC`, `LOCAL SPECIMEN`, `N SHOWN`, `READ ONLY`, `OPENED LOCALLY` and
  the specimen headlines are gone. At 393 the rail is the first view; a group opens with ‹ Groups.
  Left: a specimen that is a whole window (Window, Forms, Conversation) keeps its own status bar
  inside its frame; the Forms specimen draws Settings at its narrow width in a 640 px window.

#### Activity — `surface-activity` + Rules, ⚙ Candidates and connectors (16)

Shots: [Records 1440](atlas-2026-10-27/activity-1440.png) · [393](atlas-2026-10-27/activity-393.png) ·
[empty](atlas-2026-10-27/activity-empty-1440.png) · [Rules](atlas-2026-10-27/activity--rules-1440.png) ·
[Candidates and connectors 393](atlas-2026-10-27/activity--candidates-and-connectors-393.png)

- **Jobs:** J7; "Review a held tool request" adjacent.
- **Doors in:** Go ▸ Builder ▸ Activity, `/activity`. **Out:** a receipt, Clear records.
- **Scores:** G3 Records is a list view · T1 `SWEEP 2 ROOMS · Heartbeat`; the gear wing is five
  rows of `first-party` with `CLI_ENRICHMENT` / `CANDIDATE_INFERENCE` mono caps and *Dry run* ·
  H2 Rules says "No activity yet" (it lists rules, not activity); the empty Records status bar
  is a blank strip · F2 · De2 · Dn2 "Meeting saved · …" rows wrap to two lines at 1440 · C2
  *Clear records* (destructive) sits as a plain verb next to the Watching lamp · P2.
- **Top defect:** "first-party, first-party, first-party." Owner: `web/src/pages/cores/ActivityCore.tsx`.
- **Fix needs:** a lane.
- **W1-FACES (2026-10-27):** the gear wing is a list view: each connector by its own name
  (*GitHub CLI*) with what it does (*Enrich with the CLI*), On / Off / Failed as a dot and a
  word, *Ran 2 h ago* or *Never ran*; no `first-party`, no `CLI_ENRICHMENT`; Rules' empty
  state says *No rules yet*.

#### Memory — `surface-project-memory` without a scope (13)

Shots: [dense 1440](atlas-2026-10-27/memory-1440.png) · [393](atlas-2026-10-27/memory-393.png) ·
[empty](atlas-2026-10-27/memory-empty-1440.png)

- **Jobs:** J5, J3.
- **Doors in:** Go ▸ Work ▸ Memory, ⌘K, `/project-memory`. **Out:** a project (Room), a person,
  Ask (disabled without engine).
- **Scores:** G2 two lists with no headers · T2 · H1 the empty window is a blank body and
  "Not written yet" (what is not written?) · F1 a second Ask with its own disabled *Ask* and
  *Choose engine* · De1 · Dn3 · C1 duplicates Ask and the Projects/People windows · P2.
- **Top defect:** "Is this Ask, Projects or People? Why does it exist?" Owner:
  `web/src/pages/cores/MemoryCore.tsx`.
- **Fix needs:** a canvas (Memory's job against Ask; possibly fold into Ask's About).
- **W2-ASKWELLS (2026-10-27):** the toolbar is the Ask composer row (`askFace.tsx` AskComposer): `My whole desk` · one field *Find or ask your desk* · mic · `● No engine` · *Ask ⏎*. The field finds as it is typed: names, then `/api/memory/recall` hits, as dense rows of name · kind · date (`Decision · Oct 20`), status `15 found`; *Ask ⏎* runs the question in the Ask window. Pages not written: one line `● No engine writes the desk pages` + *Choose engine* (not a toolbar verb); an empty desk says `No projects or people yet`. Left: the canvas above. Shots: `scratchpad/shots/w2-askwells/memory{,-find,-asked}-*.png`.

#### Room — `surface-project-memory` scoped `project:<id>`: Now (15), History (9)

Shots: [Now 1440](atlas-2026-10-27/room-1440.png) · [Now 393](atlas-2026-10-27/room-393.png) ·
[History 1440](atlas-2026-10-27/room--history-1440.png) · [History 393](atlas-2026-10-27/room--history-393.png) ·
[loading](atlas-2026-10-27/room-loading-1440.png)

- **Jobs:** J3, J4.
- **Doors in:** Projects row, Today ▸ Open item, the floor's project icon, Memory row, Go ▸
  Projects ▸ <name>. **Out:** Write update, Ask this project, item rows, Sources and Plan folds.
- **Friction:** Go ▸ Projects ▸ All projects ▸ row (double press) = 4 presses; Today ▸ Open item
  = 2.
- **Now:** G2 · T2 the Plan fold holds mono caps dates (`JUL 15`, `LATE`, `26 DAYS`, read from
  the DOM) · H2 the loading face is a centred mono `Loading…` · F2 · De2 · Dn2 every row under
  the `Risks` caption wears a grey `Risk` pill · C1 a third Ask well; "Shadow traffic at 50
  percent Tue 3 Nov" has no label saying it is the next date · P2.
- **History:** G0 a 19 px `10 today` headline, `ALL / GITHUB / JIRA / ROOM` caps segmented pills,
  a 1 px black box around the timeline · T0 `TODAY: TUE, OCT 27` mono caps, mono times,
  `CREATE ITEM` caps in the Writes fold · H2 · F2 · De1 · Dn2 · C0 nothing else on the desk
  looks like this · P2.
- **Top defects:** "History is the old dashboard." "Ten items I added are hidden in Plan 17."
  Owner: `web/src/features/project-room/ProjectRoomCore.tsx`.
- **Not reached:** the brief's Sources / People / Decisions wings do not exist (the Room has
  Now and History; Sources and Plan are folds). My press on the folds did not open them in the
  shot; their content is known from the DOM read only.
- **Fix needs:** a lane for History (list view, dot + word, sentence case); Now is close.
- **W2-ASKWELLS (2026-10-27), the Room's Ask:** the Ask composer row (`askFace.tsx` AskComposer), the scope preset to the project (folded on the phone, where the menu bar names it): `▣ Payments Platform Rewrite` · *Ask this project…* · mic · Result ▾ · `● No engine` · *Ask ⏎* (secondary: Write update is the Room's primary). The question runs in the Ask window with the project as its scope (shot `room-asked-1440.png`). The old well, chip and hidden Submit are parked (`_parked/roomAskWell.v1-2026-10-27.tsx`). Left: the Plan fold's mono caps dates (`JUL 15`, `LATE`, `26 DAYS`), the grey `Risk` pills.
- **W3-B (2026-10-27), the Plan and This week:** dates `Jul 15`, `Today`; the late plate `Late` · `26 days` in sans; one-line rows (title, then `Risk · likelihood high · impact critical` quiet at the right, the state `● Open risk` / `● Reached` / `● 26 days late`); the fold counts sans; This week's open risk items read `● At risk` and the line opens the item (no grey `Risk` token). Shots: `scratchpad/shots/w3-b/after-room-plan-*`.
- **W1-FACES (2026-10-27):** History is a list view (`desk/surface/objects/ListView.tsx`):
  a toolbar with *All ▾* (All / GitHub / Jira / Room) and the search, quiet day captions
  (Today / Yesterday / Mon, Oct 20), rows of glyph · what happened · where · `14:02`, a press
  opens the item; the Writes fold uses the same rows in sentence case; the status bar is
  `8 events · since today`. No headline, no caps pills, no box.

#### New Project — `surface-project-setup` (17)

Shots: [1440](atlas-2026-10-27/project-setup-1440.png) · [393](atlas-2026-10-27/project-setup-393.png)

- **Jobs:** J3 (start a project), J5.
- **Doors in:** Projects ▸ New Project, ⌘K. **Out:** Create project (the Room), Cancel.
- **Friction:** Projects ▸ New Project ▸ type a name ▸ Create project = 3 presses + typing.
- **Scores:** G3 · T2 the Links placeholder is cut ("…or Confluenc") · H2 · F2 · De2 · Dn2 an
  unpicked `Blocked` pill wraps alone · C2 · P2.
- **Owner:** `web/src/features/project-room/door/DoorCore.tsx`. **Fix needs:** a lane (small).

#### Processes — `surface-processes` (15, builder tool)

Shots: [1440](atlas-2026-10-27/processes-1440.png) · [393](atlas-2026-10-27/processes-393.png)

- **Doors in:** Go ▸ Builder ▸ Processes, `/#processes`. **Out:** Refresh.
- **Scores:** G3 · T2 `Owner-session · Node:hub-project-writer` machine words · H2 · F2 · De1 ·
  Dn2 *Where* cut to "Owner-session · N…" at 1440 · C2 · P1 the second line of "Connection
  recheck" hangs outside the left edge.
- **Owner:** `web/src/pages/cores/ProcessCore.tsx`. **Fix needs:** a lane (small).

#### People — `surface-people` (15) and a person (18)

Shots: [People 1440](atlas-2026-10-27/people-1440.png) · [393](atlas-2026-10-27/people-393.png) ·
[empty](atlas-2026-10-27/people-empty-1440.png) · [loading](atlas-2026-10-27/people-loading-1440.png) ·
[person 1440](atlas-2026-10-27/person-1440.png) · [person 393](atlas-2026-10-27/person-393.png)

- **Jobs:** J3 (1:1 prep); "Follow up a commitment".
- **Doors in:** Dock 2 (phone 3), Go ▸ People, ⌃3, ⌘K. **Out:** a person (double press), Add
  person, Open prep.
- **Friction:** Dock ▸ press Priya = 2 presses, nothing opens (double press needed).
- **People scores:** G2 a "Your name" field band sits under the toolbar on every visit · T2
  `None` in Next 1:1 four times · H1 "Priya Karol · From your meetings" is a person made from
  the 1:1 title · F2 · De2 · Dn3 · C1 the primary verb (*Open prep*) is in the status bar; avatar
  circles in list rows · P2.
- **Person scores:** G2 · T3 · H2 · F3 *Record meeting*, *Add to agenda*, *Done* one press · De2
  · Dn2 two lone *Add* Buttons; three bare folds · C2 · P2.
- **Top defects:** "Why does People ask my name?" "Who is Priya Karol?" Owner:
  `web/src/pages/cores/PeopleCore.tsx` (the "From your meetings" row and the owner-name band).
- **Fix needs:** a lane.
- **W1-TRUTH (2026-10-27):** a 1:1 title splits on its separator (`/`, `<>`, `&`, `x`) and drops the owner; with two names and no owner name nothing is guessed (`people_suggestions.names_from_one_on_one_title`). The name band is one quiet row, once per browser, with *Set your name* (Settings ▸ You).

#### Projects — `surface-projects` (19)

Shots: [1440](atlas-2026-10-27/projects-1440.png) · [393](atlas-2026-10-27/projects-393.png) ·
[empty](atlas-2026-10-27/projects-empty-1440.png) · [loading](atlas-2026-10-27/projects-loading-1440.png)

- **Jobs:** J3. **Doors in:** Go ▸ Projects ▸ All projects (a submenu), ⌘K. No Dock tile.
  **Out:** the Room, New Project.
- **Scores:** G3 · T3 · H2 · F2 three levels of Go to reach it · De2 · Dn3 · C2 *New Project*
  is plain here, blue elsewhere · P2.
- **Owner:** `web/src/pages/cores/ProjectsCore.tsx`. **Fix needs:** none urgent.

#### Decisions — `surface-decisions` (15), a record (12), New decision (21)

Shots: [Decisions 1440](atlas-2026-10-27/decisions-1440.png) · [393](atlas-2026-10-27/decisions-393.png) ·
[empty](atlas-2026-10-27/decisions-empty-1440.png) · [record 1440](atlas-2026-10-27/decision-record-1440.png) ·
[record 393](atlas-2026-10-27/decision-record-393.png) · [New decision](atlas-2026-10-27/new-decision-1440.png) ·
[New decision 393](atlas-2026-10-27/new-decision-393.png)

- **Jobs:** J2 (make one decision), J3.
- **Doors in:** Go ▸ Decisions, ⌘K (Decisions app, Review decisions, each record), Today's
  decision row. New decision: the verb (⌘K "New Decision ^⇧N", the Decisions toolbar). **Out:**
  a record; the record's Edit, Copy, Send…, Dictate about this, Open canonical record.
- **Decisions scores:** G3 · T2 · H1 the Name column shows the decision's body ("One conference
  per engineer per year. The team agreed in the review."), not its title; State says
  `Decided` / `Open` where the record says `Accepted` · F2 · De2 · Dn2 two-line rows · C1 two
  words for one state · P2.
- **Record scores:** G1 a state cycle at the top, the decision in a bordered box, a full-width
  *Open canonical record* bar, a lone *Send…*, a "Filed · Desk root" fold, 300 px of blank,
  verbs split between the body and the status bar · T1 "canonical", "Desk root" · H2 · F2 · De1
  · Dn2 · C1 · P2.
- **New decision scores:** G3 · T3 · H3 closing writes nothing · F3 · De2 illustrated object,
  warm paper · Dn3 · C2 · P2.
- **Top defects:** "The list shows the body, not the name." "Decided or Accepted?" "Open
  canonical record — I am in the record." Owner: `web/src/pages/cores/DecisionsCore.tsx`,
  `web/src/desk/pullouts/DecisionPullout.tsx`, `web/src/pages/cores/NewDecisionCore.tsx`.
- **Fix needs:** a lane (list title; one state word; the record on the reader grammar).
- **W1-TRUTH (2026-10-27):** the hub's record list carries a Desk decision's `title`; the list names a row by it. One state word: Open / Accepted / Superseded / Retired / Rejected, in the list, the Decisions reader and the record. The record: toolbar (Edit · Accept or Retire · Send… · Copy · Dictate about this · Open record), the decision as plain reader text, the folds, a status bar (`● Accepted` · `Filed in: Desk`, a press opens the drawers); no state cycle, no box, no full-width bar; the window opens at 440 px.

#### Calendar snapshot — `surface-calendar-snapshot` (8, builder tool)

Shots: [dense 1440](atlas-2026-10-27/calendar-snapshot-1440.png) · [393](atlas-2026-10-27/calendar-snapshot-393.png) ·
[empty](atlas-2026-10-27/calendar-snapshot-empty-1440.png)

- **Jobs:** J6 (calendar evidence). **Doors in:** Go ▸ Builder ▸ Calendar snapshot,
  `/calendar-snapshot`; Settings ▸ Accounts ▸ Import image. **Out:** none on this face.
- **Scores:** G1 the section caption repeats the title; no toolbar; two thirds blank · T2 ·
  H0 on a desk with a working calendar feed it still says `● Can't read · No screenshot` · F0
  no verb at all · De0 · Dn2 · C1 · P2.
- **Top defect:** "A red dot and nothing I can press." Owner:
  `web/src/pages/cores/CalendarSnapshotReviewCore.tsx`.
- **Fix needs:** a lane (a verb to add a screenshot, a true empty line) or park it behind
  Accounts ▸ Import image only.
- **W1-TRUTH (2026-10-27):** toolbar *Import image* (the one Accounts flow, `desk/calendarImageImport.ts`) · *Check sources*; no caption; `● No screenshot yet`; the status bar says `2 sources connected` when feeds work.

#### Engines — `surface-engines` + inspector (15)

Shots: [with engine 1440](atlas-2026-10-27/engines-1440.png) · [393](atlas-2026-10-27/engines-393.png) ·
[no engine](atlas-2026-10-27/engines-noengine-1440.png) · [no engine 393](atlas-2026-10-27/engines-noengine-393.png) ·
[empty hub](atlas-2026-10-27/engines-empty-1440.png) · [engine down, after Check all](atlas-2026-10-27/engines-down-1440.png)

- **Jobs:** J6; "Run a model on another machine".
- **Doors in:** HoldSpeak menu ▸ Engines, Settings ▸ This Mac ▸ Engines ›, every *Choose engine*
  verb, `/models`. **Out:** Add an engine, Find on LAN, Check all, Try it, the job pickers, Set
  up speech.
- **Friction:** Ask ▸ Choose engine ▸ the Answers (Ask) picker ▸ an engine = 3 presses.
- **Scores:** G3 list + What runs where · T2 the Download fold holds `NOT DOWNLOADED`,
  `HUGGINGFACE.CO` mono caps (DOM read); the `huggingface.co` chip by *Set up speech* is at the
  act (allowed) · H1 after the engine's server was shut down and *Check all* pressed, the engine
  still reads `● Ready`; on the empty hub the speech model row is selected in blue by default
  · F2 · De2 · Dn2 · C1 the engine I named "Studio engine" is "atlas fixture" here (its model id)
  and "Studio engine" in Ask's status bar · P2.
- **Top defects:** "It says Ready; the server is off." "Two names for one engine." Owner:
  `web/src/features/runson/RunsOnCore.tsx`, `web/src/features/runson/useRunsOn.ts`.
- **Could not verify:** whether the inspector follows the selected row: pressing a row left
  *What runs where* unchanged (the same block for every engine).
- **Fix needs:** a lane (state after a failed check; one engine name).
- **W1-TRUTH (2026-10-27):** detect reads an endpoint whose `/models` does not answer `UNREACHABLE` (a 401/403 is an answer); the face says `Not answering` on the row, beside each job's picker and in the inspector head (`Studio engine · ● Not answering · checked just now · stub-qwen`); the status bar's check is its age (`Checked 2 h ago`). The name he gave wins over the served model id (`concierge_service.owner_engine_name`); the model id is `modelId`, quiet meta.

#### Parked rows (no window of their own)

- **Rhythm** (`surface-cadence`, parked → Settings): its scope opens Settings ▸ Notices
  ("Cadence" and "Morning brief" sections). The pane is not called Rhythm anywhere.
- **Change places** (`surface-places`, parked → Settings ▸ wallpaper): opens the Desk pane at
  its top; Wallpaper is the fourth section.
- **Commands** (`surface-commands`, parked → Speak ▸ Commands): see Speak.
- **Accounts** (`configure-integrations`): Settings ▸ Accounts; see Settings.

### What I could not reach, and why

- Speak's Journal, Learned and Blocks with entries: `glass_infra._boot` builds the hub with no
  journal recorder, so the wings show their empty faces only.
- Live during a meeting: the rig has no capture runtime.
- Loading at first paint: holding `/api/meetings`, `/api/projects` or `/api/decision*` reads
  before the desk draws kept the whole desk blank (the Chair never appeared in 30 s). Unknown
  whether the desk's first paint truly waits on those reads or my hold matched a boot read; the
  loading shots above hold the read after the desk had drawn.
- An agent answer that is delivered: the rig's agents have no live pane, so the press is
  refused (the refusal face is shown).
- The Room's Sources and Plan folds opened on screen (my press did not open them).
- The Meetings *Record* wing at 1440 (the press left the Records face).
- The Builder tool doors themselves (Go ▸ Builder): Builder tools stayed off; the windows were
  opened through the hub.

### Tracker rows (Part A)

| Window | Jobs | Doors in → out | Score | Top defects | Lane / PR |
| --- | --- | --- | --- | --- | --- |
| Calendar snapshot | J6 | Go ▸ Builder → Import image, Check sources | 8 → 15 | healed: toolbar, true empty state, feeds line; left: no feed-success shot (the seed's feed reads idle) | W1-TRUTH |
| Room ▸ History | J3 | Room wing → item Open | 9 | 2026-09 dashboard grammar | lane |
| Live meeting (W1-TRUTH, W2-LIVE, W2-LIVE-2) | J2 | Meetings ▸ Record → Start meeting | 10 → 19 | healed: honest status, phone title, Today's stepper, gear wing moved, during as a document, the ready sheet, the record's rail and Decide…, one-line phone status bar; left: project line, mic level | W1-TRUTH, W2-LIVE, W2-LIVE-2 |
| Speak | J1, dictation | Dock, ⌃5 → Talk | 10 | Speak/Speak; verbs move to the status bar; gear wing | lane |
| Components | J7 | Go ▸ Builder → specimens | 10 → 16 | healed: a group rail (32 px rows, glyphs; the list first at 393), a toolbar (Preset, Reset), the specimen on the paper, one status bar (`Local specimen · Forms · Saved`); no caps tokens, no specimen headlines; left: the Forms specimen draws Settings at its narrow width inside a 640 px window | W2-BUILDER |
| Ask | J3 | ⌘I/Ctrl+I, ⌘K → Save as note, Send | 11 | chat-demo look, oversized composer, mono errors | canvas (ASK) |
| Decision record | J2 | Decisions row → Edit, Accept / Retire, Send…, Open record | 12 → 15 → 17 | healed: reader grammar, verbs in the toolbar, Filed in: in the status bar; W3-A: the window fits its content (320 to 640 px; a long decision scrolls in the reader), the toolbar is one row at 393 (Send…, Copy, Dictate about this, Open record show their glyph on a narrow window; the word is the name and the hover title) | W1-TRUTH, W3-A |
| Memory | J5 | Go ▸ Memory → Room, person | 13 → 17 | healed: one Ask composer, the field finds as typed, honest empty lines; left: Memory against Ask (canvas) | W2-ASKWELLS (+ canvas) |
| Context | J4 | Go ▸ Builder → Save | 14 → 16 | healed: on/off in the status bar, the editor is the page; left: no door outside Builder | W2-ASKWELLS |
| Capture | J1 | Go, phone Dock → Talk, New note | 14 → 17 | healed: one empty line, verbs with glyphs, visible row verb, phone tiles | W2-ASKWELLS |
| Today | J2–J4 | Dock 0, ⌃1 → items | 14 → 16 | healed (W1-FACES + W2-ASKWELLS): sans words, `N more in Needs you`, no help sentence; left: phone status bar (kit), Open item → the item | W2-ASKWELLS |
| Room ▸ Now | J3, J4 | Projects, Today → Write update | 15 → 16 → 18 | healed: the Ask is the Ask composer row (W2); the Plan in sentence-case sans (`Jul 15`, `Today`, `Late`, `26 days`), one-line rows with the facts at the right and the state a dot + word; This week risks say `● At risk`, the line opens the item (W3-B) | W2-ASKWELLS, W3-B |
| People | J3 | Dock 2, ⌃3 → person | 15 → 17 | healed: no fake person from a 1:1 title, the name row once and quiet; left: `None` in Next 1:1, avatars, primary in the status bar | W1-TRUTH |
| Decisions | J2 | Go → record | 15 → 18 | healed: title as the name, one state word (Open / Accepted / Superseded / Retired / Rejected) | W1-TRUTH |
| Engines | J6 | HoldSpeak menu → pickers | 15 → 18 | healed: Not answering after a failed check (row, inspector, pickers), the owner's name with the model id as meta, the inspector follows the row; left: an auto-named engine (host:port label) still reads its model name here and the label in Ask | W1-TRUTH |
| Processes | J7 | Go ▸ Builder | 15 | machine words; phone line off the edge | lane |
| Activity | J7 | Go ▸ Builder → receipt | 16 | gear wing tokens; Rules says activity | lane |
| Agents | J4 | Dock 3, ⌃4 → Answer, Open | 16 | runs and tools in one list; mono refusal | lane |
| Settings | J6 | HoldSpeak menu → panes | 18 | raw enums; scope lands at top | W1-KIT (steppers are library Buttons); enums + scope: lane |
| Automations | J4 | Go ▸ Work → automation | 17 | "No engine" vs the result's model | lane |
| New Project | J3 | Projects → Room | 17 | clipped placeholder | lane (small) |
| Meetings (W1-KIT) | J2 | Dock 1, ⌃2 → meeting | 21 | gear wing | W1-KIT (press opens, Record meeting primary, phone bar, Sort verb, loading face); gear wing: lane |
| Setup | J6 | HoldSpeak menu → Use everything found | 18 | "Priya Karol"; phone footer | lane |
| Person | J3 | People → Record meeting | 18 | lone Add Buttons | — |
| Automation (open) | J4 | Automations → Run now | 18 | empty band | — |
| Projects | J3 | Go ▸ Projects ▸ All → Room | 21 | three levels deep | W1-KIT (press opens, New Project primary, glyph, loading face) |
| New decision | J2 | the verb → Create | 21 | — | — |

## Part B — the object windows, the doors, the phone (lane ATLAS-B)

### How the shots were made

- Rig: the fixtures of `tests/e2e/test_desk_sweep.py` (`desk`, `pw_browser`, `_page`,
  `_hub_open`, `SETTLED_JS`), in a scratch test that is deleted. Every window was opened with
  `POST /api/desk/windows/{id}/open` before the page loaded, or by its real door (dock tile, menu,
  ⌘K, key, floor icon).
- Seed: the sweep's seed (canvas week, Priya's 1:1, the agent flight, the failed Vendor sync,
  the Payments Project, the Friday automation), plus `POST /api/desk/seed` (drawers and modes),
  five notes, four decisions, five more Project items (16 in the Plan), a knowledge base, a
  sequence, a workflow, a thread. Three more people failed to post (`relationship_kind`), so the
  People list has the canvas seven.
- Wallpaper: there is no hub API; the choice is a browser preference. The rig set
  `localStorage["hs.desk.atmosphere"] = "rainy-city"` (`web/src/desk/gl/atmospherePreference.ts:8`).
- Widths: 1440×900 (the window crop + 24 px of floor) and 393×852 (the whole screen). All PNGs are
  1×, each under 300 KB (pngquant on the four full-desk shots).
- Only the dense state. A fresh empty hub, a lost connection and a loading hold were not shot
  (see "Not reached").

### Scores

| Window (id) | Jobs | Doors in → out | G | T | H | F | D | Dn | C | P | Sum |
| --- | --- | --- | - | - | - | - | - | - | - | - | - |
| Note (`pullout:note:*`) | J1 | floor icon (1), ⌘K (2), Inbox drawer row (2) → Done closes; Send… in place. Lane / PR: W1-DOORS (opens rendered, caret at the end); W3-NOTE-STEPS (objects in the text: glyph + ink, peek card, press opens; @ and # completion; the status-bar place line from the hub's `projects` and `source_meeting`) | 2 | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 21 |
| Decision (`pullout:decision:*`) | J3 | Needs you ▸ Decide (2), ⌘K (2), Go ▸ Decisions ▸ row (3) | 0 | 1 | 2 | 2 | 1 | 1 | 0 | 1 | 8 |
| Meeting (`surface-meetings@meeting:*`) | J2 | dock Meetings ▸ row (2), Needs you row (2) → Back to the list. Lane / PR: W2-LIVE-2 (Today's rail at Summary, Send follow-up… primary, Settings trailing, Decide… on decided rows) | 3 | 2 | 2 | 3 | 2 | 2 | 3 | 1 | 18 |
| Person (`pullout:people:*`) | J3 | dock People ▸ row (2), Today 1:1 (2) | 2 | 3 | 2 | 2 | 2 | 1 | 2 | 1 | 15 |
| Room via floor icon (`surface-project-memory@project:*`) | J3 | floor Project icon (1), Go ▸ Projects ▸ name (3) | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 15 |
| Project as a pullout (`pullout:project:*`) | J3 | hub/agent → the Room (`surface-project-memory` scoped `project:<id>`). Lane / PR: W1-DOORS | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 15 |
| Project drawer (`drawer:project:*`) | J3, J5 | hub/agent; its own Room button. Lane / PR: W2-BUILDER (head facts as dot + word: `1 need you`, `At risk`; a connection scope reads `Jira`); W3-B (no body title: the title bar is the title; toolbar Room · History · Icons/List toggles; the facts in the foot; sources lead with the object glyph, `● Checked 1 min ago`) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 15 |
| Artifact (`pullout:artifact:*`) | J4 | Today "has a new result ▸ Open" (2) | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 2 | 11 |
| Agent's window (`lane@launch:*`) | J4 | dock Agents ▸ row (2). Lane / PR: W2-BUILDER (toolbar Tell it · Open PR · Stop; the ask first; `No steps reported yet` in words; `Last step N min ago` in the status bar); W3-AGENT (canvas `docs/internal/betterment/canvases/agent-window-2026-10-27.html`, direction A, the step log: the body is the steps from the hub's events in 30 px rows, a coloured glyph per kind, the newest lit while it works, the ask lit while it asks; the PR, branch and files as object rows beside the steps (above them at 393); the ask on a soft plate, `● Asks you` + `Asked 6 min ago`; the result on a soft green plate; the state as the status bar's first dot and word, with `N steps`; done: Open PR is the primary; Terminal is a wing `Steps · Terminal`, the white title-bar tab gone; atlas pass 2: the state comes from the Agents list's truth (the live flight, else the launch's history entry): a gone session reads `Session gone` with *Start again*, never `is working`. Left: in the done shot the window says `Claude Code is done` while the Agents row says `Idle` (flight state vs session turn end; cause not verified); `Done` needs a hub close fact; the receipts and the Details track are still mono caps; shots `scratchpad/shots/w3-agent/after2/`) | 3 | 2 | 2 | 2 | 3 | 3 | 2 | 2 | 19 |
| Automation (`workbench:*`) | J4 | Go ▸ Automations ▸ row (3) | 3 | 2 | 3 | 3 | 2 | 3 | 2 | 2 | 20 |
| Drawer (`pullout:zone:*`) | J5 | floor drawer icon (1), Go ▸ Drawers ▸ name (3). Lane / PR: W3-ZONE (the Project drawer's grammar: toolbar Open · Dictate about this · Icons/List; no `Contents · N`; a dense one-line list Name · Kind · When, a press opens; `4 objects` in the status bar; opens 640×440) | 3 | 2 | 3 | 3 | 2 | 3 | 2 | 2 | 20 |
| Knowledge base (`pullout:knowledge:*`) | J5 | floor icon (1), its label says KNOWLEDGE. Lane / PR: W2-BUILDER (toolbar Add · Edit · Copy · Dictate; Add opens the item picker); W3-B (editor: toolbar Done · Add items, Name on the label/control grid, items and picker as dense 30 px rows, kind in sans) | 2 | 3 | 2 | 2 | 1 | 2 | 2 | 2 | 16 |
| Archive (`drawer:parked`) | J5 | Go ▸ Archive (2). Lane / PR: W3-ZONE (toolbar Open · Restore only when a row exists, Retry on a failed read; no dead footer; dense list Name · Kind · When in sentence case; a failed read is `● Meetings not read` in the status bar) | 3 | 2 | 2 | 2 | 2 | 3 | 2 | 2 | 18 |
| Mode / recipe (`pullout:persona:*`) | J4, J6 | no ordinary door found (Go ▸ Builder only with builder tools on). Lane / PR: W2-BUILDER (toolbar; "Which engine answers in a thread" / "Which engine runs it" in sans; no raw id) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 15 |
| Sequence / chain (`pullout:sequence:*`) | J4 | no ordinary door found. Lane / PR: W2-BUILDER (Add mode adds a step, PUT /api/chains/{id}; a greyed Run says why) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 15 |
| Workflow (`pullout:workflow:*`) | J4 | no ordinary door found. Lane / PR: W2-BUILDER (Edit left the title bar for the toolbar; Steps as a quiet list; a greyed Run says why) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 15 |
| Thread (`pullout:thread:*`) | J1 | → opens Ask (by design, Betterment Q4); scored by ATLAS-A/ASK | – | – | – | – | – | – | – | – | – |
| Needs you (`chair:needs`) | J2, J3 | bell (1), ⌃J (1), Go ▸ Needs you (2). Lane / PR: W1-DOORS (rows named after the meeting; one calendar truth); W3-DELIGHT (kind-hued glyph seats, Done settles the row out) | 3 | 2 | 2 | 3 | 3 | 3 | 2 | 2 | 20 |
| Capture (`chair:capture`) | J1, J2 | Go ▸ Capture (2), dock at 393 (1) | 2 | 3 | 2 | 3 | 1 | 3 | 2 | 2 | 18 |
| ⌘K palette | J5, J7 | ⌘K or Search (1) → the row's window. Lane / PR: W1-DOORS (parked rows name where they land; an app once) | 2 | 2 | 2 | 3 | 2 | 2 | 1 | 2 | 16 |
| Menu bar + menus (HoldSpeak, Desk, Object, Go, Window) | J7 | always on | 3 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | 21 |
| Shortcut sheet | J7 | ⌘/ , HoldSpeak ▸ Keyboard shortcuts (2) | 1 | 0 | 3 | 2 | 1 | 2 | 1 | – | 10 |
| Window switcher | J7 | ⌘` held (1) | 2 | 3 | 3 | 3 | 1 | 3 | 2 | 0 | 17 |
| Mission control (Overview) | J7 | ⌘⇧E, Window ▸ Overview (2) | 2 | 3 | 3 | 3 | 1 | 2 | 2 | – | 16 |
| Send preview (in the note) | J1, J3 | note toolbar Send… (1) → destination (2) → Send (3) | 1 | 0 | 3 | 3 | 1 | 2 | 1 | – | 11 |
| Feedback sheet | J7 | Desk ▸ Give feedback, title-bar Feedback (only with `HOLDSPEAK_UI_FEEDBACK=1`). Lane / PR: W1-DOORS (above the dock); W3-A (a toolbar of dense verbs, the state a dot and a word, `● Speech unavailable` + *Set up speech*, no caps, no route chip; it stands above the dock and above the front window's status bar at 1440 and 393) | 3 | 2 | 2 | 3 | 2 | 2 | 2 | 2 | 18 |
| Floor: icon menu / blank floor | J5, J7 | right-click an icon (1) / right-click the floor (1): the Desk menu's rows. Lane / PR: W1-DOORS | 2 | 3 | 2 | 3 | 2 | 3 | 1 | – | 16 |
| Phone desk (393) | all | Go list as home, five dock tiles. Lane / PR: W2-BUILDER (with two or more windows open the screen title is `<window> ▾` again and lists every open window); W3-A (no Go-list label shows between a sheet and the dock) | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 15 |

"–" = not shot or not applicable (no keyboard at 393). Friction numbers are presses counted by
doing them in the rig.

### The five worst by score

1. **Sequence / chain — 4.** `chain-1440.png`. A caps STEPS label over "No steps", then "Add at
   least one Agent to this linear Sequence." and no verb to add one; a mono "Material" well with a
   ghost Run; "Where it runs: This machine · Creates artifact"; Assignments. A dead end in machine
   words. Owner: "it tells me what to do and gives me no way to do it." `web/src/desk/pullouts/ChainPullout.tsx`.
2. **Project as a pullout — 3 (dead door).** `project-as-pullout-1440.png`: an empty window
   that says "No detail view for project". The hub accepts `pullout:project:<id>` and the browser
   pushes the pullout without `openPullout`'s surface redirect (`web/src/desk/compositor/hubWindows.ts:277-293`;
   `web/src/desk/pullouts/registry.ts` maps `project` to `FallbackPullout`). An agent that opens a
   Project this way gets this face.
3. **Mode (recipe) — 5.** `recipe-1440.png`. A centred avatar and a centred "Continue in
   thread"; two bordered cards, "Thread assignment" and "Run assignment", each "No default model"
   in mono and a bold mono "Choose default"; "Where it runs: Assignment:recipe" (a raw id). Owner:
   "what is an assignment, and why is it in typewriter font?" `web/src/desk/pullouts/RecipePullout.tsx`.
4. **Project drawer — 6.** `drawer-project-1440.png`. A 17 px page title that repeats the title
   bar; caps tokens "1 NEED YOU" and "STATUS AT RISK"; an Icons/List toggle; a "Nothing filed here"
   band; Sources as bordered cards with GH/J chips, `jira.example.com|team@example.com` on the row
   (an address on a working row, against UX-CANON A.9 as amended 2026-10-25) and mono caps "CHECKED
   1M AGO"; a footer of Register · Get Info · ghost Open. Owner: "a third face for my Project."
   `web/src/desk/drawer/DrawerWindow.tsx`.
5. **Workflow — 6.** `workflow-1440.png`. "Edit Workflow" sits in the title bar as a tab; caps
   STEPS; a card holding a mono "Material" well and a ghost Run with no reason; Assignments;
   "Creates artifact". `web/src/desk/pullouts/WorkflowPullout.tsx`.

Next worst, and the ones he actually meets: **Decision (8)**, **the agent's window (8)**,
**the feedback sheet (8)**, **knowledge base (9)**. Chain, recipe and workflow have no ordinary door
(see below), so the owner meets them seldom. On the windows he meets, Decision is the first fix.

### Findings, window by window

**Note** (`note-1440.png`, `note-rich-1440.png`, `note-393.png`, `note-rich-393.png`). On the
grammar: toolbar (Done · Ask about this · Find the tasks · Project · Send…), page, status bar.
- The first line of a list shows its source: "- [ ] Freeze writes" in raw markdown, and the next
  two lines show real boxes. The caret line is shown as source (the live-preview rule), and the
  caret starts on line 1, so every note with a task list opens looking broken.
  `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx` (the live-preview editor of #1502).
- The name shows twice at 1440 (title bar, then the title field) and three times at 393 (menu bar,
  sheet head, title field). WINDOW-GRAMMAR §1 names this case.
- "Saved just now" on a note nobody touched. If it reflects the last save, it is true but it reads
  like a write on open.
- At 393 the toolbar is five bare glyphs with no words.
- Fix: a lane (place the caret at the end, or render the caret line on open; let the title field
  stand in for the title bar on phone).

**Decision** (`decision-1440.png`, `decision-proposed-1440.png`, `decision-393.png`). The oldest
face on the desk. No toolbar; an "↻ Accepted" chip floating at the top (the glyph is 11 px); a
bordered "Decision" card inside the paper; a full-width "Open canonical record" bar; a lone
"Send…" in its own band; "Filed · Desk root"; 250 px of blank; a footer that says "Accepted" again
in the middle, then Copy · Dictate about this · Edit. Proposed and accepted look the same. Owner:
"this is a form from 2019." `web/src/desk/pullouts/DecisionPullout.tsx`. Fix: a lane (toolbar
Edit · Send… · Open record; status as dot + word in the status bar; the record body edge to edge).
The New decision and Decisions windows (ATLAS-A) show the target grammar.

**Meeting** (`meeting-1440.png`, `meeting-failed-1440.png`, `meeting-393.png`,
`meeting-failed-393.png`). Good bones: Outcomes wing, toolbar, 30 px rows, status bar.
- The failed meeting reads "ERROR KEPT 2 SEGMENTS NOT DONE: SUMMARY, TOPICS, ACTION ITEMS" in caps
  tokens. `web/src/desk/pullouts/MeetingWindow.tsx`.
- The good meeting's status bar says "Summary stored · No engine for summaries" — true, but it
  reads as a contradiction. Choose engine shows twice on the failed one (inline and in the bar).
- At 393 every action row grows a Done + Follow-through pair under it (80 px rows); the status bar
  wraps to two lines.
- `pullout:meeting:<id>` opens the Meetings window (by design, PHILO-17); `meeting-as-pullout-1440.png`.

**Person** (`person-1440.png`, `person-393.png`). On the grammar. The Commitments block puts
lone Add buttons in bands; Context, History, Info are three folds with wide gaps; at 393 the status
bar wraps to two lines. `web/src/desk/pullouts/PeoplePullout.tsx`. Lane.

**Room from the floor** (`room-1440.png`, `room-393.png`, `door-project-icon-1440.png`). Scored
here only as the object door; the Room itself is ATLAS-A's. Opened from the floor icon it seats
low and its lower edge goes under the dock. The risks wear grey "Risk" chips beside a "Risks"
heading.

**Artifact** (`artifact-1440.png`, `artifact-393.png`). No toolbar. The result is a card inside the
paper; Send is a heading, then the destinations as bordered cards with mono caps "FILE" and mono
paths; Filed fold; a footer of Copy · Dictate about this. The automation window shows the same
result on the new grammar, so the two faces of one result do not match.
`web/src/desk/pullouts/ArtifactPullout.tsx`, `web/src/desk/surface/send/SendWell.tsx`. Lane.

**The agent's window** (`lane-1440.png`, `lane-393.png`). 960×720 of blank: "Claude Code is
working · Write the rollback runbook", a Details fold, and an empty status bar. The fold holds mono
caps BRIEF, FILES, "· NOT READ ·" and "the launch has no worktree". Nothing says what the agent is
doing or when it last spoke. Owner: "it's working on what?" `web/src/desk/lane/LaneWindow.tsx`.
Needs a canvas (what a running agent's window shows).

**Automation** (`automation-1440.png`, `automation-393.png`). The best object window: toolbar,
the sentence, a list view with column heads and the selected row, the result, a status bar. A caps
"NEW" chip over the result.

**Drawer** (`directory-1440.png`, `door-drawer-floor-1440.png`, `directory-393.png`). "Contents · 3"
as a heading, 47 px two-line rows with an inset, a Filed fold, a footer with one verb ("Dictate
about this"). Not a list view, and it does not look like the Archive or the Project drawer.
`web/src/desk/pullouts/DirectoryPullout.tsx`.

**Knowledge base** (`kb-1440.png`, `kb-393.png`). The floor calls "Payments runbooks" a DRAWER;
it opens "Contents · No items" with no verb to add one, and a footer of Copy · Dictate about this ·
Edit. `web/src/desk/pullouts/KbPullout.tsx`.

**Archive** (`archive-1440.png`, `archive-393.png`). The title says Archive, the body says
"Nothing parked"; on an empty list the footer still shows ghost Restore and Open (dead footer).
`web/src/desk/drawer/ParkedDrawer.tsx`.

**Needs you** (`needs-1440.png`, `needs-393.png`, `door-bell-1440.png`). On the grammar. The words
are the problem:
- Three rows named "mentions ledger" / "mentions cutover": a watch hit is named after the watch,
  not after what was said.
- "Write the rollback runbook" shows twice.
- The toolbar says "No calendar · Connect calendar" while the status bar names "Next 1:1 03:23 ·
  Priya / Karol".
- "16 of 16 available" as a fold label.
- `web/src/desk/needs/NeedsDrawer.tsx`, `web/src/desk/needs/needsFace.ts`.

**Capture** (`capture-1440.png`, `phone-tile-capture-393.png`). Clean. Three verbs and Coming up;
little colour.

**⌘K palette** (`door-palette-empty-1440.png`, `-typed-`, `-none-`, `-verb-`, `phone-palette-393.png`).
- Empty: Memory is listed twice. "Change places", "Rhythm" and "Commands" are listed as Apps, but
  those windows are retired. They land in Settings ▸ Desk, Settings ▸ Notices and Speak ▸ Commands
  (`door-palette-to-*-1440.png`).
- Typed "ledger": a Project ("Payments ledger cutover") under Decisions; a Note ("Cutover
  checklist") under "Do"; Decisions and "Desk decisions" both list "Freeze the ledger schema on Nov
  12"; a Desk-decision row is 103 px with a mono "10-27"; a stray "Hand to agent" button breaks the
  grid under the top row.
- No result: only Ask "qqzzx". That is honest and useful.
- `web/src/desk/components/DeskToolShelf.tsx`, `web/src/desk/components/paletteHit.tsx`.

**Menus** (`door-menu-*-1440.png`, `door-menu-*-phone-393.png`, `door-icon-menu-1440.png`). Clean
32 px rows with key caps. Issues:
- The Desk menu holds only the New rows (plus Give feedback when the flag is on).
- Settings and Setup share one glyph.
- The Note menu offers Open and Edit for the note that is open and in edit.
- The menu bar shows "Desk" twice (the Desk menu, then the bold screen title).
- On the phone the HoldSpeak menu draws over the Go list.
- `web/src/desk/components/DeskMenuBar.tsx`, `web/src/desk/components/DeskChrome.tsx`.

**Shortcut sheet** (`door-shortcuts-1440.png`). Every word is mono; caps headings APPS, NEW,
WINDOWS, DESK; Esc is listed twice (Back; Close / cancel); the sheet writes ^ where the menus write
⌃. It is a centred overlay over the desk. `web/src/desk/components/window/ShortcutSheet.tsx`. Lane.

**Window switcher** (`door-switcher-1440.png`). A strip of names, no icons. At 393 ⌃` shows
nothing. `web/src/desk/components/window/Switcher.tsx`.

**Mission control** (`door-mission-1440.png`). The wallpaper goes flat grey; the thumbnails have no
names under them; the text in them cannot be read. Sterile. `web/src/desk/missioncontrol.ts`,
`web/src/desk/components/MissionControlConveyor.tsx`.

**Send preview** (`door-send-menu-1440.png`, `door-send-preview-1440.png`). Three presses from an
open note, which is good. The look is bad: mono caps FILE, PREVIEW, FOLDER and a mono path, and the
selected destination is a bordered box holding a preview card holding a grey Send band (card in
card in card). The same destinations look different in the artifact window.
`web/src/desk/surface/send/SendWell.tsx`. Lane.

**Feedback sheet** (`door-feedback-1440.png`, `door-feedback-picked-1440.png`). It sits over the
right half of the dock and covers the record orb. Mono caps "SELECT", "SPEECH · PENDING", "RETRY";
after a pick it says "Desk · Not supported" with no reason (in the headless rig there is no mic, so
this may be the honest result; the words do not say so). The door exists only when the hub runs
with `HOLDSPEAK_UI_FEEDBACK=1` (`holdspeak/services/ui_feedback.py:27`).
`web/src/desk/feedback/UiFeedbackHost.tsx`.

**The phone (393)** (`desk-393.png`, `phone-tile-*-393.png`, `phone-three*-393.png`,
`phone-bell-393.png`).
- Home is the Go list itself: 29 rows of apps, projects, drawers. At the end come "Note",
  "Meeting", "Decision", "Project", "Person", "Automation", "Drawer" with no "New" word, so they
  read as lists, not as creating something.
- The dock has five tiles (Today, Capture, Meetings, People, Agents) and no pager (`.desk-dock-more`
  is absent). Speak is only in Go.
- Sheets: Today, Meetings, People, Needs you, the person and the failed meeting all wrap the status
  bar to two lines.
- Meetings makes "Choose engine" the primary (blue) verb ahead of Record meeting.
- People shows a "Your name" field inside the list, and "Open prep" floats over the status bar.
- Agents shows CLI versions ("2.1.310", "0.163.0") as row subtitles.
- With three windows open (`phone-three-393.png`) only the front sheet shows, and nothing says two
  more are there. ⌃` and ⌃W changed nothing at 393 (unknown: the note editor may hold the focus).
- Lane / PR: W1-GEOM (2026-10-27). After the floating dock (#1497) Go scrolled by 2 px above the
  plate; the rules between its groups now take 2 px of air, not 4, at 420 px and less, so every Go
  row shows with no scroll. Every dock reserve (Go, the Chair's reopen list, the note's phone sheet,
  the floor's Talk, Delivery, the phone in-world editor, the `.desk-mc-tab`) reads `--desk-dock-h` /
  `--desk-snap-bottom`, no 52/56/60/76 px literal. Sheets keep the ratified 8 px of air: 682 px of
  content at 852. Score unchanged (13): the status-bar wrap and the Go-as-home list stand.

### Doors that lead nowhere, or to a window other than their name

1. `pullout:directory:<id>`, `pullout:kb:<id>`, `pullout:recipe:<id>`, `pullout:chain:<id>`.
   These use the registry's own kind words, and the hub answers 200 but no window opens: the
   browser keys these objects as `zone:`, `knowledge:`, `persona:`, `sequence:`
   (`web/src/desk/api.ts:131-139`, `qualifiedRef`). An agent that calls `desk_window_open` with the
   kind word gets success and nothing on the desk. **Healed (W1-DOORS):** the hub opens the canonical
   window for a kind word (`desk_window_service.canonical_open`); an unknown kind is refused
   (`window_unknown`).
2. `pullout:project:<id>` opens "No detail view for project" in place of the Room. **Healed (W1-DOORS):**
   the hub opens the Room; an old row opens the Room and closes itself (`pullouts/ProjectToRoom.tsx`).
3. The palette rows "Change places", "Rhythm" and "Commands" open Settings ▸ Desk, Settings ▸
   Notices and Speak ▸ Commands. They land, but under names of retired windows. Memory appears
   twice in the same list. **Healed (W1-DOORS):** "Wallpaper — Settings ▸ Desk", "Notices — Settings",
   "Commands — Speak" (`applications.ts` `paletteLabel`); an app in Recent is not listed again.
4. Right-clicking the blank floor shows no menu: there is no handler on the floor, only on icons
   (`web/src/desk/screen/Screen.tsx:226`). **Healed (W1-DOORS):** the floor opens the Desk menu's rows
   (`components/menuVerbEntries.ts`, one source with the menu bar).
5. The floor icon "Payments runbooks" is captioned DRAWER, but it opens a knowledge base with no
   way to add to it. **Healed (W2-BUILDER):** its kind word is KNOWLEDGE, and the window's toolbar Add opens
   the item picker (`PUT /api/kbs/{id}/members/{ref}`).
6. The Sequence window says "Add at least one Agent" and has no verb to do it. **Healed (W2-BUILDER):** the toolbar's Add mode
   lists the Modes and appends one to the steps; the greyed Run says "Add a mode first".
7. Give feedback is hidden unless the hub has `HOLDSPEAK_UI_FEEDBACK=1`. This is a switch, not a
   broken door, but the owner's desk shows no feedback door if the switch is off.
8. By design, and named here so nobody "fixes" them: `pullout:meeting:<id>` opens the Meetings
   window, and `pullout:thread:<id>` opens Ask.
9. Not followed (unknown): the Decision's "Open canonical record", the Project drawer's Register
   and Room, the knowledge base's Edit.

### Not reached, and why

- **The empty and error states of a fresh hub**: the rig boots one hub per module and seeds it
  once. A second cold hub was not booted. The only error states shot are the failed meeting and
  the failed automation run; no lost-connection or loading hold.
- **coder**: `/api/coders/status` has no sessions; a coder of a launch opens the agent's window
  (`coderOpenFirst`), which is shot.
- **repository, roadmap, story, game, layout** (FallbackPullout kinds): no seeded objects.
- **brief / report**: there is no brief or report pullout kind now. The brief is Today's Since
  yesterday fold (ATLAS-A, Today), and a report is an artifact (shot).
- **Shortcut sheet, mission control, send preview, feedback at 393**: not shot.
- **The screen switcher**: `.desk-screen-switcher` is absent with one desk. The bold "Desk" is a
  title, not a door.
- **Ordinary doors to modes, sequences and workflows**: Go ▸ Builder appears only with builder
  tools on (`web/src/desk/components/DeskMenuBar.tsx:197`). They were opened through the hub.
- **The feedback capture itself**: the headless browser has no mic.
