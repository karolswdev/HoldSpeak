# HS-13-08 - Pre-meeting briefing surface on /

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-07
- **Unblocks:** consumer-facing payoff of the connector framework
- **Owner:** unassigned

## Problem

The meeting_context pipeline produces useful annotations but
nothing on the runtime dashboard surfaces them. A user
glancing at `/` before starting a meeting should see "here's
what changed in your project context since last time" — that's
the whole point of the activity ledger feeding the pipeline.

## Scope

- **In:**
  - New "Project briefing" panel on `/` (the runtime
    dashboard), shown only when a `meeting_context`
    annotation exists for the current project. Sits above the
    Transcript stream panel during idle, hides during active
    meetings (the live transcript is the priority).
  - Panel renders the annotation's deterministic markdown
    using a tiny inline renderer (bullets + bold + linked
    URLs). No external markdown library.
  - "Refresh briefing" button in the panel header runs the
    `meeting_context` pipeline on demand (subject to the
    freshness rule from HS-13-06).
  - "Last refreshed" timestamp + a status pill (`success`
    when the most recent pipeline run succeeded, `warn`
    when stale > N hours, `danger` when the most recent run
    failed).
  - Empty state when no project briefing exists ("No
    briefing yet. Visit some PRs / tickets / calendar
    events, then refresh.").
- **Out:**
  - Multi-project switcher on `/`. The pre-briefing
    surfaces the *current cwd* project; switching projects
    is a `/history` concern (HS-13-09).
  - Streaming live updates as upstream packs run. The panel
    refreshes on click.

## Acceptance Criteria

- [ ] Panel shows on `/` when a `meeting_context`
  annotation exists for the current project.
- [ ] Panel hides during active meetings (existing
  `meetingActive` Alpine flag).
- [ ] "Refresh briefing" triggers the pipeline; the panel
  reflects the new annotation on success and the new error
  on failure.
- [ ] Empty state copy is precise about what the user needs
  to do next.
- [ ] Panel uses Workbench window grammar (blue title strip
  + VT323 caption "Project briefing").
- [ ] Keyboard-only path: Tab into the panel → Refresh
  button → activate; reads consistent with the rest of the
  dashboard.

## Test Plan

- Manual walk on `/` after a `meeting_context` run; assert
  the briefing renders with bullets and links.
- Manual: toggle `meetingActive` (start a meeting); panel
  hides. Stop; panel returns.
- Manual: force a pipeline failure (mock CLI return code);
  panel pill flips to `danger`; error message readable.
- a11y: Tab order, focus visible, panel announced to screen
  readers.

## Notes

The pre-briefing surface is the first visible piece of the
phase-9..13 arc paying off — activity ledger → connectors →
pipeline → meeting context. If this story can't land cleanly,
re-look at HS-13-07's annotation shape; the surface is
subordinate to the data.
