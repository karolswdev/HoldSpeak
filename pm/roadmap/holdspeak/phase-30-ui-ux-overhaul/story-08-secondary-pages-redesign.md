# HS-30-08 — History + Activity + Companion redesign

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
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

- [x] All three routes render Signal and are consistent with each other + the
      dashboard: eyebrow page headers + metric/summary cards, eyebrow panel headers,
      dark cards. `evidence/after-hs08/{history,activity,companion}.png`.
- [x] Interactions preserved **by construction**: the migration is CSS-only
      (inlined the shim mapping → canonical tokens) + an eyebrow header tweak; no
      Alpine/vanilla hook touched (history `historyApp()`, activity IIFE, companion
      `CompanionApp()` all intact).
- [x] Empty/loading states render correctly (visible in the screenshots).
- [x] Before/after for all three (`evidence/before/*` → `after-hs08/*`).
- [x] `npm run build` green; backend sweep green (2062 passed, 14 skipped).
- [x] **Shim deleted:** the tokens.css Workbench compat shim is removed; `--wb-*` =
      **0 repo-wide** (the phase's token migration is complete).

> **Deferred (noted, not silently dropped):** History keeps its **Settings** tab.
> The IA's full extraction of Settings *content* into the shell drawer is a larger
> Alpine refactor of `historyApp()` + the settings endpoints; the drawer (HS-30-04)
> exists and links into History → Settings, so settings are globally reachable
> now. Full content extraction is handed to a follow-up (flagged in HS-30-09 /
> `final-summary.md`), to avoid a risky refactor riding on this restyle chunk.

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Visual / manual: `npm run dev`; walk all three routes incl. an empty and a
  populated state each; exercise the key controls.
- Build: `npm run build` exit 0.

## Notes / open questions

- These three are lower-risk than the dashboard but carry the consistency burden —
  they prove Signal scales across the whole product, not just the hero page.
