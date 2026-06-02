# HS-30-08 — History + Activity + Companion redesign

- **Project:** holdspeak
- **Phase:** 30
- **Status:** backlog
- **Depends on:** HS-30-04, HS-30-05
- **Unblocks:** HS-30-09
- **Owner:** unassigned

## Problem

The three secondary routes share list/archive/status patterns and should be
redesigned together so they stay consistent:
- `history.astro` — meeting archive (search, filter, export, action items,
  meeting cards, transcript detail).
- `activity.astro` — local browser-history enrichment (sources, excluded domains,
  rules, candidate rules, records, retention slider).
- `companion.astro` — read-only AI PI companion overview (waiting sessions, pin/
  dismiss, summary cards, 3s polling).

## Scope

### In

- Rebuild each page's layout to the HS-30-01 IA on the Signal foundation, reusing
  the restyled components (cards, list rows, toolbars, empty states, pills).
- `history` — readable meeting cards with intelligence-readiness status, a clear
  search/filter/export bar, a legible transcript detail/search view.
- `activity` — a calm controls layout (pause/resume, retention slider), sources +
  excluded-domains management, and the records/rules columns.
- `companion` — summary cards + waiting-sessions list with pin/dismiss, status
  legible; keep the 3s polling behaviour.
- Preserve all Alpine.js behaviour (`history-app.js`, `activity-app.js`,
  `companion-app.js`) — restyle markup, keep bindings + endpoints.

### Out

- Backend / API / connector changes — UI only.
- Dashboard + dictation (HS-30-06/07).

## Acceptance criteria

- [ ] All three routes match the IA-spec layouts in Signal and are visually
      consistent with each other and the dashboard.
- [ ] Each route's primary interactions still work on the running app (history
      search/export, activity source toggles + domain add/remove + retention
      slider, companion pin/dismiss + live polling).
- [ ] Empty/loading states render correctly per route (screenshots).
- [ ] Before/after screenshots for all three in evidence.
- [ ] `npm run build` green; backend sweep green.

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Visual / manual: `npm run dev`; walk all three routes incl. an empty and a
  populated state each; exercise the key controls.
- Build: `npm run build` exit 0.

## Notes / open questions

- These three are lower-risk than the dashboard but carry the consistency burden —
  they prove Signal scales across the whole product, not just the hero page.
