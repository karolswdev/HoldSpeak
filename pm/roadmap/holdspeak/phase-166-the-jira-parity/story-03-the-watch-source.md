# HS-166-03 - The JiraWatchSource, the five templates, the candidates, the fetcher rider

- **Project:** holdspeak
- **Phase:** 166
- **Status:** backlog
- **Depends on:** HS-166-02
- **Unblocks:** HS-166-04, HS-166-05
- **Owner:** unassigned

## Problem

services/watch_sources.py:102-108 is the single gate: every
connector but gh raises `connector_snapshot_adapter_unavailable`
("pushed snapshots but no local query adapter yet"). The Jira diff
(reaction_service.py:150-161: assigned/status_changed/
priority_changed/due_changed/resolved) is complete and starving.
No watch.jira.* template exists; the interview builds candidates
only for GitHub (project_setup_service.py:748).

## Scope

- **In:** `JiraWatchSource(runner)` in watch_sources.py registered
  under `connector_id == "jira"` — compiles a WatchSpec@1 subject
  (`kind: issue`; `scope: {connection_ref, projects[],
  issue_types[]}`; `query: {status_categories[], priorities[],
  assignees[], labels[], components[], sprint, jql}`) to ONE JQL,
  fetches via the 02 search, emits entities in the shape
  `_normalize_entity(jira)` already consumes (status, assignee,
  priority, resolution, due_at) + key/summary/url/issue_type/
  status_category/updated_at. `holdspeak/jira_templates.py` — the
  github_templates.py twin: `watch.jira.blockers`,
  `.delivery_flow`, `.due_risk`, `.scope_intake`,
  `.transformation` with §8.2's V0 conditions. New comparisons
  (`entered_state`, `due_within_days`, `overdue`, `inactive_for`)
  land in watch_validation + the evaluator ONCE, provider-agnostic.
  `_jira_candidates` beside `_github_candidates` (candidates only
  for a CONNECTED connection; needs-scope: site + project filled in
  clarify — PROV-011). `test_watch` gains the §8.1-style display
  block for jira (connection = site+email, projects, normalized
  JQL, entity count, five representative issues, matched
  conditions, supported transitions, observation time, duration,
  typed error/partial). Baseline/evaluate/evaluate_due/effects:
  ZERO FORK — proven, not asserted. RIDERS PAID: (a) the sidecar
  fetcher seam — project.py:719 `_watch_service()` composes the
  same snapshot_fetcher kwargs as web_server.py:334 (one
  provider-injection shape serving gh AND jira); (b) the
  legacy-side watch guard — reaction_service.refresh_due_watches
  skips graduated rows (state in active/tested/paused/retired).
- **Out:** the face (04), live proof (05).

## Acceptance criteria

- [ ] A jira watch tests, baselines, and evaluates through the unchanged WatchService path: same source_revision dedup, `jira.issue.status_changed` reaching `_match_and_record_effects`, one effect idem key — under test with a recorded transition.
- [ ] Five templates compile and validate; the new comparisons are evaluated in one place with tests beside them; the interview proposes jira candidates only when a connection is connected.
- [ ] Both riders paid under test (sidecar fetcher injected; legacy refresh skips graduated rows).

## Test plan

- **Unit:** tests/unit/test_watch_sources.py (jira), tests/unit/test_jira_templates.py, tests/unit/test_watch_service.py (jira leg), tests/unit/test_watch_legacy_compat.py (the guard), tests/unit/test_project_mcp_driver.py (the fetcher seam).
