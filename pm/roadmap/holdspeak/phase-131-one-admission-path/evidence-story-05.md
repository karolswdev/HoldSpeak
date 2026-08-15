# Evidence - HS-131-05

- **Story:** HS-131-05 - Workbench work and memory cannot outrun cancellation
- **Status:** done
- **Date:** 2026-08-10

## Proof

### Captured run — 2026-08-10T16:07:46Z

- **Command:** `env HOME=/tmp/hs13105-ev sh -c mkdir -p /tmp/hs13105-ev && uv run pytest -q tests/unit/test_workbench_runner_migration.py tests/unit/test_sequence_workflow_runner_migration.py tests/unit/test_web_routes_primitives.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b5e5a5db477c5ae01e944096a042f407b8b17ae1

```text
........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 15.41s
```

## Verification narrative (orchestrator)

**Design beat.** Terra drafted `DESIGN-HS-131-05.md`; Sol ruled RATIFIED
WITH AMENDMENTS in ONE round under the owner's 2026-08-10 yolo-mode
rigor bar (three amendments: register `workbench.run@1` through the
parent platform; the frozen deadline is an epoch-changing execution
fence; the history row finalizes only on the winning parent receipt).
Committed before implementation.

**Implementation.** One implementation Terra on the HS-131-04 platform
(schema v50 receipt/child-link columns, v51 truthful cancelled/
indeterminate status), then verification-driven fix rounds. The
real-metal walk and the substantive test rewrite each caught REAL
pre-existing/introduced defects, all fixed with regression tests:

1. Cancel-race close: cross-request cancellation invalidated the held
   context and the runner's close paths threw raw KernelRefused,
   masking outcomes and stranding history rows at 'running'. Fixed with
   receipt-winner adoption in both the workbench runner AND the
   Sequence/Workflow service (same latent hole).
2. Memory-child payload-hash mismatch: the ServiceContract hashed a
   different payload than the request carried — EVERY real memory
   writeback refused on metal. The original matrix test was vacuous
   and missed it; the rewritten suite pins it.
3. `runtime._configure` rebuilt the broker unconditionally while the
   chains/workflows routes call it per request — any concurrent run
   destroyed every in-flight parent controller (cleared capability
   registry, killed lease refreshers). Now idempotent per database.
4. Deadline fence gap: a dispatch returning past the deadline could
   advance; the runner now expires through the epoch-changing cancel
   path before finalize.
5. Cancel disposition understated the truth ("pending" while the
   cancelled receipt already existed); now returns the elected outcome.

**Counsel ledger (two Sol implementation rounds).**
1. Review: DO NOT RATIFY — three blockers (memory child reused the
   item's deployment instead of per-child placement; replay returned an
   invented run_id without the receipt; the ruled stage-vs-cancel
   election proof was substituted with a weaker one).
2. Confirmation: **RATIFY FOR STORY CLOSE** — all three discharged,
   no new defects.

**Real-metal walk** (`assets/hs-131-05/walk_workbench_lan.py` against
llama.cpp on 192.168.1.43:8080; output in `walk-output.txt`): leg 1 —
two items → one `workbench.run` parent, two item children + two
DISTINCT memory children, all receipts terminal, two receipt-gated
memory observations, history row bound to the parent receipt; leg 2 —
memory disabled → zero memory children; leg 3 — mid-run cancel →
structured `terminal_disposition=cancelled`, parent CANCELLED, item
unfinished, no memory, child receipt retained.

**Gate accounting** (`assets/hs-131-05/gate-tail.txt`; baseline copied
forward in `assets/hs-131-05/gate-failures.txt`, 93 names):
`8 failed, 237 passed, 36 skipped, 16 deselected, 17 errors` — zero
DETERMINISTIC new failure names vs the HS-131-04 baseline. Two
accounted run-to-run tail flakes under gate load, both passing serially
and each appearing in only one of two gate runs on identical code:
`test_delivery_campaign` (2 tests, run 1 only; 3× clean parallel
probes) and `test_mesh_dispatch::test_run_dispatched_onto_the_worker_returns_badged`
(run 2 only; serial pass 52s). Six migration-chain names in run 1 were
stale v49 assertions in tests (migrations themselves correct for
v50/v51); one HS-131-03 obligation test now simulates restart with a
fresh Database instance to respect the ratified `_configure`
idempotency.

**Sol's reservation riding to the owner's sitting:** provider
cancellation signaling after the durable fence is best-effort (daemon
thread); process exit can lose the signal and upstream work runs to its
own timeout — the epoch fence blocks its late writes; resource-cleanup
only. Recorded note: the fixture-backed e2e workbench walk test skips
without `HOLDSPEAK_WORKBENCH_WALK_FIXTURE`; the real-metal walk covers
that seam.
