# Evidence — HS-41-03 — Renderer Protocol + host + `/presence` route

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The desktop seam the native renderers (HS-41-04/05) plug into, plus the HUD
content they'll display — **still zero native deps**.

- `holdspeak/desktop_presence.py` (salvaged from codex PR #17 **minus Tk**):
  - `PresenceRenderer` Protocol (`show`/`update`/`hide`/`close`) +
    `NullPresenceRenderer`.
  - `DesktopPresenceHost` — applies the transient window policy: idle hides,
    active shows + updates in place, terminal states linger then hide, a new
    event cancels a pending linger (injectable `timer_factory`).
  - `build_presence_window_view()` — the renderer-ready, **secret-redacted**
    projection (tone/label/detail/accent) for native surfaces that can't use the
    web design tokens (a tray glyph color, a notification icon).
  - `desktop_presence_enabled(env)` (the opt-in flag).
  - **`detect_presence_platform()`** (new) — probes OS + (on Linux) display
    server / compositor → `{os, wayland, compositor, overlay_capable}`.
    `overlay_capable` is False on mainstream Wayland (GNOME/KDE), True on macOS /
    X11 / wlroots — encoding the Wayland reality in code.
  - `build_desktop_presence_host()` — flag-gated; selects the best native
    renderer (none registered yet → returns None, so the web card stays the
    surface); defensive (a renderer that raises falls back to None).
- `holdspeak/web_runtime.py` — re-wired the host into the runtime: built in
  `__init__` (None unless the flag is on), fanned out from
  `_broadcast_runtime_activity` alongside the web broadcast, and closed on
  shutdown.
- **`/presence`** — `web/src/pages/presence.astro` (a chromeless, transparent,
  Signal-token-styled HUD page, **no AppLayout**) + `web/src/scripts/presence-app.js`
  (tiny, framework-free: seeds from `/api/state`, renders the card from
  `runtime_activity` WS messages, hides on the idle/hidden policy,
  auto-reconnects) + the `GET /presence` route in `web/routes/pages.py`. This is
  the exact content the native webview (HS-41-04/05) loads in a frameless window.

## Verification artifacts

> `uv run` is broken on this machine; tests run via `.venv/bin/python -m pytest`.

- **Live HUD capture:** `GET /presence` → `200`; driven by a `transcribing`
  activity snapshot the card renders (`visible: True · label: Transcribing ·
  tone-working`). Screenshot `evidence/presence_hud.png` — a rounded Signal
  surface (elev-3) on a transparent window, blue working ring, "Transcribing" +
  detail + `Hotkey` source. (When hosted in a native NSPanel/GTK window the OS
  adds rounding/shadow; the content is already this polished card.)
- Targeted: `.venv/bin/python -m pytest -q tests/unit/test_desktop_presence.py
  tests/unit/test_web_runtime.py tests/unit/test_web_presence_indicator.py`
  → all green (16 host/policy/probe/view + the desktop-fan-out + 3 HUD route/driver).
- Ruff (touched files) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2245 passed, 16 skipped` (2228/16 at HS-41-02; +17).
- Bundle rebuilt (`/presence/index.html`); `git status` shows **no** `_built/`.

## Acceptance criteria — re-checked

- [x] Protocol + Null renderer + host + env probe exist; flag off →
      `build_desktop_presence_host()` is None and nothing renders —
      `test_build_host_none_when_flag_off`, `..._none_when_no_native_renderer`.
- [x] `/presence` serves the card + updates live over the websocket —
      `test_presence_route_serves_the_hud` + the live capture.
- [x] Default suite green, **no GUI dep imported** (Null path); off-by-default
      byte-identical (the existing `web_runtime` tests pass; host is None in tests).
- [x] The focus invariant is encoded as a requirement for the native renderers
      (phase status doc + the macOS/Linux story acceptance criteria).

## Deviations from plan

- Kept `build_presence_window_view` + `_STATE_META` (the codex spike's
  renderer-ready, secret-redacting view) — it's renderer-agnostic and the native
  glyph/notification color source, so it earns its place even though the webview
  HUD uses CSS tokens.
- `detect_presence_platform` takes a `platform_name` override so the Linux /
  Wayland / wlroots branches are unit-testable on this macOS host.
