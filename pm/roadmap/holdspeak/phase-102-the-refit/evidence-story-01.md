# Evidence - HS-102-01

- **Story:** HS-102-01 - Runs on — destinations easy as heck
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Captured run — 2026-07-22T18:19:39Z

- **Command:** `sh -c cd web && npx vitest run --no-color && npx tsc --noEmit -p . && npm run tokens:gate --silent && cd .. && uv run pytest -q tests/unit/test_interior_canon_guard.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a3d5e033e5e35d9f42646fa027ac337cf567f67d

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
   Start at  12:19:40
   Duration  7.76s (transform 4.74s, setup 6.81s, import 17.54s, tests 12.88s, environment 36.27s)

token gate: clean (61 allow-listed exceptions, all in use)
........                                                                 [100%]
8 passed in 0.13s
```

## The hands-first ledger (headed, staged instance, 1440 + 393, BEFORE code)

Driven against a fresh isolated `HOME` on port 8788, 2026-07-21/22.
`assets/hs-102-01-before-form-stack.png`: `New destination` was a
literal `Name` / `Kind`-as-`<Select>` / `Base URL` / `Model` /
"Requires its own key on the hub" checkbox / `Context window` stack
in a `NEW RUNS ON DESTINATION` section bolted below the `DESTINATIONS`
list — the exact composition canon rule 1 outlaws. Switching Kind DID
already gate which fields rendered underneath (This device →
`Model file`; mesh node → `Node name`), confirming the "kind gates
fields" logic existed in code already, just wearing a bare `<Select>`
and a floating form the person had to scroll to reach.

## The fix

- `Surface.tsx`'s `SurfaceBay` gained an `expanded`/`editor` slot (the
  kit gap the design direction named) and a `ghost`/`onClick` pair for
  a dashed "add" bay — reusable by any future switchboard, not a
  `ProfilesCore`-local fork.
- `ProfilesCore.tsx`: create/edit is now `KIND_BAYS` (Endpoint / This
  device / Paired device / Mesh node) rendered as `.settings-bays`
  choice buttons — the SAME markup pattern `RuntimeDestination`
  (`settingsBespoke.tsx`) already proved for Settings — followed by a
  `SurfaceGroup`/`SurfaceSettingRow` field set that shows only the
  chosen kind's fields. Editing opens IN PLACE on the destination's
  own `SurfaceBay` (no section below the list); creating is the
  switchboard's own ghost "+ New destination" bay, which becomes the
  same expanded editor — one mechanism for both acts. An invalid Base
  URL refuses inline (row caption + a top `InlineMessage`) before the
  wire call fires; `/api/profiles` stayed byte-identical.
- One bug caught and fixed during the live drive: the first pass used
  `Checkbox` (which renders its own label) inside a
  `SurfaceSettingRow` that ALSO carries the label — the text rendered
  twice as an ugly orange button. Swapped to `SurfaceToggle` (a bare
  switch, the same piece `RuntimeDestination`'s "Warm on start" row
  uses) — confirmed fixed in `hs-102-01-after-kind-this-device.png`.

## Driven live, after (headed, staged instance, both viewports)

- `assets/hs-102-01-after-choice-bays.png` (1440) — `+ New destination`
  opens the Endpoint bay in place: choice bays up top, only
  Name/Base URL/Model/key-toggle/Context window below.
- `assets/hs-102-01-after-kind-this-device.png` — switching to "This
  device" swaps the field set live (Model file only) with the
  `SurfaceToggle` fix in place.
- `assets/hs-102-01-after-invalid-url-refusal.png` — `not-a-url` typed
  into Base URL refuses by name ("The Base URL isn't a valid http(s)
  address.") both as a caption under the field and a top banner; Save
  did not create a third destination.
- `assets/hs-102-01-after-edit-in-place.png` — `Edit` on an existing
  bay opens the SAME editor ON that bay (switchboard list still
  visible below), not a separate section.
- `assets/hs-102-01-after-make-default-delete.png` — Make default
  flipped the `DEFAULT` tag/route styling; the two-step Delete removed
  the other destination; both verbs still ride the unchanged
  PUT/DELETE wire.
- `assets/hs-102-01-after-mobile-393.png` — the same choice-bay editor
  at 393px: stacks single-column, no horizontal overflow.

## Guard added

`tests/unit/test_interior_canon_guard.py::
test_profiles_core_never_regresses_to_a_field_stack` — refuses `<Field`
or `<Select` anywhere in `ProfilesCore.tsx`, named by story, so a
future "quick fix" can't quietly bring the old form back.
