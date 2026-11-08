# Project Rooms

A Project Room shows one Project in one window: where it stands, what needs
you, who you wait on and what changed this week. Ask, updates and source
Watches act inside the Project scope. That scope is narrower than whole-Desk
Ask.

## Before you start

You can create a blank Project with no external source. A connected Project
needs a configured provider and access to the selected source scope.

| Provider | Requirement | Data boundary |
| --- | --- | --- |
| GitHub | The `gh` CLI and a signed-in account | The hub calls GitHub with that account. |
| Jira | The `acli` CLI, intended site, and account | Jira access is read-only. |
| Confluence | The `acli` CLI, intended site, and account | Confluence access is read-only. |

Open **Settings > Accounts > Connections** to check a provider. Select **Recheck** after
you change its setup. The provider CLI keeps its credentials. Do not put a
token in a Project description or Thread.

A Jira connection names both a site and account. Check the selected account
before you choose a source.

## Create a Project

1. Open **New Project** from the Desk.
2. Enter the outcome in **Project name**.
3. Paste source links in **Paste source links** when needed.
4. Select **Check sources**.
5. Select **Create project**.

The Project name is the delivery outcome. A blank Project is valid. The
status bar says **Blank project** when no source is in scope. Select
**Cancel** to leave without a Project.

After a source check, review each source row and its scope before creation.
The Room creates source Watches only for the sources and Watch templates
that you choose. A connected provider does not put every source of that
provider in the Project.

## Adjust the source

Open a connected source and select **Adjust** when the row offers it. The
available fields depend on the provider.

- GitHub can use a base branch, labels, and draft settings.
- Jira can use issue types and an optional JQL filter.
- Confluence can use a space key.

The initial Watch choices include these provider templates:

| Provider | Examples |
| --- | --- |
| GitHub | `watch.github.review_queue`, `watch.github.branch_ci`, `watch.github.ci_health`, `watch.github.merge_flow`, `watch.github.delivery_drift`, `watch.github.release_readiness` |
| Jira | `watch.jira.blockers`, `watch.jira.delivery_flow`, `watch.jira.due_risk`, `watch.jira.scope_intake`, `watch.jira.transformation` |
| Confluence | `watch.confluence.recent_blogs`, `watch.confluence.pages_by_id` |

The source picker can show that another Project already uses a source. A
source count is a check for the selected scope. It does not prove that the
provider has no other matching work.

## Review the Room

Open a Project to open its Room. The Room has two tabs: **Now** and
**History**. The Room opens on **Now**. Opening the Room sets its read
marker.

### The head

The head is the first line of **Now**.

- The status line gives the state and its reason: **On track**,
  **At risk: <reason>** or **Blocked: <reason>**. A new Project with no
  material says **New**. When the hub could not read health, or a source
  was not read on time, the line says **Not all read**.
- Press the status line to open the source of its reason.
- The line under it gives the next date (the target or the next planned
  milestone), the last published update, and the meetings of this week.
  A part with nothing to say is not shown.
- **Write update** drafts an update from the Project records at once. The
  configured engine then writes its own draft. The draft opens in the
  update posture.
- **Review N** shows when proposals wait. It opens the review posture.

### Needs you

**Needs you** lists the rows that are yours. The section is not shown when
it has no rows.

| Row | One press |
| --- | --- |
| A proposal from a meeting | **Confirm** records it. **Edit** changes its text, owner or due date, then **Save & confirm**. |
| A meeting that names this Project | **Add** files the meeting to the Project. |
| A review that waits on someone | **Nudge** opens the nudge card. **Open** opens that person in People. |
| Your open item or action | **Hand to an agent session**, **Run as a program**, **Open source** or **Open**. |
| A decision that waits | **Decide** opens its source. |

**Open** on a meeting action opens its card in follow-through. There you
set the owner and the date.

### Waiting on

**Waiting on** lists the items that other people owe, one row for each
person. The person with the most late work is first. An item shows its due
date. **Nudge** shows when the item has a destination for a nudge.

### This week

**This week** has up to four groups: **Open**, **Decided**, **Risks** and
**Changed**. A group with no lines is not shown. On a phone each group
shows its first line and **N more**.

- **Decided** lists the decisions recorded in the last seven days. Press a
  line to open the decision in the decision reader. The meeting token
  opens the meeting.
- A decision that is committed to a Person shows **Committed · <name>** at
  the end of its line.
- **Risks** lists the risks of this week's meetings and notes. A line that
  is an open risk item shows **At risk** and opens that item.
- **Open** and **Changed** come from the Project's standing pages.

A decision you confirm from a meeting proposal, or record in the meeting
Decide well, is filed to the Project when it is written. It shows in
**Decided** with its meeting as the source.

### Ask this project

The ask row is under **This week**. Type in **Ask this project** and press
Enter or **Ask**. The question runs in the Ask window with this
Project as its scope, and shows in Ask's Recent. The engine word opens
**Settings > Engines** to choose the engine. Set **Result** to
**Preparation brief** to open the prepare posture with your words.

### The folds

Under the ask row are the folds. Press a fold's **Show** or **Hide** to
open or close it. A fold with rows shows its count.

| Fold | Content | One press |
| --- | --- | --- |
| **Files** | The Notes filed to this Project. Not shown when there are none. | Select a row and press **Open note**, or open the row. |
| **Programs** | Always shown. One row for each Program of the Project, with its state word and step dots. Open when there are rows. | A row opens its Program window. With no Program: "No Programs yet" and **New program**, which opens the Programs window for this Project. |
| **Sources** | Each source, its Watch state (**Paused**, **Stale**, **Never checked** or the last check), suggested sources, **Add source**. | See "Control Watches". |
| **People** | The people the Project names. | **Open** opens a person in People. **People** on the head opens People for this Project. |
| **Plan** | The milestones and risks on a timeline with **Today**. A late milestone shows **Late**. | |

A hub that cannot read Programs says **PROGRAMS NOT READ** with
**Refresh**. It does not show an empty list.

### People

Each linked person row shows the person, their open commitments, and the
PRs and assignments that wait on them. The row opens to show each
commitment with its source and **Open source**.

An owner name that is not linked to a person shows **Owner not linked** and
**Link**. A name that matches more than one person shows **Owner not clear**
and **Resolve**. **Resolve** shows the candidates under the row. A press on
a candidate only selects it. **Link** writes the link. **Inspect** opens the
selected person, and **Check** reads again. The caption says
**PEOPLE 2 OF 3** when not all named people are linked.

When the People ledger is locked or not set up, the head verb is **Unlock**
or **Set up People**. The fold is not shown when the Project names no
people.

### The update schedule

The **Update** row is at the foot of **Now** when the Project has an
update automation.

- **Fridays 15:00** or **Only when pressed** says when the update runs.
  Press it to open the automation.
- The engine word says which engine writes it. Press it to open the
  automation.
- **NEW** shows when the latest result is not read.
- **Open latest** opens the latest update in the update posture.
- **Every Friday at 15:00** turns on the schedule.

## History

**History** lists the Project changes by day: **Today**, **Yesterday**,
then the date. Search with **Search history**. Filter with **Source**.
Press a row to open the object that it changed. A row about the Room itself
has nothing to open.

The **Writes** fold under the list shows each write to the Project. A
refused or failed write shows its reason. The status bar gives the count
and the first date, for example `42 events · since Oct 1`.

## Postures

A posture replaces the Room body while it is open. One posture is open at
a time, in this order: review, update, Steward, prepare.

### The review posture

**Review N** opens the open review of the Project. A Project has at most
one open review. **N** is the count of its open proposals. For each
proposal, press **Accept**, **Edit**, **Defer** or **Dismiss**. **Undo**
takes back the last choice. **Finish review** ends the review. **Close**
goes back to **Now**.

### The update posture

The update posture holds the Project updates and one update editor. It
opens from **Write update**, from **Open latest**, from the palette's
**Draft update**, and from a Send link to an update.

- **Save** keeps the draft. **Publish** publishes it.
- **Regenerate** writes a new draft.
- **Back** goes to the update list. **Close** goes back to **Now**.

Check citations and claims marked **UNVERIFIED** before you publish. A
project update run has the Project scope. A request from elsewhere to show
the Room (a proposal row, **History**, a filed Note) closes the update
posture first and never saves the draft.

### Use the Steward

Open **Sources**, then its **Raw** fold, and press **Watch sources**. The
Steward posture shows the Project automation policy: unattended operation,
evaluation cadence, cooldown, maximum actions, retries and allowed effects.
It controls unattended work for this Project and its configured scope.
Run it by hand first and read its result before you rely on a scheduled
run.

A run records steps and results. Read its state and receipts to see what
finished. The service can refuse a run when work is off, cooldown applies,
or no scheduler is available. A saved policy does not prove that a
scheduler ran.

### The prepare posture

Set **Result** to **Preparation brief** in the ask row. The prepare
posture builds a brief from the Room's sources, its decisions and its open
commitments. Press **Keep this brief** or **Copy the brief**. It needs no
calendar.

## Control Watches

A Watch observes one configured population and checks its conditions on the
Project service schedule. Select **Pause** or **Resume** on its row in
**Sources**. Select **Remove** to retire it. A failed check shows its
reason. A suggested source stays a suggestion until you select **Add**.
**Dismiss** removes the suggestion.

The Watch compares current items with its last baseline. A condition can
describe a change or a current state, such as overdue work. The service uses
an operation identity to reduce repeat effects for the same event. This does
not make a retry from an outside client safe.

Use **Add source** to add an allowed source. Source controls change the
Project configuration. They do not change an unrelated Project or grant
whole-Desk access.

## Use MCP or HTTP

Project services provide setup, observation, review, source, and Steward
operations through MCP and HTTP. The setup conversation and the New Project
window use the same Project services. A call still needs caller permission
and operation prerequisites.

Use [MCP sidecar](MCP_SIDECAR.md) and [API surface](API_SURFACE.md) for exact
operations. A scheduler trigger can return `scheduler_not_wired` when no
scheduler is available. Read the response and receipt. Do not treat a
successful request as proof that a provider source changed.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A provider does not connect | Follow its recovery command in **Settings > Accounts > Connections**. Select **Recheck**. |
| A count check fails | Check source scope, account, provider access, and the reason in the row. |
| **Decided** shows no decision | Check that the meeting is filed to the Project. **Decided** shows only the last seven days. |
| The status line says **Not all read** | Open **Sources** and check the stale source. Press **Retry** on the health line. |
| **Programs** says **PROGRAMS NOT READ** | Press **Refresh**. |
| A Watch creates too much work | Adjust its source or select **Pause**. Check the effect before you resume it. |
| A suggested source is not active | Select **Add**. A suggestion does not create a Watch. |
| Unattended work does not run | Check policy, runtime, scheduler, and the refusal or receipt. |
| An update has unsupported facts | Correct the draft and check its sources before you publish. |

## See also

- [Interview](INTERVIEW.md): Project discovery and context.
- [Architecture work recipes](ARCHITECTURE_WORK.md): decision and agent briefs.
- [Automation](AUTOMATION.md): triggers and execution paths.
- [Control modes](AUTHORITY.md): authority for effects.
- [Memory](RELATIONSHIP_AWARE_MEMORY.md): standing pages for a Project.
