# Phase 54 — Dictation Frontend Decomposition

**Status:** scaffolded. Opened 2026-06-11 on user direction (the agreed post-53
sequence), right after Phase 53 closed + merged (PR #40). From the
[project backlog](../BACKLOG.md): candidate **D** (frontend density paydown), promoted
from "ride along with the next dictation feature" to its own phase.

**Last updated:** 2026-06-11 (scaffolded: AGENT-BRIEF + six stories; ground truth mapped
against the live tree — `dictation.astro` 3,134 lines + `dictation-app.js` 2,967 lines =
6,101 coupled lines).

## The thesis — why this phase

The dictation cockpit is the daily-driver surface and the worst structural hotspot in
the tree. Grounded in the live tree at scaffold time:

- **`web/src/pages/dictation.astro` is 3,134 lines:** ~814 lines of markup hosting nine
  tab sections plus a single ~2,318-line `<style>` block.
- **`web/src/scripts/dictation-app.js` is 2,967 lines:** ~73 top-level functions in 15
  clusters on shared mutable state (`state`, `kbState`, `hsState`, `knNudgeState`),
  loaded as one blob via `?raw` + `new Function()`.
- **The density invariant lost every recent round.** Phases 40, 45, 47, 48, and 53 each
  grew the page; the Phase-53 brief already warned "do not grow the page further
  without paying it down". Every future dictation feature pays this tax.
- **There is no frontend decomposition precedent to follow** — every page uses the same
  monolith pattern. This phase defines it (the frontend twin of the backend
  decomposition lineage, Phases 26/31/32/34).

## Goal

Decompose the dictation frontend into navigable, single-responsibility units — ES
behavior modules per concern and Astro section partials per tab, each partial carrying
its own styles — **behavior-preserving**: same DOM contract, the existing page-content
tests green unmodified, every tab screenshot-verified, locked against regrowth by a
density guard. No feature, no visual change, no behavior change.

## Scope

- **In:** the module seam decision + proof (HS-54-01); behavior modules (HS-54-02);
  section partials + colocated styles (HS-54-03); the density guard (HS-54-04); an
  internal frontend-architecture doc (HS-54-05); closeout (HS-54-06).
- **Out:** any behavior or visual change; any backend/route change; the other monolith
  pages (`history.astro`, `index.astro`, `welcome.astro` — follow-up candidates once
  the pattern is proven); test edits to make a carve pass; new components shared across
  pages (keep the carve page-local under `components/dictation/`).

## Exit criteria (evidence required)

- The module-seam decision is made with evidence (keep or replace the `?raw` +
  `new Function()` loader) and proven on one extracted cluster with identical
  behavior. (HS-54-01)
- `dictation-app.js` is carved into single-concern ES modules (~≤600 lines each), same
  fetches/localStorage/DOM queries/poll; full suite green unmodified. (HS-54-02)
- `dictation.astro` is a thin composition (~≤300 lines) of partials under
  `web/src/components/dictation/`, styles riding with their partial, JS-injected DOM
  styles explicitly `is:global`; every tab screenshot-verified before/after. (HS-54-03)
- A density-guard test locks the post-carve budgets so the page cannot silently
  regrow; before/after metrics recorded. (HS-54-04)
- An internal architecture doc records the pattern and is linked from CONTRIBUTING.
  (HS-54-05)
- A dogfood click-through of all nine tabs on a live runtime; full suite green;
  `final-summary.md`; phase CLOSED; BACKLOG candidate D flipped to shipped; PR to
  `main` merged on green. (HS-54-06)

## Invariants

- **Behavior-preserving, proven by unmodified tests.** Editing an assertion to make a
  carve pass is failing the phase.
- **DOM contract identical.** Every id/class/`data-section` hook the JS queries stays.
- **Screenshot-verified per tab.** The scoped-CSS-on-JS-DOM gotcha is real and has
  bitten before.
- **Source only.** `holdspeak/static/_built/` stays untracked; `npm run build` clean.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-54-01 | The module seam (decide + prove on one cluster) | backlog | none |
| HS-54-02 | Behavior modules (carve dictation-app.js) | backlog | HS-54-01 |
| HS-54-03 | Section partials (carve dictation.astro) | backlog | HS-54-02 |
| HS-54-04 | The density guard | backlog | HS-54-03 |
| HS-54-05 | Docs: the frontend architecture pattern | backlog | HS-54-03 |
| HS-54-06 | Closeout: dogfood + final-summary + PR | backlog | HS-54-01..05 |

## Where we are

Scaffolded 2026-06-11. Nothing has shipped. Start with **HS-54-01** (the module seam):
answer the loader question with evidence and prove the pattern on the discovery-nudge
cluster before anything big moves.

## Open decisions (defaults chosen; flag to change)

- **JS carve before markup carve** (02 before 03): moving modules while the DOM stays
  untouched de-risks the riskier style/markup move.
- **Page-local components** (`web/src/components/dictation/`), not shared ones — no
  cross-page abstraction this phase.
- **Budgets:** ~≤600 lines per module/partial, ~≤300 for the composed page. Tune with
  evidence in HS-54-04 if the natural seams land elsewhere; the guard locks whatever
  is shipped.
- **The suggested module map** (core/blocks/readiness/knowledge/runtime/memory/journal/
  dryrun/agent/nudges/init) follows the 15 observed clusters; merging or splitting is
  the implementer's call if behavior is provably identical.
