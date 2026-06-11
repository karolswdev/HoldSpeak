# HS-55-04 — Faceted history search (API + filter row)

- **Project:** holdspeak
- **Phase:** 55
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-55-05, HS-55-06
- **Owner:** unassigned

## Problem
`GET /api/meetings` supports full-text `search` only; anything else is
client-side filtering of one 50-row page. Import makes archives big enough
that "meetings with Alice in March that still have open actions" must be a
query, not a scroll.

## Scope
- **In:**
  - **Server-side facets** on `GET /api/meetings`, composable with each other
    and with `search`, filtered **in SQL** (not by post-filtering a page):
    - `date_from` / `date_to` (on `started_at`);
    - `speaker` (meetings with segments by that speaker);
    - `tag` (existing meeting_tags);
    - `has_open_actions` (open action items > 0).
  - A small **facet-values source** for the UI (distinct speakers/tags —
    reuse existing endpoints if they exist; add the minimal one if not).
  - **The `/history` filter row:** date range, speaker select (real data),
    tag select, open-actions toggle — Signal-styled, composing with the
    search box, with a visible active-filters/clear state. Lean additions to
    the uncarved page, per the Phase-54 architecture doc.
- **Out:** artifact-type faceting (unless free); saved searches; any FTS
  schema change beyond what composition requires.

## Acceptance criteria
- [ ] Each facet filters correctly server-side, alone and combined with
      `search` and each other (integration tests with seeded meetings).
- [ ] Facets see the whole archive (a match outside the first page is found).
- [ ] The filter row renders, drives the API params, shows active filters,
      and clears; page-content test + screenshot.
- [ ] No behavior change with no facets supplied (existing callers
      byte-identical).

## Test plan
- Integration: seeded meetings exercising every facet alone + combined +
  paging; the no-params regression case.
- Page-content test for the row; screenshot evidence.
- Full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Notes / open questions
- Independent of the import stories — can land in parallel with HS-55-02/03.
