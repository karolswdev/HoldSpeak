# Programs: requirements, browse and adjust (PG-REQ)

Owner, 2026-10-31 (remote): "One thing about HoldSpeak programs is that they
are not that clear to browse, adjust, and so on. Not also clear how to add
additional requirements/checks, see how they are met, and so on. I feel like
that's a huge opportunity for HoldSpeak."

Sources: `PROGRAMS-DESIGN-2026-10-28.md` (the engine as built, with its
"Built" section and PG19), `RECIPE.md` (PG1 to PG21), `CANVAS-NOTES-2026-10-28.md`
(direction C, the ledger), `docs/programs.md` (the user doc), the code on
`main` at `2a6ebd02a`. Canvas: `canvases/programs-requirements-2026-10-31.html`
(three directions for the Requirements board, the recommended one marked).
The owner's "go with suggestions" (2026-10-27) pre-approves the recommended
direction; he judges it live on his desk.

## 1. The job

A Program today has one bar for each step, and the bar is the engine's: the
check command's log (`program_verifier.verify_text`,
`holdspeak/services/program_verifier.py:76`), the reviewer's MUST and SHOULD
(`program_runner._review`, `holdspeak/services/program_runner.py:1113`), and
the Control level. He has no place to say "and this must also be true":
"the Programs window at 393 has no clipped text", "`uv run pytest
tests/unit/test_program_rules.py` is green", "no new route skips the
residual set", "I tried it on my desk". He puts such a sentence in a brief
and hopes the agent reads it; nothing checks it, nothing shows it was met.

He also cannot find his way around a Program once it has more than a
screen of history. The Programs list has no search and no filter
(`web/src/desk/programs/ProgramsWindow.tsx:98`, five fixed columns). The
Program window has one flat Checkpoints fold for every step
(`ProgramWindow.tsx:241`). The selected step shows only its Gate fold
(`ProgramWindow.tsx:657`). And a started Program can only append steps:
`plan(replace=True)` refuses once a step started
(`program_service.py:1268`), there is no step edit, no insert, no move.

**A requirement is one sentence of his, on a Program or on a step, with the
way it is proven: a command (check), the reviewer's answer (review), a shot
of a window (shot), or his own press (word). A step is done only when its
check is green and every required requirement is met or waived by him. The
Program window shows each sentence, its state and its evidence; the Programs
list says "4 of 5 met".**

Browse and adjust come with it, because a requirement is only useful if he
can find the step it is on and change the plan when it is unmet.

## 2. What it is not

- Not a test framework. A `check` requirement runs a command the repository
  already has; HoldSpeak writes no test for him.
- Not a second reviewer. The `review` kind is a question in the reviewer's
  brief that the reviewer the step already has answers by name.
- Not an acceptance-criteria editor with fields. One sentence, one kind, at
  most one command or one window. No Given/When/Then, no tags, no weights.
- Not a way for an agent to lower his bar. An agent can propose a
  requirement; only he waives one. The engine never waives.

## 3. The nouns

| He sees | In data | It is |
|---|---|---|
| **Requirement** | `program_requirements` | one sentence of his with a kind, on the Program or on a step; `required` (default on) or not |
| **Kind** | `kind` | how it is proven: **Check** (a command), **Review** (the reviewer answers it), **Shot** (the desk sweep renders a window at a width), **Your word** (he presses Met) |
| **Evidence** | `evidence_json` | what proves the state: the log (check), the reviewer's line (review), the image and the sweep's result (shot), his press (word); always with the commit it was judged on |
| **Every step** | `each_step = 1` on a Program row | a Program requirement copied onto each step; the board says "5 of 6 steps" |
| **The end check** | Program rows with `each_step = 0` | a requirement on the whole Program, judged once after the last step merged, on the base branch |
| **Amendment** | a checkpoint of kind `amend` | a line he adds to a running step's brief, typed to the agent at the next turn boundary |

Words that never appear on a face: acceptance criteria, AC, assertion,
spec, DoD, gate condition, predicate.

## 4. The states and the kinds

### Requirement states

| He sees | In data | Meaning |
|---|---|---|
| **Not yet** | `not_yet` | not judged on the step's current commit (a new one, a changed one, or the commit moved) |
| **Met** | `met` | the evidence says it holds on the commit named in the evidence |
| **Unmet** | `unmet` | the evidence says it does not hold; the builder gets it in its next round |
| **Waived** | `waived` | he waived it, with a line; it no longer gates; it stays on the list, struck through in muted ink |

A requirement that is being judged shows **Checking** as its word (the
wire's `running: true` on `not_yet`); it is not a stored state.

Rules:

- **A state moves on a receipt.** Met and Unmet carry the evidence and the
  commit. A requirement is never Met because an agent said so.
- **The commit moves, the judgement goes.** When the step's head commit
  changes, every Met or Unmet of kind check, shot and review goes back to
  Not yet and is judged again on the new commit. Your word stays as he
  pressed it (decision 4).
- **The bar can go up while a step runs; it comes down only by his Waive.**
  He or an agent (by the level, §6) may add a requirement to a running step;
  only he waives one, and a waive writes his line to the ledger and to the
  handover note.
- **An edit of the sentence resets it.** Changing the text, the kind, the
  command or the window of a Met requirement sets it to Not yet.

### How each kind is proven

| Kind | When it is judged | How | Evidence |
|---|---|---|---|
| **Check** | at CHECK, after the step's check is green, on the same commit, through the same lock | the command runs in the step's worktree with an isolated HOME, to `<worktree>/.tmp/program-check/<step>/<ts>-<R n>.log`, with the engine's header and footer (`program-check: commit`, `tree clean`, `command`, `exit`); the verifier's requirement form reads it (§5) | the log path, the commit, the last result line ("12 passed") |
| **Shot** | at CHECK, after the check kinds | the repository's shot command renders one case at one width. HoldSpeak's own: `DESK_SWEEP_SHOTS=1 uv run pytest -q tests/e2e/test_desk_sweep.py -k "<case>-<width>"` through `scripts/test_lock.py` (the sweep writes the shot to `.tmp/evidence-shots/desk-sweep/`, `tests/e2e/test_desk_sweep.py:1064`). Met = the case is green and the image is there | the image, the case and width, the sweep's result line, the commit |
| **Review** | at REVIEW, in the round the step already has | the reviewer's brief lists each review requirement by its id; the reviewer answers `REQ R3: MET · <one line>` or `REQ R3: UNMET · <what is missing>` | the reviewer's line, its round, the reviewed commit |
| **Your word** | at MERGE (a step) or at the end (the Program) | a Your turn row with **Met** and **Unmet**; Unmet asks for one line and sends it back to the builder | his press, the time, the commit he saw |

A requirement with no way to be proven (a check with no command, a shot in a
repository with no shot command) is a **core question** at every level (the
"no rule" item of the 2026-10-28 design §6); the add row says so before he
adds it.

The kind is guessed by rule from the sentence, never by a model, and he can
change it on the row: text in backticks is a **Check** with that command; a
window name followed by "at 393" or "at 1440" is a **Shot** of that case at
that width; anything else is a **Review**. **Your word** is only his choice.

## 5. The gate, amended

The 2026-10-28 gate stands (a verified log, not an exit code). It gains one
clause:

> A step is done when its check is green **and every required requirement on
> it is Met or Waived**. A Program is done when every step is done **and every
> required end-check requirement is Met or Waived**.

The verifier gets a requirement form,
`program_verifier.verify_requirement_log(path, expect=None)`, for commands
that are not the quick check (they print no `== section` lines and no
`QUICK CHECK GREEN`):

1. the log names the commit and the worktree was clean at the start (as
   now);
2. the engine's own footer `program-check: exit 0` is there. The engine
   wrote it from its own process, so it is the engine's receipt, not the
   agent's claim;
3. no line is red by the verifier's existing `_red_line` rule (`FAILED`,
   `ERROR`, "n failed" with n > 0);
4. when the requirement names `expect` (a regular expression, for example
   `\b12 passed\b`), a line matches it.

No log path, not Met. The check kind's log opens with **Open log**, as the
step's own check does.

Where the stations light: Check and Shot are part of CHECK (the station
stays lit until they are judged); Review is part of REVIEW; Your word is
part of MERGE. The station track does not grow a seventh station.

## 6. The engine

### Where requirements run in the tick

`program_runner._after_check` (`program_runner.py:1052`) gains one step
before the review: judge the step's check and shot requirements on
`checked_commit`. A red one is a red check round (the same rounds, the log
tail of the requirement goes to the builder as its next prompt). The review
(`_attach_review`, `program_runner.py:1076`) adds the review requirements to
the reviewer's acceptance lines (today one line, "Name each finding MUST
(required) or SHOULD", `program_runner.py:1088`). `_review` parses the
`REQ` lines: an UNMET answer becomes a REQUIRED finding with
`requirement_id`, so the round machinery that exists sends it back; a
missing answer is the `requirement_unanswered` kind below.
`pass_gate` (`program_runner.py:1205`) opens the PR as now. The merge
(`_pr`, the `decide(..., "merge", …)` call at `program_runner.py:1345`)
gains the fact `requirements_met` (every required requirement Met or
Waived); a Your word requirement that is Not yet holds the merge at every
level and puts a Your turn row up.

The end check: when every step is finished, before `program_done`, the
engine makes one scratch worktree at the base branch head
(`hs-program-<id>-end`), judges the Program's own check and shot
requirements there, asks the Program's reviewer the review ones over the
diff `<base at start>..<base now>`, and puts his word ones in Your turn.

### The builder's brief

`program_brief.compose` (`holdspeak/services/program_brief.py:60`) gains one
section after "This step:", before "The rules and the proof":

```
What must be true (the owner's requirements; HoldSpeak checks each one):
- R2 · The People routes take no lock on the event loop · the reviewer judges it
- R3 · `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green · HoldSpeak runs it on your commit
- R5 · The People window at 393 has no clipped text · the desk sweep renders people-393
- R7 · The owner tried it on his desk · the owner says it
For the whole program (judged after the last step): R1 · …
```

and one acceptance line: "Do not claim a requirement is met. HoldSpeak
judges each one on your commit." An amendment he adds while the step runs
is appended to `.holdspeak/brief.md` under "Added by the owner at 14:02"
and typed at the next turn boundary as "The owner on step 4: …" (never into
a blocked agent; the 2026-10-28 rule).

### The rules by Control level

New kinds in `program_rules.KINDS` (`holdspeak/services/program_rules.py:30`):
`requirement_red`, `requirement_unmet`, `requirement_unanswered`,
`requirement_left`, `requirement_proposed`, `requirement_unprovable`,
`step_amend`, `step_change`. Each row has its test at each level, as the
§6 table of 2026-10-28 has.

| Decision | Secure | Normal | YOLO |
|---|---|---|---|
| judge a check or shot requirement on the step's commit, judge again when the commit moves | engine | engine | engine |
| a check or shot requirement is red (`requirement_red`) | the log tail back to the builder (a check round), round 2, then him | same | round 2, round 3, then him |
| the reviewer answers UNMET (`requirement_unmet`) | a REQUIRED finding back to the builder, round 2, then him | same | round 2, round 3, then him |
| the reviewer gave no answer for a requirement (`requirement_unanswered`) | him | engine asks the same reviewer once more in the same round, then him | same as Normal |
| a Your word requirement | him | him | him |
| a requirement still unmet after the rounds (`requirement_left`) | him: **Waive** / **Send back** | engine parks the step, the rest goes on, one row to him (Waive / Send back) | engine tries one smaller brief that names the requirement, then parks the step and one row to him |
| an agent proposes a requirement (`requirement_proposed`) | him: **Add** / **Skip** | him: Add / Skip | engine adds it and says so under Decided for you (Overturn) |
| a requirement with no way to prove it (`requirement_unprovable`) | him (core) | him (core) | him (core) |
| waive a requirement | him | him | him |
| a requirement added after the step's gate passed | engine judges it on the PR head; Unmet: him (Waive / Send back) | same | same |
| an orchestrating agent edits, inserts or moves a planned step (`step_change`) | him: **Apply** / **Skip** | him: Apply / Skip | engine applies it and says so (Overturn while the step is still planned) |
| an orchestrating agent amends a running step's brief (`step_amend`) | him: **Send** / **Skip** | him: Send / Skip | engine sends it at the turn boundary and says so |
| his own edit, insert, move or amendment | applied at once | applied at once | applied at once |
| a core question | him | him | him |

**Send back** on an unmet requirement types one line to the builder ("R5 is
unmet: <the evidence line>. <his line>") and starts a new round, even after
the rounds ran out (his press gives one more round). **Waive** asks for one
line ("why"); the line is the evidence.

Every judgement is a checkpoint line on the step with `kind = requirement`,
`by = engine | owner` and the requirement id in `undo_json`, so the step's
ledger and the kernel journal carry it. A Waive is an owner decision row; an
engine park after `requirement_left` is an overturnable engine decision, as
`step_failed` is now.

## 7. Browse

### The Programs list

- **Find a program**: a `StringGadget type="search"` with its mic in the
  toolbar (the Terminals window's species, `TerminalsCore.tsx:439`). It
  matches every word against the row's `search_words` (title, goal, project,
  person, step titles, PR numbers as "#1591", template name). The service
  composes `search_words`; the face matches locally, so a keystroke costs no
  request. `program.list` takes the same `q`.
- **Project ▾** and **Person ▾**: `WorkMenu`s that list only the projects
  and persons that have a Program (no item with zero). One choice each;
  **Any project** / **Anyone** clear it.
- **Group: State ▾** (State · Project), at the toolbar's right. By state
  keeps today's bands (Your turn, Running, Drafting, Done, Parked). By
  project bands by project name, "No project" last; inside a band, the worst
  state first, then the most recently changed.
- A new column **Met** between Steps and In state: "4 of 5 met" over the
  Program's required requirements (the end-check ones and every step's).
  Each step's copy of an every-step requirement counts once, and each of
  the Program's own once (a running Program of six steps with two
  every-step requirements, five of the steps' own and one of its own counts
  18). It is ok ink when all are met; an ember dot before it when one is
  Unmet or waits on his word; "7 requirements" while none is judged yet
  (the zero law: never "0 of 7 met"); empty when the Program has no
  requirement. Waived counts as met and the hover title says "1 waived".
- The status bar, when a filter is on: "3 of 12 programs · HoldSpeak ·
  Alice", then the counts that are not zero for the rows shown.

### The Program window

- **The Requirements board** (§9, direction A) sits under the Your turn
  well and above the steps. It holds the Program's own requirements, the
  every-step ones, and a summary row per step that has its own ("Step 4 ·
  2 of 3 met"). It is a fold: open when one is Unmet or waits on his word,
  closed with the token "5 of 5 met" when all are met.
- **The board** gains the **Met** column on each step row: "2 of 3" with the
  state's tone; "3 to meet" while none of its three is met; empty when the
  step has none.
- **The step fold** replaces the Gate fold. Selecting a step opens
  "Step 3 · Projections off the loop" with a `FilterTokens` strip: **Brief**
  · **Requirements** · **Gate** · **Findings** · **Handoffs** · **Ledger**.
  A token with nothing behind it is not drawn (no Findings token on a step
  with no findings). The first token shown is the one his eye needs: Gate
  when the check is red, Requirements when one is Unmet, Findings when one
  waits on him, else Brief. Each section is today's piece where one exists:
  Gate is `GateFold`'s list (`GateFold.tsx:38`), Handoffs is the handoff
  lines with View brief, Ledger is the step's own checkpoints.
- **The ledger, folded per step.** The window's Checkpoints fold becomes
  **Ledger**: one sub-fold per step ("Step 3 · 14 lines · last 18:40"), the
  Program's own lines (start, park, plan, the end check) first, newest step
  activity on top. A step's sub-fold opens to the same rows the step fold's
  Ledger token shows. Decided for you stays its own fold.

## 8. Adjust while running

### What he can change, by the step's state

| Field | Planned, Ready | Started (Briefed to Findings) | PR open, Merge? | Merged, Done, Parked |
|---|---|---|---|---|
| Title | edit | edit (the branch keeps its name) | edit | edit |
| Brief | edit | **Amend**: a line added and typed at the next turn boundary; the first brief stays as it was | frozen: Send back with a line instead | frozen |
| Owns | edit | frozen | frozen | frozen |
| After | edit | frozen | frozen | frozen |
| Effort | edit | frozen | frozen | frozen |
| Agent (first) | edit | frozen: **Hand off** moves it (owner, `program.handoff`) | frozen | frozen |
| Agent (then, at a limit) | edit | edit | frozen | frozen |
| Race | edit | frozen | frozen | frozen |
| Check gate | edit | frozen | frozen | frozen |
| Review gate | edit | none → agent until the PR opens; agent → none refused | frozen | frozen |
| Review depth | edit | edit until the review starts | frozen | frozen |
| Merge gate | edit | edit (level ↔ owner) | edit (level ↔ owner) | frozen |
| Requirements | add, edit, waive | add, edit, waive | add (judged on the PR head), waive | frozen: add it to the Program instead |
| Position | move, insert before | fixed | fixed | fixed |
| For a person, May call | edit | edit | edit | frozen |

Why each is frozen, in the words the face uses in a hover title:

- **"The agent has read it."** Brief, owns, after, effort and race are in the
  brief file and in the sibling briefs ("theirs, do not touch",
  `program_brief.theirs`). Changing them in the record would make the record
  lie about what the agent was told. The amendment adds; it does not rewrite.
- **"The worktree and the agent are set."** The first agent, effort and the
  race shape the hand (`AgentHandService.hand`); a change is a handoff,
  which exists.
- **"The bar does not come down while it runs."** The check gate and the
  review gate can only go up; a lower bar is his Waive with a line.
- **"It is merged."** History is not edited.

### Insert and move

- **Insert before**: on a selected Planned or Ready step, **Insert before**
  adds a new Planned step at its place. The new step comes after what the
  step it precedes came after, and that step now also comes after the new
  one (a `CheckGadget` "5 waits", default on). Insert before a
  started step is refused: "Step 4 started. Add the step after it."
- **Move up / Move down** on a selected Planned or Ready step (and
  `Alt+↑ / Alt+↓`). A step does not move above a step it comes after; the
  refusal names it. Order is reading order and the order the dispatcher
  hands ready steps (`program_runner._dispatch`, `program_runner.py:379`).
- **Numbers follow the order** (decision 6). Insert and move renumber every
  step by position in one transaction and rewrite every `after` list
  through the same map. A started step whose number changes keeps its
  branch name and gets one checkpoint line: "Step 4 is now step 5".

All three go through one service verb, `ProgramService.change_step`, under
the Program's lock, with one checkpoint and one `program_changed` frame.

## 9. The faces

Built in the kit, nothing hand-rolled (UX-CANON §B): `StringGadget`,
`CycleGadget`, `CheckGadget`, `FilterTokens`, `FoldGadget`, `ListView`,
`DotWord`, `StateChip`, `Token`, `SurfaceCode`, `StatusBar`, `WorkMenu`,
library `Button`. No modal: every add, edit, waive and amendment is a row
that unfolds in place.

### The Requirements board: three directions (canvas)

- **A · The checklist (recommended).** One 32 px ListView row per
  requirement, grouped: The program (judged at the end), Every step, then
  one group per step that has its own. The row: id (R3) · state dot and
  word · the sentence · kind Token · scope or "5 of 6 steps" with six small
  dots (one per step, the station-track dots' species) · evidence verb
  (**Open log**, **Open shot**, the reviewer's line in muted words, "You ·
  09:12") · the verbs his state allows (**Met** / **Unmet** for his word;
  **Waive** / **Send back** when Unmet). The last row is **Add
  requirement**.
- **B · The matrix.** Steps as rows, the every-step requirements as
  columns (R1, R2, R3), a dot per cell, a last column "own: 2 of 3". The
  sentences live in the column head's hover title and in a legend line.
  The fastest scan of "which step fails which rule"; the sentences, his
  words, are hidden, and a step's own requirements are only a count.
- **C · In the rows.** Each step row on the board gets its requirements as
  indented child rows (the race contenders' species). The Program's own sit
  in a strip above the board. Everything in one list; twenty steps with
  three requirements each are eighty rows, and the ledger's one-screen
  proof (CANVAS-NOTES 2026-10-28) is gone.

**Why A.** He asked to see how his requirements are met. A shows his
sentences in his words, each with its proof one press away, and keeps the
steps board at one 32 px row per step (the Met column carries the count).
B is the better picture for twenty steps and three every-step rules, and it
is drawn as A's closed state for the Every step group: a press on "5 of 6
steps" shows the six dots with the step numbers.

### Row grammar

**Programs list row** (32 px; 1440):
`sprite · title · StateChip · "2 of 6 steps" · "4 of 5 met" · in state · "last checkpoint"`.
At 393 (60 px, two lines): `sprite · title · StateChip` /
`2 of 6 steps · 4 of 5 met · 14 min`.

**Requirement row** (32 px):
`R3 · DotWord(state) · sentence · Token(kind) · scope · evidence · verbs`.
State tones: Met ok, Unmet fail, Not yet idle (hollow dot), Checking info
(the lit dot breathes), waits on his word ask (ember), Waived muted with the
sentence struck through. The sentence is 13/500 ink and ellipsis; its full
text is the hover title and the row's selection opens it in a two-line well
under the row with **Edit** (an `EditInPlace` with mic). At 393 the row is
two lines: `R3 · DotWord · sentence` / `Token · evidence · verbs`, plated
verbs 44 px.

**Add requirement row** (36 px, the Drafting row's species):
`StringGadget (mic) "Add a requirement" · CycleGadget kind (Check · Review ·
Shot · Your word, set by the rule as he types) · CycleGadget scope (The
program · Every step · Step 3) · the kind's one field · CheckGadget Required ·
Button Add`. The kind's field: Check shows a mono `StringGadget` for the
command (filled from the backticks); Shot shows two `CycleGadget`s, the case
(the apps of `applications.ts` and the Program's step windows) and the width
(393 · 1440); Review and Your word show nothing more. When the kind cannot
be proven here (a Shot in a repository with no shot command), the Add verb
is withheld and the row's DotWord says "No shot command in this repository".

**Step row on the board** (32 px, direction C of 2026-10-28 plus one
column): `n · title (after 4, 5) · dots and word · Met "2 of 3" · agent ·
time · "checkpoint" · Open lane`.

**Step fold** head: `Step 3 · Projections off the loop` · `FilterTokens`
(Brief · Requirements · Gate · Findings · Handoffs · Ledger) · at the right,
for a Planned step: **Move up** · **Move down** · **Insert before**; for a
started step: **Amend brief** · **Hand off**. The Brief section of a
Planned step is its fields (the Drafting gadgets); of a started step, the
brief as text with its amendments under it, and a muted DotWord "Frozen ·
the agent has read it".

**Ledger sub-fold** head: `Step 3 · Projections off the loop · 14 lines ·
last 18:40`; rows as today (by, line, time; Start from here where a ref
is).

### Your turn rows (new kinds)

- `requirement_word`: "Step 3 · Projections off the loop: R7 · You tried
  it on your desk?" · **Met** · **Unmet** · Open shot when the step has a
  shot.
- `requirement_left`: "Step 5 · Projects routes: R4 is unmet after 2
  rounds · <evidence line>" · **Send back** · **Waive**.
- `requirement_proposed`: "Codex proposes R9 on step 4: <sentence>" ·
  **Add** · **Skip**.
- `step_change` / `step_amend` (from an orchestrating agent): "The
  orchestrator moves step 6 before step 5" · **Apply** · **Skip**.

Unmet and his-word requirements are also Needs you rows (`program_items`,
the Program's title as the group; due word "Now").

### Words (for `stateWords` and the copy guard)

Requirement: Not yet, Checking, Met, Unmet, Waived, Waits for you. Kinds:
Check, Review, Shot, Your word. Scope: The program, Every step, Step n.
Counts: "4 of 5 met", "2 of 3", "5 of 6 steps". Verbs: Add requirement,
Add, Edit, Met, Unmet, Waive, Send back, Open log, Open shot, Amend brief,
Insert before, Move up, Move down, Apply, Skip, Find a program, Project ▾,
Person ▾, Group: State ▾. Frozen titles: "The agent has read it", "The
worktree and the agent are set", "The bar does not come down while it
runs", "It is merged". The Agent picker keeps "Agent: … ▾" (the Engines name
guard, 2026-10-28 Built).

### At 393

The Programs list toolbar keeps New program and Find; Templates, Project,
Person and Group fold into **More ▾**. The Program window's Requirements
board is a fold above the steps with its token ("4 of 5 met"); the step
fold opens full screen with the FilterTokens strip scrolling sideways; plated
verbs own 44 × 44.

### Delight

When the last required requirement of a step goes Met, the Met cell draws
its count in ok ink and the dot breathes once (the 2.4 s ring, once, not a
loop; none under reduced motion). A Program whose every requirement is met
says "Done · 9 of 9 met" in its Done word. The shot's thumbnail (240 px
wide) sits in the evidence well of a Shot row, so "how it is met" is a
picture, not a word.

## 10. Templates ship requirements

`program_templates.TEMPLATES` (`holdspeak/program_templates.py:26`) gains a
`requirements` list per template (`{text, kind, each_step, required}`):

| Template | Every step | The program |
|---|---|---|
| **Fast cycle** | Review: "The change does only what its brief says." | none |
| **Build and review** | Review: "The change does only what its brief says." · Review: "Each new behaviour has a test." | none |
| **Race** | Review: "The change does only what its brief says." | none |
| **Overnight on the home box** | the two of Build and review | none |
| **From the desk** | Review: "The change does what its action asks: <the action's title>" (one per step, from the step's origin) | none |

A repository adds its own defaults in `.holdspeak/program.json`
(`"requirements": [...]`, and `"shot": "<command with {case} {width}>"` for
the shot kind). HoldSpeak's own file names the sweep shot command and one
every-step Check: `uv run python scripts/ux_canon_scan.py`. A template's
requirements are `by = template`; he can edit or waive each.

## 11. The contract for the lanes

### Table (`holdspeak/db/schema.py`, minimal migration: one table, one index; SCHEMA_VERSION 88, additive)

```
program_requirements(
  id TEXT PRIMARY KEY,
  program_id TEXT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  step_id TEXT,                         -- NULL: the Program's own (the end check, or the every-step parent)
  ordinal INTEGER NOT NULL,             -- R n, unique in the Program, never reused
  text TEXT NOT NULL,
  kind TEXT NOT NULL,                   -- check | review | shot | word
  required INTEGER NOT NULL DEFAULT 1,
  spec_json TEXT NOT NULL DEFAULT '{}', -- check: {command, expect?}; shot: {case, width}
  each_step INTEGER NOT NULL DEFAULT 0, -- a Program row copied to each step
  parent_id TEXT,                       -- the every-step row a step's copy came from
  state TEXT NOT NULL DEFAULT 'not_yet',-- not_yet | met | unmet | waived
  judged_commit TEXT,
  evidence_json TEXT NOT NULL DEFAULT '{}', -- {kind: log|finding|shot|press, ref, line, by, at}
  waived_reason TEXT,
  rounds INTEGER NOT NULL DEFAULT 0,
  by_kind TEXT NOT NULL DEFAULT 'owner',-- owner | agent | template
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  judged_at TEXT
)
CREATE INDEX idx_program_requirements_program ON program_requirements(program_id, step_id, ordinal)
```

No column on `program_steps`: a step's amendments are checkpoint rows of
kind `amend`; the step's editable fields are computed. The schema snapshot
(`tests/fixtures/db_schema_canonical.txt`) is regenerated.

### REST (`holdspeak/web/routes/programs.py`, every handler through `run_in_threadpool`)

```
GET    /api/programs?q=&project_id=&person_id=     list (filters are the service's; group is the face's)
POST   /api/programs/{id}/plan                     + before: <step_id> (insert before; steps are Planned)
PATCH  /api/programs/{id}/steps/{sid}              change a step: the fields of §8 that are not frozen; before: <step_id> moves it; 409 step_frozen names the field and the reason
POST   /api/programs/{id}/steps/{sid}/amend        {line}: an amendment to a started step's brief
POST   /api/programs/{id}/requirements             {text, kind?, step_id?, each_step?, required?, spec?}; kind omitted: the rule guesses
PATCH  /api/programs/{id}/requirements/{rid}       {text?, kind?, required?, spec?}: an edit (a Met one goes to Not yet)
POST   /api/programs/{id}/requirements/{rid}/decide {choice: met|unmet|waive|send_back|add|skip, line?}  owner only
GET    /api/programs/{id}/requirements/{rid}/evidence the log text or the shot image (local hub only)
```

Each new route gets its residual-set entry, an aware clock (`local_now`), and
the api-surface regen.

### MCP (`holdspeak/mcp/families/program.py`, through `ProgramService`; palette CONDUCTOR)

| Tool | Does | Who |
|---|---|---|
| `program.require` | add a requirement (`text`, `kind?`, `step_id?`, `each_step?`, `required?`, `spec?`), or change one (`requirement_id` + fields) | owner: at once; an orchestrating agent or a step's own agent: by the level (§6 `requirement_proposed`) |
| `program.decide` | + kind `requirement` (`requirement_id`, choice `met`, `unmet`, `waive`, `send_back`), + kinds `requirement_proposed` (add, skip), `step_change` (apply, skip), `step_amend` (send, skip) | owner only (AUTHORITY, as now) |
| `program.step_update` | change a step (the §8 fields), `before` to move it | owner: at once; an orchestrating agent: by the level (`step_change`) |
| `program.amend` | add a line to a started step's brief | owner: at once; an orchestrating agent: by the level (`step_amend`) |
| `program.plan` | + `before: <step_id>` | as now |
| `program.list` | + `q`, `project_id`, `person_id` | anyone |
| `program.get` | carries the requirements (below) | anyone |

The judgement is not a tool: no agent can call "met". A step's own agent
can read its requirements (`program.get`) and propose one (`program.require`).
`tool_authority.py` gets `program.require`, `program.step_update` and
`program.amend` as WORK; `decide` stays AUTHORITY. The MCP `gate_merge`
spelling note of `docs/programs.md` holds for `program.step_update`.

### The wire

On a Program (`ProgramService._wire`, `program_service.py:857`):

```
requirements: [Requirement]            # the Program's own and the every-step parents, in ordinal order
requirements_met: {met, total, unmet, waived, his}   # required ones, Program-wide; omitted when total is 0
```

On a Program summary (`_summary`, `program_service.py:724`): the same
`requirements_met`, plus `project: {id, name} | null`, `for_person: {id,
name} | null`, `search_words: string`.

On a Step (`step_wire`, `program_service.py:767`):

```
requirements: [Requirement]            # this step's own and its every-step copies
requirements_met: {met, total, unmet, waived, his}
editable: ["title", "amend", "runs_on_then", "gate_merge", "requirements", ...]
frozen: {"brief": "The agent has read it", "after": "The agent has read it", ...}
amendments: [{at, by, line, sent_at}]
```

A Requirement:

```
{id, ordinal, label: "R3", program_id, step_id, scope: "program" | "every_step" | "step",
 text, kind, kind_word: "Check" | "Review" | "Shot" | "Your word", required,
 spec: {command?, expect?, case?, width?}, parent_id, steps: [{step_id, ordinal, state}]  # every-step parents only
 state, state_word, running, judged_commit, stale,
 evidence: {kind, ref, line, by, at, url}, waived_reason, rounds, by, choices: [...]}
```

Your turn items (`your_turn`, `program_service.py:321`) gain the kinds
`requirement_word`, `requirement_left`, `requirement_proposed`,
`step_change`, `step_amend`, each with `requirement_id` where one applies.

### Frame

`program_changed` (`program_service.py:2162`) gains `requirement_id?` and
`requirements_met?`; `desk_changed("program", id, verb)` gains the verbs
`require`, `judge`, `waive`, `step`, `amend`, `move`. The Programs window,
the Program window, the Dock lamp and Needs you consume them as now.

### Fixtures

The hub lane records, through `scripts/record_program_fixtures.py` from the
rig: `program.requirements.json` (one of each kind and state, an every-step
parent with six copies, a waived one), `program.requirement_word.json`,
`program.adjust.json` (a Planned step moved, one inserted, a started step
amended), `programs.filtered.list.json` (`q`, project, person).

## 12. The slices (lanes HUB, FACES and DOCS on one branch)

Branch `lane/programs-requirements-20261031`. PG-REQ-HUB first (the
contract and the recorded fixtures), then FACES and DOCS in parallel on the
fixtures, one quick check, one PR, as the fast cycle says.

| Slice | Lane | What | Done when (tier) |
|---|---|---|---|
| REQ1 | HUB | the table, `holdspeak/db/programs.py` rows, `ProgramService.require` / edit / waive, the wire on Program, Step and summary | a requirement of each kind is stored, read on the wire, counted in `requirements_met`; an edit of a Met one is Not yet (T1 `tests/unit/test_program_requirements.py`) |
| REQ2 | HUB | the proof: check and shot kinds at CHECK, `verify_requirement_log`, the shot command from `.holdspeak/program.json`, staleness on a new commit | a red requirement log is a check round; a green one is Met with its log; a new head commit sets Not yet (T1 `test_program_verifier.py`, the rig) |
| REQ3 | HUB | the reviewer: the REQ lines in the reviewer's acceptance, the parse, UNMET as a REQUIRED finding with `requirement_id`, the one re-ask | the fake reviewer's `REQ R2: UNMET` sends a round back; `MET` sets Met with the line; no answer re-asks once (T1, the rig) |
| REQ4 | HUB | the gate and the rules: `requirements_met` in the merge decision, Your word, `requirement_left` by level, the end check | every row of §6 at each level (T1 `test_program_rules.py`); the rig Program of §15 runs end to end |
| REQ5 | HUB | the builder's brief section and the acceptance line; amendments in `.holdspeak/brief.md` | `test_the_brief_lists_the_requirements_and_how_each_is_proven` (T1) |
| REQ6 | HUB | templates' requirements and the repository's defaults | each template plans its every-step requirements (T1) |
| REQ7 | HUB | adjust: `change_step` (edit, insert before, move, renumber, `after` remap), `amend`, the frozen table | each frozen field refuses with its reason; a move renumbers and remaps `after`; an amend waits for a turn boundary (T1 `test_program_adjust.py`) |
| REQ8 | HUB | REST, MCP, the frame, the list filters, `search_words`, recorded fixtures | `tests/integration/test_desk_programs.py` covers each new route; the MCP family test lists the tools |
| REQ9 | FACES | the Programs list: Find, Project ▾, Person ▾, Group, the Met column, the filtered status bar | `programs.app.test.tsx` from `programs.filtered.list.json`: a typed word narrows the rows; By project bands; no zero count (T2) |
| REQ10 | FACES | the Requirements board (direction A), the Add requirement row, the Your turn kinds, Needs you rows | each state drawn from `program.requirements.json`; Met, Waive, Send back press through to the rendered row (T2) |
| REQ11 | FACES | the step fold (FilterTokens), the per-step Ledger, the board's Met column, adjust in place (fields, Move, Insert before, Amend brief) | from `program.adjust.json`; a frozen field draws as text with its title (T2); sweep cases `surface-programs` and `program` at 1440 and 393 stay green (T3) |
| REQ12 | FACES | the shot pullout (`pullout:program-shot:<rid>`, an image frame) and the evidence thumbnail | the thumbnail renders from the evidence route (T2); `Alt+↑/↓` moves a step (T4, one case) |
| REQ13 | DOCS | `docs/programs.md` (Requirements, Find and filter, Change a running program; ASD-STE100), `agent/skills/holdspeak-programs/SKILL.md` (how an agent reads and proposes requirements), `RECIPE.md` (PG-REQ slices), `TRACKER.md`, `UX-CANON.md` (a line under Shipped), `pm/STATUS.md`, the api-surface and OpenAPI regen | `scripts/gen_docs.sh` clean |

## 13. What he presses

1. In the Programs window he types "stalling" in **Find a program**; one
   row is left, "The hub stops stalling · 2 of 6 steps · 4 of 5 met".
2. He opens it. The Requirements board is open because R4 is Unmet: "R4 ·
   Unmet · No new route skips the residual set · Review · Step 5 · the
   reviewer: 'projects.py adds /api/projects/{id}/fold with no entry'".
   He presses **Send back**.
3. In the Add requirement row he types "The People window at 393 has no
   clipped text"; the kind turns to **Shot**, the case to `people`, the
   width to 393. Scope **Step 4**. **Add**. Step 4 is working; the
   requirement is in its brief at the next turn boundary and is judged when
   step 4 reaches CHECK.
4. He selects step 6 (Planned), presses **Insert before**, types the title
   "The loop watch", and step 7 (was 6) now waits for it.
5. Step 3 reaches Merge? at Normal with R7 "I tried it on my desk" (Your
   word): its Your turn row has **Met** and **Unmet**. He tries it, presses
   **Met**, and the engine merges.

## 14. Decisions for the owner (defaults chosen; say if another is wanted)

**Ruled 2026-10-31 (owner, remote): "All defaults approved." Every default below stands as written; a lane builds it without a further gate.**

1. **Your word holds the merge at every level, YOLO too.** An overnight
   Program with a Your word requirement on a step merges that step when he
   presses Met in the morning; the other steps go on. Default: hold. The
   other choice: YOLO merges and asks his word after, and an Unmet word
   makes a revert step.
2. **The Program's own requirements gate Done, not each merge.** They are
   judged once, after the last step merged, on the base branch. "Every step"
   is a separate scope that copies the requirement to each step's gate.
   Default: as written.
3. **A requirement still unmet after the rounds is a failed step.** Secure
   asks him; Normal parks the step and goes on with one row to him; YOLO
   tries one smaller brief first. Default: as the failed step does today.
4. **A Met requirement goes back to Not yet when the step's commit moves**
   (check, shot, review). His word stays Met. Default: as written.
5. **The kind is guessed by rule** (backticks: Check; a window "at 393" or
   "at 1440": Shot; else Review), never by a model; he changes it on the
   row. Default: on.
6. **Numbers follow the order.** Insert and move renumber the steps; a
   started step keeps its branch name and gets "Step 4 is now step 5".
   The other choice: numbers never change and an inserted step is "4a".
   Default: renumber.
7. **Agents propose, only he waives.** A step's agent and an orchestrating
   agent may propose a requirement (YOLO adds it, the others ask him); no
   agent and no rule ever waives one. Default: as written.
8. **Every template ships "The change does only what its brief says."** on
   every step, as a Review requirement. Default: on.

## 15. How we know it worked

- The hub tier: a rig Program of three steps with one requirement of each
  kind. Step 1's Check requirement is red once (a fake command), goes back,
  is Met on round 2 with its log. Step 2's fake reviewer answers `REQ R2:
  UNMET`, the builder gets it, the second review answers MET. Step 3's Your
  word holds the merge at Normal; `program.decide requirement met` merges
  it. An Unmet one after the rounds at Normal parks the step and the rest
  goes on. A new commit on a Met step sets Not yet. The end check runs on
  the base branch and puts the Program's own word requirement in Your turn.
- Adjust: a Planned step moves and every `after` follows; insert before a
  started step refuses; every frozen field refuses with its reason; an
  amendment is typed only at a turn boundary.
- The faces tier: `programs.app.test.tsx` draws every requirement state and
  presses Met, Waive and Send back through to the rendered row, from
  recorded hub answers; the sweep stays green at 1440 and 393.
- On his desk: he re-creates "The hub stops stalling" with the requirement
  "The Programs window at 393 has no clipped text" (Shot) and sees it Met
  with its picture, and "4 of 5 met" in the Programs list.
- Astra's post-merge review finds no Met without evidence and no waive
  without his line.

## 16. What this design could not establish

- **Where an image opens.** `web/src/desk/pullouts/registry.ts` has no
  image pullout today (a search for "image" and ".png" found none), so
  REQ12 adds `pullout:program-shot:<rid>`. If the faces lane finds an image
  viewer that exists, it uses that one instead.
- **The shot command outside HoldSpeak.** Only HoldSpeak's sweep is known;
  another repository needs its own `shot` command in `.holdspeak/program.json`,
  or the Shot kind is withheld there.
- **The sweep's case ids for a step's window.** The cases come from
  `applications.ts` and the sweep's own list (`tests/e2e/test_desk_sweep.py`,
  for example `("program", "pullout:program:{program}", None)` at line 272);
  a Shot of a window the sweep has no case for cannot be added. Not verified
  for every window.
- **Whether a reviewer harness writes the REQ lines reliably.** The parse is
  strict; the one re-ask is the fallback. The rate at which Codex, Claude
  Code and pi on qwen answer every REQ line is not measured.
- **The cost of the end check.** One more worktree and one more check run
  per Program; the time is not measured.
