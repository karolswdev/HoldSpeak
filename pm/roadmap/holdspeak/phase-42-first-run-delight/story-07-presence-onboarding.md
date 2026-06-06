# HS-42-07 — Presence onboarding

- **Project:** holdspeak
- **Phase:** 42
- **Status:** done (2026-06-06)
- **Depends on:** HS-42-01, HS-42-03
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 41 made desktop presence strong, but it's invisible unless you already know
the `HOLDSPEAK_DESKTOP_PRESENCE=1` flag + the optional extras + the platform
caveats. A first-run user never discovers it.

## Scope

- In:
  - A guided, optional presence step (in Setup / the Presence checklist row):
    detect availability + whether the `.[presence]` extra is installed (reading the
    `presence{}` block from `/api/setup/status` + `detect_presence_platform()`).
  - An **in-UI live preview** of the presence card (`/presence` content).
  - Honest tier explanation: macOS / X11 / wlroots → floating HUD; Wayland
    GNOME/KDE → tray + notification. The focus invariant in one short line.
  - The exact install commands when missing: `uv pip install -e '.[presence]'` +
    the Linux freedesktop typelibs.
- Out:
  - Turning presence on by default (stays opt-in).
  - New presence renderers (Phase 41 owns those).

## Acceptance criteria

- [x] The presence step shows availability + tier accurately per platform (via the
      Phase-41 detector through `/api/setup/status`), default-off; covered by the
      tier-rule test + the HS-42-01 presence-data tests.
- [x] A faithful in-UI HUD preview renders (the transient `/presence` is hidden at
      idle, so a styled preview + a "Preview the live HUD" link is the honest form).
- [x] The focus invariant + the exact install commands (extra + Linux typelibs) are
      shown when relevant.
- [x] Bundle rebuilt; only `web/src` committed; a screenshot of the section.
- [x] Default suite green; presence stays opt-in (flag-unset byte-identical).

## Test plan

- Unit: platform → tier display mapping (macOS HUD / Wayland tray / X11 HUD).
- Frontend: `cd web && npm run build && npm run shots`.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Cross-link the existing `docs/INTELLIGENT_TYPING_GUIDE.md` §11 "Desktop Presence"
  rather than re-documenting it.
