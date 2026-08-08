# HS-126-04 — Collect breakage

- **Project:** holdspeak
- **Phase:** 126
- **Status:** done
- **Depends on:** HS-126-02
- **Unblocks:** HS-126-07
- **Owner:** unassigned

## The thesis (the bar)

Broke names failures plainly and makes each one actionable. Collect failures
from the desk's real operational records and attach the repair path rather
than presenting an opaque error receipt.

### What changes

1. Collect event errors from `pipeline_events` within the brief window.
2. Collect failed `connector_runs`, failed activity imports, and failed
   projections.
3. Normalize each failure into one breakage candidate with source reference,
   concise error state, priority, and a repair path.
4. Deduplicate the same underlying failure when it appears in more than one
   receipt stream.

## Acceptance criteria

1. Each of the four failure sources can produce a cited Broke item.
2. Every breakage item names a repair path that opens or directs to its source.
3. A repeated receipt for one unresolved failure does not inflate the section.
4. Resolved failures are not reported as currently broken without supporting
   window evidence.
5. Collection remains local and deterministic.

## Test plan

- Unit: seed one failure from each source and assert four actionable candidates.
- Unit: assert duplicate receipts collapse to one breakage item.
- Unit: assert repair paths resolve to the correct source record.
- Integration: generate candidates against SQLite fixtures.
