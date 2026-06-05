# HS-40-02 — Desktop Presence Host

- **Project:** holdspeak
- **Phase:** 40
- **Status:** implemented in `/tmp`
- **Depends on:** HS-40-01
- **Unblocks:** HS-40-03, HS-40-06
- **Owner:** unassigned

## Problem

The user may run `holdspeak` in the background and voice type into arbitrary
apps without watching the web dashboard. The runtime needs a small desktop
presence host that can subscribe to HoldSpeak's local activity stream and show
native-like macOS/Linux status windows when dictation or meeting activity
changes.

## Scope

- **In:**
  - Pick and document the desktop substrate for Phase 40. Keep it optional so
    headless/server installs and CI are not forced to load GUI libraries.
  - Add a small host process/module that connects to the local web runtime
    (`/api/runtime/status` + `/ws`) and receives `runtime_activity` events.
  - Define lifecycle ownership: started by the web runtime when enabled, stops
    when the runtime stops, reconnects if websocket drops.
  - Add config/env knobs for enable/disable and fallback behavior.
  - Degrade cleanly to web-only status when no GUI desktop session/toolkit is
    available.
- **Out:**
  - A full settings/preferences app.
  - Persistent tray/menu-bar replacement.
  - OS notification center as the primary UX.
  - Changing hotkey, audio, typing, meeting, or plugin ownership.

## Acceptance Criteria

- [ ] A desktop presence host can be enabled without changing the default
      background/runtime behavior.
- [ ] GUI dependencies are optional and skipped cleanly when unavailable.
- [ ] The host loads the initial activity snapshot from `/api/runtime/status`
      and receives live `runtime_activity` websocket events.
- [ ] Websocket disconnect/reconnect does not leave a stale window state.
- [ ] On unsupported/headless sessions, the runtime logs a clear fallback and
      continues web-only.
- [ ] Unit tests cover host state handling with fake status/websocket inputs.

## Test Plan

- Unit: host reducer / reconnect / fallback behavior with fake transports.
- Integration: runtime starts with desktop host disabled (default) and enabled
  with a fake renderer.
- Platform smoke: macOS and Linux manual or CI-available smoke if possible.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / Open Questions

- 2026-06-05 — Implemented in `/tmp`: `holdspeak/desktop_presence.py` adds the
  optional desktop presence host, null renderer fallback, env-gated Tk renderer,
  and transient show/update/linger/hide host behavior. Focused tests cover
  hidden idle state, linger cancellation, env gating, and renderer handoff.
- Substrate options to evaluate in-story:
  - a lightweight Python GUI/webview dependency with native windows;
  - a tiny platform adapter boundary (`macos`, `linux`) if one cross-platform
    option is not reliable enough;
  - OS notifications only as fallback, not as the main experience.
- Avoid reintroducing the retired `rumps` menubar runtime. This host is a
  status subscriber, not a second interactive runtime.
