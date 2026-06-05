# HS-41-05 — Linux renderer (notification + tray + overlay)

- **Project:** holdspeak
- **Phase:** 41
- **Status:** done (2026-06-05) — Tier-1 (notification + tray); the GTK-WebKit overlay is a deferred X11/wlroots-only follow-up
- **Depends on:** HS-41-03
- **Unblocks:** none
- **Owner:** unassigned
- **Evidence:** [evidence-story-05.md](./evidence-story-05.md)

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

- [x] With the flag on (Linux), state drives an updating notification + a tray
      glyph. (The overlay's *selection* is plumbed via `overlay_capable`; the
      concrete GTK-WebKit overlay window is a deferred X11/wlroots-only follow-up.)
- [x] Never steals focus (notification/tray are focus-safe by spec); deps absent
      ⇒ graceful fallback; default suite unaffected.
- [x] The Wayland-GNOME/KDE behavior (tray+notification, no overlay) is explicit.

## Outcome

`FreedesktopPresenceRenderer` (PyGObject, lazy) — an in-place-updating libnotify
notification (coalesced on state change) + a StatusNotifierItem tray glyph,
focus-safe and portable across X11/Wayland + GNOME/KDE/XFCE. Pure
`notification_for_view` + injectable seams → fully unit-tested with fakes on
macOS; graceful fallback verified (`freedesktop_presence_available()` False
here). The Tier-2 floating GTK-WebKit overlay is deferred (X11/wlroots-only,
un-verifiable on macOS). Suite 2259/16. See [evidence-story-05.md](./evidence-story-05.md).

## Notes

- The notification path is the baseline because it's the only thing that works
  on Wayland-GNOME/KDE; the tray glyph is the always-visible branded layer.
