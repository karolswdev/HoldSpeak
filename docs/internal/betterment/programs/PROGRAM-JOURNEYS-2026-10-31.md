# Programs: modeled user journeys (PG-JOURNEYS)

Owner, 2026-10-31: "Make sure you perfect the design and also immediately
draft, project and model user journeys that solve multiple use cases.
Including, e.g., haiku driven nightly 'dreaming' program that uses our idle
GPU with pi, on super broken down tasks (IMO our context maxes out at 64k
tokens). And so on. Again - from dropping only a couple of paragraphs, to a
broken down, refined down sets of steps that execute, verify, prove, to some
kind of 'Architecture, Product, Stacker, and so on' interview rounds and gates
to allow me to provide down to detail level of clarity, smoothly. So UX will
be key. If it means canvas? It means that."

Earlier the same day: Programs is the SDK and the flagship. Voice or typed
shaping goes through inference to a program text with a shown diff; planning
is inference; the definition phase runs from hands-off to very hands-on
(detail, gates, verification kinds); Delivery Workbench appears only at major
points; delight is execution perfection; a library or engine change rides in
the same plan.

Sources: `PROGRAMS-DESIGN-2026-10-28.md` (the engine as built, with its
"Built" and PG19 sections), `PROGRAMS-REQUIREMENTS-2026-10-31.md` (PG-REQ,
merged in #1665), `docs/programs.md` (the user doc), `docs/calls.md` and
`docs/phone.md` (the call and the phone), `holdspeak/program_templates.py`, the
code on `main` at `cb6ab84e5`. Canvas:
`canvases/program-journeys-2026-10-31.html` (storyboards for J1, J2, J3 and
J6, and the interview round in two directions with the recommended one
marked).

**The sibling design.** `PROGRAM-LANGUAGE-2026-10-31.md` (lane PG-LANG,
written in parallel) owns the program text grammar, shaping, planning
inference, the interview rounds as an engine contract, and the 64k step
sizing. This document does not define any of them. Where a journey shows a
program text, it is an illustration in the simplest form that reads; the
grammar of PG-LANG wins over every snippet here. The "What the journeys
demand" table marks each such need **In PG-LANG**, so that lane's slices can be
checked against it.

## 0. The journeys in one line each

| | Journey | Who and when | The one thing it proves |
|---|---|---|---|
| J1 | Two paragraphs to a shipped change | at his desk, a weekday afternoon | a pasted idea becomes steps with requirements through five short interview rounds, and ends proven, with one Delivery Workbench milestone |
| J2 | The dreaming program | 23:30 to 07:00, the home GPU idle | a cheap planner keeps a backlog of tiny steps that each fit 64k; pi builds them under YOLO; he wakes to a digest and only what is his |
| J3 | Shaping a running program by voice | at his desk, a program half done | three spoken sentences become one shown diff; he applies it; Undo and Overturn stay possible |
| J4 | From the desk, for a person | after a 1:1 | one open action becomes a Program for Alice, and Alice reviews the pull request |
| J5 | The race | a brief he does not want to wait on | Claude Code and Codex build the same brief; the first green and reviewed branch wins |
| J6 | Start and steer from the phone and the Line | in the car at night, in the kitchen at 06:40 | start by voice, hear the state, answer a held question by voice |
| J7 | A reviewer-only program | before a release | no builder; agents audit every window and the new routes and file Door tasks |
| J8 | Teaching the engine | after a step failed twice for the same reason | the lesson becomes a standing requirement of the repository |

## 1. What every journey shares

These rules are the engine as built; the journeys only use them.

- **A step moves on a receipt, not on a claim** (design 2026-10-28 §4). The
  check is a verified log (`program_verifier.verify_text`,
  `holdspeak/services/program_verifier.py:76`); a requirement is Met only on
  its evidence (PG-REQ §4).
- **The Control level decides who decides** (`docs/programs.md`, "The
  control ladder"). Secure asks him for every merge; Normal merges a green
  and reviewed step by rule; YOLO also fixes, re-plans and adds a step by
  rule. A **core question** (goal, shape, egress, money, authority, safety,
  no rule) comes to him at every level.
- **Decided for you, and Overturn.** Each engine decision is a line with its
  rule and, while it can be undone, an **Overturn** verb (#1602).
- **Your word holds the merge at every level** (PG-REQ decision 1, #1665).
- **The handover note** "Program: <title>" is rewritten on every change and is
  the first thing he, a new chat or a new agent reads (#1602).
- **Faces obey UX-CANON**: every verb is the library `Button`; no prose on a
  face (tokens, verbs, counts, names); no modal (a well that unfolds in
  place); no counter of zero; egress waits for his press at the act.

### The new axis: how much the engine asks before it starts

The Control level is about execution: who decides while the steps run. The
owner also asked for a dial on **definition**: "from dropping only a couple
of paragraphs … to … interview rounds and gates to allow me to provide down
to detail level of clarity". The journeys use one dial for it, on the Program
window's toolbar in Drafting:

| **Ask me ▾** | What the planner does before Start |
|---|---|
| **Only the core** | asks only what is a core question (who it is for when someone else sees it, money, egress, a migration); assumes the rest and shows each assumption as an **Assumed** line with **Change** |
| **Each round** (default) | one question at a time, round by round: Architecture, Product, Stack, Verification, Delivery; each question has **Skip**, and each round has **Skip the round** |
| **Everything** | each round, and then each step's details: its gate, its review depth, the kind of each requirement, its agent |

The two dials are independent. A Senior Software Architect may want
**Everything** at definition and **YOLO** at execution: he states the bar to
the detail, then lets the engine run to it. The interview's engine contract
(the round list, a question's shape, how an answer becomes a diff line) is
PG-LANG's; this document fixes the words and the stations he sees.

---

## J1 · Two paragraphs to a shipped change

### Who and when

He, at his desk, Tuesday 14:10, after a meeting where Alice asked for a recap
her team can read. He has 20 minutes before the next meeting and wants the
work to run without him for the rest of the afternoon.

### What he drops in

He opens **New program** and pastes into the goal field (or presses **Run as a
program** on the Note where he wrote it, which exists: `docs/programs.md`
"From a note"):

> After a meeting, the meeting's Note should end with a short recap: the
> decisions, the actions with their owners, and the open questions. It comes
> from the transcript we already keep, runs on the local model, and sends
> nothing out. It is a section of the Note that I can edit, not a new window.
>
> It must be fast: under 20 seconds after Stop on this Mac. It must not make
> up owners: when nobody was named, it says "No owner". Alice asked for this
> for her team's standups, so she sees it before it ships.

### The stations

| # | The engine does | He sees (the words on the face) | He presses |
|---|---|---|---|
| 1 | Planning inference (PG-LANG) reads the two paragraphs, the repository's `CLAUDE.md`, the project's notes, and drafts a program text: four steps, six requirements, the assumptions it made. | The Program window in **Drafting**. Title "Meeting recap in the Note". The program text with each drafted line marked **Drafted**. Toolbar: **Ask me: Each round ▾**, **Control: Normal ▾**, **Agent: Claude Code ▾**. The round strip: **Architecture · Product · Stack · Verification · Delivery**, the first lit. Status bar: "Drafting · 4 steps · 6 requirements · 5 questions". | nothing yet |
| 2 | Round **Architecture**, one question. | The question well above the text: "Where does the recap run?" with three answer Buttons: **In the aftercare, after Stop** · **As its own job** · **Skip**, and the mic. Under it, the line that each answer would change, muted. | **In the aftercare, after Stop** |
| 3 | The answer becomes a diff on the program text. | Step 1's brief gains "in `meeting_aftercare`"; step 1 now owns `holdspeak/services/meeting_aftercare*.py`. The changed lines are lit for 2.4 s. The strip's Architecture dot is green. | (nothing; the next question is there) |
| 4 | Round **Product**. | "Who sees it before it ships?" · **Alice reviews the pull request** · **Only you** · **Skip**. | **Alice reviews the pull request** |
| 5 | The Program gets **For Alice**; step 4 gets the person review gate (`gate_review = person`, #1602). | The status bar's place line: "Project ▸ HoldSpeak · For Alice". Step 4's track shows Alice's portrait at REVIEW. | |
| 6 | Round **Stack**. | "Who builds?" · **Claude Code, Codex reviews** (the default pair) · **pi on qwen, when idle** · **Race on step 2** · **Skip**. | **Skip** (the default stays; an **Assumed** line says so) |
| 7 | Round **Verification**: the planner turns his sentences into requirements and asks for the kind it cannot guess by rule (PG-REQ §4: backticks are a Check, "at 393" is a Shot, the rest is a Review). | "How do we know 'under 20 seconds'?" · **A test with a recorded meeting** (Check) · **You try it on your desk** (Your word) · **Both**. Then: "'It must not make up owners.' How?" · **A test on a meeting with no names** · **The reviewer reads it** · **Both**. | **Both**, then **A test on a meeting with no names** |
| 8 | Round **Delivery**. | "How does it land?" · **Merge each step** · **One pull request at the end** · **Skip**. Then "Mark it in Delivery Workbench?" · **At Done** · **No**. | **Merge each step**, **At Done** |
| 9 | The planner sizes each step (PG-LANG: a step fits its agent's context) and checks that each requirement can be proven here (PG-REQ §4: "no way to prove it" is a core question). | The final program text. Status bar: "Drafting · 4 steps · 8 requirements · 1 assumed". The round strip all green; the question well is gone. | **Start** |
| 10 | Execute (#1602): steps 1 and 3 are Ready; the dispatcher hands them; worktrees, briefs with "What must be true" (#1665). | The board: four rows, each with its station dots and its Met cell ("3 to meet"). | nothing |
| 11 | Verify: CHECK runs the check and each Check requirement on the step's commit; REVIEW asks Codex each Review requirement by its number (`REQ R3: MET · …`). | Requirements board: R3 **Met** · Open log; R5 **Unmet** · "the recap names 'Bob' as an owner; the transcript does not". | nothing (Normal: round 2 by rule) |
| 12 | Prove: step 4's pull request waits for Alice's approval on GitHub; the Your word requirement waits for him. | Your turn: "Ask Alice to review PR #1702" · **Send…**; "Step 4 · R8 · You tried it on your desk?" · **Met** · **Unmet**. | **Send…**, then (next morning) **Met** |
| 13 | The end check (#1665): the Program's own requirements on the base branch head. Then Done. One milestone in Delivery Workbench (see "The morning after"). | "Done · 14 of 14 met · 4 PRs · 2 h 10". | nothing |

A sample of the final program text, for illustration only (the grammar is
PG-LANG's):

```
Program: Meeting recap in the Note · For Alice · Control: Normal
Every step: R1 Review "The change does only what its brief says."
            R2 Review "Each new behaviour has a test."
1. The recap in the aftercare · Claude Code · owns holdspeak/services/meeting_aftercare*.py
   R3 Check `uv run pytest -q tests/integration/test_recap_latency.py` is green
2. No made-up owners · Claude Code · after 1
   R4 Check `uv run pytest -q tests/unit/test_recap_owners.py` is green
   R5 Review "The recap never names an owner the transcript does not name."
3. The recap section in the Note · Claude Code · owns web/src/desk/pullouts/note*
   R6 Shot "The Note window at 393 has no clipped text"
4. Alice's review · reviewer: Alice · after 2, 3
   R8 Your word "I tried it on my desk after a real meeting."
The program: R7 Check `scripts/quick_check.sh` is green on main
Assumed: Codex reviews Claude Code (Stack, skipped)
```

### Verification and proof at each gate

| Gate | Proof | Who reads it |
|---|---|---|
| Definition (before Start) | each requirement has a way to be proven in this repository; each step fits its agent's context; no core question is open | the planner by rule; an unprovable requirement is a core question |
| CHECK | the verified check log, then each Check log with `program-check: exit 0` (#1665), each Shot's image | the engine (the verifier) |
| REVIEW | Codex's `REQ R n` lines on the reviewed commit | the engine parses; an UNMET is a REQUIRED finding |
| Alice | her approval on GitHub, read by follow-through | the engine |
| MERGE | his **Met** on R8 | him |
| Done | the end check on the base branch head (`hs-program-<id>-end`) | the engine |

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| Definition with **Only the core** | one question (Product: Alice) | the same | the same |
| Definition with **Everything** | 5 rounds, then each step's gate, review depth and agent: about 14 questions | the same | the same |
| Each merge | he presses **Merge** | by rule on green, reviewed and met | by rule |
| R5 unmet after two rounds | him: **Send back** / **Waive** | the step parks, the rest go on, one row to him | one smaller brief, then park |

### The morning after

- **The Note** "Program: Meeting recap in the Note": "Done · 14 of 14 met · 4
  PRs · 2 h 10"; Decided for you lists the two merges by rule and the one
  **Assumed** line.
- **Needs you**: nothing left, or only R8 if he did not try it yet.
- **Delivery Workbench**: one milestone, written only at Done (the owner's
  "only at major points"): "Meeting recap in the Note · 4 PRs (#1699 to
  #1702) · 14 of 14 met". In a repository with a Delivery Workbench roadmap
  (`pm/roadmap/`, `.githooks/dw`) the engine adds it as a last tiny step that
  goes through the same check and merge. In HoldSpeak itself `pm/roadmap/` is
  history (CLAUDE.md), so the milestone is a `pm/STATUS.md` line instead.
- **The 1:1 brief** with Alice lists step 4 under "To show them" (#1602).

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| He pastes a goal that is three goals | the planner proposes three Programs in the diff ("Split into 3 programs") with **Apply** / **Skip**; it never splits on its own |
| An answer contradicts the paragraphs ("Only you" after "Alice sees it") | a core question (the goal): "You wrote that Alice sees it first. Keep Alice?" · **Keep Alice** · **Only you** |
| A Check requirement names a test that does not exist yet | allowed: the step's brief says it writes that test; at CHECK a missing file is a red check round, not Met |
| He leaves the window mid-interview | the Program stays in Drafting with "3 questions left" on its Programs row; the next open resumes at the same question |
| A step is too big for its agent | the planner splits it before Start (PG-LANG); he sees two steps where he had one, as one diff |

### Delight moments

- Each answer lights exactly the lines it changed, once, for 2.4 s (the
  breath, never a loop).
- The round strip fills green, one dot per round; when the last one fills,
  the **Start** Button becomes primary.
- "Done · 14 of 14 met" in the Done word (each step's copy of an every-step requirement counts once, PG-REQ §7); the milestone is one line, not a
  ceremony.

---

## J2 · The dreaming program

### Who and when

Weeknights, 23:30 to 07:00. The home box (qwen3.8-27b over Tailscale, the
`HOME_ENGINE_PROFILE` of `holdspeak/program_templates.py:25`) is idle. The
owner: "our context maxes out at 64k tokens", so every step must be small.

### What he drops in

Two kinds of input, and both are short.

During the day, one line at a time, with **Add to tonight** on a Door task, a
Later finding, a note line or a spoken sentence on a call:

> The Calls window's status bar says "Line starting" for 40 s after the Line is up.
>
> `ux_canon_scan.py` finds 9 raw buttons in the Terminals window.
>
> The Engines rows at 393 clip the readiness word.

And once, when he sets it up:

> Dream on HoldSpeak each weeknight. Small, safe things only: words, faces,
> tests, docs. Nothing that changes the database. pi builds on the home box;
> Claude Code reviews. If you run out of my list, take from the copy guard and
> the sweep's known reds.

### The stations

| # | Time | The engine does | He sees | He presses |
|---|---|---|---|---|
| 1 | set-up, once | A new template **Dreaming** (New: Overnight's shape plus a backlog, a night window, a planner and named sources). The automation **Every weekday at 23:30** (#1626) runs it. | The automation window: Do **Run a program** · Template **Dreaming** · Level **YOLO** · Until **07:00** · Planner **Claude Haiku ▾** (or **qwen on karol**) · Spend limit **$1 a night** · Sources **Tonight list · Copy guard · Known reds**. | **Turn on** |
| 2 | 23:30 | The automation starts the Program "Dreaming · Thu 31 Oct". The planner (PG-LANG) reads the backlog and cuts each line into steps that fit 64k: the brief, the owned files and the room for the check log tail. A line that cannot fit in two cuts is parked "Too big for one night" and goes back to the Door as a task for him. | The board fills: 9 steps, each with a budget word "38k of 64k". Today's line later: "Last night: …". | nothing |
| 3 | 23:31 | The rule "nothing that changes the database" becomes an Every step requirement: Check "`git diff --name-only` names no `holdspeak/db/` file" (PG-REQ, #1665). Any step that would touch a migration is a core question (safety, #1602). | R1 in the Requirements board, "9 steps". | |
| 4 | 23:32 to 06:30 | pi on qwen builds each step only **When idle** (`program_runner.engine_idle`, `holdspeak/services/program_runner.py:196`); Claude Code reviews; YOLO merges a green, reviewed, met step (#1602). A red step gets three rounds, then one smaller brief, then parks. | The Program row: "Running · 5 of 9 merged". The step that waits for the engine: "Ready · waiting for qwen". | nothing |
| 5 | when the list runs dry | The planner takes from the named sources only: the copy guard's report, the sweep's `KNOWN_REDS`. At YOLO a step the plan did not have is added and written under Decided for you with **Overturn** (#1602 rule). | "Added for you: Step 10 · The Terminals buttons are library Buttons · from the copy guard". | |
| 6 | 06:30 | The night window closes: no new step is handed after 06:30; a step that still works at 07:00 writes its checkpoint ref (#1649) and parks "Morning: continue from here". | "Parked · morning" on that row. | |
| 7 | 07:00 | The digest is written into the handover note (New section **Last night**), and one phone message goes out when Reach says Message for "Program is done" (`docs/phone.md:108`). | The Note, the phone, Today. | |

### Verification and proof at each gate

- **Sizing gate** (before a step is handed): the step's budget word is under
  the engine's context ceiling. HoldSpeak reads that ceiling from the engine
  today (`setup_runtime.py:199` reads `n_ctx`, `context_length` or
  `max_model_len`; `CONTEXT_WINDOW_PRESETS` has 65536 at
  `holdspeak/setup_runtime.py:49`). The budget per step is PG-LANG's.
- **CHECK**: the repository's check, verified (#1602); R1 (no database file)
  on each step's commit.
- **REVIEW**: Claude Code with the two template requirements ("The change does
  only what its brief says.", "Each new behaviour has a test.",
  `holdspeak/program_templates.py:35`).
- **MERGE**: by rule at YOLO, except a step with a Your word requirement,
  which waits for his **Met** in the morning (#1665).
- **Money**: a hosted planner (Claude Haiku) is paid; the Program's spend limit
  is set, and the planner stops planning at the limit (money is a core
  question beyond the limit, `holdspeak/services/program_rules.py:100`).

### Hands-off and hands-on

Dreaming is hands-off by design. The dial still matters:

| | Secure | Normal | YOLO (the default) |
|---|---|---|---|
| merge | each merge waits for him in the morning | by rule | by rule |
| a step the backlog did not have (from a source) | him | him | added, with Overturn |
| a red step after its rounds | him | parked, the rest go on | one smaller brief, then parked |
| a migration, egress, a deleted test | him | him | him |

Secure dreaming is still useful: the night builds and checks everything, and
the morning is a list of green, reviewed pull requests to press **Merge** on.

### The morning after

The handover note "Program: Dreaming · Thu 31 Oct", top section:

```
## Last night
23:30–06:52 · 11 steps · 8 merged · 2 parked · 1 waits on you
Merged: #1710 Line starting word · #1711 Terminals buttons (3 steps) · #1714 Engines 393 · …
Parked: Step 9 · "Too big for one night" → back on the Door
Waits on you: Step 7 · core question: "the fix needs a new column"
Spent: $0.38 of $1 (the planner) · qwen 5 h 10 · Claude Code 41 min
```

- **Needs you**: one row, "Dreaming · Step 7 asks you: the fix needs a new
  column" · **Go on** · **Park** (a core question, #1602).
- **Today**: "Last night: 8 merged, 1 waits on you" (the Programs line on
  Today exists, #1618; the "Last night" words are New).
- **The phone**: one message with the same first line.
- **Delivery Workbench**: nothing. A night is not a major point.

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| He uses the home box at 01:00 (a dictation) | his use takes the engine first; the step waits "Ready · waiting for qwen" and resumes on the next pass (#1602) |
| pi runs out of context in the middle of a step | unknown how pi behaves at its ceiling (see §"could not establish"); the step's check is red or the turn ends without a commit; three rounds, then a smaller brief (YOLO) |
| The planner proposes from a source he did not name | refused by rule: the sources are a list on the Program; a proposal outside it is not planned |
| The planner's spend limit is reached at 02:00 | planning stops; steps already planned still run on qwen; the digest says "Planner stopped at $1" |
| Two dream steps touch the same file | the second waits for the first to merge ("after 3", by the owned files rule of the brief, `program_brief.theirs`) |
| The main desk goes red after a dream merge | the main watcher traces it (CLAUDE.md fast cycle); the dream's next step is not handed until main is green again (New: a "main is red" hold) |

### Delight moments

- The board at 07:00 is a column of green MERGE dots.
- Each step row carries its budget word ("38k of 64k"), so "small" is visible.
- The digest's first line is the whole night in one breath.
- **Add to tonight** is one press from anywhere; the list is the dream.

---

## J3 · Shaping a running program by voice

### Who and when

He, at his desk, Wednesday 16:00. "The hub stops stalling" runs at Normal:
steps 1 and 2 merged, step 4 working, steps 5 and 6 planned. He holds the mic
on the Program window and speaks.

### What he drops in

Three sentences, spoken:

> Every step must keep the hub loop under 100 milliseconds. Put a step before
> the fan-out that adds the loop watch. And the fan-out runs on qwen tonight,
> not Claude.

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | Dictation into the **Shape** field (the mic on the Program window's toolbar; the field and the inference are PG-LANG's). | The three sentences as text in the field, with **Shape** and **Clear**. | **Shape** |
| 2 | Shaping inference maps each sentence to one change of the program text, and checks each change against the frozen table (PG-REQ §8). | A diff well under the toolbar: three lines, each with its Button pair. `+ R9 · Every step · Check · uv run pytest -q tests/unit/test_hub_loop_budget.py is green · 4 steps` / `+ 6 · The loop watch · Planned · before the fan-out (now 7)` / `~ 7 · The fan-out · Agent: Claude Code → pi on qwen3.8-27b · When idle`. | |
| 3 | R9 on a step that is merged is not added there ("It is merged"); on step 4, which is working, it is added and judged at CHECK (the bar can go up while a step runs, #1665). | Under the first line, muted: "Steps 1, 2 merged: not added · step 4: judged at CHECK". | **Apply all** |
| 4 | One change set: `program.require` (each_step), `program.plan` with `before`, `program.step_update` (all exist, #1665), one checkpoint "Shaped by you: 3 changes", one `program_changed` frame. | The board: a new row 6, the fan-out renumbered 7 with "pi · qwen3.8-27b" and "When idle"; the Requirements board shows R9 with four small dots. The changed rows breathe once. | |
| 5 | The change set stays undoable while each part can still be undone (a planned step, a requirement not yet judged). | Decided for you is his, so the line is in the Ledger: "16:02 · Shaped by you · 3 changes" · **Undo**. | (later) **Undo** if he wants |

### Verification and proof at each gate

- Before Apply: each diff line is checked against the frozen table; a frozen
  change is shown and refused with its reason ("The agent has read it"), never
  silently dropped.
- After Apply: R9 is a Check, so it is judged on each step's commit at CHECK
  with its log (#1665); step 7 on qwen runs only when idle.

### Hands-off and hands-on

| Who shapes | Secure | Normal | YOLO |
|---|---|---|---|
| He (voice or typed) | the diff, then his **Apply** | the same | the same |
| An orchestrating agent (Claude Code at his keyboard, Astra) | each line is a Your turn row **Apply** / **Skip** (`step_change`, #1665) | the same | applied by rule, written under Decided for you with **Overturn** while the step is planned |

His own shaped change is never applied without the diff: speech is
inference, and inference is shown before it acts.

### The morning after

The handover note's Steps list has seven steps; the Ledger keeps "Shaped by
you: 3 changes" with the sentences he spoke. If the fan-out ran overnight on
qwen, the note says "Step 7 · Merged #1720 · pi · qwen3.8-27b · 1 h 40".

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| Dictation mishears "qwen" as "Gwen" | the diff names the engine from the library's list, so a wrong match reads wrong at once; **Skip** that line |
| A sentence maps to no change | the diff says "Not understood: '…'" as a muted line; nothing applies |
| A sentence would lower the bar ("drop the review on step 5") | refused: "The bar does not come down while it runs"; the diff offers **Waive** on the requirement instead, with a line |
| He says "insert before step 4" and step 4 started | refused: "Step 4 started. Add the step after it." (#1665) |
| Two people shape at once (he and an agent) | one change set at a time under the Program's lock; the second diff is drawn again on the new text |

### Delight moments

- He speaks; three lines appear; one press; the board changes in place.
- The renumbered step says "Step 6 is now step 7" once in its ledger; nothing
  else moves.

---

## J4 · From the desk, for a person

### Who and when

He, after his 1:1 with Alice, Thursday 11:30. The meeting made an action in
the project HoldSpeak: "Alice: the 1:1 brief exports as Markdown".

### What he drops in

Nothing typed. One press on the action's row: **Run as a program**.

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | A Program from the **From the desk** template (#1602) with one step from this one action (New: the verb on an action row; today From the desk takes every open action of a project). The action's person (Alice) becomes **For Alice**. The template's step requirement: "The change does what its action asks: the 1:1 brief exports as Markdown" (`holdspeak/program_templates.py:39`). | The Program window, Drafting, one step. Ask me is **Only the core**: one question, "Does Alice review the pull request?" · **Alice reviews** · **Only you**. | **Alice reviews** |
| 2 | Step 1 gets `gate_review = person` with Alice; her GitHub login comes from her `github` alias in People (#1602). A From the desk program has no review gate by default; a person gate is one. | Alice's portrait at REVIEW on the track. | **Start** |
| 3 | Build, check, PR (#1602). | "PR open #1731". | |
| 4 | The person gate: a prepared send through the channel; the merge waits for her approval on GitHub. | Needs you: "Ask Alice to review PR #1731" · **Send…**; the send preview shows where it goes (egress at the act). | **Send** |
| 5 | Follow-through reads her approval; the merge by the level; the action closes with the PR as evidence (#1602). | "Merged #1731"; the action is done. | |

### Verification and proof at each gate

CHECK as always; REVIEW is Alice's GitHub approval, read, not claimed; the
action's own requirement is answered by the reviewer of record. Because Alice
is a person, her review answers no `REQ` line; the requirement "does what its
action asks" is his word at MERGE when no agent reviewer runs (New: a person
gate plants Review requirements as Your word).

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| the send to Alice | his press (egress) | his press | his press |
| the merge after her approval | his press | by rule | by rule |

### The morning after

- Alice's room: the Program under her commitments, "Merged #1731".
- The next 1:1 brief with Alice: "To show them: the 1:1 brief exports as
  Markdown (#1731)" (#1602).
- The project's update draft: one line in its Programs paragraph (#1602).

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| Alice has no `github` alias in People | the person gate cannot read her approval: a core question, "Alice has no GitHub name. Add it in People, or review it yourself" · **Open Alice** · **Review it yourself** |
| Alice asks for changes on GitHub | follow-through reads "changes requested"; her comments go to the builder as a round (New: person review comments as findings) |
| The action was already done by hand | the planner sees a merged PR that names the action and proposes "Close the action" instead of a Program |

### Delight moments

- One press from a 1:1 action to a running Program for the person who asked.
- "To show them" in the next 1:1 brief, without him writing it.

---

## J5 · The race

### Who and when

He, Friday 09:00, with a brief he does not want to wait on twice.

### What he drops in

> Notes search finds words inside Mermaid fences. Today a word in a diagram is
> not found. Keep the search under 50 ms for 2,000 notes.

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | The **Race** template (#1602): one brief, two contenders (Claude Code and Codex) in sibling worktrees. The template has no review gate; "first green and reviewed" needs one, so the planner asks. | One question: "Review each contender?" · **Codex reviews Claude Code, Claude Code reviews Codex** · **No review**. | the first |
| 2 | The review turns on; the template's Review requirement plants ("The change does only what its brief says.", #1665). "Under 50 ms" becomes a Check requirement the planner names from the repository's tests, or a core question if none can prove it. | The board: step 1 with two contender rows under it (the race species, #1618). | **Start** |
| 3 | Both build. The first branch that is green, reviewed and met wins; the other is parked "lost the race to Codex" (#1602). Its last checkpoint ref stays (#1649). | The winner's row lit; the loser's row muted with **Start from here**. Decided for you: "Codex won the race · 34 min · rule: first green and reviewed" with no Overturn once merged. | |

### Verification and proof

Each contender passes the same CHECK, the same requirements and an
independent review by the other harness. A contender that is green first but
fails review does not win; the race goes on.

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| the winner | he picks (both rows show **Pick**) | the first by rule | the first by rule |
| the merge | his press | by rule | by rule |

### The morning after

The note says who won and in how long (design 2026-10-28 §6, as built). The
loser's branch is parked, not deleted; its ref is one press away.

### What could go wrong

| What | The engine |
|---|---|
| Both are red after their rounds | the step fails as one step (a core question at Secure, park at Normal) with both logs |
| One contender hits its usage limit | the handoff rule (#1604) applies to that contender only; the race goes on |
| Both pass within the same tick | the one whose review passed first wins; the note says "by 40 s" |

### Delight moments

- Two rows racing on one board; the winner's MERGE dot goes green while the
  loser's track stops where it was.
- "Won by 6 min" in the Done word.

---

## J6 · Start and steer from the Phone and the Line

### Who and when

He, Thursday 23:10, driving home, calls his Line (#1606 to #1609). Friday
06:40 in the kitchen, he calls again.

### What he says

> Start the overnight program.

and in the morning:

> How is the overnight program doing?
>
> Step 7: go on, with a new column. Do not change the old rows.

### The stations

| # | When | The engine does | He hears or sees | He says or presses |
|---|---|---|---|---|
| 1 | 23:10 | The call turn finds the program by its words and holds `program.start` for his spoken yes (#1663). | "I want to start the program Overnight on the home box. Say yes or no." | "Yes." |
| 2 | 23:10 | Started; the call's transcript becomes a Note (as built). | "Started. Nine steps. The first one runs when the home box is idle." | hangs up |
| 3 | 03:12 | Step 7 hits a core question (a migration); Reach at YOLO with **May call**: call at once (`docs/phone.md:106`), but quiet hours hold an ordinary message; only an urgent call rings. A migration is not urgent: a message waits until quiet hours end (#1619). | nothing at 03:12 | |
| 4 | 06:30 | The held message goes out when quiet hours end. | On the phone: "Overnight · Step 7 asks you: the fix needs a new column on meetings" with **Go on** · **Park** (New: reply verbs on a program message). | (does not press; calls instead) |
| 5 | 06:40 | "How is …" is `program.get` by name in a sentence (#1663). | "Running. Six of nine steps merged. One waits on you: step 7 needs a new column on meetings. Last decision: merged step 6 at 05:12." | "Step 7: go on, with a new column. Do not change the old rows." |
| 6 | 06:40 | New: an answer to a held item is `program.decide` behind a spoken yes, the same hold as `program.start`. His words become the line typed to the agent. | "I want to answer step 7: go on, with your words 'a new column; do not change the old rows'. Say yes or no." | "Yes." |
| 7 | 06:41 | The core question is answered; the line goes to step 7's agent at its next turn boundary ("The owner on step 7: …"); the transcript Note links to the step. | "Done. Step 7 goes on." | |

### Verification and proof

- Authority: today a call may not "confirm a decision for you"
  (`docs/calls.md:44`, the table's last column). Station 6 needs the owner's ruling: a
  **spoken yes on his own line, after the passphrase**, counts as his press
  for `program.decide` on a core question. Without that ruling, station 6
  says "I put your answer in Needs you. Press Go on there." and writes a
  prepared answer with his line (a fallback that needs no ruling).
- The call record is evidence of the turn; the Program's ledger is the
  receipt of the answer.

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| a core question at night | a message | a message, then a call after 10 min when May call | a call at once when May call (quiet hours still hold all but urgent) |
| start by voice | spoken yes | spoken yes | spoken yes |
| answer by voice | spoken yes (with the ruling) | the same | the same |

### The morning after

The transcript Note of each call, linked from the Program's ledger: "06:41 ·
Answered by you on a call: go on, a new column". Needs you has no row left for
step 7.

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| Two programs match "overnight" | it names both and asks which, by title; it starts nothing until one is named (#1663 says it asks nothing when none match) |
| He says "yes" to the wrong thing | the hold repeats the program's full title and the step; "no" or silence starts nothing |
| The line is noisy and the answer is half heard | the read-back is verbatim; he says "no" and says it again |
| He answers by phone message and by call | the first answer closes the item; the second hears "Step 7 is answered already" |

### Delight moments

- One sentence in the car, and the night runs.
- The morning call answers in two sentences, with the one thing that is his.
- His own words, read back, become the line the agent gets.

---

## J7 · A reviewer-only program

### Who and when

He, the day before he shows the desk to his reports. No builder; he wants a
list.

### What he drops in

> Audit every window at 393 and 1440 against the UX canon, and read every route
> added this month for a lock on the event loop and for a missing residual-set
> entry. File what you find. Do not fix anything.

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | A new template **Audit** (New): each step is an audit, not a build. Its agent works in a scratch copy, as the reviewer does (AG12); `gate_merge = none` (a step with no PR, which exists, `docs/programs.md` "Gate"); no commit is expected. | The planner's steps: one per app group of `web/src/desk/applications.ts` (the sweep's manifest, `tests/e2e/test_desk_sweep.py:7`), plus "Routes added since 1 Oct". | **Start** |
| 2 | Each audit step runs the desk sweep's shots for its windows and reads them with the canon; the routes step reads the diff since 1 October. Its report is a list of findings, each MUST, SHOULD or NOTE, with evidence: a shot, a `file:line`. | The board's stations for an audit: BRIEF · WORK · REVIEW (the auditor's own findings) · FILE. | |
| 3 | New: each finding is filed as a Door task through `door.add_item` (exists, the Door's MCP), with its evidence and the project, grouped by window. | The Requirements board is replaced by **Findings**: "14 findings · 3 MUST". | (Secure: per finding **File** / **Skip**) |
| 4 | Done when every step reported. Proposal: "Make a fix program from the 3 MUST" · **Make** · **Skip** (a proposed Program, never started by rule). | "Done · 31 windows · 14 findings". | **Make** |

### Verification and proof

An audit step is done on a receipt, too: its report names each window it
read and the shot it read it from. A window with no shot is listed as "Not
read" in the report, never as clean.

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| file a finding as a Door task | his press per finding | MUST and SHOULD filed by rule; NOTE kept in the note | all filed by rule |
| make a fix program | his press | his press | proposed; started only by his press (a new Program is the goal, a core question) |

### The morning after

The Door has 14 tasks grouped by window, each with its shot; the note says
"Audit · 31 windows · 14 findings · 3 MUST"; the fix program, if he made it,
is Drafting with three steps, one per MUST.

### What could go wrong

| What | The engine |
|---|---|
| An auditor starts to edit files | the scratch copy is thrown away; any commit on an audit step is a core question (the shape of the work) |
| The same finding in 12 windows | one finding with 12 windows, not 12 tasks |
| The sweep is red for a reason unrelated to the canon | the step files it as "The sweep is red: <case>" once, and goes on |

### Delight moments

- A list, not a lecture: each task one line, with its picture.
- "Make a fix program" turns a list into work in one press.

---

## J8 · Teaching the engine

### Who and when

Thursday, Program "The words wave": step 3 failed its check twice because the
new worktree had no packages (the user doc warns of it: "A new worktree has no
installed packages", `docs/programs.md` "The gate and its log"). Codex also
wrote the same SHOULD finding on steps 2, 4 and 5: "a raw `<button>`".

### What he drops in

Nothing at first. The engine sees the lesson; he decides where it lives.

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | New: a lesson rule. When a step goes green after a round whose red named the same cause on two steps, or when the reviewer writes the same finding on three steps, the engine writes a **Lesson** with the cause, by rule, not by a model. | Your turn: "Lesson · the check needs packages: 2 steps red for it" · **Keep for this program** · **Keep for HoldSpeak** · **Skip**. And "Lesson · raw `<button>` on 3 steps" with the same verbs. | **Keep for HoldSpeak** on the first |
| 2 | **Keep for this program**: an Every step requirement (#1665). **Keep for HoldSpeak** (the repository): New, a tiny step of this Program that edits `.holdspeak/program.json` (the `check` gets `uv sync --extra dev && npm ci &&` before it; or a `requirements` item), checked, reviewed and merged as any step. The repository's defaults are read by every new Program (#1665). | A new step 7 "Keep the lesson: the check installs packages" with "from a lesson". | (the second lesson) **Keep for this program** |
| 3 | The second lesson becomes R6 · Every step · Check · `uv run python scripts/ux_canon_scan.py` (the canon scan exists, `scripts/ux_canon_scan.py`). | R6 with its six small dots. | |

### Verification and proof

A lesson kept for the repository is a pull request: the next Program reads
the change only after it merged, so a lesson cannot change the bar without a
check and a review. A lesson is never kept by rule at any level: it changes
the bar for every later Program, so it is his.

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| propose a lesson | the engine | the engine | the engine |
| keep it for this program | his press | his press | added by rule as an agent-proposed requirement (#1665 rule `requirement_proposed`), with Overturn |
| keep it for the repository or a template | his press | his press | his press |

### The morning after

`.holdspeak/program.json` has the new check line; tomorrow's dream (J2) runs
its steps with it. The note's Decided for you says "Lesson kept for HoldSpeak:
the check installs packages (#1740)".

### What could go wrong

| What | The engine |
|---|---|
| The lesson is wrong (the red was a flake) | **Skip**; a skipped lesson with the same cause is not proposed again in this Program |
| He wants it for a template, not the repository | **Keep for template** needs user templates, which do not exist (templates are Python, `holdspeak/program_templates.py:41`); until then the repository file is the place (New: user templates, not recommended now) |

### Delight moments

- The second time a mistake happens, the engine names it; the third time, it
  cannot happen.

---

## 2. What the journeys demand

Each face, engine capability, route and library gadget the journeys use. **Exists**
names the PR or the file; **In PG-LANG** is the sibling lane's
(`PROGRAM-LANGUAGE-2026-10-31.md`); **New** is not built and not in PG-LANG's
brief.

### Faces

| # | Item | Journeys | State |
|---|---|---|---|
| F1 | Programs window, Program window, the board, the Your turn well, Decided for you, the handover note | all | Exists #1602 |
| F2 | Requirements board, Add requirement row, the Met column, Find, the step fold, Insert before, Move | J1 J2 J3 J8 | Exists #1665 |
| F3 | Race contender rows, the race shot | J5 | Exists #1602, #1618 |
| F4 | Person review row "Ask Alice to review PR" with Send… | J1 J4 | Exists #1602 |
| F5 | **Run as a program** on a Note | J1 | Exists #1602 |
| F6 | The program text view (the Program as text, in the window and as a pullout) | J1 J3 | In PG-LANG |
| F7 | The **Shape** field with mic, and the shown diff with Apply / Skip per line and Apply all | J1 J3 | In PG-LANG |
| F8 | The interview question well (one question, answer Buttons, mic, Skip, the lines it would change) | J1 J4 J5 | New (the face; the engine contract is In PG-LANG) |
| F9 | The round strip (Architecture · Product · Stack · Verification · Delivery) on `FilterTokens` | J1 | New |
| F10 | **Ask me ▾** (Only the core · Each round · Everything) | J1 J4 | New |
| F11 | **Assumed** lines with Change | J1 | New |
| F12 | The step budget word ("38k of 64k") on a board row | J2 | New (the number is In PG-LANG) |
| F13 | **Add to tonight** on a Door task, a finding, a note line | J2 | New |
| F14 | The **Last night** digest section in the handover note | J2 J6 | New |
| F15 | "Last night: …" words on Today | J2 | New (the Programs line on Today exists, #1618) |
| F16 | Undo of a shaped change set, in the Ledger | J3 | New |
| F17 | **Run as a program** on a project action row | J4 | New |
| F18 | The audit board: stations BRIEF · WORK · REVIEW · FILE, the Findings board | J7 | New |
| F19 | The **Lesson** Your turn row (Keep for this program · Keep for HoldSpeak · Skip) | J8 | New |
| F20 | Reply verbs on a program message in the phone app (Go on · Park) | J6 | New (messages and replies exist, #1605) |
| F21 | The automation's Run a program fields (template, level, agent, When) | J2 | Exists #1626 |
| F22 | The automation's Until, Planner, Sources fields | J2 | New |

### Engine capabilities

| # | Item | Journeys | State |
|---|---|---|---|
| E1 | The tick, the gate, review, PR, merge, the control ladder, core questions | all | Exists #1602 |
| E2 | Requirements of four kinds, the end check, Your word holds the merge | all | Exists #1665 |
| E3 | Adjust: change, insert before, move, amend, the frozen table | J3 | Exists #1665 |
| E4 | pi on an engine, When idle | J2 J3 | Exists #1602 (`program_runner.py:196`) |
| E5 | Handoff at a usage limit | J5 | Exists #1604 |
| E6 | Checkpoint refs, Start from here | J2 J5 | Exists #1649 |
| E7 | Proposed decisions from a Program | J1 | Exists #1644 |
| E8 | An automation runs a program | J2 | Exists #1626 |
| E9 | Start a program on a call; its state in a sentence | J6 | Exists #1663 |
| E10 | Reach: a message or a call by level, quiet hours | J2 J6 | Exists #1605, #1619 |
| E11 | Planning inference: two paragraphs to a program text | J1 J2 | In PG-LANG |
| E12 | Shaping inference: speech or text to a diff of the program text | J3 | In PG-LANG |
| E13 | Interview rounds as an engine contract (rounds, a question, an answer to a diff line) | J1 J4 J5 | In PG-LANG |
| E14 | Step sizing to the agent's context (64k) | J1 J2 | In PG-LANG (the engine's ceiling is read today, `setup_runtime.py:199`) |
| E15 | The planner on a chosen engine (Claude Haiku, the LAN model) with the Program's spend limit | J2 | In PG-LANG (the spend limit rule exists, `program_rules.py:100`) |
| E16 | The **Dreaming** template: a backlog, a night window, named sources | J2 | New |
| E17 | A long-lived program that plans new steps from its backlog each night | J2 | New |
| E18 | The night window: no hand after 06:30, park at 07:00 with a ref | J2 | New |
| E19 | A "main is red" hold: no new step is handed while the base branch is red | J2 | New |
| E20 | `program.decide` behind a spoken yes on a call | J6 | New (needs the owner's ruling) |
| E21 | A phone reply that answers a Your turn item | J6 | New |
| E22 | A step from one action (not every open action of the project) | J4 | New |
| E23 | A person gate plants Review requirements as Your word | J4 | New |
| E24 | A person reviewer's "changes requested" as findings | J4 | New |
| E25 | The **Audit** template: a step with no builder, in a scratch copy, a report of findings | J7 | New |
| E26 | Each audit finding filed as a Door task with its evidence, merged across windows | J7 | New (`door.add_item` exists) |
| E27 | A proposed fix program from findings | J7 | New |
| E28 | The lesson rule (same cause on two steps, same finding on three) | J8 | New |
| E29 | Keep for the repository: a tiny step that edits `.holdspeak/program.json` | J8 | New (reading the file exists, #1665) |
| E30 | User templates (Keep for a template) | J8 | New, not recommended now |
| E31 | One Delivery Workbench milestone at Done, as a last tiny step | J1 | New (the hub reads roadmaps, `holdspeak/web/routes/roadmaps.py:287`) |
| E32 | Split one pasted goal into several Programs, proposed | J1 | In PG-LANG |

### Routes and tools

| # | Item | Journeys | State |
|---|---|---|---|
| R1 | `/api/programs` (15 routes), the `program` MCP family | all | Exists #1602 |
| R2 | Requirements, step change, amend routes; `program.require`, `program.step_update`, `program.amend` | J1 J3 J8 | Exists #1665 |
| R3 | `program.start` and `program.get` by name | J6 | Exists #1663 |
| R4 | Shape and interview routes and tools (preview a diff, apply, answer) | J1 J3 | In PG-LANG |
| R5 | `POST /api/programs/{id}/backlog` and `program.backlog_add` (Add to tonight) | J2 | New |
| R6 | `program.decide` in the CALL palette, held for the spoken yes | J6 | New |
| R7 | The lesson decide kinds (`lesson`: keep_program, keep_repository, skip) | J8 | New |

### Library gadgets

| # | Item | State |
|---|---|---|
| G1 | `Toolbar`, `StatusBar`, `ListView`, `FoldGadget`, `DotWord`, `StateChip`, `Token`, `FilterTokens`, `StringGadget` with `MicButton`, `CycleGadget`, `CheckGadget`, `WorkMenu`, `SurfaceCode`, library `Button` | Exists (the kit; UX-CANON §B) |
| G2 | A diff line species (`+`, `~`, `-`, a frozen line with its reason) | In PG-LANG (as part of F7) |
| G3 | The question well species (a question, two to four answer Buttons, Skip, a preview of the lines) | New |

**Count: 34 items are New** (14 faces: F8 to F20 and F22; 16 engine items:
E16 to E31; 3 routes: R5 to R7; 1 gadget: G3). 10 are In PG-LANG (F6, F7,
E11 to E15, E32, R4, G2). The rest exist.

The five biggest New items:

1. **The interview face** (F8 to F11, G3): the question well, the round strip,
   Ask me ▾ and the Assumed lines. It is the definition phase he asked for;
   the engine contract is PG-LANG's, the face is not.
2. **Dreaming** (E16 to E19, F12 to F14, F22, R5): a long-lived program with a
   backlog, a night window, named sources and a main-is-red hold.
3. **Answers by voice and by phone** (E20, E21, F20, R6): needs the owner's
   ruling that a spoken yes on his own line is his press.
4. **Audit programs** (E25 to E27, F18): a step kind with no builder and a
   findings board that files Door tasks.
5. **Lessons** (E28, E29, F19, R7): the rule that sees a repeated cause, and
   keeping it in the repository through a reviewed step.

## 3. The interview round: two directions (canvas)

- **A · One question, in place (recommended).** The question well sits under
  the toolbar of the Program window in Drafting, above the program text. One
  question at a time: the question in 14/600 ink, two to four answer Buttons,
  the mic, **Skip**; under it, muted, the lines of the text that the answer
  changes. The round strip (`FilterTokens`, one dot per round) is at the
  head of the question well; a press on a round token shows all its questions as rows (B's
  form) for the one who wants to answer in any order.
- **B · The round sheet.** Each round is a fold of question rows, all open
  at once, each row with its answer `CycleGadget` and mic; one **Apply the
  round** at the fold's foot writes all its answers as one diff. Fastest for
  an architect who knows every answer; it shows twelve questions where A
  shows one, and an answer's effect is seen only at Apply.

**Why A.** He asked for "smoothly" and "down to detail level": A keeps one
question and its consequence on the screen, so each answer is a visible
change to the plan, and voice works because there is one thing to answer.
B is drawn as A's open round (a press on a round token), so the architect who
wants the sheet gets it without a second face.

## 4. Journeys at 393 and on a call

**At 393.** The Program window is the screen. The question well is the top
card: the question on two lines, the answer Buttons stacked, each a plated 44
px Button; Skip at the right of the round strip. The program text is under
the card and scrolls; the diff of the last answer is lit there. The Shape
field is the bottom bar with its mic (thumb reach), and the diff opens as a
full-width well with one line per change and Apply all at its foot. The
Dreaming digest is the top of the note at 393: its first line is one line.
The Lesson and the Assumed rows take two lines with their verbs on the
second. No new 393 face is needed beyond these; the board is the station
word as now (`docs/programs.md`, "On a phone").

**On a call.** The call can: start a program by its words (#1663), say its
state in two sentences (#1663), add a line to tonight's list (F13 through
`door.add_item` or R5; a call may already add a task, `docs/calls.md:43`),
and, with the ruling, answer a held item. It cannot: make a program, shape
one, run the interview, apply a diff or waive a requirement. Shaping and the
interview need the shown diff, and a call cannot show it; a call that says
"add a step" hears "I put it on your desk as a change to look at", and the
diff waits in the Program window.

## 5. Decisions for the owner (defaults chosen; say if another is wanted)

1. **A spoken yes on his own line answers a held item** (J6 station 6).
   Default: yes, for core questions and Your word, after the passphrase, with
   the verbatim read-back. The other choice: the call writes a prepared
   answer to Needs you and he presses there.
2. **Ask me ▾ defaults to Each round.** The other choice: Only the core.
3. **A Delivery Workbench milestone only at Done**, as a last tiny step, and
   only where the repository has a roadmap. Default: on at Done.
4. **Dreaming never touches the database**: an Every step Check that names no
   `holdspeak/db/` file, on by the template. Default: on.
5. **A lesson is never kept by rule** for the repository, at any level.
   Default: as written.
6. **The interview direction is A** (one question, in place). Default: A.

## 6. What this design could not establish

- **How pi behaves at its context ceiling.** Whether pi compacts, stops or
  errors at 64k was not read in this lane; J2's "three rounds, then a smaller
  brief" assumes the turn ends without a commit.
- **Claude Haiku as a planner engine.** The model library connects hosted
  models (`model_library.connect_hosted_model`); that a Haiku-class model
  plans well enough at 64k is not measured. PG-LANG owns the planner.
- **The program text grammar.** Every snippet here is an illustration; the
  grammar is PG-LANG's.
- **Whether a phone reply can carry verbs today.** Messages and replies exist
  (#1605); verbs on a program message were not found and are marked New.
- **The audit cost.** One sweep per app group at two widths, overnight or by
  day, is not measured.
- **The sample PR numbers** (#1699 to #1740) are illustrations, not PRs.
