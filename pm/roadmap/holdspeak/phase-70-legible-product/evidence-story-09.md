# Evidence — HS-70-09: Closeout — no dead doors, one clean arrival, proven

**Date:** 2026-06-30
**Verdict:** done. The phase's thesis is proven end to end: the web is legible,
no route is a dead door, and a brand-new user goes launch → single arrival →
Home without confusion.

## No dead doors

`scripts/phase70_closeout.py` sweeps all 18 routes (following redirects) →
**18/18 resolve 200**, including the moved/renamed/aliased ones: `/live` (the
carved-out dashboard), `/studio` (new), `/meetings` → `/history` (redirect),
`/setup` + `/activity` (reframed but reachable). The route pre-flight
(`tests/e2e/test_route_preflight.py`, **2 passed**) additionally sweeps every
page for zero page errors and guards that every `pages.py` route is in
`PAGE_ROUTES` (so a new page can't ship unchecked).

## One clean arrival

- **First-run:** a fresh DB (no `FIRST_DICTATION_SUCCESS` milestone) hitting `/`
  is guarded to the single arrival: `/` → **`/welcome`** (recorded live).
- **Set-up user:** after marking the milestone, `/` stays on **Home**, and the
  nav primaries read `['Home', 'Dictation', 'Meetings', 'Studio']` — the four-door
  IA (`screenshots/closeout-home-nav.png`).

## The legibility read-test (the phase's real bar)

Against `home-empty.png`, a fresh viewer gets, in order:
1. **What is this** — "One copilot, two modes." + the one-liner.
2. **The two modes** — two co-equal cards, each with a one-line what-it-does.
3. **A first action** — "Open Dictation" / "Start a meeting" buttons, plus a
   single "Next" band pointing at the one remaining setup step.

Studio is a quiet dashed link, never competing. A person can say what HoldSpeak
is, name the two modes, and take a first action within ten seconds. Bar cleared.

## Suite + hygiene

- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **3045
  passed, 37 skipped** (unchanged across the whole phase; every ripple was
  retargeted in lockstep, never silenced).
- `cd web && npm run build` green (18 pages); `holdspeak/static/_built/` never
  committed.
- Cadence: all nine story headers + `current-phase-status.md` (CLOSED 9/9) + the
  project `README.md` (phase row + Current-phase + Last-updated) + POSITIONING
  updated across the phase.

## Deliverables

`final-summary.md` (the phase record, the route map, honest follow-ups) ships in
this commit. PR #205 is the owner's to merge on green CI.
