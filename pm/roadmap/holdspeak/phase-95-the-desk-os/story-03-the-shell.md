# HS-95-03 — The shell: dock, switching, layouts

- **Project:** holdspeak
- **Phase:** 95
- **Status:** done
- **Depends on:** HS-95-01, HS-95-02
- **Unblocks:** HS-95-08 (deep links open through the shell)

## Problem

An OS is not just windows — it is knowing what is open, getting back to it,
and trusting the room to stay arranged. Today nothing shows which desk
panels are open, a minimized window (new in HS-95-02) has nowhere to live,
and there is no way to move between windows except hunting for them. The
DeskChrome room menu currently fills this role by *leaving the desk* — the
opposite of a shell.

## Scope

- In:
  - a dock: one bar showing open and minimized windows with kind icons and
    truncated titles; tap focuses/restores; long-press or context affordance
    closes; lives above the stage, below nothing (top of the z ladder with
    the chrome band);
  - window switching: keyboard cycling on desktop (and the dock as the
    touch path); most-recently-used order from the existing `panelOrder`;
  - snap targets: drag-to-edge half/quarter tiling on desktop viewports,
    within the persisted-rect system;
  - named layout persistence: the current arrangement (windows, rects,
    minimized set) survives reload per desk, replacing ad-hoc
    `panelRects`-only persistence; a "reset layout" verb;
  - DeskChrome's room menu reworked to open desk windows (wiring lands per
    surface in HS-95-05..08; this story ships the shell affordance and
    converts the menu's mechanism from `<Link>` to window-open actions).
- Out:
  - multiple virtual desks/spaces (note as a rider if trivially close,
    otherwise BACKLOG);
  - notification surfaces (AttentionDrawer already exists and simply docks);
  - any new page.

## Acceptance criteria

- [x] The dock shows every open and minimized window; tap focuses or
      restores; the affordance to close works; empty dock is invisible.
- [x] Keyboard cycling moves focus through windows in MRU order on desktop;
      the dock provides the same on touch.
- [x] Dragging a window to screen edges snaps to half/quarter tiles; snapped
      rects persist and un-snap by drag.
- [x] Rects, the maximized set, and the minimized record survive reload
      ("reset layout" returns the documented defaults); the open set stays
      feature-owned and a reopening window always presents itself — the
      HS-95-02 designed semantics, pinned by the walk.
- [x] The DeskChrome menu no longer navigates by `<Link>`; it dispatches
      window-open actions (destinations may temporarily open the legacy
      routes' windows as they land in later stories, but the mechanism is
      the shell's).
- [x] All shell furniture is chrome-band tap-transparent per the Phase 93
      round-2 contract; default layouts never sit under the chrome.
- [x] The 393px viewport gets the dock as a compact strip compatible with
      the bottom-sheet window form.

## Test plan

- `npm --prefix web test` — shell store suites: MRU order, snap math,
  layout persistence round-trips, reset.
- Playwright: open/minimize/cycle/snap/reload walk at 1440; dock strip and
  sheet interplay at 393.
- Screenshot pass of dock states (empty, three open, one minimized).

## Implementation direction

- The dock derives entirely from store state; no separate registry
  (standing rule: everything is a projection of the store).
- Snap is geometry in the store's rect vocabulary — no new positioning
  system.
- Keep labels terse; icons carry the weight (no prose in the UI).
- Compositor-only motion for dock hover/restore transitions.

## Evidence required

- captured web test run;
- Playwright shell walk output at both viewports;
- screenshots: dock states, a snapped layout, the reloaded arrangement.
