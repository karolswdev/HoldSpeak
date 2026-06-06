# HS-41-08 — Linux GTK-WebKit floating overlay (X11/wlroots)

- **Project:** holdspeak
- **Phase:** 41
- **Status:** done (2026-06-05) — live-captured on `.43` (Ubuntu/X11)
- **Depends on:** HS-41-03, HS-41-05
- **Unblocks:** none
- **Owner:** unassigned
- **Evidence:** [evidence-story-08.md](./evidence-story-08.md)

## Problem

HS-41-05 shipped the everywhere-portable Linux Tier-1 (notification + tray). On
**overlay-capable** compositors (X11, wlroots) the macOS-HUD twin — a rich
**floating webview of the Signal card** — is also possible. `.43` is Ubuntu
24.04 on **X11** with WebKit2 4.1 + Gtk3, so it's buildable + capturable.

## Scope

- In:
  - `holdspeak/desktop_presence_gtk.py`: `_GtkWebKitOverlay` — a GTK3 `POPUP`
    window (override-redirect, keep-above, skip-taskbar/pager, **non-focus**,
    transparent RGBA, **click-through** via an empty input shape) hosting a
    `WebKit2.WebView` of the local `/presence` URL, positioned top-right. Driven
    in a child process (GTK owns its main loop), lazy-started on first show.
    `GtkOverlayRenderer` wraps it for `FreedesktopPresenceRenderer`.
  - Wire it into `FreedesktopPresenceRenderer`: when `overlay_capable`, the
    overlay is shown/hidden alongside the notification.
  - Selection/availability (`gtk_overlay_available()` = gi Gtk+WebKit2).
  - Live build + capture on `.43`.
- Out:
  - Wayland-GNOME/KDE (overlay impossible there — Tier-1 only; unchanged).

## Acceptance criteria

- [x] On an overlay-capable Linux session the GTK-WebKit overlay renders the
      `/presence` Signal card; **focus is not stolen** (POPUP + accept_focus
      False).
- [x] Only built when `overlay_capable` + gi Gtk/WebKit2 present; graceful
      fallback to notification-only otherwise.
- [x] Live capture on `.43` (Ubuntu/X11) — `evidence/linux_presence_overlay.png`.

## Outcome

`desktop_presence_gtk.py` — a GTK3 `POPUP` (override-redirect, keep-above,
non-focus, transparent, click-through) hosting a `WebKit2.WebView` of `/presence`,
fork-child-driven, wired into `FreedesktopPresenceRenderer` when `overlay_capable`.
**Live-captured on `.43`** (Ubuntu/X11): the same Signal card as the macOS HUD,
floating over the desktop, served from the Mac over an SSH reverse tunnel. Suite
2261/16. See [evidence-story-08.md](./evidence-story-08.md).

## Test plan

- Unit (no GUI): overlay selected only when overlay_capable + available; the
  renderer wires/skips it; injectable.
- Live: run on `.43` pointed at a LAN `/presence`, capture the overlay window.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
