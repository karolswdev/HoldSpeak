# Evidence - HS-131-02

- **Story:** HS-131-02 - The admitted invocation runner
- **Status:** done
- **Date:** 2026-08-09

## Proof

### Captured run — 2026-08-10T02:53:01Z

- **Command:** `sh -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_inference_runner.py tests/unit/test_kernel_cancelled_schema.py tests/unit/test_inference_kernel.py tests/unit/test_kernel_broker.py tests/integration/test_kernel_real_hub.py tests/unit/test_deployment_revisions.py -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 226c0021dd2219c62d23ca65b9c2eeb14dea1804

```text
   Building holdspeak @ file:///Users/karol/dev/tools/HoldSpeak
      Built holdspeak @ file:///Users/karol/dev/tools/HoldSpeak
Uninstalled 1 package in 1ms
Installed 1 package in 2ms
........................................................................ [ 88%]
.........                                                                [100%]
81 passed in 24.89s
```

## The fourteen-round counsel loop

This story ran the deepest acceptance loop in the repository's history:
fourteen Sol counsel rounds, each recorded with the orchestrator's
disposition in [SOL-COUNSEL-HS-131-02](./SOL-COUNSEL-HS-131-02.md).
Final verdict (Round 14 verification): **ratify**, all twelve
ratification obligations covered, no residual reservation on the
implementation. Sitting-visible reservations Sol named as non-blocking:
`CLOSURE_FAILED` tombstones lack restart reconciliation/eviction;
`reap_expired()` is never invoked at production startup (TTL 3600 s)
and misses `awaiting_decision` stranding; a permanently hung
`adapter.cancel()` leaks one daemon thread.

## What shipped

- `inference.invoke` operation + `InferenceRunner` (kernel/
  inference_runner.py): per-invocation state machine (RUNNING /
  CANCEL_REQUESTED / CANCELLING / CANCELLED / DISPATCHING / PUBLISHING
  / PUBLISHED / CLOSURE_FAILED) under one Condition; atomic
  RUNNING→DISPATCHING dispatch right; single-performer cancellation
  election; durable-before-observable on every terminal path (bounded
  receipt retries behind `closing`; exhaustion → retained
  `ClosurePersistenceError`, never a fabricated disposition);
  BaseException-symmetric boundaries.
- `cancelled` as a first-class kernel terminal state: schema v45, both
  CHECK constraints, evidence-preserving two-table rebuild migration
  with a real-v44 migration test; web process projection updated.
- Warrant-bound `continuation_identities` (owner-only declaration);
  full-ancestor revalidation at claim in the executor plane (egress
  included); serialized journal sequence allocation; canonical payload
  hashing (allow_nan=False) verified by the runner; saved-definition
  revision resolution; cancel-child lifecycle receipts (ack→succeeded,
  completed→refused `cancel-disposition:completed`, unknown/timeout→
  indeterminate, error→failed).
- Kernel density fence honored by carving five typed concern modules
  (causation, inference_invoke, inference_cancel, inference_shared,
  journal_txn) — move-only, post-ratification, fence 12/12.

## Amendment (visible, owner may overrule at the sitting)

The durable cross-table publication-staging protocol is deferred to
HS-131-03 as its blocking acceptance criterion (one shared primitive
before the first production migration; crash-recovery tests named).
Recorded in story-02, story-03, and the phase decision log per Sol's
Round-2 terms.

## Full-suite regression diff (orchestrator-run, read before flip)

Ship-gate run on the final tree (isolated HOME, quiet tree):
**77 failed, 4792 passed, 17 errors** vs the shipped story-01 set
(78 failed, 17 errors). Name diff (`assets/hs-131-02/ship-failures.txt`):
- **NEW: none.**
- **REPAIRED: `test_decision_commitments::test_migrates_v38_database_to_decision_commitments`**
  — classified repaired-by-131-02 (the v45 migration work fixed the
  v38 chain).
- Runner focused suite: 81 tests (58 in test_inference_runner.py),
  five consecutive green runs at every round; stability proven after
  each concurrency fix.

## Real-model walk (live LAN metal)

`assets/hs-131-02/walk_runner_lan.py` against llama.cpp on
192.168.1.43:8080 (Qwen3.6-35B), output in `walk-output.txt`:
- Revision captured, then the profile mutated to a bogus endpoint —
  the admitted revision still executed the original endpoint
  (Article XI.3 proven on metal).
- One real invocation → one admitted operation, one terminal receipt,
  one causally linked `external.egress` child (all succeeded).
- Cancellation mid-generation → invocation closed `cancelled`, cancel
  child `succeeded`, late model output never published.
