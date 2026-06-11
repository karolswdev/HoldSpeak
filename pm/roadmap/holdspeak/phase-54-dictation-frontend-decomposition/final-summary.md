# Phase 54 — Dictation Frontend Decomposition: final summary

**Closed:** 2026-06-11 (opened and closed the same day). 6/6 stories shipped.
From [backlog](../BACKLOG.md) candidate **D** (frontend density paydown),
promoted from "ride along with the next dictation feature" to its own phase on
user direction (the agreed post-53 sequence 54 → I → J → K).

## What shipped

The dictation cockpit — 6,101 coupled lines across two files, grown five
phases running — is now a navigable, single-responsibility frontend, locked
against regrowth, fully behavior-preserving (and twice better than that: the
seam surfaced and fixed two real latent bugs).

| | Before | After |
|---|---|---|
| `dictation.astro` | 3,134 lines | **252** (a thin composition) |
| `dictation-app.js` | 2,967 lines | **19** (entry) + 12 modules (largest 576) |
| Components | — | 14 under `components/dictation/` (largest 499) |
| Largest file | 3,134 | 576 (**5.4× smaller**) |
| Regrowth lock | a soft invariant that lost 5 rounds | `test_frontend_density_guard.py` (5 tests, default suite) |

- **HS-54-01 — the module seam.** The `?raw` + `new Function()` loader was a
  Phase-10 migration shim with nothing depending on the eval; the page now
  loads a real bundled ES module. Client chunks ship un-minified (the shim
  always shipped full source anyway) via a `configEnvironment` override of
  Astro 6's hardcoded client minify. Proven live on the discovery-nudge
  cluster (4/4 Playwright dogfood).
- **HS-54-02 — behavior modules.** Twelve single-concern ES modules; the
  section-loader registry in `core.js` keeps the graph acyclic; zero test
  files changed; all-tabs dogfood 16/16 with zero page errors.
- **HS-54-03 — section partials.** Eleven section/feature partials carrying
  their own styles + three markup-less shared-style components imported first
  to preserve the cascade order (verified positionally in the built CSS);
  nine-tab screenshot sweep committed.
- **HS-54-04 — the density guard.** Page ≤300, entry ≤50, components/modules
  ≤600, carve-don't-bump messages, proven both ways.
- **HS-54-05 — docs.** `docs/internal/ARCHITECTURE_WEB_FRONTEND.md` (the
  seam, the registry, the scoping trap, the budgets, a six-step add-a-section
  walkthrough), linked from CONTRIBUTING.
- **HS-54-06 — closeout.** A seeded-activity nudge dogfood (cards → pin →
  clear → dismiss → discovery nudge; zero page errors) on top of the standing
  16/16 all-tabs dogfood; full suite green; this summary; PR to `main`.

## The two latent bugs the seam caught

1. **A duplicate `escapeAttr` declaration** — under the eval loader, function
   hoisting silently let the later declaration win; module scope rejected it
   at build time. The dead alias was removed (the live implementation kept).
2. **Silently unstyled JS-rendered UI.** Astro emits scoped styles with
   `[data-astro-cid]` attribute selectors, which never match runtime-injected
   DOM — so JS-rendered block cards, template cards, readiness cards, the
   JS-rendered editor's controls, and warn/error banners had shipped with
   **no styling** (verified by computed-style probes: `border: 0px none`,
   raw UA buttons). The carve moved those rules to `is:global` as the design
   intended; they now apply. Pixel-faithful holds for everything that was
   actually styled; these elements got their intended styles back.

## Evidence trail

Per story: `evidence-story-0{1..6}.md`; dogfoods `dogfood_story01.py`
(nudge module, 4/4), `dogfood_story02.py` (all nine tabs + write paths,
16/16), `dogfood_story06.py` (seeded nudges + pin, 6/6) — all asserting
**zero uncaught page errors**; screenshots under `screenshots/`
(`story01-*`, `story02-*`, `story03-<tab>` ×9, `story06-*`).

Final state: full suite **2545 passed, 17 skipped** (+5 = the guard);
`npm run build` clean; 0 `_built/` tracked; every page-content assertion in
the suite byte-identical (two test *helpers* learned the carved tree).

## Lessons

- **Prove the seam on a small slice first.** HS-54-01's deliberately tiny
  scope caught the loader question, the strict-mode question, and the
  minification/test interaction before 2,900 lines depended on the answers.
- **"Behavior-preserving" needs instruments, not eyes.** The zero-pageerror
  Playwright harness and computed-style probes caught what reading diffs and
  looking at screenshots could not (and proved a "bug" was pre-existing).
- **Dogfood failures are claims to verify, not regressions to fix.** Twice
  the dogfood was wrong about the environment (a disabled pipeline's dry-run
  neither stages nor journals) — probing the server settled it each time.
- **Evidence is write-once; dogfoods write to fixed paths.** A re-run
  overwrote two committed PNGs (restored from git). Future dogfoods should
  emit to per-run names or be re-pointed after a story closes.

## Follow-ups (not this phase)

- `history.astro` (largest page) and `index.astro` still use the monolith
  pattern + the `?raw` loader — and may carry the same latent scoped-CSS bug
  (probe first). Documented in the architecture doc; a future density phase.
- The Route screenshots CI job will re-baseline where the latent-bug fix
  changed pixels (JS-rendered cards now styled) — expected and desirable.
