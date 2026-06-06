# Evidence — HS-41-08 — Linux GTK-WebKit floating overlay

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The macOS HUD's **twin on Linux** — the rich floating Signal card, on
overlay-capable compositors (X11/wlroots). Same `/presence` webview, so it's the
same design on both platforms.

- `holdspeak/desktop_presence_gtk.py` (gi/Gtk3/WebKit2, lazy, behind the flag):
  - `_GtkWebKitOverlay` — a GTK3 `POPUP` window (override-redirect, keep-above,
    skip-taskbar/pager, **non-focus** `set_accept_focus(False)` /
    `set_focus_on_map(False)`, NOTIFICATION type hint, transparent RGBA visual,
    **click-through** via an empty input shape) hosting a `WebKit2.WebView` of
    the local `/presence` URL, positioned top-right.
  - `GtkOverlayRenderer` — drives it in a **fork** child process (GTK owns its
    main loop; the parent never touches GTK so fork is clean), lazy-started on
    first show. `gtk_overlay_available()` probes Gtk + a WebKit2 typelib.
- `holdspeak/desktop_presence_freedesktop.py` — when `overlay_capable`, the
  renderer builds the overlay (gi available) and shows/hides it **alongside** the
  notification; injectable + skipped on non-overlay-capable compositors.
- `scripts/presence_linux_overlay_smoke.py` — the cross-host live harness.

## Verification artifacts

- **LIVE on real Linux** (`.43` — Ubuntu 24.04.2 LTS, GNOME on **X11**, WebKit2
  4.1 + Gtk3): the actual `GtkOverlayRenderer` ran on `.43`, its WebView pointed
  at the Mac's `/presence` over an **SSH reverse tunnel** (`-R` — the Mac server
  stays loopback-only/auth-gated; no LAN bind, no firewall hole). It rendered the
  **floating Signal card** — `evidence/linux_presence_overlay.png`: a blue
  "Transcribing" ring, "Transcribing", *"Turning your speech into text…"*,
  `Hotkey`, floating over the desktop. `overlay_available: True` on `.43`. The
  exact same card as the macOS HUD, now a GTK3 window on X11.
- Unit (no GUI, injected fake overlay): `tests/unit/test_desktop_presence_freedesktop.py`
  — the overlay is shown/hidden/closed alongside the notification when injected
  + `overlay_capable`, and is **never built** when not `overlay_capable`
  (GNOME-Wayland → notification + tray only).
- Ruff (touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  `2261 passed, 16 skipped` (2259/16 at HS-41-05; +2). No GUI dep in the default
  suite (overlay only on overlay-capable Linux with gi present).

## Acceptance criteria — re-checked

- [x] On an overlay-capable Linux session the GTK-WebKit overlay renders the
      `/presence` Signal card — the live `.43` capture.
- [x] Only built when `overlay_capable` + gi Gtk/WebKit2 present; graceful
      fallback to notification-only otherwise —
      `test_overlay_not_used_when_not_overlay_capable`.
- [x] Live capture on `.43` (Ubuntu/X11) — `evidence/linux_presence_overlay.png`.
- Focus-safety: the window is a `POPUP` with `accept_focus`/`focus_on_map` False
  (non-focus by construction), so injected keystrokes keep landing in the target
  app — same invariant as the macOS panel.

## Deviations from plan

- The GTK child uses **fork** (Linux default) rather than spawn — fork is clean
  here (the parent never imports gi) and avoids spawn's `__main__` re-import
  (which broke the stdin-run live driver). The macOS Cocoa renderer keeps spawn
  (fork + AppKit is unsafe).
- Live capture used an SSH reverse tunnel to keep the Mac server loopback-only
  (the auth gate refuses a non-loopback bind without a token — correctly).
