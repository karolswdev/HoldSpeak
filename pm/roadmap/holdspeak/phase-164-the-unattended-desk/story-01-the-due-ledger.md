# HS-164-01 - The due ledger: cadence, opt-in, circuit — trace-first

- **Project:** holdspeak
- **Phase:** 164
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-164-02
- **Owner:** unassigned

## Problem

Unattended work needs durable bookkeeping: WHEN a watch is due, WHO
opted in, and WHETHER a source's circuit is open. §14 P5 + the
bounded-delegation ruling (an explicit opt-in approves the exact
configured work until disabled). Migrations stay minimal (owner
ruling): every column earns its place, and existing machinery is
traced before anything new (the 162 RIDE law).

## Scope

- **In:** TRACE FIRST: connector_watches' existing refresh/due
  machinery (ReactionService.refresh_due_watches already ticks in
  the conductor) and the 161 watch_rules/evaluations shapes — reuse
  or extend, never duplicate. Then additive schema (one version
  bump, named columns, snapshot regenerated, ALL version-pin tests
  greped and updated — the 163 scar): per-watch evaluation cadence +
  next_due/last_evaluated bookkeeping; per-project unattended opt-in
  on the steward policy (explicit, default OFF); durable circuit
  state per source/watch (opened_at, failure streak, half-open
  bookkeeping — trace holdspeak/intel/endpoint_health.py's HS-103-04
  shape and decide durable-vs-memory with STW-009 recovery in view).
  Repo methods with conn-accepting variants. Real-DB reconcile on a
  COPY (orchestrator's leg).
- **Out:** the schedulers (02/03), conductor wiring (04), UI (05).

## Acceptance criteria

- [ ] Additive bump; reconcile-from-prior green + idempotent; positional fence green; snapshot regenerated; EVERY schema-version pin found by grep and updated honestly.
- [ ] The opt-in is explicit and default OFF under test; disabling it is durable and immediate.
- [ ] Circuit state round-trips through repos; the trace decision (reuse vs new, durable vs memory) is recorded in the story file.

## Test plan

- **Unit:** tests/unit/test_unattended_schema.py.
