# HS-166-02 - Discovery + search: projects, issue types, statuses, JQL

- **Project:** holdspeak
- **Phase:** 166
- **Status:** done
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

- [x] Projects paginate with a stable cursor; a partial page returns `partial` with what it got; a bad JQL returns `query_invalid` with acli's message.
- [x] Issue types + statuses resolve for a real project key — enumerated or honestly `derived`, never invented (PROV-011).
- [x] Routes and MCP tools return byte-equal shapes (parity assertions), each naming its connection ref.

## Test plan

- **Unit:** tests/unit/test_jira_provider.py (discover/search/validate with recorded outputs).
- **Integration:** tests/integration/test_provider_routes.py (the jira routes + MCP parity beside the github block).

## Trace record (orchestrator round, 2026-09-03)

- Shipped on JiraProviderAdapter: `_with_account` (ONE helper:
  binary check → lock → switch → status read-back → the command
  closure, all under the lock; a mismatch aborts BEFORE the command
  — under test), `discover(kind=projects|issue_types|statuses)`,
  `search(enrich=)`, `count`, `validate_scope`; three routes + three
  MCP twins delegating to the route helpers; allowlist NOT widened;
  no schema change. MCP TOOLS pin 40→43, honest.
- Discovery truth on the real CLI: issue types are ENUMERATED
  (`project view --key K --json` carries issueTypes: Epic/Subtask/
  Task); statuses are OBSERVED from one bounded `--fields key,status`
  search (labeled `observed`), with Jira's three fixed categories
  labeled `static`. The search field cap honored: search fetches
  the allowed fields; `enrich=True` adds due/resolution/updated per
  issue via `workitem view` and reports `calls` (1 + N).
- LIVE PROOF (the owner's real site): 2 projects discovered; types
  enumerated; statuses observed (Done/done, In Progress/
  indeterminate); search of 3 issues with enrichment = 4 calls,
  due dates real (2026-09-10, 2026-09-17); count 2 not-done; bad
  JQL → `query_invalid` with Jira's message verbatim; validate KAN
  true with types, NOPE false typed.
- FINDING for 03: on this team-managed site a Done issue carries
  `resolution: null`. The existing `jira.issue.resolved` diff (fires
  on resolution appearing) will never fire there; `status_category`
  → `done` is the honest completion signal and the templates must
  condition on it. Recorded, never invented.
