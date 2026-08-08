# HS-127-03 — Exact meeting evidence

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** HS-127-02
- **Unblocks:** HS-127-04
- **Owner:** unassigned

## The thesis (the bar)

A receipt's provenance must resolve to the sentence that produced it, not a
meeting title or a plausible timestamp. The user can open the exact speaker
quote from the receipt.

### What changes

1. Persist artifact, meeting, and segment references in receipt sources.
2. Use `DecisionRepository.resolve_decision_moment()` for verified moments.
3. Record verified timestamp precision and honest unresolved provenance.
4. Deliver a source-target handoff that opens the quote in its meeting context.

## Acceptance criteria

1. A meeting-origin receipt retains its artifact, meeting, and segment refs.
2. Verified moments use `resolve_decision_moment()` rather than inferred time.
3. An unresolved moment remains explicitly unresolved; no timestamp is forged.
4. Opening receipt evidence lands on the exact speaker quote when resolvable.

## Test plan

- Service: persist and resolve a receipt with an exact meeting segment.
- Service: exercise unresolved provenance and assert an honest result.
- Integration: open a receipt source and assert the selected quote and speaker.
