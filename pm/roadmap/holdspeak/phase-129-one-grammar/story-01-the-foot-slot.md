# HS-129-01 — The foot slot: one window anatomy

- **Project:** holdspeak
- **Phase:** 129
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-129-02, HS-129-03, HS-129-04, HS-129-05
- **Owner:** unassigned

## The thesis (the bar)

The window contract is head fixed, body scrolls, foot fixed — and today only
pullouts and eight hand-composed windows honor it. `DeskWindowFrame` exposes
no foot; `SurfaceWindowHost` (web/src/desk/components/SurfaceWindows.tsx:337-363)
mounts all 14 registered cores entirely inside the scrolling
`.desk-surface-body`, so every hosted core's `SurfaceFooter` scrolls with
content and floats mid-window when content is short (audit B: Settings ~179 px,
Meetings 130–156 px of dead space). The frame gains a foot the same way it
gained wings.

### What changes

1. `SurfaceWindowHost` renders a foot target as a SIBLING after
   `.desk-surface-body`, and provides a `FootSlotContext` mirroring the
   existing `WingSlotContext` (SurfaceWindows.tsx:324-361).
2. `SurfaceFooter` (web/src/desk/surface/SurfaceFooter.tsx) portals into the
   foot target when the context is present; renders in place otherwise —
   zero edits in the 14 cores' JSX beyond what tests reveal, and zero
   behavior change for the already-correct pullouts/windows.
3. `window-chrome.css` becomes the single owner of frame anatomy (head/body/
   foot placement, scroll invariant); the split `.desk-pullout-head`
   ownership with pullout.css:56-71 ends (audit D §2 target ownership).
4. `.desk-surface-body` gains `min-height: 0` (the pullout body already has
   it, pullout.css:49-51) so small windows shrink the body instead of
   clipping the foot (audit B's resize defects).
5. Contract tests land FIRST (audit D migration step 1): the footer-sibling
   invariant, the only-body-scrolls invariant, and container reflow in a
   narrow window — frozen against ZoneWindow as the reference.

## Acceptance criteria

1. Every registered SurfaceWindowHost core (14 + Settings' Guide route) shows
   its footer pinned to the window's bottom edge: content taller than the
   window scrolls under it; content shorter leaves the foot at the bottom,
   never mid-window.
2. Resizing a window small never hides or clips the foot; the body shrinks
   and scrolls (Speak/Settings/Meetings at 372 px height — audit B's
   reproduction).
3. All 18 pullout kinds and the 8 correct direct windows are pixel-unchanged
   at default size (no regression from CSS ownership consolidation).
4. The contract tests fail on the pre-change tree and pass after.

## Test plan

- Web: new `__tests__` for FootSlotContext portal + sibling invariant;
  existing suites for SurfaceWindows/cores stay green; typecheck.
- Walk: Playwright — Settings, Meetings, Speak at 1440×900 default, small
  (560×372), and maximized; footer bounding-box y equals window bottom in
  all states.
