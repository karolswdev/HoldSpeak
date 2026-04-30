# HS-13-09 - Cross-meeting summary on /history

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-07
- **Unblocks:** "phase 13 paid off" exit (HS-13-10)
- **Owner:** unassigned

## Problem

`/history` already groups meetings by project (the Projects
tab). What's missing is the cross-meeting *narrative* — the
project's activity arc across recent sessions. The
meeting_context pipeline accumulates annotations per project
over time; a `/history` view that walks them in reverse
chronological order is the natural surface.

## Scope

- **In:**
  - On the existing Projects tab in `/history`, when a
    project is selected, render a "Project briefing
    timeline" panel underneath the project metadata.
  - Timeline = a list of `meeting_context` annotations for
    that project, newest first, each rendered as a dense
    `ListRow`: timestamp + first-line summary + expand-
    toggle for the full markdown body.
  - "Run briefing now" button in the panel toolbar — runs
    the `meeting_context` pipeline scoped to the selected
    project.
  - Empty state when the project has no briefing
    annotations.
  - The expanded body uses the same tiny inline renderer
    from HS-13-08 (one shared util file).
- **Out:**
  - Cross-project "what changed everywhere this week"
    overview. One project at a time stays the model.
  - Diff view between briefings. Each briefing is a
    snapshot, not a delta.
  - Editing / annotating briefings by hand. Briefings are
    pipeline output; the user can clear them, not edit
    them.

## Acceptance Criteria

- [ ] Selecting a project in `/history` Projects tab shows
  the briefing timeline panel below project metadata.
- [ ] Empty-state copy when no briefings exist.
- [ ] Timeline rows expand inline (no modal); markdown
  renders bullets + bold + links.
- [ ] "Run briefing now" runs the pipeline for the selected
  project's id; success refreshes the timeline.
- [ ] Workbench window grammar throughout.
- [ ] Inline renderer extracted to a shared util reused by
  both HS-13-08 and HS-13-09.

## Test Plan

- Manual walk: select project → expand a briefing → assert
  bullets render.
- Manual: empty project → empty state.
- Manual: "Run briefing now" → row appears.
- Integration: API path `/api/projects/{id}/briefings`
  returns rows in the expected order.

## Notes

This is the second consumer-facing surface in the phase-13
C-arc. It's deliberately less prominent than the dashboard
pre-briefing — `/history` is a review surface, the dashboard
is a starting surface, and the same data serves both roles
at different ergonomic levels.
