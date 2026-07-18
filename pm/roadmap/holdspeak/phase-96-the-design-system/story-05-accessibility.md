# HS-96-05 — The accessibility pass

- **Project:** holdspeak
- **Phase:** 96
- **Status:** backlog
- **Depends on:** HS-96-03
- **Unblocks:** HS-96-07

## Problem

The OS is pointer-first today. Windows do not manage focus on open or
return it on close; the dock and menu carry partial ARIA; some
shelf/chrome affordances are unreachable by keyboard; reduced-motion
covers the old animations but not all of Phase 95's. The ui-styling
skill's accessibility patterns (Radix-grade focus and keyboard behavior)
are the bar; whether to adopt Radix primitives themselves is this
story's recorded decision.

## Scope

- In:
  - window focus management: opening a window moves focus to it,
    closing returns focus to the opener, Escape semantics consistent —
    WITHOUT modal traps (Article VII: windows coexist);
  - a keyboard reachability audit of the desk (chrome, shelf, dock,
    windows, a11y layer) with every gap fixed;
  - ARIA completeness on the shell furniture (menu, dock toolbar, tabs,
    verbs) per the skill's patterns;
  - reduced-motion completeness for Phase 95's additions (GL bob/motes
    already honor it; verify window transitions, dock, snap);
  - the Radix decision: evaluate adopting Radix primitives under Signal
    skins for menu/tabs/dialog-like surfaces vs. implementing the
    patterns by hand; DECIDE, record the reasoning in the story, and
    implement the chosen path for at least the menu;
  - axe-core sweeps for the desk surface added to the suite.
- Out:
  - full WCAG certification; native/Swift a11y.

## Acceptance criteria

- [ ] Focus: open moves in, close returns, Escape consistent, no traps —
      pinned by tests and a keyboard-only Playwright walk that operates
      windows, dock, menu, and shelf end to end.
- [ ] Every interactive desk affordance is keyboard-reachable; the audit
      table ships in the evidence with each gap's fix.
- [ ] axe-core sweep of the desk (windows open) reports no violations at
      the severity gate chosen in-story; the gate is recorded.
- [ ] The Radix decision is recorded with reasoning and implemented for
      the menu at minimum.
- [ ] Reduced-motion: no continuous decorative animation runs with the
      preference set (verified by the existing lock pattern extended to
      the new surfaces).

## Test plan

- vitest focus/ARIA tests; the keyboard-only walk; axe-core sweep;
  `npm run check`.

## Evidence required

- the audit table; walk output; axe report; the recorded decision.
