# Evidence — HS-45-02: The Journal, a reviewable utterance timeline

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-45-dictation-memory`.

## What shipped

Dictation's `/history`: a **Journal** tab on `/dictation` that makes the
HS-45-01 rows reviewable — *what I said → what it became → where it was headed →
how long it took* — searchable, filterable, and curatable, at the Phase-44
premium bar. The per-utterance **latency black box is now open**.

### API — `holdspeak/web/routes/dictation/pipeline.py`

- `GET /api/dictation/journal?limit=&source=` → `{enabled, retention, count,
  items[]}` (newest-first; reports the toggle + retention so the UI can state
  the privacy posture; empty — never an error — on a bare server).
- `DELETE /api/dictation/journal/{id}` → `{removed, count}` (404 if absent / no repo).
- `DELETE /api/dictation/journal` → `{cleared, removed, count}` (the one-click wipe).
- `_journal_to_dict` serializer; reads the durable repo via `ctx.journal.repository`.
- *(Also present: `POST …/journal/{id}/correct` — dormant plumbing for HS-45-03;
  no UI calls it yet.)*

### UI — `web/src/pages/dictation.astro` + `web/src/scripts/dictation-app.js`

- A new **Journal** section via the existing `[data-section]` tab pattern
  (`section-journal` / `view-journal`) — the Alpine-free DOM contract preserved,
  every existing id untouched.
- A reviewable **timeline**: each entry is an elevated, accent-edged card with a
  **source chip** (Spoken / Dry-run), routed **block + confidence** + **target**
  badges, a **timestamp**, a **"You said" → "It typed"** two-column flow (each
  copy-able via the `CommandPreview` clipboard idiom), a **per-stage latency
  strip** (proportional segments + total, degrading gracefully when `stage_ms`
  is sparse), and a collapsible **warnings** disclosure. Corrected entries get a
  green edge + ✓ marker (the flag HS-45-03 sets).
- **Search** (transcript + final text, client-side, instant) + **filters**
  (source · only-with-warnings · only-corrected). **Per-entry delete** +
  **Clear journal** over the DELETE endpoints.
- A first-class **local-only trust statement** (the TrustChip idiom, expanded:
  "lives only on this machine · secret-filtered · retention-capped · clear
  anytime"), which flips to a warning tone when journaling is off.
- A **warm empty state** ("Your dictations will appear here…").
- The **Phase-44 bar**: ambient cockpit hero + solid-accent pill nav, elevated
  rounded cards with hover lift, SVG glyphs, focus-visible search, and a
  `prefers-reduced-motion` guard.

## Tests — `tests/integration/test_web_dictation_journal.py` (8 tests)

API: empty-by-default (`enabled:true`, retention 500), newest-first listing with
routing/latency fields, `source` filter + `limit`, delete-one (+ 404 on repeat),
clear-all, and **delete/clear 404 (not 500) on a bare server**. Page-content:
the Journal tab + view + list host + search + filters + clear button + the
local-only trust statement are in `/dictation`; the latency-strip + journal-card
styles are in the built stylesheet; the reduced-motion guard is inline.

```
$ uv run pytest -q tests/integration/test_web_dictation_journal.py
8 passed in 1.12s

$ uv run pytest -q tests/unit/test_dictation_routes_split.py
2 passed   # route-table guard updated: 30 → 34 (the 4 journal routes)
```

### Live screenshot

`scripts/screenshot_journal.py` starts a real server backed by a temp DB seeded
with 3 realistic rows (spoken + dry-run, varied routing/latency, one corrected),
drives the Journal tab with Playwright, and writes
**`evidence/journal_timeline.png`** — the populated timeline: source chips, block/
target badges, said→typed frames, latency strips, the corrected marker, and the
trust note, all at the premium bar.

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2351 passed, 17 skipped
$ uv run ruff check holdspeak/web/routes/dictation/pipeline.py
All checks passed!
$ (cd web && npm run build)   # ✓ 12 pages built
```

**0** `holdspeak/static/_built/` tracked (gitignored — `web/src` committed only).

## Invariants held

- **DOM contract preserved** — the Journal is an additive `[data-section]` tab;
  the route-table guard + the cockpit page-content tests stay green.
- **Local-first & private** — the trust statement is first-class on the surface;
  the API exposes the retention bound; the wipe + per-entry delete are wired.
- **Phase-44 bar + a11y** — premium hero/pill-nav/elevated cards, focus-visible,
  reduced-motion, SVG glyphs, overflow-safe (`overflow-wrap: anywhere`).
- **Read + curate only** — no routing/typing path touched; the in-moment fix is
  HS-45-03.
