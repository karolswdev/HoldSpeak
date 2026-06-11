# Evidence — HS-54-01: The module seam (decide + prove on one cluster)

**Date:** 2026-06-11
**Branch:** `phase-54-dictation-frontend`

## 1. The loader question, answered

**What it was:** every page loaded its app script via
`import factorySource from "../scripts/<page>-app.js?raw"` + `new Function(factorySource)()`
(`dictation.astro:802-813` pre-change). `git log -S "new Function"` traces the
pattern to **HS-10-09** ("rebuild /dictation on the design system") — the comment in
the page said it plainly: the *legacy* script ran at module level and the eval was a
migration shim to reuse it verbatim. It is an artifact of the Phase-10 rebuild, not
architecture.

**What depended on the eval:** nothing. Verified before cutting:

- No inline `onclick=` handlers anywhere (`grep -c "onclick" → 0` in both the page
  and the JS; all wiring is `addEventListener`, 76 call sites) — so no window-global
  function requirements.
- No `DOMContentLoaded` reliance (the comment was stale); init runs at top level,
  and an Astro-emitted `type="module"` script is deferred — identical timing to the
  shim (the shim itself ran inside such a module).
- No sloppy-mode dependence: the only suspicious bare assignments
  (`readiness =`, `rows =`, `data =`, `payload =`) are all `let`-declared in scope
  (verified each site).
- Sole consumer of `dictation-app.js` is `dictation.astro`.

**Decision: replace the shim with a real bundled ES module import** for the
dictation page (`<script> import "../scripts/dictation-app.js";</script>`). Other
pages keep their shims — explicitly out of scope; the pattern doc (HS-54-05) names
them as follow-ups.

## 2. The seam surfaced a real latent bug

Module scope is stricter than the eval, and the very first build caught a genuine
defect: **`escapeAttr` was declared twice** (a thin `escapeHtml` alias at `:365` and
a full attribute-escaper at `:2192`). Rollup:

```
[ERROR] ... ModuleScope.addDeclaration ...
  Location: web/src/scripts/dictation-app.js:2192:9
```

Under the eval shim, function hoisting silently made the later declaration win for
the *entire* file — the `:365` alias was dead code that looked alive. The
behavior-preserving fix: delete the dead alias, keep the surviving implementation
(the one that was actually live for all callers). A comment at the old site records
why.

## 3. The proof extraction (cluster 13 → a real module)

`web/src/scripts/dictation/discovery-nudge.js` (new): the HS-47-04 discovery nudge
moved verbatim — `knNudgeState`, dismiss/disable/hide/show, both localStorage keys
(`holdspeak.knNudgeDisabled`, `holdspeak.knNudgeDismissed`) — with its two monolith
dependencies (`api`, `projectRootParam`) **injected** via `initDiscoveryNudge()`
(they still live in the monolith; switch to direct imports when the shared core
module exists in HS-54-02). The storage key that the init wiring touched directly
moved behind a new `knNudgeDisableGlobally()` export so keys stay private to the
module. The monolith imports the six names; behavior call sites unchanged.

Bundle verification: the dictation chunk contains the module
(`grep -rl "holdspeak.knNudgeDismissed" → dictation.astro...js`) and no longer
contains `new Function`; the other pages' chunks still do (untouched).

## 4. Un-minified client build (and why)

With real bundling, Astro minifies page scripts — which broke 7 integration tests
that assert source markers (`renderRuntimeGuidance`, `replayJournalEntry`,
`wireFixit(host)`…) in the **served chunk**. Under the shim, users always downloaded
the complete un-minified source (the `?raw` string), so un-minified output *is* the
behavior-preserving choice: `astro.config.mjs` now disables client minification.
Astro 6 hardcodes `minify: true` for the client environment
(`astro/dist/core/build/static-build.js`), ignoring `vite.build.minify`, so the
override uses the supported `configEnvironment` plugin hook. Loopback serving makes
size irrelevant; readable JS suits a local-first tool.

**Test-assertion integrity:** every page-content assertion in the suite is
**byte-identical**. The single test-file change is the `_app_js()` *helper* in
`test_web_dictation_cockpit.py`, which hardcoded the single-file layout
(`read_text` on `dictation-app.js`); it now reads the entry **plus**
`scripts/dictation/*.js` — the same combined source the page bundles into one
chunk. Its assertions are untouched.

## 5. Test + build output (actually run, actually read)

Dictation slice after the change:

```
$ uv run pytest -q tests/integration -k "dictation or cockpit"
158 passed, 1 skipped, 353 deselected in 25.81s
```

(The skip is the standing llama-cpp model-file gate, not new.)

Build:

```
$ cd web && npm run build
02:18:24 [build] 13 page(s) built in 5.10s
02:18:24 [build] Complete!
$ git ls-files holdspeak/static/_built | wc -l
0
```

Full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`):

```
2540 passed, 17 skipped in 78.81s (0:01:18)
```

## 6. Live dogfood (the module on a real runtime)

`dogfood_story01.py` (committed beside this file) boots a real
`MeetingWebServer` + Playwright and drives the carved module's whole surface:

```
PASS  1. nudge visible via the carved module
PASS  2. per-project dismiss persists across reload
PASS  3. nudge returns once dismissal is cleared
PASS  4. global 'stop suggesting' persists across reload
RESULT: PASS
```

Screenshots: `screenshots/story01-nudge-visible.png`,
`screenshots/story01-nudge-dismissed.png`.

## 7. What this hands HS-54-02

- The seam is proven: page entry is a bundled ES module; carved modules live in
  `web/src/scripts/dictation/` with explicit exports.
- Monolith-resident deps (`api`, `projectRootParam`, shared `state`) are injected
  for now; HS-54-02's `core.js` replaces injection with direct imports.
- The `_app_js()` helper already reads the whole `scripts/dictation/` tree, so
  further carves need no test-infrastructure changes.
- Watch for more eval-masked duplicates: module scope will reject them at build
  time (that is a feature).
