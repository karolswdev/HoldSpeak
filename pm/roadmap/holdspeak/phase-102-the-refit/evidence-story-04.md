# Evidence - HS-102-04

- **Story:** HS-102-04 - The Meetings wings — Outcomes / Record / Artifacts
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Captured run — 2026-07-22T22:26:17Z

- **Command:** `sh -c cd web && npx vitest run --no-color && npx tsc --noEmit -p . && npm run tokens:gate --silent && cd .. && uv run pytest -q tests/unit/test_interior_canon_guard.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0ae88db40c0e8543193ba31f61afe5e72f6eab19

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
   Start at  16:26:18
   Duration  8.97s (transform 4.14s, setup 6.34s, import 19.19s, tests 16.14s, environment 41.97s)

token gate: clean (61 allow-listed exceptions, all in use)
...........                                                              [100%]
11 passed in 0.17s
```

## The ledger (code-grounded — no live "before" walk this time)

Unlike the prior three stories, this ledger is grounded in reading
`HistoryCore.tsx` rather than a live "before" screenshot walk (the
Artifacts defect is code-verifiable and matches the round-7
inventory's own citation verbatim). Confirmed at `HistoryCore.tsx:474-489`
(pre-fix): the Artifacts wing, when populated, mapped each artifact
row to a `Disclosure` wrapping `<SurfaceCode>{body_markdown}</SurfaceCode>`
— a raw dump per artifact, exactly as convicted. The Outcomes list
(the rail's `SurfaceRows` of meetings) had no needs-you sort and no
`quiet` treatment — every row read identically regardless of state.
The Record wing (`ImportSection`) already had the round-7 drop-well
grammar (detail fields appear only once a file is picked) but no
leading verb row — recording lived only in the window header, not on
this wing's own face.

## The fix

- **Artifacts**: replaced the `Disclosure`/`SurfaceCode` loop with
  `SurfaceLibrary`/`SurfaceLibraryTile` — the exact components
  `DictationCore.tsx`'s Blocks wing already uses (`SurfaceLibrary` at
  Surface.tsx:457, `SurfaceLibraryTile` at 484). The artifact's
  `body_markdown` renders through `Material` as the tile FACE; name
  at primary; provenance (meeting title + `humanTime`) at secondary;
  an "Open" verb calls `openPrimitive(\`artifact:${id}\`)` — the
  round-9 object card, the same pattern `WorkbenchCore.tsx` already
  uses for artifacts. One real defect caught mid-drive: plugin
  artifact bodies self-title with a leading markdown heading matching
  their own name, which duplicated visually against the tile's spine
  — a regex strips a leading heading that exactly matches the title
  before rendering.
- **Outcomes**: `SurfaceRow` gained an optional `quiet` prop (a kit
  addition, `Surface.tsx`) — a row with nothing pending (a `success`/
  `neutral` tone) reads lower-weight than one needing a look (`error`/
  `warning`); the rail sorts needs-you rows first. `rowTone`/`needsYou`
  factor the existing state logic (no behavior change to the pill
  itself) so sort and quiet share one source of truth.
- **Record**: a leading verbs row (`Record meeting` + a quiet "or drop
  a recording below" caption) sits above the existing drop well — the
  wing now leads with its two verbs at display step, per rule 3;
  `ImportSection`'s already-shipped round-7 drop-well grammar
  (detail fields appear only once a file is picked) is untouched.
- `MeetingDetail`'s `outcomes` view (round 6, shipped) is byte-
  identical — only the `artifacts` branch changed. No wire route
  touched (`/api/meetings/*`, `/api/meetings/{id}/artifacts`
  byte-identical).

## Driven live, after (headed, staged instance, both viewports, REAL imported + intelligence-processed material)

A synthetic transcript (`.txt`, 5 segments naming a decision, two
action items, and a stated risk) was imported through the real
`/api/meetings/import` wire, then run through the REAL plugin chain
(`holdspeak intel --reroute <id> --profile balanced`, against the
LAN model at `192.168.1.43`) — 4 real artifacts synthesized
(Requirements Extractor, Project Detector, Decision Capture, Action
Owner Enforcer), not fixtures.

- `assets/hs-102-04-after-outcomes-list.png` (1440) — the rail: one
  settled meeting, `data-quiet="true"` confirmed in the DOM (checked
  directly, not just visually) — `<li class="surface-row" data-quiet="true">…Intelligence ready`.
- `assets/hs-102-04-after-outcomes-detail.png` — the Outcomes face
  (round 6, untouched) still reads correctly: "Needs you — 0 /
  Nothing waiting on you," the transcript folded as a receipt.
- `assets/hs-102-04-after-artifacts-library.png` — the Artifacts wing
  as a real 2×2 library: each tile's face IS the artifact's Material-
  rendered body (no raw dump, no duplicated heading after the fix),
  name at primary, "Q3 planning kickoff · 5m ago" at secondary, an
  Open verb per tile.
- `assets/hs-102-04-after-record-wing.png` — Record meeting (primary)
  + "or drop a recording below" lead above the drop well, both
  verbs display-step.
- `assets/hs-102-04-after-mobile-393.png` — the Artifacts library at
  393px: single column, tiles stack, no overflow.

## Walk legs grown, run live

`uv run python scripts/desk_gl_walk.py meetingflow` against this
staged instance:

```
meetingflow: arrival -> outcomes face in 3 interactions, 1 outcome concepts, transcript folded, no tab wall
meetingflow: artifacts wing is the library composition (populated)
```

The existing budget leg is unchanged and green (3 ≤ 4 interactions,
the round-6 Outcomes face untouched); the grown leg asserts the
Artifacts wing is `.surface-library` (or the honest empty state) and
never a `desk-pullout-md` dump — proven against REAL populated data
in this run, not just the empty branch.

## Guard added

`tests/unit/test_interior_canon_guard.py::
test_history_core_artifacts_wing_is_the_library` — pins
`SurfaceLibrary`/`SurfaceLibraryTile` usage in `HistoryCore.tsx`
(a positive assertion, since `Disclosure`/`SurfaceCode` stay
legitimately used elsewhere in the same file for the out-of-scope
Outcomes routing receipt).
