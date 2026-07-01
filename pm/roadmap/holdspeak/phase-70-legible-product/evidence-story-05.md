# Evidence — HS-70-05: Meetings mode, made whole

**Date:** 2026-06-30
**Verdict:** done. `/history` stopped being an oddly-named "History" archive and
became the **Meetings** front door, with the whole mode's entry actions (start a
live meeting, import a recording/transcript) promoted to the top instead of
buried, and the archive + facets + aftercare beneath.

## What shipped

- **`web/src/pages/history.astro`** — the Meetings surface:
  - Retitled: eyebrow "Meeting Archive" → "Meetings"; h1 "HoldSpeak History" →
    "Meetings"; page `<title>` → "HoldSpeak — Meetings"; hero copy reframed to
    name the whole mode (capture/import → decisions, actions, aftercare,
    searchable).
  - **Entry actions promoted to the hero:** "Start a meeting" (→ `/live`, the
    live-capture surface HS-70-02 carved out) and "Import a recording or
    transcript" (opens the existing HS-55/57 import panel and scrolls to it).
  - The archive, faceted search (Meetings / Action items / Speakers / Projects /
    Intel queue), and aftercare are unchanged beneath.
- **`holdspeak/web/routes/pages.py`** — a `/meetings` route that **redirects to
  `/history`** (307), so the canonical name resolves to a URL without a risky
  route rename. Registered in `PAGE_ROUTES`.

## Honest follow-up

The archive empty state still reads "Finish a meeting on Runtime …" — "Runtime"
is the retired dashboard name (now `/live`). Empty-state copy is fixed
app-wide in **HS-70-07** (guiding empty states); noted, not silently left.

## Proof

- **`screenshots/meetings-empty.png`** — `/history` as "Meetings": the hero with
  "Start a meeting" + "Import a recording or transcript", the metric grid, the
  faceted archive, the empty list.
- **`screenshots/meetings-import.png`** — the import panel opened from the hero
  action (drop zone + fields), scrolled into view.
- **Tests:** route pre-flight **2 passed** (`/meetings` redirect + `/history`
  swept, zero page errors); full suite **3045 passed, 37 skipped**; build green
  (17 pages). No test asserted the old "HoldSpeak History" title positively.
