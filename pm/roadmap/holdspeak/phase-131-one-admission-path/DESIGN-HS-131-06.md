# HS-131-06 design — Scheduled Workbench work carries bounded delegation

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-10) — the nine amendments in the Sol ruling below are binding on implementation  
**Decision boundary:** make an owner's existing Workbench schedule-enable gesture a device-local, exact-terms delegation. Every valid tick uses HS-131-05's admitted `WorkbenchRunner`; no scheduler-owned direct inference loop, new schedule UI, or generic autonomous grant is introduced.

## Context

`holdspeak/workbench_conductor.py:421-679` still treats a matching cron minute as authority, creates its own `workbench_runs` record, and calls `intel.run_prompt` directly. Its `run_workbench(..., principal=None)` seam deliberately leaves that leg for this story (`:682-695`). HS-131-05 supplies the replacement: `WorkbenchRunner` starts a durable `workbench.run` parent, admits each item/memory child, receipt-gates projections, and adopts a concurrent terminal receipt (`holdspeak/services/workbench_runner.py:85-98`). `ParentRunController` is the only parent opener/closer and its epoch cancellation fences late child projections (`holdspeak/kernel/parent_run.py:105-129,182-246`).

The owner ruling grants continuing approval only for the configured work, effective target, and cadence on this device. `sync_service.py:75` currently syncs `schedule` and `schedule_enabled`; that is configuration, never authority.

## 1. Device-local delegation record

Schema v52 adds `kernel_schedule_delegations` and no `SYNC_REGISTRY` entry:

```sql
id TEXT PRIMARY KEY, workbench_id TEXT NOT NULL UNIQUE,
delegator_kind TEXT NOT NULL, delegator_identity TEXT NOT NULL,
recipe_id TEXT NOT NULL, recipe_revision TEXT NOT NULL,
workbench_revision TEXT NOT NULL, schedule_revision TEXT NOT NULL,
cadence TEXT NOT NULL, deployment_revision_id TEXT NOT NULL,
terms_sha256 TEXT NOT NULL, expires_at REAL,
state TEXT NOT NULL CHECK (state IN ('LIVE','REVOKED','EXPIRED')),
revoked_at REAL, revocation_reason TEXT NOT NULL DEFAULT '',
created_at REAL NOT NULL, updated_at REAL NOT NULL
```

`recipe_revision` is `recipes.last_modified`, the same immutable-at-admission `SavedDefinition` revision established by HS-131-03 and already used by `WorkbenchRunner` (`workbench_runner.py:112`). `workbench_revision` is `workbenches.last_modified`; `schedule_revision` is a new monotonic `workbenches.schedule_revision INTEGER NOT NULL DEFAULT 1`, incremented only when `schedule`, `schedule_enabled`, `recipe_id`, or `profile_id` changes. `deployment_revision_id` is the exact result of resolving Workbench → Recipe → global placement and `capture_deployment_revision`. `terms_sha256` canonically hashes every preceding bound term plus nullable expiry. It contains neither a credential nor a provider secret.

The unique active row is replaced, not mutated: replacement first marks the prior row `REVOKED`, then inserts a new ID in the same transaction. Historical rows retain the authority basis named by receipts.

## 2. Owner gesture is the sole minting/reapproval seam

In `holdspeak/services/workbench_service.py`, `create_workbench()` (`:40-48`, including template creation at `:195-199`) and `update_workbench()` (`:50-57`) compare old and proposed bound terms before persistence. Only an authenticated `PrincipalKind.OWNER` may make `schedule_enabled` transition false → true; after writing the configuration, `ScheduleDelegationService.enable_from_owner()` resolves and snapshots the terms above and atomically replaces the local delegation. A non-ready target refuses the enable write rather than creating an unusable approval.

Changing a bound field, including any synced update, revokes the old local row in that write transaction and leaves `schedule_enabled` configuration intact but locally unauthorized. Reapproval is the existing disable/enable control; no new UI is needed. A scheduler or agent request is refused for enable, replacement, reactivation, or term widening. `schedule_enabled` true arriving through sync creates nothing; its first due tick is `delegation_missing`.

On disable, the same service transaction marks the live delegation `REVOKED` with `schedule_disabled`, then finds open Workbench parents whose frozen `delegation_id` is that row. After commit it invokes `ParentRunController.cancel_by_operation_id()` using the internally issued scheduler principal for each exact operation. The controller's state/epoch transition cancels the active child and prevents queued admission; `WorkbenchRunner._adopt_terminal()` retains the winning cancellation receipt and late output cannot finalize.

## 3. Scheduler admission and tick flow

Add `PrincipalKind.SCHEDULER`; the conductor constructs only `Principal(SCHEDULER, "local-workbench-conductor")`. It has no owner/decide/delegate right. Add a narrow parent-controller delegated-start path, not a parallel controller: `ParentRunController.start_delegated_schedule(...)` submits `workbench.run@1` with that principal and freezes `delegation_id`, `terms_sha256`, and the bound terms in the parent input. Kernel parent admission validates the local row under its admission transaction, applies the authority basis `schedule-delegation:<id>:<terms_sha256>`, and auto-admits this one bounded scheduler operation. The scheduler never supplies an owner principal and never calls `decide`.

`WorkbenchConductor._tick()` retains cron matching and `_last_check` minute dedupe, but replaces `run_workbench(wb.id)` with `WorkbenchRunner.run_scheduled(scheduler_principal, wb.id)`. For each due minute that method:

1. re-reads the device-local delegation and live Workbench/Recipe/placement;
2. checks enabled state, `LIVE`, optional expiry, cadence, schedule revision, Recipe ID/revision, Workbench revision, and captured deployment revision;
3. invokes the delegated parent start, whose kernel-side check repeats those terms atomically; and
4. only if admitted, calls the existing `WorkbenchRunner` item/memory loop with the scheduler principal and frozen parent terms.

The runner must use the already frozen deployment revision for the scheduled parent's first child; per-child resolution remains permitted only when it still equals the delegation's bound deployment revision. A mismatch closes/refuses before dispatch, never silently retargets.

Final refusal names are `schedule_disabled`, `delegation_missing`, `delegation_revoked`, `delegation_expired`, `delegation_cadence_changed`, `delegation_stale_work`, and `delegation_target_changed`. The delegated-start path records one terminal refused parent-attempt receipt with that reason before provider construction/dispatch. It is also used for a duplicate due tick (`duplicate_tick`), although normal `_last_check` prevents that path. Valid ticks create the ordinary admitted durable parent and normal invocation children.

## 4. Receipt and recovery truth

The parent and child receipt provenance records `actor_kind=scheduler`, `actor_identity=local-workbench-conductor`, `delegator_kind=owner`, `delegator_identity`, `authority_basis=schedule-delegation:<id>:<terms_sha256>`, frozen `deployment_revision_id`, and terminal outcome. The delegator is metadata, never the executing principal. Child receipts inherit their scheduler parent causation; no receipt labels the owner as actor.

A process restart keeps a `LIVE`, unexpired delegation. The next due tick revalidates it and proceeds without reapproval. Existing controller lease reconciliation remains responsible for a parent abandoned mid-run.

## 5. Migration and deletion

Bump `holdspeak/db/schema.py` from v51 to v52; add the delegation table, its `workbench_id/state` lookup index, and `workbenches.schedule_revision`. Add repository/codec access only for the local delegation table; exclude it from sync. Migrate the normal schema-upgrade path with existing rows defaulting schedule revision to 1 and **no** delegations, so every pre-v52 enabled schedule refuses `delegation_missing` until the owner toggles the existing control locally.

Delete `_run_scheduled_workbench_legacy`. Make `run_workbench()` require an explicit principal and retain it solely as the manual compatibility seam; `principal=None` raises the named `scheduler_principal_required` service refusal. The conductor calls the dedicated scheduler entry only.

## Invariants

1. A valid schedule is one local, owner-created, exact-terms delegation; sync cannot mint, revive, or widen it.
2. Every scheduled provider call is an HS-131-05 child of one scheduler-actor admitted `workbench.run` parent.
3. Every invalid due tick has a named terminal refusal receipt before provider dispatch.
4. Disable/revocation wins over future child admission and over late projection publication.
5. A persistent valid delegation survives restart; a changed work, cadence, target, or explicit expiry does not silently follow configuration.

## Test matrix

| Acceptance criterion / invariant | Planned focused proof |
| --- | --- |
| Owner enable snapshots exact terms; no credentials | `tests/unit/test_schedule_delegations.py::test_owner_enable_creates_local_exact_terms_delegation` |
| Scheduler parent/children and receipt actor/delegator truth | `tests/unit/test_schedule_delegations.py::test_due_tick_uses_scheduler_parent_and_admitted_workbench_runner_children` |
| Named pre-dispatch refusals | `tests/unit/test_schedule_delegations.py::test_due_tick_refuses_disabled_revoked_expired_stale_cadence_and_target_before_provider` |
| Edit invalidates; scheduler/agent cannot mint | `tests/unit/test_schedule_delegations.py::test_bound_edit_revokes_and_requires_owner_reenable` |
| Synced enable is configuration only | `tests/unit/test_schedule_delegations.py::test_synced_enabled_schedule_refuses_delegation_missing` |
| Disable races active dispatch | `tests/unit/test_schedule_delegations.py::test_disable_cancels_scheduler_parent_and_fences_late_output` |
| Dedupe and restart | `tests/unit/test_workbench_conductor.py::test_minute_dedupe_and_restart_with_live_delegation` |
| Production tick | `tests/e2e/test_workbench_walk.py::test_local_owner_schedule_receipt_and_reenable` |

## Recorded notes

- `_last_check` stays in-memory idempotency only. A process restart can cause at most one duplicate tick; both attempts are admitted and receipted. Durable per-minute claiming adds mechanism without addressing a likely yolo-mode defect, so it is not required here.
- Cadence census: `cadence/scheduler.py` and `cadence/service.py` ticks perform scoring/projection only. The sole Cadence LLM call is authenticated request-time `holdspeak/services/cadence_service.py:131`, owned by HS-131-07. This contract applies to future Cadence-triggered model work, but adds no Cadence runner now.
- Cross-device replay, clock tampering, and global distributed cron leadership are not mandatory at the owner-set yolo bar; the local durable delegation, kernel revalidation, and receipt trail cover real configuration and cancellation failures.

## Open questions for Sol

1. Ratify `schedule_revision` as a synced configuration revision, or replace it with the existing Workbench revision plus the individually compared schedule fields; the latter is less schema but cannot name schedule-only revision independently.
2. Ratify the narrow `ParentRunController.start_delegated_schedule()` admission extension and refused parent-attempt receipt as the controller-only path, including scheduler auto-admission without `decide`.
3. Ratify template creation with an enabled schedule as the owner's deliberate enable gesture, provided its resolved target is ready; otherwise require templates to start disabled.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The design has the right authority model and
addresses the charter's acceptance criteria in substance: device-local
delegation, exact-term binding, scheduler-as-actor, owner-as-delegator, kernel
re-derivation, pre-dispatch refusals, ordinary admitted children, restart
persistence, and conservative migration. The following amendments are required
to close real races, prevent duplicate work, and make the promised receipt
provenance implementable.

### Amendments (binding)

1. **Replace `UNIQUE(workbench_id)` with a partial unique index covering only
   the live delegation for each Workbench.** The proposed constraint makes
   revoke-then-insert impossible while retaining historical rows, contradicting
   the receipt-history contract.
2. **Persist the enabling configuration change, resolved deployment revision,
   and replacement delegation in one `BEGIN IMMEDIATE` transaction.** Otherwise
   a crash or concurrent target edit can leave the control enabled without the
   delegation the owner's gesture purported to create.
3. **Implement `start_delegated_schedule()` as a dedicated controller-only
   atomic admission path, and permit `SCHEDULER` children only through
   `submit_trusted_child` after its parent capability and frozen delegation
   have been re-derived under lock.** The generic broker currently rejects
   non-owner/non-agent principals; globally admitting schedulers there would
   grant broader authority than the delegation permits.
4. **Have scheduler child operations inherit the parent's exact
   `schedule-delegation:<id>:<terms_sha256>` authority basis and immutable
   delegator reference rather than the trusted-child path's generic authority
   string.** The current child journal cannot otherwise produce the receipt
   provenance promised by the design.
5. **Make every disable or bound-term invalidation atomically revoke the
   delegation and epoch-fence all matching open parents before the transaction
   commits, then signal providers and complete receipt-winner adoption after
   commit.** Revoking first and calling `cancel_by_operation_id()` afterward
   leaves a real window — and a crash boundary — in which a revoked parent can
   admit or publish another child; this rule covers Recipe revision and
   effective-deployment changes, not only WorkbenchService fields.
6. **Put the Workbench item `claimed` transition behind the parent epoch fence
   or conditionally restore it when cancellation wins before adopting the
   terminal receipt.** The existing runner can write `claimed` after
   cancellation, lose child admission, and leave the item permanently stuck
   even though output publication is correctly fenced.
7. **Give each scheduled due minute a durable identity and atomically emit
   `duplicate_tick` for a second claim before provider dispatch, while
   retaining `_last_check` only as the in-process fast path.** Restart-double
   admission of the same minute contradicts the charter's duplicate-tick
   refusal criterion and causes real duplicate inference.
8. **Keep `schedule_revision` as a device-local monotonic persistence revision
   that increments for every local or incoming synced bound-field change,
   rather than accepting a remotely supplied counter value.** Independent
   devices can produce equal or regressing counters; local monotonicity stays
   honest.
9. **Create template Workbenches with schedules disabled and require the
   existing explicit enable control to mint delegation.** Choosing a template
   is not necessarily a deliberate recurring-inference gesture.

### Open-question rulings

1. `schedule_revision`: ratified as amended by Amendment 8 — independent
   revision, locally generated, never synced as authoritative counter state.
2. `start_delegated_schedule()`: ratified as amended by Amendments 3-5 —
   scheduler auto-admission without `decide` is sound only inside this narrow
   controller path, with durable authority re-derived atomically and no
   generic scheduler admission right.
3. Template creation: templates start disabled, per Amendment 9. Target
   readiness alone does not turn template creation into explicit
   recurring-work approval.

### Migration ruling

The v52 migration behavior is **correct and required**. A pre-v52
`schedule_enabled=true` row cannot prove this device received a deliberate
local owner gesture rather than synced configuration, so `delegation_missing`
until local disable/re-enable is honest rather than excessively hostile.

### Sol recorded notes

- No Cadence runner is required in this story; the scheduled Cadence tick
  performs no model inference.
- Cross-device replay hardening, clock-tamper defenses, distributed cron
  leadership, and periodic reapproval remain below the owner-set rigor bar.
- Once Amendment 7 supplies durable due-minute identity, `_last_check`
  remains an optimization, never an authority source.

### Orchestrator disposition

All nine amendments ADOPTED — each names a real-use defect class (crash
consistency, cancellation races, dishonest receipt provenance, duplicate
inference) or a charter AC (Amendment 7's duplicate-tick refusal), so none
falls to the yolo bar as a recorded note. Amendment 6 additionally patches a
latent HS-131-05 runner defect (post-cancellation `claimed` write stranding an
item) and its fix lands in `services/workbench_runner.py` within this story.
Amendment 7 supersedes the first recorded note above (in-memory dedupe alone
is no longer sufficient); the note is retained for history.
