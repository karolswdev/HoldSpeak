# Evidence — HS-65-01: Pre-flight — every route loads clean

**Date:** 2026-06-13
**Verdict:** done — and it earned its place immediately: the sweep found
**two dead-on-arrival page bugs**, both pre-existing, both invisible to
every prior test because no dogfood opened those two pages.

## What shipped

`tests/e2e/test_route_preflight.py`, two tests:

- `test_preflight_covers_every_html_route` — enumerates the GET routes
  whose handler lives in `routes.pages` from the LIVE app and asserts
  `PAGE_ROUTES` covers them exactly (a new page can't ship unswept; a
  removed one can't linger). Runs in CI (no browser needed).
- `test_every_route_loads_without_page_errors` — boots the real server,
  loads all 11 page routes in Chromium, asserts zero uncaught page
  errors per route. `importorskip`s Playwright and skips cleanly when no
  browser is present (CI has none); the green evidence run is local.

## The two bugs (both pre-existing)

1. **`/activity` JS was dead since Phase 9/10.**
   `web/src/scripts/activity-app.js` began with a literal `<script>` line
   (and no closing tag) — a leftover from when it lived inline in the
   `.astro` page. The page imports it `?raw` and runs it via
   `new Function(source)()`, so the leading `<` threw "Unexpected token
   '<'" on every load and the ENTIRE page script never ran: no
   `load()`, no API calls, no live data. Last touched in `cfd657b`
   (HS-9-13). Fixed by removing the spurious tag; the file now parses as
   JS (`node --check`), and a live probe confirms `load()` now fires all
   five `/api/activity/*` calls it was meant to.
2. **`/companion` threw on every load.** The readiness-blockers
   `<template x-for="blocker in status.blockers">` evaluated its
   expression even while its `x-show` parent was hidden (Alpine
   evaluates x-for regardless of x-show), so `status` being `null` on
   first paint threw "Cannot read properties of null (reading
   'blockers')". Fixed with `(status?.blockers || [])`.

Both pages now load with zero page errors; the activity page is
functionally restored (it had been a static shell for ~55 phases).

## Proof

- The sweep: 2 passed (coverage guard + the 11-route browser sweep,
  green after the fixes).
- Full suite: **2777 passed, 17 skipped** (+2); web build clean, 0
  `_built/` tracked.
