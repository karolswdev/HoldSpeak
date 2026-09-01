# HS-161-02 - The compilation: five templates, and GitHub joins the interview

- **Project:** holdspeak
- **Phase:** 161
- **Status:** backlog
- **Depends on:** HS-161-01
- **Unblocks:** HS-161-03
- **Owner:** unassigned

## Problem

§8.1: the recommended templates (`watch.github.review_queue`,
`ci_health`, `merge_flow`, `delivery_drift`, `release_readiness`)
compile outcome + repo scope into precise WatchSpec@1 — the V0
conditions (PR opened, review requested/decision changed, checks
changed esp. to failure/recovery, head changed, merged/state,
no-activity duration) and filters (state, base, author, label,
draft, bounded search) as CLOSED WatchCondition@1 trees. INT-007:
the interview's recommendations ride a LIVE provider inventory —
GitHub candidates appear only when the provider is genuinely ready.

## Scope

- **In:** the five §8.1 templates as closed spec-builders (a pure
  module beside watch_validation.py — the house convention);
  compile(template, repo_scope, options) → a full WatchSpec@1 draft
  (subject pull_request, scope {repositories:[owner/repo]}, query
  filters, trigger poll + §4.1 cadence preset, rules with validated
  conditions, §7.3 actions). The setup engine grows the github
  family: `suggest()` includes template candidates when
  connection_status says connected (the 01 adapter consulted live —
  INT-007), each carrying source/scope/conditions/action/cadence/
  readiness/rationale (INT-008); `clarify` gains the repo-scope
  step (discovered list or typed fallback); proposals persist like
  natives. PROV-011: no invented repo identities — candidates name
  ONLY discovered/validated repos or carry the needs-scope state.
- **Out:** the live test (03), UI (05), evaluation.

## Acceptance criteria

- [ ] Five templates compile to valid WatchSpec@1 (watch_validation green on every output); the V0 conditions/filters map exactly (a truth table per template).
- [ ] Suggest with a connected provider yields GitHub candidates beside natives; disconnected/unauthenticated yields NONE (not grey theater — SETFLOW-004's spirit); zero invented repos.
- [ ] Repo clarify: discovered selection AND the typed fallback both produce a validated scope.
- [ ] 159's setup suites stay green (the family grows additively).

## Test plan

- **Unit:** `tests/unit/test_github_templates.py` (compile truth tables) + additive setup-service tests (github candidates, readiness gating, clarify).

## Notes / open questions

- Templates are data + a builder, not five classes — keep the closed table shape the 160 rule-table established.
