# HS-178-03 — The Projects surface

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-01, HS-178-02
- **Unblocks:** HS-178-08
- **Owner:** unassigned

## Problem

The desk has no surface for seeing all projects at once. The Door lists
projects for creation; the shade's PROJECTS section (171) shows counts
but not depth. A Projects surface shows every active Room as a row with
health, urgency, and a depth pane that opens the full needs-you list
grouped by project.

## Scope

- In:
  - The Projects surface (window or shade section, per the design):
    Room rows with needs-you count, first WHY, release-readiness
    indicator (green/amber/red), oldest-unresolved age token.
  - Urgency sort: red first, then amber, then green; within severity,
    oldest unresolved first.
  - The depth pane: selecting a project row opens the cross-project
    needs-you detail with rows grouped by project, ranked by severity
    and age.
  - Filtering: by project, by severity, by signal type.
  - Both widths (1440 + 393; the 393 view stacks rows vertically,
    the depth pane becomes a drill-down navigation).
  - Library species only (SurfaceLedger, SurfaceLedgerRow, StateChip,
    SurfaceSection, Button).
- Out:
  - Project creation (the Door owns that).
  - External writes from the surface.
  - The companion's portfolio view (Phase 179).

## Acceptance criteria

- [ ] Every active Room appears as a row with needs-you count, first
      WHY, release-readiness indicator, and oldest-unresolved age
      (Article I — the Desk is the operating surface).
- [ ] Rows sorted by urgency (red, amber, green; then by age).
- [ ] The depth pane shows cross-project needs-you rows grouped by
      project (Article VII.1 — no prose; tokens and verbs only).
- [ ] Filtering by project, severity, and signal type works.
- [ ] Both widths (1440 + 393) verified by screenshot walk.
- [ ] Every verb is the library Button (UX-CANON.md rule A.1).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k projects_surface`
  - Rendering with seeded portfolio aggregate data.
  - Urgency sort order.
  - Filtering.
- Integration: the surface reads from the portfolio aggregate route.
- Manual: screenshot walk at 1440 + 393; the owner's desk with his
  real projects.

## Notes / open questions

- If the design resolves the portfolio as a deeper shade section rather
  than a window, this story adapts the shade's PROJECTS section from
  171 rather than building a new window.
