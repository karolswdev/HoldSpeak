# HS-127-05 — Affected-work links

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** HS-127-04
- **Unblocks:** HS-127-06
- **Owner:** unassigned

## The thesis (the bar)

A receipt explains the work it changed, and the work explains the receipt
that authorized its direction. Links must be typed, bidirectional, and
openable rather than a free-text project mention.

### What changes

1. Link receipts to projects, workbench items, action items, meetings, and
   artifacts through `decision_receipt_work`.
2. Project receipt links back into each affected object's existing face.
3. Preserve link type, label, and stable target reference.
4. Reject dangling or duplicate links while allowing many affected objects.

## Acceptance criteria

1. Each supported work kind can link to and from a receipt.
2. Links are visible from the receipt and the affected work object.
3. Removing a link preserves the receipt, work object, and audit history.
4. Missing targets fail by name instead of creating an opaque reference.

## Test plan

- Repository: create, deduplicate, list, and remove typed work links.
- Integration: navigate receipt → work and work → receipt for every kind.
- Regression: delete an attempted link target and assert an honest failure.
