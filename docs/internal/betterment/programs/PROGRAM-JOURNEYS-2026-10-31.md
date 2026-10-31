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

Sources: `PROGRAM-LANGUAGE-2026-10-31.md` (PG-LANG, merged in #1666: the
Program text, shaping, planning, rounds, sizing, Dreaming, Delivery Workbench,
the SDK, slices LANG1 to LANG15), `PROGRAMS-DESIGN-2026-10-28.md` (the engine
as built), `PROGRAMS-REQUIREMENTS-2026-10-31.md` (PG-REQ, #1665),
`docs/programs.md`, `docs/calls.md`, `docs/phone.md`,
`holdspeak/program_templates.py`, the code on `main` at `c263e89d4`. Canvas:
`canvases/program-journeys-2026-10-31.html` (storyboards for J1, J2, J3 and
J6, and the interview round in two directions with the recommended one
marked).

**How this document and PG-LANG divide the work.** PG-LANG is the system: the
grammar, the contracts, the faces and its slices. This document walks the
owner's use cases on that system, station by station, and names what the
system does not cover yet. Every program text here follows PG-LANG §3.2
exactly (the version line, `>` for his words, `R<n> <kind>:` lines, `round`
blocks with `?` and `=`, `budget`, `planner`, `night`, `within`, lamps after
`#`). Where the two documents differed, PG-LANG won, unless a journey showed
a real hole; each such case is listed in "Reconciled with PROGRAM-LANGUAGE" at
the end. What PG-LANG does not cover is New, with a slice id **JRN n**; those
slices are appended to PG-LANG as §13b.

## 0. The journeys in one line each

| | Journey | Who and when | The one thing it proves |
|---|---|---|---|
| J1 | Two paragraphs to a shipped change | at his desk, a weekday afternoon | a pasted idea becomes a draft, then five rounds of one question each, then steps with requirements that execute, verify and prove |
| J2 | The dreaming program | 23:30 to 07:00, the home GPU idle | a cheap planner cuts the backlog into steps that fit the 64k budget; pi builds them under YOLO; he wakes to "Since last night" and only what is his |
| J3 | Shaping a running program by voice | at his desk, a program half done | three spoken sentences become one change well of diff rows; Apply; at YOLO, Overturn |
| J4 | From the desk, for a person | after a 1:1 | one open action becomes a Program for Alice, and Alice reviews the pull request |
| J5 | The race | a brief he does not want to wait on | Claude Code and Codex build the same brief; the first green and reviewed branch wins |
| J6 | Start and steer from the Phone and the Line | in the car at night, in the kitchen at 06:40 | start by voice, hear the state, answer a held question from the phone |
| J7 | A reviewer-only program | before a release | no builder; agents audit every window and the new routes and file Door tasks |
| J8 | Teaching the engine | after a step failed twice for the same reason | the lesson becomes a standing requirement of the repository |

## 1. What every journey shares

The engine as built (PG-REQ, the 2026-10-28 design) and the system of PG-LANG;
the journeys only use them.

- **A step moves on a receipt, not on a claim.** The check is a verified log
  (`program_verifier.verify_text`, `holdspeak/services/program_verifier.py:76`);
  a requirement is Met only on its evidence (PG-REQ §4).
- **The Control level decides who decides** (`docs/programs.md`, "The
  control ladder"). A **core question** (goal, shape, egress, money,
  authority, safety, no rule) comes to him at every level.
- **Decided for you, and Overturn** (#1602). At YOLO a shaped change applies
  at once and is one line here with Overturn (PG-LANG §4.6).
- **Your word holds the merge at every level** (PG-REQ decision 1, #1665).
- **The handover note** "Program: <title>" is rewritten on every change
  (#1602).
- **One window, two views.** The Program window shows **Board · Text** (and
  **Both** above 1100 px); the shaping bar "Change the program" with its mic
  and **Shape**; the change well with diff rows and **Apply** / **Not this**
  (PG-LANG §9).
- **Faces obey UX-CANON**: every verb is the library `Button`; no prose on a
  face; no modal; no counter of zero; egress waits for his press at the act.

### Hands-off and hands-on at definition

PG-LANG §6.5 is the ladder: 1 Dropped, 2 Drafted, 3 Interviewed, 4 Refined,
5 Running, 6 Verified, 7 Proven, 8 Done. The journeys use its two paths:

| Stance | His presses before Start | What it costs him |
|---|---|---|
| **Hands-off** | **Plan it**, **Apply**, **Start** (none at YOLO when an Automation made it) | under a minute; every default is a line of the draft he can read |
| **Hands-on** | **Plan it**, **Ask me first**, one answer and one **Apply** per question, **Done with** each round, **Start** | ten minutes for five rounds (PG-LANG §16 target) |
| **To the detail** | as hands-on, then the step fold of each step (Brief, Requirements, Gate, Sizing) or the Text view | as long as he wants |

The Control level is separate: it decides who decides while the steps run.
A Senior Software Architect may define to the detail and then run at YOLO.

---

## J1 · Two paragraphs to a shipped change

### Who and when

He, at his desk, Tuesday 14:10, after a meeting where Alice asked for a recap
her team can read. He has 20 minutes before the next meeting.

### What he drops in

**New program**, then into the goal `PadGadget` (or **Run as a program** on
the Note where he wrote it):

> After a meeting, the meeting's Note should end with a short recap: the
> decisions, the actions with their owners, and the open questions. It comes
> from the transcript we already keep, runs on the local model, and sends
> nothing out. It is a section of the Note that I can edit, not a new window.
>
> It must be fast: under 20 seconds after Stop on this Mac. It must not make
> up owners: when nobody was named, it says "No owner". Alice asked for this
> for her team's standups, so she sees it before it ships.

### The stations

| # | Station (PG-LANG §6.5) | The engine does | He sees (the words on the face) | He presses |
|---|---|---|---|---|
| 1 | Dropped | nothing yet | Drafting · no steps. The shaping bar reads "Describe the work"; the verb is **Plan it**. | **Plan it** |
| 2 | Drafted | `program.draft` (LANG6) on the `agent.plan` engine: the goal, the template's shape, the repo map, the last 10 merged PR titles. | Ghost rows rise on the board; the status bar says "Planning · qwen3.8-27b". The change well: "4 steps · 8 requirements · 5 rounds to ask" · **Apply** · **Ask me first** · **Not this**. | **Ask me first** |
| 3 | Interviewed: Architecture | `program.round` next (LANG9), one question. | The round strip over the board: **Architecture · Product · Stack · Verification · Delivery**, Architecture breathing. The question row: "Where does the recap run?", the why in muted words, three offered answers (**In the aftercare, after Stop** · **As its own job** · **In the Note window**), the field with its mic, **Skip question**. | **In the aftercare, after Stop** |
| 4 | the answer becomes rows | One shaping call with "In the Architecture round, to 'Where does the recap run?', the owner said 'In the aftercare, after Stop'" (PG-LANG §6.2). | The question folds to one line ("? Where does the recap run · = In the aftercare, after Stop"); under it the change well: `~ step 1 · owns … → holdspeak/services/meeting_aftercare_service.py`, `~ step 1 · brief`. | **Apply**, then **Done with Architecture** |
| 5 | Product | the next round | "Who sees it before it ships?" · **Alice reviews the pull request** · **Only you**. The rows: `+ program · for Alice`, `~ step 4 · review agent → Alice`. | the first, **Apply**, **Done with Product** |
| 6 | Stack | | "Which test runner proves the latency?" | **Skip round** (struck through on the strip) |
| 7 | Verification | Measure is a kind here (LANG11), never guessed; the round picks it. | "How do we know 'under 20 seconds'?" · **A measured run** · **You try it** · **Both**. Rows: `+ R3 measure: The recap is in the Note under 20 s after Stop.` with `bound total < 20 s`, `+ R8 word: I tried it on my desk after a real meeting.` with two `walk` lines. | **Both**, **Apply**; then "No made-up owners: how?" · **A test on a meeting with no names** → `+ R4 check`; **Apply**; **Done with Verification** |
| 8 | Delivery | | "How does it land?" · **Merge each step** · **One owner press per merge**. (In a repository with the rails, a second question offers `delivery dw <project>/<phase>/<story>`; HoldSpeak has dw off, PG-LANG §8.1.) | **Merge each step**, **Apply**, **Done with Delivery** |
| 9 | Refined | sizing (LANG8) has nothing to do: Claude Code has no budget unless the text names one | Drafting · 4 steps · 8 requirements. The strip: five tokens, four ok, one struck through; each done token keeps "n changes". | **Start** |
| 10 | Running | the tick (#1602); briefs with "What must be true" (#1665) | the board, each row with its Met cell ("3 to meet") | nothing |
| 11 | Verified | CHECK runs the check, R4 and R3 (the measure's log and its value, LANG11); REVIEW asks Codex R1, R2, R5 by number | R3 **Met** · "total 14.2 s (bound < 20 s)"; R5 **Unmet** · "names Bob; the transcript has no Bob". | nothing: Normal gives round 2 by rule |
| 12 | Proven | step 4's PR waits for Alice's approval; R8 waits for his word | Your turn: "Ask Alice to review PR #1702" · **Send…**; next morning "Step 4 · R8 · I tried it on my desk after a real meeting" with its walk lines · **Met** · **Unmet** | **Send…**, then **Met** |
| 13 | Done | the end check on the base head (R7); the note's Done line | "Done · 14 of 14 met" | nothing |

The Program text after station 9 (PG-LANG §3.2; lamps after `#`):

```
# program text 1
program Meeting recap in the Note
  goal
  > After a meeting, the meeting's Note should end with a short recap: the
  > decisions, the actions with their owners, and the open questions. It comes
  > from the transcript we already keep, runs on the local model, and sends
  > nothing out. It is a section of the Note that I can edit, not a new window.
  > It must be fast: under 20 seconds after Stop on this Mac. It must not make
  > up owners: when nobody was named, it says "No owner". Alice asked for this
  > for her team's standups, so she sees it before it ships.
  in HoldSpeak · main · project HoldSpeak
  control normal
  check scripts/quick_check.sh
  agent Claude Code
  reviewer Codex at delta
  for Alice

every step
  R1 review: The change does only what its brief says.
  R2 review: Each new behaviour has a test.

at the end
  R7 check: `scripts/quick_check.sh` is green.

round Architecture · done
  ? Where does the recap run?
  = In the aftercare, after Stop.                     # → step 1 owns, step 1 brief
round Product · done
  ? Who sees it before it ships?
  = Alice reviews the pull request.                   # → for Alice, step 4 review
round Stack · skipped
round Verification · done
  ? How do we know "under 20 seconds"?
  = Both: a measured run, and I try it.               # → R3 measure, R8 word
  ? How do we know it never makes up an owner?
  = A test on a meeting with no names.                # → R4 check
round Delivery · done
  ? How does it land?
  = Merge each step.

step 1 The recap in the aftercare
  owns holdspeak/services/meeting_aftercare_service.py
  brief
  > After Stop, write the recap at the end of the meeting's Note from the kept
  > transcript, on the local model. Send nothing out.
  R3 measure: The recap is in the Note under 20 s after Stop.
    run uv run pytest -q tests/integration/test_recap_latency.py
    bound total < 20 s

step 2 No made-up owners
  owns holdspeak/services/meeting_recap_owners.py
  after 1
  brief
  > When nobody was named, the owner is "No owner".
  R4 check: `uv run pytest -q tests/unit/test_recap_owners.py` is green.
  R5 review: The recap never names an owner the transcript does not name.

step 3 The recap section in the Note
  owns web/src/desk/pullouts/NotePullout.tsx
  brief
  > The recap is a section of the Note he can edit, not a new window.
  R6 shot: The Note window at 393 has no clipped text.

step 4 The recap in the export
  after 2, 3
  review Alice
  brief
  > The meeting's Markdown export carries the recap section.
  R8 word: I tried it on my desk after a real meeting.
    walk Record a meeting of two minutes and press Stop.
    walk Open its Note and read the recap.
```

Requirement count: 8 sentences (R1 to R8); the Met count is 14, because each
step's copy of R1 and R2 counts once (PG-REQ §7): 8 copies, 5 steps' own, 1
of the whole program.

### Verification and proof at each gate

| Gate | Proof | Who reads it |
|---|---|---|
| Definition | each requirement can be proven here (`requirement_unprovable` otherwise); each round's answers are `=` lines with the lamp of what they became | the hub, by rule |
| CHECK | the verified check log; R4's log with `program-check: exit 0`; R3's log with a value under its bound (LANG11); R6's image | the verifier |
| REVIEW | Codex's `REQ R n` lines on the reviewed commit | the engine parses; UNMET is a REQUIRED finding |
| Alice | her approval on GitHub, read by follow-through | the engine |
| MERGE | his **Met** on R8, after its walk | him |
| Done | the end check on the base head (`hs-program-<id>-end`) | the engine |

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| Plan it | rows wait for **Apply** | the same | the draft applies at once (PG-LANG §6.5) |
| each answer's rows | **Apply** | **Apply** | applied at once, one line under Decided for you with Overturn |
| each merge | his **Merge** | by rule on green, reviewed and met | by rule |
| R5 unmet after the rounds | him: **Send back** / **Waive** | park, the rest go on, one row to him | one smaller brief, then park |

### The morning after

- **The Note** "Program: Meeting recap in the Note": "Done · 14 of 14 met · 4
  PRs · 2 h 10"; a "Why" section with one line per answer that became a
  requirement (PG-LANG §10).
- **Needs you**: nothing, or only R8 if he did not walk it yet.
- **Delivery Workbench**: nothing in HoldSpeak (off, PG-LANG §8.1). The same
  journey in one of his repositories with the rails has `delivery dw
  <project>/<phase>/<story>` from the Delivery round, and at Done one PR
  "Delivery: Meeting recap in the Note done" with the evidence of PG-LANG §8.3
  (LANG13).
- **The 1:1 brief** with Alice: step 4 under "To show them" (#1602).

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| He pastes three goals at once | the draft proposes three Programs (New: JRN1); without it, the draft is one long Program and the rounds' Architecture question is where he splits it by hand |
| An answer contradicts the paragraphs ("Only you" after "Alice sees it") | the shaping guard: a removed `for Alice` is a core question (egress), drawn with its reason, his press at every level |
| A Check names a test that does not exist yet | the step's brief says it writes that test; at CHECK a missing file is a red round, not Met |
| He leaves mid-interview | the Program stays in Drafting with the round strip as it was; the asking round resumes at its question (`rounds_json`) |
| The planner writes a line the parser cannot read | "The engine's answer could not be read. The program is unchanged." · **Try again** (PG-LANG §4.8) |

### Delight moments

- A step is born from his answer: its six station dots draw left to right as
  the row lands (PG-LANG §9.7).
- A round closes: its token turns ok and keeps "4 changes".
- "Done · 14 of 14 met".

---

## J2 · The dreaming program

### Who and when

Weeknights, 23:30 to 07:00. The home box (qwen3.8-27b over Tailscale,
`HOME_ENGINE_PROFILE` at `holdspeak/program_templates.py:25`) is idle. The
owner: "our context maxes out at 64k tokens".

### What he drops in

During the day, one line at a time, with **Add to tonight** (New: JRN2) on a
Door task, a Later finding or a note line, or by a sentence on a call. Each
press marks the item for the dreaming backlog, which PG-LANG reads by rule
(§5.5: Door tasks with the word "dream", Later findings, small actions, the
canon scanner's residues). Three lines of his:

> The Calls window's status bar says "Line starting" for 40 s after the Line is up.
>
> The Terminals window has raw buttons.
>
> The Engines rows at 393 clip the readiness word.

And once, the Program (an Automation, "Run a program" with the Dreaming
template, PG14 #1626 and LANG12):

```
# program text 1
program Dreaming · HoldSpeak
  in HoldSpeak · main · project HoldSpeak
  template dreaming
  control yolo
  agent pi on qwen3.8-27b
  planner Claude Haiku
  spend up to $1
  reviewer Claude Code at glance
  budget 64k
  when idle
  night 23:30–07:00 · at most 8 steps
  within web/src/desk/, docs/, tests/unit/

every step
  R1 review: The change does only what its brief says.
  R2 check: `uv run python scripts/ux_canon_scan.py` is green.
```

`planner Claude Haiku` is a hosted engine from his library; `spend up to $1`
answers the money core question before the first call. `planner
qwen3.8-27b` costs nothing and needs no spend line.

### The stations

| # | Time | The engine does | He sees | He presses |
|---|---|---|---|---|
| 1 | set-up | the Automation (PG14) gains the Dreaming template and the night line (LANG12) | the automation window: Do **Run a program** · Template **Dreaming** · Level **YOLO** · When **Every weekday at 23:30** | **Turn on** |
| 2 | 23:30 | the Program record reopens as Running (one record, one Note history, PG-LANG §5.5). The planner reads the backlog by rule and makes one tiny step per item (one `agent.plan` call per item). Sizing (LANG8): each step's estimate must be at most half the budget (`WORKING_SHARE`, 32k of 64k). | The board fills; each row's lamp says its estimate: "# 18k of 64k". | nothing |
| 3 | 23:31 | One step is too big: "Too big for qwen · 41k of 32k". At YOLO the planner splits it into parts that together own what it owned (`step_too_big`, PG-LANG §5.4). | Decided for you: "Split step 3 (too big for qwen): 2 parts · rule: YOLO splits" · **Overturn** (while the parts are Planned). | |
| 4 | 23:32–06:30 | pi on qwen builds one step at a time, only when idle (`program_runner.engine_idle`, `holdspeak/services/program_runner.py:196`); Claude Code reviews at glance; YOLO merges green, reviewed and met (#1602). | "Running · 5 of 9 merged"; a waiting row: "Ready · waiting for qwen". | nothing |
| 5 | 02:40 | The backlog's canon scanner residue gives one more step; YOLO adds a step the plan lacked and says so. | "Added for you: step 10 · from the canon scanner" · **Overturn**. | |
| 6 | 03:12 | Step 7's fix needs `holdspeak/db/`, outside `within`: a core question at every level. Reach (#1619): a migration is not urgent, so quiet hours hold the message. | Your turn on the Program; Needs you in the morning. | |
| 7 | 07:00 | The night stops (at 07:00, at `at most 8 steps`, or after two red steps in a row): Ready steps go back to the backlog; a Working step finishes its turn and parks "the night ended". | "Parked · the night ended" on that row. | |
| 8 | 07:00 | "Since last night" is written on top of the handover note (LANG12). The night is not Done, so the "Program is done" reach does not fire: one phone message with the first line is New (JRN4). | The Note, Today, the phone. | |

A guard the night needs that PG-LANG does not have: **no step is handed
while the base branch is red** (New: JRN3). Every dream merge to HoldSpeak's
main redeploys his desk (PG-LANG §15.6); the stop after two red steps counts
the night's own steps, not a red main that another merge caused.

### Verification and proof at each gate

- **Sizing**, before a step is handed (LANG8): the estimate by rule, no model.
- **CHECK**: the repository's check, R2 (the canon scanner) on each commit.
- **REVIEW**: Claude Code at glance, R1 by number.
- **MERGE**: by rule at YOLO; a Your word requirement waits for the morning.
- **The bounds**: `within` (a file outside it is a core question), `night`,
  `at most`, `spend up to`.

### Hands-off and hands-on

| | Secure | Normal | YOLO (the template) |
|---|---|---|---|
| merge | each waits for his **Merge** in the morning | by rule | by rule |
| a step from the backlog the plan did not have | him | him | added, with Overturn |
| a step too big for its budget | **Split** / **Run anyway** | the same | split, with Overturn |
| a red step after its rounds | him | parked, the rest go on | one smaller brief, then parked |
| outside `within`, a migration, egress, a deleted test, money past the limit | him | him | him |

### The morning after

The handover note "Program: Dreaming · HoldSpeak", top section:

```
## Since last night
23:30–06:52 · 10 steps · 8 merged · 1 parked · 1 waits on you
Merged: #1710 Line starting word · #1711, #1712 Terminals buttons (split in 2) · #1714 Engines at 393 · …
Parked: step 9 · the night ended · continues from its checkpoint
Waits on you: step 7 · outside within: holdspeak/db/
Spent: $0.38 of $1 (the planner) · qwen 5 h 10 · Claude Code 41 min
```

- **Needs you**: "Dreaming · Step 7 asks you: the fix needs holdspeak/db/" ·
  **Go on** · **Park**.
- **Today**: "Dreaming: 8 merged, 1 waits on you" (PG-LANG §5.5).
- **The phone**: the first line of "Since last night" (JRN4).
- **Delivery Workbench**: nothing. A night is not a major point.

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| He dictates at 01:00 | his use takes the engine first; the step waits "Ready · waiting for qwen" |
| pi meets its context limit mid-step | the sizing rule is there to prevent it; whether pi compacts or stops is not known (see "could not establish"); a turn with no commit is a red round |
| The planner reaches `spend up to $1` | planning stops; planned steps still run on qwen; the digest says "Planner stopped at $1" |
| Two steps own the same file | the second waits ("after"), as the brief's "theirs, do not touch" rule |
| Main is red after another merge | New (JRN3): no step is handed until main is green; the digest says how long the night waited |

### Delight moments

- The board at 07:00 is a column of green MERGE dots.
- Each row's lamp ("# 18k of 64k") shows that small is small.
- "Since last night" says the night in one line.
- **Add to tonight** is one press from anywhere.

---

## J3 · Shaping a running program by voice

### Who and when

He, at his desk, Wednesday 16:00. "The hub stops stalling" runs at Normal:
steps 1 and 2 merged, step 4 working, steps 5 and 6 planned. He holds the
shaping bar's mic.

### What he drops in

Three sentences, spoken:

> Every step must keep ruff green. Put a step before the fan-out that adds the
> loop watch. And the fan-out runs on qwen tonight, not Claude.

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | The `program` voice grammar puts the words in the shaping bar (LANG5). | "Change the program" holds the three sentences; **Shape**. | **Shape** (or the end of the held press) |
| 2 | Quick forms first (no model); the rest is one `program.shape` call (LANG3); the splice; the `text_apply` preview; the guard. | The bar breathes "Reading the program". | |
| 3 | The change well. | The say head: "Add ruff to every step; add The loop watch before the fan-out; put the fan-out on qwen when idle" and "qwen3.8-27b · 2.8 s". The diff rows (below). | **Apply** |
| 4 | One apply through the existing verbs: one checkpoint "Changed by the text: 6 changes", one `program_changed` frame. | The new step 6 lands with its dots drawn one by one; the fan-out is step 7 with "pi · qwen3.8-27b"; R9 has five small dots. | |

The rows (PG-LANG §3.8):

```
+ every step · R9     R9 check: `uv run ruff check .` is green.          allowed
+ step 6 The loop watch · after 4, 5                                     allowed
↕ step 6              before step 6 (step 6 is now step 7)               allowed
~ step 7 · after      4, 5  →  6                                          allowed
~ step 7 · agent      Claude Code  →  pi on qwen3.8-27b                   allowed
+ step 7 · when idle                                                     allowed
```

and the text after the apply:

```
every step
  R2 review: The change does only what its brief says.
  R3 check: `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green.
  R9 check: `uv run ruff check .` is green.

step 6 The loop watch                             # Planned
  after 4, 5
  brief
  > Add the loop watch.

step 7 The fan-out                                # Planned
  after 6
  agent pi on qwen3.8-27b
  when idle
  brief
  > One frame per change, not one per row.
```

R9 goes to the steps that are not merged (PG-REQ: an every-step requirement
is copied to each step that is not merged); on step 4, which works, it is
judged at CHECK.

### Verification and proof

- Before Apply: every row is classed (allowed, refused, conflict, lowers).
  None of these lowers the bar.
- After Apply: R9 is a Check on each step's commit; step 7 runs only when
  qwen is idle.

### Hands-off and hands-on

| Who shapes | Secure | Normal | YOLO |
|---|---|---|---|
| He | **Apply** | **Apply** | applies at once; one line under Decided for you: "Shaped: ruff on every step; The loop watch before the fan-out; the fan-out on qwen" · **Overturn** while the changed steps are Planned |
| An orchestrating agent | a proposal row "The orchestrator changes the program: 6 changes" · **Apply** · **Skip** | the same | applies with a Decided for you line and Overturn |
| A row that lowers the bar | his **Apply this** per row, at every level | the same | the same |

### The morning after

The note's Steps list has seven steps; the Ledger keeps "Changed by the text:
6 changes". If the fan-out ran overnight on qwen: "Step 7 · Merged #1720 · pi ·
qwen3.8-27b · 1 h 40".

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| Dictation hears "Gwen" | the vocabulary is the desk's engines; the row says "pi on qwen3.8-27b" or the engine asks one question ("which engine?") under the bar |
| A sentence no quick form reads and no engine is set | "No engine is set for planning" · **Open Engines** · **Open text** |
| "And step 4 does not need the review" (step 4 works) | the row "~ step 4 · review agent → none · Lowers the bar · Refused: The bar does not come down while it runs"; nothing of it applies |
| "Insert before step 4" and step 4 started | refused: "Step 4 started. Add the step after it." |
| An agent changed step 7 since he read the text | the row is a conflict: "Step 7's agent changed since you read it: now Codex"; **Apply** applies the rest |

### Delight moments

- He speaks; the rows come; one press; the new step's dots draw one by one.
- "Step 6 is now step 7" once in the ledger; nothing else moves.

---

## J4 · From the desk, for a person

### Who and when

He, after his 1:1 with Alice, Thursday 11:30. The meeting made an action in
the project HoldSpeak: "Alice: the 1:1 brief exports as Markdown".

### What he drops in

Nothing typed. One press on the action's row: **Run as a program** (New:
JRN13; today the verb is on a Note, and From the desk takes every open action
of a project). The draft it plans:

```
# program text 1
program The 1:1 brief exports as Markdown
  in HoldSpeak · main · project HoldSpeak
  template from the desk
  for Alice

step 1 The 1:1 brief exports as Markdown
  from action:act-7f20
  review Alice
  R1 word: The change does what its action asks: the 1:1 brief exports as Markdown.   # JRN14: a Review under a person gate is your word
```

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | A Program from the **From the desk** template (#1602) with one step from this one action (JRN13), planned at once (LANG6). The action's person (Alice) becomes `for Alice`. The template's step requirement: "The change does what its action asks: …" (`holdspeak/program_templates.py:39`). | The change well: "1 step · 1 requirement · 1 round to ask" · **Apply** · **Ask me first** · **Not this**. After **Ask me first**, the Product round asks one question: "Does Alice review the pull request?" · **Alice reviews** · **Only you**. | **Alice reviews**, **Apply** |
| 2 | Step 1 gets `gate_review = person` with Alice; her GitHub login comes from her `github` alias in People (#1602). A From the desk program has no review gate by default; a person gate is one. | Alice's portrait at REVIEW on the track. | **Start** |
| 3 | Build, check, PR (#1602). | "PR open #1731". | |
| 4 | The person gate: a prepared send through the channel; the merge waits for her approval on GitHub. | Needs you: "Ask Alice to review PR #1731" · **Send…**; the send preview shows where it goes (egress at the act). | **Send** |
| 5 | Follow-through reads her approval; the merge by the level; the action closes with the PR as evidence (#1602). | "Merged #1731"; the action is done. | |

### Verification and proof at each gate

CHECK as always; REVIEW is Alice's GitHub approval, read, not claimed; the
action's own requirement is answered by the reviewer of record. Because Alice
is a person, her review answers no `REQ` line; the requirement "does what its
action asks" is his word at MERGE when no agent reviewer runs (New, JRN14: a person
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
| Alice asks for changes on GitHub | follow-through reads "changes requested"; her comments go to the builder as a round (New, JRN14: person review comments as findings) |
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

The text after the one question (PG-LANG's race form, §3.7):

```
# program text 1
program Mermaid words in Notes search
  in HoldSpeak · main · project HoldSpeak
  template race

step 1 Find words inside Mermaid fences
  race 2
  agent Claude Code, then Codex
  review agent
  brief
  > Notes search finds words inside Mermaid fences. Today a word in a diagram
  > is not found. Keep the search under 50 ms for 2,000 notes.
  R1 review: The change does only what its brief says.
  R2 measure: Notes search over 2,000 notes takes under 50 ms.
    run uv run pytest -q tests/unit/test_notes_search_speed.py
    bound p95 < 50 ms
```

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | **Plan it** on the **Race** template (#1602): one brief, two contenders (Claude Code and Codex) in sibling worktrees. The template has no review gate; "first green and reviewed" needs one, so the Verification round asks. | The question row: "Review each contender?" · **Each reviews the other** · **No review**. | the first, **Apply** |
| 2 | The review turns on; the template's Review requirement plants ("The change does only what its brief says.", #1665). "Under 50 ms" becomes a Measure requirement with its bound (LANG11), or `requirement_unprovable` if no command can print the number. | The board: step 1 with two contender rows under it (the race species, #1618). | **Start** |
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
06:30 his phone shows a held message; at 06:40 in the kitchen he calls again.

### What he says

> Start the overnight program.

and in the morning:

> How is the overnight program doing?
>
> Step 7: go on, with a new column. Do not change the old rows.

### The stations

| # | When | The engine does | He hears or sees | He says or presses |
|---|---|---|---|---|
| 1 | 23:10 | The call finds the program by its words and holds `program.start` for his spoken yes (#1663). | "I want to start the program Overnight on the home box. Say yes or no." | "Yes." |
| 2 | 23:10 | Started; the transcript becomes a Note. | "Started. Nine steps. The first one runs when the home box is idle." | hangs up |
| 3 | 03:12 | Step 7 meets a core question (a file outside `within`). Reach at YOLO with `may call` is a call at once (`docs/phone.md:106`), but quiet hours hold all but an urgent call (#1619); this is not urgent, so a message waits. | nothing at 03:12 | |
| 4 | 06:30 | The held message goes out. New (JRN6): the message carries the item's own verbs, and a press on his paired phone is his press. | "Overnight on the home box · Step 7 asks you: the fix needs holdspeak/db/" · **Go on** · **Park** | (he calls instead) |
| 5 | 06:40 | "How is …" is `program.get` by name, said as `spoken_state` (#1663). | "Running. Six of nine steps merged. One waits on you: step 7 needs holdspeak/db/. Last decision: merged step 6 at 05:12." | "Step 7: go on, with a new column. Do not change the old rows." |
| 6 | 06:40 | **Default, no ruling needed (JRN5):** the spoken answer becomes a prepared answer on the Your turn item: the choice (Go on) and his words as its line. Nothing is decided on the call. | "I put your answer on your desk: go on, with your words 'a new column; do not change the old rows'. Press Go on there or on your phone." | hangs up |
| 7 | 06:41 | The prepared row in Needs you and on the phone message; his press is the decision (`program.decide`, owner only); the line goes to step 7's agent at its next turn end ("The owner on step 7: …"). | Needs you: "Step 7 · Go on · 'a new column; do not change the old rows' · prepared on a call" · **Go on** · **Not this** | **Go on** (on the phone) |

**With the ruling** (PG-LANG §15.10, JRN7): station 6 asks "I want to answer
step 7: go on, with your words '…'. Say yes or no." and his spoken yes is the
decision, the same hold as `program.start`. Today a call may not "confirm a
decision for you" (`docs/calls.md:44`), so this waits for his word.

### Verification and proof

- The call record is evidence of the turn; the Program's ledger is the
  receipt of the answer: "06:41 · Answered by you: go on · prepared on a
  call".
- The read-back is verbatim; the prepared row shows the words exactly as they
  will be typed to the agent.

### Hands-off and hands-on

| | Secure | Normal | YOLO |
|---|---|---|---|
| a core question at night | a message | a message, then a call after 10 min when `may call` | a call at once when `may call` (quiet hours hold all but urgent) |
| start by voice | spoken yes | spoken yes | spoken yes |
| answer by voice | a prepared answer, his press | the same | the same (or a spoken yes, with the ruling) |
| shape by voice ("put step 8 on Codex") | `program.shape` held for his yes, the diff read back from the rows' `say` (LANG5) | the same | the same |

### The morning after

The transcript Note of each call, linked from the ledger. Needs you has no
row left for step 7.

### What could go wrong, and what the engine does

| What | The engine |
|---|---|
| Two programs match "overnight" | it names both by title and starts nothing until one is named |
| He says yes to the wrong thing | the hold repeats the full title and the step; "no" or silence does nothing |
| A noisy line, half heard | the read-back is verbatim; he says "no" and says it again |
| He answers on the phone and on a call | the first press decides; the second hears "Step 7 is answered already" |

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

The text (`template audit` is New, JRN8; PG-LANG has no such template):

```
# program text 1
program Release audit
  in HoldSpeak · main · project HoldSpeak
  template audit                                    # JRN8
  control normal
  within web/src/desk/, holdspeak/web/routes/

step 1 Speak and Calls windows
  merge none
  brief
  > Read each window at 393 and 1440 against docs/internal/UX-CANON.md.
  > File what you find. Change nothing.

step 2 Routes added since 1 October
  merge none
  brief
  > Read each route for a lock on the event loop and for its residual-set entry.
```

### The stations

| # | The engine does | He sees | He presses |
|---|---|---|---|
| 1 | A new template **Audit** (New, JRN8): each step is an audit, not a build. Its agent works in a scratch copy, as the reviewer does (AG12); `gate_merge = none` (a step with no PR, which exists, `docs/programs.md` "Gate"); no commit is expected. | The planner's steps: one per app group of `web/src/desk/applications.ts` (the sweep's manifest, `tests/e2e/test_desk_sweep.py:7`), plus "Routes added since 1 Oct". | **Start** |
| 2 | Each audit step runs the desk sweep's shots for its windows and reads them with the canon; the routes step reads the diff since 1 October. Its report is a list of findings, each MUST, SHOULD or NOTE, with evidence: a shot, a `file:line`. | The board's stations for an audit: BRIEF · WORK · REVIEW (the auditor's own findings) · FILE. | |
| 3 | New (JRN9): each finding is filed as a Door task through `door.add_item` (exists, the Door's MCP), with its evidence and the project, grouped by window. | The Requirements board is replaced by **Findings**: "14 findings · 3 MUST". | (Secure: per finding **File** / **Skip**) |
| 4 | Done when every step reported. Proposal (JRN10): "Make a fix program from the 3 MUST" · **Make** · **Skip** (a proposed Program, never started by rule). | "Done · 31 windows · 14 findings". | **Make** |

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
| 1 | New (JRN11): a lesson rule. When a step goes green after a round whose red named the same cause on two steps, or when the reviewer writes the same finding on three steps, the engine writes a **Lesson** with the cause, by rule, not by a model. | Your turn: "Lesson · the check needs packages: 2 steps red for it" · **Keep for this program** · **Keep for HoldSpeak** · **Skip**. And "Lesson · raw `<button>` on 3 steps" with the same verbs. | **Keep for HoldSpeak** on the first |
| 2 | **Keep for this program**: an Every step requirement (#1665). **Keep for HoldSpeak** (the repository): New (JRN12), a tiny step of this Program that edits `.holdspeak/program.json` (the `check` gets `uv sync --extra dev && npm ci &&` before it; or a `requirements` item), checked, reviewed and merged as any step. The repository's defaults are read by every new Program (#1665). | A new step 7 "Keep the lesson: the check installs packages" with "from a lesson". | (the second lesson) **Keep for this program** |
| 3 | The second lesson becomes one row in the change well: `+ every step · R6   R6 check: \`uv run python scripts/ux_canon_scan.py\` is green.` (the scanner exists, `scripts/ux_canon_scan.py`). | R6 with its six small dots. | **Apply** |

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

Each face, engine capability, route and library gadget the journeys use.
**Exists** names the PR or the file; **In PG-LANG** names the slice of
`PROGRAM-LANGUAGE-2026-10-31.md` §13; **New** names its JRN slice, appended to
that design as §13b; **Dropped** was in the first draft of this document and
is not needed on PG-LANG's system (see "Reconciled").

### Faces

| # | Item | Journeys | State |
|---|---|---|---|
| F1 | Programs window, Program window, the board, the Your turn well, Decided for you, the handover note | all | Exists #1602 |
| F2 | Requirements board, Add requirement row, the Met column, Find, the step fold, Insert before, Move | J1 J2 J3 J8 | Exists #1665 |
| F3 | Race contender rows, the race shot | J5 | Exists #1602, #1618 |
| F4 | Person review row "Ask Alice to review PR" with Send… | J1 J4 | Exists #1602 |
| F5 | **Run as a program** on a Note, planning at once | J1 | Exists #1602; plans at once In PG-LANG LANG6 |
| F6 | The Text view (Board · Text · Both) | J1 J3 | In PG-LANG LANG2 |
| F7 | The shaping bar with its mic, the change well with Apply / Not this | J1 J3 | In PG-LANG LANG4 (well LANG2) |
| F8 | The question row (question, why, offered answers, field with mic, Skip question) | J1 J4 J5 | In PG-LANG LANG10 |
| F9 | The round strip with a state dot per round, Done with <round>, Skip round | J1 | In PG-LANG LANG10 |
| F10 | "Ask me ▾" (Only the core · Each round · Everything) | J1 J4 | Dropped: **Plan it** / **Ask me first** (LANG7) |
| F11 | "Assumed" lines | J1 | Dropped: every default is a line of the draft (LANG6, LANG7) |
| F12 | The estimate lamp ("# 18k of 64k"), the Sizing token, "Too big for qwen" | J2 | In PG-LANG LANG8, LANG10 |
| F13 | **Add to tonight** on a Door task, a finding, a note line | J2 | New · JRN2 |
| F14 | "Since last night" in the handover note | J2 J6 | In PG-LANG LANG12 |
| F15 | "Dreaming: 8 merged, 1 waits on you" on Today | J2 | In PG-LANG LANG12 |
| F16 | Undo of his own shaped change | J3 | Dropped: Overturn at YOLO; below YOLO nothing applies without his Apply |
| F17 | **Run as a program** on a project action row | J4 | New · JRN13 |
| F18 | The audit board (BRIEF · WORK · REVIEW · FILE), the Findings board | J7 | New · JRN9 |
| F19 | The Lesson Your turn row (Keep for this program · Keep for HoldSpeak · Skip) | J8 | New · JRN11 |
| F20 | The item's verbs on a phone message (Go on · Park, Met · Unmet) | J6 | New · JRN6 |
| F21 | The automation's Run a program fields | J2 | Exists #1626 |
| F22 | The automation's Dreaming template and night line | J2 | In PG-LANG LANG12 |
| F23 | The prepared answer row in Needs you ("prepared on a call") | J6 | New · JRN5 |

### Engine capabilities

| # | Item | Journeys | State |
|---|---|---|---|
| E1 | The tick, the gate, review, PR, merge, the control ladder, core questions | all | Exists #1602 |
| E2 | Requirements of four kinds, the end check, Your word holds the merge | all | Exists #1665 |
| E3 | Adjust: change, insert before, move, amend, the frozen table | J3 | Exists #1665 |
| E4 | pi on an engine, when idle | J2 J3 | Exists #1602 (`program_runner.py:196`) |
| E5 | Handoff at a usage limit | J5 | Exists #1604 |
| E6 | Checkpoint refs, Start from here | J2 J5 | Exists #1649 |
| E7 | Proposed decisions from a Program | J1 | Exists #1644 |
| E8 | An automation runs a program | J2 | Exists #1626 |
| E9 | Start a program on a call; its state in a sentence | J6 | Exists #1663 |
| E10 | Reach: a message or a call by level, quiet hours | J2 J6 | Exists #1605, #1619 |
| E11 | Planning: a goal becomes a draft (`program.draft`) | J1 J4 J5 | In PG-LANG LANG6 |
| E12 | Shaping: a sentence becomes diff rows; the guard; YOLO apply and Overturn | J3 | In PG-LANG LANG3 (voice LANG5) |
| E13 | Interview rounds, one question at a time, each answer a shaped change | J1 J4 J5 | In PG-LANG LANG9 |
| E14 | Sizing: `budget`, the estimate, `step_too_big`, the split | J2 | In PG-LANG LANG8 |
| E15 | The `planner` line and `spend up to` for a hosted planner | J2 | In PG-LANG LANG3, LANG12 |
| E16 | The Dreaming template | J2 | In PG-LANG LANG12 |
| E17 | One record reopened each night, steps from the backlog read by rule | J2 | In PG-LANG LANG12 |
| E18 | The night stop (`night`, `at most`, two red steps) | J2 | In PG-LANG LANG12 |
| E19 | No step is handed while the base branch is red | J2 | New · JRN3 |
| E20 | `program.decide` behind a spoken yes on a call | J6 | New · JRN7 (needs the ruling, PG-LANG §15.10) |
| E21 | A press on a phone message decides the item | J6 | New · JRN6 |
| E22 | A Program from one action (not every open action) | J4 | New · JRN13 |
| E23 | A person gate plants Review requirements as Your word | J4 | New · JRN14 |
| E24 | A person reviewer's "changes requested" as findings | J4 | New · JRN14 |
| E25 | The Audit template: a step with no builder, in a scratch copy, a report of findings | J7 | New · JRN8 |
| E26 | Each audit finding filed as a Door task with its evidence, merged across windows | J7 | New · JRN9 (`door.add_item` exists) |
| E27 | A proposed fix program from findings | J7 | New · JRN10 |
| E28 | The lesson rule (same cause on two steps, same finding on three) | J8 | New · JRN11 |
| E29 | Keep for the repository: a tiny step that edits `.holdspeak/program.json` | J8 | New · JRN12 (reading the file exists, #1665) |
| E30 | User templates (Keep for a template) | J8 | New, not planned (parked; the repository file is the place) |
| E31 | Delivery Workbench: the link and one PR at Done | J1 | In PG-LANG LANG13 |
| E32 | The draft proposes several Programs when the goal is several goals | J1 | New · JRN1 |
| E33 | The Measure kind; walk lines on Your word | J1 J5 | In PG-LANG LANG11 |
| E34 | The night's end reaches him: one phone message with the first line of "Since last night" | J2 | New · JRN4 |
| E35 | A spoken answer to a held item becomes a prepared answer | J6 | New · JRN5 |

### Routes and tools

| # | Item | Journeys | State |
|---|---|---|---|
| R1 | `/api/programs`, the `program` MCP family | all | Exists #1602 |
| R2 | Requirements, step change, amend; `program.require`, `program.step_update`, `program.amend` | J1 J3 J8 | Exists #1665 |
| R3 | `program.start` and `program.get` by name | J6 | Exists #1663 |
| R4 | `program.text`, `text_apply`, `shape`, `draft`, `round` and their routes | J1 J3 | In PG-LANG LANG1, LANG3, LANG6, LANG9 |
| R5 | Mark an item for the dreaming backlog (`program.backlog_add`, `POST /api/programs/{id}/backlog`) | J2 | New · JRN2 |
| R6 | `program.decide` in the CALL palette, held for the spoken yes | J6 | New · JRN7 |
| R7 | The lesson decide kinds (`lesson`: keep_program, keep_repository, skip) | J8 | New · JRN11 |
| R8 | `program.shape` in the call palette, held, the diff read back | J6 | In PG-LANG LANG5 |

### Library gadgets

| # | Item | State |
|---|---|---|
| G1 | `Toolbar`, `StatusBar`, `ListView`, `FoldGadget`, `DotWord`, `StateChip`, `Token`, `FilterTokens`, `StringGadget` with `MicButton`, `CycleGadget`, `CheckGadget`, `WorkMenu`, `SurfaceCode`, library `Button` | Exists (the kit; UX-CANON §B) |
| G2 | `DiffRow`, `ChangeWell` | In PG-LANG LANG2 |
| G3 | `QuestionRow`, `RoundStrip` | In PG-LANG LANG10 |
| G4 | `TextPane` | In PG-LANG LANG2 |

**Tally: 24 New, 23 In PG-LANG, 20 Exists, 3 Dropped** (70 rows). 23 of the
New rows map to fourteen slices, JRN1 to JRN14; E30 is parked, not a slice.
The first draft of this document had 34 New and 10 In PG-LANG over 64 rows.
Against LANG1 to LANG15: 11 of those New rows moved to In PG-LANG, 3 were not
needed (Dropped), 20 stay New; E32 moved from In PG-LANG to New (PG-LANG does
not split a goal into Programs); six rows were added (F23, E34, E35 New; E33,
R8, G4 In PG-LANG).

The five biggest New items:

1. **Answers from the phone and on a call** (JRN5, JRN6, JRN7): a prepared
   answer by default, the phone's own verbs, and, with his ruling, the spoken
   yes.
2. **Audit programs** (JRN8 to JRN10): a step with no builder, a findings
   board that files Door tasks, a proposed fix program.
3. **Lessons** (JRN11, JRN12): a rule that sees a repeated cause, kept in the
   repository through a reviewed step.
4. **Dreaming's edges** (JRN2 to JRN4): Add to tonight, the red-main hold,
   the morning message.
5. **From the desk, for a person** (JRN13, JRN14): one action as a Program,
   and the person gate's requirements and comments.

## 3. The interview round: two directions (canvas)

- **A · One question, on the board (recommended; PG-LANG's R-A).** The round
  strip over the board (Architecture · Product · Stack · Verification ·
  Delivery, a state dot each: open hollow, asking breathing, done ok, skipped
  struck through) with **Done with <round>** and **Skip round** at its right.
  Under it one question row: the question, its why in muted words, up to
  three offered answers as plated Buttons, the field with its mic, **Skip
  question**. His answer folds the question to one line; its diff rows come
  in the change well under it; **Apply**; the next question rises.
- **B · The round sheet.** Each round a fold of question rows, all open at
  once, each with an answer `CycleGadget` and its mic; one **Apply the round**
  shapes all of its answers into one change well. Fastest for an architect
  who knows every answer; it reads as a form, and the owner asked for one at a
  time. PG-LANG's R-B (a column) is the same idea beside the board.

**Why A.** One question and its consequence on the screen; voice works
because there is one thing to answer; the eye stays on the plan. A done round
prints as a `round` block in the Text view, so the whole interview is
readable at once without a sheet.

## 4. Journeys at 393 and on a call

**At 393.** The Program window is the screen; Board · Text are two tokens,
one at a time. The shaping bar is full width with its 44 px mic and **Shape**.
The change well's rows are two lines (`+ step 7 The loop watch` / `after 4 ·
pi · low · Allowed`) with plated 44 px verbs. The round strip scrolls
sideways; the question row stacks (question, offered answers in a column, the
field). "Since last night" is the top of the Note. The Lesson and prepared
answer rows take two lines with their verbs on the second (PG-LANG §9.6).

**On a call.** The call can start a program by its words and say its state
(#1663); shape it, with the diff read back from the rows' `say` sentences and
a lowers-the-bar row needing its own yes (LANG5); answer the next round
question (`round_answer`, held when it changes the plan, PG-LANG §10); mark a
line for tonight (JRN2); give a prepared answer to a held item (JRN5) or,
with the ruling, decide it (JRN7). It cannot make a program, waive a
requirement, or apply a row that lowers the bar without its own yes.

## 5. Decisions for the owner (defaults chosen; say if another is wanted)

1. **A spoken yes on his own line decides a held item** (JRN7). Default:
   **no**; the call prepares the answer and his press decides it (JRN5).
   Added to PG-LANG as §15.10.
2. **A press on his paired phone is his press** (JRN6). Default: yes, for
   the item's own verbs; a waive is never offered on the phone (it needs a
   typed line).
3. **A lesson is never kept by rule** for the repository, at any level.
   Default: as written.
4. **Dreaming waits while main is red** (JRN3). Default: on.
5. **The interview direction is A** (PG-LANG's R-A). Default: A.

## 6. What this design could not establish

- **How pi behaves at its context limit.** PG-LANG §17: pi reads its window
  from the deployment's `context_ceiling` or uses 32,768
  (`holdspeak/delivery/pi_launch.py:58`, `:128`); whether his revision carries
  64k is not read. J2's `budget 64k` assumes it does.
- **Claude Haiku as a planner.** The library connects hosted models
  (`model_library.connect_hosted_model`); how well a Haiku-class model writes
  `program.shape@1` blocks is not measured.
- **Whether the phone app can carry verbs today.** Messages and replies exist
  (#1605); verbs on a program message were not found, so JRN6 is New.
- **The audit cost.** One sweep per app group at two widths is not measured.
- **The sample PR numbers** (#1699 to #1740) and the action id `act-7f20` are
  illustrations.

## Reconciled with PROGRAM-LANGUAGE

Each case where the first draft of this document (#1667) and PG-LANG (#1666)
differed. PG-LANG won unless the journey showed a real hole.

| # | The journeys said | PG-LANG says | Resolved |
|---|---|---|---|
| 1 | "Ask me ▾: Only the core · Each round · Everything" on the toolbar | **Plan it**, then **Apply** or **Ask me first**; rounds do not gate Start (§6.5, §9.3, §15.5) | PG-LANG; F10 dropped. The three stances map to its two paths plus the step fold (§1 above) |
| 2 | "Assumed" lines with Change | every default is a line of the draft, applied by his press | PG-LANG; F11 dropped |
| 3 | The answer changes the plan at once; the lines light | an answer is one shaping call; its rows wait in the change well for **Apply** | PG-LANG |
| 4 | Verbs "Skip", "Skip the round"; the strip in the question well | **Skip question**, **Skip round**, **Done with <round>**; the strip over the board | PG-LANG; the canvas uses its words |
| 5 | "Shape field", "Apply all / Skip all", per-line Apply | the shaping bar "Change the program", **Shape**; the change well with **Apply** / **Not this**; a per-row **Apply this** only on a lowers-the-bar row | PG-LANG |
| 6 | **Undo** of his own shaped change | Overturn only for what YOLO applied; below YOLO nothing applies without his Apply | PG-LANG; F16 dropped |
| 7 | The ledger line "Shaped by you: 3 changes" | "Changed by the text: n changes"; at YOLO "Shaped: …" under Decided for you | PG-LANG |
| 8 | "Under 20 seconds" and "under 50 ms" as Check requirements | the Measure kind with a `bound` (LANG11); a walk is Your word with `walk` lines | PG-LANG; J1 R3 and J5 R2 are `measure`, J1 R8 has `walk` lines |
| 9 | Dreaming: "no `holdspeak/db/` file" as an every-step Check | `within` bounds the files; outside is a core question | PG-LANG; `within` |
| 10 | Dreaming: a "Sources" field and "Until 07:00" on the automation | the backlog is read by rule; `night 23:30–07:00 · at most 8 steps` | PG-LANG; the sources field is gone |
| 11 | Budget words "38k of 64k", "41k of 64k" as fitting | a step fits when its estimate is at most half the budget (`WORKING_SHARE` 0.5) | PG-LANG; fitting lamps are at most 32k, and 41k is "Too big for qwen · 41k of 32k", split at YOLO |
| 12 | A step too big is parked "Too big for one night" and goes back to the Door | `step_too_big`: Split / Run anyway; YOLO splits | PG-LANG |
| 13 | The digest section "Last night" | "Since last night" | PG-LANG |
| 14 | One dw milestone in HoldSpeak, as a STATUS line | dw is off for HoldSpeak; one PR at Done, opt-in by `delivery dw`, only where the rails are (§8) | PG-LANG; J1 shows it as the variant in a repository with the rails |
| 15 | A call answers a held question by a spoken yes | not in PG-LANG; `docs/calls.md:44` forbids confirming a decision on a call | a real hole: JRN5 (prepared answer, no ruling) is the default; JRN7 waits for the ruling (§15.10) |
| 16 | The night ends with a phone message | the night is not Done, so no "Program is done" reach fires | a real hole: JRN4 |
| 17 | A red main stops nothing | the night stops after two red steps of its own | a real hole: JRN3 |
| 18 | "Add to tonight" | the backlog reads Door tasks with the word "dream" | a real hole on the face (he would type a magic word): JRN2 marks the item |
| 19 | `planner` takes an engine name | §3.2's EBNF says `planner AGENT`; §5.5's own example writes `planner qwen3.8-27b` | the journeys follow §5.5 (an engine of the library); LANG3 should make the EBNF say `planner ENGINE` |
| 20 | The estimate lamp names the budget ("18k of 64k"), the held word the share ("41k of 32k") | the same two forms in §5.4 | kept as PG-LANG writes them; LANG8 should pick one denominator for both |
