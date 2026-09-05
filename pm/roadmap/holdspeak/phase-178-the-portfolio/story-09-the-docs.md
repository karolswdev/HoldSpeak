# HS-178-09 — The docs

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-08
- **Unblocks:** HS-178-10
- **Owner:** unassigned

## Problem

The portfolio surface, the cross-project aggregate, the dependency
alerts, and the Monday brief's portfolio section introduce new
architecture and new user-facing concepts. The documentation must
reflect these.

## Scope

- In:
  - ARCHITECTURE.md updated with the portfolio aggregate, the
    dependency detection algorithm, and the `GET /api/desk/portfolio`
    route.
  - USER_GUIDE.md extended with the Projects surface, the command deck
    verbs, and the Monday brief portfolio section.
  - POSITIONING.md canonical feature names table updated if new
    canonical names are introduced.
  - Guide screenshots re-shot for every face changed by this phase.
- Out:
  - API docs (the route docstrings are sufficient).
  - The companion's portfolio docs (Phase 179).

## Acceptance criteria

- [ ] ARCHITECTURE.md documents the portfolio aggregate and the
      dependency detection algorithm.
- [ ] USER_GUIDE.md describes the Projects surface, the command deck
      verbs, and the brief's portfolio section.
- [ ] Guide screenshots match the shipped face at both widths.
- [ ] POSITIONING.md canonical names updated if needed.

## Test plan

- Unit: n/a (docs story).
- Integration: n/a.
- Manual: doc review; screenshot freshness check.

## Notes / open questions

- None.
