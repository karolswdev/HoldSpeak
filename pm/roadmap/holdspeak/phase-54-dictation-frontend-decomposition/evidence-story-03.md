# Evidence — HS-54-03: Section partials (carve dictation.astro)

**Date:** 2026-06-11
**Branch:** `phase-54-dictation-frontend`

## 1. The carve

The 3,131-line `dictation.astro` is now a **252-line composition** of fourteen
components under `web/src/components/dictation/`:

```
  62  BlocksSection.astro       62  ReadinessSection.astro
  79  KnNudge.astro             89  FactsSection.astro
  98  HooksSection.astro       154  RuntimeSection.astro
 167  KnowledgeStyles.astro    212  DryRunSection.astro
 213  ContextSection.astro     224  DepthControlStyles.astro
 248→252 dictation.astro (page) 349  SharedStyles.astro
 375  ActivityNudges.astro     439  JournalSection.astro
 499  MemorySection.astro
```

Markup moved verbatim; every `id`, class, and `data-*` hook is preserved. The
page keeps only the cockpit spine (hero, section tabs, project-root row,
agent-context banner, the hidden CommandPreview, the script entry) plus the
spine's scoped styles.

## 2. The style architecture (and the cascade-order trap, defused)

Astro 6 emits scoped styles with an `[data-astro-cid-…]` **attribute**
selector (verified in the built CSS) — so scoped rules add specificity and
never match JS-rendered DOM. Two consequences drove the design:

- **Three markup-less style components** (`SharedStyles`, `KnowledgeStyles`,
  `DepthControlStyles`) hold every rule used by more than one section
  (panels/forms/buttons/banners/boxes; the kn-* explainer grammar shared by
  Facts + Context; the depth/seg/switch grammar shared by Runtime + Memory).
  They are imported **before** the section partials so the emitted CSS keeps
  the pre-carve base-then-feature order — verified positionally in the built
  bundle (`.btn` @4.8k < `.fixit-yes` @46.6k; `input[type=text]` @4.2k <
  `.moment-form input` @45.5k; `.lat-seg` base < its stage tints).
- **Feature partials carry their own styles**: `is:global` where the rules
  target JS-rendered DOM (readiness cards, template cards, journal cards,
  learn digest, trace stages, moment/fixit, activity nudges, hook cards),
  scoped where the markup is static in that partial (the discovery nudge,
  the guided-setup panel, the runtime counters).

`is:global` is page-contained: Astro only ships a component's styles on
pages that import it, and no other page imports these.

## 3. The carve surfaced (and fixed) a real latent visual bug

While verifying, a computed-style probe on the **pre-carve** build showed the
scoped-CSS-on-JS-DOM trap had been silently biting shipped UI: JS-rendered
elements whose classes lived in the scoped block carried the design system's
class names but **no styling**, because the emitted `.block-card[data-astro-cid-…]`
selectors can never match runtime-injected DOM. Probe on a live server,
pre-carve build:

```
.template-card:        border=0px none        bg=rgba(0,0,0,0)        ← unstyled
.template-card .btn:   border=2px outset ...  bg=rgb(107,107,107)     ← raw UA button
```

Same probe, post-carve build (those rules now global, as the design intended):

```
.template-card:        border=1px solid rgba(255,255,255,0.12)  bg=rgb(21,23,29)
.template-card .btn:   border=1px solid rgba(255,255,255,0.12)  bg=rgb(21,23,29)
```

Affected pre-carve (all now fixed): JS-rendered block cards, template cards,
readiness cards + guidance blocks, the JS-rendered block editor's form
controls and buttons, JS-rendered meta-banner warn/error boxes, and the `.hs`
file-list cards. This is the same gotcha the repo already documented for
`is:global` (and the same class of find as HS-54-01's duplicate `escapeAttr`):
the carve did not change these rules' intent — it made them finally apply.
**Pixel-faithful therefore holds for everything that was actually styled;
the previously-unstyled JS-rendered elements now receive their intended
design-system styling.**

## 4. Tests (assertions unmodified) + build

The only test change is the `_page()` helper in
`test_web_dictation_cockpit.py`, which hardcoded the single-file layout; it
now reads the page **plus** `components/dictation/*.astro` (the same combined
source the page renders). Every assertion is byte-identical — the same
treatment HS-54-01 gave `_app_js()`.

```
$ uv run pytest -q tests/integration -k "dictation or cockpit"
158 passed, 1 skipped, 353 deselected in 26.34s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2540 passed, 17 skipped in 77.10s (0:01:17)

$ cd web && npm run build
13 page(s) built — clean; 0 _built/ tracked
```

The built artifact names still match the artifact-reading tests' globs
(`dictation.astro_astro_type_script*.js`, `dictation*.css` — verified by the
green `test_web_dictation_correction_ritual` / `journal_replay` /
`moment_of_truth` runs, which read the served bundle).

## 5. Live verification

- **Behavior:** `dogfood_story02.py` (all nine tabs + dry-run → moment-of-
  truth → journal → corrections + runtime save) re-run on the carved markup:
  **16/16 PASS, zero uncaught page errors**.
- **Visual:** a full nine-tab screenshot sweep on the carved build, committed
  as `screenshots/story03-<tab>.png` (readiness, blocks, kb, hs, hooks,
  runtime, memory, journal, dry-run). Spot-reviewed: the page spine (hero,
  solid-accent active tab, project-root row), the Facts explainer + worked
  example + teaching empty state, the Runtime depth fieldset (segmented
  control, switches), and the Blocks tab — where the JS-rendered cards now
  visibly carry their intended borders, surfaces, and accent pills (§3).

## 6. What this hands HS-54-04

- Final shape: page 252 lines; largest component 499 (`MemorySection`);
  largest behavior module 576 (`knowledge.js`). Budgets for the guard:
  page ≤ 300; components/modules ≤ 600.
- The `story02-*.png` evidence files were briefly overwritten by the dogfood
  re-run and restored from git (evidence is write-once); the dogfood writes
  to fixed names, so future re-runs after a story closes should copy results
  elsewhere or be re-pointed.
