# HS-127-06 — Review queue

- **Project:** holdspeak
- **Phase:** 127
- **Status:** backlog
- **Depends on:** HS-127-05
- **Unblocks:** HS-127-07
- **Owner:** unassigned

## The thesis (the bar)

A review date is a promise only if the desk can surface it. The receipt
service must return due and overdue decisions as evidence-backed attention,
not another orphaned list.

### What changes

1. Add `DecisionReceiptService.due_for_review()` with explicit time semantics.
2. Classify due, overdue, superseded, and closed receipt states honestly.
3. Project actionable receipts into existing attention surfaces.
4. Link queue entries to the receipt, its owner, evidence, and affected work.

## Acceptance criteria

1. Due and overdue open receipts appear in deterministic priority order.
2. Superseded or closed receipts do not create false review attention.
3. Empty queues state no due reviews without generated filler.
4. Queue rows open the receipt and retain their source evidence.

## Test plan

- Service: test due, overdue, future, closed, and superseded boundaries.
- Projection: assert attention entries carry receipt identity and open target.
- Integration: resolve a review and assert it leaves the actionable queue.
