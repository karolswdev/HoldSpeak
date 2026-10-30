# Programs

A program is a goal cut into steps. An agent does each step in its own worktree.
HoldSpeak runs the configured check and review gates, opens a pull request when
the step has a PR gate, and merges only when the step's merge gate and Control
level allow it. What only you can do waits for you in **Needs you**. The program
keeps a note on your desk that tells its state in plain words.

Use a program when one goal is too big for one agent: "make the hub stop stalling", "the words wave", "wave 6 of the atlas".

![The Programs window at 1440: five programs in bands, Your turn first](assets/programs/programs-1440.png)

*The Programs window. The programs that wait on you are on top.*

## What a program has

| Part | What it is |
|---|---|
| **Program** | A goal, a repository, a base branch, a control level, the steps and a handover note. |
| **Step** | One bounded part of the goal: a brief, the files it owns, the agent that does it, an effort and a gate. One step is one agent in one worktree. |
| **Gate** | The step's independent check, review (`none`, `agent`, or `person`), and merge (`level`, `owner`, or `none`) settings. A `none` merge gate finishes without a PR. |
| **Checkpoint** | One line that the agent, HoldSpeak or you write on a step at an important moment. |
| **Your turn** | A thing that only you can do: merge, decide a finding, resume a parked step, answer a core question. |
| **Handover note** | A desk note named "Program: <title>". HoldSpeak writes it again after each change. |

## Start a program

### From a goal

1. Open **Go ▸ Programs** (after Agents), or press ⌃7.
2. Press **New program**. The Program window opens in **Drafting**.
3. Type the goal. Choose the repository (or a project, which gives its repository).
4. Add the steps. Paste a brief for each step. Give each step the files it owns. A step can start after other steps ("after 2, 3").
5. Press **Start**.

### From the desk

Choose the **From the desk** template and a project. HoldSpeak makes one step for each open action of the project. When the pull request of a step merges, HoldSpeak closes its action and keeps the pull request as the evidence.

### From a note

On a note, open the toolbar fold and press **Run as a program**. The note becomes the goal.

### Programs on a schedule

An automation can start a program. In the automation window, press **Edit**, and under **Do** press **Run a program**. Choose the template, the level (Secure, Normal or YOLO; no choice keeps the template's level) and the agent. Type the goal. Then choose **When**: a time ("Every weekday at 23:30"), an event, or only **Run now**.

Each run makes one program and starts it:

- **From the desk** takes the automation's project (a project under **About**) and makes one step for each open action of that project.
- The other templates take the goal from **Do**. They make one step for each item under **About** (a note, an action, a decision). With no items, the goal is the one step.

The run's result is the program: its row in **Results** shows the program and its state now, and a press opens the Program window. The Program window says "From the automation Nightly fixes". While the last program that the automation made still runs, a new run starts nothing and says so.

When the model library has an engine that pi can run on, **New automation** also offers **Overnight on the home box**: each weekday at 23:30, pi builds on that engine when it is idle, Claude Code reviews, and the program runs at YOLO. Its schedule stays off until you turn it on. Phone calls are off for it.

Tools and agents use `automation.create` with `do: "run_program"` and the fields `program_template`, `program_control`, `program_runs_on`, `program_may_call` and `program_may_handoff`. Only you can set the level, the agents and the two permissions.

## Templates

| Template | Steps | Gate | Review |
|---|---|---|---|
| **Fast cycle** | One step for each brief you paste. | The repository's check. | None. The step's merge gate uses your Control level. |
| **Build and review** | One step for each brief. | The check. | Codex reviews each change at the configured depth. |
| **Race** | One brief, two agents (Claude Code and Codex) in two worktrees. | The check. | None. The first contender that satisfies its configured gate wins; HoldSpeak parks the other. |
| **Overnight on the home box** | One step for each brief. pi builds on your home engine when it is idle. | The check. | Claude Code reviews. The program runs at YOLO and its merge gate is `level`. |
| **From the desk** | One step for each open action of a project. | The check. | None. |

You can change all values after you pick a template.

### Overnight on the home box

Use this template for work you want done while you sleep. pi does the steps on
your home engine (for example qwen3.8-27b over Tailscale). Claude Code reviews
each change. The program runs at YOLO and its default step has a check, an agent
review, and a level merge gate, so a green and reviewed step can merge without
you. In the morning you find the merged pull requests, a note that tells what
HoldSpeak decided for you, and only the core questions in Needs you. Phone
escalation is enabled by this template, but it still follows the configured
Reach rules and requires a configured phone path.

## The agent and the engine

Each role in a program (the agent that builds a step, the reviewer, each agent in a race) has an agent, and pi also has an engine. Choose them with **Agent: … ▾** in the Program window's toolbar, or on the step's row:

| Choice | What runs |
|---|---|
| **Claude Code** | The `claude` harness. |
| **Codex** | The `codex` harness. |
| **pi on an engine** | The `pi` harness on an engine from your library: your home engine, a LAN engine, or a hosted model. |
| **The desk's assignment** | pi on the engine that **Settings ▸ This Mac ▸ Engines** gives to code. |

The default pair: Codex reviews the work of Claude Code, and Claude Code reviews the work of Codex. You can change each role on each step.

**When idle.** A pi step with **When idle** starts only when its engine is idle. Until then the step says **Ready · waiting for qwen**. Your own use (dictation, Ask) always gets the engine first. The step starts on the next pass after the engine is idle again.

## When an agent runs out

Claude Code and Codex stop when their plan's usage window is used up. A program can continue the step in another agent.

**The order of agents.** Open **Agent: … ▾** in the toolbar. The first choice runs the step. Under **Then, at a limit**, press each agent that can take over, in order. The button then reads, for example, **Agent: Claude Code, then Codex**.

**What the step says.** When an agent shows its limit notice, the step says **Limited until 14:00**. HoldSpeak reads the notice on the agent's own screen.

**What happens next** depends on the control level:

| Control | What HoldSpeak does |
|---|---|
| **Secure** | A Your turn row asks you to continue in the next configured agent or **Wait**. |
| **Normal** | The same row. If the program **may hand off on its own**, HoldSpeak continues after 10 minutes. |
| **YOLO** | HoldSpeak continues at once in the next agent and writes it under Decided for you. |

HoldSpeak skips an agent that the desk does not have, an agent that the program does not allow, and an agent that is at its own limit. If no agent is left, the step waits until the reset time. When the limit resets, HoldSpeak tells the agent to continue.

HoldSpeak moves a stopped turn one time only. It never moves the same turn two times.

**The handoff brief.** The next agent works in the same worktree, on the same branch. It does not get the conversation of the earlier agent. It gets a brief that HoldSpeak makes from the step's record, without a model: the goal, the step's brief, the plan and its progress, what you said, the files that changed, `git status`, `git diff --stat`, the end of the last red check, the open questions, and the repository's CLAUDE.md or AGENTS.md. HoldSpeak removes keys, tokens, passwords and private keys from the brief before it sends it.

In the Checkpoints fold, a handoff is one line: **Step 1 · Handed to Codex · usage limit**. Press **View brief** to read the brief that was sent, what was removed (for example "Redacted: 2 keys, 1 token") and how many earlier turns it does not include.

**Allowed agents.** In Drafting, the **Allowed agents** fold sets which agents
may receive this repository's context. An empty list means every agent that the
desk has. Turn an agent off for a repository whose code must stay with one
company.

**Checkpoint refs.** Each checkpoint on a step also keeps the step's worktree as it is at that moment: the commits, the changes that are not committed and the new files (git's ignored files stay out). HoldSpeak writes it to a hidden ref, `refs/holdspeak/checkpoints/<step>/<n>`, through a temporary index. Your working tree, its index and its branch do not change. If git cannot write the ref, the checkpoint keeps a note and the step continues. In the Checkpoints fold, a row with a ref shows its short commit; the full ref is in its title. A handoff brief names the ref that the next agent continues from, and **View brief** shows it. Press **Start from here** on a row to add a new step that has the same brief and agent; its worktree starts at that ref, on a new branch. The step's own agent can ask for the same thing (`program.start_from`): at YOLO, HoldSpeak adds the step and shows it under Decided for you; at Secure and Normal, you decide. HoldSpeak does not remove old refs yet.

**By hand.** A tool or the API can move a running step to another agent (`program.handoff`, or `POST /api/programs/{id}/steps/{sid}/handoff` with `preview: true` to read the brief first). Only you can do this; an agent cannot.

## The steps and their states

A step goes through six stations: BRIEF · WORK · CHECK · REVIEW · PR · MERGE. The board shows the stations as dots. The lit dot is the current station.

| The step says | What it means |
|---|---|
| **Planned** | The steps it waits for are not done. |
| **Ready** | It can start. It waits for a free agent. |
| **Working** | The agent works on it. |
| **Asks you** | The agent waits for you. The row is in Needs you. |
| **Limited until 14:00** | The agent stopped at its usage limit. See "When an agent runs out". |
| **Checking** | The agent made a commit. The check runs in the worktree. |
| **Check failed** | The check log is not green. The agent gets the end of the log and tries again. |
| **In review** | A reviewer reads the change. |
| **Findings** | The reviewer found problems. The agent gets them and tries again. |
| **PR open** | The pull request is open. HoldSpeak waits for CI. |
| **Merge?** | The step waits for your merge. |
| **Merged** | The pull request merged. |
| **Parked** | You parked the step, or HoldSpeak parked it after it failed. |

The program is **Drafting**, **Running**, **Your turn**, **Done**, **Parked** or **Failed**. The worst state of its steps shows in the Programs list and on the Dock.

A step moves on a receipt, not on a claim. "Done" from the agent is not enough: HoldSpeak waits for a new commit on the step's branch. "Green" is a green check log. "Merged" is the merge that GitHub reports.

![The Program window at 1440: the Gate fold of a step whose check failed, and one agent that asks you](assets/programs/program-running-gate-1440.png)

*A running program at YOLO. Step 3's check failed in the Pytest section; the Gate fold shows the command, the verdict and each section. Step 5 waits for its idle engine.*

On a phone, the board is the screen and each step shows its state as one word:

![The Program window at 393](assets/programs/program-running-393.png)

## Your turn, and what is a core question

HoldSpeak decides what it can decide by rule at the program's control level. A **core question** always comes to you, at every level:

- **The goal.** A step would change what the program is for, or a finding says that the goal is wrong.
- **The shape of the work.** A step touches files outside the repository, or files that no step owns.
- **Egress.** A step would send something beyond its own pull request: a message to a person, a post, a publish.
- **Money.** pi on a paid engine, and the program has no spend limit, or the cost is more than the limit.
- **Authority or settings.** The gate holds a tool call, a change to Settings, a credential.
- **Safety.** A finding about security or data loss, a deleted test, a migration that drops or changes rows.
- **No rule.** HoldSpeak has no rule for the choice.

Each item of your turn is a row in Needs you, in a group with the program's title. It is also on top of the Program window, with its verbs: **Merge** / **Not yet**, **Fix now** / **Later** / **Skip**, **Go on** / **Park** for a core question, **Resume** / **Skip**, **Answer**.

![The Program window at 1440: Your turn with a merge, two findings and a core question](assets/programs/program-your-turn-1440.png)

*Your turn at Secure: a merge, a REQUIRED and a SHOULD finding, and a core question (a step touched a file that no step owns).*

**Open lane** on a step opens that agent's lane window. **Open program** in a project's Room or a person's room opens the program. In Agents, the "Step 4 of …" line under an agent opens it too.

## The control ladder: Secure, Normal, YOLO

A program uses your desk's control mode when you make it. You can change it for each program with **Control ▾**.

| Decision | Secure | Normal | YOLO |
|---|---|---|---|
| Start, brief again, run the check, start a reviewer | HoldSpeak | HoldSpeak | HoldSpeak |
| Open the step's pull request on your repository | HoldSpeak | HoldSpeak | HoldSpeak |
| Merge when the check is green and the review passed | You when `gate_merge=level` or `owner` | HoldSpeak when `gate_merge=level`; you when `owner` | HoldSpeak when `gate_merge=level`; you when `owner` |
| A REQUIRED finding | Two rounds for the agent, then you | Two rounds, then you | Three rounds, then you |
| A SHOULD finding | You | HoldSpeak: **Later** (a task for you) | HoldSpeak: fixed in the open round, else Later |
| A NOTE finding | HoldSpeak: Skip | HoldSpeak: Skip | HoldSpeak: Skip |
| A routine question from the agent | You | HoldSpeak types the desk's draft | HoldSpeak types the desk's draft |
| A tool call that the gate can allow by its rules | You | HoldSpeak | HoldSpeak |
| A failed check | Two rounds, then you | Two rounds, then you | Three rounds, then you |
| A step that still fails | You | HoldSpeak parks it, the other steps go on | HoldSpeak tries one smaller brief, then parks it |
| The winner of a race | You | HoldSpeak | HoldSpeak |
| A step the plan did not have | You | You | HoldSpeak adds it and tells you |
| The program is done | You close it | HoldSpeak | HoldSpeak |
| A core question | You | You | You |

Use Secure for a repository where you do not trust the engine yet. Use YOLO when you want HoldSpeak to do as much as possible without you.

The agents of a program's steps follow the program's level, not your desk's control mode. This applies to their routine questions and to the tool calls that the gate holds. A program at Secure on a desk at YOLO sends each question and each held call to you. A program at YOLO on a desk at Normal gets the desk's draft typed and the calls that the YOLO rules allow. Agents that are not in a program continue to use your desk's mode. Each answer or call that HoldSpeak gives for a step is a line in **Decided for you**, for example "Answered for you: …" or "Allowed: Bash", with its rule. HoldSpeak writes one "Allowed" line for each tool and rule on a step. Note: file edits in the step's own worktree follow your desk's mode at the time the agent starts.

## Decided for you, and Overturn

Each decision that HoldSpeak makes for you is a line in the **Decided for you** fold of the Program window, and in the handover note. Each line gives the rule. While a decision can be undone, it has an **Overturn** verb: a Later task, a Skip, a parked step, or an added step. A merge cannot be undone.

## Phone escalation

A program or step may set **May call**. This only permits the engine to ask
the Phone service to call where the Reach rules allow it; it does not force a
call. Secure does not allow an unattended program call. The owner's
**Settings > Calls > Phone > Reach you** choices, quiet hours, reply state,
repeat window, active-call state, and the configured phone/Line path still
apply. Without a paired phone or configured Line, the call is held or falls
back to a message according to the service result. If **May call** is off, the
program uses the normal message or desk path.

## The gate and its log

Each program has a check command. The default is the `check` command in the repository's `.holdspeak/program.json`, then `scripts/quick_check.sh` if the repository has it.

HoldSpeak runs the check in the step's worktree with an isolated home folder. If the repository has `scripts/test_lock.py`, only one check runs at a time on the machine. The check writes a log to `<worktree>/.tmp/program-check/<step>/<time>.log`. Then HoldSpeak reads the log. The exit code is not enough. The check is green only when:

1. the log names the commit, and the worktree was clean at the start;
2. each section of the check has a result line;
3. no section is red, and no section shows two times;
4. the log ends with the check's own result line.

A check with no log is not green. The **Gate** fold of a step shows the command, the result of each section and **Open log**.

A new worktree has no installed packages. If your check needs them, put a command in `.holdspeak/program.json` that installs them first (for example `uv sync --extra dev` and `npm ci`). Otherwise the check is red, and the log tells why.

## The handover note

Each program has one desk note, "Program: <title>". HoldSpeak writes it again after each change. You do not edit it. It has:

- one line of state ("Running · 2 of 6 steps done · 1 waits on you");
- **Your turn**: what waits on you;
- **Steps**: each step, its state, its agent, its time and its last checkpoint;
- **Parked**: the parked steps and why;
- **Decided for you**: each decision of HoldSpeak and its rule;
- **Last checked**: the time of the last change.

Read this note first after a day away. A new chat or a new agent also reads it first. When the program is done, the note gets one last line ("Done · date · number of pull requests · time") and stays as the record of the program.

## The program on your desk

A program is a desk object, like a meeting or a note.

- **Its project.** A program made from a project uses the project's repository. A program without a project goes to the project of its repository. If there is none, the Program window shows **No project**: on a wide screen, press it to file the program. The project's Room shows a **Programs** fold, and its Needs you rows. The handover note goes to the project's memory. The project's update draft gets a Programs paragraph, and the Monday brief counts the running programs.
- **Its origin.** A program can come from a meeting (its actions are the steps), a decision (the pull requests become the decision's work), a note, or a project item. The status bar of the Program window tells where the program lives and where it came from: "Project ▸ HoldSpeak · From the meeting of Tue 28 Oct · For Alice".
- **The person it is for.** A program or a step can name a person. The person's room shows the program under their commitments. Your 1:1 brief with that person lists a merged step under "To show them", and a finding they own under "To ask".
- **A human review.** A step can name a person as its reviewer. Then Needs you shows "Ask Alice to review PR #1591" with **Send…** (a prepared send; you press Send). The merge waits until that person approves the pull request on GitHub.
- **What it leaves.** Today shows one line, such as "Programs: 1 running, 1 waits on you", on a day a Program moved. Each merged step is a result on Today and in the timelines of the project and the person. A **Later** decision makes a task for you, filed to the project and to the person. A **Skip** writes one line with your reason in the note.
- **Proposed decisions.** When you skip a finding, HoldSpeak makes a proposed decision. When the rules skip a finding that is more than a NOTE, HoldSpeak also makes one, and it names the rule. When the rules skip a NOTE finding, HoldSpeak makes no proposed decision: the note line and the Decided for you row are sufficient. When HoldSpeak merges a pull request by the rule of Normal or YOLO, it also makes a proposed decision. The decision tells the reason, the rule, the level and the step. It is linked to the program and to the pull request of the step. The project's drawer shows it in the **Proposed decisions** fold, with its program and its pull request. Press **Open** to read it in the Decisions window, and accept it there. HoldSpeak does not accept it for you. In the Program window, the row of the decision says "Proposed as a decision". If you overturn a Skip, its proposed decision goes away.

## For tools and agents

The service and web API use `gate_merge: "level"` for merge behavior governed by the Program's Control level.
The current MCP step schema spells that value `"auto"` instead.
MCP callers must send `"auto"`, `"owner"`, or `"none"`; the service normalizes `"auto"` to `"level"`.
This spelling difference does not change the gate's behavior.


The MCP tools are in the `program` family:

| Tool | What it does | Who can use it |
|---|---|---|
| `program.create` | Make a program (title, goal, repository or project, base branch, control, check command, agent and engine, template). | You, or the orchestrating agent |
| `program.plan` | Replace or add steps. `size: "auto"` sets each step's effort by rule. | You, or the orchestrating agent |
| `program.update` | Change the title, goal, control, project, spend limit, agent or engine. | You, or the orchestrating agent |
| `program.start`, `program.park`, `program.resume` | Start, park or resume a program. | You, or the orchestrating agent |
| `program.get`, `program.list` | Read programs, their steps, checkpoints and your turn. | Everyone |
| `program.checkpoint` | Write one line on a step. | The step's own agent, you |
| `program.step_done` | The step's agent says that it is done, with its report. HoldSpeak still waits for the commit. | The step's own agent |
| `program.decide` | Merge, decide a finding, resume a parked step, answer a core question. | You only |
| `program.overturn` | Undo a decision of HoldSpeak. | You only |
| `program.start_from` | Add a step whose worktree starts at a checkpoint's ref. When an agent asks, the control level decides. | You, the step's own agent |
| `program.handoff` | Move a running step to another agent, with the handoff brief. `preview: true` shows the brief and sends nothing. The next agent uses the same worktree and branch. | You only |

An agent can make and start a program, but it cannot decide for you, and it does not prompt a step's agent: HoldSpeak does that. The skill `agent/skills/holdspeak-programs/SKILL.md` tells an agent how to drive a program.

The routes are under `/api/programs` (see [API surface](API_SURFACE.md)). Each change of a program is a `program_changed` frame.

`HOLDSPEAK_PROGRAMS=off` stops the engine: it hands, checks and merges nothing. Test hubs set it.
