# CAD-1-06 — Unit/integration tests + the no-side-effects guard

- **Program:** cadence-engine · **Phase:** 1 · **Status:** done (built + tested; CI green) — locks the phase's behavior.
- **Depends on:** CAD-1-01..05.

## Problem

The substrate's invariants (idempotent projection, killed-stays-killed, off-by-default byte-identity,
no external side effects) must be mechanically enforced, not just hand-checked, before any surface
builds on it.

## The design

Most behavior is covered by the per-story tests (1-01..05). This story adds the **cross-cutting
guards** and fills gaps:

1. **No-side-effects guard** — a test that imports the whole `holdspeak.cadence` package and asserts
   it makes **no** network/connector/actuator-execute calls: grep/AST the package for forbidden
   symbols (`record_proposal` is allowed only from Phase 6+; in Phase 1 assert it's absent), and a
   runtime test that a full `tick()` writes only `cadence_*` tables (no `actuator_proposals`
   insert, no socket). This is the structural proof of the chart's trust boundary.
2. **Off-by-default byte-identity** — `enabled=False` ⇒ `WebRuntime` starts no cadence thread and
   the cadence tables stay empty after a start/stop cycle.
3. **Determinism** — scoring + scheduling with an injected `now` are reproducible (no `datetime.now()`
   leakage inside the pure functions).
4. **Idempotency + killed-survives** — re-collection invariants (also in 1-02; assert here as the
   canonical regression).
5. **Fixtures** — a small seeded-DB fixture (meeting + actions + a pending proposal) in
   `tests/integration/conftest` reused by collector/scheduler/CLI tests.

## Scope

- **In:** the no-side-effects guard, the off-by-default test, determinism + idempotency regressions,
  shared fixtures.
- **Out:** dogfood protocol/e2e (Phase 8), any LLM-path tests (Phase 7).

## Proof / acceptance

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py` green.
- The no-side-effects guard fails if any cadence module gains a connector/execute call.
- The off-by-default test fails if the thread starts when disabled.

## Test plan

The aggregate above is the test plan; CI runs it via the standard `uv run pytest -q` (these live in
`tests/unit` + `tests/integration`, no opt-in flag — they're hermetic, no network, no model).
