---
name: holdspeak-programs
description: Use when you orchestrate a goal on the owner's desk as a HoldSpeak Program over MCP (create, plan, start, follow), or when you are the agent of one Program step. Not for changing the Programs engine's own code.
---

# holdspeak-programs

A Program is a goal cut into steps. HoldSpeak hands each step to an agent
in its own worktree, runs the check, starts the review, opens the PR and
merges by the Program's control level (Secure, Normal, YOLO). You drive
the record; the engine drives the agents. Read first:

- `docs/programs.md` (the user doc: states, the control ladder, core questions)
- `docs/internal/betterment/programs/PROGRAMS-DESIGN-2026-10-28.md` (§4 states, §6 rules, §7 tools, "Built")
- `holdspeak/mcp/families/program.py` (the tool schemas)
- `docs/internal/betterment/programs/PROGRAMS-REQUIREMENTS-2026-10-31.md` (requirements, browse, adjust)
- `docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md` (the Program text, shaping, planning, rounds; the code in `holdspeak/services/program_text.py` wins where they differ)

## Drive a Program (you orchestrate)

1. `program.create` with `title`, `goal` (the owner's words), `repository`
   (a local git folder) or `project_id`, `base_branch`, and a `template`
   (`fast-cycle`, `build-and-review`, `race`, `from-the-desk`,
   `overnight`, `dreaming`, `audit`). Leave `control` unset: it takes the
   desk's Control mode. You cannot set a control wider than the one you run
   under: `control_wider` ("Refused: a program runs no wider than what made
   it"). Ask the owner. The Program is in Drafting.
2. `program.plan` with `steps` and `size: "auto"`. Each step: `title`,
   `brief`, `owns` (the files or folders it alone may change), `after`
   (step numbers it waits for). The rule sets each step's effort. Give
   steps that touch the same files an `after` order; two steps never own
   one file.
3. `program.start`. Only the owner, or the agent that made the Program, may
   start, park, plan or change it.
4. `program.get` to follow it: each step's state, agent, check, review,
   PR, and `your_turn` (what waits on the owner). The handover note
   `program-<id>` ("Program: <title>") says the same in prose; read it
   first after a break.
5. Tell the owner what waits on him. Do not wait in a loop on a step: the
   engine ticks every 30 s, after each press, and about 1 s after a step's
   agent ends its turn.

## Size and the night (PG-LANG LANG8, LANG12)

- A step whose size is over half its budget is not handed: it is held
  "Too big for qwen · 41k of 32k". At YOLO the engine splits it (Decided for
  you); at Secure and Normal the split is a `step_change` proposal (Apply
  splits, Skip runs it as it is). Keep steps small: one concern, at most
  three owned files.
- A Program with `night` hands steps only inside its window ("sleeps until
  23:30"), at most `at most` a night. `program.add_to_night` (`kind`
  `action`, `note` with `line`, or `program_step`; `item_id`) puts an item in
  tonight's Program; an agent's add lands only at YOLO. Do not put a big
  task there: the night planner cuts each item into one small step inside
  `within`.

## Read and write the Program text

`program.text` (by `program_id` or `name`) returns the Program as text, one
statement per line, with `revision`. Read `docs/programs.md` "The Program
text" for the grammar. Keep these rules:

- Lamps (two spaces, `#`, the rest of the line) are state. The hub never
  reads them back; do not write them and do not count on them.
- `>` lines are the owner's words. Keep them byte for byte. Never put your
  own words on a `>` line as his.
- A new step is `step +`, a new requirement `R+`; the hub gives the numbers.
  Under a started step, add a brief line with `+ <line>`; do not rewrite
  its `>` brief.
- To change the Program, send the WHOLE changed text to
  `program.text_apply` with `base` set to the text you read. The default is
  `dry_run: true`: it writes nothing and returns `changes` (each row: `op`,
  `where`, `field`, `before`, `after`, `verdict`, `code`, `reason`,
  `lowers_bar`) and `allowed_text` (your text with each refused change put
  back). Read the rows first. Then apply with `dry_run: false`. It applies
  only when no row is `refused` or `conflict`; send `allowed_text` to
  apply the rest.
- A `conflict` row means the Program changed after you read it: read
  `program.text` again and redo your change on the new text.
- `program.shape` (one sentence) and `program.plan_draft` (a goal) return
  the same rows from one engine call and write nothing. Apply their
  `proposed_text` or `allowed_text` with `program.text_apply` and their
  `base`.

What the hub refuses, by code: `field_fixed` (`in`, `template`, `from`, a
step's `merged`), `step_frozen` (a frozen field of a started step, with its
reason), `step_stays` (remove a started or merged step), `round_question`
and `round_state` (the `?` lines and `asking` are the engine's),
`round_done`, `owner_required` (a change or waive of one of his
requirements, a round answer), `text_bad_value`, `text_unknown_word`,
`program_closed`. Do not retry a refusal; tell the owner.

**Never put a row id in `allow_lower`.** A row with verdict `lowers` makes
the Program check less (a higher control level, a review or check taken
off, a lower depth, a merge gate from `owner`, a requirement made optional
or weaker, a waive). Only his own press applies it. Leave it in the well
and tell him.

## Be a step's agent (you build one step)

- Your brief is your first prompt. It names your files ("yours") and the
  sibling steps' files ("theirs, do not touch").
- `program.checkpoint` with one line at each important moment ("31
  handlers, 20 done"). Only your own step accepts your line.
- Commit on your step's branch. Run the gate command the brief names and
  keep its log path. Never report green without the log path.
- `program.step_done` with your report: files changed, what you left
  out, the log path. Put the most important line first: the step's row
  shows the first lines of your report under "The agent says:", marked as
  not checked by HoldSpeak. Name a missing step in `follow_ups`; YOLO adds it,
  the other levels ask the owner. The engine still waits for your commit.
- **A question that blocks you:** ask it in your session and wait. Do not
  guess. The step shows "Asks you". At Normal and YOLO the desk can type a
  draft answer to a routine question. A core question (below) always goes
  to the owner. Write the same question in one `program.checkpoint` line,
  so the handover note has it.
- **A held commit.** At Secure and Normal the gate can hold your
  `git commit`. Do not retry it, do not go around it (no other branch, no
  `--no-verify`, no second commit tool) and do not ask him to commit for
  you. Call `program.step_done` and end your turn. He sees "Allow the
  commit" and "Not now"; at YOLO the rule allows it. A change you leave
  uncommitted at the end of your turn gets the same row, and Allow makes
  the commit on your branch. Not now parks the step; the change stays in
  the worktree. Do not commit the `.tmp/program-check` logs.

- **The owner took your lane.** When the step says "You have the lane",
  the owner types in it. HoldSpeak sends you nothing until he presses
  Hand it back. Do not ask him to hand it back. A commit on the branch
  still goes to the check.

## Be an audit step's agent (template `audit`)

- Read and run tests only. Change nothing and commit nothing: the gate
  refuses every write, and a commit on an audit step is a core question
  for the owner. An audit step never merges.
- Report each finding on its own line: `MUST: <what is wrong> ·
  <evidence>`, `SHOULD: …` or `NOTE: …`. The evidence is a file:line, a
  route or a screenshot path. MUST is a defect he must fix, SHOULD is worth
  fixing, NOTE is for the record. Name each window, route or file you
  read. If you find nothing, say `No findings`. Then `program.step_done`
  with that report and end your turn.
- Your findings become Door tasks by the control level. From the MUST
  findings, `program.propose_fix` (the owner or the agent that made the
  audit) makes a fix Program in Drafting: one step per MUST, each with a
  Review requirement that it is fixed. It is never started by that call.

## Requirements (the owner's bar)

A requirement is one sentence of the owner's, with a number (R3) and a
kind: **check** (a command HoldSpeak runs on the step's commit),
**review** (the step's reviewer answers it), **shot** (the desk sweep
renders a window at 393 or 1440), **word** (the owner presses Met; its
`walk` lines are the things he will do, in order), **measure** (a command
and a bound such as `p95 < 100 ms`; HoldSpeak runs it at the check. Under
the bound it is Met ("Measured 1.4 s, under 2 s"); over the bound the check
is red and comes back as the next round; "Not measured yet" until it runs).
`program.get` carries them: `requirements` and `requirements_met` on the
Program and on each step. In the text a requirement is
`R3 check: <sentence>`, with `run`, `expect`, `shot`, `bound`, `walk` or
`waived:` lines under it.

**You build a step.** Your brief has "What must be true": each
requirement of your step with how it is proven, then the ones for the
whole program. Make the change meet each one. Run a check requirement's
command yourself if you want to know early, but **never say a requirement
is met**: HoldSpeak runs it on your commit and reads its log; a red one
comes back to you as the next round, with the log's end. A new commit sets
your step's Met check, shot and review requirements back to Not yet; they
are judged again. A line "The owner on step 4: …" is an amendment to your
brief from him; take it into the step.

**You review a step.** Your acceptance lines name each review
requirement by its number. Answer each one on its own line, exactly:

```
REQ R3: MET · <one line: what in the diff shows it>
REQ R4: UNMET · <one line: what is missing>
```

Answer every REQ you were given. UNMET is a MUST: it goes back to the
builder as a REQUIRED finding. A missing answer gets one more ask (Normal,
YOLO), then goes to the owner.

**You propose a requirement.** `program.require` with `program_id`,
`text`, and `step_id` (one step) or `each_step: true` (every step), or
neither (the whole program, judged after the last step). Leave `kind`
unset and the rule picks it: text in backticks is a check, "<Name> window
at 393" is a shot, the rest is a review. A step's own agent may propose
on its step; the agent that made the Program may propose anywhere. At
YOLO it is added and listed under Decided for you; at Secure and Normal
the owner presses Add or Skip. A requirement HoldSpeak cannot prove (a
check with no command, a shot with no shot command in the repository) is
refused with `requirement_unprovable`.

To propose one in the text, add an `R+ <kind>: <sentence>` line and send
it through `program.text_apply`; it goes up the same ladder. A measure
needs `kind: "measure"` and `spec` with `command`, `metric`, `op`, `bound`
and `unit` (else `requirement_unprovable`: "A measure needs a command and a
bound").

**You never lower the bar.** No agent waives a requirement, marks one
Met, or changes one of his (`program.require` with `requirement_id` and
`program.decide` kind `requirement` are his only). In the text: never
write a `waived:` line, never make his requirement `optional` or another
kind, never take a check, a review or a gate off, never raise the control
level, never change his `>` lines, his `?` questions or his `=` answers.
When a requirement cannot be met, say so in your report and in a
checkpoint line; he decides.

**The interview rounds are his.** `program.round` with `next` asks the
engine for the next question; that is for him to answer. Do not answer a
round (`answer`), close it (`done`, `skip`) or skip its questions for him,
even where the tool lets the agent that made the Program do it. A `=` line
from an agent in the text is refused (`owner_required`).

**You orchestrate and the plan must change.** `program.step_update`
(the fields a step's state leaves open; `before` moves a Planned or Ready
step), `program.plan` with `before` (insert before a Planned or Ready
step) and `program.amend` (one line to a started step's brief, typed at
its next turn end). Each of yours goes to the owner at Secure and Normal
(Apply or Skip, Send or Skip); YOLO applies it. A frozen field is refused
with `step_frozen` and its reason ("The agent has read it"): do not retry
it, tell him.

## The rules

- **Never prompt a step's agent directly.** The engine briefs, re-briefs
  and sends the log tail at a turn boundary. Do not use `agent.prompt` or
  `agent.answer` on a launch that belongs to a step.
- **Never decide.** `program.decide` (merge, findings, parked steps, core
  questions, a held commit, a race winner, close, an agent at its limit, a
  requirement, a to-do (`done`, `cant`), a proposal, a failed delivery, the
  audit's findings (`audit_file`), a fix program (`fix_program`), a lesson
  (`lesson`)), `program.overturn`
  and `program.handoff` are the owner's press (AUTHORITY). You refuse them;
  you tell him the row in Needs you. `phone.brief` and `phone.later` (the
  briefing page, Telegram, Later) are his too; never call them for him.
- **Runs on is a list.** `runs_on: ["claude", "codex"]` on `program.create`,
  `program.update` or a step: the first agent runs it, the next takes over
  when one stops at its usage limit (PG19). If you start on a handoff brief
  ("# Handoff brief"), check the worktree against it first and continue on
  the same branch.
- **Core questions are his at every level:** the goal, files outside the
  repository or outside what the steps own, egress beyond the step's own
  PR, money (pi on a paid engine with no spend limit), authority or
  settings, a security or data-loss finding, a deleted test, a migration
  that drops rows, a choice with no rule.
- **Whose word.** A brief line marked "HoldSpeak on step N" is the engine;
  "the owner on step N" is him. Never present your own words as his.
- **Park with a reason.** `program.park` takes `reason`: `proof` (a run
  that proved the engine) or `done-with-it`. The list folds such a row.
- **From a shell.** `holdspeak program create|start|get|decide` uses the
  same service, and so does `holdspeak.sdk.programs` from Python. With
  `HOLDSPEAK_AGENT_CREDENTIAL` set, the agent rules apply to you there too.
- Never commit outside your branch, never stash, never push `main`. One
  test run at a time through the repository's lock.

## Proof

Report the Program id, each step's state and PR number from
`program.get`, and the check log paths. A claim of "merged" needs the PR
number the engine read back; a claim of "green" needs the log path. A
requirement's state is the one `program.get` reports, with its evidence;
never your own.
