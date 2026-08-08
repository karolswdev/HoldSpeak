# HS-128-06 — WHY affordance on primitives

- **Project:** holdspeak
- **Phase:** 128
- **Status:** done
- **Depends on:** HS-128-04
- **Unblocks:** HS-128-07
- **Owner:** unassigned

## The thesis (the bar)

Work should carry its reasons. A compact `WHY N` control makes governing
receipts discoverable at the primitive where their consequence is felt.

### What changes

1. Add `[WHY N]` to workbench-item, action-item, and project detail views.
2. Derive `N` from governing `DecisionReceiptService` links for that work item.
3. On click, open Intelligence directly to Receipts with the relevant WHY filter.
4. Preserve zero as an honest inactive or absent affordance per the primitive's
   existing detail grammar; do not invent a reason.

## Acceptance criteria

1. Each named primitive renders the affordance from real governing receipt links.
2. Clicking it opens filtered receipts in the existing pullout, not a modal.
3. Multiple links preserve their governing-receipt result set.
4. No link makes no fabricated rationale claim or dead navigation path.

## Test plan

- Web: render workbench, action, and project detail with zero, one, and many links.
- Interaction: click WHY and assert Receipts opens with exactly those IDs.
- Service: verify linked receipt identifiers survive primitive projection.
