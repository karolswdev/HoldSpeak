# HS-2-04 — Step 3: Plugin host integration

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-02, HS-2-03
- **Unblocks:** HS-2-06, HS-2-07
- **Owner:** unassigned

## Problem

Spec §9.4 — wire the router output to the plugin host so each window
triggers the right plugin chain per active profile, recorded as
`PluginRun` entries.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.4.
- **Out:** Persistence schema (HS-2-05); synthesis pass (HS-2-07).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up._

## Notes / open questions

- Reuse the existing plugin-host surface used by deferred-intel, or fork a meeting-window-aware variant? Spec §5.3 expects integration, not a fork; confirm at pickup.
