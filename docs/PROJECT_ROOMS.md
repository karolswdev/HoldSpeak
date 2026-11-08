# Project Rooms

A Project Room shows one Project in one window: where it stands, what needs
you, what changed and what is open. Ask, updates and source
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

### The mast

The mast is the top of **Now**: the Project's icon, the Project name and
one facts line, for example `On track · last update Sat 7 Nov 23:40 · 3 need
you`.

- The state word comes first, in its colour: **On track** is green,
  **At risk: <reason>** and **Blocked: <reason>** are red, an archived
  Project is grey. A new Project with no material says **New**. When the
  hub could not read health, or a source was not read on time, the line
  says **Not all read**. Press the reason to open its source.
- **last update** gives the day and time of the last published update.
- **N need you** opens the **Needs you** rows under the mast. Press it
  again to close them. It is not shown at zero.
- A bar under the mast has the colour of the state.
- **Draft update** tells the update engine to draft the Project's status
  update from the sources. The records draft shows at once; the engine's
  draft follows. You review the draft and you send it. **Draft update**
  does not write a note.
- **History** opens the **History** tab.

Under the mast is the **Ask this project** field with its microphone. Type
a question and press Enter. The question runs in the Ask window with this
Project as its scope, and shows in Ask's Recent.

On a phone, the verbs are **Draft update** and **Ask** on one row. **Ask**
opens the Ask window with this Project as its scope. **History** is the
second tab.

### Needs you

**Needs you** lists the rows that are yours. It opens from **N need you**
on the mast.

| Row | One press |
| --- | --- |
| A proposal from a meeting | **Confirm** records it. **Dismiss** removes it. Press its text to change the text, owner or due date, then press **Save & confirm**. |
| A meeting that names this Project | **Add** files the meeting to the Project. |
| A review that waits on someone | **Nudge** opens the nudge card. **Open** opens that person in People. |
| Your open item or action | **Hand to an agent session**, **Run as a program**, **Open source** or **Open**. |
| A decision that waits | **Decide** opens its source. |
| Proposals that wait for review | **Review N** opens the review posture. |

**Open** on a meeting action opens its card in follow-through. There you
set the owner and the date.

### What changed

**What changed** shows the first lines of the latest published update in
large type, then one line: the day and time, who wrote it, and **open the
update**. **open the update** opens it in the update posture.

When an update draft is kept, the foot of the plate says **Update draft ·
<time>**. **Continue** opens the draft in the update posture, with the text
you did not save.

Under it, **Files** and **Sources** are two folds side by side. A fold
with rows shows its count. Press a fold to open or close it. **Plan** is
there too when the Project has milestones or risks.

| Fold | Content | One press |
| --- | --- | --- |
| **Files** | The Notes filed to this Project. Not shown when there are none. | Select a row and press **Open note**, or open the row. |
| **Sources** | Each source, its Watch state (**Paused**, **Stale**, **Never checked** or the last check), suggested sources, **Add source**. | See "Control Watches". |
| **Plan** | The milestones and risks on a timeline with **Today**. A late milestone shows **Late**. | |

### What is open

**What is open** has up to three plates. Each plate has an icon, a name, a
count or word at the right, a coloured bar and one line. Press a plate to
open what it names.

| Plate | Line | Bar | Press |
| --- | --- | --- | --- |
| **Programs** | `2 running · 1 waits on you: <step>`, or **No Programs yet** with **New program** | Yellow for what waits on you, blue for what runs | Opens the Programs window for this Project. |
| **People** | What others owe, for example `Bea owes a review · Dana owes 2`, or the people the Project names | The share of people who owe you | Opens **Waiting on** and the Project's people under the plate. |
| **Decisions** | The latest decision and its day | The share of decisions committed to a person | Opens the decision in the decision reader. |

The People plate is not shown when the Project names nobody. The Decisions
plate is not shown when there is no decision. A hub that cannot read
Programs says **Not read** with **Refresh**. It does not show an empty
list.

**Waiting on** lists the items that other people owe, one row for each
person. The person with the most late work is first. An item shows its due
date. **Nudge** shows when the item has a destination for a nudge.

Each linked person row shows the person, their open commitments, and the
PRs and assignments that wait on them. An owner name that is not linked to
a person shows **Owner not linked** and **Link**. A name that matches more
than one person shows **Owner not clear** and **Resolve**.

### The status bar

The status bar of **Now** says when the update runs and with which engine,
for example `updates every friday 15:00 · Gemini CLI` or `updates only when
pressed · Gemini CLI`. Press it to open the update automation, where you
set the schedule and the engine. `saved <time>` gives the newest save of
an update.

## History

The **History** toolbar has **Source**, **Search history** and **Prepare a
brief**. **Prepare a brief** opens the prepare posture.

Under the toolbar, **Pages** lists the Project's standing pages: **Open**,
**Risks** and **Changed**. A row shows the page's first sentence. Press a
row to open the page under it: each sentence with its source. A page that
is not served is not shown.

The list gives the Project changes by day: **Today**, **Yesterday**, then
the date. Press a row to open the object that it changed. A row about the
Room itself has nothing to open.

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

The update posture holds the Project updates and one update editor. Its
head says what happens, for example `Gemini CLI drafts from the sources ·
you send`. It opens from **Draft update**, from **open the update**, from
**Continue**, from the palette's **Draft update for <project>**, and from a
Send link to an update. The Room
does not open in the update posture from an earlier visit.

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

Press **Prepare a brief** on the **History** toolbar. The prepare
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
| **Decisions** is not shown | Check that the meeting is filed to the Project. The plate shows the decisions of the last seven days. |
| The status line says **Not all read** | Open **Sources** and check the stale source. Press **Retry** on the health line. |
| **Programs** says **Not read** | Press **Refresh**. |
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
