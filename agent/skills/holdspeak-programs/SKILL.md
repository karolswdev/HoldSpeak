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

## The rules

- **Never prompt a step's agent directly.** The engine briefs, re-briefs
  and sends the log tail at a turn boundary. Do not use `agent.prompt` or
  `agent.answer` on a launch that belongs to a step.
- **Never decide.** `program.decide` (merge, findings, parked steps, core
  questions, a race winner, close, an agent at its limit), `program.overturn`
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
number the engine read back; a claim of "green" needs the log path.
