# HS-166-01 - The acli pack + the connection ledger: many accounts, many sites

- **Project:** holdspeak
- **Phase:** 166
- **Status:** done
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

- [x] Two connections (two sites, or two emails on one site) coexist; `connection_status` on each switches, reads back, and persists its own row; a read-back mismatch is a typed error under test.
- [x] Binary absent / not logged in / connected all typed, with the recovery command exact; Jira appears in `provider.list` and `GET /api/providers` in the honest state.
- [x] The lock serializes interleaved callers under test (two threads, two connections, zero cross-reads).

## Test plan

- **Unit:** tests/unit/test_jira_provider.py (the test_github_provider.py fake-runner idiom; recorded acli outputs carry `recorded_from`), tests/unit/test_connector_packs.py (acli pack manifest + allowlist refusal).

## Trace record (orchestrator round, 2026-09-03)

- Shipped: connector_packs/acli_jira.py (3-tuple allowlist
  `(jira, group, verb)`, read verbs only; the go-CLI jira_cli.py
  pack untouched), services/jira_provider.py (JiraProviderAdapter;
  the CODE_*/STATE_* constants IMPORTED from github_provider — one
  source; STATE_DISCONNECTED added there for both), three routes +
  three MCP twins + `collect_provider_manifests(principal=)` as the
  ONE provider-list builder (readiness from persisted rows +
  shutil.which only — never a CLI run inside a list call).
- ORCHESTRATOR CATCHES, all four paid in-round: (1) readiness absent
  from the provider list — SETFLOW-005 "partial" was a comment, not
  an assertion (theater); (2) acli's own account registry
  (~/.config/acli/jira_config.yaml, no tokens) unread —
  `known_accounts()` now enumerates it, cloud_id/account_id never
  surfaced; (3) `connection_ref` did not normalize — a URL-form site
  split one identity into two rows and turned a good account into
  "not authenticated" (found ONLY by the live run; the fake runner
  could never see it); (4) new rows stamped `unavailable` against
  the docstring's own `disconnected`.
- LIVE PROOF (real acli 1.3.36, the owner's OAuth account): partial
  → connected with last_connected_at; URL-form ref == bare ref;
  known_accounts lists the registry's account as current; the
  wrong-email path returns owner_action_required with the exact
  login command; readiness {connected: 1 of 2}. The unit truth table
  covers binary-absent / unauthenticated / account-not-found /
  read-back-mismatch (degraded, scope_denied) / connected, plus the
  two-thread lock test (zero cross-reads).
- Pins updated honestly: ALL_PACKS 5→6, KNOWN_CONNECTORS 5→6, MCP
  TOOLS 37→40 (provider.jira_*; the project.* pin 33 unchanged; the
  _thread_side law holds — provider.* stays out of the thread
  palettes).
- Not built (by design): remove_connection is trivial and shipped;
  no schema change; no PermissionGate widening needed (no binary
  allowlist exists — recorded).
