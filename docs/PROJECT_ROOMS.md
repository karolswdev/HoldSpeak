# Project Rooms

A Project Room is the operational surface for one Project. It connects
the Project to external providers (GitHub, Jira), installs Watches
(Project-scoped) over pull requests and issues, and runs the Steward
when conditions fire.

## What a Project Room contains

When you open a Project Room you see the Project's identity, linked
meetings, resources, the current Delta (what changed since the last
update), and the installed Watches (Project-scoped) with their
evaluation history. The Room is one coherent read: everything the
Steward and the owner need to assess the Project's state.

## Providers

A provider connects HoldSpeak to an external system. Each provider
requires its own CLI, installed and authenticated separately.

### GitHub

Requires [`gh`](https://cli.github.com/). Authenticate with
`gh auth login`. HoldSpeak reads connection status, discovers
repositories, and validates an owner/repo pair. Pull request
observations feed Watches (Project-scoped) and the Delta.

### Jira

Requires [`acli`](https://acli.atlassian.com/). Install with:

```bash
brew tap atlassian/homebrew-acli && brew install acli
acli jira auth login --site <yoursite>.atlassian.net --email <you> --token
```

A Jira connection is identified by (site, email). One owner may hold
multiple connections across different `*.atlassian.net` sites or
multiple accounts on one site. HoldSpeak never stores Jira credentials.

Every Jira call follows the switch-and-verify law: `acli jira auth
switch` to the target account, then the command, then `acli jira auth
status` read-back, under one process lock. A read-back mismatch is a
typed error, never a silent wrong read.

Issue types are enumerated from the Jira project. Statuses are observed
from the issue population (labeled as observed); Jira's three status
categories (new, indeterminate, done) are labeled as static.

All Jira access is read-only. Jira calls contact
`<site>.atlassian.net` from this device.

## Watches (Project-scoped)

A Watch observes a population of entities (pull requests or issues)
through a provider connection, evaluates conditions against each
entity's transitions, and fires actions when conditions match.

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

### Evaluation

A Watch evaluation fetches the current population, computes transitions
against the last baseline, matches conditions, and records effects.
The evaluator is the same for both providers. Conditions compare at the
change level (a field changed, changed to a value, entered a state) or
at the snapshot level (overdue, due within N days, inactive for N days,
older/newer than N days). Duplicate effects are prevented by
idempotency keys.

## The setup interview

Creating a Project Room is a guided interview. The interview discovers
connected providers, proposes Watch candidates based on the Project's
scope, lets you pick templates and configure conditions, tests the
Watch against the live population, baselines it, and activates it.
The interview persists across sessions; you can resume where you left
off.

## The Steward

The Steward is a bounded LLM run scoped to one Project. When a Watch
condition fires, the configured action can trigger a Steward run. The
Steward reads the Project Room's state, the triggering observations,
and the Delta, then produces an assessment. The Steward's output is
recorded as a Project update.

## MCP tools

The MCP sidecar exposes the full Project Room surface as tools. Six
Jira-specific tools (`provider.jira_connections`,
`provider.jira_add_connection`, `provider.jira_connection`,
`provider.jira_discover`, `provider.jira_search`,
`provider.jira_validate_scope`) complement the four GitHub tools
(`provider.github_connection`, `provider.github_discover`,
`provider.github_validate_repo`, and the shared `provider.list`).

See [MCP sidecar](./MCP_SIDECAR.md) for the full tool reference.

## HTTP routes

The provider routes are listed in [API surface](./API_SURFACE.md)
under `web.routes.providers`.
