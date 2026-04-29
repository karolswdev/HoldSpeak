# HS-10-12 - Motion + accessibility pass

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-10-06, HS-10-07, HS-10-08, HS-10-09, HS-10-10, HS-10-11
- **Unblocks:** HS-10-13
- **Owner:** unassigned

## Problem

Motion and accessibility are the easiest aspects of a design system to
half-do and the easiest to forget. After all four routes are rebuilt,
the system needs a deliberate sweep so that micro-transitions are
consistent (start/stop, run/preview, dialog open/close), focus is
visible everywhere, and contrast holds across every state.

## Scope

- **In:**
  - Micro-transitions for state changes:
    - Meeting start/stop transition on `/`.
    - Connector preview → run transition on `/activity`.
    - Dialog open/close on `ConfirmDialog`.
    - Pill tone changes (animate the dot, not the box).
  - All transitions consume motion tokens from HS-10-02 and respect
    `prefers-reduced-motion: reduce`.
  - Accessibility audit per route, captured as a checklist in evidence:
    - All interactive elements reachable by keyboard.
    - Focus order is logical.
    - Visible focus ring matches the system grammar.
    - All form inputs have associated labels.
    - All non-decorative SVGs have `aria-label` or `role="img"`.
    - Color contrast holds at AA for all text and meaningful UI in
      every state pill.
  - One axe-core (or equivalent) automated pass per route, with the
    findings either fixed or recorded as known acceptable.
- **Out:**
  - Page-level transitions / route animations — these conflict with
    the "calm and precise" direction.
  - WCAG AAA level work.

## Acceptance Criteria

- [ ] Every micro-transition listed above exists and uses motion
  tokens.
- [ ] `prefers-reduced-motion: reduce` flattens all transitions to 0ms
  (verified per route).
- [ ] Axe-core run on each route shows zero serious or critical
  violations, or each remaining violation has a written justification
  in evidence.
- [ ] Keyboard-only walkthrough completes the four canonical workflows
  (start meeting, preview/run gh enrichment, review history meeting,
  edit a dictation block) without dead-ends.

## Test Plan

- Axe-core run script committed under `web/` if practical; otherwise
  documented browser-extension run with screenshots.
- Manual keyboard-only run of the four canonical workflows.
- Manual `prefers-reduced-motion` toggle in DevTools.

## Notes

This is the polish story. Don't merge it with any rebuild — it
deliberately follows them so the auditor (you or a teammate) can see
the whole system at once.
