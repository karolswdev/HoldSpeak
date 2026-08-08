# HS-127-02 — Unify decision origins

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** HS-127-01
- **Unblocks:** HS-127-03, HS-127-04
- **Owner:** unassigned

## The thesis (the bar)

Meeting-derived and desk-authored decisions are both real origins. A receipt
must bridge either origin without migrating, duplicating, or replacing its
canonical source record.

### What changes

1. Add `DecisionReceiptService.create_from_meeting()` for `decisions`.
2. Add `.create_from_desk()` for `desk_decisions`.
3. Map each origin's available facts into the required receipt contract.
4. Make creation idempotent per source decision and retain the source link.

## Acceptance criteria

1. A receipt can be minted from either existing decision family.
2. Source records remain authoritative and unchanged by receipt creation.
3. Repeating creation for one source returns the existing receipt.
4. Missing origin facts are named for author completion, never invented.

## Test plan

- Service: mint and retrieve receipts from meeting and desk decisions.
- Service: call each origin method twice and assert one receipt identity.
- Regression: assert source rows are byte-for-byte unchanged after minting.
