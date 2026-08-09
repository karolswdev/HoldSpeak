# HS-130-08 — DecisionReceipt → Decision: the word returns to evidence

- **Project:** holdspeak
- **Phase:** 130
- **Status:** done
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

"Receipt" is reserved by the Constitution (Article XI) and the kernel journal
(kernel/journal.py:258-276) for **immutable** evidence of what ran — one
insert-once row per operation. `DecisionReceiptService` stores the opposite: a
**mutable governing document** with `rationale/alternatives/owner/review_date`
in `_EDITABLE_FIELDS` (decision_receipt_service.py:14-16), `update_receipt()`
with a revision trail (:132-181), `supersede()` flipping lifecycle (:263-301),
`due_for_review()` (:338). Shipping honest kernel receipts (this phase) while
"Receipt" simultaneously names an editable document is exactly the confusion
the owner is complaining about. **Rename the word now.** Blast radius measured:
12 backend files, 1 web file, 4 tables, 4 sync kinds.

### What changes

1. `DecisionReceipt*` → `Decision*` across the service, schema tables, sync
   kinds, API routes, and the one web surface. "Receipt" is left meaning only
   immutable kernel evidence.
2. One schema/sync migration renames the tables and the four sync kinds;
   `TestKindSetCannotDrift` (test_primitive_contract.py) is updated in lockstep
   so the kind-set stays coherent (note: this is one of the tests in the
   inherited-96 ledger — HS-130-10 accounts for it).
3. The user-visible "Receipts" surface Phase 127 shipped is renamed to
   "Decisions"; the Intelligence pullout's Receipts view (Phase 128) that
   shows **kernel** receipts keeps its name — the two were conflated by the
   shared word and now read as distinct things.
4. **The word only.** The model convergence — Decision links to immutable
   receipts for create/accept/change/supersede — is **deferred to Phase 133**
   with an owner beat.

## Acceptance criteria

1. No product code names the mutable governing document "Receipt"; "Receipt"
   in code and UI means immutable kernel evidence only.
2. The rename is behavior-preserving: create/edit/supersede/review flows work
   unchanged under the new name; the migration runs once and is idempotent.
3. The sync kind-set is coherent after the rename (kind-drift test green).
4. No new links between Decision and kernel receipts are added (that is 133);
   this story does not touch the receipt lifecycle.

## Test plan

- Backend: rename regression across the service's existing tests; one-shot
  migration test; kind-drift test green; a grep asserting no `DecisionReceipt`
  identifier survives outside a compatibility alias at the migration boundary.
- Web: the renamed surface renders; typecheck.
- Full backend suite + web tests read from file before flip.

## Out of scope

- Decision↔Receipt model convergence, lineage, and lifecycle linking (Phase
  133).
- Merging Decision with any other surface.
