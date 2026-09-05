# HS-178-02 — The portfolio aggregate

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-01
- **Unblocks:** HS-178-03, HS-178-04, HS-178-05, HS-178-06
- **Owner:** unassigned

## Problem

`GET /api/desk/needs-you` (projects.py:380) iterates every active Room
per request and flattens needs-you items into one list. This is flat:
no per-project health summary, no release-readiness indicator, no
dependency detection. The portfolio surface needs a deeper cross-Room
read that groups, ranks, and caches.

## Scope

- In:
  - `GET /api/desk/portfolio` — a new route returning per-project
    Room summaries (needs-you count, first WHY, release-readiness
    indicator, oldest unresolved age, health tokens), the full
    needs-you rows grouped by project, and dependency alert candidates.
  - The response reuses the cadence cache from 171 (never recomputes
    Room sections per request).
  - The response shape supports both the Projects surface and the
    Monday brief's portfolio section.
- Out:
  - The face (HS-178-03 owns the surface).
  - External writes (reads only; Article V:5).
  - Dependency detection logic (HS-178-05 owns that).

## Acceptance criteria

- [ ] `GET /api/desk/portfolio` returns per-project Room summaries with
      needs-you count, first WHY, release-readiness indicator, and
      oldest unresolved age.
- [ ] The response includes full needs-you rows grouped by project
      and ranked by severity then age.
- [ ] The response uses the cadence cache; response time < 100 ms from
      cache (Article V:5 — reads are free).
- [ ] Verified by a unit test with two seeded projects with different
      needs-you states.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k portfolio_aggregate`
  - Two projects, different needs-you: verify grouping and ranking.
  - Cache hit: verify response time from warm cache.
  - Archived project excluded.
- Integration: the route serves the portfolio surface.
- Manual: the aggregate on the owner's desk with his real projects.

## Notes / open questions

- The cadence cache from 171 stores per-Room snapshots. The portfolio
  aggregate reads from those snapshots, not from live Room reads.
  The cache invalidation signal is the cadence tick (stale-for-one-tick
  is acceptable).
