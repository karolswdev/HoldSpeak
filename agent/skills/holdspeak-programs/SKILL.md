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

## Drive a Program (you orchestrate)

1. `program.create` with `title`, `goal` (the owner's words), `repository`
   (a local git folder) or `project_id`, `base_branch`, and a `template`
   (`fast-cycle`, `build-and-review`, `race`, `from-the-desk`,
   `overnight`). Leave `control` unset: it takes the desk's Control mode.
   The Program is in Drafting.
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

## Be a step's agent (you build one step)

- Your brief is your first prompt. It names your files ("yours") and the
  sibling steps' files ("theirs, do not touch").
- `program.checkpoint` with one line at each important moment ("31
  handlers, 20 done"). Only your own step accepts your line.
- Commit on your step's branch. Run the gate command the brief names and
  keep its log path. Never report green without the log path.
- `program.step_done` with your report: files changed, what you left
  out, the log path. Name a missing step in `follow_ups`; YOLO adds it,
  the other levels ask the owner. The engine still waits for your commit.

## Requirements (the owner's bar)

A requirement is one sentence of the owner's, with a number (R3) and a
kind: **check** (a command HoldSpeak runs on the step's commit),
**review** (the step's reviewer answers it), **shot** (the desk sweep
renders a window at 393 or 1440), **word** (the owner presses Met).
`program.get` carries them: `requirements` and `requirements_met` on the
Program and on each step.

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

**You never lower the bar.** No agent waives a requirement, marks one
Met, or changes one of his (`program.require` with `requirement_id` and
`program.decide` kind `requirement` are his only). When a requirement
cannot be met, say so in your report and in a checkpoint line; he decides.

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
  questions, a race winner, close, an agent at its limit, a requirement,
  a proposal), `program.overturn`
  and `program.handoff` are the owner's press (AUTHORITY). You refuse them;
  you tell him the row in Needs you.
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
- Never commit outside your branch, never stash, never push `main`. One
  test run at a time through the repository's lock.

## Proof

Report the Program id, each step's state and PR number from
`program.get`, and the check log paths. A claim of "merged" needs the PR
number the engine read back; a claim of "green" needs the log path. A
requirement's state is the one `program.get` reports, with its evidence;
never your own.
