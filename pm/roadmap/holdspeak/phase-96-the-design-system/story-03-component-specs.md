# HS-96-03 — Component state specs

- **Project:** holdspeak
- **Phase:** 96
- **Status:** backlog
- **Depends on:** HS-96-01
- **Unblocks:** HS-96-04, HS-96-05

## Problem

The Signal grammar and the OS chrome have no written contract for their
states. Hover exists where someone added it; focus-visible is
inconsistent; active/pressed is mostly absent; busy states are per-widget
inventions. The design-system skill's component-spec pattern (a property
× state matrix per component) is the fix — written down, then made true.

## Scope

- In:
  - state matrices (default / hover / focus-visible / active / disabled
    / busy, plus component-specific states like recording or parked) for:
    Signal Button, chips, inputs, Select, Switch, Tabs, StatusPill,
    InlineMessage; the OS chrome: DeskWindowFrame (head, verbs, grip),
    dock chips, the desk-chip family, the shelf rows, the egress badge,
    the orb, zone trays, and desk objects (GL hover/selected states
    included, expressed in the same vocabulary);
  - the matrices written to `docs/internal/DESIGN_SYSTEM.md` referencing
    component tokens only;
  - the gaps implemented: every interactive element gains focus-visible
    and active treatments from the matrix; busy states unified on one
    pattern;
  - a spec-conformance test sweep for the implementable rows (rendered
    class/aria assertions, not pixels).
- Out:
  - new components; palette changes beyond the matrices' needs.

## Acceptance criteria

- [ ] The spec document covers every listed component with a full state
      matrix in token vocabulary.
- [ ] Every interactive element on the desk shows a visible
      focus-visible state and a distinct active state, per spec —
      verified by the conformance sweep and a keyboard screenshot pass.
- [ ] Busy/loading is one pattern across Signal and the chrome.
- [ ] Web suite green; no spec row references a raw value.

## Test plan

- the conformance sweep in vitest; a keyboard-traversal Playwright walk
  capturing focus states at 1440; `npm run check`.

## Implementation direction

- Spec first, implement second; where current behavior contradicts a
  sensible matrix, the matrix wins and the change is named.
- GL states (hover glow, selected ring) get token-derived values through
  the generated TS module from HS-96-02.

## Evidence required

- the spec doc; conformance sweep output; the keyboard focus walk shots.
