# HS-40-04 — Web Cockpit Reference Indicator

- **Project:** holdspeak
- **Phase:** 40
- **Status:** implemented in `/tmp`
- **Depends on:** HS-40-01
- **Unblocks:** HS-40-05, HS-40-06
- **Owner:** unassigned

## Problem

Even with native windows, the web dashboard should remain the reference and
debug surface for HoldSpeak status. It should render the same presence contract
so users can see exactly what the desktop host is reacting to.

## Scope

- **In:**
  - Add a persistent activity indicator to `web/src/pages/index.astro`, driven
    by `HoldSpeakDashboard()` in `web/src/scripts/dashboard-app.js`.
  - Consume initial state from `/api/runtime/status.activity` and live
    `runtime_activity` websocket updates.
  - Render state dot/ring, label, detail, last event age, and last error.
  - Use existing Signal tokens; pulse only the dot/ring; respect reduced
    motion.
  - Keep dimensions stable across labels and mobile/desktop breakpoints.
- **Out:**
  - Broad dashboard redesign.
  - Native renderer implementation.
  - Dictation/meeting mapping beyond whatever HS-40-01 already emits.

## Acceptance Criteria

- [ ] The web dashboard shows the same current activity state as the desktop
      host.
- [ ] Websocket reconnect falls back to `/api/runtime/status` without leaving
      stale state.
- [ ] The indicator has an accessible status region (`role="status"` or
      equivalent polite update pattern).
- [ ] No text overlaps or button/control layout shifts on desktop or mobile.
- [ ] Existing meeting controls, transcript stream, and pending-actions panel
      remain usable.

## Test Plan

- Frontend: dashboard message handling tests or Playwright fixture states.
- Build: web bundle build command from `web/package.json`.
- Screenshots: captured under HS-40-06.

## Notes / Open Questions

- The web indicator is also the fallback UX when the desktop host cannot run.
  It should therefore explain desktop-host disabled/unavailable states when
  that diagnostic is exposed.
- 2026-06-05 — Implemented in `/tmp`: `dashboard-app.js` now keeps
  `runtimeActivity`, consumes `/api/runtime/status.activity`, falls back through
  `state.activity` / `state.runtime.activity`, and handles live
  `runtime_activity` websocket messages. `/` now renders a compact hero
  presence card with state ring, label, detail, source, and desktop-window
  mode. `npm run build` and `npm run shots` pass, with evidence captured under
  HS-40-06.
