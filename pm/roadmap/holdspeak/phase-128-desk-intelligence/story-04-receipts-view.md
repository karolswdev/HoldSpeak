# HS-128-04 — Receipts view

- **Project:** holdspeak
- **Phase:** 128
- **Status:** backlog
- **Depends on:** HS-128-01
- **Unblocks:** HS-128-05, HS-128-07
- **Owner:** unassigned

## The thesis (the bar)

Receipts answer why from the Desk. Search and the full decision record coexist
in one pullout, so the owner can follow evidence without a modal detour.

### What changes

1. Make Receipts search-first, querying on keystroke into a `SurfaceLedger`.
2. Provide a `WHY` mode that filters results to governing decision receipts.
3. Render detail in place: rationale, alternatives, owner, provenance quote,
   affected-work chips, supersession chain, and revision timeline.
4. Preserve the result context while a detail is open; never open a modal.

## Acceptance criteria

1. Search returns `DecisionReceiptService` results as the query changes.
2. Detail contains every structured receipt field and exact provenance quote.
3. WHY-filtered results can be opened and cleared without losing pullout state.
4. Supersession and revisions expose durable history rather than collapsed copy.

## Test plan

- Web: test keystroke search, empty results, WHY filter, and detail rendering.
- Service: fixture receipt revisions, supersession, provenance, and work links.
- Interaction: open detail and return to its preserved result ledger.
