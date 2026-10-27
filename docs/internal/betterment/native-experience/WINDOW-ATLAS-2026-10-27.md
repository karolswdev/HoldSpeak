# The window atlas — 2026-10-27

P0 of the [Window Program](WINDOW-PROGRAM-2026-10-27.md). Every window and door, shot in
realistic states and scored with the program's eight-axis rubric (0–3 each: Grammar, Text,
Honest states, Friction, Delight, Density, Consistency, Phone; 24 is the top). Part A is the
application windows of `web/src/desk/applications.ts`; Part B is the object windows and the
doors.

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
| Room ▸ History | 0 | 0 | 2 | 2 | 1 | 2 | 0 | 2 | **9** |
| Live meeting (W1-TRUTH) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **15** |
| Speak (+ wings) | 1 | 1 | 1 | 2 | 1 | 2 | 1 | 1 | **10** |
| Components | 0 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | **10** |
| Ask | 2 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | **11** |
| Decision record (W1-TRUTH) | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | **15** |
| Memory | 2 | 2 | 1 | 1 | 1 | 3 | 1 | 2 | **13** |
| Context | 2 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | **14** |
| Capture | 2 | 3 | 1 | 2 | 1 | 2 | 1 | 2 | **14** |
| Today | 2 | 1 | 2 | 3 | 2 | 2 | 1 | 1 | **14** |
| Room ▸ Now | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | **15** |
| People (W1-TRUTH) | 3 | 2 | 2 | 2 | 2 | 3 | 1 | 2 | **17** |
| Decisions (W1-TRUTH) | 3 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | **18** |
| Engines (W1-TRUTH) | 3 | 2 | 3 | 2 | 2 | 2 | 2 | 2 | **18** |
| Processes | 3 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | **15** |
| Activity | 3 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | **16** |
| Agents | 2 | 1 | 2 | 3 | 2 | 3 | 1 | 2 | **16** |
| Settings (frame + 8 panes) | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| Automations | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| New Project | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **17** |
| Meetings | 3 | 2 | 2 | 2 | 2 | 3 | 2 | 2 | **18** |
| Setup | 3 | 2 | 2 | 3 | 2 | 3 | 2 | 1 | **18** |
| Person | 2 | 3 | 2 | 3 | 2 | 2 | 2 | 2 | **18** |
| Automation (one open) | 2 | 2 | 3 | 3 | 2 | 2 | 2 | 2 | **18** |
| Projects | 3 | 3 | 2 | 2 | 2 | 3 | 2 | 2 | **19** |
| New decision | 3 | 3 | 3 | 3 | 2 | 3 | 2 | 2 | **21** |

No window scores 2 or more on every axis. The phone axis and the consistency axis are the
weakest across the board.

### What runs through many windows (fix once, heal many)

1. **The phone status bar eats the window.** At 393 the status bar wraps to two or three lines
   and puts a 44 px Button on its own row; content is cut under it (Today, Meetings, Setup,
   Speak, People, Engines). Owner: "half my phone is the footer". Owner: the status-bar species,
   `web/src/desk/surface/kit.tsx` (StatusBar) + `kit.css`.
2. **Column headers lie on the phone.** Meetings, People, Agents, Decisions, Processes,
   Engines, Automations and Setup draw four column headers over rows that have turned into two
   lines; the header cells no longer sit over anything. Owner: `web/src/desk/surface/objects/ObjectList.tsx`.
3. **A press selects, nothing opens.** In Meetings and People a press on a row selects it; the
   meeting or person opens only on a double press or Enter
   (`ObjectList.tsx:12`, `:283`), and no collection toolbar carries an Open verb. Flow log:
   Dock ▸ Meetings ▸ press a row = 2 presses, 0 windows opened
   ([flow-meeting-1440](atlas-2026-10-27/flow-meeting-1440.png),
   [flow-person-1440](atlas-2026-10-27/flow-person-1440.png)).
4. **Half the windows have no glyph in the title bar.** Today, Ask, Meetings, Agents, People,
   Decisions, Speak, Settings carry their object glyph; Projects, Memory, Engines, Setup,
   Context, Automations, Components, Activity, Processes, Live, Capture, Calendar snapshot do
   not. Owner: `web/src/desk/applications.ts` `surface.sprite` and the head in
   `web/src/desk/components/DeskWindow.tsx`.
5. **Three Ask wells.** Ask, Memory ("Ask your desk") and the Room ("Ask this project…") each
   draw their own composer, engine line and refusal. Owner: "which one do I use?"
   (`web/src/desk/components/AskPanel.tsx`, `web/src/pages/cores/MemoryCore.tsx`,
   `web/src/features/project-room/ProjectRoomCore.tsx`).
6. **Three loading faces.** Meetings and People show a faint grey ring (People also drops its
   toolbar while it waits), the Room shows a centred mono `Loading…`, Decisions and Projects
   show a toolbar over a blank body
   ([people](atlas-2026-10-27/people-loading-1440.png),
   [room](atlas-2026-10-27/room-loading-1440.png),
   [meetings](atlas-2026-10-27/meetings-loading-1440.png)).
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
   nothing under 12 px.
10. **The primary verb wanders.** Meetings makes *Choose engine* the blue verb over *Record
    meeting*; People puts its primary (*Open prep*) in the status bar; Agents' *Start an agent*
    is blue on an empty desk and plain on a full one; Projects' *New Project* is plain while
    Decisions' and People's *New* verbs are blue.
11. **Phone floor bleed.** In every 393 shot a desk-icon label (`Inbox`) shows in the strip
    between the sheet and the Dock (Part B owns the phone desk; noted here because every
    application shot shows it).

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
| Live meeting | J2 | Meetings ▸ Record → Start meeting | 10 → 15 | healed: honest status, phone title, Today's stepper; left: gear wing (old grammar), during/after canvas | W1-TRUTH (+ canvas) |
| Speak | J1, dictation | Dock, ⌃5 → Talk | 10 | Speak/Speak; verbs move to the status bar; gear wing | lane |
| Components | J7 | Go ▸ Builder → specimens | 10 | breaks the grammar it shows | lane |
| Ask | J3 | ⌘I/Ctrl+I, ⌘K → Save as note, Send | 11 | chat-demo look, oversized composer, mono errors | canvas (ASK) |
| Decision record | J2 | Decisions row → Edit, Accept / Retire, Send…, Open record | 12 → 15 | healed: reader grammar, verbs in the toolbar, Filed in: in the status bar; left: toolbar wraps to two rows at 393; window is 440 px, not content-fit | W1-TRUTH |
| Memory | J5 | Go ▸ Memory → Room, person | 13 | second Ask; blank empty | canvas |
| Context | J4 | Go ▸ Builder → Save | 14 | no state | lane |
| Capture | J1 | Go, phone Dock → Talk, New note | 14 | blank band | lane |
| Today | J2–J4 | Dock 0, ⌃1 → items | 14 | mono ask card, count 32 vs 5, Send form in a fold | lane |
| Room ▸ Now | J3, J4 | Projects, Today → Write update | 15 | third Ask; Risk pills; items hidden in Plan | lane |
| People | J3 | Dock 2, ⌃3 → person | 15 → 17 | healed: no fake person from a 1:1 title, the name row once and quiet; left: `None` in Next 1:1, avatars, primary in the status bar | W1-TRUTH |
| Decisions | J2 | Go → record | 15 → 18 | healed: title as the name, one state word (Open / Accepted / Superseded / Retired / Rejected) | W1-TRUTH |
| Engines | J6 | HoldSpeak menu → pickers | 15 → 18 | healed: Not answering after a failed check (row, inspector, pickers), the owner's name with the model id as meta, the inspector follows the row; left: an auto-named engine (host:port label) still reads its model name here and the label in Ask | W1-TRUTH |
| Processes | J7 | Go ▸ Builder | 15 | machine words; phone line off the edge | lane |
| Activity | J7 | Go ▸ Builder → receipt | 16 | gear wing tokens; Rules says activity | lane |
| Agents | J4 | Dock 3, ⌃4 → Answer, Open | 16 | runs and tools in one list; mono refusal | lane |
| Settings | J6 | HoldSpeak menu → panes | 17 | raw enums; raw steppers; scope lands at top | lane |
| Automations | J4 | Go ▸ Work → automation | 17 | "No engine" vs the result's model | lane |
| New Project | J3 | Projects → Room | 17 | clipped placeholder | lane (small) |
| Meetings | J2 | Dock 1, ⌃2 → meeting | 18 | press does not open; Choose engine primary; gear wing | lane |
| Setup | J6 | HoldSpeak menu → Use everything found | 18 | "Priya Karol"; phone footer | lane |
| Person | J3 | People → Record meeting | 18 | lone Add Buttons | — |
| Automation (open) | J4 | Automations → Run now | 18 | empty band | — |
| Projects | J3 | Go ▸ Projects ▸ All → Room | 19 | three levels deep | — |
| New decision | J2 | the verb → Create | 21 | — | — |
