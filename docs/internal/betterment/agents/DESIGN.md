# Agents (today: "Conductor"): betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk with a fake
Claude Code, 85 shots, 2026-10-17), `MODEL.md` (the code map) and
`../herdr/STUDY.md` (what to take from herdr). Companions:
`../workbench/DESIGN.md` (Automations), `../engines/DESIGN.md`,
`../mcp/DESIGN.md`. Cluster F: INVENTORY rows 27 to 31.

## 1. The job

Owner, 2026-10-05: "I wanted it to work with agents. In a semi-autonomous
way. As an orchestrator. And out of the box. And batteries included."

He opens Agents when he has a piece of work for a coding agent (Claude
Code, Codex or pi), or when one of them needs him. He runs three to eight at
once, across his projects, while he is in meetings. He works the way he
already works with us: one agent builds, another reviews, and he makes the
final call. He closes Agents when:

- every agent that waits on him has his answer, and he gave each answer in
  one press;
- he knows which agents finished, and he has read what each one did;
- he trusts that nothing is lost: not a finished turn he did not look at,
  not an answer the desk gave for him, not an agent that a restart stopped.

## 2. What it is today

The full walk is in `RECON.md`. In short: **the loop works under the face**.
A brief reached the agent 5 s after Launch, its question showed in about
10 s, and a typed answer and a key reached its terminal in about 1 s. These
were never observed before. **The face fails the job.** One hand, one
answer, one approval and "is it done?" took **about 25 presses across five
windows and 6 to 8 minutes**, and two parts never work.

| Step | What happens | Shot |
|---|---|---|
| Find where to start | The Conductor has no start verb. On a note in front, Object ▸ "Hand to coder" is grey ("Select an object"). Needs you has no hand verb. The verb is in the Project Room. | `03-conductor-empty-1440.png`, `07b-object-menu-note-focused-1440.png`, `11-needs-you-more-1440.png`, `12-action-opened-1440.png` |
| Hand it | A good sheet: grounded brief, acceptance, new branch, Control mode, honest egress chip. No place for his own sentence. | `13-hand-sheet-1440.png` |
| See it ask | In the Conductor in about 10 s. Not in Needs you: under YOLO the desk holds the question while it drafts. | `15-conductor-asks-1440.png` |
| The desk answers for him | 44 s later the desk typed "Yes, …" to a "1 or 2" question. Nothing told him; one line in the lane foot. | `17-see-the-call-1440.png` |
| Approve a command | The card says "permission to use Bash", not the command. No Allow. Raw ▸ Keys ▸ ENTER, with the command below the fold. | `16-conductor-permission-1440.png`, `20b-lane-terminal-bottom-1440.png` |
| Answer it himself | Answer ▸ type ▸ Answer refuses "ARM FIRST" ▸ ARM ▸ Answer. The drafted answer was right. | `31-after-answer-1440.png`, `32-after-armed-answer-1440.png` |
| Know it is done | The agent said "Done". The desk says "Working", 8 minutes later too, and it holds one of the three slots. Today shows nothing. | `23-conductor-after-done-1440.png`, `28-hand-sheet-at-cap-1440.png`, `24-today-after-agent-1440.png` |
| Restart | Dead agents keep asking. ARM fails with 409; the face still says "ARM FIRST". | `38-conductor-after-reboot-1440.png`, `39b-ghost-answer-1440.png` |
| Other agent faces | Delivery board (`rider:claude · NODE local · TARGET TERM_… · OFFLINE`), Terminals (`no tmux panes · SPAWN`), and "New Agent", which makes a saved prompt. | `42-delivery-board-1440.png`, `47b-terminals-open-1440.png`, `44-new-agent-1440.png` |

## 3. Why it fails

1. **The state model is wrong about the one thing he needs: is it done?**
   State comes only from hooks. A finished turn with no PR reads "working"
   (`MODEL.md` §2), nothing marks a finished turn as unread, a dead agent
   keeps its last question, and a session with no signal decays to "idle"
   in silence. So he must open every agent to know anything, which is the
   exact thing herdr's "done until seen" fixes. (`23-*`, `38-*`)
2. **One concept, six faces and three names.** A coding session is the
   Conductor's "coder", a lane, a session window, a Needs you "CC" row, a
   desk icon, and a Delivery board "work attempt". Meanwhile "Agent" means
   a saved prompt (New Agent, the thread modes in Search). Answer exists in
   six places with three paths underneath (`MODEL.md` §3). (`03-*`, `42-*`, `48-*`)
3. **An answer is a trip, not a press.** The question is in one window, the
   answer box in another; the permission card hides the command; ARM sits
   in front of Answer and blames him. The desk has the facts (the screen
   holds the command and the numbered choices), but the face does not use
   them. (`16-*`, `20b-*`, `31-*`)
4. **The desk acts for him without telling him.** Under YOLO the question
   is held out of Needs you, and the answer is typed in silence, in the
   wrong form. A good default with no receipt he can see breaks trust.
   (`15-*`, `17-*`)
5. **Agents are an island.** The hand verb is missing where items live
   (an open note, Needs you, Search). Today does not know agents exist. No
   automation can start one, no agent can hand work to another, and the
   builder/reviewer loop he runs every day lives in our scripts, not in
   the product. (`07b-*`, `11-*`, `24-*`)
6. **Nothing survives a restart.** The worktree and the branch survive,
   the conversation does not, and the face pretends nothing happened.
   (`38-*`)

## 4. The design

### The concept

**An agent is a coding session that works on one item for you, in its own
branch, until it needs you or is done.** Agents is the one list of them,
the ones that need you on top. Each finished turn is a **result**: it stays
**New** until he reads it.

This follows the product model (`../PLAN.md` §2): "Agent" means only a coding
agent session; its home is **Agents** (today the Conductor); what it
produces is a **Result**; what waits on him is in **Needs you**; its New
results show in **Today**.

### The states he sees

Ported from herdr's state model (`../herdr/STUDY.md` §1.2), with a credit
line (see "Credit" below).

| He sees | It means | herdr | How we know, in order of authority |
|---|---|---|---|
| **Asks you** | the agent asked a question and waits | blocked | hook (Stop with a question, Notification `idle_prompt` / `elicitation_dialog`); then a screen rule |
| **Wants to run** … | an approval prompt or a held tool call | blocked | hook (`permission_prompt`, PermissionRequest), a gate proposal; then a screen rule, which also reads the command and the choices |
| **Done** (New until opened) | a turn ended after real work, with no question | done | Stop after a UserPromptSubmit in the same turn (herdr's `completion_seq`); a screen rule |
| **Working** | it runs a turn | working | hooks (tool calls); the screen spinner or "esc to interrupt" |
| **Quiet** | done and seen, or idle at its prompt | idle | the seen bit; a screen rule |
| **No signal** | an agent is there, but nothing tells us its state for 10 min | unknown | no hook, no rule match. Never shown as "done" or "idle" |
| **Stopped** · **Stopped by restart** | its process is gone | – | the launch record and a tmux check on hub start and each heartbeat |
| **PR open** · **Merged** | the follow-through | – | Heartbeat (as built) |

Rules:

- **Blocked is strict.** "Asks you" and "Wants to run" appear only on a hook
  subtype or a matched question or approval screen, never on a guess.
- **Done stays until seen.** Opening the agent (its row or its window) marks
  the turn seen. Each turn has its own seen bit; a restored session or a
  start-up idle is never a "Done".
- **The worst state wins** for a group (a project, the Dock tile, Today).

### The words

| He sees | It replaces |
|---|---|
| **Agents** (the app), **an agent** | Conductor, coder, coders, lane, flight, session, rider:claude, work attempt |
| **Hand to agent** | Hand to coder, LAUNCH (Delivery board), SPAWN |
| **Start an agent** (in Agents) | – (no start verb today) |
| **Asks you**, **Wants to run** … | ASKS YOU, WANTS APPROVAL, "Claude needs your permission to use Bash", TO APPROVE, CC |
| **Answer**, the choice buttons (**1 · config**) | Answer + ARM + "ARM FIRST", Use draft |
| **Allow**, **Deny** | Approve, See the call, Raw ▸ Keys ▸ ENTER |
| **Done**, **New** | "Working" after the end, DONE-only-with-a-PR, IDLE |
| **Quiet**, **No signal** | idle, stale, a silent decay |
| **Stopped by restart**, **Resume** | ghosts, "ARM FIRST" on a dead pane |
| **Tell it** | Re-brief |
| **Terminal** | Raw, Open terminal, Back to session, RAW LINES 93 Δ 6s |
| **Close** (a done agent), **Stop** (a working one) | Details ▸ Stop ▸ "Stop · sure? (ends the coder's session)", stopped_by_owner |
| **Review by** | – (new) |
| **Connect Claude Code** | Install hooks, "Hooks: see the coder's work, hand it work" |
| **The desk answered** | THE DESK ANSWERED, "The desk: …" prefix only |

Removed from the face: `GRANT`, `YOLO · DIRECT`, `CTRL`, `Receipt
steering:7 · %0`, `TARGET TERM_… · OFFLINE`, `INCOMPATIBLE`, `NO LIVE
SOURCE`, `NODE local`, `WT wt_…`, `action:action_5f5e…` and every other
internal id. The stored names (`coder`, `launch`, `flight`, `agent_hand`,
`coder.*` MCP tools) stay in code.

### The Agents window (desktop, 1440)

One window. The header counts only what is there (no counters of zero). The
rows are sorted: Needs you (oldest first), Done and New (newest first),
Working, Quiet, then Stopped (folded).

```
┌ Agents ──────────────────────── 2 need you · 1 new · 2 working ─ [ Start an agent ] ┐
│                                                                                      │
│ ● Write the on-call note for the new flag            Claude Code · Platform · 4 min  │
│   Asks: Should the rollback flag live in config/flags.yaml (shared with staging)     │
│   or in an env var (per host)?                                                       │
│   [ 1 · config ]  [ 2 · env ]   [ Say or type the answer …          🎤 ] [ Answer ]  │
│   Draft: 1, from your decision "The rollback flag moves into config/flags.yaml"      │
│                                                                                      │
│ ● Move rollback flag into config/flags.yaml          Claude Code · Platform · 1 min  │
│   Wants to run:  rm -rf build/ && make release                                       │
│   [ Allow ]  [ Deny ]  [ Terminal ]                                                  │
│                                                                                      │
│ ◆ Draft test scaffolding for flags            NEW    Claude Code · done 8 min ago    │
│   "Done. The flag now lives in config/flags.yaml, with a test."                      │
│   3 files changed · Reviewed by Codex, round 2, nothing left        [ Open ] [ Close ]│
│                                                                                      │
│ ○ Review Theo's PR                       Codex · Platform · working 2 min · Reading  │
│ ○ Rollback runbook (helper of "Draft test scaffolding")   Codex · reviewing · 40 s   │
│                                                                                      │
│ ▸ Stopped today (1)                                                                  │
│ ▸ Agents you started yourself (2)                                     (decision 1)   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

- **A row is the whole job for that agent.** He answers, allows or opens
  from the row; no other window opens for a question.
- **Choice buttons** come from the question ("Answer 1 for config, 2 for
  env") or from the agent's own numbered menu on its screen (`❯ 1. Yes`,
  `2. No`). One press answers.
- **Answer** sends the typed or spoken text in one press. The press is his
  authority, so it arms the send for this one question; there is no ARM
  step on the face (the grant stays scoped to this wait and the pane is
  checked again before typing, as built).
- **The draft** shows when the desk has one (Normal and YOLO), with its
  source in words. "Use draft" fills the box; it never sends by itself in
  Normal.
- **Wants to run** shows the command, read from the screen (or the gate's
  held call). **Allow** sends the agent's "yes" key, **Deny** sends its
  "no" key; for a gate-held call they decide the gate's proposal. One
  press either way.
- **When the desk answered** (YOLO), the row shows "The desk answered: 1,
  from your decision '…'" and is **New** until he opens it. He can **Tell
  it** something else. While the desk drafts, the row says "The desk is
  drafting an answer" with **Answer it myself**.
- **Done** rows show the agent's last words, what changed (files, branch,
  PR), the review rounds when there was a reviewer, and **Open** / **Close**.
  Close ends the agent's session and keeps the branch and the worktree.
- **Group by project** when the agents span two or more projects: a thin
  project line with the worst state of its agents (herdr's workspace
  rollup). With one project, no group lines.
- **Start an agent** unfolds in place: *What should it do?* (text and mic),
  *Project* (projects with a repository), *Agent* (Claude Code, Codex, pi),
  *Review by* (none, Codex, Claude Code, pi), and **Start**. It files a note
  with his words in the project and hands that note, so the brief is
  grounded the same way.
- **Empty state:** one line, "An agent works on one item for you, in its
  own branch." Then **Start an agent**. "On this Mac" (Claude Code, Codex,
  pi, with **Connect** when hooks are missing) shows only when something is
  missing.

### The agent's window (today the lane)

Opened by **Open** on a row, by a desk object's "Agent" line, or from Needs
you and Today. The top block is the same row as in Agents (Asks / Wants to
run / Done, with the same verbs). Below it, two views:

- **Story** (default): the lane timeline as built (Brief, Run, Says,
  Answer), plus **The desk answered** entries, review rounds and helpers.
- **Terminal**: the live screen, opened **at the bottom** and following the
  tail, with Find. The keys (Esc, Enter, arrows, Ctrl-C) sit under it.

When the turn is done, a **Result** block leads the Story: the agent's last
message, files changed (from the branch), the PR when there is one, and
three folds from the hub's own record of its MCP calls: **Looked at**
(meetings, people, decisions it read, as links), **Wrote** (desk writes)
and **Prepared** (sends waiting for his press). Cost shows when the CLI
reports it.

Verbs in the window foot: **Tell it**, **Stop** (working) or **Close**
(done), **Resume** and **Hand again** (stopped by restart).

### Phone (393)

The Agents window is full screen, with the same order. Each row is a card:
title, agent and age on one line, the question or command in full (never
cut with "…"), choice buttons full width, then the answer box with the mic
and **Answer**. Allow and Deny are two full-width buttons. The Dock's
Agents tile carries the worst-state lamp and the count of agents that need
him.

```
┌ ‹ Back   Agents        2 need you ┐
│ ● Write the on-call note …        │
│   Claude Code · Platform · 4 min  │
│   Asks: Should the rollback flag  │
│   live in config/flags.yaml or in │
│   an env var (per host)?          │
│   [        1 · config          ]  │
│   [        2 · env             ]  │
│   [ Say or type …     🎤 ][Answer]│
│ ● Move rollback flag …            │
│   Wants to run:                   │
│   rm -rf build/ && make release   │
│   [ Allow ]          [ Deny ]     │
│ ◆ Draft test scaffolding    NEW   │
│   "Done. The flag now lives …"    │
│   [ Open ]           [ Close ]    │
└───────────────────────────────────┘
```

### Where agents show outside Agents

- **Needs you** carries "Asks you" and "Wants to run" rows, with the same
  verbs inline. While an agent works on an action, the agent's row
  replaces the action's row (one row per piece of work, not two).
- **Today** opens with an Agents line when there is something: "2 agents
  need you · 1 finished". Below it, each New result is a card ("Claude Code
  finished *Draft test scaffolding* · 3 files · reviewed") with **Open**.
  Needs-you agents use Needs you's own rows. Nothing shows when all agents
  are quiet (no counters of zero).
- **The Dock tile** "Agents" carries the worst state: a lamp for Needs you,
  a dot for New, and the count of agents that need him.
- **Notifications** (decision 2): "Needs you" always; "Done" quietly, never
  for the agent he is looking at.
- **Desk objects** (a note, an action, a meeting) show an "Agent" line when
  an agent works on them ("Claude Code · working" or "Done · New"), which
  opens the agent's window. The separate desk icons per agent leave the
  floor.

### Hand to agent, from where the work is

- On every work item where he reads it: the window in front (note,
  meeting, action, decision, Room issue), Needs you rows (More ▸ Hand to
  agent), Search results, and a drop on the Agents Dock tile.
- The sheet keeps what works (the grounded brief, acceptance, the egress
  chip) and adds two lines: **Add a sentence** (his words go into the brief;
  the API already takes them) and **Review by**. *Where* reads "Platform ·
  new branch draft-test-scaffolding" (a readable branch slug).
- **Working at once**: a setting, default 6 (he runs three to eight). Done
  and Quiet agents do not count: their process waits and costs nothing.
  At the limit, Launch becomes **Start when one is free** (a queue), never a
  dead red line.

### After a restart (herdr idea 3)

- On hub start and at each heartbeat, an agent whose tmux session is gone
  becomes **Stopped by restart**. It never keeps asking.
- **Resume** (one press, or **Resume all** in the Agents header) opens a new
  session in the same worktree through the same credential start-up and
  runs the agent's own resume: `claude --resume <id>`, `codex resume <id>`,
  `pi --session <path>`. The hooks already carry the session id; the launch
  stores it.
- If the resume fails (an old id), the agent's window opens a shell in its
  worktree and offers **Hand again**. Nothing resumes by itself.

### Agents that work together (herdr idea 2)

New MCP tools in the CONDUCTOR set, so a launched agent can drive another
under the same rules:

| Tool | Does | Rules (copied from herdr's contract) |
|---|---|---|
| `agent.prompt` | sends text to an agent; with `wait`, also waits, in one request | refuses an agent that is blocked (`agent_blocked`): a real answer goes through `agent.answer`; says `agent_prompt_stalled` if nothing moves in 5 s |
| `agent.wait` | waits until done, needs you or quiet | pinned to that session: a new agent in the same pane never satisfies it |
| `agent.read` | the last N lines, or the last message from the hook | read only |
| `agent.answer` | answers a question of an agent it started (text or a choice) | only its own helpers; never an approval prompt: Allow stays with him or the gate |
| `agent.start_helper` | starts one helper (a reviewer, a test runner) in its own worktree | counts against "working at once"; same Control mode; decision 3 |

A helper shows as an indented row under its parent ("helper of …"). The
gate, the credential and Stop treat it as a launch of its own.

### Review by: the builder and the reviewer (the Muad'Dib/Astra pattern)

"Review by" on the hand sheet (or on Start an agent) makes a pair. The hub
runs the loop, not the agents, so it is the same every time:

1. The builder (for example Claude Code) works until its turn is **Done**
   and its work is committed on its branch.
2. The hub starts the reviewer (for example Codex) as a helper: its own
   worktree at the builder's commit, read only, with a review brief: the
   item, the acceptance checks, "review the diff of this branch against
   main; list findings as MUST and SHOULD with file and line; change
   nothing".
3. When the reviewer is Done, the hub gives its findings to the builder
   (`agent.prompt`): "Fix the MUST findings, then commit."
4. At most **two rounds** (our own rule for Astra). Then the pair is Done
   for him, with one result: "Reviewed by Codex, round 2, nothing left", or
   "2 MUST findings left after 2 rounds" as a Needs you row with **Open**.
5. He makes the final call: he reads the result, opens the PR, merges.

The row says "Claude Code builds · Codex reviews · round 1". Each round's
findings are in the Story. Either agent asking a question goes to Needs
you like any agent.

### Automations meet Agents (herdr idea 5)

Two meetings, both through the product model's one name for each concept:

- **An automation can hand work to an agent.** In Automations
  (`../workbench/DESIGN.md`), *Do* gets a second kind, **Hand to an agent**:
  *About* names the items (for example "new Jira bugs labelled agent-ok",
  "this week's actions I marked for an agent", "a PR that asks for my
  review"), *With* names the agent and *Review by*. Each run hands each new
  item once (an item already handed is skipped), under "working at once".
  The automation's result lists the agents it started.
  Starters, shown only when their source works: *Morning bug sweep* (every
  weekday 7:00, Jira bugs labelled agent-ok, Claude Code, Review by
  Codex); *Review requests* (when GitHub asks me to review, Codex reads the
  PR and writes findings into the agent's result, never posts them);
  *Friday runbook* (Fridays 16:00, update the runbook from this week's
  decisions).
  Turning such an automation on is AUTHORITY at creation, once; each run is
  then the automation's own press (`../mcp/DESIGN.md`).
- **An agent's result appears in Today.** Every Done turn is a Result,
  New until read: in the agent's row, in Today, and on the automation
  that started it.

This differs from an agent as an **engine** (`../engines/DESIGN.md`): there
an automation asks Claude Code one question and gets text back
(`claude -p`); here an agent gets an item, a branch and a session.

### Seeing every agent (herdr ideas 1 and 7)

- **Screen rules.** The hub reads the bottom lines and the title of each
  agent's tmux pane (it already reads the pane for the terminal view) and
  applies per-agent rules: regions (the last 12 lines, the line above the
  prompt box, the pane title), `contains`, `regex`, `not`, a priority. We
  port herdr's rule files for Claude Code, Codex, pi, Gemini CLI and
  OpenCode as data, with a local override folder. Rules give: state when
  no hook speaks; the command and the choices of a prompt; the spinner that
  says Working between hooks. A hook still wins over the screen.
- **Why this state** (behind RAW, in the agent's window): which source
  decided (hook or rule), the rule, the evidence lines and the age.
- **Agents he started himself** (decision 1): agents running in his own
  tmux panes show in a folded section, with the same states and Answer /
  Allow. HoldSpeak did not start them, so it offers no Stop and no brief.

### A HoldSpeak skill (herdr idea 6)

`holdspeak --skill` prints a short `SKILL.md` that matches the installed
version: check the launch credential first and stop without it; read the
brief's refs with `project.get` and `memory.search`; say Done in one line
with what changed; use `agent.start_helper` for a reviewer; never write
"Closes #N". Launched agents get it with their settings; his own Claude
Code and Codex get it with one press on Connect.

### Credit

The state model (five states, the seen bit, a completion sequence, strict
blocked), the prompt-and-wait contract, the resume table and the agent
detection rules come from **herdr** (`github.com/herdrdev/herdr`,
Apache-2.0, v0.9.5). The rule files we vendor keep their copyright notice
and license; `NOTICE` names herdr and what we changed. Nothing is copied
from the AGPL fork or any snapshot before herdr 0.8.0.

### What is removed or parked (nothing is deleted)

| Thing | Where it goes |
|---|---|
| The Conductor name, "coder" | Agents, agent (face only) |
| The session window, the coder card, the per-agent desk icons | one agent window; desk objects get an "Agent" line |
| Answer in six places | one row component in Agents, Needs you and Today |
| The ARM chip, GRANT bar, YOLO · DIRECT | behind RAW in the agent's window (Keys stay) |
| **Delivery board**, **Terminals**, **Mission Control**, RepoWindow Issues | behind RAW as builder tools. The agent row carries the PR and CI; the Room carries sources |
| The Delivery board's LAUNCH and Terminals' SPAWN | parked; Hand to agent is the one way to start |
| **New Agent** (saved personas) | leaves the Desk menu (`../PLAN.md` decision 3). Saved prompts live on as Thread modes (shown as "Mode", not "AGENT", in Search) and as Automation starters |
| The old Agents app (`/companion`) | manifest row and route unmapped |
| Today's parked Agents section | replaced by the Agents line and Result cards |

## 5. Decisions for the owner

These are the herdr study's three decisions, designed in above. Each has a
default, so the build starts on it.

1. **See agents you started yourself.** The hub reads the bottom lines of
   your own tmux panes, on this Mac, to find agents HoldSpeak did not start,
   with the same secret filter the hooks use. Nothing leaves the Mac.
   Recommended: **yes, on by default**, in a folded "Agents you started
   yourself" section.
2. **Done notifies.** A finished agent raises a quiet notification (no
   sound by default), never for the agent you are looking at, and stays
   **New** until you open it. Done goes to Today, not to Needs you. This
   amends the Conductor's A5 rule ("Needs you is what needs him"; done was
   kept out of notifications). Recommended: **yes**.
3. **Helpers inside a launch are WORK.** A launched agent may start one
   helper (a reviewer or a test runner) in its own worktree without your
   press, inside "working at once" and its own Control mode. Under Secure it
   asks. Recommended: **yes under Normal and YOLO**. (Review by, which you
   choose on the sheet, does not depend on this: your press starts both.)

## 6. How we know it worked

On his own desk, with real agents, in a working week:

- He hands an item from the window where he reads it in **2 presses**
  (Hand to agent, Launch), or types a task into Start an agent in
  **3 presses**.
- He answers a question with choices in **1 press**, or speaks and presses
  **Answer** (1 press), from the Agents list, Needs you or the phone.
- He allows a command in **1 press**, and he read the command first.
- With five agents running, one glance at the Dock tile or Today tells him
  how many need him and how many finished, **without opening any**.
- A finished agent is **New** until he opens it, and he never finds a done
  agent marked "Working".
- After a Mac restart, **1 press** (Resume all) brings every stopped agent
  back to its conversation.
- He hands one item with **Review by Codex** and gets one result that says
  how many review rounds ran and what is left, without touching the
  reviewer.
- An automation hands two bugs overnight, and at 8:00 Today shows two New
  results.
- The core job (hand, answer, allow, read the result) takes **at most 6
  presses in one window, under 2 minutes of his attention per agent**,
  against about 25 presses in five windows today.
