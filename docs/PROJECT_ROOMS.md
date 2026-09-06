# Project Rooms

Use a Project Room to review one Project, its sources, and the work that needs you.
Configure Project-scoped Watches when you want HoldSpeak to observe supported source changes.

## Before you start

You can create a blank Project without external sources.
A connected Project also needs a configured provider and access to its source scope.

| Provider | Requirement | Data boundary |
| --- | --- | --- |
| GitHub | The `gh` CLI and an authenticated account | Calls contact GitHub from the hub. |
| Jira | The `acli` CLI and the intended site/account | Calls contact the selected Atlassian site from the hub. Jira access is read-only. |

Open **Settings > Connections** to inspect readiness and the relevant recovery command.
Use **Recheck** after you change the provider setup.
The provider CLIs retain their credentials. Do not put tokens in a Project description or Thread.

A Jira connection identifies both the site and account.
When multiple accounts exist, verify the selected identity before choosing a source scope.

## Create a Project

1. Select **Desk > New Project**.
2. Enter the outcome in the **What are you delivering?** field.
3. Select a source scope if the Project needs one.
4. Review the enabled Watch controls and live counts.
5. Select **Create Project**.

The outcome supplies the Project's name and outcome text.
The name uses the first 80 characters.
A Project with no selected sources is a valid blank Project.
The footer identifies that state before creation.

The **SOURCES** section contains a row for each supported provider.
A connected row offers a repository or project picker.
An unconnected row offers **Connect**, which opens the existing connection controls.
The source row rechecks readiness when you return.

Selecting a scope starts the live count check for enabled Watches.
The row reports **CHECKING** while the request runs.
A failed check reports its reason with **CAN'T CHECK**.
The current Web setup does not require a separate test wizard.

## Adjust the source population

Use **Adjust** on a connected row to change its population filters.
GitHub supports the base branch, labels, and draft inclusion.
Jira supports issue types and an optional JQL filter.

The initial GitHub controls enable **OPEN PRS** and **CI**.
The initial Jira controls enable **OVERDUE** and **DUE 7 DAYS**.
**BLOCKED** starts off.
Your selected controls determine the Watches created with the Project.

A source already used by another Project shows that relationship in the picker.
Use the existing Project when it already represents the work you want to discuss.
See [Interview](INTERVIEW.md) for discovery and setup through a Thread.

## Review the Room

Open a Project to enter its Room.
Use **ROOM** for current work and **HISTORY** for dated events.

| Section | What to inspect |
| --- | --- |
| Headline | The number of items that need you and the available health or target-date state |
| **NEEDS YOU** | Review requests, failing CI, overdue work, and pending proposals |
| **SOURCES** | Watch scope, current counts, last check, host, and pause/resume controls |
| **SINCE YOU LOOKED** | Source changes since the saved read marker |
| **DECISIONS & COMMITMENTS** | Available decisions and commitments from linked work |
| Ask field | A question about the Project, with the configured model boundary |

Open a source item to inspect the original record.
Read a proposal before using its decision control.
Opening or refreshing the Room updates its read marker.

**HISTORY** groups events by date.
Use the source filters or text search to find an event.
The detailed [User Guide](USER_GUIDE.md#project-room) describes the individual controls.

## Control Watches

Each Watch observes a defined population and evaluates its conditions.
The Room exposes **Pause** and **Resume** for the applicable Watch state.
A failed check identifies its reason.
A suggested source remains a suggestion until you add it.

The evaluator compares the current population with the previous baseline.
Supported conditions can describe transitions or current state, such as overdue work.
The service uses operation identities to prevent duplicate effects for the same evaluated event.
That protection does not make an arbitrary external client retry safe.

### GitHub templates

Five built-in templates for pull request Watches:

- `watch.github.review_queue`: surfaces PRs awaiting review.
- `watch.github.ci_health`: tracks CI check failures.
- `watch.github.merge_flow`: observes merge activity.
- `watch.github.delivery_drift`: flags PRs with no recent activity.
- `watch.github.release_readiness`: tracks release-blocking PRs.

### Jira templates

Five built-in templates for issue Watches:

- `watch.jira.blockers`: surfaces issues entering a blocked state.
- `watch.jira.delivery_flow`: tracks status transitions and completion.
- `watch.jira.due_risk`: flags issues approaching or past their due date.
- `watch.jira.scope_intake`: observes newly discovered issues.
- `watch.jira.transformation`: tracks priority escalations, reassignments, and staleness.

## Use the Steward

Open **Steward** from the Room to inspect its automation policy.
Configure unattended behavior only for the required Project and scope.
Use a manual run to inspect the available result before relying on unattended work.

The run records its steps and results.
Use its execution state and Receipts to determine what completed.
The service can refuse disabled work, cooldown conflicts, or an unavailable scheduler.
A configured policy alone does not prove that the scheduler ran.

Use **Draft update** to prepare an update from available Project evidence.
Inspect citations and unsupported claims before you save or publish the update.
The model boundary identifies where any model-generated wording ran.
See [the drafted update](USER_GUIDE.md#the-drafted-update) for the current controls.

## Use MCP or HTTP

The Project services also expose setup, observation, review, and Steward operations through MCP and HTTP.
The conversation-based setup driver and the current Web setup share the underlying Project services.
Their interfaces have different interaction steps.

Use the generated [MCP roster](MCP_SIDECAR.md#project) and [API surface](API_SURFACE.md) for exact operations.
A tool call still requires the caller's permissions and the operation's prerequisites.
A scheduler trigger can return `scheduler_not_wired` when the required runtime seam is unavailable.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A provider cannot connect | Follow its recovery command in **Settings > Connections**. Run **Recheck** afterward. |
| The count check fails | Verify source scope, provider identity, and access. Read the displayed reason. |
| The Room has no decision records | Link the relevant work or keep a manual brief with explicit gaps. A blank Room does not prove that no decisions exist elsewhere. |
| A Watch produces too much work | Adjust its population or pause it. Review the effect before resuming. |
| Unattended work does not run | Check the policy, runtime, scheduler, and reported refusal. |
| A draft contains unsupported facts | Correct the draft and inspect its sources before publishing. |

## See also

- [Interview](INTERVIEW.md): repeatable context and Project discovery.
- [Architecture work recipes](ARCHITECTURE_WORK.md): decision and agent briefs.
- [Automation](AUTOMATION.md): triggers and execution paths.
- [Control modes](AUTHORITY.md): authority for effects.
