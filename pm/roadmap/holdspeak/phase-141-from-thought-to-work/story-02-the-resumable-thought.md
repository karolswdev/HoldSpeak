# HS-141-02 — The resumable thought

- **Status:** backlog
- **Depends on:** 141-01
- **Unblocks:** 141-03…09

## Problem

The aggregate must survive every ordinary interruption without turning into a
new chat subsystem or losing which question, attachment set, or result belongs
to which working revision.

## Scope

Add the service/API projection for loading one thought, listing unfinished
thoughts, recording attachment revisions and known inference invocation/result
links, completing/reopening, and reconciling reload. Invocation receipts may be
durable; model output advances product state only through an accepted owner
transition.

Define the refinement-owned Ask correlation contract: caller-stable request ID,
thought/working/context revisions, Ask invocation ID, kernel operation identity,
persisted review-result identity, and terminal/reconciliation state. Do not rely
on AskPanel component state or the current internal random Ask ID alone.

## Acceptance

- [ ] Every nonterminal state round-trips across hub/browser restart.
- [ ] A known completed invocation may reconcile to a persisted review result;
  an unknown/unpersisted answer never resurrects as fact.
- [ ] Correlation is durable before dispatch and uniquely links the exact frozen
  revisions, Ask invocation, kernel operation, and persisted review result.
- [ ] Unfinished list is bounded, owner-readable, and revision honest.
- [ ] Stale/deleted refs and working-note tombstones refuse by name.
- [ ] DTOs never contain secrets or hidden hydrated context material.

## Tests

Focused service/route/restart matrix; stale invocation/result/ref legs; bounded
list and DTO privacy assertions.
