# Ask, Notes and Memory: betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk, 65 shots,
2026-10-17) and `MODEL.md` (the code map). Companions:
`../engines/DESIGN.md`, `../mcp/DESIGN.md`, `../workbench/DESIGN.md`.
Cluster E of `../PLAN.md`: Ask AI, Threads, Notes and thoughts, Knowledge,
Memory, Search.

## 1. The job

He manages three people and a handful of projects. Many times a day he has a
question about his own work: "What do I owe Mira this week?", "What blocks
the November 5 freeze?", "What did we decide about the rollback?", "Which
risk in this note has no owner?". He wants to ask it from wherever he is (a
note, a meeting, a project, a person, or nowhere), read a short answer that
names its sources, and then act on it in the same place: ask again, make the
task, give it to Mira, keep it. Between meetings he also writes things down:
half an idea, a worry about Jun. He wants those notes to turn into tasks,
questions and project items without retyping them.

He closes the window when:

- he has the answer, and he can see what it looked at;
- what he decided to do is done (the task exists, the note is kept);
- he could find this again tomorrow, from Search or from the person or project.

The README promises this: "Every piece of your work is something you can talk
to" and "Memory that cites its sources". He calls HoldSpeak an agentic OS;
this cluster is where that claim is tested every day.

## 2. What it is today

The full walk is in `RECON.md`.

| Step of the job | What happens today | Shot |
|---|---|---|
| Ask across the desk | Works. Right answer in 9 s. But the sources are every record on the desk (`GROUNDED ON 14 OF 14`), five as raw ids (`Action · m-mira-a0`). | `06-ask-running-t010s-1440.png` |
| Ask with no engine | Says `No engine for answers`, `Choose an engine`. Then three windows and two presses to make it work. | `04-*`, `05-*` |
| Keep the answer | It becomes an artifact named `Summarize`, with a Send block. No follow-up question is possible. | `08-ask-kept-1440.png` |
| Ask about a note | Works, scoped (`Question sources: Ledger migration risks`), 37 s. The old question comes back as `DRAFT · RECOVERED`. | `10-*`, `11-*` |
| Ask about a project | A third face. 100 s, then `No assigned model completed this request`. `Resume`: 131 s, then a raw SQL error. | `27-*` |
| Ask about a person | Not possible. All 13 Object verbs are grey with Mira's window in front. Her window says `YOU OWE` nothing, though three meetings say I owe her. | `33-*` |
| Go on as a Thread | Continue in thread loses the note (`Source unavailable {'ref_kind': 'note', …}`). Every Thread reply was empty, with no error, in 30 ms. | `13-*`, `14-*`, `15-*` |
| Write an idea down | Two menu entries and two different editors for one record. The sticky is good. | `16-*`, `19-new-note-1440.png` |
| Turn it into tasks | `Task` pastes the whole paragraph as one task for Me. `Finish` does nothing. `Develop this thought` runs no model and moves the note into Inbox. | `17-*`, `18-*`, `21-*` |
| Keep reference material | Knowledge is a named list of desk objects, the same as a drawer. It offers modes as `AGENT`. It leaves no icon. | `22-*` |
| Find "what we decided" | Memory is reachable only by Search. It is a search page (`Recent work`, `ALSO 10`, raw ids). The decision is not first. No standing page exists. | `25-*` |
| Ask from Search | No row offers to ask the typed question. Memory snippets show `**` and `[]`. On the phone a tap on a memory row does nothing. | `24-*`, `32-*`, `35-*` |

What worked: the Ask answers were good and fast when the engine was free, the
"no engine" failure speaks in words, the sticky note is light, and the memory
background made sensible beliefs in 20 minutes. The parts are real.

## 3. Why it fails

1. **One job is split into five tools that do not share anything.** Ask AI,
   Ask this project, Object ▸ Ask, the thought's Ask and a Thread each have
   their own window, their own engine row (`ask.answer` and `chat.turn`), their
   own source picker with its own words (`ADD NOTES`, `Question sources`,
   `Sources`, `@`, `Add a note`), and their own way to save (artifact, project
   task, note). An answer cannot become a conversation, a conversation cannot
   start from an answer, and the one with tools (Thread) is the one that did
   not answer (`MODEL.md` §2, §3). He does not want five tools; he wants to
   ask. (`06-*`, `08-*`, `14-*`, `27-*`)
2. **Failures still have no reason.** Recon R1's text is gone from the Ask
   window, but the class of bug is not. A Thread turn that fails completes as
   an empty reply (`MODEL.md` §3). The Room prints `No assigned model
   completed this request`, then a raw SQL error. The likely cause, a
   one-slot engine busy with background work while a 60 s deadline runs twice,
   matches Recon R1's 122 s exactly, and nothing on the face says "the engine
   is busy with meeting analysis". (`14-*`, `27-*`)
3. **Ask is stuffed context, not an agent.** Ask reads a pile of records
   pasted into one prompt (everything on the desk when nothing is picked). It
   cannot look something up, cannot read Jira, cannot make the task he asks
   for. It names its sources as a list of everything it was given, not what
   it used. For "the most advanced agentic OS", the daily question runs on the
   least agentic path in the product. (`MODEL.md` §1)
4. **A note is two things, and "develop" is nothing.** Note and Thought are
   one record with two menu entries and two editors. The words promise an
   engine that helps him think ("Develop this thought") and an end that does
   something ("Finish"); neither runs anything. The meeting turns a
   transcript into decisions and owed items; the note gets none of that.
   (`17-*`, `18-*`, `19-*`, `21-*`)
5. **Memory has no place he would open.** The README sells standing pages
   with cited sentences. On the face there are none; the Memory window is a
   search page reachable only by Search, its rows carry ids, and the person
   window does not know what he owes Mira. Memory works in the background and
   is invisible in the foreground. (`25-*`, `33-person-mira-1440.png`)
6. **Concepts without a job.** Knowledge duplicates drawers. Search finds the
   answer's raw parts but cannot ask. Empty threads count as sources and as
   memory hits. Each extra concept is one more thing to learn and one more
   place to look. (`22-*`, `24-*`, `31-ask-answer-393.png`)

## 4. The design

### The concept

**Ask is one window where he asks his desk a question. The answer comes with
what it looked at, and he can go on, act or keep it, in place. Every Ask is a
Thread from its first question; a Thread is just an Ask he went on with.**

**A note is anything he writes down. The engine can read it with him (Ask
about this note) or pull the tasks, decisions and people out of it (Find the
tasks), the same way it does for a meeting.**

**Memory is what his desk already knows, written as short standing answers
with sources. It shows where he looks (the person, the project, Today), and
Ask reads it first.**

### The words

| He sees | It replaces |
|---|---|
| **Ask** (the app, the verb, ⌘I) | Ask AI, Ask this project, Continue in thread, New Thread, Develop this thought |
| **Ask about this** (on any object) | Object ▸ Ask AI, Ask this project, Continue in thread |
| **a thread** (a saved Ask with more than one question; listed under **Recent** in Ask) | Thread window, New thread, `ASSISTANT` |
| **About** (named chips: *My whole desk*, *Ledger migration*, *Mira Kovacs*, *Platform sync*, *Notes in Work*) | ADD NOTES, Question sources, Sources, `@`, Ground on the rails, Add a note, AI context, GROUNDED ON N OF M |
| **Looked at** (what the answer used, as links) | GROUNDED ON 14 OF 14, Sources · 12, Run details, RECEIPT |
| **Wrote** (with Undo) / **Prepared** (with Send) | Keep as note, `/todo`, Allow once (for desk writes) |
| **Save as note** | Keep, Bin, PLUGIN OUTPUT, Summarize, LINEAGE |
| **Note** (one kind, one window) | Thought, Write a thought, New Note's form editor |
| **Find the tasks** | Develop this thought, Finish, Task (as a paste) |
| **Done** (closes the note; nothing else) | Finish, Resume |
| **Memory**; pages named by their question: **What I owe**, **What changed this week**, **What we decided**, **What is open**, **What I owe Mira** | Recent work, ALSO, REF, BELIEF, CURRENT, SEEN, EVIDENCE, remembered |
| **Ask "…"** (a row in Search) | nothing |
| Engine row **Answers** (in What runs where) | the separate rows for Ask answer, Desk chat and Thought development |

Retired from every face in this cluster: `GROUNDED`, `ASSISTANT`, `Mode ·
None` and the six mode buttons, `CALL` (moves under More), `DRAFT ·
RECOVERED`, `SAVED HERE`, `UNFINISHED`, `Filed · Desk root`, `Dictate about
this` (the mic on the field does that), raw ids, raw markdown, host strings
(`192.168.1.43:8080`).

### The Ask window (desktop)

One window, opened by ⌘I, Go ▸ Ask, a Search row, or **Ask about this** on
any object. It opens at 880×640 or larger.

```
┌ Ask ───────────────────────────────────────────── Recent ▾ ┐
│ About  [ Mira Kovacs ✕ ] [ + ]                             │
│                                                            │
│  You   What do I owe Mira this week?                       │
│                                                            │
│  This week you owe Mira one thing:                         │
│  • Feedback on her cutover design doc, due Friday.         │
│    (1:1 with Mira, Oct 15)                                 │
│  Her promotion packet review is also yours, due in two     │
│  weeks.                                                    │
│                                                            │
│  ▸ Looked at  1:1 with Mira · What I owe Mira · 2 actions  │
│  [ Make it a task ]  [ Save as note ]  [ Copy ]  [ Send… ] │
│                                                            │
│  You   Make the feedback a task for Friday.                │
│                                                            │
│  Done. One task for you, due Friday 24 Oct:                │
│  "Give Mira feedback on the cutover design doc".           │
│  ▸ Wrote  1 task  [ Undo ]                                 │
│                                                            │
│ ┌────────────────────────────────────────────────────┐ 🎙 │
│ │ Ask a follow-up…                                     │   │
│ └────────────────────────────────────────────────────┘     │
│ Claude Code · can use your desk          9 s     [ Ask ]   │
└────────────────────────────────────────────────────────────┘
```

- **About** is one line of named chips above the conversation. Empty means
  *My whole desk*, and the line says so. The **+** opens the one About picker
  (below). Opening Ask from an object puts that object in About and leaves
  the question empty.
- **The answer** is rendered text. Inline source names in brackets are links.
  There is no raw id anywhere.
- **Looked at** is folded by default, one line: what the answer actually used,
  in words, each item a link. For an engine with the desk's tools, the hub
  lists the tool calls it served (meetings read, people read, pages read,
  Jira issues). For an engine without tools, it lists the records the answer
  cited, not the whole pile it was given.
- **The verbs under an answer**: *Make it a task* (owner and date filled from
  the answer; one press adds it, with Undo), *Save as note* (a note titled by
  the question), *Copy*, *Send…* (prepares a send; he presses Send). Only
  verbs that can work are shown.
- **Wrote** and **Prepared** appear under any answer that changed the desk or
  prepared a send, each with Undo or Send (`../mcp/DESIGN.md`).
- **The follow-up box** is always at the foot. A second question makes it a
  thread; nothing else changes on the face.
- **The engine line** at the foot: the engine's name and one phrase: "can use
  your desk" or "reads only what is in About". No host string. Pressing it
  opens the engine picker in place (from Engines), never Settings in a
  second window.
- **Recent** (top right) lists his past asks, newest first, one line each
  (the first question, the About chips, the age). Pressing one reopens it in
  the same window.
- **While it runs**: "Working… 4 s · Claude Code · reading 1:1 with Mira" in
  the answer's place; the steps show as they happen. Nothing above moves.
  **Stop** replaces Ask.
- **A failure says why and offers one fix**, in his words:
  - "The LAN engine is busy with meeting analysis. Ask waits for it, or
    [ Use Claude Code for this one ]."
  - "No engine for answers. [ Choose one ]" (the picker opens in place).
  - "The note 'Platform sync' was deleted, so it left About. [ Ask again ]".
  - "The LAN engine did not answer in 60 s. [ Ask again ]".
  Never "did not answer" when nothing reached the engine, never a raw error.

### The Ask window (phone, 393)

```
┌ ‹ Back   Ask            Recent ┐
│ About: Mira Kovacs ✕   +       │
│ You: What do I owe Mira…       │
│ This week you owe Mira one     │
│ thing: feedback on her cutover │
│ design doc, due Friday.        │
│ ▸ Looked at (3)                │
│ [Make it a task] [Save as note]│
│ [More ▾]                       │
│ ┌──────────────────────────┐🎙 │
│ │ Ask a follow-up…          │   │
│ └──────────────────────────┘   │
│                         [ Ask ]│
└────────────────────────────────┘
```

The same order. Copy and Send go under More. The follow-up box stays above
the keyboard.

### Opening Ask pre-scoped

| From | Press | About becomes |
|---|---|---|
| Anywhere | ⌘I, Go ▸ Ask, phone Go ▸ Ask | *My whole desk* |
| Search | type a question, Enter on **Ask "…"** | *My whole desk*, the question filled and asked |
| A note (window or icon) | **Ask about this** | that note |
| A meeting | **Ask about this** | that meeting |
| A project (Room) | the Room's **Ask** field, or Ask about this | that project |
| A person (window or icon) | **Ask about Mira** | that person |
| A drawer | **Ask about this** | that drawer's contents |
| Selected text in a note | **Ask about this** | that note, with the text quoted in the question |

The Room keeps a one-line **Ask this project** field because the owner looks
there, but pressing Enter opens the Ask window with the project in About; the
Room no longer has its own answer face or unfinished list.

### When an answer becomes a thread

Every Ask is stored as a thread from its first question (decision 1). It
appears in Recent and in Search. It is a "thread" in Recent only after a
second question; a one-question ask shows as the question alone. Nothing asks
him to keep it. **Forget** (under More) deletes it. The old *Keep* (artifact)
and *Bin* go away; *Save as note* is the way to file an answer on the desk.

### Ask my whole desk (the agent)

When the engine on the **Answers** row can use tools (an agent on this Mac,
or a server or service that accepts tool calls), Ask runs as an agent turn:

- It gets **the desk's tools**, the same CONDUCTOR set an automation run gets
  (`../mcp/DESIGN.md`): read anything on the desk (meetings, notes, people,
  projects, decisions, memory pages, Jira, GitHub); write on the desk (notes,
  tasks, Needs-you rows, *proposed* decisions); never send; never change
  settings, engines or authority. About is the starting point, not a fence:
  "What do I owe Mira" starts at Mira and may read the meetings she was in.
- It reads **memory pages first** (`memory.page`), then recall, then the
  records. A page answer is fast and already cited.
- It may **act when he asks it to** ("make it a task for Theo", "add this to
  Ledger migration", "draft my reply to Jun"). Desk writes run at once and
  show under **Wrote** with Undo (decision 3). Sends are only **Prepared**.
  Settings, schedules and authority stop for his press, as today.
- **Looked at** comes from the hub, which serves every tool call through the
  turn's credential and so knows each one. It needs nothing from the agent.
- With an engine without tools, Ask works as today: About is put into the
  prompt, and the engine line says "reads only what is in About". *My whole
  desk* then means the current desk-wide grounding, capped, with memory pages
  first.
- **Modes** leave the face. The Interview mode stays reachable as the
  starter "Interview me about my goals" in the empty Ask window; Chase and
  Draft become what the agent does when asked. The data and MCP tools stay.
- The Call (voice conversation) moves under More ▸ Talk it through.

### Ask goes first

A question he is waiting for must not queue behind background work. When an
Ask runs on an engine that also has background jobs (meeting analysis,
memory facts, pages), the hub holds new background calls to that engine until
the Ask turn finishes. If the engine is still busy after 5 s, the running line
says so in words ("waiting for the LAN engine, busy with meeting analysis")
and offers another engine he has, in one press. The deadline comes from the
engine (a CLI agent needs longer than 60 s), and a retry never starts a second
60 s wait silently.

### The note

One kind, one window: the sticky (today's thought window), for every note.

```
┌ Jun and the cutover weekend ─────────────────────────────┐
│ Jun is nervous about the cutover weekend. Maybe pair him  │
│ with Mira on call, and write the on-call handbook first.  │
│ Theo could own the handbook.                         🎙   │
│                                                          │
│ [ Ask about this ] [ Find the tasks ] [ Project ▾ ] [ Send… ] │
│ Saved 7:31 PM                                   [ Done ] │
└──────────────────────────────────────────────────────────┘
```

- **New Note** (⌃N) is the only way in from the menu; *Write a thought*
  leaves the menu, and ⌃T opens New Note too. The form editor with the format
  bar leaves the face; markdown typed in the sticky still renders.
- The title is the first line, shown once (title bar only).
- **Ask about this** opens Ask with the note in About. This is what "develop
  this note" becomes: thinking it through is a conversation with the note as
  its subject, in the one Ask window. **Add to note** under an answer appends
  the answer to the note, with Undo, so the note grows from the conversation.
- **Find the tasks** runs the meeting's extraction on the note (tasks with
  owners from People, decisions, people named) and shows the same outcome
  rows the meeting shows: *Pair Jun with Mira on call · owner Me*, *Write the
  on-call handbook · owner Theo*. Each row is one press to confirm. Confirmed
  tasks appear where tasks appear (Needs you, the person, the project).
- **Project ▾** adds the note to a project (today's Project well).
- **Done** closes the window. It runs nothing and changes no state the user
  must learn. (Today's Finish and Resume leave the face.)
- Notes stay where he put them. Opening or asking about a note never moves it
  into a drawer.

Phone: the same sticky full screen; the four verbs in one row, wrapping to
two; Done in the title strip.

### The About picker (shared)

One picker, used by Ask, and later by Automations' About line
(`../workbench/DESIGN.md`):

- One field: type a name. It finds meetings, notes, people, projects,
  decisions and drawers **by name**, grouped by kind, newest first.
- Each pick becomes a named chip. A desk object dropped on the Ask window
  becomes a chip.
- Shortcuts at the top before typing: *My whole desk*, *This week's
  meetings*, each person, each project.
- Never offers modes, threads with no answer, artifacts named by a plugin, or
  source-repository roadmaps.

### Knowledge

A Knowledge collection is a named set of desk objects, which is what a drawer
already is (`MODEL.md` §5). So: **New Knowledge leaves the New list**, and each
existing collection shows as a drawer with the same name and members
(decision 2). A drawer is a fine About chip ("Notes in Work", "Reference").
Data and `kb.*` MCP tools stay.

### Memory

Memory becomes a place he uses because it shows up where he already looks:

- **Pages are on by default.** They run on the **Background work** engine
  (or Everything else) as soon as one exists. Today they wait for a separate
  assignment that nobody makes.
- **The person window** shows **What I owe Mira** and **What Mira owes me**
  as its first section, each sentence with its source link (a meeting, a
  1:1, a note). This replaces the empty `YOU OWE` / `THEY OWE YOU` rows.
- **The Room** shows **What is open and who owes it** and **What we decided**
  first, then the rest of the Room.
- **Today** shows **What I owe** and, on Mondays, **What changed this week**.
- **The Memory app** (in Go) opens on the desk pages, then a search field
  that asks: typing a question there runs Ask with *My whole desk*. Beliefs
  (today's observations) appear under each page's **Why** fold, in his words
  ("you plan to write…", never "the owner plans…"), each with its sources.
- **Recall puts the current decision first**, with the decision it replaced
  under it.
- A page with no source sentence says nothing; a page that has not been
  written yet says "Not written yet. Memory needs an engine for background
  work." with the engine picker, once, on the Memory app only.

```
┌ Memory ──────────────────────────────────────────────────┐
│ [ Ask your desk…                                    🎙 ] │
│                                                          │
│ What I owe                                    updated 9:10 │
│ • Feedback on Mira's cutover design doc, Friday.         │
│   (1:1 with Mira)                                        │
│ • The cutover on-call rotation, Friday. (Platform sync)  │
│ ▸ Why                                                    │
│                                                          │
│ What changed this week                                   │
│ • Freeze of the old ledger set for Nov 5, if two clean   │
│   reconciliation runs. (Ledger migration review)         │
│ ▸ Why                                                    │
│                                                          │
│ Projects   Ledger migration ›                            │
│ People     Mira Kovacs › · Theo Brandt › · Jun Park ›    │
└──────────────────────────────────────────────────────────┘
```

Phone: the same, one column; Projects and People as rows.

### Search

- When the typed text reads like a question (ends in "?" or starts with
  who/what/when/why/how/which/did/do/is), the first row is **Ask "…"**. Enter
  asks it. Otherwise **Ask "…"** is the last row, reachable with one arrow.
- One section per kind; no repeated `OBJECTS` or `MEETINGS` headers.
- Memory rows show clean text (no `**`, no `[]`, no ids) and one word for
  why they matched only when it helps ("in the transcript").
- A tap on any row opens it, on the phone too.
- Empty threads (a question with no answer) are not listed.

### The Object menu

- It acts on the front window's object, or the selected icon when no window
  is in front.
- Rows that do not apply are not shown (no greyed rows with an excuse,
  UX-CANON A.11). On a note: Open, Ask about this, Find the tasks, Rename,
  Duplicate, Move to drawer, Delete. On a person: Ask about Mira, Prep 1:1.
- *Continue in thread*, *Ask AI* and *Ask this project* collapse into **Ask
  about this**.

### What one press does

| Verb | One press |
|---|---|
| Ask (⌘I) | Opens Ask, About = My whole desk, cursor in the box. |
| Ask about this | Opens Ask with that object in About, cursor in the box. |
| Ask "…" (Search) | Opens Ask with the text, and asks it. |
| Ask (the button) | Runs the question. Becomes Stop while it runs. |
| Stop | Ends the turn; what was written so far stays, marked stopped. |
| Make it a task | Adds the task the answer names, with owner and date; shows it under Wrote with Undo. |
| Save as note | Makes a note titled by the question, with the answer and its Looked at links; shows "Saved to your desk" with Open. |
| Add to note | (Ask opened from a note) appends the answer to that note, with Undo. |
| Send… | Prepares a send in the Send well; he presses Send there. |
| Copy | Copies the rendered answer. |
| Undo (under Wrote) | Reverses that desk write. |
| Recent ▸ a row | Reopens that ask or thread in the same window. |
| More ▸ Forget | Deletes that ask or thread, with Undo for 10 s. |
| More ▸ Talk it through | Starts the Call on this thread. |
| + (About) | Opens the About picker in place. |
| ✕ on a chip | Removes it from About. |
| Engine line | Opens the engine picker in place. |
| New Note (⌃N) | Opens an empty sticky, cursor in it. |
| Find the tasks | Runs extraction on the note; shows outcome rows to confirm. |
| Confirm (outcome row) | Makes that task or proposed decision. |
| Done (note) | Closes the note window. |
| Memory ▸ a page source | Opens that meeting, note or decision at the cited place. |

### What is removed or parked (nothing is deleted)

- **Thread as a separate window** and **New Thread** in the New list: threads
  open in Ask. The Thread window code is parked.
- **Write a thought**, the note form editor, **Develop this thought**,
  **Finish / Resume**, **ThoughtContextPicker** and the dead thought branch of
  NotePullout: parked. `refinement_thoughts` rows stay; old thoughts open as
  notes.
- **Keep / Bin** and the `Summarize` artifact path of Ask: parked. Old kept
  answers stay as artifacts.
- **The Room's own answer face** and its unfinished list: parked; the
  `project_ask_tasks` data stays readable.
- **New Knowledge**: leaves the New list (decision 2).
- **Thread modes** on the face; **slash commands** stay for the keyboard but
  leave the face (`/todo` becomes Make it a task).
- **The Memory app's search-page face** (`Recent work`, tabs, `ALSO`): parked
  behind RAW.
- In Engines' What runs where, the rows for Ask answer, Desk chat and Thought
  development become one row, **Answers** (a note for `../engines/DESIGN.md`).

## 5. Decisions for the owner

1. **Every Ask is kept as a thread, with no Keep or Bin.** Recent lists them;
   Forget deletes one; Save as note files an answer on the desk. Recommended:
   yes. Ledger, not gate: nothing is lost, and nothing asks him to file.
2. **Knowledge collections become drawers.** New Knowledge leaves the New
   list; each collection shows as a drawer of the same name. Recommended:
   yes. One concept for "a named set of my things".
3. **Ask may write on the desk when he asks it to** (tasks, notes, proposed
   decisions, Needs-you rows) without a hold, shown under Wrote with Undo.
   Sends are only prepared; settings and authority still stop for his press.
   Recommended: yes. It is the same rule as automation runs
   (`../mcp/DESIGN.md` decision 1) and the desk's YOLO default.

This design also applies the plan's ruling "Ask (the verb), its answer can go
on as a Thread" with one change: the user sees one window named **Ask**, and
"thread" is only the word for a saved Ask with more than one question. If the
owner prefers a visible Threads list as its own app, Recent can become that
app without other changes.

## 6. How we know it worked

He presses ⌘K, types "What do I owe Mira this week?", presses Enter, and
reads the answer with its Looked at line in **under 20 s and 3 presses**. He
types "make the feedback a task for Friday" and sees it under Wrote, in the
same window, in **2 more presses**. Then:

- From his note about Jun, **Find the tasks** gives him the two tasks with
  owners in **1 press** plus one Confirm each.
- He opens Mira's window and reads what he owes her, with the meeting it came
  from, in **1 press**, with no Ask.
- On a busy LAN engine, an Ask either answers or says, in words, that the
  engine is busy with meeting analysis and offers his other engine. He never
  sees an empty reply, a raw error, or "did not answer" with no reason.
- Tomorrow he finds yesterday's question in Ask ▸ Recent or Search in **2
  presses**.
