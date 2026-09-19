# HS-200-47: A schedule knows its own zone instead of following the hub's clock

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-200-33, HS-200-34, HS-200-53
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); C9's time-zone interpretation clause; AC P200-A25

## Problem

**The product's only cron wall clock has no recorded zone, and it reads a naive
clock.**

`cron_is_due` takes `now = datetime.now()` when the caller supplies nothing
(`holdspeak/cron.py:45`) — a naive local timestamp with no `tzinfo`. Its one
scheduled caller passes nothing: `_cron_is_due(wb.schedule)`
(`holdspeak/workbench_conductor.py:544`, through the one-line wrapper at
`:148-151`, which accepts no `now`).

And the row has nowhere to say what zone it meant. `workbenches` carries
`schedule`, `schedule_enabled`, `schedule_revision`
(`holdspeak/db/schema.py:1714-1716`) and no zone column. So `0 8 * * 1` means
"whatever the hub's OS clock calls 08:00 today" — which moves by an hour across
a DST boundary, moves again if the hub is relocated, and is recorded nowhere
that the owner or an occurrence receipt can read.

**The product already knows how to do this correctly one module away.**
`ScheduledRecordingService.create_schedule` takes a `tz` parameter
(`holdspeak/services/scheduled_recording_service.py:177`), derives the hub's
local zone with a UTC fallback when it builds a schedule from a calendar event
(`:235-240`), and persists it on the row (`:289`). `scheduled_recording_conductor`
imports `cron_is_due` and `next_cron_fire` from the same module
(`holdspeak/scheduled_recording_conductor.py:29`) — the same helper, used with a
zone.

This is a correctness defect in a shipped path. It is not a rider on the recipe
work: it will outlive this cluster, and every occurrence identity C9 requires
("binding revision, time-zone interpretation, scheduled time") is wrong until it
is paid.

## Scope

Give a Workbench schedule an explicit zone, interpret its cron in that zone, and
record the interpretation on the occurrence so a receipt says which local time
fired.

Implementation seams: `holdspeak/db/schema.py` (`workbenches`, additive only —
`feedback_migrations_stay_minimal`); `holdspeak/cron.py`;
`holdspeak/workbench_conductor.py` (`_cron_is_due` and its `_tick` caller);
`holdspeak/services/workbench_service.py` schedule verbs and the routes and MCP
family that reach them; `holdspeak/services/schedule_delegation.py` `_terms`
(the frozen `cadence` string is the zone's natural home in the delegation hash).

Out: a second scheduler, a calendar-aware schedule, or changing the five-field
cron grammar. Out: retiring the naive default from `cron_is_due` for callers
that legitimately pass their own `now` — the defect is the missing zone, not
the helper's signature.

## Acceptance criteria

- [ ] A Workbench schedule records the zone it was authored in, and an existing
      row with no zone resolves to a named default rather than an implicit one.
- [ ] `cron_is_due` is evaluated against a zone-aware instant for the scheduled
      path; the conductor no longer relies on `datetime.now()` with no `tzinfo`.
- [ ] A spring-forward gap and an autumn fold each produce the declared number
      of firings — proven by injected time, not by waiting for a real DST date.
- [ ] Moving the hub's OS zone does not change when an existing schedule fires.
- [ ] The zone is part of the delegation's frozen terms, so changing it changes
      `terms_sha256` and requires the owner's re-approval like any other term
      (`holdspeak/services/schedule_delegation.py:37-39`).
- [ ] An occurrence receipt names the local time and the zone it was computed
      in, not only the epoch minute.
- [ ] Every new fence is proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_schedule_zone`. Drive the real conductor tick and the
real `cron_is_due` with injected instants across a DST gap and fold; drive the
real schedule verb for the stored zone and the real
`ScheduleDelegationService` for the terms hash. Assert against the real
constants, never a transcribed copy (`reference_lying_test_doubles`).

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidates (HS-200-46).** Two sentences here must stay true and belong
in `tests/unit/doc_claims/registry.py` once this ships: that the scheduled cron
path evaluates against a zone-aware instant, and that `workbenches` carries a
zone column read by the conductor. Both are cheap predicates over the real
module and the real `SCHEMA_SQL`. Each is **`known_false` today** and can enter the registry before the fix: the predicate fails now, and HS-200-46's rule makes it fail again the moment the code starts satisfying it, which forces the flip to `holds` in the same commit as the repair.

**Unknown, not broken:** the clock is reported never to have fired on the owner's
machine — `kernel_schedule_ticks` empty on his desk, a figure carried from the 2026-09-18 clock measurement's read of his real database, not measured by this lane — so no DST
drift has actually harmed him. What IS measured here is the code: the naive clock
and the missing column, both read at the file:line above on `ba48baf3`.
