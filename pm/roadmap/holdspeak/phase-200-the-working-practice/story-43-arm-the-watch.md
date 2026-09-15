# HS-200-43: Let a watch become schedulable, and let a manual evaluation count

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-42
- **Unblocks:** HS-200-13, HS-200-15, HS-200-16, HS-200-23
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** the 2026-09-13 operational-surface audit §3.2-3.3 (`docs/internal/OPERATIONAL-SURFACE-AUDIT.md`)

## Problem

**A watch can only become schedulable inside the function that only runs on
already-schedulable watches.**

`list_due_watches` requires `next_evaluation_at IS NOT NULL`
(`holdspeak/db/automations.py:451`). Every write of that column in the package is
`holdspeak/services/watch_service.py:922` and `:1009` — **both inside
`evaluate_due`** (which begins at `:850`). No creation path passes it: the Door
(`project_door_service.py:322`) and the Interview (`project_setup_service.py:750`)
set only `baseline_state="pending"`, and `baseline_watch` (`watch_service.py:573`)
sets only `baseline_state`.

**So a watch that has never been evaluated by the scheduler can never be selected
by the scheduler.** The owner's desk: **32 watches, 30 enabled, 2 armed.**

**And a manual evaluation cannot substitute**, because
`_match_and_record_effects` (`watch_service.py:958`) has exactly one caller —
inside `evaluate_due`. The MCP tool `project.watch.evaluate` therefore runs, and
records no effects, and can never reach the steward. `watch_effects` on his desk:
**0**.

Downstream, everything unattended in the Project Rooms arc depends on this:
steward `run_due` (`workbench_conductor.py:632`) waits on watches that never
arm, and all nine of his steward policies have `unattended_enabled=0`.

## Scope

Arm a watch at the moment it is created or enabled, backfill the watches already
on disk, and make a manual evaluation record its effects like a scheduled one.

Implementation seams: `holdspeak/services/watch_service.py` (creation, enable,
baseline, `evaluate_due`, `_match_and_record_effects`);
`holdspeak/db/automations.py`; the Door and Interview creation paths;
`holdspeak/db/reconcile.py` for the backfill.

Out: changing the cadence model, the circuit breaker, or the effect vocabulary.
Out: turning unattended execution ON for the owner — the policies stay his.

## Acceptance criteria

- [x] A watch created through the Door and a watch created through the Interview
      are both selectable by `list_due_watches` without a prior manual run.
- [x] Enabling a previously disabled watch arms it; disabling does not leave a
      row that the scheduler will pick up anyway.
- [x] Watches already on disk are backfilled, and the backfill is proven wired by
      driving the real reconcile entry point — not the helper (HS-200-10's B3
      lesson: the helper shipped built, tested and uncalled).
- [x] A manual `project.watch.evaluate` records effects exactly as a scheduled
      evaluation does, and the steward can act on them.
- [x] Arming respects the paused and retired states; a tombstoned watch is not
      resurrected by the backfill.
- [x] The double-scheduler question is settled: both `workbench_conductor` and
      `heartbeat_service` call `evaluate_due`, and **only the heartbeat checks
      quiet hours** (`heartbeat_service.py:318`). Either the conductor honours
      quiet hours or the promise is corrected. Name the ruling in the evidence.
- [x] Every new fence proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_watch_arming`. Create through the real Door and real
Interview services, then assert selection through the real
`list_due_watches`. Backfill proven through `reconcile_schema`.

## Notes / open questions

The audit's §3.2 and §3.3. Note the related inherited defect found in Phase 166:
`older_than`/`newer_than` returned False unconditionally, so at least one shipped
watch had never matched. Confirm it stays fixed once watches actually run.

## Built (2026-09-14) — the rulings, and what counsel found under them

**Rulings (orchestrator, on the owner's standing deferral; research lane verified
each premise at file:line before the ruling):**
- **R1 The heartbeat is the single scheduler.** Both `workbench_conductor` (every
  60 s, no quiet-hours check, no `owns_database` gate, app-wired service) and the
  heartbeat (every `sweep_every_minutes`, quiet-hours and ownership gated, but a
  BARE `WatchService`) called `evaluate_due`; the conductor always won, so quiet
  hours never actually held evaluation and a hub that lost its claim still
  evaluated. The conductor's watch block is deleted (its steward block stays);
  the heartbeat prefers the app-wired service via `get_scheduler_services()` with
  a logged bare fallback (the real loss in the fallback is the Jira adapter's acli
  runner, not the fetcher — corrected after counsel F4). Source fence: the
  conductor module no longer calls `evaluate_due` (a regex; it would not see a
  `getattr` — said out loud here).
- **R2 Quiet hours hold the whole sweep**, evaluation included; 171's settled
  design and ARCHITECTURE/USER_GUIDE now say one sentence. **The owner's hand
  overrides**: Run now (Settings, MCP `heartbeat.run_now`) passes `owner_hand=True`
  — unbounded and not held; the receipt records `quiet_overridden`. The steward
  triggers never touched `run_sweep`, so they carry only the unbounded limit.
- **R3 Arm to `now`, always.** The first version armed `now + cadence` when no
  snapshot existed, keyed on `snapshot_json` (never `baseline_state`, which the
  Door writes `established` at INSERT before any snapshot). Counsel proved the
  cadence branch protected nothing — see the P0 below — and it is gone.
- **R4 The backfill is ungated**, in reconcile step 2 beside HS-200-10's, in its
  own SAVEPOINT: `_apply_data_backfills` runs only under `if shape_changed:` and
  never fires on an up-to-date desk, so a backfill placed there would have shipped
  dead — the B3 lesson a second time.
- **R5 Manual evaluation records effects** through `_record_effects_if_any`,
  extracted from `evaluate_due`'s guard and called by `evaluate_once` too; the
  key is derived from the evaluation, so manual + scheduled mint exactly one.
  `evaluate_once` also leaked the internal `_transitions` dict over HTTP and
  MCP; stripped.
- **The unattended sweep is bounded** (`WATCH_SWEEP_MAX = 10`, oldest-due first,
  `watches_deferred` on the receipt); `list_due_watches` gained a total order
  (`next_evaluation_at, id`) because arming puts many rows on one instant.

**Counsel's P0, reproduced and paid.** Arming an unbaselined watch an hour out
does not prevent it discovering its entire source as new — it delays it:
`_evaluate_core` diffs against `snapshot or {}` and `baseline_state` is never read
by evaluation. Counsel's repro: one `pending`/NULL-snapshot row plus one
`older_than` rule → 30 transitions, 30 observations, 1 effect. Now the first
evaluation of ANY watch with an empty baseline is silent by construction in
`_evaluate_core`: the fetched snapshot is persisted as the baseline (through
`_persist_baseline`, which `baseline_watch` now shares), `baseline_state` set,
outcome `baselined`, zero transitions, no evaluation row, cadence advanced; the
receipt counts `watches_baselined` apart from `watches`. Same repro: 0. On the
owner's desk the ~30 backfilled rows baseline over three sweeps, ~45 minutes,
every one silent. (Counsel's premise that meeting watches are never baselined
was wrong — `ensure_meeting_watch` baselines inline, in a swallowed try/except
that never sets `baseline_state`; both the happy and the swallowed-failure paths
are fenced.)

**Fences:** 39 in `tests/unit/test_phase200_watch_arming.py`; the Door and
Interview legs drive the real services, selection the real `list_due_watches`,
the backfill the real `reconcile_schema`, the owner's-hand legs the real MCP
dispatch AND the real HTTP routes. Every fence on new behaviour was proven to
fail on a surgical pre-fix tree (four of them, one per ruling round, left under
the scratchpad). Counsel: RATIFY-WITH-CONDITIONS → RATIFY on re-read.

**Parked (BACKLOG.md):** the chosen cadence preset never reaches
`evaluation_cadence_minutes` (every watch runs hourly whatever he picked); the
sweep's 40-evaluations-an-hour ceiling has no face.

**Not verified:** on the owner's real desk — the 30-enabled/2-armed gap closing
on his next open is an inference from the backfill's WHERE clause, not a
measurement.

