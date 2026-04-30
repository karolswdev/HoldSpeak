# HS-12-04 - Designer handoff refresh + phase exit

- **Project:** holdspeak
- **Phase:** 12
- **Status:** done
- **Depends on:** HS-12-01, HS-12-02, HS-12-03
- **Unblocks:** phase 13 (TBD)
- **Owner:** unassigned

## Problem

Phase 12 doesn't land until the artifact a designer would judge
matches the new voice. `designer-handoff/style-handoff.md` from
phase 10 documents the pre-Workbench voice; if we don't refresh
it, future contributors get the wrong reference.

## Scope

- **In:**
  - Rewrite `designer-handoff/style-handoff.md` to document the
    Workbench-evoking voice: palette values, font choice,
    radius-0 grammar, what was deliberately *not* taken from
    Workbench (stripe title bars, gadget bevels, pixel cursor).
  - Update `designer-handoff/ux-inventory.md` only where the
    voice change affects surface-level claims.
  - Refresh every screenshot in
    `designer-handoff/screenshots/` against the running app.
  - Phase DoD checklist:
    - All HS-12-01..03 stories `done` with evidence files.
    - `current-phase-status.md` story table fully updated.
    - `pm/roadmap/holdspeak/README.md` "Last updated" line
      bumped, phase 12 flipped to `done`.
    - `npm run build` clean.
    - `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.
- **Out:**
  - Any new design work.
  - Phase 13 prep beyond a one-line "what comes next" in this
    file.

## Acceptance Criteria

- [x] `style-handoff.md` reflects the Workbench-evoking voice;
  the open questions section is closed or explicitly deferred.
- [x] Every route screenshot in `designer-handoff/screenshots/`
  was captured against the new voice.
- [x] Phase 12 flipped to `done` in the project README phase
  index in this same commit.

## Test Plan

- Manual screenshot recapture against the running app.
- Full regression sweep: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes

This story is the discipline that makes "phase 12 done" mean
something specific. Don't skip the open-questions audit in
`style-handoff.md` — that document is the lighthouse for whether
the voice is coherent.
