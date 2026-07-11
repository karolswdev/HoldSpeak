# HS-91-05 — Activity, Commands, and Cadence in React

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01, HS-91-02
- **Unblocks:** HS-91-09
- **Owner:** unassigned

## Problem

These operational tools share repeated rule, connector, macro, test and status
patterns, but are implemented as independent pages and runtime HTML renderers.
They are the clearest proof that a shared React system can make dense tooling
feel deliberate instead of browser-default.

## Scope

- In: React `/activity`, `/commands`, `/cadence`; activity controls/sources/
  exclusions/rules/connectors/candidates; macro CRUD/test/fire; Cadence policy,
  rehearsal and feedback; shared dense table/card/action patterns.
- Out: new connectors/macros/coaching features; backend changes not required by
  an already-documented parity defect.

## Acceptance criteria

- [x] All ledger verbs and states pass for all three routes.
- [x] Runtime-created raw HTML/buttons are gone; lists render as keyed React
      components using Signal controls and status components.
- [x] Destructive actions use the shared confirmation contract and return focus
      to the trigger; pending/error/success states do not shift controls.
- [x] Dense layouts remain usable at compact-Web width with no sub-24 px target
      or horizontal viewport overflow.
- [x] Existing backend integration tests stay green and cohort Astro/scripts
      are removed.

## Test plan

- Unit: form/list reducers, connector and macro interaction tests.
- Integration: existing Activity/Commands pytest plus browser CRUD/test flows.
- Manual / device: activity rule + connector dry run; macro test/fire; Cadence
  rehearsal with honest unavailable-runtime state.

## Notes / open questions

“Dense” is a presentation variant of the same components, not permission to
invent smaller, raw controls.
