# HS-200-52: A surface can create a recurring binding that actually recurs

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-43
- **Unblocks:** HS-200-33
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); HS-200-43's arming work; C9

## Problem

**HS-200-43 made a watch arm the moment it exists. The general-purpose create
verb still mints one that can never arm.**

`ReactionService.create_watch` (`holdspeak/services/reaction_service.py:219`)
calls `self._repo.create_watch(...)` at `:229` with no `state`, and the repo's
INSERT names six columns — `id`, `connector_id`, `query_kind`, `name`,
`query_json`, `enabled` (`holdspeak/db/automations.py:30-36`). `state` takes its
schema default of `''` (`holdspeak/db/schema.py:2483`).

An empty state is refused everywhere it matters:

- `arm_watch` returns `None` for any state outside
  `_EVALUABLE_STATES = {"active", "tested"}`
  (`holdspeak/services/watch_service.py:67`, `:115`), and
  `set_watch_enabled` says so in its own comment — *"a legacy row stays owned by
  `refresh_due_watches` and never crosses into `evaluate_due`'s territory"*
  (`holdspeak/services/reaction_service.py:242-250`).
- `list_due_watches` selects only `state IN ('active','tested')` with a non-NULL
  `next_evaluation_at` (`holdspeak/db/automations.py:457-458`).

That verb is what both general surfaces reach: `POST` on the automations route
(`holdspeak/web/routes/automations.py:187-191`) and the MCP family
(`holdspeak/mcp/families/reactions.py:76`). **Neither can create a connector
watch that the scheduler will ever pick up.**

The mints that DO produce an evaluable row are not general surfaces:
`ProjectService.create_from_setup` writes `state="active"` and arms in the same
transaction (`holdspeak/services/project_service.py:2524`,
`:2538`) — reachable only by creating or finalizing a Project — and
`ensure_meeting_watch` writes `state="active"` for the `meeting` connector
(`holdspeak/services/watch_service.py:1553`), fired automatically when a meeting
is linked (`holdspeak/runtime/routing_glue.py:313-314`,
`holdspeak/services/project_service.py:3473-3474`,
`holdspeak/services/heartbeat_service.py:507`), never by an owner's create act.

So the owner's only route to a working recurring **change-driven** binding is to
create a whole Project. This sits beside the cluster's clock work rather than
inside it: it is the same defect class — a create path that mints something the
scheduler refuses — on the other recurring owner.

## Scope

Make the general create verb mint a watch the scheduler can select, or refuse
honestly and name the path that can, and settle what the legacy `state=''`
population is for.

Implementation seams: `holdspeak/services/reaction_service.py` (`create_watch`,
`set_watch_enabled`); `holdspeak/db/automations.py` (`create_watch`);
`holdspeak/web/routes/automations.py`; `holdspeak/mcp/families/reactions.py`;
`holdspeak/services/watch_service.py` graduation and `arm_watch`.

Out: changing `_EVALUABLE_STATES`, the cadence model, or the circuit breaker.
Out: retiring `refresh_due_watches` and the legacy rows it owns — if the two
schedulers must stay separated, say so in the evidence and keep them separated.

## Acceptance criteria

- [ ] A watch created through the real automations route and a watch created
      through the real MCP verb are both selectable by the real
      `list_due_watches`, or both refuse with a sentence naming what is
      required — and the refusal is an error, not a soft `success: false`
      (HS-200-45's rule).
- [ ] The graduation path from a created watch to an evaluable one is reachable
      by the owner without creating a Project, and is proven end to end.
- [ ] Baselining stays silent: the first evaluation of a newly created watch
      returns `baselined` with zero transitions, as HS-200-43 established — a
      new create path must not reopen the discovery flood counsel reproduced.
- [ ] Paused, retired and disabled rows are untouched by the change.
- [ ] The legacy `state=''` population's owner is stated and unchanged, or
      migrated deliberately with the reason recorded.
- [ ] A fence reproduces the defect against the pre-fix tree — create through
      the real route, assert `list_due_watches` never returns it — and passes
      after.

## Test plan

Planned suite: `phase200_watch_create_armable`. Drive the real HTTP route and
the real MCP dispatch against a real temporary database; assert selection
through the real `list_due_watches`, never a re-read of the row the test wrote
(`reference_lying_test_doubles`). Extend
`tests/unit/test_phase200_watch_arming.py` where its legs already cover the
same seam rather than mirroring them.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidate (HS-200-46).** One sentence must stay true: every watch
create path reachable from a surface yields a row the scheduler can select, or
refuses. The predicate drives the real create verbs and the real selector. Each is **`known_false` today** and can enter the registry before the fix: the predicate fails now, and HS-200-46's rule makes it fail again the moment the code starts satisfying it, which forces the flip to `holds` in the same commit as the repair.

**Unknown, not broken.** Whether the owner's 32 existing watches include any
`state=''` row that he expected to recur is not measured here — reading his
real database is not this lane's to do. The measurement is of the code paths,
not of his data.
