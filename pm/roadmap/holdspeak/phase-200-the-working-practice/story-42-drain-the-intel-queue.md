# HS-200-42: Make a finished meeting actually produce intelligence

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-07
- **Unblocks:** HS-200-12, HS-200-13, HS-200-16, HS-200-23
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** the 2026-09-13 operational-surface audit §3.1 (`docs/internal/OPERATIONAL-SURFACE-AUDIT.md`)

## Problem

**Nothing in the running product drains the intel queue.** A stopped meeting
writes an `intel_jobs` row (`holdspeak/runtime/routing_glue.py:324`) and the row
is never executed.

- `IntelQueueWorker` (`holdspeak/intel_queue.py:677`) and
  `start_intel_queue_worker` (`:874`) — a complete polling worker with backoff,
  retry ceilings and alerting — have **zero production callers**. Every reference
  is the module itself, a test, or `scripts/phase107_closeout_beats.py`.
- `drain_intel_queue` has exactly two production callers:
  `holdspeak/commands/intel.py:110` (the CLI) and
  `holdspeak/services/meeting_intel_service.py:37`, reached only by
  `POST /api/intel/process` — and **no face calls that route**
  (`grep -rn "intel/process" web/src` → 0).
- The face's `Run intelligence` verb does not run intelligence:
  `MeetingIntelService.run_intelligence` (`meeting_intel_service.py:55`) calls
  `request_intel_retry` and returns `{"state": "queued"}`.

The hub's lifespan starts three conductors — workbench, scheduled recording,
calendar ingest (`holdspeak/web_server.py:1222-1268`) — and not this one.

**Where it entered.** Phase 172's settled design asserted the opposite:
*"The deferred queue worker (`intel_queue.py:592`, `IntelQueueWorker`) already
picks up queued jobs. No new worker needed; the existing
`_deferred_plugin_queue_loop` processes them"*
(`../phase-172-the-loop-closes/assets/settled-design-loop-closes.md:317-320`).
That loop calls `process_next_plugin_run_job`
(`holdspeak/runtime/plugin_queue.py:80`) — **a different queue.**

**The owner's desk, 2026-09-13:** `intel_snapshots` **0**; one job `queued`
since 2026-09-10; one meeting session ever recorded, and it was cancelled. The
product's headline flow has never completed once on his machine.

## Scope

Give the intel queue a production drainer inside the hub's own lifespan, under
the same start/stop discipline HS-200-03 imposed on every other conductor, and
make the face's `Run intelligence` verb mean what it says.

Implementation seams: `holdspeak/web_server.py` lifespan; `holdspeak/intel_queue.py`;
`holdspeak/services/meeting_intel_service.py`; the meeting face's intelligence verb.

Out: changing the intel pipeline itself, the model routing, or the snapshot
schema. Out: auto-enqueue policy (`intelligence_auto` stays the owner's setting).

## Acceptance criteria

- [x] A meeting stopped on a running hub produces an intel snapshot with no CLI
      command and no manual route call, and the job leaves the queue.
- [x] The drainer starts inside the hub lifespan and is stopped with the others;
      a second hub cannot run a second drainer against the same database.
- [x] `Run intelligence` on the face either runs it or names honestly what it
      queued and when that will execute. A verb that returns `queued` while
      nothing drains the queue is the defect, not the fix.
- [x] Retry, backoff and the attempt ceiling are exercised against a failing job,
      and a permanently failing job lands in a state the face can show.
- [x] Quiet hours and the owner's `intelligence_auto` setting are respected by
      the drainer, not bypassed by it.
- [x] A fence test fails against the pre-fix tree: prove the drainer is called by
      driving the real lifespan, not by calling the helper.

## Test plan

Planned suite: `phase200_intel_drain`. Drive the real hub lifespan for the
start/stop proof. The `reference_lying_test_doubles` law applies in full: mint
through the real producer, assert against the real validator, and prove every new
fence FAILS pre-fix.

## Notes / open questions

The audit's §3.1 is the evidence. This story is not a canon debt and not a zero
census — it is the product's headline flow failing on the owner's own desk, and
the zero census is its symptom rather than its justification.

## Built (2026-09-14) — what shipped, what was ruled, what counsel found

**The drainer is a fourth lifespan conductor** (`holdspeak/intel_queue_conductor.py`),
started in the hub startup block after the calendar conductor and stopped in
`_shutdown` with the others (HS-200-03 discipline; the shutdown fence now requires
it). It is gated on the database owner lock: a hub started under
`HOLDSPEAK_ALLOW_UNOWNED_DB=1` starts no drainer — the three existing conductors
were never ownership-gated, so the guard was added rather than inherited. Poll
15 s plus a `wake()` the verb calls, so `Run intelligence` drains within a second
instead of a poll. `on_meeting_ready` broadcasts `aftercare_ready` and the
`runtime_queue` frame to the open browser.

**Rulings (orchestrator, on the owner's standing deferral):**
- `intelligence_auto` gates ENQUEUE only; the drainer never re-checks it — a manual
  `Run intelligence` taken while auto is `off` must still execute (counsel P2-8,
  ratified in the conductor docstring).
- Quiet hours govern NOTIFICATION, not compute. Verified: there is no
  `aftercare_ready` → desktop-notification path at all (it is a WebSocket frame
  only), so there was no gate to bypass; the test proves the drainer computes
  during quiet hours and posts nothing.
- Article III: the job row's `model_host` is restated AT EXECUTION TIME from the
  frozen deployment revision the bound job actually egresses through, written
  before the model call. The enqueue-time value (from mutable Config) is only an
  estimate, and on the walk rig the two disagreed (`local` vs `same_device`).
  Both claim-planner INSERTs now carry `model_host` onto the successor row.
- Shutdown custody: the database owner lock is released only after the conductors
  have stopped (`DatabaseOwnershipMixin._stop_writers_and_release_database`);
  the drainer join is 60 s and a still-running model call is named in the log.

**Two defects found on the way, both paid:** (1) `IntelQueueWorker._check_failure_alerts`
called `get_database().get_intel_queue_summary()`, an accessor `Database` never had
— every alert check raised and was swallowed (invisible while the worker had zero
callers; an ERROR line every 15 s the moment it ran). A lying test double had
modelled the accessor; corrected, and a regression fence added. (2) **The attempt
ceiling was unreachable with an empty routed plugin chain**: the bound-claim planner
re-froze an identical descriptor on every claim and inserted the replacement with
`attempts=0`, so a permanently failing job retried forever and grew `intel_jobs` by
two rows a cycle. Unreachable before (nothing drained); fixed at the root by not
re-freezing when descriptor and `displaced_work` are identical.

**The face.** The shot walk caught what every unit test passed: the first face
change was invisible — the receipt swapped the badge to `QUEUED` before the verb
branch could render. Paid: the badge carries the fact (`QUEUED` vs `NOT DRAINING`),
read durably from the `runtime_queue` frame (which now carries `drainer`), the
receipt is only the pre-frame window, and the verb comes back after a failed job.
Two species defects paid in the species, not the face: `SurfaceLedgerRow` rendered
its trailing verb INSIDE the row's own `<button>` (every click also opened a window
over the row; nested buttons) — the line is now `role="button"` with the trailing
slot stopping propagation; and the `1 QUEUED` chip overlapped the headline at 393.
Shots at 1440 and 393 in `assets/story-42-shots/` with DOM-read badge text per
shot in `walk-facts.md`. Web baseline: 2469 passed, zero branch-new, five HEALED.

**Counsel:** RATIFY-WITH-CONDITIONS, then RATIFY on re-read with every original
finding closed. Parked in BACKLOG.md: the 60 s join runs inside the async shutdown
hook; `egress_model_host` names leg 1 only; recovery rows supersede once; no
`busy_timeout`/WAL (HS-200-45).

**Not verified:** on the owner's real desk (isolated-HOME proof only) and against a
real provider (faked at the `MeetingIntel` seam). His hub still runs pre-42 code.

