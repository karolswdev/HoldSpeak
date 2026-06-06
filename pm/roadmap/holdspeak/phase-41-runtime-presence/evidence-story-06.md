# Evidence — HS-41-06 — Documentation

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The user-facing documentation for desktop presence — how to turn it on, the
optional-extras install (incl. the Linux system typelibs), the per-platform
surfaces with **embedded screenshots from both OSes**, the honest Wayland
caveat, and the focus invariant.

### Primary section — `docs/INTELLIGENT_TYPING_GUIDE.md` §11 "Desktop Presence"

A new section (slug `#11-desktop-presence-ambient-on-desktop-status`) covering:

- **Turn it on** — `HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak` + `uv pip install
  -e '.[presence]'`; the Linux freedesktop typelibs as system packages
  (`gir1.2-notify-0.7` / `gir1.2-ayatanaappindicator3-0.1` for Tier-1;
  `gir1.2-gtk-3.0` / `gir1.2-webkit2-4.1` for the Tier-2 overlay). Explicit
  off-by-default / zero-dep-when-unset callout.
- **The states** — a table mapping the live runtime-activity states
  (`listening`/`recording`/`transcribing`/`processing`/`typing`/`complete`/
  `error`) to their labels, cross-checked against
  `holdspeak/runtime_activity.py::_DEFAULT_LABELS`; the `idle`-never-renders
  transient rule.
- **macOS** — the floating HUD (non-activating `NSPanel` + `WKWebView`) + the
  menu-bar glyph, with `assets/presence/macos-hud.png` +
  `macos-menubar-glyph.png`.
- **Linux** — the in-place notification + tray (Tier 1, everywhere) with
  `assets/presence/linux-notification.png`, and the GTK-WebKit floating HUD
  (Tier 2, X11/wlroots) with `assets/presence/linux-overlay.png`.
- **The Wayland caveat** — GNOME/KDE-Wayland block the overlay → Tier-1
  notification+tray is the native path there; the GNOME AppIndicator-extension
  wart documented. Matches `detect_presence_platform`'s `overlay_capable` logic.
- **The focus invariant** — the non-negotiable "never takes keyboard focus"
  rule, with the per-platform mechanism.

### Screenshots (real captures from HS-41-04/05/08, both OSes)

Copied from the phase evidence into `docs/assets/presence/`:

| File | Source evidence | Platform |
|---|---|---|
| `macos-hud.png` | `evidence/macos_presence_hud.png` | macOS HUD |
| `macos-menubar-glyph.png` | `evidence/macos_presence_glyph.png` | macOS menu-bar glyph |
| `linux-notification.png` | `evidence/linux_presence_notification.png` | Linux (`.43`/GNOME) notification |
| `linux-overlay.png` | `evidence/linux_presence_overlay.png` | Linux (`.43`/X11) floating HUD |

### Cross-links

- `README.md` — a **Desktop presence** bullet in "What it does" + a row in
  "Where to go next".
- `docs/README.md` — a Desktop Presence sub-bullet under the Intelligent Typing
  Guide entry.
- `docs/GETTING_STARTED.md` — a tip after "Try Basic Voice Typing" pointing at
  the §11 section.

## Tests run

```
uv run pytest -q tests/unit/test_doc_drift_guard.py
3 passed in 0.03s
```

`test_doc_drift_guard.py` is the doc-truth + live-doc link-check guard. It
resolves every relative markdown link **and image path** in the live `docs/`
set — so the four embedded `assets/presence/*.png` are proven to exist on disk,
and no doc links a dangling path. Green.

## Acceptance criteria

- [x] Enabling + per-platform behavior documented, incl. the Wayland caveat +
      the optional-extras install.
- [x] Screenshots embedded (macOS HUD/glyph + Linux notification/overlay);
      doc-guards + link-check green.
- [x] Every documented surface matches what shipped in HS-41-01…05/08
      (states ← `runtime_activity`; overlay-capability ← `detect_presence_platform`;
      extras ← `pyproject` `presence`; typelibs ← the renderer modules).
