# Evidence - HS-102-02

- **Story:** HS-102-02 - Live Meeting — a working face
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Captured run — 2026-07-22T20:23:55Z

- **Command:** `sh -c cd web && npx vitest run --no-color && npx tsc --noEmit -p . && npm run tokens:gate --silent && cd .. && uv run pytest -q tests/unit/test_interior_canon_guard.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 06018d48a95e4f2db95e0b26b485f2ee6c4c3bb6

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/HoldSpeak/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/HoldSpeak/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/HoldSpeak/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/HoldSpeak/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/HoldSpeak/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/HoldSpeak/web/node_modules/axe-core/axe.js:28249:12) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:189:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:189:7) undefined

 Test Files  49 passed (49)
      Tests  312 passed (312)
   Start at  14:23:56
   Duration  6.32s (transform 3.44s, setup 4.79s, import 14.05s, tests 10.73s, environment 29.34s)

token gate: clean (61 allow-listed exceptions, all in use)
.........                                                                [100%]
9 passed in 0.13s
```

## The hands-first ledger (headed, staged instance, BEFORE code)

Corroborates story-02's problem statement exactly, live: opening the
Meetings→Record wing (`assets/hs-102-02-before-live-meeting-plumbing.png`,
captured during the phase-102 evaluation on a staged instance) showed a
`connected/00:00/0/recording` four-cell stat strip, a "Bookmark"
section (label "Optional label" + "Add bookmark" button), an "Intent
routing" preset `<Select>` defaulted to "Balanced," a "Preview route"
`<textarea>`, and a "Deferred plugin jobs" panel dumping
`total jobs`/`queued jobs`/`running jobs`/`failed jobs`/`queued due
jobs`/`scheduled retry jobs` as raw labeled numbers — all visible at
the FIRST instant a meeting starts, before a word is spoken. A live
walk also found the recording control (the top `Record` chip / the
dock's `RecordOrb`) both OPENS and STARTS in one action — there is no
reachable "configured before recording" idle state in normal use; the
idle-face code path (post-stop, or a resumed session) still had to be
fixed since it renders whenever `active` is false.

## The fix

- `LiveCore.tsx` gained a `door`/`doorOpen` gear split via
  `SurfaceWings`/`useWindowWings` (the same mechanism
  `DictationCore.tsx`'s "Configure dictation" door already uses) —
  Intent routing, Preview route, Deferred plugin jobs, and the
  Devices list all moved behind "Configure meeting."
- The `MetricStrip` four-cell grid is gone; `connection`/`duration`/
  `segments` compose into ONE `SurfaceFacts` line ("Recording · 00:00
  · N segments" while active, "<connection> · ready" at idle).
- The transcript now rides `SurfaceStream`/`SurfaceStreamEntry` (the
  same shape the Journal wears) instead of a bare `<ol>`.
- Bookmark is a `+ Bookmark` verb in the stream's own `controls` slot;
  clicking it opens a transient unlabeled "Name this moment…" input
  (EditInPlace-style: Enter or blur commits, Escape cancels) instead
  of a standalone form section. `/api/bookmark` only accepts a label
  at creation (no rename-after endpoint exists, and none was added —
  out of scope), so the composer defers the POST until commit rather
  than firing immediately with an empty label.
- `/api/state`, `/api/bookmark`, `/api/meeting/start`,
  `/api/meeting/stop`, `/api/intents/*`, `/api/plugin-jobs/*`,
  `/api/devices/health` all stayed byte-identical.

## Driven live, after (headed, staged instance, both viewports)

- `assets/hs-102-02-after-recording-face.png` (1440) — starting a
  meeting via the Record chip: `Stop meeting` leads, one quiet facts
  line, the transcript stream with a real captured segment, `Edit
  details` — zero stat-strip, zero forms, zero textareas.
- `assets/hs-102-02-after-bookmark-composer.png` — `+ Bookmark`
  clicked: the inline "Name this moment…" input appears in the
  stream's own head, not a section below.
- `assets/hs-102-02-after-configure-door.png` — the gear open: Intent
  routing / Preview route / Intelligence / Deferred plugin jobs, the
  transcript fully hidden — a real second face, not a scroll-down.
- `assets/hs-102-02-after-stop-idle.png` — after Stop: `Start meeting`
  leads, "Meeting saved." success banner, facts line reads "connected
  · ready," zero plumbing visible.
- `assets/hs-102-02-after-mobile-393.png` — the recording face at
  393px via the dock's `RecordOrb`: same composition, single column,
  no horizontal overflow.

## Guard added

`tests/unit/test_interior_canon_guard.py::
test_live_core_never_regresses_to_a_stat_strip` — refuses `MetricStrip`
anywhere in `LiveCore.tsx`, named by story.
