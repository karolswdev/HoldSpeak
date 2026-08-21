# HS-141-02 — The resumable thought

- **Status:** done
- **Depends on:** 141-01
- **Unblocks:** 141-03…09

## Problem

The aggregate must survive every ordinary interruption without turning into a
new chat subsystem or losing which question, attachment set, or result belongs
to which working revision.

## Scope

Add the service/API projection for loading one thought, listing unfinished
thoughts, carrying the attachment cursor/link, recording known inference
invocation/result links, and reconciling reload. This story carries no concrete
attachment rows (Story 05 owns them) and projects lifecycle state only; the
owner-facing complete/reopen decision belongs to Story 06. Invocation receipts
may be durable; model output advances product state only through an accepted
owner transition.

Define the refinement-owned Ask correlation contract: caller-stable request ID,
thought/working/context revisions, Ask invocation ID, kernel operation identity,
persisted review-result identity, and terminal/reconciliation state. Do not rely
on AskPanel component state or the current internal random Ask ID alone.

## Acceptance

- [x] Every nonterminal state round-trips across hub/browser restart.
- [x] A known completed invocation may reconcile to a persisted review result;
  an unknown/unpersisted answer never resurrects as fact.
- [x] Correlation is durable before dispatch and uniquely links the exact frozen
  revisions, logical invocation, each physical Ask attempt/kernel operation,
  and the single persisted review result.
- [x] Unfinished list is bounded, owner-readable, and revision honest.
- [x] Stale/deleted refs and working-note tombstones refuse by name.
- [x] DTOs never contain secrets or hidden hydrated context material.

## Tests

Focused service/route/restart matrix; base/follow-up/orphaned attempt and stale
invocation/result/ref legs; bounded/private list assertions; hub-local
continuity exclusion from paired sync.
