# HS-200-22: Integrate the calendar work required by daily recipes

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-01, HS-200-09, HS-200-11, HS-200-21
- **Unblocks:** HS-200-23, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-CTX-002; AA-AUT-003; AC-04, AC-18; C5, C9

## Problem

Calendar work is already authored in Phase 175. Integration should follow actual workflow needs and preserve explicit recording intent.

## Scope

Inspect current PR 558 and adopt the useful event/context and preparation seams. Complete the required faces and inherited proof.

Implementation seams: Calendar ingest and events; Door upcoming; scheduled recording services; Phase 175 branch lineage.

Out: Rebuilding the calendar adapter or requiring calendar access for first value.

## Acceptance criteria

- [ ] Record an exact disposition for every carried Phase 175 change before integration.
- [ ] Meeting preparation works with a manual purpose and with an explicitly associated event.
- [ ] Ambiguous Project matching, changed events, cancellation, time zones, and recurrence have defined behavior.
- [ ] Recording activation follows existing explicit settings and authority; an inferred association alone cannot grant new recording intent.
- [ ] Imported behavior has production-path and compact-layout proof. Remaining Phase 175 work keeps a named destination.

## Test plan

Existing calendar/scheduled-recording suites plus planned phase200_calendar_recipe tests. Browser: event-linked preparation and recovery. Physical recording proof only for enabled recording behavior.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
