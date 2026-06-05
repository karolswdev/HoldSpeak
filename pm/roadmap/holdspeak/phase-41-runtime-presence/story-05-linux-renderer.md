# HS-41-05 — Linux renderer (notification + tray + overlay)

- **Project:** holdspeak
- **Phase:** 41
- **Status:** backlog
- **Depends on:** HS-41-03
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Native, portable, focus-safe presence on Linux — across X11/Wayland and
GNOME/KDE/XFCE — without a custom overlay where the platform forbids it.

## Scope

- In:
  - `FreedesktopPresenceRenderer` (optional extras — lazy behind the flag):
    - **Tier 1 (everywhere):** an in-place-updating **D-Bus notification**
      (`org.freedesktop.Notifications`, reuse the returned id via `replaces_id`,
      `transient` hint, a per-state icon) — coalesced on state-change, not per
      event — plus a **StatusNotifierItem** tray glyph (custom pixels in the
      accent). Degrade to notification-only when no tray host (GNOME w/o the
      AppIndicator extension).
    - **Tier 2 (X11 / wlroots only):** a frameless GTK-WebKit overlay of the
      `/presence` card; **not** attempted on Wayland-GNOME/KDE.
  - Optional extras in `pyproject.toml` (`PyGObject` / `dbus`); graceful Null
    fallback when absent.
  - Verification (D-Bus/SNI driven with fakes for CI; real-render notes) +
    screenshot evidence where capturable.
- Out:
  - macOS (HS-41-04).

## Acceptance criteria

- [ ] With the flag on (Linux), state drives an updating notification + a tray
      glyph; the overlay appears only on overlay-capable compositors.
- [ ] Never steals focus; deps absent ⇒ Null fallback; default suite unaffected.
- [ ] The Wayland-GNOME/KDE behavior (tray+notification, no overlay) is explicit.

## Notes

- The notification path is the baseline because it's the only thing that works
  on Wayland-GNOME/KDE; the tray glyph is the always-visible branded layer.
