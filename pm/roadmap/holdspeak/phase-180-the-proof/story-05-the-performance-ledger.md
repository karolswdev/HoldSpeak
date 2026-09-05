# HS-180-05 — The performance ledger

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** Phase 179 merged
- **Unblocks:** HS-180-09
- **Owner:** unassigned

## Problem

A release candidate needs a performance baseline. Key routes, memory
use, and startup time must be measured and compared against the 170
baseline (if one exists) or established as the first baseline.

## Scope

- In:
  - Response times for key routes: `GET /api/desk/needs-you`,
    `GET /api/desk/portfolio`, `GET /api/projects/{id}/room`,
    `GET /api/projects` -- measured from the hub on the owner's
    machine (cold + warm, p50 + p95 over 10 requests).
  - Memory use at steady state: the hub process's RSS after 10 minutes
    of idle with 3 active projects.
  - Startup time from cold: the time from `holdspeak web` to the first
    successful API response.
  - Comparison with the 170 baseline if it exists; otherwise this
    becomes the baseline.
  - The ledger filed as evidence in the phase folder.
- Out:
  - Performance optimization (180 proves, it does not build).
  - Load testing (the owner is one user; the proof is single-user
    performance).
  - Companion app performance (that is a separate measurement).

## Acceptance criteria

- [ ] Response times for key routes measured (cold + warm, p50 + p95)
      (Article VIII.1 -- native-grade craft; Article IX.3 -- evidence).
- [ ] Memory use at steady state measured.
- [ ] Startup time from cold measured.
- [ ] No regression from the 170 baseline (or the baseline established
      if 170 did not measure).
- [ ] The ledger filed as evidence.

## Test plan

- Unit: n/a.
- Integration: n/a.
- Manual: the measurements on the owner's machine; the ledger.

## Notes / open questions

- The performance budget from Article VIII.1 is "60fps interaction
  budget on the production bundle." This story measures server-side
  latency and resource use, not frame rate. Frame rate is a face-level
  measurement covered by the census (170's scanner checks for
  animation and render patterns).
