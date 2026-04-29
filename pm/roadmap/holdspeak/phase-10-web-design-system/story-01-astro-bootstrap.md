# HS-10-01 - Astro + Open Props bootstrap

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** none
- **Unblocks:** every other HS-10 story
- **Owner:** unassigned

## Problem

The web runtime is five hand-authored HTML files in `holdspeak/static/`,
each carrying its own inline `<style>` block. There is no component
boundary, no token layer, no shared header, and no build pipeline. Any
"design system" work in raw HTML/CSS would just relocate the
inconsistency. We need a static-first, light-touch frontend pipeline
before anything else lands.

## Scope

- **In:**
  - `web/` source directory at the repo root containing an Astro
    project (`package.json`, `astro.config.mjs`, `src/pages/`,
    `src/components/`, `src/styles/`).
  - Open Props installed and imported as the token base.
  - Build output configured to emit into `holdspeak/static/` so the
    FastAPI runtime continues serving the same paths (`/`, `/activity`,
    `/history`, `/dictation`, `/docs/dictation-runtime`).
  - One "hello" route shipped through the new pipeline (e.g. a
    placeholder `/dictation/_design-check`) to prove the full
    source → build → served-by-FastAPI loop works.
  - `npm run build` and `npm run dev` documented in `web/README.md`.
  - `.gitignore` updated for `web/node_modules/` and `web/dist/`.
- **Out:**
  - Migrating any of the existing five pages (those are HS-10-06
    through HS-10-09).
  - Authoring tokens or components (HS-10-02, HS-10-03).
  - Adding Tailwind, React, or any UI framework on top of Astro.
  - CI integration of `npm run build` (tracked separately if needed).

## Acceptance Criteria

- [x] `cd web && npm install && npm run build` produces files under
  `holdspeak/static/` without erasing the existing five legacy pages.
- [x] FastAPI runtime serves the new "hello" route alongside the
  existing pages with no regressions.
- [x] `npm run dev` serves the design-check route with hot reload.
- [x] Open Props is reachable from a component (one variable used in a
  test style).
- [x] `web/README.md` documents the dev/build commands and the
  output-into-`holdspeak/static/` contract.
- [x] No new runtime Python dependency is introduced; Node is a
  build-time dependency only.

## Test Plan

- Manual: run `npm run build`, confirm output lands in
  `holdspeak/static/` and the legacy pages still load.
- `uv run pytest -q` regression sweep (excluding
  `tests/e2e/test_metal.py` per project convention).
- Manual browser check of the design-check route at the local runtime
  URL.

## Notes

The output-co-located-with-legacy strategy is intentional: it lets
HS-10-06 through HS-10-09 migrate one route at a time without ever
breaking the runtime. Each rebuild story replaces one legacy file with
its Astro-built equivalent.
