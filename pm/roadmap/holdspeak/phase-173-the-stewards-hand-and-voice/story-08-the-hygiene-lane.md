# HS-173-08 — The hygiene lane

- **Project:** holdspeak
- **Phase:** 173
- **Status:** done
- **Depends on:** HS-173-06
- **Unblocks:** HS-173-09
- **Owner:** unassigned

## Problem

Every phase carries hygiene items from THE-TUESDAY-ARC.md section 4
that its tree touches. Phase 173's steward and update work may touch
items from the ledger: the sidecar fetcher seam (165), the four
legacy-wrapping writes in one transaction (158 S-1), and any tsc-
erroring web files in the steward/update UI area.

## Scope

- In:
  - Identify which hygiene lane items from THE-TUESDAY-ARC.md
    section 4 this phase's tree touches.
  - Pay them: fix the identified items in the same phase.
  - Record what was paid and what remains.
- Out:
  - Hygiene items whose tree is not touched by this phase.
  - Refactoring beyond what the hygiene items require.

## Acceptance criteria

- [x] Every hygiene lane item whose tree this phase touches is
      identified and paid.
- [x] The record names what was paid and what remains for later phases.

## Test plan

- Unit: whatever the specific hygiene items require.
- Integration: n/a.
- Manual: the record is truth-audited.

## Notes / open questions

- The specific items will be identified when the phase starts; they
  depend on which files 173's stories touch.
