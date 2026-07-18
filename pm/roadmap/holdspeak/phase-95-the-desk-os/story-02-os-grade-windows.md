# HS-95-02 — OS-grade windows

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-95-03, HS-95-04, HS-95-05, HS-95-06, HS-95-07, HS-95-08

## Problem

Phase 93's `useDeskWindow` hook gives panels drag, resize, persist, raise,
and coexist — but it is a hook each panel hand-wires (`setEl`,
`handleProps`, `style`, `grip`, its own open gate). There is no
`<DeskWindow>` container with a content slot, so hosting arbitrary content
in a window is not possible, and the nine existing consumers each carry
their own copy of the wiring. There is also no window lifecycle beyond
open/closed: no minimize, no restore, no maximize, no consistent close
affordance — table stakes for the OS feel the owner demands.

## Scope

- In:
  - a `<DeskWindow id title icon …>{children}</DeskWindow>` container over
    the existing hook: one chrome (head, close, minimize, maximize/restore),
    one focus/z behavior, one persisted-rect behavior, a content slot that
    accepts arbitrary React children;
  - window lifecycle in the desk store: open, focus, minimize, restore,
    maximize, close; `panelRects`/`panelSaved`/`panelOrder` extended, all
    persisted in the existing `hs.desk.panels` slot;
  - motion-driven open/close/minimize transitions (the `motion` dependency
    is already present) within the interaction budget;
  - migration of all nine hand-wired panels (ask, attention, delivery-board,
    delivery-terminal, delivery-dossier, inspector, chat, pullout, session)
    onto the container — no panel keeps private wiring;
  - the phone form: on narrow viewports a window presents as the Phase 93
    round-2 bottom sheet, from the same component and state.
- Out:
  - the dock/taskbar and window switching (HS-95-03);
  - page-core content (HS-95-04 onward);
  - any weakening of the Phase 93 physics contract — drag, resize, persist,
    raise, coexist, tap-transparent chrome band, the 72px grabbable clamp
    strip, and the cascade are the regression floor.

## Acceptance criteria

- [ ] `<DeskWindow>` hosts arbitrary children with one shared chrome; a new
      window is added with no wiring beyond `id`, `title`, and children.
- [ ] Minimize, restore, maximize, and close work on every window; state
      survives reload via the existing persistence slot.
- [ ] All nine existing panels render through the container; the hook is no
      longer exported for hand-wiring; behavior parity is proven by the
      existing desk interaction tests passing unmodified or with
      mechanical-only updates.
- [ ] Drag/resize/persist/raise/coexist/cascade/clamp behave exactly per the
      Phase 93 contract (regression suite green).
- [ ] Open/minimize/close transitions run compositor-only (transform/opacity;
      no layout thrash in DevTools).
- [ ] At 393px every window presents as a bottom sheet with the same content
      and lifecycle.
- [ ] No modal anywhere: windows coexist and never trap focus globally
      (standing rule: edit in-world, no modals).

## Test plan

- `npm --prefix web test` — desk window/store suites (extended for
  lifecycle transitions and persistence round-trips).
- Playwright: open three windows, minimize one, maximize one, reload,
  assert restored geometry and states; run at 1440 and 393.
- Visual: screenshot pass on the shared chrome across all nine migrated
  panels.

## Implementation direction

- Build the container on top of `useDeskWindow`, then fold the hook private.
  Do not fork the physics; extend the store actions
  (`setPanelRect`/`focusPanel`) with lifecycle state rather than adding a
  parallel mechanism.
- Chrome verbs are icons with accessible labels, not prose (standing rule:
  labels state WHAT in fewest words).
- Minimized windows park their state, not their mount, unless the content
  opts into unmount (heavy cores from HS-95-04 will want unmount-on-minimize
  — design the slot API for both).
- Keep the z ladder documented in `desk.css` current as the single place the
  ladder is written down.

## Evidence required

- captured web test run including new lifecycle suites;
- Playwright lifecycle walk output at both viewports;
- screenshots of the one chrome across all nine panels;
- the diff showing the nine panels' private wiring deleted.
