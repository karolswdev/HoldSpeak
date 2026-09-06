# HS-178-04 — Release readiness across Rooms

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-02
- **Unblocks:** HS-178-08
- **Owner:** unassigned

## Problem

Phase 173 ships a per-project release-readiness scorecard (story 05).
The portfolio needs a cross-project aggregate: a red signal in any Room
turns the portfolio's aggregate red for that signal dimension. The
aggregate scorecard gives the owner one glance across all projects.

## Scope

- In:
  - The release-readiness aggregate computation: for each signal
    dimension (review latency, CI health, open blockers, overdue
    commitments), the worst state across all active Rooms is the
    portfolio's aggregate state for that dimension.
  - The aggregate appears in the Projects surface as a summary row
    (or header) and in the Monday brief's portfolio section.
  - The aggregate is computed from the cadence-cached Room health
    sections (no new reads).
- Out:
  - New signal dimensions beyond 173's set.
  - Per-project scorecard rendering (173 owns that).

## Acceptance criteria

- [ ] The portfolio-level scorecard aggregates 173's per-project
      scorecards; a red in any Room turns the aggregate red for that
      signal (Article VI — honest at zero; a green aggregate means every
      Room is green).
- [ ] The aggregate appears in the Projects surface and in the Monday
      brief's portfolio section.
- [ ] Verified by a unit test with three seeded projects: one green,
      one amber, one red; the aggregate is red.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k release_readiness_aggregate`
  - Three projects with different states; verify aggregate.
  - All green; verify aggregate is green.
  - One red on review latency; verify that dimension is red.
- Integration: the aggregate renders in the Projects surface.
- Manual: the owner's desk.

## Notes / open questions

- The signal dimensions are 173's decision; this story aggregates
  whatever 173 ships. If 173 defers a signal, the portfolio aggregate
  omits that dimension.
