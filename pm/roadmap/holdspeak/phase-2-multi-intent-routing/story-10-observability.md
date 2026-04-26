# HS-2-10 — Step 9: Observability + hardening

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-09
- **Unblocks:** HS-2-11
- **Owner:** unassigned

## Problem

Spec §9.10 — structured logs, runtime counters
(`window_starts`, `intent_transitions`, `plugin_runs`,
`plugin_failures`, `synthesis_dedupe_hits`, etc.), `holdspeak doctor`
checks, and stop-path safety (no leaked threads / partial-state
corruption on Ctrl-C). Mirrors DIR-O-001/002 + DIR-DOC-001/002 from
DIR-01.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.10 + §6.5.
- **Out:** Final regression gate (HS-2-11).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up; reuse the stop-path deadlock test pattern called out in spec §12 mitigation #4._

## Notes / open questions

- Should `holdspeak doctor` get a single `meeting pipeline` check, or one per concern (router runtime, persistence schema, profile config)? DIR-01 went with two separate checks — likely the right precedent.
