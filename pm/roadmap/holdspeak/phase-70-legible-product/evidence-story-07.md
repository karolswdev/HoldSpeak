# Evidence — HS-70-07: Guiding empty states (no scary blanks)

**Date:** 2026-06-30
**Verdict:** done. A shared empty-state primitive lands, and the one surface
that read as scary/stale (the Meetings archive) is fixed. An audit confirmed the
other primary surfaces already guide rather than blank.

## What shipped

- **`web/src/styles/global.css`** — the shared **`.empty-state`** primitive
  (glyph + title + one guiding line + at most one action), global so it paints
  on Alpine/JS-injected DOM. Copy stays labels-not-manuals.
- **`web/src/pages/history.astro`** — the Meetings archive empty state, rebuilt
  on the primitive, in **two guiding variants** (no more scary blank, no stale
  links):
  - **No match** (filters active, 0 results): "No meetings match these filters"
    + "Widen the date range, speaker, or tag." + a **Clear filters** button.
  - **First run** (no meetings, no filters): "No meetings yet" + "Start a live
    meeting or import a recording or transcript." + **Start a meeting** (→ `/live`)
    and **Import** buttons.
  - This also fixes the **HS-70-05 follow-up**: the old copy said "Finish a
    meeting on Runtime …" (a retired dashboard name) and linked `/` + `/activity`.

## The audit (most surfaces already guide)

- **Home** — guiding subtitles from HS-70-02 ("Nothing yet. Hold your key and
  speak." / "…Capture or import your first meeting.").
- **Dictation journal** — already a guiding empty ("Your dictations will appear
  here." + what-gets-remembered) **and** a no-match variant
  (`scripts/dictation/journal.js`).
- **Dictation project context** — a teaching empty (`ContextSection.astro`,
  `kn-empty`, HS-47-02).
- **Studio** — always renders its six cards (no empty case).

The gap was the Meetings archive; the rest were already correct, so they were
left as-is (retrofitting the working ones to the new class would be churn and
risk, for no user-visible gain). Load vs empty vs no-match are distinct on every
surface (the Meetings list gates `x-show="loading"` / `=== 0 && facetsActive()`
/ `=== 0 && !facetsActive()` / `> 0`).

## Proof

- **`screenshots/empty-state-meetings.png`** — the Meetings first-run empty
  state: glyph + "No meetings yet" + the guiding line + Start / Import actions,
  no stale "Runtime" link.
- **Tests:** no test asserted the old (or new) empty copy; full suite **3045
  passed, 37 skipped**; build green (18 pages).
