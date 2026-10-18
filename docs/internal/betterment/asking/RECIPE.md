# Ask, Notes and Memory: the recipe

The build slices for `DESIGN.md`. Each slice is one PR in the fast cycle
(`CLAUDE.md`): quick check, merge, the main watcher runs the whole suite,
Astra reviews after. Each merge leaves the desk better and never half-broken.
Tests follow the test diet: T1 a hub test (`tests/unit|integration/test_desk_<app>.py`),
T2 one vitest file per app (`web/src/**/__tests__/<app>.app.test.tsx`), T3 the
desk sweep (`tests/e2e/test_desk_sweep.py`), T4 a real browser only for drag,
focus, keys, touch or exact geometry. Test doubles replay recorded real hub
answers (`web/src/test/recordedHub.ts`), never typed ones.

Order and dependencies:

| Slice | Name | Needs |
|---|---|---|
| Q0 | Threads tell the truth | – |
| Q1 | The Room's Ask tells the truth | – |
| Q2 | Ask goes first | – |
| Q3 | Search asks | – |
| Q4 | One Ask window | Q0 |
| Q5 | Ask about this, from everywhere | Q4 |
| Q6 | The About picker | Q4 |
| Q7 | Ask my whole desk | Q4, Engines E1, MCP M1 |
| Q8 | One note | Q4 |
| Q9 | Find the tasks | Q8 |
| Q10 | Knowledge becomes drawers | Q6 |
| Q11 | Memory where he looks | – |
| Q12 | The Memory app | Q4, Q11 |

Q0 to Q3 are repairs and can start now, in parallel. Q11 can start now.

---

## Q0. Threads tell the truth

- **Goal**: a Thread reply is never empty and silent; Continue in thread brings
  the object with it.
- **Files**: `holdspeak/services/thread_service.py`,
  `web/src/desk/verbRegistry.ts`, `web/src/desk/pullouts/ThreadPullout.tsx`,
  `tests/unit/test_desk_thread.py` (new or existing per app).
- **Changes**:
  1. In the streaming turn, when a pass ends with `outcome != "succeeded"`
     (any mode, not only Interview), set `error_code` and a plain error text
     from the routed result (`thread_service.py:1326-1350`), so that the
     message completes with `error_json` (`:1826-1841`). When the outcome is
     `succeeded` but no text and no tool call came back, fail it with
     "The engine finished without an answer".
  2. Find and fix the cause of the empty replies seen in `RECON.md` steps 12
     and 13 (the turn completes 30 ms after it starts, with a receipt and no
     parts, on an engine that answers Ask). Record the cause in the PR.
  3. `object.continue-in-thread` sends string refs (`"note:n-risks"`), or the
     service accepts `{ref_kind, ref_id}` objects and freezes the real ref with
     its body (`verbRegistry.ts:543`, `thread_service.py:236-241`).
  4. The Thread face prints the error words under the reply, with **Ask
     again**, using `runWords.ts`. A source that cannot be read shows its name
     and "was deleted", never a dict.
- **Done when**: on a hub with the LAN engine, Desk ▸ New Thread, "What do I
  owe Mira this week?", Send gives an answer, or a reply that says why in
  words. Object ▸ Continue in thread on a note lists the note by title under
  Sources, and the first reply uses it. At 1440 and 393.
- **Tests**: T1: a failed routed turn completes with `error_json`; a seed ref
  object is stored as the real ref. T2 (`thread.app.test.tsx`): a recorded
  failed turn renders the reason and Ask again.
- **Not in this slice**: merging Thread into Ask (Q4); tools in Ask (Q7).

## Q1. The Room's Ask tells the truth

- **Goal**: Ask this project answers, or says why in words; Resume works.
- **Files**: `web/src/features/project-room/ProjectRoomCore.tsx`,
  `holdspeak/services/ask_service.py` (or the adoption service that writes
  `inference_adoption_material_snapshots`), `web/src/desk/ask.ts`,
  `tests/unit/test_desk_room_ask.py`.
- **Changes**:
  1. The Room prints `reasonWords(reason)` (`runWords.ts`), never the hub's
     raw sentence (`ProjectRoomCore.tsx:2141`).
  2. Resume on a stopped project ask must not reuse the old operation id for
     the material snapshot (the `UNIQUE constraint failed:
     inference_adoption_material_snapshots.operation_id` of
     `RECON.md` step 9). Give the retry its own operation, or reuse the
     snapshot.
  3. The hub sends a `reason` for every refusal, including `ValidationError`
     cases and `grounding_not_found`, so `ask.ts:264-267` never falls back to
     `did_not_answer` when nothing reached the engine.
- **Done when**: in a Room with a busy one-slot engine, Ask this project ends
  with words such as "The LAN engine was busy and did not answer in 60 s" and
  **Ask again**; Ask again runs and answers. At 1440 and 393.
- **Tests**: T1: Resume after a stopped ask succeeds against a recorded
  engine reply; every ask refusal path carries a `reason`. T2
  (`room.app.test.tsx`): a recorded failure renders words, never raw text.
- **Not in this slice**: moving the Room's Ask into the Ask window (Q5).

## Q2. Ask goes first

- **Goal**: a question he waits for never queues silently behind background
  work.
- **Files**: the intelligence queue conductor and the memory conductor
  (`holdspeak/intel_queue_conductor.py`, `holdspeak/memory_conductor.py`), the
  adoption service's admission, `web/src/desk/components/AskPanel.tsx`,
  `web/src/desk/surface/runWords.ts`, `tests/integration/test_desk_ask_priority.py`.
- **Changes**:
  1. While a foreground turn (`ask.answer`, `chat.turn`) is admitted to an
     engine, background callers (meeting analysis, `memory.extract`,
     `memory.page`) do not start new calls on that engine. They resume when
     the turn ends.
  2. If the engine is still busy 5 s after the Ask starts, the hub sends a
     `busy` progress event naming the background job; the running line reads
     "Waiting for the LAN engine, busy with meeting analysis", and offers
     another assigned or available engine in one press.
  3. The deadline comes from the engine kind (a CLI agent gets longer), and a
     second attempt after a deadline is shown ("Trying again, 1 of 2"), never
     silent.
- **Done when**: with meeting analysis running on the LAN engine, Ask "What
  do I owe Mira this week?" answers within the engine's own answer time plus
  the time to finish the one call in flight, or shows the busy words within
  6 s. At 1440.
- **Tests**: T1 (integration): a background job waits while a foreground
  turn is admitted to the same engine; the busy event is sent after 5 s.
  T2 (`ask.app.test.tsx`): the recorded busy event renders the words and the
  other-engine button.
- **Not in this slice**: engine kinds themselves (Engines E-slices).

## Q3. Search asks

- **Goal**: he types a question in ⌘K and gets an answer in one Enter; the
  memory rows read cleanly.
- **Files**: `web/src/desk/components/DeskToolShelf.tsx`,
  `web/src/desk/components/paletteHit.tsx`, `holdspeak/web/routes/memory*.py`
  (snippet cleaning), `web/src/desk/components/__tests__/search.app.test.tsx`.
- **Changes**:
  1. A row **Ask "…"** is first when the text reads like a question (ends in
     "?" or starts with who, what, when, why, how, which, did, do, does, is,
     are), else last. Enter opens Ask with the text and runs it (today's Ask
     window is fine for this slice).
  2. One section per kind; merge the repeated `OBJECTS` and `MEETINGS`
     sections.
  3. Memory snippets are plain text: strip markdown marks and empty `[]`.
     Rows never show raw ids. Threads with no answer are not listed.
  4. The found-by chip shows only `in the transcript` / `in a note` /
     `by meaning`, as plain words.
  5. A tap on a memory row opens it on the phone (the shelf must not take the
     pointer event, `RECON.md` step 27).
- **Done when**: ⌘K, "what did we decide about the freeze?", Enter shows the
  answer. On the phone, a tap on a memory row opens it. At 1440 and 393.
- **Tests**: T2: the Ask row ranks first for a question; snippets render with
  no `**`; recorded memory hits from `/api/memory/search`. T4 (touch): one tap
  test on a memory row at 393.
- **Not in this slice**: changing recall ranking (Q12).

## Q4. One Ask window

- **Goal**: Ask and Thread are one window; an answer can be followed up in
  place; every ask is kept under Recent.
- **Files**: `web/src/desk/components/AskPanel.tsx` (becomes the Ask window
  over a thread), `web/src/desk/threads.ts`, `web/src/desk/ask.ts`,
  `holdspeak/services/thread_service.py`, `holdspeak/services/ask_service.py`,
  `web/src/desk/applications.ts`, `web/src/desk/verbRegistry.ts`,
  `web/src/desk/components/__tests__/ask.app.test.tsx`.
- **Changes**:
  1. Pressing Ask creates a thread and runs its first turn. For an engine
     without tools, the turn uses today's Ask grounding (About in the prompt,
     memory pages first), so answers stay as good as today. Store the
     grounding refs the answer cites, to draw **Looked at**.
  2. The window draws the conversation: About line, You / answer pairs, the
     answer's verbs (Save as note, Copy, Send…), the follow-up box, the
     engine line ("reads only what is in About"), Stop while running.
  3. **Recent** (top right) lists threads newest first; a row reopens it.
     **More ▸ Forget** deletes with Undo.
  4. **Save as note** makes a note titled by the question with the answer and
     its links. Keep, Bin and the `Summarize` artifact path leave the face
     (parked).
  5. One engine row: `chat.turn` follows the `ask.answer` assignment when it
     has none of its own, so the user sets **Answers** once.
  6. Desk ▸ New Thread and the Thread window open the Ask window. The Thread
     window is parked.
  7. No raw ids, no host string, no `GROUNDED ON`.
- **Done when**: ⌘I, ask, read the answer, type a follow-up, read the second
  answer, close, reopen from Recent: all in one window. At 1440 and 393.
- **Tests**: T1: Ask creates a thread with one user and one assistant
  message; Looked at refs are stored. T2: the window renders a recorded
  two-turn thread, Save as note, Recent. T3: the sweep covers the Ask window at
  both widths.
- **Not in this slice**: tools (Q7), the About picker (Q6; keep today's
  pickers, relabelled About).

## Q5. Ask about this, from everywhere

- **Goal**: one verb, **Ask about this**, on every object, opening Ask
  pre-scoped.
- **Files**: `web/src/desk/verbRegistry.ts`, `web/src/desk/objectMenu.ts`,
  `web/src/desk/components/DeskMenuBar.tsx`,
  `web/src/features/project-room/ProjectRoomCore.tsx`, the person window
  (`web/src/desk/pullouts/` people view), `web/src/desk/__tests__/objectMenu.app.test.tsx`.
- **Changes**:
  1. Replace Object ▸ Ask AI, Ask this project and Continue in thread with
     **Ask about this** (on a person: **Ask about Mira**). It opens Ask with
     the object in About and an empty question.
  2. The Object menu acts on the front window's object, else the selected
     icon. Rows that do not apply are not shown; no greyed rows with excuses.
  3. The Room's Ask field opens Ask with the project in About and runs the
     question; the Room's answer face and unfinished list are parked.
  4. Selected text in a note: Ask about this quotes it in the question.
  5. The hub reads a project chip in About as the project's records (meetings,
     notes, decisions, open items), not its title (`ask_service.py:700-707`).
- **Done when**: from a note, a meeting, the Room, Mira's window and a
  drawer, one press opens Ask with the right chip. With Mira's window in front,
  the Object menu shows only verbs that work. At 1440 and 393.
- **Tests**: T2: menu rows per kind, front-window object; the Room field
  opens Ask with the project chip. T1: a project About grounds on its records.
- **Not in this slice**: the shared picker (Q6).

## Q6. The About picker

- **Goal**: one picker that finds his things by name, used by Ask (and ready
  for Automations).
- **Files**: new `web/src/desk/about/AboutPicker.tsx`, `AskPanel.tsx`,
  `web/src/desk/grounding.ts`, `web/src/desk/about/__tests__/about.app.test.tsx`.
- **Changes**: one name field; finds meetings, notes, people, projects,
  decisions and drawers by name, grouped, newest first; shortcuts *My whole
  desk*, *This week's meetings*, each person, each project; picks become
  chips; dropping a desk object on the Ask window adds a chip. Never lists
  modes, unanswered threads, plugin-named artifacts or repository roadmaps.
  Replace ADD NOTES, Ground on the rails and Question sources in Ask.
- **Done when**: in Ask, + then "Mira" offers Mira, the 1:1 and her meetings;
  a dragged note becomes a chip. At 1440 and 393.
- **Tests**: T2 against recorded search answers. T4: one drag-a-note test.
- **Not in this slice**: Automations' About line (their recipe adopts this
  component).

## Q7. Ask my whole desk

- **Goal**: on an engine that can use tools, Ask looks things up and acts,
  and shows Looked at, Wrote and Prepared.
- **Files**: `holdspeak/services/thread_service.py`,
  `holdspeak/services/thread_tools.py`, `holdspeak/mcp/palettes.py`,
  `holdspeak/tool_authority.py` (read only), `AskPanel.tsx`,
  `tests/integration/test_desk_ask_tools.py`.
- **Changes**:
  1. An Ask turn on a tool-capable engine gets the CONDUCTOR set (reads,
     including People and memory pages; desk writes; no send, config or
     authority; no nested model tools), as `../mcp/DESIGN.md` rules for
     automation runs. For agents on this Mac, attach only HoldSpeak's MCP
     server (Engines E-slices supply the CLI engine).
  2. The system prompt tells it to read memory pages first and to treat About
     as the starting point.
  3. The hub records every tool call it serves for the turn and returns
     **Looked at** (reads, by name), **Wrote** (desk writes, each with an
     undo handle) and **Prepared** (sends). The window draws them.
  4. **Make it a task** under an answer runs the same write the agent would.
  5. Modes leave the face; "Interview me about my goals" is a starter in the
     empty Ask window.
  6. The engine line says "can use your desk".
- **Done when**: with a tool engine, "What do I owe Mira this week?" with no
  About answers from her meetings and her pages, and Looked at lists them as
  links; "make it a task for Friday" shows the task under Wrote, and Undo
  removes it. No send leaves without his press. At 1440 and 393.
- **Tests**: T1 (integration): a recorded tool turn produces Looked at and
  Wrote; a send tool call becomes Prepared, not sent; a config tool is
  refused. T2: the window renders a recorded tool turn.
- **Not in this slice**: other MCP servers inside a turn (MCP decision 2).

## Q8. One note

- **Goal**: a note is one thing with one window; "develop" means asking about
  it.
- **Files**: `web/src/desk/verbRegistry.ts`, `web/src/desk/newThought.ts`,
  `web/src/desk/pullouts/Pullout.tsx`,
  `web/src/desk/pullouts/ThoughtWorkspaceWindow.tsx`,
  `web/src/desk/pullouts/NotePullout.tsx`, `web/src/desk/pullouts/__tests__/note.app.test.tsx`.
- **Changes**:
  1. Every note opens in the sticky window. New Note (⌃N) and ⌃T both open an
     empty sticky. *Write a thought* leaves the Desk menu; the form editor and
     *Develop this thought* leave the face (parked).
  2. The foot: **Ask about this**, **Find the tasks** (hidden until Q9),
     **Project ▾**, **Send…**, and **Done** in place of Finish/Resume.
  3. The title shows once (title bar); the heading that repeats the first
     line goes.
  4. Opening, asking about or finishing a note never moves it to another
     drawer.
  5. In Ask opened from a note, **Add to note** under an answer appends it to
     the note, with Undo.
- **Done when**: Desk ▸ New Note opens the sticky; an old plain note opens in
  the sticky with its text intact; Ask about this then Add to note grows the
  note; the note stays where it was. At 1440 and 393.
- **Tests**: T2: every note routes to the sticky; Add to note writes and
  undoes. T1: adopting is no longer required to open a note. T3: sweep.
- **Not in this slice**: extraction (Q9).

## Q9. Find the tasks

- **Goal**: one press pulls the tasks, owners and decisions out of a note, as
  a meeting does.
- **Files**: the meeting outcome extraction service (reuse, do not copy),
  `holdspeak/services/refinement_thought_service.py` or a new
  `note_outcomes_service.py`, `ThoughtWorkspaceWindow.tsx`, the outcome row
  component from the meeting face, `tests/unit/test_desk_note_outcomes.py`.
- **Changes**: run the meeting's extraction over the note text with the People
  list for owner matching; show the meeting's outcome rows under the note
  (task, owner, date; proposed decision); Confirm makes the task or the
  proposed decision with the note as its source; the rows stay with the note.
- **Done when**: the Jun note gives "Pair Jun with Mira on call (Me)" and
  "Write the on-call handbook (Theo)"; Confirm puts each where tasks show
  (Needs you, Theo's window). At 1440 and 393.
- **Tests**: T1 with a recorded engine reply; T2 the outcome rows on a note.
- **Not in this slice**: running extraction on its own when a note is saved
  (a later automation can do that).

## Q10. Knowledge becomes drawers

- **Goal**: one concept for "a named set of my things".
- **Files**: `web/src/desk/verbRegistry.ts`, the drawer listing
  (`web/src/desk/drawer/`), `holdspeak/services/primitive_service.py` (read
  path), `tests/unit/test_desk_drawers.py`.
- **Changes**: New Knowledge leaves the New list; each existing collection
  shows as a drawer with its name and members (read through the drawer view;
  the `kbs` data and `kb.*` tools stay); the About picker lists them as
  drawers.
- **Done when**: an existing collection appears as a drawer on the desk and as
  an About chip; nothing offers "Knowledge". At 1440 and 393.
- **Tests**: T1: a kb reads as a drawer; T3: sweep.
- **Not in this slice**: migrating kb rows into directory rows.

## Q11. Memory where he looks

- **Goal**: Mira's window says what he owes her, with sources, without an Ask.
- **Files**: `holdspeak/memory/pages.py`, `holdspeak/memory/engine.py`,
  `holdspeak/memory_conductor.py`, `web/src/desk/standingPages.tsx`, the person
  window, `ProjectRoomCore.tsx` (Pages fold order), Today's view,
  `tests/integration/test_desk_memory_pages.py`.
- **Changes**:
  1. Pages run on the Background work engine (or Everything else) by default,
     with no separate assignment. Find why no page was written in the walk
     (`RECON.md` Unknown) and fix it.
  2. Add the person pages to the fixed set if missing (*What I owe them*,
     *What they owe me*), as `docs/internal/MEMORY-DESIGN.md` §3.4 lists.
  3. The person window shows those two pages first; the Room shows *What is
     open* and *What we decided* first; Today shows *What I owe*.
  4. Page sentences and beliefs speak to him ("you"), never "the owner".
- **Done when**: on a seeded desk with an engine, within one background pass,
  Mira's window lists "Feedback on her cutover design doc, Friday (1:1 with
  Mira)" with a working link. At 1440 and 393.
- **Tests**: T1 (integration): a recorded page write for a person scope; the
  read API returns it. T2: the person window renders recorded pages.
- **Not in this slice**: the Memory app face (Q12).

## Q12. The Memory app

- **Goal**: Memory is in Go and opens on the answers, not on a search form.
- **Files**: `web/src/desk/applications.ts`,
  `web/src/pages/cores/ProjectMemoryCore.tsx` (a new `MemoryCore.tsx`),
  `holdspeak/services/recall_service.py`,
  `web/src/pages/cores/__tests__/memory.app.test.tsx`.
- **Changes**: Memory gets a Go row; the window opens on the desk pages (What
  I owe, What changed this week), each with **Why** (beliefs with sources),
  then Projects and People rows that open their pages; the top field asks
  (opens Ask with the text). Recall puts the current decision first, the
  replaced one under it. The old search face is parked behind RAW.
- **Done when**: Go ▸ Memory, read "What I owe" with sources in 1 press;
  typing "what did we decide about the freeze?" in its field answers with the
  decision first. At 1440 and 393.
- **Tests**: T2 with recorded pages and recall; T1 recall order; T3 sweep.
- **Not in this slice**: page editing or new page kinds.
