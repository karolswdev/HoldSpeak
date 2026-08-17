# HS-135-07 — The Brief lane

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** HS-135-05
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

The desk speaks first (Phase 126) — but the Brief lives in a pullout.
Lane one of the Chair: the Brief's headline truths, at a glance.

## Scope

### In

- The Brief lane composes the existing Brief view's summary data
  (the "N things waiting" headline + the Changed/Broke/Waiting/
  Decisions counts + top items to the curated bound) via the lane
  contract; header-click opens the Intelligence window on the Brief
  wing (single-instance); Acknowledge/Defer ride as per-item verbs
  where the existing surface exposes them.
- Truthful states: the no-false-ALL-CLEAR law (Phase 132) holds — the
  lane can never say clear while commitments exist (reuse the fixed
  collector; test it at the lane).

### Out

- Brief generation changes; Wave-2 Daily-Brief merge; new data
  endpoints (compose what exists).

## Acceptance criteria

- [x] Seeded state renders the real headline + counts; empty state is
  honest; never false-clear (tests).
- [x] Header opens Intelligence/Brief window; item verbs persist their
  effects (reload test).

## Test plan

- `cd web && npx vitest run` — new lane suite + intelligence suites
  touched.
