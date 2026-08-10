# HS-131-06 — Scheduled work carries bounded delegation

- **Project:** holdspeak
- **Phase:** 131
- **Status:** in-progress
- **Depends on:** HS-131-01, HS-131-02, HS-131-05
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

The Workbench conductor currently treats `schedule_enabled` plus a matching cron
minute as sufficient authority and calls `run_workbench` with no authenticated
principal. A scheduler cannot impersonate the owner, and approval on every tick
would make recurring automation useless. The owner has ruled that deliberately
enabling the schedule grants bounded continuing authority for the exact work,
effective target, and cadence until changed or disabled.

## Scope

### In

- Persist a device-local, owner-created, revocable schedule delegation when the
  owner deliberately enables recurring Workbench or Cadence model work on that
  scheduler node. Synced schedule configuration is not authority and cannot
  mint or revive a delegation on another device.
- Bind the delegation to the exact Workbench/work definition revision,
  deployment revision/effective target, cadence, owner authority source,
  schedule revision, and optional explicit expiry. The ordinary contract lasts
  until changed or disabled; it does not demand periodic reapproval. Store no
  credential.
- Authenticate the conductor as a scheduler principal. At each due tick the
  kernel derives authority from the live delegation reference; the scheduler
  never submits an owner principal or calls `decide` as the owner.
- Admit every due parent run and all invocation children normally. Record actor
  `scheduler`, the bounded delegation as authority basis, and the owner as
  delegator.
- Disable, revoke, expire, or invalidate delegation when the schedule, work
  definition, effective inherited target, or cadence changes. Refuse stale or
  mismatched ticks by name before provider dispatch.
- Preserve minute-level dedupe from
  `holdspeak/workbench_conductor.py:704-738` as idempotency, not authority.
- Apply the same bounded-delegation contract to any Cadence-triggered model work
  found by the phase fence; pure scoring/scheduling computation remains
  non-inference.

### Out

- Generic grants for unrelated autonomous effects.
- Approval on every tick.
- Silent retargeting when a global or inherited target changes.
- New scheduling UI beyond wiring the existing enable/disable gesture to the
  delegation contract.

## Acceptance criteria

- [ ] Enabling a schedule as the owner creates one delegation bound to exact
  work, effective target/deployment revision, and cadence.
- [ ] A due tick authenticates as the scheduler, derives authority from that
  delegation, and creates a normal admitted parent plus invocation children.
- [ ] Receipts distinguish actor, delegator, authority basis, target, and
  outcome; no receipt falsely names the owner as the executing actor.
- [ ] Disabled, revoked, duplicate, stale-definition, changed-cadence, and
  changed-target ticks refuse by name before any model call and leave a terminal
  refusal receipt. Expiry is enforced only when the owner explicitly chose that
  bound; the default delegation lasts until changed or disabled.
- [ ] Editing any bounded term invalidates the old delegation and requires a new
  deliberate enable gesture.
- [ ] Disabling during an active run revokes future claims and cancels or marks
  the active operation indeterminate according to the runner contract; late
  output cannot publish.
- [ ] A scheduler or agent principal cannot mint, widen, approve, or reactivate
  the delegation.
- [ ] Syncing an enabled schedule to another device does not sync authority or
  start model work there; that device refuses `delegation_missing` until its
  owner deliberately enables the schedule locally.
- [ ] Existing cron matching and dedupe behavior remain deterministic.

## Test plan

- Unit: focused delegation codec/policy tests; Workbench conductor tests for due,
  duplicate, disabled, explicitly owner-expired, revoked, stale work, target
  change, cadence change, and actor/delegator receipt fields.
- Integration: real scheduler tick through kernel admission and one LAN model
  child; disable during execution; restart with a persisted live delegation.
- Manual / device: enable one short schedule, observe one run, change its target,
  observe named refusal, then deliberately re-enable and observe the new exact
  revision.

## Notes / open questions

"Until disabled" does not mean an old delegation silently follows edited
configuration. The approval is for exact terms. A change invalidates those
terms, and the Desk must require the existing deliberate enable gesture again.
