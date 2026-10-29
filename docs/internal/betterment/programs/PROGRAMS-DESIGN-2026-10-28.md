# Programs: the orchestration engine on top of HoldSpeak

Owner, 2026-10-28: "one, holistic PR, on building a proper, well built-out, well
specified, and well delightful software orchestration engine that runs on top of
HoldSpeak, with best practices taken straight from herdr as well as some recently
starred repositories … The quest of joy. The quest of delight."

Sources: `../herdr/STUDY.md` (herdr's model, states, agent-to-agent contract),
`../agents/DESIGN.md` and `../agents/RECIPE.md` (AG0–AG15, built: one item → one
agent → one worktree → a reviewer → a PR → merged), and the owner's stars of
October 2026: roost, DeckHand, openharness, Orca, hivehouse, living-map,
proactive-agent/workbench, nodeterm, laya-guard, kestra, future-agi, ECC. What
each gave is credited inline as "(repo)".

## 1. The job

He has a goal that is bigger than one item: "make the hub stop stalling", "the
words wave", "wave 6 of the atlas". Today that goal lives in the orchestrator's
head and in scratch briefs: the orchestrator cuts it into lanes by hand, writes
a brief file per lane, makes a worktree, starts an agent, reads its report, runs
the quick check, opens the PR, merges, redeploys, and keeps a running log in a
memory file. Nothing of that is on his desk. He cannot see what is running, what
waits on him, what is parked, or what was proven, unless he reads chat.

**A Program is a goal cut into steps, each step handed to an agent in its own
worktree, each result checked by a verified gate, reviewed by a fresh agent,
and merged on his press or by delegation; the Program keeps its own handover
note on the desk, and what waits on him is always on top.**

The engine runs on what AG0–AG15 built: the hand (`AgentHandService`), the
launch ledger and lane, the review loop (AG12), helpers (AG11), the Heartbeat's
follow-through to a merged PR, Needs you, Notes, the kernel's receipts. It adds
the one missing noun, the Program, and the loop that drives steps through it.

## 2. What it is not

- Not a workflow DSL. kestra's lesson is one declarative source edited three
  ways; ours is one record (a Program with Steps) edited by the owner in the
  window, by an orchestrating agent over MCP, or by a template. No YAML, no
  graph language. Dependencies are "after step N", nothing more.
- Not a terminal multiplexer. herdr owns terminals; HoldSpeak keeps tmux (AG as
  built) and takes herdr's contract (states, prompt-and-wait, occupant pinning,
  `agent_blocked`) as rules. If he runs herdr one day, the study's idea 9 (a
  read-only bridge) still stands and is not in this PR.
- Not a second review bot. The reviewer is a HoldSpeak agent launch in a
  scratch copy (AG12), at a stated depth, with a verdict. Astra stays the
  reviewer of HoldSpeak's own PRs by the owner's ruling; the engine's reviewer
  is for the Programs he runs on any repo.
- Not a cost estimator. No invented dollars (openharness); tokens and minutes
  are shown when the harness reports them, otherwise nothing.

## 3. The nouns

| He sees | In data | It is |
|---|---|---|
| **Program** | `programs` | a goal, a repository, a base branch, a control level (Secure, Normal or YOLO), steps, a handover note |
| **Step** | `program_steps` | one bounded piece of the goal: a brief, the files it owns, an agent profile, an effort, a gate; it becomes one launch in one worktree |
| **Gate** | `program_steps.gate_*` | what must be true before a step is done: the check log verified, the review verdict, his press |
| **Checkpoint** | `program_checkpoints` | one line the agent, the engine or he writes on a step at a meaningful moment (Orca) |
| **Your turn** | Needs you rows | anything only he can do: answer, allow, decide a finding, merge, resume (roost) |
| **Handover** | a desk Note | the Program's state as prose, rewritten on every change, so a dead session or a new chat starts from it (living-map, DeckHand) |
| **Template** | `program_templates.py` | a starting shape: Fast cycle, Build and review, Race |

Words that never appear on a face: lane (as a noun for a step), launch id,
worktree path as a title, flight, orchestrator, DAG, pipeline.

## 4. The states

### Program

| He sees | In data | Meaning |
|---|---|---|
| **Drafting** | `drafting` | steps are being written; nothing runs |
| **Running** | `running` | at least one step is working or checking |
| **Your turn** | `waiting` | no step can move without him (a question, a finding, a merge, a parked step with no sibling to run) |
| **Done** | `done` | every step done or parked by him; the note says what was parked |
| **Parked** | `parked` | he parked it; worktrees kept; Resume brings it back |
| **Failed** | `failed` | a step failed twice and nothing else can run; his Resume or Park |

The worst state wins for the Programs list and the Dock lamp (AG0 rule).

### Step

| He sees | In data | How it moves on |
|---|---|---|
| **Planned** | `planned` | its dependencies are not done |
| **Ready** | `ready` | dependencies done; waits for a working slot (`agents.working_at_once`) |
| **Briefed** | `briefed` | the brief is written to the worktree (`.holdspeak/brief.md`); the launch is starting |
| **Working** | `working` | the launch is working (AG0 state from hooks or screen) |
| **Asks you** / **Wants to run** | `waiting` | the launch is blocked (AG0); the row is in Needs you |
| **Checking** | `checking` | the agent's turn ended with a commit; the gate command runs in the worktree under the test lock |
| **Check failed** | `check_failed` | the verifier read the log and it is not green; the agent gets the log tail as its next prompt (round 2); after round 2 the step is **Failed** |
| **In review** | `review` | a reviewer launch reads the diff in a scratch copy (AG12); verdict PASS or FAIL with REQUIRED / SHOULD / NOTE findings (hivehouse) |
| **Findings** | `findings` | FAIL: REQUIRED findings go back to the builder (round 2 of AG12); after two rounds, what is left is **Your turn** with Fix now / Later / Skip per finding (roost) |
| **PR open** | `pr_open` | the branch is pushed and the PR is open; the Heartbeat's follow-through watches it |
| **Merge?** | `merge_ask` | Secure: a Needs you row "Merge step 3 of The hub stops stalling?"; Normal and YOLO: merged at once when the check is green and the review passed, logged under Decided for you |
| **Merged** | `merged` | the PR merged; the worktree and session are cleaned by follow-through (as built) |
| **Done** | `done` | merged, or a step with no PR gate (a research step) whose result note is written |
| **Parked** | `parked` | he parked it, or the engine parked it after two failed rounds with his Needs you row saying why |
| **Failed** | `failed` | see Check failed and Findings |

Rules:

- **Blocked is strict** (AG0): a step is **Your turn** only on a hook subtype,
  a matched screen, a verifier red, a finding left, or a merge ask.
- **A step moves on a receipt, never on a claim.** The agent's "done" is the
  launch's turn end with a new commit on the step's branch (`launch_lane.
  worktree_facts`); the gate's green is the verified log; the PR's merge is
  the follow-through receipt.
- **Two rounds, then him** (AG12, hivehouse): a check or a review goes back to
  the builder once; what is still red after that is his.
- **Never typed into a blocked agent.** The engine answers only with its own
  brief or the log tail at a turn boundary; a question is his (AG11's
  `agent_blocked` rule).

## 5. The gate: a verified log, not an exit code (hivehouse)

Every Program names its check command (default from the repository's
`.holdspeak/program.json`, else `scripts/quick_check.sh` if present, else none).
The engine runs it in the step's worktree, under `scripts/test_lock.py` when
the repository has it, with an isolated HOME, to a log file
`<worktree>/.tmp/program-check/<step>/<ts>.log`. Then the **verifier** reads
the log, not the exit code:

1. the log names the commit it ran on, and `git status --porcelain` in the
   worktree was empty at the start;
2. every named section (for the quick check: build, vitest, pytest, sweep,
   canon, repo) has a result line;
3. no section is red, and no section appears twice;
4. the log ends with the check's own verdict line.

A gate without a log path is never green. The step's row shows **Checked ·
green · 3 min · log**, and the log opens in a Note pullout.

## 6. The engine

`holdspeak/services/program_service.py` (CRUD, the state machine, the note)
and `holdspeak/services/program_runner.py` (the tick). The runner ticks:

- every 30 s from the workbench conductor's loop (`workbench_conductor.py`),
  the same thread that runs scheduled automations;
- at once on a coder frame (`intel_status` scope `coder`) for a launch that
  belongs to a step, and on a `desk_changed("launch", id, …)` from the
  Heartbeat (PR found, merged).

One tick, for each running Program, in order:

1. **Dispatch**: steps that are `ready` (dependencies `done` or `merged`),
   up to the free slots of `agents.working_at_once` across all Programs and
   the hand queue, become `briefed`: write the brief, hand through
   `AgentHandService.hand(kind="program_step", item_id=step.id, profile,
   start_point=program.base_branch, review=…)`. The hand makes the worktree
   (`hs-program_step-<id>`) and the launch; the step records `launch_id`,
   `worktree`, `branch`.
2. **Follow**: a step whose launch is `working` is `working`; `blocked` is
   `waiting` (and a Needs you row through `coder_items`, as built); a turn
   end with a new commit is `checking`.
3. **Check**: run the gate (one at a time on the machine, through the lock);
   verify; green → `review` if the step has a reviewer, else `pr_open` (push
   and `gh pr create` through the launch's own `gh`, as the hand does today);
   red → round 2 or `failed`.
4. **Review**: AG12's loop, with the depth from the step (`glance`, `delta`,
   `standard`); PASS → `pr_open`; FAIL → findings.
5. **Merge**: `pr_open` with CI green (follow-through's rollup) → Secure:
   `merge_ask` (a Needs you row with Merge / Not yet); Normal and YOLO:
   `gh pr merge --squash` and `merged`, logged under Decided for you.
6. **Note**: if anything changed, rewrite the handover note (§8) and emit
   `desk_changed("program", id, "step")`.
7. **Program state**: worst state wins; `done` when nothing is left.

The brief the engine writes (compose in `program_brief.py`, on top of
`agent_brief.compose_agent_brief`):

- who and where: the Program's title, this step's title and number, the
  repository, the worktree and branch, the base branch (DeckHand's briefing);
- the goal of the Program in his words, then this step's brief;
- the files this step owns, and the files sibling steps own right now, as
  "theirs, do not touch" (DeckHand etiquette; workbench's unmerged-branch
  list);
- the proof it must leave: the gate command and "never report green without
  the log path" (hivehouse); the named tests;
- the rules: never commit outside the step's branch, never stash, never
  push `main`, one test run at a time through the lock; a checkpoint line
  through `program.checkpoint` at each meaningful moment (Orca); its final
  message is the report (files changed, what was left out, the log path);
- whose word it has: "HoldSpeak on step N" vs "the owner on step N"
  (hivehouse), so a re-brief from the engine is never mistaken for him.

Triage (workbench): `program.plan` with `size: "auto"` sets each step's
`effort` and `profile` by rule, not by model: a step owning more than 12
files or saying "refactor" or "migrate" gets `high`; a one-paragraph brief
with one file gets `low`; the default is `medium`. The profile is the
Program's default unless the step names one. He can change both on the row.

Race (Orca): a step with `race: 2|3` is handed to that many agents at once
(the profiles in order: Claude Code, Codex, pi) in sibling worktrees; the
first branch whose gate is green and review passes wins; the others are
parked with "lost the race to <agent>". Agreement across the losers' diffs is
not computed in this PR; the note says which agent won and in how long.

Control: the desk's own ladder, and only core questions reach him (owner
2026-10-28: "every step or decision lands with me. No, absolutely not … if
those decisions relate to a core question, then yes, send them back to me, but
multiple levels of this, with YOLO really trying to be as hands off as
possible").

A Program's control is the desk's **Control mode** (Secure · Normal · YOLO,
as built for agents, the gate and the desk's answers), defaulting to the
desk's current mode, settable per Program. The engine decides everything it
can decide by rule at its level; what it cannot decide by rule, or what is a
**core question**, goes to him. "Decided for you" is a fold in the window
and a section in the note: every engine decision, with its rule, and an
**Overturn** verb on each for as long as it can still be undone.

**A core question** is any of these, at every level:
- the goal: a step would change what the Program is for, or a finding says
  the goal is wrong;
- the shape of the work: a step would touch files outside the Program's
  repository or outside what its steps own, or the engine would need to add
  a step the plan did not have (YOLO may add a step and tell him; Normal
  asks);
- egress beyond the step's own PR: sending to a person, posting, publishing,
  a message that leaves the device (the owner's standing rule);
- money: a paid engine or harness beyond the Program's `spend_limit_usd`
  (Automations' field, reused), or any spend when the limit is unset;
- authority or config: a tool call the gate holds (as built), a change to
  Settings, a credential;
- safety: a reviewer finding tagged security or data-loss, a test deleted,
  a migration that drops or rewrites rows;
- no rule: the engine has no rule for the choice (a question from an agent
  the desk's draft cannot answer, a finding it cannot classify).

What each level decides without him (everything above still comes to him):

| Decision | Secure | Normal | YOLO |
|---|---|---|---|
| start, re-brief, run the gate, start a reviewer, park a lost racer | engine | engine | engine |
| open the step's PR on his own repository | engine | engine | engine |
| merge on green + PASS | him | engine | engine |
| REQUIRED finding | round 2 to the builder, then him | round 2, then him | round 2, round 3, then him |
| SHOULD finding | him | engine: **Later** (a Door task) | engine: fix if the round is open, else Later |
| NOTE finding | engine: Skip, logged | engine | engine |
| a routine agent question (which file, which name, proceed?) | him | the desk's draft is typed (`AgentResponder`, ROUTINE class) | typed |
| an approval the gate can allow by its own rules (read, build, test) | him | engine | engine |
| a failed check round | round 2, then him | round 2, then him | round 2, round 3 with a fresh worktree, then him |
| a step that fails after the rounds | him | engine parks it, carries on with the rest, one row to him at the end | same, and the engine tries one re-plan of the step (a smaller brief) before parking |
| a race winner | him | engine | engine |
| adding a step the plan lacked | him | him | engine adds it and says so in the note |
| the Program's Done | him (he closes) | engine | engine |
| a core question | him | him | him |

The desk's rule for **what is routine** is the one that exists
(`agent_responder.AgentResponder`: a ROUTINE draft is typed under YOLO and
Normal, a NON-ROUTINE draft waits); Programs add no second classifier for
agent questions. For findings and failures the rule is the table above,
coded in `program_rules.py` as one function `decide(level, kind, facts) ->
Decision | CoreQuestion`, with its own tests per row.

**Overnight on the home box** runs at YOLO: he wakes to merged PRs, a note
that says what was decided for him and why, and at most the core questions
in Needs you. A Program at Secure is for a repository he does not trust the
engine with yet.

Every engine decision is a checkpoint line with `by: engine` and a kernel
operation (`program.step` with the step as target), so the Processes window
and the kernel journal carry the provenance (DeckHand, future-agi).

### Runs on: any agent, any engine (owner 2026-10-28: "we could use any of our engines there too, right? E.g. that qwen we have. I want to keep using it on its down time")

Every role in a Program (a step's builder, its reviewer, a race contender) is
a **Runs on** choice, and the choice is the same vocabulary the desk already
uses for Runs on everywhere else:

| Runs on | What runs | Where it runs |
|---|---|---|
| **Claude Code** | the `claude` harness (`claude-default` profile) | Anthropic |
| **Codex** | the `codex` harness (`codex-default`) | OpenAI |
| **pi on <engine>** | the `pi` harness (`pi-default`) with the hub's engine of choice | any engine in his library that is OpenAI-compatible: the home box's qwen3.8-27b over Tailscale (`engine-tailscale-karol-8080`), a LAN llama.cpp, a hosted model |
| **the desk's assignment** | pi on whatever `agent.code` is assigned to right now | Settings ▸ Runs on |

In data: `program_steps.profile` (the harness profile) and `program_steps.engine`
(an engine profile id, only meaningful for pi; NULL = the desk's `agent.code`
assignment). The same two fields exist on the Program as the defaults
(`default_profile`, `default_engine`, `reviewer_profile`, `reviewer_engine`).
The faces show one picker, **Runs on ▾**, that lists the three harnesses and,
under pi, the engines from the model library with their readiness word (the
Engines window's own list, same words, same sprites). A step's row shows the
engine's name beside the agent sprite ("pi · qwen3.8-27b on karol").

**Down time.** A Program or a step may say **when idle** (`prefer_idle: 1`):
its pi steps are dispatched only when the chosen engine reports idle through
the hub's engine lanes (`holdspeak/engine_lanes.py`: the background lane is
free and no foreground inference holds the slot) and are held in **Ready ·
waiting for qwen** otherwise; a foreground use (his dictation, Ask) always
wins the slot, and the step resumes on the next tick. This is how the home
box earns its keep overnight: a Build-and-review Program with the builder on
Claude Code and the reviewer on pi · qwen when idle, or the whole refactor
on qwen alone while he sleeps. YOLO is what lets that run to merge without him.

The default pairing stays a default only: Codex reviews Claude Code, Claude
Code reviews Codex, and both can be replaced by pi on any engine, per step.

### The desk's tools are the agents' tools

Every agent a Program launches gets the HoldSpeak MCP injected for its
harness (`holdspeak/delivery/agent_mcp.py`, as built), so a step's agent
has the whole desk: `program.checkpoint` and `program.step_done` for its own
step, `agent.start_helper` / `agent.prompt` / `agent.wait` / `agent.read`
(AG11) for a helper, `door.add_item` for a task it finds, `note.*` for what
it learns, `people.*` and `meeting.*` to read context, the read-only
`kernel.receipt`. An orchestrating agent (a launch handed "run this as a
Program", or an external MCP client such as Claude Code at his keyboard, or
Astra over codex) drives the engine through the `program.*` family of §7
through the same server. The one rule holds for all of them: egress,
authority and config tools stop for his press (the owner's 2026-09-29
ruling), `program.decide` is his alone, and a step's agent cannot touch
another step's record.

## 7. The desk's tools for agents (MCP family `program`)

Through the one service layer (MCP flows through services). In the CONDUCTOR
palette, callable by the owner and by a launch credential:

| Tool | Does | Who |
|---|---|---|
| `program.create` | title, goal, repository (a project's repository or a path), base branch, control, check command, default Runs on (profile + engine), reviewer Runs on, `prefer_idle`, template | owner; an orchestrating agent |
| `program.plan` | replace or append steps: title, brief, owns, after, Runs on (profile + engine), `prefer_idle`, effort, race, gate kinds; `size: auto` | owner; orchestrating agent |
| `program.start` / `program.park` / `program.resume` | the obvious | owner; an orchestrating agent may start the Program it created |
| `program.get` / `program.list` | the Program with its steps, checkpoints, your-turn items | anyone |
| `program.checkpoint` | one line on the calling step | the step's own launch (by its credential), the engine, the owner |
| `program.step_done` | the step's launch says it is done, with its report | the step's own launch; the engine still waits for the commit receipt |
| `program.decide` | a finding: fix_now / later / skip; a merge: merge / not_yet; a parked step: resume / skip | owner only |

An orchestrating agent (an Opus launch handed "run the refactor as a
Program") can `program.create`, `program.plan`, `program.start`, then
`program.get` while its steps run; it never prompts a step's agent directly
(the engine does), and it cannot `program.decide`.

## 8. The handover note (living-map, DeckHand, roost)

One desk Note per Program, titled "Program: <title>", id
`program-<id>`, rewritten on every change by the engine, never by hand:

```
# Program: The hub stops stalling

Running · 2 of 6 steps done · 1 waits on you

## Your turn
- Step 3 "Projections off the loop": merge? (PR #1591, check green, review passed)

## Steps
1. Indexes — Merged #1585 · Claude Code · 41 min
2. Retention — Merged #1585 · Claude Code · 41 min
3. Projections off the loop — PR open #1591 · Codex · 23 min · "ran the sweep twice, both green"
4. People routes — Working · Codex · 12 min · "31 handlers, 20 done"
5. Projects routes — Ready
6. The fan-out — Planned (after 4, 5)

## Parked
(none)

## Decided for you
- 19:09 · merged step 3 (check green, review passed) · rule: Normal merges on green+PASS
- 18:40 · SHOULD finding on step 2 → Later (Door task) · Overturn

## Last checked
2026-10-28 17:40 · engine
```

The note is the one place a new chat, a new agent, or he, after a day away,
reads first. It links each step to its lane window and its PR.

## 9. The faces

Built in the kit, nothing hand-rolled (UX-CANON §B). Two windows and three
seams.

### Programs (the app window, `surface-programs`, verb `open-programs`, ⌃7)

A ListView of Programs, waiting-first (DeckHand): Your turn, then Running,
then Drafting, Done, Parked; within a band the most recently changed on top.
A row: title · StateChip · "3 of 6 steps" · elapsed in state · the last
checkpoint line. Toolbar: **New program** (opens the Program window in
Drafting with the Fast cycle template), **Templates** fold. Status bar: the
counts that are not zero, and the Dock lamp's word. Empty: "No program yet.
A program is a goal cut into steps, each handed to an agent. Start one from
a goal, or hand this desk's open work as a program" with one Button.

### The Program window (`pullout:program:<id>`)

Title bar: the title (editable in Drafting). Toolbar: **Start** / **Park** /
**Resume**, **Add step**, **Race** (on the selected step), **Control: YOLO ▾** (Secure · Normal · YOLO).

Content, top to bottom:

1. **Your turn** well (only when non-empty): one row per item with its
   verbs inline: Merge / Not yet; Fix now / Later / Skip; Answer (opens the
   lane's wait well); Resume / Skip.
2. **The board**: steps as rows in order, each with a station track like the
   lane's (BRIEF · WORK · CHECK · REVIEW · PR · MERGE) with the current
   station lit and the ones passed drawn, the agent's sprite and name, the
   elapsed time, the checkpoint line, and the Open verb (the lane window).
   Dependencies as "after 2, 3" in the row's eyebrow. A race shows the
   contenders as indented rows under the step.
3. **Decided for you** fold: every engine decision with its rule and an **Overturn** verb while it can still be undone (a merge cannot; a Later task, a Skip, a parked step, an added step can).
4. **Checkpoints** fold: every line, newest first, with by (agent sprite,
   engine mark, his portrait) and time.
5. **Gate** fold on a selected step: the check command, the last log's
   verdict, the sections as DotWords (build · vitest · pytest · sweep ·
   canon · repo), and **Open log**.

Status bar: `Running · 2 of 6 done · 1 waits on you · check: quick_check.sh ·
control Owner`. At 393 the board is the screen; the station track becomes
the StateChip and the lane opens full-screen.

Delight: the station track's lit station breathes the same way the Record
orb does; a step that merges draws its MERGE station in the success colour
with the PR number; the Programs row for a finished Program shows a small
"Done in 1 h 12" word; the empty state has the telephone-sprite's sibling, a
"program" sprite (a stack of three cards with a lit one) drawn by
`gen-icons-d.py`.

### Seams

- **Needs you**: `program_items` in `needs_you_membership.compose`: merge
  asks, findings left, parked-after-failure, with the Program's title as the
  group and the verbs above. The Door's "due word" for them is "now".
- **Today**: "Programs: 1 running, 1 waits on you" as a line in Since
  morning when any Program moved today.
- **Agents** (the Conductor): an agent that belongs to a step shows "Step 4
  of The hub stops stalling" under its name and Open goes to the Program.
- **Dock**: the Agents lamp takes the worst Program state too.

## 9b. The Program in the ecosystem (owner 2026-10-28: "think how to integrate that whole concept into the overall ecosystem … linked to projects … linked to a person")

A Program is a desk object like a meeting or a note: it has a place, an
origin, people, and it leaves things behind. Nothing here is a new face; it
is the same seams every other object uses.

### Where it lives: the Project

- `programs.project_id` is the Program's home. A Program made from a Project
  takes the Project's repository and base branch (the hand's
  `project_repository`); a Program made from a goal without a project is
  filed under the Project the repository belongs to when there is one, else
  it stays unfiled and the Programs window shows "No project" as a Token he
  can press to file it (the zone's `zone_file`, as notes do).
- The Room (`project_get_room` / the Project drawer) gets a **Programs** fold:
  one row per Program with its state and "n of m", the worst state first;
  the Room's Needs you well carries the Program's your-turn rows.
- The handover note is filed to the Project (`notes.project_id`), so it is
  in the Project's memory and in the steward's reading. The steward's
  update draft (`project_update_drafter`) gets a "Programs" paragraph: done,
  running, waiting, with PR numbers; the Monday brief's project line counts
  running Programs.
- **From the desk** (template §10) makes one step per open action of the
  Project; a step whose origin is an action closes that action on merge with
  the PR as evidence, exactly as the hand closes its origin item today
  (`follow_through.sweep_merged`).

### Where it came from: the origin

`programs.origin_ref` names what started it: `meeting:<id>` (its actions
became the steps), `decision:<id>` (a decision whose work this is;
`decision_record.link_work` attaches the PRs as the decision's work),
`note:<id>` (a note he wrote the goal in; "Run as a program" is a verb on
the Note's toolbar fold), `project_item:<id>`, or nothing (a goal typed in
the window). A step's `origin_ref` is the action or item it came from. The
Program window's status bar says the place line the Note has: "Project ▸
HoldSpeak · from the meeting of Tue 28 Oct · for Alice".

### Who it is for: the person

- `programs.for_person_id` and `program_steps.for_person_id` (nullable): the
  person this work is owed to (a report who asked, a stakeholder, a reviewer
  who must sign off). The person's room (People window, the 1:1 prep) gets a
  **Programs** line under their commitments: "The hub stops stalling · 4 of
  6 · PR #1591 waits on you", and the 1:1 brief (`people_one_on_one_brief`)
  lists it under "To show them" when a step merged since the last 1:1 and
  under "To ask" when a finding waits on a decision they own.
- A step may also name the person as its **reviewer of record**: a human
  review gate (`gate_review = 'person'`): the step waits in his Needs you as
  "Ask Alice to review PR #1591" with the Send verb (a prepared send through
  the channel, his press), and the merge waits for the PR's approval from
  that GitHub login (follow-through reads reviews; the login comes from the
  person's `github` alias in People).
- Findings decided **Later** become a Door task for him, filed to the Project
  and to the person when the step names one; **Skip** writes one line to the
  Program's note under Decisions with the reason he typed (no decision
  record in this PR; a later slice may promote skips to proposed decisions).

### What it leaves behind

- Every merged step is a Result (AG10) on Today and in the person's and
  Project's timelines; the Program's Done is one Result with the PR list.
- The handover note stays as the Program's record; on Done the engine
  appends "Done · <date> · <n> PRs · <time>" and files it; the memory
  conductor reads it like any note (nothing new to build).
- The Week (chair:week) counts Programs done this week; Since morning shows
  Programs that moved today.

### What drives it from the ecosystem (later slices, named here so the schema fits)

- Automations: a Do kind **Run a program** (template + Project), on a
  schedule or a Watch event (a Jira epic moves to Ready → From the desk).
- A Calls turn: "start the overnight program on the hub" is `program.start`
  behind his spoken yes (the Calls gate, as built).
- Decisions: a skipped finding or an engine merge may become a proposed
  decision record.

Schema for this PR: `programs.origin_ref TEXT NULL`, `programs.for_person_id
TEXT NULL`, `program_steps.origin_ref TEXT NULL`, `program_steps.for_person_id
TEXT NULL`, `program_steps.gate_review` gains the value `'person'`, plus
`notes.project_id` on the handover note. No new tables.

## 10. Templates (`holdspeak/program_templates.py`)

| Template | Steps | Gate | Reviewer |
|---|---|---|---|
| **Fast cycle** (HoldSpeak's own) | one step per brief he pastes | the repository's check command | none; the desk's Control mode |
| **Build and review** | one step per brief; reviewer `codex-default` at depth `delta` | check | Codex |
| **Race** | one brief, `race: 2` (Claude Code, Codex) | check | none |
| **Overnight on the home box** | one step per brief; builder pi · qwen when idle, reviewer Claude Code at depth `delta`; YOLO | check | Claude Code |
| **From the desk** | one step per open action of a project (AG14's items), owns unset | check | none |

A template is a Python descriptor, like `workbench_templates.AGENT_STARTERS`;
no YAML.

## 11. The contract for the lanes

### Tables (`holdspeak/db/schema.py`, minimal migration: three tables, one index)

```
programs(id TEXT PK, title, goal_markdown, project_id NULL, repo_root, base_branch,
         control 'secure'|'normal'|'yolo', spend_limit_usd REAL NULL, check_command NULL, reviewer_profile NULL, reviewer_engine NULL,
         default_profile, default_engine NULL, prefer_idle INT DEFAULT 0, state, note_id NULL, revision INT, created_at, updated_at)
program_steps(id TEXT PK, program_id FK, ordinal INT, title, brief_markdown,
         owns_json, after_json, profile NULL, engine NULL, prefer_idle INT DEFAULT 0, effort, race INT DEFAULT 0, race_of NULL,
         gate_check INT DEFAULT 1, gate_review INT DEFAULT 0, gate_merge 'owner'|'auto'|'none',
         state, launch_id NULL, worktree NULL, branch NULL, pr_url NULL, pr_number NULL,
         check_log NULL, check_verdict NULL, review_verdict NULL, findings_json,
         rounds INT DEFAULT 0, parked_reason NULL, started_at, ended_at, updated_at)
program_checkpoints(id INTEGER PK, step_id FK, at, by 'agent'|'engine'|'owner', line)
CREATE INDEX idx_program_steps_program ON program_steps(program_id, ordinal)
```

### REST (`holdspeak/web/routes/programs.py`, every handler through `run_in_threadpool`)

```
GET    /api/programs                         list (waiting-first order is the service's)
POST   /api/programs                         create {title, goal, repository|project_id, base_branch, control, check_command, template}
GET    /api/programs/{id}                    the program, steps, checkpoints, your_turn
POST   /api/programs/{id}/plan               {steps:[…], size:"auto"|null, replace:bool}
POST   /api/programs/{id}/start | /park | /resume
POST   /api/programs/{id}/steps/{sid}/checkpoint {line}
POST   /api/programs/{id}/steps/{sid}/decide {kind, choice, finding_id?}
POST   /api/programs/{id}/steps/{sid}/race  {n}
```

Each new route gets its residual-set entry (`docs/internal/philo/phase-5/
residual-set.json`), an aware clock (`local_now`), and the api-surface regen.

### Frame

`program_changed` {program_id, step_id?, state, your_turn: int} in
`RUNTIME_FRAME_TYPES` and `frames.ts`, consumed by the Programs window, the
Program window and the Dock lamp. Also `desk_changed("program", id, verb)`
for the generic listeners.

### MCP

`holdspeak/mcp/families/program.py`, the tools of §7, through
`ProgramService`; palette CONDUCTOR; `program.decide` owner-only in
`tool_authority.py`; `program.checkpoint` and `program.step_done` accept a
launch credential only for the step that launch belongs to.

### Hand kind

`agent_operations.AGENT_HAND` accepts kind `program_step`; `agent_brief.
compose_agent_brief` delegates to `program_brief.compose` for it;
`AgentHandService._hand` resolves the repository from the Program, names the
worktree `hs-program-<step id>` and the branch `program/<program slug>/<step
ordinal>-<step slug>`, and passes `start_point=base_branch`.

## 12. The slices (one PR, three lanes on one branch)

| Lane | Owns | Done when |
|---|---|---|
| **PG-HUB** | `holdspeak/services/program_service.py`, `program_runner.py`, `program_brief.py`, `program_verifier.py`, `holdspeak/program_templates.py`, `holdspeak/db/schema.py` (+ snapshot), `holdspeak/db/programs.py`, `holdspeak/web/routes/programs.py`, `holdspeak/mcp/families/program.py`, `agent_operations.py` (kind), `agent_hand_service.py` (kind), `needs_you_membership.py` (`program_items`), `workbench_conductor.py` (tick), `realtime_frames.py`, `runtime/composition.py` (frame), tests | a Program of three steps (one after the other two) runs against the fake agent rig: both first steps hand, their fake commits pass a fake gate (a script that writes a green log), the reviewer fake PASSes, the merge ask lands in Needs you, `program.decide merge` moves them to merged (the follow-through fake), the third step dispatches, the note is rewritten at each change; a red gate goes to round 2 then parks with a Needs you row; a race of 2 parks the loser |
| **PG-FACES** | `web/src/desk/programs/` (ProgramsWindow.tsx, ProgramWindow.tsx, StepRow.tsx, StationTrack.tsx, api.ts, types.ts, programs.css, `__fixtures__/` recorded from the hub lane's rig), `applications.ts` (surface-programs, the pullout family `program:`), `pullouts/registry.ts`, `runtime/frames.ts`, `needsYou.ts` (program rows), the Conductor row's step line, the Dock lamp, `gen-icons-d.py` (the program sprite), `calls.app.test.tsx`-style `programs.app.test.tsx`, sweep cases `surface-programs` and `pullout:program` at 1440 and 393 | every state of §4 drawn from recorded fixtures; the your-turn verbs press through to the rendered outcome; still, fit, contrast, 44 px at 393 |
| **PG-ECO** (inside PG-HUB and PG-FACES by file ownership) | hub: `origin_ref`, `for_person_id`, the Room's Programs fold data, the steward paragraph, the 1:1 brief lines, the action close on merge, the note filed to the project; faces: the Room fold, the person room line, the Note's "Run as a program" verb, the status-bar place line, "No project" token | a Program made From the desk closes its actions on merge; the person's 1:1 brief lists the merged step; the Room shows the Program |
| **PG-DOCS** | `docs/internal/betterment/programs/{PROGRAMS-DESIGN-2026-10-28.md (this), RECIPE.md}`, `docs/programs.md` (user doc, ASD-STE100), `docs/internal/UX-CANON.md` (a line under Shipped), `agent/skills/holdspeak-programs/SKILL.md` (how an agent drives a Program over MCP), `CLAUDE.md` (the `HOLDSPEAK_PROGRAMS=off` switch beside the others), `pm/STATUS.md`, the api-surface and OpenAPI regen, the graph atlas citation if a new edge | docs current; `scripts/gen_docs.sh` clean |

Sequence: PG-HUB first (the contract and recorded fixtures), PG-FACES and
PG-DOCS in parallel on the hub lane's fixtures, then one merge into the
program branch, one quick check, the whole browser suite, one PR.

## 13. What he presses

1. The Programs window opens from the Dock's Agents group and ⌃7; New program
   asks for a goal and a repository; the Fast cycle template is picked.
2. He pastes briefs as steps, or presses "From the desk" and picks a project.
3. Start. The board fills; each step's agent appears in Agents too.
4. Anything that needs him is in Needs you with its verbs; the Program's
   note on his desk says the same in prose.
5. At Secure he merges; at Normal and YOLO the engine merges and tells him
   under Decided for you. Done.

The first Program is HoldSpeak's own refactor program, re-created from this
PR's own steps so the engine's first run is the engine's own history.

## 14. Decisions for the owner (defaults chosen; say if another is wanted)

1. Control is the desk's Control mode ladder (Secure · Normal · YOLO), per
   Program, defaulting to the desk's current mode; only core questions reach
   him at any level (owner's word, 2026-10-28).
2. Two rounds before "Your turn", for the gate and the review alike.
3. The gate's verifier is strict: no log path, not green.
4. The engine's own reviewer defaults to Codex when the builder is Claude
   Code, and to Claude Code when the builder is Codex; any role can be pi on
   any engine, and a Program can prefer an engine's idle time (owner's word,
   2026-10-28).
5. A race never exceeds three contenders.

## 15. How we know it worked

- The PR's own quick check and the whole browser suite green.
- The rig Program of §12 runs end to end in the unit tier with fake agents.
- On his desk: the refactor Program recreated from this PR's steps shows
  Done with its merged PR numbers; a new Program from a goal reaches Your
  turn with a merge ask within one tick of the fake gate.
- Astra's post-merge review finds no missing receipt: every state change
  in a Program has a kernel operation and a checkpoint line.

## Built, 2026-10-28

The engine lane (PG-HUB, with the hub half of PG-ECO) built §3 to §11 on
`lane/programs-20261028` (merge `be286204b`). The design's intent stands;
this section names where the build differs from the text above, and why.
The faces lane (PG-FACES, merge `bad00fb76`) is in "The faces" below.

### Where the build differs

- **The checkpoint column is `by_kind`, not `by`.** `by` is an SQL keyword
  (`ORDER BY`, `GROUP BY`); the column name keeps every query plain. The
  wire key stays `by` (`agent`, `engine`, `owner`), so §8 and the faces read
  as written.
- **More columns than §11 lists.** `programs.closed_at` (when a Program was
  closed, by him or by the engine), `programs.template`, `programs.created_by`;
  on a step `held_reason` (the "waiting for qwen" and "waiting for a free
  agent" words), `parked_by` (`owner`, `engine`, `race`: only an engine park
  is his turn), `facts_json` (the facts the rules read: core questions he
  cleared, a person's approval), `review_depth`, `head_commit` /
  `checked_commit` (the receipt that the check ran on the agent's commit),
  `report` (the agent's `program.step_done` text); on a checkpoint the
  decision columns `operation_id`, `kind`, `choice`, `rule`, `overturnable`,
  `overturned_at`, `undo_json`. A decision is a checkpoint row, so "Decided
  for you" and the Checkpoints fold read one table and no fourth table was
  needed.
- **`gate_review` is text, not an integer:** `none`, `agent` (the Program's
  reviewer) or `person` (§9b's human review gate). One column holds the
  three values §9b needed.
- **`gate_merge` is `level`, `owner` or `none`.** `level` (the default; `auto`
  is accepted as its alias) means the Program's Control level decides the
  merge; `owner` keeps his press for that one step at every level; `none` is
  a step with no PR. "auto" read as "always merges", which is not what the
  level does at Secure.
- **YOLO's third round and the re-plan reuse the step's worktree and
  agent.** §6 says "round 3 with a fresh worktree". The same worktree keeps
  the agent's context and the branch the PR is open on; a fresh worktree
  would lose both and open a second PR. The re-plan is a new, smaller brief
  to the same launch.
- **Spend is a core question only for pi on a hosted engine.** Claude Code
  and Codex run on his own subscriptions, so the engine has no per-call
  spend to compare with `spend_limit_usd`; a local or LAN engine costs
  nothing. pi on a hosted (paid) engine with no spend limit set goes to him
  before the step is handed (`program_runner._spend_core`).
- **More routes and two more tools than §7 and §11 list.** Routes:
  `GET /api/programs/templates`, `PATCH /api/programs/{id}` (the
  `program.update` change), `POST /api/programs/{id}/from-desk` (the From
  the desk template's steps), `POST /api/programs/{id}/close` (his Done at
  Secure), `POST /api/programs/{id}/decisions/{decision_id}/overturn`. Tools:
  `program.update` and `program.overturn`. The family is
  `program.create`, `plan`, `update`, `start`, `park`, `resume`, `get`,
  `list`, `checkpoint`, `step_done`, `decide`, `overturn`; `decide` and
  `overturn` are AUTHORITY (his press). The registry is now 301 tools in 51
  families.
- **`program.decide` takes more kinds than §7 names:** `merge` (merge,
  not_yet), `finding` (fix_now, later, skip), `parked` (resume, skip),
  `ask_review` (prepare: a send is prepared, he presses Send), `core` (go_on,
  park), `race` (pick), `add_step` (add, skip), `close` (close). Each is a
  your-turn kind the §6 table can send to him.

### Taken from Moonfold (PG19)

The handoff of PG19 takes its ideas from Moonfold's provider handoff
(github.com/Mr-Dark-debug/Moonfold, `docs/user/provider-handoff.md` and
`apps/server/src/handoff/`): a fallback order of agents, a limit notice
that offers "Continue in …" beside waiting for the reset, a brief built
from the thread's history without a model so the same thread gives the
same brief, redaction counted by kind and shown before the send, a
divider with View brief, allowed providers per project, never twice for
the same stopped turn, and an optional usage warning. HoldSpeak's words
and code are its own; no Moonfold code was copied. Moonfold is MIT
licensed (Copyright (c) 2026 T3 Tools Inc., Copyright (c) 2026 Moonfold
contributors); the attribution is in `THIRD_PARTY_NOTICES.md`. Where
HoldSpeak differs: the brief is built from the step's record (checkpoints,
his lines, the gate's log, the worktree), not a chat transcript; the next
agent continues on the step's own branch, so there is no new thread; the
levels of the control ladder decide what Moonfold's Ask and Automatic
modes decide.

### What was left out, and why

- **The runner does not tick at once on a coder frame.** It ticks every 30 s
  from the workbench conductor and at once after a press (start, resume,
  decide, overturn) and after the agent's `program.step_done`. A step can
  wait up to 30 s after its agent's turn ends. A frame-driven tick needs a
  hub-side listener on the coder frame; that is a later slice.
- **The desk's answers follow the desk's Control mode, not the Program's
  own level.** `AgentResponder` (a routine draft typed for the agent) and the
  gate (a held tool call) read the desk's one Control mode. A Program at
  YOLO on a desk at Secure still has its agent's routine questions and held
  calls waiting for him. Making both read the Program's level is a change to
  the gate's authority and is left for its own review.
- **A new worktree needs `uv sync --extra dev` and `npm ci`** before
  `scripts/quick_check.sh` can run in it. The engine does not run them; a
  repository's `.holdspeak/program.json` can name a check command that
  does. A gate that cannot build is red, and the log says why.
- **The recorded fixtures carry temporary paths** (the rig's worktrees under
  the test HOME). The faces read the paths as data; nothing depends on them.

### The faces (PG-FACES)

Built in `web/src/desk/programs/` from the recorded fixtures; the shots are
in `docs/assets/programs/` (from the faces lane's
`.tmp/evidence-shots/programs/`). Where the faces differ from §9 and the
canvas:

- **The picker reads "Agent: … ▾", not "Runs on ▾".** The user sees
  "Engines" since betterment E6, and the Engines name guard
  (`tests/unit/test_engines_name_guard.py`) refuses "Runs on" in any built
  string and any user doc. Data and code keep `profile` and `engine`.
- **The place line is plain words at 393; "No project" files the Program
  only at 1440.** At 393 the status bar has no room for ghost Buttons, so
  the line is words and the Token is not pressable there.
- **"0 of 3 done" reads "3 steps".** The zero law (UX-CANON: no counters of
  zero): a count starts to show done only from one.
- **The Open verbs read "Open lane" (a step) and "Open program" (the Room
  and person rows),** not a bare "Open": each names what it opens.
- **Programs opens from Go ▸ Daily (after Agents) and ⌃7.** There is no Dock
  tile of its own; the worst Program state joins the Agents lamp.
- **No race shot.** The hub rig recorded no race fixture, so the race rows
  are not drawn in a shot; the race is proven in the hub tier
  (`test_a_race_of_two_parks_the_loser`).
- **The person line, the Room fold and the Note's "Run as a program" are
  pinned in `programs.app.test.tsx` (and the Note's in
  `note.app.test.tsx`) only;** no browser shot shows them.
- **The canvas's "Control: Owner / Delegate" words** are the ladder's
  Secure · Normal · YOLO on the built window (§6 as amended).


## PG19 Handoff: when an agent runs out (2026-10-28)

Owner, 2026-10-28, on Moonfold: "how could it enhance our Programs and other
pipelines?" Canvas: `canvases/handoff-2026-10-28.html` (1440 and 393).

### What and why

A step's agent can stop at its harness's usage limit: Claude Code's
"limit reached · resets 2pm", Codex's "You've hit your usage limit … try
again at 2:05 PM". Before PG19 the step sat in Working until the reset, or
the engine read the stopped turn as "no commit" and parked it. Overnight on
the home box that is a lost night.

PG19 gives every role an **ordered list of agents** (Runs on, first to
last), reads the limit notice from the agent's own screen, and continues
the step in the next agent: same worktree, same branch, with a
**handoff brief** that HoldSpeak builds without a model from what it
already holds (the step's brief, the goal, the plan and progress, what he
said since, the files changed, `git status`, `git diff --stat`, the last red
check's tail, open asks, the repository's CLAUDE.md or AGENTS.md). The
brief is redacted before it leaves; he sees the counts by kind.

**Recommendation (pre-approved, built):** the list is the Agent picker's
menu ("then Codex" rows under the first choice), not a separate editor;
the limit is a step state of its own (**Limited until 14:00**); the
handoff is a divider line in the Checkpoints fold with **View brief**; at
Normal the Your turn row has **Continue in Codex** as its first press.

### The rules (`program_rules.decide(level, "limited", facts)`)

| Facts | Secure | Normal | YOLO |
|---|---|---|---|
| a next agent is free (on, allowed, not limited itself) | Your turn: Continue in <next> / Wait until <reset> | Your turn, Continue first; after 10 min HoldSpeak continues on its own when the Program **may hand off** | continue at once in the next agent |
| no next agent is left | wait until the reset, and say so | same | same |
| this stopped turn was handed off before | nothing (never twice for one stopped turn) | same | same |
| a usage warning (the share he set is reached, at a turn end) | Your turn | Your turn | continue at once |

Skipped entries: an agent the desk does not have (profile unknown), an
agent the Program does not allow (`allowed_profiles`, default all), and an
agent whose own limit is still on (read on any step of any Program).

### In data

- `program_steps.runs_on_json` and `programs.default_runs_on_json`: an
  ordered list of `{profile, engine}`. The first entry is the old
  `profile` / `engine` pair, which stay readable and are written from it.
- `programs.allowed_profiles_json` (empty: every agent),
  `programs.may_handoff` (default off), `programs.usage_warning_share`
  (default off; a share such as 0.9).
- `program_steps.handoffs_json`: one entry per handoff: `at`, `from`, `to`,
  `reason` (`usage_limit`, `usage_warning`, `by_hand`), `by`, `brief_ref`,
  `brief`, `redacted` (counts by kind), `earlier_turns`, `launch_from`,
  `launch_to`.
- The step state `limited` (station Work, tone warn). Its word is
  "Limited until 14:00", with "· continuing in Codex" while a next agent
  waits for his press or the 10 minutes.

### The pieces

- `holdspeak/agent_context/usage_limit.py`: two notice rules (Claude Code,
  Codex) and the share read; pure, the notice text pinned in tests from the
  harnesses' documented wording (no capture of a real notice is in the
  repository; marked as such in the test).
- The screen record carries the notice (`ScreenRecord.limit`); the flight
  says `limited` with `limit: {until, words, rule}` over the hook's word.
- `holdspeak/services/program_handoff.py`: `gather` (reads the database and
  git), `build` (pure: the same inputs give the same bytes), `redact_counted`.
- `ProgramRunner.handoff`: marks the earlier launch `handed_off`, hands
  the step again through the hand with the brief as its first message
  (`AgentHandService.hand(..., handoff_brief=…)`: the Hand again path, the
  same worktree and branch), records the entry and the checkpoint.
- By hand: `program.handoff(step_id, to, preview)` and
  `POST /api/programs/{id}/steps/{sid}/handoff`, owner only.
