# HS-166-02 - Discovery + search: projects, issue types, statuses, JQL

- **Project:** holdspeak
- **Phase:** 166
- **Status:** backlog
- **Depends on:** HS-166-01
- **Unblocks:** HS-166-03
- **Owner:** unassigned

## Problem

§8.2 step 1: discover site, Projects, issue types, status
categories; step 3: a constrained population by status, priority,
assignee, component, label, sprint, or advanced JQL. PROV-006:
searchable, bounded/paginated, stable-ID, tolerant of partial pages.

## Scope

- **In:** `JiraProviderAdapter.discover(principal, connection_ref,
  *, kind, query, cursor, limit)` — `kind=projects` over `acli jira
  project list --json --limit N` (stable id = project key; client
  filter on key/name like github_provider.py:273's discover);
  `kind=issue_types|statuses` over `acli jira project view --key K
  --json` IF the real shape carries them, ELSE derived from one
  bounded `acli jira workitem search --jql "project = K" --fields
  issuetype,status --json --limit 200` and LABELED
  `derived: true` (PROV-007 — decided on the real CLI, recorded in
  the trace). `search(principal, connection_ref, *, jql, fields,
  limit)` over `acli jira workitem search --jql --fields
  key,summary,issuetype,status,assignee,priority,duedate,resolution,
  updated,project --json --limit`; `validate_scope(principal,
  connection_ref, project_key)` = one bounded search probe (the
  validate_repo twin, github_provider.py:376). Every call runs under
  the 01 lock with the switch + read-back. JQL passes through
  VERBATIM when the owner types it (`query_invalid` typed from
  acli's error, never rewritten). Routes beside providers.py:54-154:
  `GET/POST /api/providers/jira/connections`, `POST
  .../connections/{ref}/recheck`, `GET /api/providers/jira/discover`,
  `POST /api/providers/jira/validate-scope`. MCP twins in
  project.py:1349-1395: `provider.jira_connections`,
  `provider.jira_add_connection`, `provider.jira_discover`,
  `provider.jira_validate_scope` — serializers DELEGATE to the
  route's own (the 165 law; copied glue goes in the register).
- **Out:** watch compile/test (03), the picker UI (04).

## Acceptance criteria

- [ ] Projects paginate with a stable cursor; a partial page returns `partial` with what it got; a bad JQL returns `query_invalid` with acli's message.
- [ ] Issue types + statuses resolve for a real project key — enumerated or honestly `derived`, never invented (PROV-011).
- [ ] Routes and MCP tools return byte-equal shapes (parity assertions), each naming its connection ref.

## Test plan

- **Unit:** tests/unit/test_jira_provider.py (discover/search/validate with recorded outputs).
- **Integration:** tests/integration/test_provider_routes.py (the jira routes + MCP parity beside the github block).
