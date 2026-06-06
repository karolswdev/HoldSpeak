# HS-41-06 — Documentation

- **Project:** holdspeak
- **Phase:** 41
- **Status:** done
- **Depends on:** HS-41-01, HS-41-02, HS-41-03, HS-41-04, HS-41-05
- **Unblocks:** HS-41-07
- **Owner:** unassigned

## Problem

Users need to know presence exists, how to turn it on, what they'll see per
platform, and the honest Wayland caveat.

## Scope

- In:
  - A user-facing section (in the intelligent-typing / getting-started guide):
    enable with `HOLDSPEAK_DESKTOP_PRESENCE=1`; the per-platform surfaces
    (macOS HUD + glyph; Linux notification + tray; the Wayland-GNOME/KDE
    tray-only reality); the optional-extras install note.
  - Screenshots (macOS HUD/glyph; Linux notification/tray).
  - Doc drift-guard + link-check green.
- Out:
  - Marketing copy (closeout/README hero if needed).

## Acceptance criteria

- [x] Enabling + per-platform behavior documented, incl. the Wayland caveat +
      the optional-extras install. (`docs/INTELLIGENT_TYPING_GUIDE.md` §11)
- [x] Screenshots embedded (macOS HUD/glyph + Linux notification/overlay);
      doc-guards + link-check green (`test_doc_drift_guard.py` 3 passed).
- [x] Every documented surface matches what shipped in 01–05/08.
