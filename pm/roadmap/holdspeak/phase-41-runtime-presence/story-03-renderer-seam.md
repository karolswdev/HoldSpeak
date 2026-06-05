# HS-41-03 — Renderer Protocol + host selection + `/presence` route

- **Project:** holdspeak
- **Phase:** 41
- **Status:** backlog
- **Depends on:** HS-41-01, HS-41-02
- **Unblocks:** HS-41-04, HS-41-05
- **Owner:** unassigned

## Problem

The desktop presence layer needs a clean seam so each platform plugs in its own
native renderer, and a content source for the webview HUD.

## Scope

- In:
  - `holdspeak/desktop_presence.py`: the `PresenceRenderer` Protocol
    (`show`/`update`/`hide`/`close`), `NullPresenceRenderer`, a
    `DesktopPresenceHost` applying the window policy (active/linger/hidden +
    linger timers), `desktop_presence_enabled(env)`, and
    `build_desktop_presence_host()` that **probes the platform/compositor** and
    returns the best available renderer (or None). Salvage the host/policy logic
    from the codex spike **minus** the Tk renderer.
  - A minimal **`/presence`** web route — a transparent-bg, HUD-sized page that
    renders just the Signal presence card, driven by the `runtime_activity`
    websocket (the content the Tier-2 webview HUD loads).
  - Wire the host into `web_runtime._broadcast_runtime_activity` (fan-out to the
    web broadcast + the desktop host).
  - Tests: host policy (show/update/hide/linger), enabled-flag parsing, env
    probing, the `/presence` route.
- Out:
  - The actual macOS/Linux native renderers (HS-41-04/05).

## Acceptance criteria

- [ ] The Protocol + Null renderer + host + env probe exist; with the flag off,
      `build_desktop_presence_host()` returns None and nothing renders.
- [ ] `/presence` serves the card and updates live over the websocket.
- [ ] Default suite green with **no** GUI dep imported (Null path); off-by-default
      byte-identical.
- [ ] The focus invariant is encoded as a requirement for the native renderers.

## Notes

- Env probe: `darwin` → mac tier; Linux → detect `WAYLAND_DISPLAY` +
  compositor (wlroots vs GNOME/KDE) to choose overlay-capable vs tray-only.
