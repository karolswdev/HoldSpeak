# Evidence — HS-54-02: Behavior modules (carve dictation-app.js)

**Date:** 2026-06-11
**Branch:** `phase-54-dictation-frontend`

## 1. The carve

The 2,907-line `dictation-app.js` monolith (post-HS-54-01) is now a 19-line
entry importing twelve single-concern ES modules under
`web/src/scripts/dictation/`:

```
  19  dictation-app.js        (entry: imports init.js, documents the map)
  59  discovery-nudge.js      (DI removed — now imports api/projectRootParam from core)
 152  readiness.js
 161  init.js                 (event wiring + page-load sequence, original order)
 211  core.js                 (state, api, utils, activateSection + registry)
 211  runtime.js
 251  journal.js
 268  activity-nudges.js
 278  agent.js
 309  memory.js
 328  blocks.js
 374  dryrun.js               (incl. the moment-of-truth ritual, shared w/ journal)
 576  knowledge.js            (KB facts + .hs/ context + guided setup + suggestion)
```

Every module is under the ~600-line budget (largest: knowledge.js at 576).
Code moved **verbatim** (comments included); the only changes are
import/export statements, module headers, and the one structural idiom below.

## 2. The one structural idiom: the section-loader registry

`activateSection`'s per-tab loader dispatch and the cross-module
"reload that section if active" calls (knowledge → readiness, agent → kb/hs)
would have made the module graph cyclic with direct imports. Instead, core
holds a tiny registry: each feature module calls
`registerSection(name, loader)` at module-eval time, and `activateSection` /
`loadSection(name)` dispatch through it. The observable behavior is
identical: the same seven sections have the same seven loaders, registered
before any user event can fire (init.js imports every module before its
wiring runs). All other cross-module calls are direct imports; the resulting
graph is **acyclic** (verified by inspection: blocks→dryrun→knowledge/memory,
journal→dryrun, readiness→blocks/knowledge/runtime, agent→blocks/dryrun/
discovery-nudge — no back edges).

Three shared HTML helpers moved to core to keep it that way:
`renderRuntimeGuidance` (used by readiness + runtime), `renderDryTelemetry`
(knowledge + dryrun), `learnSigChip` + `plural` (memory + journal + dryrun).
The discovery-nudge module's HS-54-01 dependency injection is gone — it now
imports `api`/`projectRootParam` from core directly, as that story's notes
planned.

## 3. Behavior preserved — the locks

- Same endpoints, same five localStorage keys, same DOM queries, same init
  wiring order (init.js is the original line sequence verbatim), same 10s
  `loadAgentContext` poll.
- `setLearnWindow` (declared mid-init in the monolith) moved to memory.js;
  its two listeners wire identically in init.js.
- The activity-nudge pin-clear wiring moved verbatim into
  `wireActivityNudgePinClear()`, called from init.js at the original point in
  the sequence.
- **Zero test files changed in this story.** The `_app_js()` helper from
  HS-54-01 already reads the whole `scripts/dictation/` tree.

## 4. Test + build output (actually run, actually read)

```
$ cd web && npm run build
02:39:00 [build] 13 page(s) built in 5.06s          (clean, first try)
$ git ls-files holdspeak/static/_built | wc -l
0

$ uv run pytest -q tests/integration -k "dictation or cockpit"
158 passed, 1 skipped, 353 deselected in 26.28s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2540 passed, 17 skipped in 78.62s (0:01:18)
```

## 5. Live dogfoods (the modules on a real runtime)

`dogfood_story01.py` (the HS-54-01 nudge proof) re-run on the carved tree:
4/4 PASS.

`dogfood_story02.py` (new, committed beside this file) boots a real
`MeetingWebServer` + Playwright, treats **any uncaught page error as fatal**
(the instant tell for a missed export), walks all nine tabs, and exercises
the moved write paths:

```
PASS  tab readiness: activated + populated
PASS  tab blocks: activated + populated
PASS  tab kb: activated + populated
PASS  tab hs: activated + populated
PASS  tab hooks: activated + populated
PASS  tab runtime: activated + populated
PASS  tab memory: activated + populated
PASS  tab journal: activated + populated
PASS  tab dry-run: activated + populated
PASS  runtime: pipeline enabled via UI, save round-trips
PASS  dry-run: final text + stage trace + moment-of-truth rendered
PASS  ritual: 'Right' acknowledged
PASS  journal: the dry-run is journaled
PASS  memory: correction added + listed
PASS  memory: correction deleted
PASS  zero page errors across the whole run
RESULT: PASS
```

Screenshots: `screenshots/story02-readiness.png`, `story02-dryrun.png`,
`story02-journal.png`.

Dogfood honesty note: two early failures were **wrong dogfood assumptions,
not carve regressions** — a fresh temp config has the pipeline disabled, and
a disabled pipeline's dry-run takes a simple server path that executes no
stages and never journals (verified by probing the API directly:
`journal_id` absent from the response). The fix was to enable the pipeline
through the UI first (which doubles as the runtime-save round-trip), after
which the full stage trace + moment-of-truth + journal flow proves out.

## 6. What this hands HS-54-03

- The markup carve can now proceed with the DOM contract untouched — every
  `getElementById` the modules use is enumerable per module, which tells the
  partial boundaries exactly.
- Net line cost of modularity: 2,976 → 3,197 (+221 lines of imports/exports/
  headers across 13 files) — the price of navigability; the largest file
  dropped from 2,907 to 576.
