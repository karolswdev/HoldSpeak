# Evidence — HS-75-03 — The settings knob (cockpit config)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-75-preview-before-type`)

## What changed

- **The cockpit toggle** (settings.astro, the Voice section, searchable):
  "Preview before it types — a finished dictation shows a card first;
  Type it commits, Discard drops it." One checkbox on
  `settings.dictation.preview_before_type`; no prose beyond the em-hint
  idiom every neighboring field uses.
- **The settings boundary carries it**: the PUT's explicit
  `DictationConfig(...)` construction gains the field (absent falls back
  to current — never silently flips).
- **A REAL bug found by the round-trip test**: `Config.load`'s explicit
  dictation constructor DROPPED the field — the knob would save, echo
  `true`, and silently revert on the next load (every restart). Fixed in
  the loader; the test now proves GET(default false) → PUT(true) →
  fresh GET(true) against the real app on a scratch config file.

## Verification artifacts

- `test_settings_round_trip_carries_the_knob` — the full GET/PUT/GET
  cycle on the real routes (405-method and patch-seam missteps fixed
  during authoring, honestly). Story file total: **8 passed**.
- Web build green. Full suite: **3088 passed, 37 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] The knob in the cockpit's settings with honest copy.
- [x] The boundary + the LOADER round-trip (the loader half was the real
      work).
