# Phase 54 — Agent Brief (read this first)

You are picking up **Phase 54 — Dictation Frontend Decomposition** for HoldSpeak. This
brief is self-contained: the mission, the exact code seams (mapped against the live tree
at scaffold time), the rules of the road, and a per-story definition of success. Read it,
then read [`current-phase-status.md`](./current-phase-status.md) and the story you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

The dictation cockpit is HoldSpeak's daily-driver surface and its worst structural
hotspot. At scaffold time it is **6,101 coupled lines across two files**:

- `web/src/pages/dictation.astro` — **3,134 lines** (~814 lines of markup hosting nine
  tab sections, then a single ~2,318-line `<style>` block).
- `web/src/scripts/dictation-app.js` — **2,967 lines**: ~73 top-level functions in 15
  identifiable clusters, operating on shared mutable state objects, loaded as one blob.

This is backlog candidate **D** (frontend density paydown), promoted from "ride along
with the next dictation feature" to its own phase because the standing density invariant
lost every recent round: Phases 40, 45, 47, 48, and 53 each grew the page. Every future
dictation feature pays this tax until it is paid down.

Decompose both files into navigable, single-responsibility units — **section partials**
(Astro components per tab) and **behavior modules** (ES modules per concern) — fully
**behavior-preserving**: same DOM, same ids/classes, same behavior, the existing
page-content tests green **unmodified**, screenshot-verified per tab. This is the
frontend twin of Phases 26/31/32/34 (the backend decomposition lineage), and it defines
the frontend pattern the other monolith pages (`history.astro`, `index.astro`) can
follow later.

This is a **debt** phase. It ships no feature, no visual change, no behavior change.

---

## 1. The one thing you must not get wrong

**Behavior-preserving means the tests prove it, not you.**

- The existing integration tests that pin this page (`test_web_dictation_cockpit.py`
  and the dictation API/page tests listed in §3) must pass **unmodified**. Editing an
  assertion to make a refactor pass is failing the phase.
- The rendered page keeps its DOM contract: every `id`, every class the JS queries
  (~300+ `getElementById`/`querySelector` calls), every `data-section` hook. The JS
  modules keep the same fetch calls, the same localStorage keys, the same intervals.
- Each tab is screenshot-verified after its carve. The Astro scoped-CSS gotcha (§5) has
  bitten before: **a class existing in the bundle is not the same as it applying**.
- When in doubt between "cleaner" and "identical", ship identical. Cleanups that change
  behavior belong in a future phase with their own thesis.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md`, **7** checkboxes; `mkdir -p .tmp` first). A story
  flipping to `done` ships its `evidence-story-{n}.md` in the same commit; **one**
  done-flip per commit. The phase-exit story needs `evidence-story-{last}.md` **and**
  `final-summary.md` in the same commit. Status line is `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates the story header, this phase's
  `current-phase-status.md`, the project `README.md`, and any canon doc touched.
- **One PR per phase, merged on green CI** (Unit, Integration macOS, E2E macOS, Linux
  Smoke, Route screenshots). Branch `phase-54-dictation-frontend`; at close push + PR
  to `main` + merge.
- **Tests actually run.** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **The web bundle is gitignored.** Edit `web/src`, `cd web && npm run build`, commit
  source only, never `holdspeak/static/_built/`. JS-injected DOM needs `<style
  is:global>`; screenshot-verify.
- **High UI/UX bar still applies to a refactor:** the bar here is *pixel-faithful*.
  Ship before/after screenshot evidence per tab (`scripts/screenshot_*.py` pattern).
- **No user-facing doc changes expected** (internal-architecture docs only, HS-54-05),
  so the Phase-51 roadmap-vocab guard should stay untouched and green.

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

**`web/src/pages/dictation.astro` (3,134 lines) — the section map:**

- `:1-36` frontmatter — imports only `AppLayout` (layout) + `CommandPreview`
  (component). `web/src/components/` already exists (TopNav, Panel, Pill…), so
  per-page component folders have a home: `web/src/components/dictation/`.
- Markup, in order: cockpit hero (`:22-57`), `#kn-nudge` discovery nudge (`:38-97`),
  the nine-tab pill nav `.cockpit-tabs` (`:99-110`, `data-section` attrs), meta
  banners + project-root override (`:112-134`), then the section panels:
  Readiness (`:136-152`), Blocks (`:154-192`, active default), Runtime (`:194-328`),
  Memory & Depth (`:330-413`), Journal (`:415-471`), Dry-run (`:473-504`),
  Project Facts / KB (`:506-588`), Project Context / `.hs/` + guided-setup modal
  (`:590-737`), Agent Hooks (`:739-790`).
- `:791-814` — a hidden `CommandPreview` (bundles its CSS) and the script injection:
  the page loads `dictation-app.js` **via `?raw` import + `new Function()`**, not as
  an ES module. This is the pattern every page uses today.
- `:816-3134` — one `<style>` block (~2,318 lines), sectioned by feature with clear
  comment landmarks (hero, tabs, panels, blocks, readiness, knowledge explainers,
  guided setup, depth knobs, memory, journal, moment-of-truth, dry-run, activity
  nudges). The activity-nudge styles (`:2805-3134`) target **JS-injected DOM**.

**`web/src/scripts/dictation-app.js` (2,967 lines) — the 15 clusters:**

| # | Cluster | ~Lines |
|---|---|---|
| 1 | HTTP + utils (`api`, `escapeHtml`, `deepClone`…) | 21-357 (interleaved) |
| 2 | Block editor (load/render/CRUD/templates/preview) | 38-349 |
| 3 | Tab switching `activateSection` | 393-430 |
| 4 | Readiness snapshot | 431-602 |
| 5 | Project Facts (KB) | 608-759 |
| 6 | Project Context (`.hs/`) + guided setup + doc suggestion | 760-1128 |
| 7 | Runtime config + depth knobs | 1128-1331 |
| 8 | Memory + learning digest + corrections | 1328-1639 |
| 9 | Journal + replay + latency strip | 1641-1869 |
| 10 | Dry-run + moment-of-truth ritual | 1880-2251 |
| 11 | Agent context + hooks | 2262-2421 |
| 12 | Project-root override + recent roots | 2421-2540 |
| 13 | Discovery nudge (`#kn-nudge`) | 2541-2594 |
| 14 | Activity pre-briefing nudges | 2595-2843 |
| 15 | Init: event wiring + loaders + 10s `loadAgentContext` poll | 2845-2967 |

- Shared mutable state: `state` (blocks/editor/section/project), `kbState`, `hsState`,
  `knNudgeState`, plus constants (`STARTER_HS_FILES`, `REWRITE_PASS_DESC`, `AN_SVG`).
- localStorage keys: `holdspeak.projectRootOverride`, `holdspeak.recentProjectRoots`,
  `holdspeak.knNudgeDisabled`, `holdspeak.knNudgeDismissed`, `holdspeak.anPin`.

**Build + module reality:** plain Astro, `web/package.json` has `"type": "module"`, no
custom bundler config. **No page uses ES module imports for its app script today** —
Phase 54 establishes that pattern (HS-54-01). Astro natively bundles
`<script>` module tags; the open question is why `?raw` + `new Function()` was chosen
(suspected: to defeat Astro's processing/hoisting). HS-54-01 answers it with evidence.

**The tests that lock the page:**
- `tests/integration/test_web_dictation_cockpit.py` — hero, elevation, behavior hooks,
  knowledge explainers, empty states, guided setup.
- Plus the per-feature integration tests asserting page content + APIs:
  `test_web_dictation_blocks_api.py`, `test_web_dictation_corrections_api.py`,
  `test_web_dictation_journal.py`, `test_web_dictation_learning_digest.py`,
  `test_web_project_kb_api.py`, `test_web_dictation_settings_api.py`,
  `test_web_dry_run_api.py`, `test_dictation_moment_of_truth.py`,
  `test_dictation_journal_replay.py`; e2e: `test_dictation_enrichment_e2e.py`,
  `test_dictation_journal_e2e.py`, `test_dictation_learning_digest_spoken_e2e.py`.
- Screenshot scripts under `scripts/` (`screenshot_*.py` pattern) + the Route
  screenshots CI job.

---

## 4. Per-story definition of success

- **HS-54-01 — The module seam.** Decide and prove how a page's behavior splits into
  real ES modules under the Astro build. Investigate why pages load scripts via `?raw`
  + `new Function()`; either replace it for the dictation page with a bundled module
  entry (`<script>` + imports) or document precisely why it must stay and how modules
  compose under it. Prove the chosen seam by extracting **one small cluster** (the
  discovery nudge, cluster 13, is the suggested candidate: self-contained, 5 functions,
  2 localStorage keys) into `web/src/scripts/dictation/` with identical behavior.
  `npm run build` clean; the page works; evidence shows the decision + the proof.
- **HS-54-02 — Behavior modules.** Carve the remaining clusters of `dictation-app.js`
  into single-concern ES modules (suggested: `core.js` (state/api/utils/tabs),
  `blocks.js`, `readiness.js`, `knowledge.js` (KB + `.hs/` + guided setup +
  suggestion), `runtime.js`, `memory.js`, `journal.js`, `dryrun.js` (incl.
  moment-of-truth), `agent.js` (context + hooks + project root), `nudges.js`
  (discovery + activity), `init.js`), with explicit imports/exports replacing global
  reference. Same fetches, same localStorage keys, same DOM queries, same 10s poll.
  No file over ~600 lines. Full suite green unmodified.
- **HS-54-03 — Section partials.** Carve the nine tab panels (+ hero, nudge shell,
  meta banners) out of `dictation.astro` into Astro components under
  `web/src/components/dictation/`, **each carrying its own styles**; styles that
  target JS-injected DOM move into explicit `<style is:global>` blocks colocated with
  their partial. The page file becomes a thin composition (~target ≤300 lines). DOM
  contract identical; every tab screenshot-verified before/after; page-content tests
  green unmodified.
- **HS-54-04 — The density guard.** A unit test (the doc-drift-guard pattern) that
  locks the paydown: budgets for the dictation frontend (e.g. no file under
  `web/src/components/dictation/` or `web/src/scripts/dictation/` over ~600 lines;
  `dictation.astro` under its post-carve budget) so the page cannot silently regrow.
  Report the before/after numbers (6,101 → N across M files) in evidence.
- **HS-54-05 — Docs (dedicated docs story).** An internal architecture doc
  (`docs/internal/` — e.g. `ARCHITECTURE_WEB_FRONTEND.md`) recording the pattern:
  where a page's partials and modules live, how a new section is added, the
  `is:global` rule for JS-injected DOM, the module-seam decision from HS-54-01, and
  that `history.astro` / `index.astro` are the follow-up candidates. Linked from
  `CONTRIBUTING.md`'s dev section. Internal doc — roadmap vocabulary is fine here.
- **HS-54-06 — Closeout.** A dogfood click-through of all nine tabs against a live
  runtime (every loader fires, every form saves, nudge + pin + journal + replay +
  dry-run + moment-of-truth all behave), the full suite green, `npm run build` clean,
  0 `_built/` tracked, before/after metrics in `final-summary.md`, phase CLOSED,
  BACKLOG candidate D flipped to shipped, PR to `main` merged on green.

---

## 5. Gotchas that will bite you

- **Astro scoped CSS dies on JS-injected DOM.** The runtime-rendered cards (activity
  nudges, journal entries, learning digest, readiness cards, block list…) have no
  `data-astro-cid`, so scoped styles silently fail on them. When styles move into
  partials, anything targeting JS-rendered markup must be `<style is:global>`.
  **Screenshot-verify every tab** — a class present in the bundle ≠ it applies.
- **The `?raw` + `new Function()` loader is load-bearing until proven otherwise.**
  Do not assume ES modules just work; HS-54-01 exists to prove the seam on a small
  slice before 2,900 lines ride on it. If the answer is "keep the loader", the module
  split must still happen (e.g. modules composed at build), just documented honestly.
- **Init-order coupling.** Cluster 15 wires listeners and fires loaders in a specific
  order, and `activateSection` lazily loads per-tab data. Preserve order exactly;
  subtle races (e.g. the agent-context poll, the readiness-driven runtime hints) are
  behavior.
- **Shared state is shared.** `state.projectRootOverride` and friends are read across
  clusters (KB, `.hs/`, readiness, blocks). When modularizing, keep one shared state
  module rather than duplicating; do not "fix" the sharing.
- **The hidden `CommandPreview` at `:791` is intentional** — it bundles CSS + the copy
  delegator used by JS-rendered copy buttons. Keep it.
- **Tests pass unmodified or the phase failed.** If a content assertion breaks, the
  carve changed the DOM — fix the carve, not the test.
- **Do not touch the other pages.** `history.astro` (largest), `index.astro`,
  `welcome.astro` share the monolith pattern; they are explicitly out of scope.
  Phase 54 sets the pattern; a future phase applies it.

---

## 6. Where to start

`HS-54-01` (the module seam) is first and deliberately small: answer the loader
question with evidence and prove the pattern on the discovery-nudge cluster before
anything big moves. Then 02 (behavior modules) before 03 (markup partials) — the JS
carve de-risks the markup carve because the DOM contract stays untouched while modules
move. Suggested sequence: 01 → 02 → 03 → 04 → 05 → 06. Keep every step
behavior-preserving, keep the tests unmodified, and screenshot every tab you touch.
This is the phase that makes every future dictation feature cheaper.
