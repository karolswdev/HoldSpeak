# Project Rooms

Use a Project Room to review one Project, its sources, and the work that needs you.
Add Watches when you want HoldSpeak to observe changes in the sources of a Project.

## Before you start

You can create a blank Project with no external source.
A connected Project needs a configured provider and access to its source scope.

| Provider | Requirement | Data boundary |
| --- | --- | --- |
| GitHub | The `gh` CLI and a signed-in account. | The hub calls GitHub. |
| Jira | The `acli` CLI and the intended site and account. | The hub calls the Atlassian site. Jira access is read-only. |
| Confluence | The `acli` CLI and the intended site and account. | The hub calls the Atlassian site. Confluence access is read-only. |

Open **Settings > Connections** to check each provider.
Use **Recheck** after you change a provider setup.
The provider CLIs keep their credentials.
Do not put a token in a Project description or a Thread.

A Jira connection names both a site and an account.
When you have more than one account, check the selected account before you choose a source.

## Create a Project

1. Select **Desk > New Project**.
2. Enter the outcome in the **What are you delivering?** field.
3. Select a source for each provider that the Project needs.
4. Check the Watch switches and their counts.
5. Select **Create Project**.

The outcome becomes the Project name, cut to 80 characters, and the outcome text.
With no source selected, the footer shows **NO SOURCES · BLANK PROJECT**. This is a valid Project.
Select **Cancel** to leave without a Project.

The **SOURCES** section has one row for each provider.
A connected row has a picker for a repository, project, or space.
A row that is not connected has **Connect**, which opens the connection controls.
The row checks the connection again when you return.

When you select a source, HoldSpeak counts the matches for each enabled Watch.
The row shows **CHECKING** while it counts.
A failed count shows **CAN'T CHECK** and the reason.

## Adjust the source

Select **Adjust** on a connected row to change what it watches.

- GitHub: base branch, labels, and drafts.
- Jira: issue types and an optional JQL filter.
- Confluence: space key.

The first switches are:

| Provider | On | Off |
| --- | --- | --- |
| GitHub | **OPEN PRS**, **CI** | none |
| Jira | **OVERDUE**, **DUE 7 DAYS** | **BLOCKED** |
| Confluence | **RECENT BLOGS** | **PAGES BY ID** |

Your switches decide which Watches HoldSpeak creates with the Project.
The picker shows when another Project already uses a source.
To set up a Project in conversation, see [Interview](INTERVIEW.md).

## Review the Room

Open a Project to enter its Room.
The Room has two wings: **ROOM** for current work and **HISTORY** for dated events.

| Section | Content |
| --- | --- |
| Head | The health, the target date, the last check, and **Draft update**. |
| **OPEN HERE** | Review requests, failing CI, overdue work, and pending proposals. **Review** appears when proposals wait. |
| **SOURCES** | Each Watch, its counts, its last check, its host, **Pause** or **Resume**, and **Steward**. |
| **SINCE YOU LOOKED** | Source changes since you last opened the Room. |
| **DECISIONS & COMMITMENTS** | Decisions and commitments from linked work. |
| Ask field | A question about the Project. A chip shows where the model runs. |

Open a source item to read the original record.
Read a proposal before you decide it.
Opening the Room updates the read marker.

**HISTORY** groups events by date.
Filter by source or search the text.
See the [User Guide](USER_GUIDE.md#project-room) for each control.

## Control Watches

A Watch observes one population of items and checks its conditions on a schedule.
Select **Pause** or **Resume** on its row in **SOURCES**.
A failed check shows its reason.
A suggested source stays a suggestion until you add it.

The Watch compares the current items with the last baseline.
A condition can describe a change or a current state, such as overdue work.
The service uses an operation identity to prevent a repeat effect for the same event.
This does not make a retry from any outside client safe.

Built-in Watch templates:

| Provider | Templates |
| --- | --- |
| GitHub | `watch.github.review_queue`, `watch.github.branch_ci`, `watch.github.ci_health`, `watch.github.merge_flow`, `watch.github.delivery_drift`, `watch.github.release_readiness` |
| Jira | `watch.jira.blockers`, `watch.jira.delivery_flow`, `watch.jira.due_risk`, `watch.jira.scope_intake`, `watch.jira.transformation` |
| Confluence | `watch.confluence.recent_blogs`, `watch.confluence.pages_by_id` |

## Use the Steward

Select **Steward** in the **SOURCES** section to see the automation policy of the Project.
Configure unattended work only for the Project and scope that need it.
Run it by hand first, and read the result, before you rely on unattended runs.

A run records its steps and results.
Read its state and its Receipts to see what finished.
The service can refuse a run when the work is disabled, in cooldown, or when no scheduler is available.
A saved policy does not prove that the scheduler ran.

Select **Draft update** in the head to prepare an update from the evidence of the Project.
Check the citations and any unsupported claims before you save or publish.
The model chip shows where the model ran.
See [the drafted update](USER_GUIDE.md#the-drafted-update).

## Use MCP or HTTP

The Project services also give setup, observation, review, and Steward operations through MCP and HTTP.
The setup by conversation and the Door share the same services.
Use [MCP sidecar](MCP_SIDECAR.md) and [API surface](API_SURFACE.md) for exact operations.
A call still needs the caller's permission and the operation prerequisites.
A scheduler trigger can return `scheduler_not_wired` when no scheduler is available.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A provider does not connect | Follow its recovery command in **Settings > Connections**. Select **Recheck**. |
| The count check fails | Check the source scope, the account, and your access. Read the reason. |
| The Room shows no decisions | Link the work, or keep a brief by hand. An empty section does not prove that no decision exists elsewhere. |
| A Watch creates too much work | Adjust its source, or pause it. Check the effect before you resume. |
| Unattended work does not run | Check the policy, the runtime, the scheduler, and the refusal. |
| A draft has unsupported facts | Correct the draft and check its sources before you publish. |

## See also

- [Interview](INTERVIEW.md): repeatable context and Project discovery.
- [Architecture work recipes](ARCHITECTURE_WORK.md): decision and agent briefs.
- [Automation](AUTOMATION.md): triggers and execution paths.
- [Control modes](AUTHORITY.md): authority for effects.
- [Memory](RELATIONSHIP_AWARE_MEMORY.md): standing pages for a Project.
