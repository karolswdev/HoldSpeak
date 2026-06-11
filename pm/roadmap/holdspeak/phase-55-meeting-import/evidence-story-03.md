# Evidence — HS-55-03: The /history import UI

**Date:** 2026-06-11
**Branch:** `phase-55-meeting-import`

## 1. What shipped

On `/history`'s meetings tab (lean, cohesive additions to the uncarved page,
per the Phase-54 architecture doc — Alpine `x-for` templates carry the Astro
cid, so the new styles stay scoped):

- **The opener:** an "Import a recording" button (upload glyph, accent) at
  the right of the search toolbar.
- **The panel:** an accent-edged `detail-card` with a dashed **drop target**
  (drag/drop + browse; shows the chosen filename), Title / Speaker label /
  Tags fields, and the honest notes verbatim: WAV out of the box, ffmpeg for
  compressed formats, **one speaker label**, **the audio file isn't kept**,
  **everything stays on this machine**.
- **Submit:** multipart POST with `started_at_ms` from `File.lastModified`
  (old recordings sort where they happened); a success flash; the panel
  closes; the list refreshes quietly.
- **Live lifecycle on the card:** `intel_status="importing"` renders an
  accent, reduced-motion-safe pulsing **"Importing…"** pill with the
  window-progress detail line (the card's existing `meta-line` shows the
  row's `intel_status_detail` for free); a **quiet poll** (2 s, no
  list-wide loading flicker) runs **only while an import is in flight** —
  started on submit, re-armed after a page refresh if a row is mid-import,
  self-stopping when none is.
- **Failure:** `import_failed` renders a danger pill + the actionable
  detail, with a **Remove** affordance placed *outside* the card button
  (valid HTML — the card itself is a `<button>`, so the row is wrapped) that
  confirms via `holdspeakConfirm` and calls the new
  `DELETE /api/meetings/{id}`.

## 2. Live proof (Playwright, real browser upload)

`dogfood_story03.py` — a real WAV attached through the real file input on a
live server (slowed fake transcriber so the importing state is observable):

```
PASS  panel opens with the honest notes
PASS  card shows Importing… (progress detail visible: True)
PASS  card resolved in place, no manual refresh
PASS  zero page errors across the whole run
RESULT: PASS
```

Screenshots committed and visually reviewed: `story03-panel.png` (the
affordance + panel with drop target and notes), `story03-importing.png`
(the flash + the card with the pulsing Importing… pill and progress
detail), `story03-resolved.png` (resolved in place).

## 3. Tests + build (actually run, actually read)

`tests/integration/test_web_history_import_ui.py` — 4 page-content locks:
the affordance + panel markers, the honest truths verbatim, the lifecycle
pill styles + labels + the remove path, and the behavior markers
(`/api/meetings/import`, `started_at_ms`/`lastModified`, `watchImports` /
`refreshMeetingsQuiet`, the importing-only poll condition).

```
$ uv run pytest -q tests/integration/test_web_history_import_ui.py \
    tests/integration/test_web_history_archive.py
7 passed in 0.02s

$ cd web && npm run build
13 page(s) built — clean
$ git ls-files holdspeak/static/_built | wc -l
0

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2562 passed, 17 skipped in 81.36s (0:01:21)
```

(2558 → 2562: the four page-content tests.)

## 4. Notes

- Net page growth kept lean: ~+90 markup lines + ~+110 style lines on
  `history.astro`, ~+100 behavior lines on `history-app.js` — cohesive,
  prefixed (`import-*`, `card-remove`), and documented here since the
  Phase-54 guard does not cover this page.
