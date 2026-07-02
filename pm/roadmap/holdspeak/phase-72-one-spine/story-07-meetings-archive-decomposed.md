# HS-72-07 — The meetings archive, decomposed

- **Status:** todo
- **Priority:** MED (the largest file in the product, on its most-used archive surface)
- **Depends on:** —

## Goal

`web/src/pages/history.astro` is 3,400 lines and `history-app.js` is 1,777 —
the web's worst monolith pair, untouched by the Phase-54 decomposition that
fixed the dictation cockpit. Apply the same, proven pattern: section partials
+ focused ES modules, with the density guard extended so it cannot regrow.

## Scope

- **In:** `history.astro` → thin page + `components/meetings/*` partials
  (archive list/facets, detail, action items, speakers, intel queue,
  aftercare, artifacts, proposals — cut along the existing tab/section
  seams); `history-app.js` → modules under `scripts/meetings/` (the Alpine
  factory may remain one factory composed from imported modules — the
  `?raw` loader constraint is real; composition inside it is still
  possible); the density guard (the Phase-54 lock) extended to cap the new
  files; `<style is:global>` discipline for every JS-rendered block.
- **Out:** any feature/UX change (pixel-identical is the bar); `live.astro`
  and `dashboard-app.js` (HS-72-08 touches their socket layer; their full
  decomposition rides on how much that story already shrinks them);
  `desk.astro` (fresh Phase-71 code — watch item).

## Tasks

- [ ] Cut the partials + modules; keep base-then-feature CSS import order
      (the `SharedStyles`-first lesson).
- [ ] Extend the density-guard test with the new maxima (page + scripts).
- [ ] Screenshot-verify every tab/section after the split — a class present
      in the bundle is not proof it applies (the standing Astro gotcha).
- [ ] Route pre-flight + zero page errors on `/history` with seeded
      meetings, artifacts, proposals, aftercare.

## Proof required

Before/after `wc -l` table; density guard green with the new caps; the
screenshot set across tabs (seeded data) showing no visual regression; route
pre-flight green; full suite green.
