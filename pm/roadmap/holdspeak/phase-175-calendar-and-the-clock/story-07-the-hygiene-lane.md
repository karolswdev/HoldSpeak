# HS-175-07 — The hygiene lane

- **Project:** holdspeak
- **Phase:** 175
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-175-08
- **Owner:** unassigned

## Problem

Every phase in the Tuesday Arc carries a hygiene lane (THE-TUESDAY-ARC.md
section 4) paying items from the 169 ledger that the phase's tree
touches. Phase 175 touches the calendar ingest conductor, the scheduled
recording conductor, the Monday brief service, and the watch sources —
each may carry hygiene debt (the sidecar fetcher seam from 165, the
empty-patch revisions from 158 N-1, the nine tsc-erroring web files
from 150).

## Scope

- In:
  - Census the hygiene items from THE-TUESDAY-ARC.md section 4 that
    Phase 175's tree touches (calendar_ingest_conductor.py,
    scheduled_recording_conductor.py, monday_brief_service.py,
    watch_sources.py, project_service.py).
  - Pay the items this phase's tree touches.
- Out:
  - Hygiene items that belong to other phases' trees.
  - New feature work (that is stories 02-05).

## Acceptance criteria

- [ ] The census of hygiene items is documented with each item's
      source, current state, and resolution.
- [ ] Every item this phase's tree touches is paid or explicitly
      deferred with a reason and re-target phase.
- [ ] No new hygiene debt introduced by this phase's work.

## Test plan

- Unit: the relevant tests pass after paying each item.
- Integration: n/a.
- Manual: the census is reviewed for completeness.

## Notes / open questions

- The sidecar fetcher seam (165) may apply if watch_sources.py or the
  conductor uses the sidecar for any reads. Census at story time.
- The nine tsc-erroring web files (150) may include calendar-related
  components. Census at story time.
