# Evidence - HS-131-04

- **Story:** HS-131-04 - Sequence and Workflow admit every model step
- **Status:** done
- **Date:** 2026-08-10

## Proof

### Captured run — 2026-08-10T10:27:06Z

- **Command:** `env HOME=/tmp/hs13104-evidence-home sh -c mkdir -p /tmp/hs13104-evidence-home && uv run pytest -q tests/unit/test_sequence_workflow_runner_migration.py tests/unit/test_web_routes_primitives.py tests/unit/test_workflow_graph.py tests/integration/test_primitive_framework_sync.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d6809905d15776a6cc0890f109ded730d2237c46

```text
........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 18.45s
```

## Verification narrative (orchestrator)

**Design beat (ORCHESTRATION §2b).** Terra drafted `DESIGN-HS-131-04.md`;
Sol ruled it RATIFIED WITH AMENDMENTS in one round — eight binding
amendments, three open questions answered, fourteen required test-matrix
additions. Committed as `e5852e28` before any implementation.

**Implementation.** Four Terras in sequence (kernel foundation; routes/
projections/cancel/sync repair; durable CAS checkpoint seam; route-altitude
test uplift), then three orchestrator-driven fix rounds (kernel fence
defects; Sol's blocking findings; lease heartbeat + final findings) and a
gate-repair round. Schema v46 → v49 (kernel_parent_runs, kernel_parent_checkpoints,
lease columns).

**Counsel ledger (five Sol rounds).**
1. Design ruling: RATIFIED WITH AMENDMENTS (8).
2. Implementation review: DO NOT RATIFY — 8 blocking findings
   (atomicity boundary, forgeable closure, no terminal CAS/receipt
   election, lease absent, aggregate crash gaps, provenance hash split,
   vacuous proofs, walk disposition mismatch).
3. Fix round discharged most; re-review: DO NOT RATIFY narrowed to
   F4 (lease heartbeat + check-close race) plus two weak proofs and
   a kind-scoped idempotency defect.
4. Final fix round (parent_lease.py daemon refresher 10s/90s; stale-lease
   CAS re-election in the closing transaction; (kind, identity, key)
   idempotency; strengthened interleaving + real replay proofs).
5. Final confirmation: **RATIFY FOR STORY CLOSE** — all items discharged,
   no new defects.

**Real-metal walk** (`assets/hs-131-04/walk_sequence_workflow_lan.py`
against llama.cpp on 192.168.1.43:8080, output in `walk-output.txt`):
leg 1 — two-step Sequence: one `sequence.run` parent, exactly two admitted
`inference.invoke` children, all receipts succeeded, threaded output;
leg 2 — iPad-authored graph: two model children (llm, extract), pure
`keep_if` minted none; leg 3 — mid-run cancel: active child receipt
`cancelled`, no post-cancel admission, parent terminal CANCELLED via
receipt election.

**Gate accounting** (`assets/hs-131-04/gate-tail.txt`, failure baseline
copied forward in `assets/hs-131-04/gate-failures.txt`):
`7 failed, 238 passed, 35 skipped, 16 deselected, 17 errors` —
**ZERO new failure names vs the HS-131-03 baseline; SEVEN repaired**:
`test_ipad_synced_graph_workflow_runs_on_the_hub` (the seventh
HS-130-10 ledger failure, this story's chartered target) and the six
`test_intel_cloud` serial-tail flakes. One real product bug was found
by the gate's parallel lane and fixed: parent-lease daemon refreshers
leaked across broker replacement (now disposed via
`ParentRunController.shutdown()`).

**Sol's named reservations riding to the owner's sitting:**
1. Workflow execution remains finite and linear — this story added no
   retry/fallback/loop dispatch semantics (none existed to migrate:
   `retryThenQueue` is terminal, `fallbackOnDevice` is pure carry-through).
2. An indeterminate parent may truthfully retain receipt-backed partial
   checkpoints with no aggregate Artifact; presentation/resumability is
   an owner decision.
3. Two race proofs sit at controller/CAS altitude because HTTP cannot
   deterministically schedule the interleavings.

**Orchestrator disposition note for the sitting:** counsel ran five
rounds on this story. After round 3 I judged the remaining F4 items a
realistic-failure-mode product bug (any LAN generation >90s would have
been falsely closed indeterminate) rather than optional adversarial
rigor, and proceeded to the final fix round instead of pausing for an
owner ruling. The owner may re-rule the rigor bar for the remaining
phase stories.
