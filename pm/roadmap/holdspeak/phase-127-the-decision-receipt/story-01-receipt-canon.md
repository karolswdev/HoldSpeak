# HS-127-01 — Receipt canon

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-127-02 through HS-127-10
- **Owner:** unassigned

## The thesis (the bar)

A decision receipt is a compact, durable record, not a rewritten decision
or a transient lifecycle return value. Establish one canonical, local-first
schema that preserves the choice and every later change needed to explain it.

### What changes

1. Add `decision_receipts` with decision, rationale, alternatives, owner,
   review date, lifecycle, origin reference, and supersession fields.
2. Add `decision_receipt_sources` for provenance and
   `decision_receipt_work` for affected-work links.
3. Add append-only `decision_receipt_revisions`; edits write a revision.
4. Advance the schema from v40 to v41 with indexes and migration coverage.

## Acceptance criteria

1. A receipt requires decision, rationale, alternatives, owner, review date,
   and lifecycle before it persists.
2. Sources, work links, and revisions retain stable receipt identity and
   foreign-key integrity.
3. Revision history is append-only; no update path silently overwrites it.
4. The v40-to-v41 migration preserves existing data and is idempotent.

## Test plan

- Migration: upgrade a populated v40 database to v41 and reopen it.
- Repository: reject missing required receipt fields and persist valid records.
- Repository: append revisions and verify prior revision content is unchanged.
