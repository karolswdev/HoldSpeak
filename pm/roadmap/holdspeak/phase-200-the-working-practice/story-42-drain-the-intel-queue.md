# HS-200-42: Make a finished meeting actually produce intelligence

- **Project:** holdspeak
- **Phase:** 200
- **Status:** ready
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

- [ ] A meeting stopped on a running hub produces an intel snapshot with no CLI
      command and no manual route call, and the job leaves the queue.
- [ ] The drainer starts inside the hub lifespan and is stopped with the others;
      a second hub cannot run a second drainer against the same database.
- [ ] `Run intelligence` on the face either runs it or names honestly what it
      queued and when that will execute. A verb that returns `queued` while
      nothing drains the queue is the defect, not the fix.
- [ ] Retry, backoff and the attempt ceiling are exercised against a failing job,
      and a permanently failing job lands in a state the face can show.
- [ ] Quiet hours and the owner's `intelligence_auto` setting are respected by
      the drainer, not bypassed by it.
- [ ] A fence test fails against the pre-fix tree: prove the drainer is called by
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
