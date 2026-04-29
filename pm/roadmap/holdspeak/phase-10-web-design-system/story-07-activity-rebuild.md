# HS-10-07 - `/activity` rebuild

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-10-03, HS-10-04, HS-10-05
- **Unblocks:** HS-10-13
- **Owner:** unassigned

## Problem

`/activity` is the densest screen in the product and the worst-feeling
one (see `designer-handoff/screenshots/activity-desktop.png`). Long
monotone activity rows, poorly differentiated preview-vs-saved
candidates, hand-rolled connector controls, and per-panel empty states
that reinvent each other. It is the screen most in need of visual
grammar.

## Scope

- **In:**
  - Replace `holdspeak/static/activity.html` with `web/src/pages/
    activity.astro`.
  - Top-level grid: ingestion + retention status panel; project rules
    panel; meeting candidates panel; connectors panel; activity records
    list.
  - **Preview vs saved candidate grammar**: visually distinct row
    styles (token-driven, not just a label) so a user can scan a list
    and see "preview, preview, saved, preview" instantly.
  - **Connector control pattern** (consumed later by HS-10-10): each
    connector card shows status pill (enabled/disabled/CLI-missing/
    last-error), preview button, run button (disabled when not
    enabled), output controls.
  - Activity records list uses `ListRow` with stable secondary lines
    (no row-height jitter on long URLs — wrap policy in tokens).
  - Every panel uses the standard `EmptyState` from HS-10-03 with a
    single useful next action.
  - All destructive actions show a `Pill` indicating *what* will be
    affected (connector output vs source data) — wired into HS-10-11.
- **Out:**
  - New connector functionality (those live in phase 11).
  - Project rule preview/apply API changes.
  - Calendar candidate ingestion changes.

## Acceptance Criteria

- [ ] All five `/activity` panels render on the new system.
- [ ] Preview vs saved candidates are distinguishable in a 2-second
  glance (sample screenshots in evidence).
- [ ] Connector controls follow the same grammar across `gh`, `jira`,
  Firefox events, and calendar candidates.
- [ ] Empty state for each panel names a useful next action.
- [ ] Activity records list does not horizontally overflow at 1280px;
  long URLs wrap or truncate per the wrap policy.
- [ ] Existing `/activity` API contracts remain unchanged.

## Test Plan

- Static surface integration test (parallel to HS-9-11's pattern).
- Manual visual sweep with seeded local data: empty, partial, dense.
- Manual narrow-viewport pass at 768px and 420px.

## Notes

This is the screen most likely to expose gaps in the component library
— flag any `ListRow` / `Panel` / `Pill` weaknesses back into HS-10-03's
gallery and patch the components rather than working around them
inline.
