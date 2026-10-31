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
| **Requirement** | One sentence that you want true, on a step, on every step or on the whole program, with the way HoldSpeak proves it: a command, the reviewer's answer, a shot of a window, or your word. See "Requirements". |
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

### On a call

On a call, say "start the overnight program". HoldSpeak asks "I want to start the program Overnight on the home box. Say yes or no." and starts it only when you say yes. Say "how is the phone program doing" to hear its state. See [Calls](calls.md#what-a-call-can-do).

### Programs on a schedule

An automation can start a program. In the automation window, press **Edit**, and under **Do** press **Run a program**. Choose the template, the level (Secure, Normal or YOLO; no choice keeps the template's level) and the agent. Type the goal. Then choose **When**: a time ("Every weekday at 23:30"), an event, or only **Run now**.

Each run makes one program and starts it:

- **From the desk** takes the automation's project (a project under **About**) and makes one step for each open action of that project.
- The other templates take the goal from **Do**. They make one step for each item under **About** (a note, an action, a decision). With no items, the goal is the one step.

The run's result is the program: its row in **Results** shows the program and its state now, and a press opens the Program window. The Program window says "From the automation Nightly fixes". While the last program that the automation made still runs, a new run starts nothing and says so.

When the model library has an engine that pi can run on, **New automation** also offers **Overnight on the home box**: each weekday at 23:30, pi builds on that engine when it is idle, Claude Code reviews, and the program runs at YOLO. Its schedule stays off until you turn it on. Phone calls are off for it.

Tools and agents use `automation.create` with `do: "run_program"` and the fields `program_template`, `program_control`, `program_runs_on`, `program_may_call` and `program_may_handoff`. Only you can set the level, the agents and the two permissions.

### From pull requests that merged already

A program can hold work that merged before the program existed. Each merged pull request is one step in the state Merged, with its number and its merge time. No agent runs it. A program of only such steps is Done at once. In the Programs window it says "Merged 14 PRs · 28 Oct", and the fold of each step says "Imported from PR #1584". To make one, run `scripts/program_import_history.py --title "…" --goal "…" --repository <folder> --pr 1584-1598`. The script reads each pull request with `gh` and leaves out a pull request that did not merge. Add `--dry-run` to see the steps first. Tools and agents give `program.plan` a step with `history: {pr_number, merged_at}`.

## Templates

| Template | Steps | Gate | Review |
|---|---|---|---|
| **Fast cycle** | One step for each brief you paste. | The repository's check. | None. The step's merge gate uses your Control level. |
| **Build and review** | One step for each brief. | The check. | Codex reviews each change at the configured depth. |
| **Race** | One brief, two agents (Claude Code and Codex) in two worktrees. | The check. | None. The first contender that satisfies its configured gate wins; HoldSpeak parks the other. |
| **Overnight on the home box** | One step for each brief. pi builds on your home engine when it is idle. | The check. | Claude Code reviews. The program runs at YOLO and its merge gate is `level`. |
| **From the desk** | One step for each open action of a project. | The check. | None. |

You can change all values after you pick a template. Each template also gives each new program its default requirements (see "The template defaults").

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

**Is the notice known on this desk?** Open **Settings ▸ Engines** and press the Claude Code or Codex row. The **Limit notice** line tells you if HoldSpeak read a real stop of that agent on this desk. **Verified · last stop Mon 15:17 · reset Sat 02:00** gives the time of the last stop and the reset time that the notice gave. **Documented · never read here** tells you that HoldSpeak knows only the published wording of the notice. When HoldSpeak reads a stop on the agent's screen, the line changes to verified. Point to the line to see the notice. HoldSpeak keeps the words of the notice, but it removes the times, the dates and the time zone.

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
**Settings > Reach > Reach you** choices, quiet hours, reply state,
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

## Requirements

<!-- PG-REQ (2026-10-31): the hub behaviour below is from the hub build
(holdspeak/services/program_requirements.py, program_service.py,
program_runner.py). The window faces (the Requirements board, the Add
requirement row, Find, the step fold, Move and Insert before) are written as
designed in docs/internal/betterment/programs/PROGRAMS-REQUIREMENTS-2026-10-31.md
§7 to §9; the FACES lane ships them in the same PR. -->

A requirement is one sentence that you want true, with the way HoldSpeak proves it. Examples: "`uv run pytest -q tests/unit/test_program_rules.py` is green", "The People window at 393 has no clipped text", "No new route skips the residual set", "I tried it on my desk".

A step is done only when its check is green **and** each required requirement on the step is **Met** or **Waived**. A program is done only when each step is done **and** each required requirement of the whole program is Met or Waived.

### Where a requirement is

| Scope | When HoldSpeak judges it |
|---|---|
| **Step n** | On that step only, on the step's commit. |
| **Every step** | HoldSpeak copies the requirement to each step that is not merged, and to each step that you add later. Each copy has the same number (R2 on step 3 and R2 on step 5). The board says "5 of 6 steps". |
| **The program** | One time, after the last step is finished (the end check). HoldSpeak runs each Check and Shot in a new worktree at the head of the base branch, `hs-program-<id>-end`. A Review requirement of the whole program comes to you as a Your turn row with **Met** and **Unmet**, because no reviewer reads the base branch yet. |

Each requirement has a number, R1, R2 and so on. A number is not used again in the same program.

### The four kinds

| Kind | How HoldSpeak proves it | The evidence |
|---|---|---|
| **Check** | At CHECK, after the step's check is green, on the same commit. HoldSpeak runs the command in the step's worktree with an isolated home folder. The log goes to `<worktree>/.tmp/program-check/<step>/`. | The log, its commit and its last result line. Press **Open log**. |
| **Review** | At REVIEW. The step's reviewer gets each Review requirement by its number and answers `REQ R3: MET · <one line>` or `REQ R3: UNMET · <what is missing>`. | The reviewer's line, its round and the commit it read. |
| **Shot** | At CHECK. The repository's shot command renders one window at 393 or at 1440. Met when the case is green and the image is there. | The image, the window, the width and the commit. Press **Open shot**. |
| **Your word** | At MERGE (a step) or at the end (the program). A Your turn row asks you. | Your press and its time. |

**A Check log is green only when:**

1. the log names the commit, and the worktree was clean at the start;
2. HoldSpeak's own last line says `program-check: exit 0` (HoldSpeak writes that line, not the agent);
3. no line is red (`FAILED`, `ERROR`, or "n failed" with n more than 0);
4. when the requirement has an expected line (a pattern such as `\b12 passed\b`), one line of the log matches it.

A log that is not there is not green.

**The kind is set by a rule, not by a model.** Text in backticks is a Check with that command. A window name followed by "window at 393" or "window at 1440" is a Shot of that window at that width. All other text is a Review. Only you choose **Your word**. You can change the kind on the row.

A requirement that HoldSpeak cannot prove is not added, and HoldSpeak tells you why: "A check needs a command", "A shot needs a window and a width", "No shot command in this repository".

A Review requirement needs a reviewer. On a step with no review gate, a Review requirement starts the program's reviewer for that step.

### The states

| The row says | What it means |
|---|---|
| **Not yet** | HoldSpeak did not judge it on the step's current commit. |
| **Checking** | HoldSpeak judges it now. |
| **Met** | The evidence says that it is true on the commit that the evidence names. |
| **Unmet** | The evidence says that it is not true. The agent gets it in its next round. |
| **Waits for you** | It is Your word, and it waits for your press. |
| **Waived** | You waived it, with one line. It does not stop the step. It stays on the list, struck through. |

A state changes only on evidence. A requirement is never Met because an agent says so.

**When the commit changes, the judgement goes.** When the step's head commit changes, each Met or Unmet Check, Shot and Review goes back to Not yet. HoldSpeak judges it again on the new commit. Your word stays as you pressed it.

**When you change the sentence, the judgement goes.** A change to the text, the kind, the command or the window sets the requirement to Not yet.

### When a requirement is not met

| What happens | Secure | Normal | YOLO |
|---|---|---|---|
| A Check or Shot is red | The log end goes back to the agent, two rounds, then you | The same | Three rounds, then you |
| The reviewer answers UNMET | A REQUIRED finding for the agent, two rounds, then you | The same | Three rounds, then you |
| The reviewer does not answer for a requirement | You | HoldSpeak asks the same reviewer one more time, then you | As Normal |
| A Check or Shot is still red after the rounds | You: **Send back** or **Waive** | HoldSpeak parks the step, the other steps go on, one row to you | HoldSpeak tries one smaller brief that names the requirement, then parks the step |
| Your word | You | You | You |
| An agent proposes a requirement | You: **Add** or **Skip** | You: Add or Skip | HoldSpeak adds it and writes it under Decided for you |
| Waive a requirement | You | You | You |

An UNMET answer from the reviewer goes through the rounds as a REQUIRED finding. After the rounds, it comes to you as a finding with **Send back** and **Waive**. HoldSpeak does not park the step for it.

**Your word stops the merge at every level, YOLO too.** An overnight program with a Your word requirement on a step merges that step when you press **Met** in the morning. The other steps go on.

**Send back** types the requirement to the step's agent ("HoldSpeak on step 5: R5 is unmet: <the sentence> (<the evidence>). The owner: <your line>") and starts one more round, also after the rounds are used. **Unmet** on Your word does the same.

**Waive** asks for one line: why. That line is the evidence. It goes in the Program window's ledger and in the handover note. Only you can waive. No agent and no rule waives a requirement.

A requirement that you add while a step's pull request is open is judged on the pull request's head. The step goes back through CHECK on the same commit.

### Your turn rows

| Row | Verbs |
|---|---|
| "Step 3 · Projections off the loop: R7 · I tried it on my desk" | **Met** · **Unmet** |
| "Step 5 · Projects routes: R4 is unmet after 2 rounds · <the evidence>" | **Send back** · **Waive** |
| "Codex proposes a requirement on step 4: <sentence>" | **Add** · **Skip** |

The first two rows are also in **Needs you**, in the group with the program's title. An agent's proposal shows only in the Program window's Your turn.

### What the agent reads

The brief of a step has a section "What must be true". It lists each requirement of the step that is not waived, with its number and the way HoldSpeak proves it, then the requirements of the whole program:

```
What must be true (the owner's requirements; HoldSpeak checks each one):
- R2 · The People routes take no lock on the event loop · the reviewer judges it
- R3 · `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green · HoldSpeak runs it on your commit
- R5 · The People window at 393 has no clipped text · the desk sweep renders people-393
- R7 · The owner tried it on his desk · the owner says it
For the whole program (judged after the last step): R1 · …
```

The rules of the brief also say: "Do not claim a requirement is met. HoldSpeak judges each one on your commit."

### The template defaults

| Template | Every step |
|---|---|
| **Fast cycle** | Review: "The change does only what its brief says." |
| **Build and review** | Review: "The change does only what its brief says." · Review: "Each new behaviour has a test." |
| **Race** | Review: "The change does only what its brief says." |
| **Overnight on the home box** | The two of Build and review. |
| **From the desk** | On each step: Review: "The change does what its action asks: <the action's title>". |

A template adds a Review requirement only when its steps have a review gate. Build and review and Overnight on the home box have one, so their requirements are on each new program. Fast cycle, Race and From the desk have no review gate, so they add no requirement. HoldSpeak never starts a second reviewer for a template's default. A template's requirement says "by template". You can change or waive each one.

### `.holdspeak/program.json` for another repository

A repository gives HoldSpeak its own defaults in `.holdspeak/program.json`:

```json
{
  "check": "scripts/quick_check.sh",
  "shot": "DESK_SWEEP_SHOTS=1 uv run pytest -q tests/e2e/test_desk_sweep.py -k \"{case}-{width}\"",
  "shot_image": ".tmp/evidence-shots/desk-sweep/*{case}-{width}*.png",
  "requirements": [
    {"text": "`uv run ruff check .` is green", "kind": "check", "each_step": true, "required": true}
  ]
}
```

| Key | What it does |
|---|---|
| `check` | The step's check command (see "The gate and its log"). |
| `shot` | The command that renders one window. `{case}` is the window and `{width}` is 393 or 1440. Without it, a repository has no Shot kind. |
| `shot_image` | A pattern under the worktree for the image that the shot command writes. The newest file that matches is the evidence. |
| `requirements` | Requirements that each new program of the repository gets. Each item has `text`, and can have `kind`, `spec` (`command`, `expect`, `case`, `width`), `each_step` (default true) and `required` (default true). A Review item is added only when the template's steps have a review gate. An item that HoldSpeak cannot prove is not added. |

HoldSpeak's own file names the desk sweep's shot command. It has no default requirement.

## Find and filter

In the Programs window:

- **Find a program** (with its mic) keeps only the rows that have each word you type. It reads the title, the goal, the project, the persons, the step titles, the pull request numbers (type "#1591") and the template. The window finds locally; each key costs no request.
- **Project ▾** and **Person ▾** keep only the programs of one project or one person. They list only the projects and persons that have a program. **Any project** and **Anyone** remove the filter.
- **Group: State ▾** puts the rows in bands by state (Your turn, Running, Drafting, Done, Parked) or by project ("No project" is last). In a band, the worst state is first, then the newest change.
- The **Met** column says "4 of 5 met" for the required requirements of the program. Each copy of an Every step requirement counts one time, and each requirement of the whole program counts one time. A Waived one counts as met; point to the cell to see "1 waived". Before HoldSpeak judges any of them, it says "7 requirements". A program with no requirement has an empty cell.
- When a filter is on, the status bar says "3 of 12 programs · HoldSpeak · Alice".

At 393, Templates, Project, Person and Group are in **More ▾**.

In the Program window:

- The **Requirements** fold is above the steps. It has the requirements of the whole program, the Every step requirements, and one row for each step that has its own ("Step 4 · 2 of 3 met"). It is open when one is Unmet or waits for you. It is closed with "5 of 5 met" when all are met. The last row is **Add requirement**: type the sentence; the kind follows the rule as you type; choose the scope (The program, Every step, Step n) and press **Add**.
- Each step row on the board has a **Met** cell: "2 of 3", or "3 to meet" before any is met.
- When you select a step, its fold opens with **Brief**, **Requirements**, **Gate**, **Findings**, **Handoffs** and **Ledger**. A part with nothing in it is not shown. The fold opens on the part that needs you first: Gate when the check is red, Requirements when one is Unmet, Findings when one waits for you, else Brief.
- The **Ledger** fold has one part for each step ("Step 3 · 14 lines · last 18:40"). The program's own lines (start, park, plan, the end check) are first.

Tools and agents use `program.list` with `q`, `project_id` and `person_id`, or `GET /api/programs?q=&project_id=&person_id=`.

## Change a running program

What you can change on a step depends on its state:

| Field | Planned, Ready | Started (Briefed to Findings) | PR open, Merge?, Parked | Merged, Done |
|---|---|---|---|---|
| Title | Change | Change (the branch keeps its name) | Change | Change |
| Brief | Change | **Amend brief**: add a line | Frozen: **Send back** with a line | Frozen |
| Owns, After | Change | Frozen | Frozen | Frozen |
| Effort, Race | Change | Frozen | Frozen | Frozen |
| Agent (first) | Change | Frozen: **Hand off** moves it | Frozen | Frozen |
| Agent (then, at a limit) | Change | Change | Frozen | Frozen |
| Check gate | Change | Frozen | Frozen | Frozen |
| Review gate | Change | From none to agent; not from agent to none | Frozen | Frozen |
| Review depth | Change | Change until the review starts | Frozen | Frozen |
| Merge gate | Change | Change | Change (frozen when Parked) | Frozen |
| Requirements | Add, change, waive | Add, change, waive | Add (judged on the PR head), waive | Frozen: add it to the program |
| Place | **Move up**, **Move down**, **Insert before** | Fixed | Fixed | Fixed |
| Person, May call | Change | Change | Change (frozen when Parked) | Frozen |

Point to a frozen field to see why:

- **"The agent has read it."** The agent has its brief, its files and the files of the other steps. A change to the record would not change what the agent was told. An amendment adds; it does not rewrite.
- **"The worktree and the agent are set."** To move the step to another agent, use **Hand off**.
- **"The bar does not come down while it runs."** A gate can only go up. To lower the bar, waive a requirement with a line.
- **"It is merged."** HoldSpeak does not change history.

**Amend brief.** On a started step, press **Amend brief** and type one line. HoldSpeak adds it under the brief and types it to the agent at its next turn end, never into an agent that waits: "The owner on step 4: <your line>". The first brief stays as it was.

**Insert before.** On a selected Planned or Ready step, press **Insert before**. The new step is Planned, in that place. It waits for the same steps as the step after it, and that step now also waits for the new one (**5 waits**, on by default). You cannot insert before a started step: "Step 4 started. Add the step after it."

**Move up, Move down** (`Alt+↑`, `Alt+↓`) on a selected Planned or Ready step. A step cannot go above a step that it waits for; HoldSpeak names that step. The order is the order of reading and the order in which HoldSpeak starts ready steps.

**The numbers follow the order.** Insert and move give each step a new number by its place and change each "after" to match, in one write. A started step whose number changes keeps its branch name and gets one line: "Step 4 is now step 5".

Your change applies at once. A change from an orchestrating agent follows the Control level: at Secure and Normal, a Your turn row asks you (**Apply** or **Skip**, **Send** or **Skip** for an amendment); at YOLO, HoldSpeak applies it and writes it under Decided for you.

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
`program.step_update` takes both `"level"` and `"auto"`.


The MCP tools are in the `program` family:

| Tool | What it does | Who can use it |
|---|---|---|
| `program.create` | Make a program (title, goal, repository or project, base branch, control, check command, agent and engine, template). | You, or the orchestrating agent |
| `program.plan` | Replace or add steps. `size: "auto"` sets each step's effort by rule. `before: <step id>` inserts the steps before a Planned or Ready step (`waits`, default true: that step also comes after them). | You, or the orchestrating agent |
| `program.update` | Change the title, goal, control, project, spend limit, agent or engine. | You, or the orchestrating agent |
| `program.start`, `program.park`, `program.resume` | Start, park or resume a program. | You, or the orchestrating agent |
| `program.get`, `program.list` | Read programs, their steps, checkpoints, requirements and your turn. `program.list` takes `q`, `project_id` and `person_id`. `program.start` and `program.get` also take `name` (words of the title or the template); by name, the answer has `spoken`, and a name with no program is an answer that starts nothing. | Everyone |
| `program.checkpoint` | Write one line on a step. | The step's own agent, you |
| `program.step_done` | The step's agent says that it is done, with its report. HoldSpeak still waits for the commit. | The step's own agent |
| `program.require` | Add a requirement (`text`, `kind`, `step_id` or `each_step`, `required`, `spec`). With `requirement_id`, change one: you only. | You at once; an orchestrating agent or a step's own agent by the Control level (YOLO adds it, Secure and Normal ask you) |
| `program.step_update` | Change a step: the fields that its state leaves open. `before` moves a Planned or Ready step. A frozen field is refused with `step_frozen` and its reason. | You at once; an orchestrating agent by the Control level |
| `program.amend` | Add one line to a started step's brief. HoldSpeak types it at the next turn end. | You at once; an orchestrating agent by the Control level |
| `program.decide` | Merge, decide a finding, resume a parked step, answer a core question. Kind `requirement` with `requirement_id`: `met`, `unmet`, `waive` (with `reason`), `send_back`. With `proposal_id`: `requirement_proposed` (`add`, `skip`), `step_change` (`apply`, `skip`), `step_amend` (`send`, `skip`). | You only |
| `program.overturn` | Undo a decision of HoldSpeak. | You only |
| `program.start_from` | Add a step whose worktree starts at a checkpoint's ref. When an agent asks, the control level decides. | You, the step's own agent |
| `program.handoff` | Move a running step to another agent, with the handoff brief. `preview: true` shows the brief and sends nothing. The next agent uses the same worktree and branch. | You only |

No tool marks a requirement Met: HoldSpeak judges it, or you press. An agent can propose a requirement but cannot waive one, and cannot change one of yours.

An agent can make and start a program, but it cannot decide for you, and it does not prompt a step's agent: HoldSpeak does that. The skill `agent/skills/holdspeak-programs/SKILL.md` tells an agent how to drive a program.

The routes are under `/api/programs` (see [API surface](API_SURFACE.md)). Each change of a program is a `program_changed` frame.

`HOLDSPEAK_PROGRAMS=off` stops the engine: it hands, checks and merges nothing. Test hubs set it.
