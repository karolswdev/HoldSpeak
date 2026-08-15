# Evidence - HS-131-03

- **Story:** HS-131-03 - Ask and Agents take the same door
- **Status:** done
- **Date:** 2026-08-10

## Proof

### Captured run — 2026-08-10T07:10:28Z

- **Command:** `sh -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_web_routes_ask.py tests/unit/test_web_routes_recipe_chat.py tests/unit/test_run_artifacts.py tests/unit/test_run_frames.py tests/unit/test_projection_stager.py tests/unit/test_ask_runner_migration.py tests/unit/test_recipe_runner_migration.py tests/unit/test_projection_schema.py tests/unit/test_hs13103_remaining_obligations.py tests/unit/test_intel_cloud.py tests/unit/test_web_routes_primitives.py -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 05b0fc40fe53fe5a2f240370cbf8a7e2171cdb31

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 16.25s
```

## The design beat, and what it bought

First story built under ORCHESTRATION §2b: the ProjectionStager design
was drafted and Sol-ruled BEFORE implementation
([DESIGN-HS-131-03](./DESIGN-HS-131-03.md) — eight amendment groups
resolved on paper in one round, then three implementation review rounds
to "ratify with named reservations"). Contrast: HS-131-02's identical
review depth took fourteen rounds post-hoc.

## What shipped

- **ProjectionStager** (schema v46): the durable protocol closing the
  crash window between a caller's domain write and the runner's terminal
  receipt — stage commit → terminal receipt with stage reference →
  idempotent BEGIN IMMEDIATE finalization; startup/periodic recovery
  gated on the liveness reaper (which now RUNS in production, partially
  discharging the HS-131-02 reservation); mechanical bypass fence
  (identity-checked transaction-bound permits, AST fences, forged-permit
  refusal).
- **Ask through the door**: `holdspeak.ask@1` versioned contract,
  canonical payload hash, admitted `inference.invoke`, staged
  `ask_results` projection, one shared typed outcome mapper, in-flow
  refusals, no-retarget preserved.
- **Recipe run + chat through the door**: SavedDefinition with the exact
  persisted revision (`persona:`/fallback revisions gone; RunLifecycle
  removed from recipe_service), staged Artifact/chat projections, chat
  turns as authenticated root invocations (trusted-parent positive path
  deferred to HS-131-04/05 — Sol-accepted).
- **Cancellation across request lifetimes**: the runner is broker-owned
  (one per configured runtime), so a cancel arriving on a different HTTP
  request reaches the live invocation; principal via the kernel
  `_as_principal` context, fail-closed; cancel routes on Ask and Recipe.
- **Event-loop repair**: the migration had made runner dispatch block
  the async loop — caught by the full gate, fixed with
  `asyncio.to_thread` around dispatch.

## Defects the verification layers caught (each fixed + regression-tested)

1. Broker/database identity mismatch → `inference_deployment_revision_unknown`
   on real metal (caught by the LAN walk; unit tests had pre-seeded state).
2. Fresh-runner-per-cancel → "pending" for live invocations (caught by the
   choreographed proof).
3. Per-service runner vs per-request route construction → same defect one
   layer up (caught by Sol's review; fixed broker-owned; cross-instance
   proof added).
4. Event-loop blocking (caught by the full gate's `engine_off_the_loop`).

## Full-suite regression accounting (two-lane gate, armed with signal timeouts)

Lane 1 (parallel): 75 failed — new names ONLY the six `test_intel_cloud`
tests, which pass 11/11 serially and at the charter baseline; they are
parallel-contention flakes newly EXPOSED because the meeting extra
(openai) was absent from the baseline venv (they skipped before). Moved
to the gate's serial tail; de-flaking is remediation work. Lane 2
(serial): 7 failed + 17 errors, all in the known inherited set.
**REPAIRED: `tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged`.**
Zero unaccounted new names. Artifacts: `assets/hs-131-03/gate-failures.txt`.

## Real-model walk (live LAN metal)

`assets/hs-131-03/walk_ask_agent_lan.py` against llama.cpp on
192.168.1.43 (output in `walk-output.txt`): Ask → one admitted
invocation, succeeded receipt, exactly one finalized `ask_results` row;
saved Agent run → second invocation family, one `recipe_results` row;
profile mutated to a bogus endpoint afterward → named refusal with the
true upstream reason ("Destination 'LAN .43 (mutated)' refused the run:
Cloud server error (502) … ECONNREFUSED"), no phantom rows.

## Sitting-visible items

- Sol's five named design-floor reservations (migrated-service raising
  spies, stage-closure exhaustion, expired-stage reap-through-discard,
  exhaustive non-success recovery, wrong-receipt-linkage negatives).
- ⚠️ Incident: a subagent ran `scripts/gen_api_surface.py` without an
  isolated HOME and migrated the owner's REAL database v43→v46; backup
  at `~/.local/share/holdspeak/holdspeak.db.20260809-233406.bak`;
  surfaced to the owner (restore if running main's hub before Phase 131
  merges). Prevention: isolated HOME for ALL scripts, now standing rule.
- A nondeterministic lane-1 hang (Condition.wait stack) surfaced twice
  and is now bounded by the gate's signal-method timeouts; the two
  timeout-marked tests fall within the known inherited set.
