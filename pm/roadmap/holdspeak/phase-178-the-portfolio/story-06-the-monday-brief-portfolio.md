# HS-178-06 — The Monday brief portfolio section

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-02
- **Unblocks:** HS-178-08
- **Owner:** unassigned

## Problem

The Monday brief (monday_brief_service.py:112) aggregates kernel
operations but has no per-project structure. A senior architect
managing three people needs the brief to show each project's state at
a glance: its scorecard, its top needs-you, and what changed since the
last brief.

## Scope

- In:
  - A PORTFOLIO section in the Monday brief: one row per active
    project with the release-readiness scorecard indicator, the top
    needs-you item, and the delta (new items, resolved items, changed
    states) since the previous brief.
  - The section uses the portfolio aggregate (HS-178-02) as its data
    source.
  - The section renders in the shade (171's brief display) and in any
    future brief export.
- Out:
  - Changes to the brief's generation pipeline beyond adding the
    portfolio section.
  - Cross-brief trend analysis (the delta is brief-to-brief, not
    week-to-week).

## Acceptance criteria

- [ ] The Monday brief includes a PORTFOLIO section with one row per
      active project (Article I — the Desk is the operating surface;
      the brief is part of the Desk).
- [ ] Each row shows the release-readiness indicator, the top
      needs-you item, and the delta since the previous brief.
- [ ] Verified by a unit test generating two consecutive briefs with
      changed project states; the delta is correct.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k monday_brief_portfolio`
  - Brief with two projects; verify portfolio section structure.
  - Second brief after a project gains a needs-you item; verify delta.
- Integration: the brief renders in the shade.
- Manual: the owner's desk; the brief with his real projects.

## Notes / open questions

- The delta computation needs a way to compare the current portfolio
  state with the previous brief's snapshot. If 171 stores the brief's
  data (as `monday_brief_items` suggests), the delta can be derived
  from the stored items.
