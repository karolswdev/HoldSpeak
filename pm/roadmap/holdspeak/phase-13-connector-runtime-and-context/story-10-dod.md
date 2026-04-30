# HS-13-10 - Phase 13 exit + DoD

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-01 through HS-13-09
- **Unblocks:** stable connector-runtime + meeting-context baseline
- **Owner:** unassigned

## Problem

Phase 13 should close with evidence that the runtime substrate,
pipeline runner, and meeting-context surfaces form a coherent
ecosystem — not three loosely-related arcs.

## Scope

- **In:**
  - Phase evidence bundle (one `evidence-story-{n}.md` per
    shipped story).
  - Focused phase-13 sweep covering substrate +
    pipelines + meeting-context tests.
  - Full non-Metal regression.
  - Roadmap status updates: phase 13 done, parent README
    phase index updated, designer-handoff screenshots
    refreshed where the new pre-briefing / project-
    briefing-timeline panels appear.
  - Update `docs/CONNECTOR_DEVELOPMENT.md` with the
    pipeline kind + permission enforcement notes that
    landed during the phase.
- **Out:**
  - New connector features.
  - Phase 14 prep beyond a one-line "what comes next" in
    this file.

## Acceptance Criteria

- [ ] Every shipped story has a matching
  `evidence-story-{n}.md` file in the phase folder.
- [ ] `current-phase-status.md` story table fully updated.
- [ ] `pm/roadmap/holdspeak/README.md` "Last updated"
  bumped, phase 13 flipped to `done`.
- [ ] `docs/CONNECTOR_DEVELOPMENT.md` documents the
  pipeline kind, the permission gates, the user-pack
  discovery path, and the run-history surface.
- [ ] `designer-handoff/screenshots/` includes shots that
  reflect the new dashboard pre-briefing panel + the
  project briefing timeline on `/history`.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  green.
- [ ] `npm run build` clean.

## Test Plan

- Focused sweep against the new test files.
- Full regression sweep.
- Manual screenshot recapture against the running app.

## Notes

If any of the consumer-facing stories (HS-13-08, HS-13-09)
need polish slices in the style of phase 12, this story is
where they roll up — but the substrate stories (01..05) and
the pipeline stories (06..07) should land cleanly without
revisits. If they don't, that's the signal to step back and
re-look at the contract.
