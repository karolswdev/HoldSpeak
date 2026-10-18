# Automations (today: "Workbench"): betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk, 88 shots,
2026-10-17) and `MODEL.md` (the code map). Companion: `../engines/DESIGN.md`.

## 1. The job

Owner, 2026-10-17: "I wanted to create a simple automation. But you guess
what? I got so fucking confused. Let's actually even start with just the
name. Who the fuck would know what a workbench is?"

He opens this when he wants HoldSpeak to do a small piece of work for him,
again and again, so that he does not do it by hand. Examples from his week:
draft the Friday team update from this week's meetings and notes; after
each meeting, draft the follow-ups with owners; on Monday morning, prepare
his three 1:1s. He closes it when:

- the automation exists, and he can read what it does as one sentence;
- he has seen it run once and read a good result;
- he trusts it to run again, and he knows where the next result will appear.

He chooses the engine that does the work, and that includes the engines he
already pays for (OpenRouter, Claude Code, Codex), not only the LAN model.

## 2. What it is today

The full walk is in `RECON.md`. In short, for a first-time user who already
has a LAN engine, the job takes **about 45 presses, three extra windows and
12 to 15 minutes**, and two steps do not work at all.

| Step | What happens | Shot |
|---|---|---|
| Find it | No icon, no dock entry, nothing in Go, nothing in the phone launcher. Only Desk ▸ New Workbench (7th of 9) and Search. | `01-find-*` |
| Learn what it is | "No workbenches yet". Nothing says what one does. | `02-home-empty-1440.png` |
| Make one | Template cards show raw cron (`0 2 * * *`). "Agent" and "workbench" are used as the same word. No name is asked. | `03-create-chooser-1440.png` |
| Tell it what to work on | One instruction box. "@" finds only drawers and deletes the typed word. Dragging a note onto it says `NO DROP · NOT A WORKBENCH ITEM`. | `12-*`, `13-drag-over-workbench-1440.png` |
| Give it an engine | Run is dead but looks live. "Choose an engine" opens Settings. "Use it" adds the engine but does not assign it. "Choose default" opens Settings again, under the name "Custom tasks". | `08-*`, `09-*` |
| Run it | The page jumps. Items say `NEEDS REVIEW` before they run. | `14-running-*` |
| Read the result | Raw markdown and internal ids. `DONE` and `Review needed` at once. "Awaiting review" has no review verb. | `15-done-1440.png`, `19-open-artifact-1440.png` |
| Check the run | `0/0 done · NO MODEL · FAILED` after three good results. The home list calls the same run "Cancelled". | `16-runs-tab-1440.png` |
| Retry a failure | "Error: failed", with no reason. "Re-run" only puts the item back in the queue. | `24-*` |
| Schedule it | Three controls for one fact. Looking at another start mode silently turned the schedule off. | `10-*` |
| Find it again | Nothing on the desk, Needs you or Today knows about its four results. | `21-*`, `22-*`, `25-*` |

What worked: with an engine, the results were good, and they cited his notes
by name. The engine under the face is real.

## 3. Why it fails

1. **The concept is wrong for the job.** In code, a workbench is *a queue of
   separate tasks that one saved prompt answers one by one* (`MODEL.md` §1).
   He wants *one job that runs again and again*. With the queue concept, a
   schedule only fires on tasks someone typed beforehand. Each task is a
   separate call, so "this week's notes into one update" cannot happen.
   Templates promise work that the runner cannot do ("Review open PRs" with
   no PRs in reach).
2. **The name and the words describe the machinery, not the job.**
   Workbench, Agent, Skills, Items, Item assignment, Reference assignment,
   Workspace, Park, P2, Receipt, Artifact, `3 INHERITEDS`, `WITHOUT AGENTS`.
   "Workbench" alone means four things in the codebase (`MODEL.md` §5).
3. **Its parts live in other windows.** The engine is in Settings, the
   results in an artifact window, and their review is nowhere. One job
   crosses three windows and two names for the same setting.
4. **It reports wrong facts.** The run record contradicts the items, a failed
   run shows green, every run says NO MODEL, and failures have no reason. A
   face that is wrong about what happened cannot earn trust, and trust is
   the third thing he needs before he closes it (§1).
5. **It has no order.** The add-task form is the biggest thing on the face.
   The result, which is the reason the automation exists, is 1300 px down
   on the phone. Mixed materials, raw cron and raw markdown make it read as
   an admin panel.
6. **It duplicates other features.** Meeting Prep, Weekly status, Triage and
   Morning Brief each exist elsewhere already (prepared recipes, cadence,
   the Today brief). Workflows ("New Workflow") sit next to it under another
   name (`MODEL.md` §5).

## 4. The design

### The concept

**An automation does one job for you, again and again.** Each one reads as
one sentence:

> **When** every Friday at 3 PM · **do** "draft my team update: what
> shipped, what slipped, what I need from each person" · **about** this
> week's meetings and notes · **with** Claude Code · **put the result** in
> my Inbox.

Each time it runs, it makes one **result**. A result is a piece of text he
can read, copy, open as a note, or send. That is the whole model he has to
learn.

### The words

| He sees | It replaces |
|---|---|
| **Automations** (the app), **an automation** | Workbench, Workbenches, "… Agent" |
| **When** | Starts when, Mode, Schedule, Event trigger, cron |
| **Do** | Agent, recipe, Instruction, Items, Skills |
| **About** | Grounding, refs, zones, `@` drawers |
| **With** | Item assignment, Reference assignment, Choose default, Custom tasks |
| **Put the result** | Artifact, Workbench output, Open artifact |
| **Results** | Runs, Receipts, Items done |
| **Run now**, **On / Off** | ▸ Run, Enabled checkbox, ⏱/⏸ |
| **What it has learned** (a fold) | Memory, MEMORIES 3, OBS |

The code may keep the name `workbench` (it is a stored kind used in the
kernel, assignments, foreign keys and MCP; `MODEL.md` §6). The user never
sees it.

### The automation window

One window. The sentence is on top, and the results are below it. The window
opens large enough to show both (at least 880×640 at 1440).

```
┌ Friday team update ─────────────────────────────── On ●  [ Run now ] ┐
│                                                                      │
│  When        Every Friday at 3:00 PM                    next: Fri 15:00 │
│  Do          Draft my team update: what shipped, what slipped,       │
│              and what I need from Mira, Theo and Jun.                │
│  About       This week's meetings · Notes in Work                    │
│  With        Claude Code · sonnet                    → ANTHROPIC     │
│  Put it in   My Inbox                                                │
│                                                                      │
│ RESULTS                                                              │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Fri 17 Oct, 15:00 · 41 s · Claude Code                     NEW   │ │
│ │ Team update, week 42                                             │ │
│ │ Shipped: the rollback runbook (Mira) …                           │ │
│ │ (the rendered text, full width, readable)                        │ │
│ │ [ Open as note ]  [ Copy ]  [ Send… ]                            │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│  Fri 10 Oct · 38 s · Claude Code · Team update, week 41           ›  │
│  Fri 3 Oct · failed: Claude Code is not signed in    [ Run again ]   │
│                                                                      │
│ ▸ What it has learned                                                │
└──────────────────────────────────────────────────────────────────────┘
```

- **Each line of the sentence is the control.** Pressing a line unfolds its
  editor in place, under that line, and never opens another window:
  - **When**: three choices. *On a schedule* uses plain pickers (every day /
    weekday / week on [day] / hour, at [time]) and never shows cron. *When
    something happens*: a meeting ends; a note lands in [drawer]; GitHub asks
    me to review; Jira assigns me an issue. *Only when I press Run now.*
    "Next: Fri 15:00" shows when it is on.
  - **Do**: a plain text box with the voice mic. It holds the whole
    instruction. Starters fill it, and he can change every word.
  - **About**: a picker that finds meetings, notes, drawers, projects and
    people **by name**. Each pick becomes a named chip ("This week's
    meetings", "Notes in Work"), and the sentence text stays whole. A desk
    object dropped on the window becomes a chip. For *when something
    happens*, the thing that happened is the source, and the line says so
    ("the meeting that ended").
  - **With**: the engine picker from Engines (`../engines/DESIGN.md`), the
    same list in the same order, including agents on this Mac and services.
    The egress chip shows where the prompt goes. If no engine exists, the
    picker shows what is **Found** and adds it in one press. Run now then
    works, with no trip to Settings.
  - **Put it in**: My Inbox (the default, as a note); Needs you; a file; or
    a saved destination. A destination *prepares* a send, and he presses
    Send. That is the egress rule, unchanged.
- **Results** are newest first. The newest one is open and rendered (no `##`,
  no `**`, no ids). Older ones are one line each and open in place. A
  result is **NEW** until he opens it. There is no "awaiting review": a
  result is not a decision.
- **A failure says why**, in words ("Claude Code is not signed in", "the LAN
  engine did not answer in 60 s", "the note 'Platform sync' was deleted"),
  with **Run again**, which runs at once.
- **While it runs**, the newest result card shows "Working… 12 s · Claude
  Code" in place. Nothing above it moves.
- **On / Off** is one switch in the title strip. Looking at another *When*
  choice never changes the saved one; only pressing a choice does.
- **What it has learned** is a fold with the remembered lessons, each with
  Forget. It is closed by default.

Phone (393): the same order. The sentence lines become full-width rows with
the value under the label, and the newest result follows. Run now and On/Off
stay in the title strip.

### The Automations app (home)

```
┌ Automations ───────────────────────────────── [ New automation ] ┐
│ Friday team update     Every Friday 15:00 · Claude Code    1 NEW │
│ Meeting follow-ups     When a meeting ends · LAN Qwen            │
│ 1:1 prep               Mondays 8:00 · OpenRouter · Off           │
└──────────────────────────────────────────────────────────────────┘
```

- One row for each automation: name, When, With, and NEW when it applies
  (no "0 new").
- **Empty state**: one line, "An automation does one job for you, again and
  again." Below it are the starters as large cards.
- **New automation** shows the starters plus *Start from scratch*. A starter
  opens a new automation window with the sentence filled in. The blanks it
  cannot guess are highlighted ("About: *which people?*"). He can run it at
  once.

### Starters (only ones that work)

| Starter | When | Do | About | Put it in |
|---|---|---|---|---|
| Friday team update | Fridays 15:00 | draft the update: shipped, slipped, asks per person | this week's meetings and notes | Inbox |
| Meeting follow-ups | when a meeting ends | list decisions and follow-ups with owners and dates | the meeting that ended | Needs you |
| 1:1 prep | Mondays 8:00 | for each person: open commitments, last 1:1, what to raise | *which people?* | Inbox |
| Summarize a drawer | only when I press Run now | summarize what is new | *which drawer?* | Inbox |

TODO Agent, Triage Agent and Morning Brief are retired as starters. Today
and cadence already do that work. Their data stays.

### Finding it

- **Automations** appears in Go, in the phone launcher's Apps, and in the
  palette. **New ▸ Automation** stays.
- **NEW results** appear in Today ("Friday team update has a new result")
  and on the Automations dock entry once one exists. They do not appear in
  Needs you, unless *Put it in* is Needs you.

### What is removed or parked (nothing is deleted)

- The task queue (items, priorities P1–P5, Park, Dismiss, Clear done) leaves
  the face. In data, each run makes one item, which is the result.
- Agent, Skills and Workspace leave the face. The instruction lives on the
  automation. Old automations keep their agent's prompt as their Do text.
- Idle starts ("overnight resourcefulness") are parked behind RAW.
- "New Workflow" leaves the New menu (decision 2).
- The `pending-review` state of automation results is dropped in favour of
  NEW (decision 1).

### What has to change underneath (`MODEL.md` §6)

- An automation holds its own instruction and its sources. Each run (manual,
  scheduled or event) makes **one** occurrence item from them and runs it.
  This makes a schedule useful without typed tasks, and it lets the sources
  be read together in one prompt.
- The time limit applies to each run, not to a batch (today 60 s for the
  whole batch), and comes from the engine (a CLI needs longer).
- Run records tell the truth: status, model, engine and tokens match what
  ran, and a failure stores its reason.
- Results land in *Put it in* (an Inbox note by default) and do not wait in
  pending-review.

## 5. Decisions for the owner

1. **A result is not a review.** Drop "awaiting review" for automation
   results and show NEW until opened. Recommended: yes. Ledger, not gate:
   the run is still recorded.
2. **Park "New Workflow", the Agents list and idle starts from the face.**
   Their data and MCP tools stay. Recommended: yes. One way to automate,
   not three.
3. **Let an agent engine work in a folder.** When *With* is Claude Code or
   Codex, *About* may also be a repository folder, which the agent reads
   (read-only) to answer, for example "When GitHub asks me to review,
   summarize the PR and the risky files." Recommended: yes, as the last
   slice, after Engines E1.

## 6. How we know it worked

He presses New automation, picks *Friday team update*, sets With to Claude
Code, and presses Run now. He reads a good result in the same window
within about a minute. That takes **at most 6 presses, under 2 minutes, in
one window**. Then:

- he can find the automation again from Go or the phone launcher in **1
  press**;
- he sees a NEW result in Today the following Friday without opening the
  app;
- he reads a failed result and knows from its words what to fix.
