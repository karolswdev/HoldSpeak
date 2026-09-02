# HS-164-01 - The due ledger: cadence, opt-in, circuit — trace-first

- **Project:** holdspeak
- **Phase:** 164
- **Status:** done
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

## Trace record

### Decision 1: Legacy vs graduated scheduler boundary

The **legacy scheduler** is `ReactionService.refresh_due_watches`
(reaction_service.py:308). It owns the pre-graduation connector_watches
rows: reads cadence from `watch["query"].get("refresh_interval_minutes")`
(JSON, not a column) and uses `watch["updated_at"]` as the due-ness
clock.

The **graduated path** (WatchSpec@1, HS-159-01) already has
`next_evaluation_at` and `last_evaluated_at` columns on
connector_watches (schema.py:2322-2323) and `WatchService.evaluate`
writes `last_evaluated_at` (watch_service.py:637). What was missing: a
REAL column for the cadence value itself so the graduated scheduler
never digs into JSON. Added `evaluation_cadence_minutes INTEGER NOT NULL
DEFAULT 60` — the legacy path keeps reading JSON; the graduated path
reads the column. Story 02 traces the boundary in full.

### Decision 2: Durable vs in-memory circuit

The HS-103-04 circuit breaker (`endpoint_health.py`) is purely
in-memory: `_EndpointState` tracks `consecutive_failures` and
`opened_at` (monotonic time), keyed by endpoint string, lost on
restart. Shape: 3 failures open the circuit; after cooldown one
half-open probe is allowed through.

**Decision: DURABLE.** The charter requires STW-009 (recovery) and
restart survival. Added to connector_watches:
- `circuit_state TEXT NOT NULL DEFAULT 'closed'` (closed/open/half_open)
- `circuit_failure_streak INTEGER NOT NULL DEFAULT 0`
- `circuit_opened_at TEXT` (nullable, ISO timestamp)

No `circuit_half_open_at` column: the scheduler derives half-open from
`circuit_opened_at + cooldown_seconds` (already on steward_policies).
The in-memory EndpointHealth stays for LLM endpoints; the watch circuit
is its own concern with its own persistence.

### Decision 3: Opt-in home

`steward_policies` already has `enabled` (general policy on/off),
`bounds_json`, and `cooldown_seconds`. The bounded-delegation ruling
demands an EXPLICIT opt-in for unattended work, default OFF.

**Decision: a REAL named column, not bounds_json.** Added
`unattended_enabled INTEGER NOT NULL DEFAULT 0` on steward_policies.
Disabling is a plain `UPDATE steward_policies SET unattended_enabled=0`
— immediate and durable. The column is law-bearing (the conductor must
check it before every unattended run); a JSON field would be invisible
to a simple query and would not carry a NOT NULL + DEFAULT constraint.
