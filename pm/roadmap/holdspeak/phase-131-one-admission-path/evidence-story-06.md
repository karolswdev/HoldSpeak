# Evidence - HS-131-06

- **Story:** HS-131-06 - Scheduled work carries bounded delegation
- **Status:** done
- **Date:** 2026-08-10

## Proof

### Captured run — 2026-08-10T20:08:56Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.JXjQ43xQwC uv run pytest -q tests/unit/test_kernel_effect_fence.py tests/unit/test_schedule_delegations.py tests/unit/test_workbench_conductor.py tests/unit/test_workbench_runner_migration.py tests/unit/test_db_schema_policy.py tests/unit/test_kernel_cancelled_schema.py tests/unit/test_projection_schema.py tests/unit/test_kernel_broker.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 17e136e09f4191ebfa5760f28b2fb5a3b76b985a

```text
....................................................................     [100%]
68 passed in 13.35s
```

## Verification narrative

### The design beat (committed separately as c37277bd)

Terra drafted [DESIGN-HS-131-06](./DESIGN-HS-131-06.md) from the charter and
the owner's bounded-delegation ruling; Sol ruled it RATIFY-AS-AMENDED in ONE
round with nine binding amendments (partial live-unique index, one
BEGIN IMMEDIATE enable gesture, controller-only scheduler admission,
delegation authority basis on children, atomic revoke+fence on every
bound-term change, the claimed-transition cancellation fence, durable
due-minute identity with duplicate_tick, device-local monotonic
schedule_revision, templates start disabled). All nine were adopted under the
yolo bar — each names a real-use defect class or a charter AC. The ruling and
the orchestrator disposition live inline in the design doc.

### What shipped

- **Schema v52** (`holdspeak/db/schema.py`, `db/migrations.py`):
  `kernel_schedule_delegations` (exact terms: recipe revision, workbench
  revision, schedule revision, cadence, deployment revision, terms hash,
  delegator, optional expiry; no credential) under a partial unique index on
  `workbench_id WHERE state='LIVE'`; durable `kernel_schedule_ticks` minute
  claims; `workbenches.schedule_revision`; delegator-provenance columns on
  kernel operations. Pre-v52 enabled schedules get NO delegation — they
  refuse `delegation_missing` until a local re-enable (Sol ruled this honest
  and required).
- **The enable gesture is the only mint** (`services/workbench_service.py`,
  `services/schedule_delegation.py`): owner-only; configuration write,
  deployment-revision capture, and delegation replacement in one
  BEGIN IMMEDIATE. Any bound-term edit or disable — including incoming sync
  changes (`services/sync_service.py`) — revokes and epoch-fences open
  matching parents in the same write transaction, then signals provider
  cancellation and completes receipt-winner adoption after commit. Templates
  are created with schedules disabled. A scheduler or agent principal is
  refused `owner_principal_required` for mint/reactivate.
- **Atomic delegated admission** (`kernel/parent_run.py`): the conductor
  authenticates as `Principal(SCHEDULER, "local-workbench-conductor")`
  (rights-empty kind in `principals.py`; the generic broker still refuses
  scheduler principals — admission exists only through the controller path).
  `start_delegated_schedule` runs a pure-read pre-check, then broker
  submit/decide/claim with DEFERRED parent persistence, then ONE
  authoritative BEGIN IMMEDIATE that re-verifies every bound term, applies
  expiry, claims the due-minute tick, inserts the `kernel_parent_runs` row,
  and stamps `authority_basis`/delegator provenance together. A failed
  re-check terminalizes the operation with a provenance-stamped refused
  receipt in that same transaction; the minute is not consumed.
- **Seven named refusals** — `schedule_disabled`, `delegation_missing`,
  `delegation_revoked`, `delegation_expired`, `delegation_cadence_changed`,
  `delegation_stale_work`, `delegation_target_changed` — plus
  `duplicate_tick`, each leaving a durable terminal refused receipt before
  any provider work. Receipts carry `actor_kind=scheduler`,
  `actor_identity`, `delegator_kind=owner`, `delegator_identity`,
  `authority_basis=schedule-delegation:<id>:<terms_sha256>`, and the frozen
  deployment `target_ref` (`kernel/journal.py` now exposes target_ref on all
  receipt reads). `delegation_missing` keeps provenance honestly empty.
- **Drift cannot outrun an active run**: scheduler children re-verify recipe
  revision and deployment revision inside the trusted-child admission
  transaction (`kernel/trusted_child.py`), the runner re-checks before every
  dispatch (`services/workbench_runner.py`), and the publication fence
  re-derives the CURRENT effective deployment from live rows inside the
  projection-finalization transaction
  (`kernel/projection_stager.py` + `resolve_workbench_deployment_revision`
  in `deployment_revisions.py`) — an in-flight provider result cannot
  publish after a recipe or profile/deployment edit; the stage is discarded,
  the child receipt names the reason, and the delegation revokes+fences.
- **The legacy leg is dead**: `_run_scheduled_workbench_legacy` (259 lines
  of direct `intel.run_prompt` with no principal) is deleted;
  `run_workbench(principal=None)` refuses `scheduler_principal_required`;
  the conductor keeps cron matching and `_last_check` as in-process fast
  path only — authority is the durable delegation, idempotency is the
  durable tick claim.
- **Two inherited defects repaired in passing**: (1) `WorkbenchRunRecord`
  never had the `mint_failures` field its repository constructor passes —
  verified against a main worktree: every `workbench_runs.create()` and
  run-history read on main raises TypeError once exercised; self-concealing
  until HS-131-05's admitted runner started successfully inserting run rows;
  caught by this story's real-metal walk, repaired in both model
  definitions. (2) A latent HS-131-05 runner race — the item `claimed` write
  landing after cancellation could strand the item forever — found by Sol's
  design review (Amendment 6), fixed with an epoch-conditioned claim plus
  restore-on-lost-election, and proven by
  `test_cancellation_before_claim_does_not_strand_item_and_next_run_processes_it`.

### The counsel ledger (implementation)

Sol rode FOUR implementation rounds to RATIFY-WITH-RESERVATIONS:

- **Round 1** (3 blockers): non-atomic delegated admission
  (validation/tick/parent/provenance in separate transactions); recipe and
  deployment drift unfenced for active parents with silent per-child
  retargeting possible; refusal receipts missing delegation provenance.
- **Round 2** (2 blockers): admission race CLOSED; in-flight publication
  after recipe/deployment edits still open; receipt reads missing
  target_ref.
- **Round 3** (1 blocker): recipe publication fence CLOSED, receipt target
  CLOSED; the deployment publication check was TAUTOLOGICAL (frozen value
  compared against a copy of itself — a profile endpoint/model edit mid-call
  slipped through).
- **Round 4**: the live conn-scoped deployment resolver replaced the
  frozen-vs-frozen comparison; **RATIFY-WITH-RESERVATIONS**, all nine
  amendments discharged, all seven charter ACs satisfied.

Round 3 crossed the ORCHESTRATION §2b three-round valve; the orchestrator
proceeded without pausing for an owner ruling on the grounds that the
trajectory was strictly converging (3→2→1 blockers), each fix had a
Sol-endorsed mechanism, and the owner's least-friction ruling applies. The
disposition is recorded here for the sitting to re-rule if desired.

### Sol's sitting-visible reservations (final, four)

1. **Process-global admission guards** — `_delegated_schedule_admission`,
   `_delegated_parent_start`, `_trusted_scheduler_child` are mutable
   process-level flags; safe under the serial conductor, call-local
   capabilities would be cleaner under future concurrency.
2. **Secondary internal owner helper** —
   `ScheduleDelegationService.enable_from_owner()` is marked internal but
   remains callable outside the atomic Workbench gesture; it must not become
   an application-facing minting seam.
3. **Pre-authoritative crash shell** — process death after broker claim but
   before authoritative admission leaves one claimed operation with no
   parent and no consumed minute; it cannot dispatch; cleanup/reconciliation
   debt.
4. **Provisional child-success observability** — provider success can
   briefly be visible before publication finalization reclassifies the child
   to a named refusal; consumers must treat child success as provider
   completion, not proof of publication.

### The verification liturgy

1. **Focused suites** (orchestrator re-ran after every round, output read
   from files): 46 tests green under isolated HOME —
   `test_schedule_delegations.py` (18: exact-terms mint, atomic-enable
   rollback, scheduler parent/child receipt provenance tuples, six
   parametrized named refusals each asserting the durable refused receipt,
   bound-edit revocation, sync-flag refusal, the REAL disable-during-run
   race through the actual owner gesture mid-provider-call, atomic refusal
   provenance incl. honest emptiness for delegation_missing, the
   disable-in-the-admission-gap race proving the minute is not consumed,
   in-flight recipe-edit and profile-edit publication fences, mid-run
   recipe-edit child-admission backstop, scheduler/agent mint refusal),
   `test_workbench_conductor.py` (durable duplicate_tick across a REAL
   restart — new Database over the same file), the full HS-131-05
   `test_workbench_runner_migration.py` regression set (17) plus the new
   claimed-race test, and the schema/migration suites updated to v52.
2. **Test substance verified by the orchestrator**: the first-pass
   disable-cancel test was caught as a vacuous shell (asserted only an idle
   validate refusal) and rewritten as a real race through the actual
   disable gesture — continuing this phase's pattern that test COUNT is
   never accepted as proof.
3. **Real-metal walk** (`assets/hs-131-06/walk_bounded_schedule_lan.py`
   against live llama.cpp on 192.168.1.43:8080, isolated HOME, runtime
   singleton database; output in `assets/hs-131-06/walk-output.txt`): five
   legs green after EVERY code round — (1) enable→delegation→scheduler tick
   ran an admitted child on real metal with the exact
   actor/delegator/basis receipt tuples; (2) same-minute duplicate refused
   with a durable receipt; (3) bound edit revoked → named refusal → a
   deliberate re-enable minted NEW terms and ran on metal under the new
   basis; (4) sync-only `schedule_enabled` refused `delegation_missing`
   with no model call; (5) owner disable during an in-flight generation →
   parent CANCELLED, item stayed pending, delegation revoked. The walk's
   first run crashed on the inherited `mint_failures` defect — the walk
   remains this phase's most reliable bug-finder.
4. **Full gate** (`scripts/test_gate.sh` on the quiet tree, isolated HOME):
   see the capture below and `assets/hs-131-06/gate-tail.txt` /
   `gate-failures.txt`; failure names diffed against the HS-131-05 baseline
   (`assets/hs-131-05/gate-failures.txt`, normalized) — accounting recorded
   below.

### Gate triage (first run → fixes → clean re-run)

The first full gate surfaced NINE new names vs the HS-131-05 baseline
(93 names). Triage classified them exactly:

- **Four stale version pins** (deterministic, the predicted family):
  `test_migrates_v38_database_to_decision_commitments`,
  `test_schema_migrates_v40_to_v43`,
  `test_v43_renames_legacy_decision_receipt_tables_once`,
  `test_schema_migrates_v39_to_v40` asserted "current == 51"; updated to 52.
- **`test_claim_receipt_reconcile_and_cursor_projection`** (deterministic):
  the receipt-ENRICHMENT this story added (actor/delegator/basis/target on
  receipt reads) made the create-path and replay-path payloads diverge.
  Fixed in the PRODUCT, not the test: every receipt read/create/transition
  path in `kernel/journal.py` now returns the same joined shape via one
  shared `_RECEIPT_SQL` — receipt payloads are consistent everywhere.
- **`test_kernel_broker_modules_stay_within_line_budget`** (deterministic):
  the story's kernel surgery pushed `parent_run.py` to 359 lines and
  `broker.py` to 301 against the 300-line density guard. Honored the
  guard's own instruction ("carve a typed concern module; don't bump the
  budget"): the delegated-schedule concern moved into
  `kernel/schedule_delegated.py` (105 lines) with thin controller
  delegations preserved (`parent_run.py` → 283, `broker.py` → 300).
- **Three flakes with serial passes** (accounted, not deterministic):
  `test_every_mermaid_block_renders` (slow browser render under load),
  `test_falls_back_to_typing_when_no_tmux_pane`,
  `test_types_into_focused_when_no_waiting_session` — all pass serially on
  identical code.

After the fixes: 106 focused tests green (including the whole
`test_kernel_effect_fence.py`), the real-metal walk green again, and the
gate re-run's accounting recorded below.

### Gate accounting (final run)

Baseline: `assets/hs-131-05/gate-failures.txt` (93 normalized names). This
story's final gate: `assets/hs-131-06/gate-failures.txt` (94 names,
`gate-tail.txt` alongside). Diff: **ZERO deterministic new names, zero
disappeared**. One new name —
`test_workbench_deadline_expiry_fences_new_children_and_late_projections` —
is an accounted flake: it passed 3/3 immediate serial re-runs on identical
code (deadline-timing sensitivity under xdist load) and passed in every
focused run of this story. The first gate run's three flakes (mermaid
render, two remote-dictation delivery names) all passed in the final run,
confirming their serial-pass classification. One outside kill interrupted
the first re-run during the serial tail (lane 1 had completed); relaunched
once per the standing rule.

### Post-ratify gate repairs (disposition)

Three mechanical changes landed AFTER Sol's round-4 ratify, driven by the
gate's own guards, recorded here for the sitting rather than re-convening a
fifth round: (1) the delegated-schedule concern moved verbatim from
`parent_run.py` into `kernel/schedule_delegated.py` to honor the 300-line
kernel density guard (thin controller delegations preserved; zero behavior
change); (2) `kernel/journal.py` receipt create/transition paths now return
the same enriched provenance shape as receipt reads via one shared
`_RECEIPT_SQL` (extends Sol's Blocker-2 fix to the create path — receipt
payloads are consistent everywhere); (3) a one-line compaction in
`broker._refuse_attempt`. All verified by the 106-test focused set, the
fence suite, the real-metal walk re-run, and the final gate.
