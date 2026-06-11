# Evidence — HS-56-01: Assets + the mascot gate

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

## 1. What shipped

- **Assets vendored** to `web/public/qlippy/` (136 KiB total): all 14 sprite
  strips (`sprites/<state>.png`, 80×80 × 9 frames), the 4 composited glyphs,
  the canonical avatar (`qlippy.png` + `@4x`), and a provenance README
  (PixelLab object `44c0b009-…`, the strip geometry, the
  body-emotes/composited-glyph design rule, the local-only note). The build
  carries them: 14 sprites verified in `_built/qlippy/sprites/` after
  `npm run build` (served under the `/_built` base).
- **`PresenceConfig.mascot: bool = False`** — a second opt-in on top of
  `enabled`. The settings route's `PresenceConfig(**presence_data)`
  construction means the field round-trips `/api/settings` with **zero route
  changes**; an older config shape (presence with only `enabled`) coerces
  forward to the default (test).
- **The settings sub-toggle**: "Qlippy, the mascot" sits indented under the
  HUD toggle behind a left rail (`.mascot-subfield`), **inert + dimmed when
  presence itself is off** (guarded click, `aria-disabled`), with honest
  copy ("He only ever offers — nothing runs without your click. Off keeps
  the minimal status ring.").

## 2. Tests (actually run, actually read)

`tests/integration/test_presence_mascot_gate.py` — 5 tests: default-off +
`/api/settings` round-trip (`{"enabled": true, "mascot": true}` persisted and
re-read), the older-config forward-coercion, the dataclass default, the
settings-page sub-toggle locks (subordination + the guarded click + the
honest copy), and the vendored-assets lock (14 sprites incl. every state the
later stories use, the 4 glyphs, the provenance id in the README).

```
$ uv run pytest -q tests/integration/test_presence_mascot_gate.py
5 passed in 0.73s

$ cd web && npm run build           # clean; 14 sprites in _built/qlippy/sprites
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2573 passed, 17 skipped in 83.53s (0:01:23)
```

(2568 → 2573: the five gate tests.) 0 `_built/` files tracked.

## 3. Live screenshots (reviewed)

`screenshots/story01-mascot-toggle-inert.png` (presence off → the sub-toggle
dimmed/inert) and `story01-mascot-toggle-on.png` (presence + mascot both on —
the indented rail layout, both switches accent).

## 4. Notes for HS-56-02

- The presence page reads the flag from the existing `GET /api/settings`
  (`settings.presence.mascot`) — no `/api/state` changes, no consumer risk.
- Sprite URL shape: `/_built/qlippy/sprites/<state>.png`;
  `background-size: 720px 80px` + `steps(9)` + `image-rendering: pixelated`.
