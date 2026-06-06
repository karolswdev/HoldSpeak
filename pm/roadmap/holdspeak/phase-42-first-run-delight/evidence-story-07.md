# Evidence — HS-42-07 — Presence onboarding

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

A guided presence step on `/setup` that makes the Phase-41 desktop presence
**discoverable** — availability + the honest per-platform tier, a faithful HUD
preview, the focus invariant, and the exact enable commands.

### The section — `web/src/pages/setup.astro` + `setup-app.js`

`#presence-setup` ("Desktop presence (optional)") driven by the
`/api/setup/status` `presence{}` block:

- **Status pill** — On · Available · off · Not on this platform (from
  `presence.enabled`/`available`).
- **Plain intro** — "see what the copilot is doing (listening · transcribing ·
  typing) while you dictate into another app."
- **Honest tier text** (`presenceTier`, from `presence.os`/`wayland`/`tier`):
  - macOS → "A floating HUD of the Signal card + a menu-bar glyph."
  - Linux X11/wlroots → "A floating HUD + a tray glyph + an in-place notification."
  - Linux Wayland GNOME/KDE → "A tray glyph + an in-place notification (your
    compositor blocks floating overlays)."
- **The focus invariant** in one line — "🔒 It never takes keyboard focus — your
  keystrokes keep landing in the app you're typing into."
- **Enable commands** (shown when off, copyable): `HOLDSPEAK_DESKTOP_PRESENCE=1
  holdspeak` + `uv pip install -e '.[presence]'` (+ the Linux freedesktop
  typelibs `gir1.2-notify-0.7 …` when `os == linux`).
- A **faithful inline HUD preview** (the dark Signal card — orange ring +
  "Transcribing / Turning your speech into text… / Hotkey" — tagged "Preview",
  since `/presence` is transient/hidden at idle), plus **Presence docs** and
  **Preview the live HUD ↗** (`/presence`) links.

Restrained: the preview reuses the Signal palette; no new asset.

## Verification

- **Live (Playwright):** on macOS the section read status **"Available · off"**
  and tier **"A floating HUD of the Signal card + a menu-bar glyph."**
  Screenshot: [`evidence/setup_presence_onboarding.png`](./evidence/setup_presence_onboarding.png)
  — the copy + tier + focus line + enable commands + the inline HUD preview.

## Tests run

```
uv run pytest -q tests/integration/test_web_presence_onboarding.py
→ 2 passed
```

- `test_setup_page_has_presence_onboarding` — the section, the focus invariant,
  and the inline HUD preview ship in the built `/setup` (build-agnostic).
- `test_presence_tier_and_install_rules` — the platform→tier rules (macOS HUD +
  glyph vs Wayland tray + notification) and the enable/extra/typelib commands.

The presence platform/tier **data** is Python-tested in HS-42-01
(`test_setup_status.py::test_presence_tier_*`). Full suite: see the commit message.

## Acceptance criteria

- [x] The presence step shows availability + tier accurately per platform (via
      the Phase-41 detector through `/api/setup/status`); default-off; covered by
      the tier-rule test + the HS-42-01 presence-data tests.
- [x] A faithful in-UI HUD preview renders (the transient `/presence` is hidden at
      idle, so a styled preview + a "Preview the live HUD" link is the honest form).
- [x] The focus invariant + the exact install commands (extra + Linux typelibs)
      are shown when relevant.
- [x] Bundle rebuilt; only `web/src` committed; a screenshot of the section.
- [x] Default suite green; presence stays opt-in (flag-unset byte-identical).
