# Projects, updates and decisions: betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk, 77 shots,
2026-10-17) and `MODEL.md` (the code map). Companions:
`../workbench/DESIGN.md` (Automations), `../engines/DESIGN.md`,
`../mcp/DESIGN.md`. Cluster C of `../PLAN.md`: INVENTORY rows 10 to 15.

## 1. The job

He is a Senior Software Architect with three reports and a few projects in
flight. The cluster serves three moments of his week:

- **Any time, 10 seconds**: he opens a project and knows where it stands. Is
  it on track, and if not, why? What does it need from him? Who is he
  waiting on? What changed and what was decided this week?
- **Friday**: he sends his manager (or his team) the status update. He
  wants a good draft from the week's real material in seconds, edits a line
  or two, and sends it. The README promises exactly this: "Draft update
  writes the weekly status from those records" and "the steward drafts the
  update and proposes a reviewer nudge" (`README.md:101-102`).
- **When something is decided**: it is kept once, with why and what it
  replaced, and every other place links to it.

He closes the project window when he knows the state, the update is sent or
scheduled, and nothing waits on him that he did not see.

## 2. What it is today

The walk is in `RECON.md`. In short:

| Step | What happens | Shot |
|---|---|---|
| Find projects | Not in the desktop Go menu. The phone Go menu lists each project by name. The palette lists three verb rows that cannot run. | `01-menu-go-1440.png`, `02-palette-project-1440.png` |
| Make a project | One field (name) and three source rows. GitHub and Jira each say "copy this command into a terminal". Nothing asks about meetings, notes or people. | `03-door-*` |
| See its material | Three meetings about payments exist; the new Room shows none. Adding each takes 5 presses from inside the meeting. | `04-room-first-open-1440.png`, `06-meeting-*` |
| Know where it stands | "7 open here · On track" while the release is blocked. Seven rows, six of them his reports' work, each with "Hand to coder". The real answers (decided, risks, changed) are three good pages hidden in the fourth fold, `PAGES`. | `08-room-populated-1440.png`, `13-room-pages-open-1440.png` |
| Write the Friday update | With no sources: 37 s, a confident empty draft ("All sources consulted successfully"). With sources: **96 s of spinner, then nothing on the face.** The hub answered 409 `not_usable`, and while it worked the whole hub froze (`/health` took 74 s). | `05-draft-*`, `09-draft2-*` |
| The draft he could have had | The records draft takes 0.1 s and is structurally right, but it pastes his 1:1 with Mira into the team update, says "No risks", and always says "All sources consulted successfully". | `27-update-deterministic-open-*` |
| Let the steward help | Opened by a button named "Watch sources". It reports a pipeline (Observe, Compare, Propose, Act, Verify, Record), makes no draft and no nudge, and flags a 20-minute-old decision as "due for periodic review". | `14-*`, `16-*`, `17-review-open-1440.png` |
| Keep a decision | Confirm in the meeting works. The desk drawer named Decisions stays empty. New Decision asks only for a title and drops the decision loose on the desk. It is found in Today's fourth wing. | `20-decisions-drawer-1440.png`, `22-today-decisions-1440.png`, `23-new-decision-created-1440.png` |

What worked: the meeting summaries (14 s, correct owners and dates), the
background pages, "Ask this project" (a correct, cited risk answer in under
20 s), and Publish into the Send well.

About 40 presses, a terminal for each outside source, two failed drafts and
about 25 minutes to get an update he could send, and that one came from MCP.

## 3. Why it fails

1. **The update is one big model call, blocking and silent.** The face asks
   one engine for a complete, schema-shaped update in one prompt, on the
   server's event loop, with a 120 s deadline, and hides the failure
   (`MODEL.md` §3). Every working part sits next to it unused: the records
   draft (0.1 s), the background pages, Ask. The job is "an agent that reads
   the project and writes", and today it is "one completion that must parse".
2. **The Room shows machinery, not the state.** The head word comes from a
   lookup that ignores the meetings and notes, so a blocked release reads "On
   track". The main list mixes his own asks with his reports' work and offers
   every row to a coding agent. What he needs is in folds named `PAGES`,
   `DECISIONS AND OWED` and `SINCE YOU LOOKED`. 15,310 lines draw a face whose
   10-second answer is wrong.
3. **A project does not know its own material.** The door asks for a name and
   three providers he cannot connect from there. It links no meetings, notes
   or people, though their titles name the project. Sources need a terminal.
   So the first update is empty, and the Room starts "Clear here".
4. **The steward is a second automation engine with its own words.** It has a
   policy (Off, Tell me, Do it), its own runs and a six-phase report, it
   never asks an engine, and it shares watches with Reactions and cadence.
   Under the product model, "work done again or later" is an Automation
   (`../PLAN.md` §2). The steward is the clearest case of one job in many homes.
5. **Decisions live in four stores and three faces.** Confirm in a meeting
   writes a record; New Decision and the meeting's Decide well write a
   different kind; the Room reads only records reached through meetings; the
   desk drawer named Decisions holds nothing (`MODEL.md` §6).
6. **It says things that are not true.** "On track", "All sources consulted
   successfully", "No risks or blockers", "due for periodic review", a 1:1
   in a team update. A manager cannot send what he cannot trust.

## 4. The design

### The concept

**A project is a body of work and the things it is about: its meetings,
notes, people, decisions and outside sources. Its window tells you where it
stands on one screen, and its update is a result that an automation writes
from those things.**

Three rules carry the design:

- **Never block, never go quiet.** Every press answers in under a second
  with something true. Slow work runs in the background and says what it is
  doing.
- **Show the state, not the machinery.** No pipeline phases, no revision
  numbers, no generator names, no folds for the 10-second job.
- **One home each.** The update's engine and schedule live in Automations.
  A decision lives in Decisions. Questions live in Ask. The project window
  shows them and links to them.

### The words

| He sees | It replaces |
|---|---|
| **Projects** (in Go), the project's name as the window title | Room as a window name, `surface-project-memory`, "Project · AGENT" |
| **Now** and **History** (the two wings) | ROOM, HISTORY |
| **On track** · **At risk: *reason*** · **Blocked: *reason*** | On track with no reason, `CHECKED 2M AGO` |
| **Needs you** (his own asks and things to Confirm) | OPEN HERE, `7 open here`, Clear here, UNFINISHED |
| **Waiting on** *person* | `WAITING ON THEO` chips on rows offered to a coder |
| **This week**: Decided · Risks · Changed | PAGES, What did we decide, Risks and disputes, What changed this week, SINCE YOU LOOKED |
| **Sources** (meetings, notes, GitHub, Jira, Confluence) | Watch sources, Watches on the face, MTG, `CHECKED 19:30` |
| **Write update** | Draft update, Regenerate, generator names, REV n, DETERMINISTIC, MODEL · OPENAI COMPATIBLE |
| **Draft from your records** / **Written by *engine*** | deterministic / model |
| **Looked at** | Source Coverage, SOURCES list of cut strings |
| **Nudge** (a reviewer nudge, prepared for Send) | Hand to coder on someone else's task |
| **Decisions** (the app), **a decision** | Decisions drawer, desk decision, decision record, Today ▸ DECISIONS wing |
| **Ask about this project** | Ask this project well, Preparation brief toggle |

Stop using on the face: steward, policy, Run once, Observe, Compare,
Propose, Act, Verify, Record, review flags, materiality, assessment,
`[UNVERIFIED]`, `pprop_…`, `READ 19:32 · NEXT CHECK 19:33`, Get Info table
of files, `Filed · Desk root`. POSITIONING's "Watches (Project-scoped)" and
"the steward's hand" need a names-table edit when this lands (decision 1).

### The project window: Now (1440)

```
┌ Payments migration ─────────────────────────────── NOW  HISTORY ─┐
│ At risk: tokenization waits on the HSM ceremony   [ Write update ] │
│ Cutover Thu 23 Oct · last update Fri 10 Oct · 3 meetings this week │
│                                                                    │
│ NEEDS YOU                          │ THIS WEEK                     │
│ Confirm: Kafka for ledger events   │ Decided                       │
│   Architecture review · Oct 16     │  Old ledger read-only 30 days › │
│                       [ Confirm ]  │ Risks                         │
│ Put Mira on the guild agenda (Nov) │  Tokenization blocked on the  │
│                    [ Done ][ Open ]│   HSM ceremony       Sync 10-14 │
│                                    │  Rollback runbook is a draft  │
│ WAITING ON                         │                 Note · risks  │
│ Theo  runbook review Tue ·         │ Changed                       │
│       Kafka cost Mon      [ Nudge ]│  Staging dry run passed       │
│ Jun   HSM date Wed · ADR Fri       │  Kafka chosen for ledger events│
│                           [ Nudge ]│                               │
│ Mira  PLAT-212 review, today       │                               │
│                           [ Nudge ]│                               │
│                                                                    │
│ [ Ask about this project…                                  🎙 ]    │
│ Sources  3 meetings · 2 notes · GitHub acme/payments · Jira PAY  [ Add ] │
│ Update   Fridays 15:00 · Claude Code · new result today      [ Open ] │
└────────────────────────────────────────────────────────────────────┘
```

- **The head** is the one big fact (display size): the state and its reason
  in his words. The reason comes from this week's risks: a blocker in a
  meeting, a risk item, an overdue owed item, a failing CI source. No risk
  means "On track". The line under it: the next date (target or next
  milestone), the last update, this week's meetings. No counters of zero.
- **Needs you** is the project's filter of the one Needs you list
  (`../PLAN.md` §2): proposals to Confirm (decisions, actions, suggested
  sources, steward proposals) and items he owes. Each row has one verb that
  does the job in place. Absent when empty.
- **Waiting on** groups what his reports and peers owe, by person, one line
  each with due words. **Nudge** prepares a short reviewer nudge (PR comment,
  Jira comment, Slack or email, whichever destination the item has) in the
  Send well; he presses Send. Nudge is shown only when the item has a place
  to send to. "Hand to coder" leaves these rows; it stays on his own items
  through the Object menu.
- **This week** promotes the three background pages that already exist
  (`MODEL.md` §2) into one column: Decided (each line links to the decision in
  Decisions), Risks, Changed. Each line keeps its source chip, which opens the
  meeting or note. A line the engine got wrong has Dismiss (it feeds the page
  rebuild).
- **Ask about this project** opens the Ask window with About = this project
  (one home for Ask). The answer stays in the Ask window, not in a second
  well here.
- **Sources** is one line that unfolds in place (§ Sources below).
- **Update** is one line: the update automation's When and With, and NEW
  when a result is unread. **Open** shows the newest update in this window
  (the Update state). Change opens the automation in Automations.
- Removed from the face: the five folds, Files (the project's drawer already
  holds its files; Get Info opens from the desk icon), Briefs and Prepare
  (cluster D owns meeting prep), the Unfinished list, the footer
  `READ · NEXT CHECK`, `Refresh` (the window refreshes itself).

Phone (393): one column in this order: head with **Write update** full
width; Needs you; Waiting on (one row per person); This week (Decided, Risks,
Changed, each collapsed to its first line with "2 more"); Ask; Sources;
Update.

### The update state (what Write update does)

```
┌ Payments migration · Update ───────────────────────── [ Back ] ┐
│ For [ My manager ▾ ]   Week Mon 13 – Fri 17 Oct                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Payments migration, week 42                    At risk     │ │
│ │ The ledger cutover is on track for Thu 23 Oct: the staging │ │
│ │ dry run passed. Card tokenization is blocked on the        │ │
│ │ security team's HSM key ceremony; Jun has a date by Wed.   │ │
│ │ Decided: old ledger read-only for 30 days after cutover.   │ │
│ │ Next week: rollback runbook review (Theo, Tue) …           │ │
│ │ I need: a date for the HSM ceremony from Security.         │ │
│ └────────────────────────────────────────────────────────────┘ │
│ ◌ Claude Code is improving this draft · 14 s        [ Stop ]   │
│ ▸ Looked at  3 meetings · 2 notes · 1 decision · PAY-212       │
│                              [ Edit ]  [ Copy ]  [ Send… ]     │
└────────────────────────────────────────────────────────────────┘
```

One press, in this order:

1. **Under 1 s**: the draft from his records appears, rendered as text (no
   `##`, no `**`, no `[UNVERIFIED]`). It is the existing records draft, made
   better: risks come from meeting risks, risk items and notes filed as
   sources; 1:1 meetings and People notes are left out (decision 2); the
   coverage line says what was read and what was not ("Jira PAY: not read,
   sign-in needed").
2. **In the background**, the project's update automation runs on its engine.
   The line under the text says who is working and for how long. Nothing
   else on the desk waits: the work runs off the hub's request loop.
3. **When the engine finishes**, its text replaces the draft in place, with
   "Written by Claude Code · 41 s" and **Undo** (back to the records draft).
   If he started editing, the engine's text waits as a second card ("A better
   draft is ready · Use it") and never overwrites his words.
4. **If the engine fails**, one line says why in words ("The LAN engine did
   not finish in 120 s", "Claude Code is not signed in", "The answer could
   not be read") with **Try again**. The records draft stays.

**For** picks the reader: My manager (outcome, risks, asks; short) or My team
(who does what next week; longer). It is part of the automation's Do text,
set here for convenience; the choice is saved on the automation.

**Looked at** lists what the engine read (meetings, notes, decisions,
issues, PRs), each a link. With a tool-capable engine this is the list of
desk tools the run called (`../mcp/DESIGN.md`).

**Send…** opens the Send well (the existing publish then send path). It
always prepares; he presses Send.

**History** shows past updates as one line each ("Fri 10 Oct · sent to
#payments-leads · Claude Code"), and the project's events in his words
("Added the Architecture review", "Confirmed: old ledger read-only").

### The agent writes the update

With an engine that can use tools (Claude Code, Codex, pi, or a server that
accepts tool calls), the update automation does not get a prompt stuffed
with records. It gets the desk's tools through the CONDUCTOR set
(`../mcp/DESIGN.md`) and a Do text like:

> Write the weekly status update for *Payments migration* for my manager.
> Read this week's meetings, the project's decisions, what each person owes,
> the open risks, and the Jira and GitHub state of its sources. Lead with
> the state and the one thing I need. Leave out 1:1s and People notes. Cite
> what you used.

The agent calls `project.get_room`, `meeting.get`, `decision_record.list`,
`provider.jira_search`, the GitHub reads and `memory.page` itself, and saves
its text as the project's next update draft with its sources. It may write
on the desk (the draft, Needs-you rows) and never sends. This is the
answer to "Draft update ran 91 s and produced nothing": the engine is no
longer asked to produce a perfect JSON document in one breath; it works the
way he would, and the records draft covers the wait.

An engine without tools gets the same Do text plus the records draft and the
three pages as its material, and returns plain text. No JSON schema: the
text is the update, and Looked at is the list of material it was given.

### The steward folds into Automations

| What the steward does today | Its home in the design |
|---|---|
| Refresh the project's sources | The sources refresh on their own cadence (the watches keep doing this). No automation is needed. |
| Turn changes into proposals to review | Rows in the project's **Needs you** (Confirm, Dismiss). |
| Draft the update | The project's **update automation** (When: Fridays 15:00, or only when pressed; Do: the update text above; About: this project; With: an engine; Put it in: this project's updates). |
| Propose a reviewer nudge on a PR that waits | An automation starter, **Nudge on waiting reviews** (When: a PR in this project's repository waits 2 days for review; Do: prepare a short, kind nudge to the reviewer; Put it in: Needs you). He presses Send. |
| Policy Off / Tell me / Do it | The automation's On/Off and its Put it in. |
| Runs and steps | The automation's results. Past steward runs show in History as plain events. |

The first press of **Write update** in a project makes its update automation
quietly (When: only when I press Run now, With: the engine for Drafts and
updates) and runs it. The Update line in the project window then offers
"Every Friday at 15:00" as one press, which turns the schedule on in the
automation. The Steward posture is parked behind RAW. Its tables and its MCP
tools stay.

### Sources: connect a project in one go

The door asks for what he knows, in the order he thinks of it:

```
┌ New Project ─────────────────────────────────────────────────────┐
│ Name      [ Payments migration                              🎙 ]   │
│ Sources   [ Paste links: a repository, a Jira project, a space ]   │
│           ✓ GitHub acme/payments                 signed in · karol │
│           ✓ Jira PAY · acme.atlassian.net        signed in         │
│           ○ Confluence PAYM          not signed in on this Mac [ Sign in ] │
│ Found     3 meetings and 2 notes mention "payments"     [ Add all ] │
│ People    Mira Okafor · Theo Lindqvist · Jun Park   (from those meetings) │
│                                              [ Create project ]    │
└──────────────────────────────────────────────────────────────────┘
```

- **Paste links**: one field takes any mix of `github.com/org/repo`, a Jira
  browse or board URL, or a project key, and a Confluence space URL. Each
  becomes a source row with its sign-in state, checked against the
  provider's validate tools (`provider.github_validate_repo`,
  `provider.jira_validate_scope`, `provider.confluence_validate_space`). Every
  row is the same component as the Accounts row.
- **Sign in** unfolds the one terminal command with Copy and Recheck in
  place (sign-in for `gh` and `acli` is theirs, not ours). Once he signs in
  for one project, every later project sees "signed in".
- **Found** searches meetings and notes by the name and its words as he
  types (keyword and meaning search already exist). **Add all** links them;
  each also has a remove cross. New meetings that match are offered later as
  Needs you rows ("Architecture review mentions payments · Add").
- **People** comes from the speakers of those meetings matched to his People;
  it fills `team_members`.
- **Create project** opens the project window, already populated.

From any agent (a Thread, or his own Claude Code), "make a project for the
payments migration with acme/payments and Jira PAY" calls the same tools
(`project.create`, the provider validators, `project.link`), so the door is
never the only way in.

In the project window, **Sources** unfolds the same rows plus each source's
state in words ("Jira PAY · 12 open · read 10 min ago", "GitHub: not signed
in"). Pause and Remove sit on the row. "Watches" and rules leave the face;
rule editing stays behind RAW.

### Decisions: one home

- **One kind**: every decision is a decision record. Confirm in a meeting
  (today), the meeting's Decide well and Desk ▸ New Decision (today desk
  decisions) all write a record (decision 3).
- **One home**: **Decisions** in Go and in the phone launcher, the window
  that Today ▸ Decisions shows today, with search, the current/all filter and
  Supersede. The desk icon named Decisions opens this window instead of an
  empty drawer.
- **New decision** asks for the decision, About (a project chip, pre-filled
  when opened from a project or a meeting) and Why (optional, with the mic).
  It never lands loose on the desk floor.
- **Everywhere else links**: the meeting's Decided rows, the project's This
  week ▸ Decided, the update text, Ask answers and Today's Needs you
  ("Confirm: Kafka for ledger events") each open the one record. None keeps
  a copy.
- The project reads its decisions by project (linked by its meetings **or**
  filed to it), so a decision made at the desk shows in the project.
- "Due for periodic review" is raised only from the decision's own review
  date, never minutes after it was made.

### What each press does

| Verb | Result |
|---|---|
| Go ▸ Projects | A list of projects, one row each: name, state and reason, next date, NEW update. One press opens a project. |
| Write update | The records draft in under 1 s; the engine's draft replaces it when ready, with Undo; a failure says why and keeps the draft. |
| For ▾ | Rewrites the draft for that reader (records draft at once; engine draft follows). |
| Edit | Edits the rendered text in place. |
| Send… | The Send well with a preview; Send is his press. |
| Every Friday at 15:00 | Turns on the update automation's schedule. |
| Confirm (Needs you) | Commits the proposal: a decision record, an owed item or a source. |
| Done (his item) | Marks it complete. |
| Nudge | Prepares a reviewer nudge in the Send well for that item's place. |
| Ask about this project | The Ask window with About = this project. |
| Sources ▸ Add | Unfolds the paste field and the Found list in place. |
| Found ▸ Add all | Links the meetings and notes; the window updates at once. |
| Decided line | Opens that decision in Decisions. |
| Source chip on a This week line | Opens the meeting or note at the cited place. |
| New decision ▸ Save | One decision record, about the chosen project. |

A verb that cannot work is not shown: no Nudge without a place to send, no
Write update engine line without an engine (the records draft still works),
no palette rows that say "Select a Project".

### What is removed or parked (nothing is deleted)

- The Steward posture and its policy face: parked behind RAW. `steward_*`
  tables, `project_steward_service.py` and the steward MCP tools stay.
- The Review posture as a separate face: its proposals become Needs you
  rows. The posture stays reachable from RAW.
- The five folds, Files, Briefs, Unfinished, the Room's Ask well: removed from
  the Now wing; their data stays (Files are in the project drawer, briefs in
  cluster D, asks in Ask).
- The update editor toolbar (B, I, U, H1, H2, H3…): replaced by a plain
  in-place text edit of the rendered update.
- "Hand to coder" on other people's owed items.
- The desktop "Decisions" drawer as a zone: it becomes the Decisions app icon.
  The zone row stays in data.
- Palette rows "Draft update · Select a Project", "Ask this project · Select
  a Project", "Gather · No Room has two windows".
- Watch actions that nothing drains: no longer offered when a rule is made
  (`MODEL.md` §5). Existing pending rows stay.

### What has to change underneath (`MODEL.md`)

- The draft route runs off the event loop and returns at once; the engine
  pass is a background job the window polls, like the steward and briefs
  already do.
- The records draft gets real risks, a true coverage line and the 1:1 rule.
- The engine draft drops the JSON-schema contract for plain text plus cited
  sources, and becomes the project's update automation run (one
  `project_updates` row per result, never a second store).
- Health reads risks from meetings, risk items and notes.
- Desk decisions and the Decide well write decision records, linked to the
  project; the Room reads decisions by project.
- An MCP write for an agent's update draft (`project.update_draft` exists;
  it gains sources and the engine name), and "add a source by URL".

## 5. Decisions for the owner

1. **The Friday update is an Automation, and the steward folds into
   Automations and Needs you.** Write update runs the project's update
   automation; the reviewer nudge becomes a starter; the Steward face is
   parked. Recommended: **yes**. It applies the plan's ruling that work done
   again or later has one home, and it gives the steward an engine for the
   first time.
2. **Updates leave out 1:1s and People notes unless he adds them.** A 1:1
   meeting (a meeting with one of his People and him only, or titled "1:1")
   and People notes never enter a project update's text, even when filed to
   the project. Recommended: **yes**. The walk put Mira's workload talk into a
   team update.
3. **One decision record.** New Decision and the meeting's Decide well write
   decision records; existing desk decisions are copied into records once
   (their table stays). The Decisions window is in Go, and the desk icon
   opens it. Recommended: **yes**.

## 6. How we know it worked

On a Friday afternoon, on his own desk, with his real meetings:

- He opens a project from Go in **1 press** and, within **10 seconds** and
  without scrolling at 1440, can say whether it is at risk and why, what he
  must do, and who he is waiting on. The state agrees with what his meetings
  said.
- He presses **Write update** and reads a readable draft in **under 2 s**.
  Within about a minute the engine's draft replaces it, and Looked at names
  this week's real meetings and decisions. No 1:1 content is in it.
- He edits one line and presses **Send…** then **Send**: **at most 5 presses
  and 3 minutes** from opening the project to a sent update.
- While the engine works, every other window on the desk answers at once.
- When the engine fails, he reads why in one line and still has a draft.
- He makes a new project by pasting two links: its meetings are found, its
  sources say "signed in", in **at most 6 presses**, with no terminal if he
  signed in once before.
- A decision he confirms in a meeting shows in the project's This week and in
  Decisions, and the desk icon named Decisions shows it.
