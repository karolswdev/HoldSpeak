# Phase 54 — Dictation Frontend Decomposition

**Status:** in-progress (3/6). Opened 2026-06-11 on user direction (the agreed post-53
sequence), right after Phase 53 closed + merged (PR #40). From the
[project backlog](../BACKLOG.md): candidate **D** (frontend density paydown), promoted
from "ride along with the next dictation feature" to its own phase.

**Last updated:** 2026-06-11 (**HS-54-03 done: the page is carved.** The 3,131-line
`dictation.astro` is now a **252-line composition** of fourteen components under
`components/dictation/`: eleven section/feature partials carrying their own styles
plus three markup-less shared-style components (`SharedStyles`, `KnowledgeStyles`,
`DepthControlStyles`) imported first so the emitted CSS keeps the pre-carve
base-then-feature cascade order (verified positionally in the built bundle). The
carve **exposed and fixed a real latent visual bug**: Astro 6 emits scoped styles
with `[data-astro-cid]` attribute selectors, so every JS-rendered element whose
class lived in the old scoped block (block cards, template cards, readiness cards,
the JS-rendered editor's forms/buttons, warn/error banners) has been **silently
unstyled** — proven by before/after computed-style probes (`border=0/UA-default` →
the intended design-system values). Assertions byte-identical (the `_page()` helper
learned the carved tree, mirroring `_app_js()`); slice 158 passed; full suite
**2540 passed, 17 skipped**; `npm run build` clean; the all-tabs dogfood re-ran
16/16 with zero page errors; a nine-tab screenshot sweep is committed.
**HS-54-02 (prior): the monolith is carved.** The
2,907-line `dictation-app.js` is now a 19-line entry + twelve single-concern ES
modules under `scripts/dictation/` (largest: `knowledge.js` at 576 — all under the
~600 budget). Code moved verbatim; the one structural idiom is core's
section-loader registry (`registerSection`/`loadSection`), which keeps the module
graph **acyclic** where direct imports would have made knowledge↔readiness and
core↔features cycles. Three shared HTML helpers (`renderRuntimeGuidance`,
`renderDryTelemetry`, `learnSigChip`) moved to core for the same reason; the
discovery-nudge DI from HS-54-01 became direct core imports as planned. **Zero
test files changed**; slice 158 passed; full suite **2540 passed, 17 skipped**;
`npm run build` clean. Proven live by a new all-tabs Playwright dogfood
(`dogfood_story02.py`): all nine tabs activate + populate, pipeline enabled via
the UI, dry-run renders final text + stage trace + moment-of-truth, the ritual
acknowledges, the run journals, a correction adds + deletes — 16/16 PASS with
**zero uncaught page errors**. Two early dogfood failures were wrong assumptions
(a disabled pipeline's dry-run never journals — verified server-side), not carve
regressions. **HS-54-01 (prior): the module seam decided and proven.**
The `?raw` + `new Function()` loader turned out to be a Phase-10 (HS-10-09) migration
shim with nothing depending on the eval — no inline handlers, no DOMContentLoaded
reliance, no sloppy-mode dependence (each verified). The dictation page now loads its
behavior as a **real bundled ES module**, and the first carved module
(`web/src/scripts/dictation/discovery-nudge.js`, the HS-47-04 nudge, deps injected via
`initDiscoveryNudge` until core.js exists) rides the seam with identical behavior —
proven live by `dogfood_story01.py` (4/4: show, dismiss-persists, return-on-clear,
global-off-persists). The seam immediately paid for itself: module scope rejected a
**latent duplicate `escapeAttr` declaration** the eval had been masking via hoisting
(the dead `:365` alias deleted; the live `:2192` implementation kept). Client chunks
now ship **un-minified** via a `configEnvironment` vite hook (Astro 6 hardcodes client
`minify: true`, ignoring `vite.build.minify`) — behavior-preserving in the strictest
sense, since the shim always shipped the full un-minified source as a raw string.
Every page-content assertion byte-identical; the one test change is the `_app_js()`
helper reading the carved tree. Slice 158 passed; full suite **2540 passed, 17
skipped**; `npm run build` clean; 0 `_built/` tracked.)

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
| HS-54-01 | The module seam (decide + prove on one cluster) | done | none |
| HS-54-02 | Behavior modules (carve dictation-app.js) | done | HS-54-01 |
| HS-54-03 | Section partials (carve dictation.astro) | done | HS-54-02 |
| HS-54-04 | The density guard | backlog | HS-54-03 |
| HS-54-05 | Docs: the frontend architecture pattern | backlog | HS-54-03 |
| HS-54-06 | Closeout: dogfood + final-summary + PR | backlog | HS-54-01..05 |

## Where we are

**HS-54-01 + HS-54-02 + HS-54-03 shipped 2026-06-11.** The whole paydown is done:
6,101 coupled lines are now a 19-line script entry + twelve behavior modules
(largest 576) and a 252-line page + fourteen components (largest 499). Both
carves were proven on a live runtime (16/16 all-tabs dogfood, zero page errors;
nine-tab screenshot sweep), the full suite is green with byte-identical
assertions, and the seam surfaced two real latent bugs along the way (the
duplicate `escapeAttr`; the silently-unstyled JS-rendered elements).

Next is **HS-54-04 — the density guard**: lock the shipped shape (page ≤ 300;
components and modules ≤ 600) with a drift-guard-style unit test so the page
cannot silently regrow.

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
