# HS-166-01 - The acli pack + the connection ledger: many accounts, many sites

- **Project:** holdspeak
- **Phase:** 166
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-166-02
- **Owner:** unassigned

## Problem

Jira is invisible in the provider list (providers.py:31-43 lists
only `native`; GitHub is appended from its manifest). SETFLOW-005
says Jira MUST appear partial rather than ready. And the owner's
focus is many accounts against many `*.atlassian.net` sites — a
connection is (site, email), not "Jira".

## Scope

- **In:** `holdspeak/connector_packs/acli_jira.py` — a NEW pack
  (the jira_cli.py go-CLI pack is PARKED, untouched): allowlisted
  read verbs only — `jira auth status`, `jira auth switch`, `jira
  project list|view`, `jira workitem search|view`; `requires_cli:
  "acli"`. `holdspeak/services/jira_provider.py` —
  `JiraProviderAdapter(db, runner=None)` mirroring
  github_provider.py:103-420: `manifest()` (provider_id "jira",
  transport "connector_pack", discover/read True, subscribe/effect
  False, versioned); `list_connections(principal)` /
  `add_connection(principal, site, email)` (site normalized to
  `<x>.atlassian.net`; ref = `site|email`; NO secret ever stored —
  PROV-004) / `connection_status(principal, connection_ref)` =
  `acli jira auth switch --site --email` then `acli jira auth
  status` READ BACK under ONE process-wide lock (the
  switch-and-verify law; a read-back naming another site/email =
  CODE_SCOPE_DENIED-class typed error, never a silent wrong read);
  binary absent = `unavailable` (typed, PROV-009 codes reused from
  github_provider.py:56-61); not logged in = `owner_action_required`
  with the exact recovery command `acli jira auth login --site X
  --email Y --token` (PROV-005). Rows in `watch_provider_connections`
  (provider_id "jira", external_connection_ref = the ref) — one row
  per (site, email); no schema change expected. Provider list
  (providers.py + project.py:1351 `provider.list`): Jira appears
  from `manifest()` with readiness `unavailable` (no acli) /
  `partial` (acli, zero connected accounts) / `connected` (≥1) —
  never invented.
- **Out:** discovery/search (02), watches (03), web (04).

## Acceptance criteria

- [ ] Two connections (two sites, or two emails on one site) coexist; `connection_status` on each switches, reads back, and persists its own row; a read-back mismatch is a typed error under test.
- [ ] Binary absent / not logged in / connected all typed, with the recovery command exact; Jira appears in `provider.list` and `GET /api/providers` in the honest state.
- [ ] The lock serializes interleaved callers under test (two threads, two connections, zero cross-reads).

## Test plan

- **Unit:** tests/unit/test_jira_provider.py (the test_github_provider.py fake-runner idiom; recorded acli outputs carry `recorded_from`), tests/unit/test_connector_packs.py (acli pack manifest + allowlist refusal).
