# Evidence — HS-55-04: Faceted history search (API + filter row)

**Date:** 2026-06-11
**Branch:** `phase-55-meeting-import`

## 1. What shipped

**Repo** (`db/meetings.py`): `list_meetings` — which already supported
`date_from`/`date_to`/`tag` in SQL but never exposed them — gains `speaker`
(distinct segments match), `has_open_actions` (`action_items.status =
'pending'`), and `meeting_ids` (so full-text hits flow through the same
faceted query). Plus `list_facet_values()` (distinct speakers + tags,
NOCASE-ordered).

**Route** (`GET /api/meetings`): exposes `date_from`/`date_to` (ISO; a bare
`date_to` date is inclusive of the whole day), `speaker`, `tag`,
`has_open_actions`, all composing with `search` **in SQL over the whole
archive** (search → FTS ids → the faceted query). Plus
`GET /api/meetings/facets` for the filter row — deliberately registered
**before** `/api/meetings/{meeting_id}` so "facets" never matches as an id.

**A fix that fell out:** the old search branch returned full
`MeetingState.to_dict()` payloads whose **nested** `intel_status`
(`{"state", "detail"}`) broke the history card's status pill (the class
binding got an object → every search result rendered the fallback pill).
Both branches now return the same flat summary shape; search results carry
working pills. Recorded as behavior-improving, like the carve finds.

**UI** (`/history` meetings tab): a facet row under the toolbar — From/To
date inputs, a speaker select and tag select fed by the facets endpoint, an
"Open actions" toggle, and a Clear-filters button that appears only when a
facet is active. One `meetingsQuery()` builder drives **every** meetings
fetch (load, search, and the HS-55-03 quiet import poll — active filters
survive imports and refreshes). With no params the request and response are
byte-identical to before.

## 2. Tests (actually run, actually read)

`tests/integration/test_web_meetings_facets_api.py` — 5 tests over a seeded
archive: every facet alone (incl. the inclusive bare-date `date_to`),
facets composed with each other and with `search` (and the search-shape
fix asserted: flat `intel_status` strings), **whole-archive proof**
(`limit=1` + facets still finds the oldest match — SQL, not page
post-filtering), the no-params regression shape, and the facets endpoint
values.

Page locks added to `test_web_history_import_ui.py` (the facet-row markers +
the query-builder markers).

```
$ uv run pytest -q tests/integration/test_web_meetings_facets_api.py
5 passed in 1.29s

$ uv run pytest -q tests/integration/test_web_history_import_ui.py \
    tests/integration/test_web_meetings_facets_api.py tests/integration/test_web_history_archive.py
13 passed in 1.22s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2568 passed, 17 skipped in 81.34s (0:01:21)
```

(2562 → 2568: five facet tests + one facet-row lock.)

## 3. Live proof

A Playwright pass against a seeded server: selecting speaker "Alice" in the
row narrowed the list from 3 to 2 cards (stat card following), zero page
errors. Screenshot committed and reviewed: `screenshots/story04-facets.png`
(the full row: dates, speaker select on Alice, tags, Open-actions toggle,
Clear filters). `npm run build` clean; 0 `_built/` tracked.
