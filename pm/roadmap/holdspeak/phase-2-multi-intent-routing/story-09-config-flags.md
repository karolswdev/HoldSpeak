# HS-2-09 — Step 8: Config + feature flags

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-06
- **Unblocks:** HS-2-10
- **Owner:** unassigned

## Problem

Spec §9.9 — make MIR-01 opt-in via config (mirror DIR-01's
`dictation.pipeline.enabled` pattern), with all knobs (window size,
hysteresis, profile selection, plugin allowlist) exposed as
documented config keys.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.9.
- **Out:** Observability counters + hardening (HS-2-10).

## Acceptance criteria

- [ ] _TBD when story is picked up; require byte-identical behavior with the flag off (mirror DIR-01 phase exit criterion #4)._

## Test plan

- _TBD when story is picked up._

## Notes / open questions

- Feature-flag namespace: `meeting.pipeline.enabled`? Cross-check existing config schema for collisions.
