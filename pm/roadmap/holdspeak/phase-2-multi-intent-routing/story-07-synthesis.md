# HS-2-07 — Step 6: Synthesis pass

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-04, HS-2-05, HS-2-06
- **Unblocks:** HS-2-08
- **Owner:** unassigned

## Problem

Spec §9.7 — end-of-meeting pass that merges per-window plugin
artifacts into coherent final outputs (no duplication, lineage
preserved). This is what turns a stream of window artifacts into a
single shareable artifact set.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.7.
- **Out:** UI surfacing (HS-2-08), feature-flag plumbing (HS-2-09).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up._

## Notes / open questions

- Dedupe key: `ArtifactLineage` source-window-IDs vs. content hash vs. plugin-supplied idempotency key. Spec §12 mitigations name "idempotency key + synthesis dedupe"; pin the exact strategy at pickup.
