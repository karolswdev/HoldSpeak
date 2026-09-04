# HS-168-02 - The connections service: one readiness shape on the hub

- **Project:** holdspeak
- **Phase:** 168
- **Status:** backlog
- **Depends on:** HS-168-01
- **Unblocks:** HS-168-03, HS-168-04
- **Owner:** unassigned

## Problem

Readiness lives in three places with three shapes: GET /api/
providers/github/connection (providers.py:105, from
GitHubProviderAdapter.connection_status at github_provider.py:183),
GET /api/providers/jira/connections (providers.py:221, the (site,
email) ledger), and the calendar's configured flag on the Door. The
interview's suggest step returns proposals with no idea whether
their provider is connected, so the face guesses. There is no MCP
twin for "what is connected".

## Scope

- **In:** (a) ONE readiness shape — `GET /api/connections` — over
  the existing adapters (no new authority; the adapters stay the
  source): per tool `provider_id`, `state` (connected ·
  owner_action_required · unavailable · not_configured), `account`
  (login / site+email / calendar source names), `next_action` (kind
  + label), `recovery_hint` (the exact command), `last_checked_at`,
  `egress_host`; `POST /api/connections/{provider}/recheck`
  delegating to the existing rechecks; Jira add stays on its 166
  route. (b) the suggest step (project_setup.py suggest + the
  proposal serializer) annotates every proposal with its provider's
  readiness (`connection: {state, account}`) read through the same
  service — the face never derives it. (c) known scopes per setup
  session: the repo / project chosen for one proposal is recorded on
  the session answers (the 167-02 jira_scope precedent) and returned
  as `known_scopes` on the session so 04 can OFFER it; never applied
  by the service. (d) MCP twins `connection_list` +
  `connection_recheck` in the project family, classified in
  thread_tools._TOOL_CLASSES, the tool census + MCP_SIDECAR
  regenerated in the same commit; the family count renamed
  honestly. (e) the schema untouched (session answers are JSON);
  if a column is needed the snapshot regenerates in the same commit.
  (f) THE CAP (the audit's F7): suggest's `_MAX_PROPOSALS = 8` cut
  after native → GitHub → Jira drops every Jira card on a desk with
  three native facts (project_setup_service.py:74, :333-336). The cap
  becomes PER PROVIDER (native · github · jira; the connected
  providers never starved) with a failing-then-passing test on a
  3-native + 5-GitHub + 5-Jira desk.
- **Out:** OAuth, token capture, new providers, calendar setup.

## Acceptance criteria

- [ ] `GET /api/connections` returns the same state the per-provider routes return for gh connected / gh logged out / acli one account / nothing configured — pinned by tests that drive the adapters, not fixtures that hand-seed the row.
- [ ] Suggest returns `connection` on every proposal and `known_scopes` on the session; scope recorded once is returned, never applied.
- [ ] MCP twins registered, classified, censused; parity test web = MCP for list + recheck.
- [ ] The per-provider cap: a 3 + 5 + 5 desk persists cards for every connected provider (failing-then-passing).

## Test plan

- **Unit:** tests/unit/test_hs168_connections_service.py (the four states; the Jira ledger; the calendar flag; recheck delegation).
- **Routes:** tests/web/test_hs168_connections_routes.py (+ the suggest annotation on the 159 setup route tests).
- **MCP:** tests/mcp/test_hs168_connection_tools.py (registry, classes, parity).
