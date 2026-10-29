# Project Rooms

Use a Project Room to review one Project, its configured sources, and work
that needs you. A Project Room has a narrower service scope than whole-Desk
Ask. Add a Watch only when you want the Project service to observe a source.

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

1. Select **Desk > New Project**.
2. Enter the outcome in **Project name**.
3. Paste source links in **Paste source links** when needed.
4. Select **Check sources**.
5. Select **Create Project**.

The Project name is the delivery outcome. A blank Project is valid. The Door
shows **NO SOURCES · BLANK PROJECT** when you create it without a source.
Select **Cancel** to leave without a Project.

After a source check, review each source row and its scope before creation.
The Project Room creates source watches only for sources and watch templates
that you choose. A connected provider does not mean that every source in that
provider is in the Project.

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
source count is a check for the selected scope. It is not a proof that the
provider contains no other matching work.

## Review the Room

Open a Project to enter its Room. The Room has **ROOM** and **HISTORY** wings.

| Section | Content |
| --- | --- |
| Head | Health, state, target, last check, and **Write update**. |
| **NEEDS YOU** | Review requests, failing checks, overdue work, and pending proposals. **Review N** appears when proposals wait. |
| **PLAN** | Current planned work and Project follow-through. |
| **SOURCES** | Sources, Watch state, counts, last check, host, and source controls. |
| **SINCE YOU LOOKED** | Source changes since the last Room read marker. |
| **DECISIONS & COMMITMENTS** | Decisions and commitments from linked Project work. |
| Ask field | **Ask this project**, with an answer or brief result and a model chip. |

Open a source item to read its original record. Read a proposal before you
decide it. Opening the Room updates the read marker.

**HISTORY** groups dated Project events. Filter by source or search the text.
The Room can show a missing result, a failed check, or a pending proposal.
None of these states proves that the underlying provider has no work.

## Control Watches

A Watch observes one configured population and checks its conditions on the
Project service schedule. Select **Pause** or **Resume** on its row in
**SOURCES**. Select **Remove** when the Room offers it. A failed check shows
its reason. A suggested source stays a suggestion until you select **Add**.

The Watch compares current items with its last baseline. A condition can
describe a change or a current state, such as overdue work. The service uses
an operation identity to reduce repeat effects for the same event. This does
not make a retry from an outside client safe.

Use **Add source** to add an allowed source. Source controls change the
Project configuration. They do not change an unrelated Project or grant
whole-Desk access.

## Use the Steward

Select **Steward** in **SOURCES** to see the Project automation policy. It
controls unattended work for this Project and its configured scope. Run it by
hand first and read its result before you rely on a scheduled run.

A run records steps and results. Read its state and Receipts to see what
finished. The service can refuse a run when work is disabled, cooldown applies,
or no scheduler is available. A saved policy does not prove that a scheduler
ran.

Select **Write update** in the head to prepare an update from Project
evidence. Check citations and unsupported claims before you save or publish.
The model chip shows the model route. A project-update run has the Project's
service scope. It is narrower than a whole-Desk Ask about the same Project.

## Use MCP or HTTP

Project services provide setup, observation, review, source, and Steward
operations through MCP and HTTP. The setup conversation and Project Door use
the same Project services. A call still needs caller permission and operation
prerequisites.

Use [MCP sidecar](MCP_SIDECAR.md) and [API surface](API_SURFACE.md) for exact
operations. A scheduler trigger can return `scheduler_not_wired` when no
scheduler is available. Read the response and receipt. Do not treat a
successful request as proof that a provider source changed.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A provider does not connect | Follow its recovery command in **Settings > Accounts > Connections**. Select **Recheck**. |
| A count check fails | Check source scope, account, provider access, and the reason in the row. |
| The Room shows no decisions | Check linked work and source scope. An empty section does not prove that no decision exists elsewhere. |
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
