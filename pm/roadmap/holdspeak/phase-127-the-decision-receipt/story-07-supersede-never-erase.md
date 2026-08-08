# HS-127-07 — Supersede, never erase

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** HS-127-06
- **Unblocks:** HS-127-08
- **Owner:** unassigned

## The thesis (the bar)

A changed decision must not destroy the reason the earlier choice was made.
Supersession seals the predecessor, names the successor and reason, and
preserves both evidence chains for future inspection.

### What changes

1. Add receipt-level supersession through `DecisionLifecycleService` lineage.
2. Seal the predecessor and record successor identity, reason, and time.
3. Retain predecessor sources, revisions, work links, and lifecycle facts.
4. Prevent edits that rewrite a sealed choice as if it were current.

## Acceptance criteria

1. Superseding creates a successor and a two-way, navigable lineage.
2. The predecessor remains readable with all evidence and revisions intact.
3. The successor names why it replaces the predecessor.
4. Invalid self-links, cycles, and destructive replacement are refused by name.

## Test plan

- Service: supersede a receipt and retrieve both directions of lineage.
- Service: attempt self-link and cycle mutations and assert named refusals.
- Integration: open predecessor evidence after its successor is current.
