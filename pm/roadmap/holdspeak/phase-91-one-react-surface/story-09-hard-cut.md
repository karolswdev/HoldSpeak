# HS-91-09 — The hard cut: one Vite app, no Astro or Alpine

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-03, HS-91-04, HS-91-05, HS-91-06, HS-91-07, HS-91-08
- **Unblocks:** HS-91-10
- **Owner:** unassigned

## Problem

Incremental migration is only useful if the temporary dual stack is actually
removed. This story deletes the escape hatches and makes architectural drift
mechanically difficult.

## Scope

- In: switch every route to one Vite shell; simplify FastAPI page serving;
  delete Astro pages/layouts/components, Alpine and migrated imperative scripts;
  remove dependencies/config; update package commands; add no-Astro/no-Alpine/
  no-selector-bootstrap guards; regenerate built assets and route tests.
- Out: feature polish beyond cutover defects; backend API redesign.

## Acceptance criteria

- [x] `find web/src -name '*.astro'` returns nothing; dependency and source
      censuses find no Astro/Alpine/client-island/directive residue.
- [x] One `index.html` and React entry serve every product route through
      FastAPI fallback; all 17 direct links return 200 and correct route content.
- [x] No migrated product script creates controls with `innerHTML` or manages
      state through global selectors; an explicit guard pins the allowed set.
- [x] Production bundle has no Astro or Alpine chunk and package description,
      commands, lockfile and developer docs name Vite/React only.
- [x] Full React and backend Web test suites pass before the old files are
      removed and again after removal.

## Test plan

- Unit: full `npm run test:web` and typecheck.
- Integration: full Web pytest selection and 17-route Playwright audit.
- Manual / device: cold direct-load every route, browser back/forward, tokenized
  link, refresh, offline/reconnect and restart.

## Notes / open questions

Deleting generated `_built` artifacts is part of the rebuild mechanics; source
history, not dead compatibility files, is the rollback plan.
