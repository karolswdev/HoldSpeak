# HS-91-01 — The React foundation and parity ledger

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-91-02, HS-91-03, HS-91-04, HS-91-05, HS-91-06, HS-91-07, HS-91-08
- **Owner:** unassigned

## Problem

The existing React Desk is an Astro island while every other route has its own
Astro page, Alpine state, and imperative scripts. A safe migration needs the
destination shell and a machine-readable account of what each route already
does before markup starts moving.

## Scope

- In: explicit Vite + React + TypeScript entry; browser router; shared shell,
  token/auth bootstrap and runtime-bus provider; FastAPI SPA deep-link seam;
  route/verb/state/persistence inventory for all canonical routes; React test
  harness; one non-critical proof route behind the new shell.
- Out: feature-route migration beyond the proof route; visual component
  completion (HS-91-02); removal of Astro/Alpine (HS-91-09).

## Acceptance criteria

- [x] `web` has explicit Vite config and React entry that builds into the
      existing `_built` package location without changing backend APIs.
- [x] Browser router names every canonical route and direct navigation/refresh
      is integration-tested through FastAPI, including query-token bootstrap.
- [x] A checked-in parity ledger records every route's verbs, endpoints,
      loading/empty/error states, local/session storage keys, WebSocket use,
      and focus-sensitive interactions.
- [x] Shared typed `apiFetch`/auth and runtime-bus providers replace new direct
      global fetch/WebSocket bootstraps; errors remain typed and user-readable.
- [x] React/Vitest/Testing Library test commands exist and the proof route has
      route, error-boundary, and accessibility tests.
- [x] Existing Astro routes remain behaviorally unchanged during this story.

## Test plan

- Unit: `npm run test:web` for router, API client, auth and runtime-bus tests.
- Integration: FastAPI TestClient deep links + Playwright proof-route load.
- Manual / device: direct-load the proof route with and without a token, then
  navigate back to the existing React Desk without a full-page failure.

## Notes / open questions

The ledger is a migration gate, not documentation theater. A route cannot move
to done later unless every ledger row has an explicit result.
