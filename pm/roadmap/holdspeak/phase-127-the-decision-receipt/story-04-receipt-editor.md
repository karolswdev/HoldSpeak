# HS-127-04 — Receipt editor

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** HS-127-02, HS-127-03
- **Unblocks:** HS-127-05
- **Owner:** unassigned

## The thesis (the bar)

The desk decision primitive is where a human completes a choice. It must
expose receipt facts in-world and make “accept as receipt” a deliberate,
auditable action rather than a hidden conversion.

### What changes

1. Extend the desk decision primitive with owner, alternatives, rationale,
   review date, and receipt acceptance.
2. Present source evidence and the resulting receipt in the existing desk
   grammar, with no modal flow.
3. Route edits through append-only receipt revisions.
4. Show the current receipt state and revision lineage to the editor.

## Acceptance criteria

1. The editor captures every required receipt field before acceptance.
2. Accepting a decision creates or opens its source-linked receipt.
3. Editing a receipt creates a new revision and preserves earlier content.
4. The editor presents exact source evidence when it is available.

## Test plan

- Component: render, validate, and accept all required fields in-world.
- Service: edit a receipt twice and assert append-only revisions.
- Integration: accept a desk decision and reopen its source-linked receipt.
