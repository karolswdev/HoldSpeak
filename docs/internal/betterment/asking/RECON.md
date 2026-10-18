# Asking, thinking and memory: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. I walked the
six features of cluster E as a first-time user on a fresh desk, at 1440x900
and 393x852. I fixed nothing. All shots are in `shots/` (65 files). The rig
is in the footnote.[^rig]

The jobs I walked, in the owner's words where we have them:

1. Ask "What do I owe Mira this week?" and get a cited answer.
2. Ask about one note, one project and one person.
3. Go on with an answer as a conversation (a Thread), and have it make a task.
4. Get an idea down, then turn it into a task, a project item or a question.
5. Keep reference material that Ask can use (Knowledge).
6. Ask "what did we decide on the freeze" and get the current answer with its
   sources (Memory), and find any of this again (Search).

The seed: three meetings with transcripts and accepted actions (Platform sync,
1:1 with Mira, Ledger migration review), one project (Ledger migration), one
decision (freeze the old ledger on November 5), two notes (Ledger migration
risks, On-call handbook idea) and three people (Mira Kovacs, Theo Brandt, Jun
Park). The LAN engine `qwen3.8-27b` answered for real.

## Friction log

"Presses" counts presses and typed fields. "Wait" is measured. "Est." is my
estimate for a first-time user who reads the screen.

| # | Step | What I pressed | What I saw (exact text) | What a newcomer expects | Where I got stuck | Presses | Wait / est. | Shots |
|---|---|---|---|---|---|---|---|---|
| 1 | Find Ask | `Go` | `Ask AI ⌘I` in Go, fourth row. Desk menu has nine "New …" verbs, including `New Note`, `Write a thought`, `New Knowledge`, `New Thread` | One Ask | Found at once. The Desk menu offers four ways to start writing or asking | 2 | – / 5 s | `02-menu-go-1440.png`, `02-menu-desk-1440.png` |
| 2 | Ask with no engine | Typed the question, `Ask` | `Ask` is live with `No engine` beside it. After the press: `✕ Answer`, `No engine for answers`, `Choose an engine` | Ask says why, and offers the fix | Works: the reason is in words. `Ask` should not look live when it cannot work | 3 | 1 s / 15 s | `03-ask-empty-noengine-1440.png`, `04-ask-noengine-pressed-1440.png` |
| 3 | Get an engine from Ask | `Choose an engine` → `Find on LAN` → `Use it` → `Answers and notes` → `Qwen3.8 27B` | Settings opens as a second window. `Use it` says `1 engine` but every job still says `no engine`. A second press assigns it: `PATCHED 19:22 · ANSWERS AND NOTES → QWEN3.8 27B`. The menu bar chip reads `→ LAN-SCAN:E63F69AE45A3319E7D37075EC7…` | One press makes Ask work | Same wall the Automations walk met (Engines cluster) | 5 | 6 s / 60 s | `05-ask-*` |
| 4 | Ask across the desk | Back in Ask, `Ask` | `Asking · 192.168.1.43:8080 · LAN · 3 s`, then the answer: "This week you owe Mira one thing: Feedback on her cutover design doc — due Friday." Under it: `GROUNDED ON 14 OF 14` and 14 chips, among them `Action · m-mira-a0`, `Action · m-plat-a1`, `Note · Start here`, `Note · Weekly update`. Foot: `192.168.1.43 · LAN`, `ANSWERED IN 9 S`, `Bin`, `Keep` | The answer, and the two or three sources it used, by name | The answer was right and fast. The sources are every record on the desk, five with raw ids, two of them seed notes. `Run details` holds `LAST TURN · qwen3.8-27b · RECEIPT ··c5c2` | 1 | 9 s / 20 s | `06-ask-running-t002s-1440.png`, `06-ask-running-t010s-1440.png`, `07-ask-run-details-1440.png` |
| 5 | Keep the answer | `Keep` | A new window titled `Summarize`, `PLUGIN OUTPUT`, a `SEND` block with `HoldSpeak folder · FILE`, `LINEAGE · via Summarize · 0 items`, `Copy`, `Dictate about this`. A `Summarize` icon lands on the desk | It is saved with my question as its name, and I can go on asking | The answer is saved as an artifact named "Summarize", not a note and not a conversation. Nothing lets me ask a follow-up | 1 | 2 s / 20 s | `08-ask-kept-1440.png` |
| 6 | Ask about one note | Select `Ledger migration risks`, `Object` ▸ `Ask AI` | Ask opens with `Question sources: Ledger migration risks` and the old question pre-filled: `DRAFT · RECOVERED` | An empty question, scoped to the note | The scope works. The old question came back | 3 | – / 15 s | `09-object-menu-note-1440.png`, `10-object-ask-note-1440.png` |
| 7 | Get the note answer | Typed "Which of these risks has no owner, and who should own it?", `Ask` | A good answer: the reconciliation job has no owner; Theo should own it. `GROUNDED ON 7 OF 7` (it read the whole desk again). It calls me "the desk lead" | – | Good answer. Slow | 2 | 37 s / – | `11-object-ask-note-answer-1440.png` |
| 8 | Ask about the project | Room ▸ `Ask this project…`, typed "What blocks the November 5 freeze?", Enter | A third Ask face. 100 s, then `UNFINISHED 1`, `SAVED 19:34`, `SAVED HERE`, `Resume`, and in red: `No assigned model completed this request` | An answer, or the reason it could not answer | No reason. The engine has one slot and it was busy with background meeting analysis (the `RUNNING · Meeting analysis` toast was up) | 2 | 100 s / – | `26-room-1440.png`, `27-room-ask-running-1440.png`, `27-room-ask-answer-1440.png` |
| 9 | Retry the project question | `Resume` | 131 s, then: `UNIQUE constraint failed: inference_adoption_material_snapshots.operation_id` | The answer | A raw database error on the face. The retry cannot work | 1 | 131 s / – | `27-room-ask-resume-1440.png` |
| 10 | Ask about a person | Opened `Mira Kovacs`; `Object` menu | Mira's window: `YOU OWE` empty, `THEY OWE YOU` empty, `No 1:1 planned`. With her window in front, all 13 Object verbs are greyed, Ask AI too | Ask about Mira, and see what I owe her | No Ask from a person. Her window does not know the three things I owe her that the meetings hold | 2 | – / 20 s | `33-person-mira-1440.png`, `33-person-object-menu-1440.png` |
| 11 | Go on as a Thread | Select the note, `Object` ▸ `Continue in thread` | `New thread`, `Mode · None`, `Sources · 1`, `No turns`. Inside Sources: `Source unavailable` and the raw text `{'ref_kind': 'note', 'ref_id': 'n-risks'}` | The note is the subject of the thread | The note did not arrive. The source shows raw code | 3 | 2 s / 20 s | `12-thread-from-note-1440.png`, `13-thread-mode-sources-open-1440.png` |
| 12 | Ask in the Thread and make a task | Typed "Which risk in this note has no owner? Then make a task for Theo …", `Send` | `YOU` and my text, then `ASSISTANT` with nothing under it, only `Keep as note`, `More`. No error. The thread now lists 12 sources | An answer, and a task with Undo | Silent. The hub stored an assistant reply with no text and no error, completed 30 ms after it started | 2 | 30 ms, then nothing in 2 min / – | `14-thread-running-t003s-1440.png`, `14-thread-reply-1440.png` |
| 13 | A new Thread from the menu | `Desk` ▸ `New Thread`, "What do I owe Mira this week?", `Send` | The same empty `ASSISTANT` reply. The same question in Ask had answered in 9 s on the same engine | – | Threads did not answer once in this walk | 3 | 30 ms / – | `15-new-thread-empty-1440.png`, `15-new-thread-reply-1440.png` |
| 14 | Write an idea down | `Desk` ▸ `Write a thought`, typed three sentences | A sticky window: the first line as a heading, the text, a mic. Foot: `Add a note`, `Copy`, `Ask`, `Task`, `Project`, `Send`, `Finish`, `Saved 7:31 PM` | – | Works and feels light. The title repeats the first line three times (title bar, heading, text) | 2 | – / 20 s | `16-thought-new-1440.png`, `16-thought-typed-1440.png` |
| 15 | Turn it into a task | `Task` | `TASK`, the whole thought pasted as the task text, `↻ ME` (an owner that cycles), a date box, `Add`, `Close` | "Pair Jun with Mira on call" and "Theo owns the handbook" as two tasks with owners | It does not read the note. One task, my whole paragraph, owner Me | 1 | – / 30 s | `17-thought-task-1440.png` |
| 16 | Finish the thought | `Finish` | `Ask` disappears, `Finish` becomes `Resume`. Nothing else happens | The tasks and people in it are found, like a meeting | Finish only flips a state | 1 | – / 10 s | `18-thought-finished-1440.png` |
| 17 | Make a note the other way | `Desk` ▸ `New Note` | A different window: `Edit New note`, a title box, a format bar `B I U H1 H2 H3 List 1. </> Link Quote`, `Write`, `Tags`, `Done` | The same sticky as step 14 | Two editors for one kind of record | 1 | – / 10 s | `19-new-note-1440.png` |
| 18 | Develop an existing note | Opened `Ledger migration risks`; `Develop this thought` | Before: `Filed · Desk root`, `Copy`, `Dictate about this`, `Develop this thought`. After: the sticky window of step 14. No model ran. The note moved off the desk into the Inbox drawer | The engine helps me think it through | "Develop" only changes which window shows the note, and moves it | 2 | – / 30 s | `20-note-open-1440.png`, `21-note-developed-1440.png`, `23-inbox-drawer-1440.png` |
| 19 | Keep reference material | `Desk` ▸ `New Knowledge` ▸ `Add items` | `Edit New Knowledge`, `Items · No items`. The list offers meetings, notes, the decision, two `New thread` rows, the project, six modes as `AGENT` (`Chase`, `Desk`, `Draft`, …) and four `ROADMAP` rows from the HoldSpeak source repository | Name it, add files or notes, done | No name step. "Knowledge" is a named list of desk objects, the same as a drawer. Modes appear as agents | 4 | – / 45 s | `22-knowledge-new-1440.png`, `22-knowledge-add-items-1440.png`, `22-knowledge-two-items-1440.png` |
| 20 | Find the Knowledge again | `Done`, looked at the desk | No icon for it. `New note` and the thought are not on the desk either | What I make is where I can see it | Three things I made this session are not on the desk | 1 | – / 20 s | `22-knowledge-done-1440.png` |
| 21 | Search | `⌘K`, "rollback" | `OBJECTS`: the note (selected). `MEMORY`: the two empty threads (`LINK`), the Platform sync line with `rollback` marked, the action `Mira 2026-10-22 pending`. Chips `KEYWORD`, `LINK` | – | Good: the object row is selected first. The empty threads come up as memory | 2 | 2.5 s / 10 s | `24-search-empty-1440.png`, `24-search-rollback-1440.png` |
| 22 | Ask from Search | `⌘K`, "what did we decide about the freeze" | Four memory rows; the decision's text ends in `[]`. No row offers to ask the question | "Ask this" as a row | Search and Ask do not know each other | 2 | 3 s / 15 s | `24-search-question-1440.png` |
| 23 | Open Memory | `⌘K`, "memory", Enter | `Memory`, `Recent work`, `SEARCHED 19:32`, tabs `ALL DECISIONS COMMITMENTS BRIEFS MEETINGS`, `OWED 6` with `Done` on each, `MEETINGS 3`, `ALSO 10` with raw ids `note_c2933c562148`, `th_28a810d95cf5` | Standing pages: what I owe, what we decided, with sources | Memory is a search page. There are no standing pages. Only Search reaches it | 3 | 3 s / 30 s | `24-search-memory-1440.png`, `25-memory-app-1440.png`, `25-memory-app-scrolled-1440.png` |
| 24 | Ask Memory the question | Typed "What did we decide about the freeze?" in Memory, Enter | `4 remembered`, `REF · WHAT DID WE DECIDE ABOUT THE FREEZE?`. First: the meeting line "We need to decide the freeze date". The decision is under `ALSO`, with `[]`. Two empty threads as `thread:th_…` | The decision first, then where it came from | Recall does not put the current decision first | 2 | 4 s / 20 s | `25-memory-search-question-1440.png`, `25-memory-beliefs-1440.png` |
| 25 | Memory on the phone, 20 minutes later | Search ▸ "memory" | `CURRENT 7`: beliefs such as "The owner plans to write a one-page on-call handbook…", each with `BELIEF`, `CURRENT`, `1 SOURCE`, `SEEN 10-17`, `EVIDENCE NOTE 10-17` | – | The background work had made beliefs. They speak of "the owner". The desktop window still showed the last search | 3 | – / 20 s | `34-memory-393.png` |
| 26 | Ask on the phone | `Go` ▸ `Ask AI`, typed, `Ask` | Full-screen Ask. Answer in 35 s (the engine was busy): the freeze decision, `GROUNDED ON 6 OF 6`, two of them `Thread · New thread` (the empty ones). `Keep`, `More` | – | Works. Empty threads count as sources | 3 | 35 s / – | `31-ask-393.png`, `31-ask-running-393.png`, `31-ask-answer-393.png` |
| 27 | Search on the phone | Search, "Mira"; then "What do I owe"; tapped a memory row | `PEOPLE`, `MEETINGS`, `VERBS` (`Prep 1:1 with Mira Kovacs`), `OBJECTS`, `MEETINGS` again, `PROJECTS`, `OBJECTS` again, `VERBS`, `MEMORY` with `**Feedback on her cutover design doc**` (raw markdown). A tap on a memory row did nothing | One list, and a tap opens the row | Sections repeat. The tap is taken by the panel, not the row | 4 | – / 30 s | `32-search-mira-393.png`, `34-search-thread-393.png`, `35-search-row-tap-ignored-393.png` |
| 28 | The thought on the phone | Search "Jun is nervous", Enter | The sticky, full screen, `Resume`, `More` | – | Works | 3 | – / 10 s | `36-search-thought-393.png`, `36-thought-393.png` |

## Verbs that did nothing, failed, or did something else

1. **Thread replies are empty and silent.** Two threads, two empty `ASSISTANT`
   replies, 30 ms each, no error (`14-thread-reply-1440.png`,
   `15-new-thread-reply-1440.png`). The same engine answered Ask in 9 s.
2. **Room ▸ Ask this project** failed after 100 s with `No assigned model
   completed this request` (`27-room-ask-answer-1440.png`), and `Resume`
   failed with a raw SQL error (`27-room-ask-resume-1440.png`).
3. **Object ▸ Continue in thread** loses the object: the thread shows
   `Source unavailable {'ref_kind': 'note', 'ref_id': 'n-risks'}`
   (`13-thread-mode-sources-open-1440.png`).
4. **Keep** saves the answer as an artifact named `Summarize`, with a Send
   block (`08-ask-kept-1440.png`). The question is lost as its name.
5. **Develop this thought** runs no model. It switches the window and moves the
   note into Inbox (`21-note-developed-1440.png`, `23-inbox-drawer-1440.png`).
6. **Finish** on a thought only flips `Finish` to `Resume`
   (`18-thought-finished-1440.png`).
7. **Task** on a thought pastes the whole text as one task for Me
   (`17-thought-task-1440.png`).
8. **The Object menu** greys all 13 verbs when a person window is in front
   (`33-person-object-menu-1440.png`). On a selected note it greys 3 of 13
   (`Ask this project`, `Draft update`, `Archive`), which do not apply to a
   note and should not be shown.
9. **A tap on a memory row** in phone Search did nothing
   (`35-search-row-tap-ignored-393.png`).

## Words a newcomer would not understand

Copied exactly as shown: `GROUNDED ON 14 OF 14`, `Action · m-mira-a0`,
`Run details`, `LAST TURN · qwen3.8-27b · RECEIPT ··c5c2`, `Bin`, `Keep`,
`PLUGIN OUTPUT`, `LINEAGE · via Summarize · 0 items`, `Dictate about this`,
`DRAFT · RECOVERED`, `Question sources:`, `ADD NOTES`, `UNFINISHED 1`,
`SAVED HERE`, `Resume`, `Mode · None`, `DESK INTERVIEW CHASE DRAFT PLAN
PROJECT`, `Sources · 12`, `Source unavailable`, `ASSISTANT`, `CALL`,
`Thread details`, `Filed · Desk root`, `Develop this thought`, `Finish`,
`↻ ME`, `Edit New Knowledge`, `Items`, `AGENT` (for modes), `ROADMAP`,
`MEMORY`, `KEYWORD`, `LINK`, `MEANING`, `Recent work`, `SEARCHED 19:32`,
`ALSO 10`, `REF ·`, `4 remembered`, `BELIEF`, `CURRENT`, `SEEN 10-17`,
`EVIDENCE DEC 10-17`, `RELATED · REFERENCED BY THREAD`, `thread:th_…`,
`note_c2933c562148`, `→ LAN-SCAN:E63F…`, `→ YOUR NETWORK`, `192.168.1.43:8080 · LAN`.

## What worked

- **Ask itself.** "What do I owe Mira this week?" answered right in 9 s, from
  the 1:1 transcript, and told the promotion packet apart as "not this week"
  (`06-ask-running-t010s-1440.png`). The note-scoped answer reasoned well and
  named an owner (`11-object-ask-note-answer-1440.png`).
- **Ask says why when it has no engine** (`04-ask-noengine-pressed-1440.png`).
  The Recon R1 "THE HUB REFUSED IT" text is gone from the Ask window.
- **The sticky note** is quick, and its foot has the right verbs (Ask, Task,
  Project, Send).
- **Search** selects the object row first, and finds transcript lines by word.
- **Memory's background work** made sensible beliefs within 20 minutes.

## Unknown (not verified)

- **Why Thread replies come back empty.** The stored reply has a receipt id and
  no text, no error and no tool-turn steps. The code path that completes a
  failed turn with no error text is named in `MODEL.md` §3; what failed under
  it, I did not trace.
- **Whether the Room failure was the busy engine.** The LAN server has one
  slot (`/slots` reported one, busy), and meeting analysis and memory
  extraction were running. A 60 s deadline with two attempts matches both the
  100 s here and the 122 s in Recon R1. I believe this is the cause; I did not
  prove it.
- **Why no standing page was written.** I set the default engine myself, and
  beliefs appeared, but `/api/memory/pages` stayed empty for the desk and the
  project for about 20 minutes.
- **Why "Ledger migration risks" and the new items left the desk.** I saw
  where they went (Inbox) only for two of them.
- **The four `ROADMAP` rows** in Knowledge's list probably come from the
  rig's working repository, not from a real user's desk.

[^rig]: An isolated hub through `scripts/graph_walk.py serve` on port 8801,
    with the environment of `_isolated_hub_env` (scratch `HOME` from
    `mktemp -d`, every isolation switch, no repository root). The code was
    the owner's desk worktree (`wt-daily-delight-delivery-20261017`, the
    merge of #1247; main had only one later product change, in setup routes),
    with its own built bundle. Seed written into the scratch database with the
    product's own services (`MeetingState` with transcripts and accepted
    actions, `PrimitiveService` notes and decision, `PeopleService`
    relationships, `projects.create_project`). Real LAN engine `qwen3.8-27b`
    at `192.168.1.43:8080`, assigned through Settings ▸ Engines on the face;
    replies are real. Chromium headless through Playwright, driven from a
    small local driver on port 8809; 1440x900 and 393x852 (mobile, touch,
    scale 2). The hub, the driver and the scratch HOME were removed at the end.
