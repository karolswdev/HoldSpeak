# Evidence — HS-41-05 — Linux renderer (notification + tray)

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The native, focus-safe, **everywhere-portable** Linux presence surface — the
Tier-1 path that works on X11 *and* Wayland, GNOME/KDE/XFCE alike (the desktops
where a floating overlay is impossible), using the two freedesktop standards
that never steal keyboard focus:

- `holdspeak/desktop_presence_freedesktop.py` (PyGObject, lazy-imported behind
  the flag):
  - `notification_for_view()` — pure projection of a presence view into
    notification fields (summary `HoldSpeak — {label}`, body, per-state
    freedesktop icon, urgency, `transient`).
  - `FreedesktopPresenceRenderer` (a `PresenceRenderer`) — an **in-place-updating
    desktop notification** (one notification, `update()`d as state changes) +
    a **StatusNotifierItem tray glyph** (Ayatana/AppIndicator) keyed to state.
    **Coalesced**: re-notifies only on a *state change* (the tray still refreshes
    each event) so a burst of same-state updates doesn't spam. Real gi seams
    (`_LibnotifyNotifier`, `_AppIndicatorTray`) are **lazy** + injectable;
    graceful fallback when libnotify/PyGObject is absent.
- `holdspeak/desktop_presence.py` — `_select_presence_renderer` picks the
  freedesktop renderer on Linux when libnotify is available, passing the
  `overlay_capable` flag from the platform probe.
- `pyproject.toml` — the `presence` extra gains `PyGObject` (linux-gated; the
  libnotify/AppIndicator typelibs are system packages, documented in HS-41-06).

### Honest scope: the floating overlay is deferred

The Tier-2 free-floating **GTK-WebKit overlay** of `/presence` (the macOS HUD's
analog) is only possible on **X11 + wlroots** compositors — *not* on mainstream
Wayland (GNOME/KDE), where the compositor blocks arbitrary overlays. On the
dominant Linux desktops the notification + tray **is** the native experience, so
that's the HS-41-05 deliverable. The overlay is plumbed (`overlay_capable` flows
to the renderer) but the concrete GTK window is **deferred** rather than ship
untested GUI code I can't verify on this macOS host — it's an X11/wlroots-only
extra for a later pass (noted in the status doc).

## Verification artifacts

- **LIVE on real Linux** (`.43` — Ubuntu 24.04.2 LTS, GNOME on X11): the actual
  `FreedesktopPresenceRenderer` was run over SSH against the live `:0` session
  (its system `python3` + gi). `freedesktop_presence_available()` → **True**
  there; the renderer showed a real notification and built the tray
  (`shown: transcribing | tray: yes` — `AppIndicator3` is present). Capture:
  `evidence/linux_presence_notification.png` — a real GNOME banner from the
  renderer: the HoldSpeak app icon (the transcribing → `emblem-synchronizing`
  icon), **"HoldSpeak — Transcribing"**, *"Turning your speech into text…"*.
  (GNOME's Do-Not-Disturb was briefly toggled to surface the banner, then
  restored to its prior value; temp files cleaned up.)
- Availability on the dev host (macOS): `freedesktop_presence_available()` →
  **False** (PyGObject absent) → the renderer is not selected → the web card
  stays the surface. The graceful-degradation path is real here.
- Unit (injected fake notifier/tray, no gi): `tests/unit/test_desktop_presence_freedesktop.py`
  — the field mapping (recording → mic icon/normal urgency/transient; error →
  dialog-error/critical/persistent), notify+tray on show, **coalesce** (same
  state → one notification, tray still refreshed), re-notify on state change,
  hide idles the tray + closes the notification, and the Linux selection /
  no-libnotify fallback.
- **Best-effort tray** (a fix this surfaced): the AppIndicator typelib is missing
  on stock GNOME without the extension, so `_ensure_started` builds the
  notification (required) and the tray (best-effort → notification-only when the
  typelib/host is absent) rather than failing the whole renderer.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  `2259 passed, 16 skipped` (2251/16 at HS-41-04; +8). No GUI dep in the default
  suite (Linux renderer not selected on macOS).

## Acceptance criteria — re-checked

- [x] With the flag on (Linux), state drives an updating notification + a tray
      glyph — `test_renderer_notifies_and_sets_tray_on_show`,
      `test_renderer_notifies_again_on_state_change`.
- [x] Never steals focus (notifications + tray are focus-safe by spec); deps
      absent ⇒ graceful fallback; default suite unaffected.
- [x] The Wayland-GNOME/KDE behavior (tray + notification, **no** overlay) is
      explicit — the overlay is gated on `overlay_capable` and deferred.
- [~] The floating overlay "appears only on overlay-capable compositors" — the
      *selection* is plumbed; the concrete GTK-WebKit overlay window is a
      documented X11/wlroots-only follow-up (not built untested).

## Deviations from plan

- The Tier-2 GTK-WebKit overlay is deferred — but note `.43` is **X11** (and has
  `WebKit2 4.1` + `Gtk3`), so the overlay *is* buildable there; it's teed up as a
  fast follow-up rather than shipped untested. The notification + tray is the
  everywhere-portable deliverable and is now **live-verified** on real GNOME.
