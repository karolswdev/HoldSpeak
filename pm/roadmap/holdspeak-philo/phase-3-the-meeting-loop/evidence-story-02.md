# Evidence - PHILO-3-02

- **Story:** PHILO-3-02 - See and find the summary (A2)
- **Status:** done
- **Date:** 2026-09-23

## Proof

### Captured run — 2026-09-23T15:48:01Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j4.meetings_import.imported --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/preflight-import`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-DVBCVHGd.js'] hub=http://127.0.0.1:56427 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5i_222_y/.local/share/holdspeak/holdspeak.db engine=real
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/preflight-import/20260923T154801Z-case.j4.meetings_import.imported-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/preflight-import/20260923T154801Z-case.j4.meetings_import.imported-astra-1440/after.png']
NOTE: placeholder(s) ['meeting_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /meetings/0/id equals the declared value
```

### Captured run — 2026-09-23T15:56:37Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build && npm run bundle:gate


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (11 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (822 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-3-02/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28249:12) undefined

 Test Files  303 passed (303)
      Tests  2800 passed (2800)
   Start at  09:56:46
   Duration  89.55s (transform 5.05s, setup 11.91s, import 32.52s, tests 60.10s, environment 52.41s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1689 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/api.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store/compositorSlice.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/SpeakFace.tsx but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/App.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/PreparePosture.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/recall/RecallFace.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ImportSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/MeetingReview.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-23T15:59:28Z

- **Command:** `npm --prefix web run bundle:gate`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text

> holdspeak-web@0.0.1 bundle:gate
> node scripts/check-bundle.mjs

bundle gate passed (Desk JS 1319310 B; Desk CSS 317635 B; source maps 0)
```

### Captured run — 2026-09-23T16:01:58Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.summary_text --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-BIa4O2Vp.js'] hub=http://127.0.0.1:57283 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-od_szjdu/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: []
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/jobs/0/meeting_id', 'value': '7ea05e6f'} at 'protocol: GET /api/intel/jobs' — /jobs/0/meeting_id is absent; wanted '7ea05e6f'
```

### Captured run — 2026-09-23T16:10:49Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.summary_text --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-BIa4O2Vp.js'] hub=http://127.0.0.1:57770 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-q395pi3d/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary/20260923T161049Z-case.j6.run_summary.summary_text-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[data-testid=concierge-add-engine]").first to be visible
```

### Captured run — 2026-09-23T16:12:19Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.summary_text --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-BIa4O2Vp.js'] hub=http://127.0.0.1:57851 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-x2olw9ue/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary/20260923T161220Z-case.j6.run_summary.summary_text-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary/20260923T161220Z-case.j6.run_summary.summary_text-astra-1440/after.png']
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T16:13:40Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.summary_text --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-BIa4O2Vp.js'] hub=http://127.0.0.1:57926 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5oqrlw6a/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary/20260923T161340Z-case.j6.run_summary.summary_text-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final-summary/20260923T161340Z-case.j6.run_summary.summary_text-astra-393/after.png']
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T16:15:12Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j5.meeting_open.planned_host_disclosed --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/j5-prefix`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-BIa4O2Vp.js'] hub=http://127.0.0.1:58011 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-8ytg45tl/.local/share/holdspeak/holdspeak.db engine=real
JOB: j5
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/j5-prefix/20260923T161512Z-case.j5.meeting_open.planned_host_disclosed-astra-393/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'hit_target', 'min_width': 44, 'min_height': 44} at '[data-testid=arrival-run-intel]' — control rect {'x': 278, 'y': 381, 'w': 97, 'h': 24} is smaller than 44x44px
```

### Captured run — 2026-09-23T16:19:31Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build && npm run bundle:gate


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (11 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (822 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-3-02/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28249:12) undefined

 Test Files  303 passed (303)
      Tests  2800 passed (2800)
   Start at  10:19:40
   Duration  87.99s (transform 4.67s, setup 11.79s, import 31.79s, tests 59.63s, environment 51.68s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1689 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/api.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store/compositorSlice.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/SpeakFace.tsx but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/App.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/PreparePosture.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/recall/RecallFace.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ImportSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/MeetingReview.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InterviewPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/NewWorkbenchChooser.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ScheduleCreateWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ThreadComposer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/RoomActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/windowCommands.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/atmosphereActivity.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/infoContract.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/keymap.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/newThought.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/ThreadsSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/DecisionsView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/useDeskChangedRefresh.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/ChangePlacesCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/threads.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/callLoopWiring.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/CallChip.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/hooks/useChatImport.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/ThreadsSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                     0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2      4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2          4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2          4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2      4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2      4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2              4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2              5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2              5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2               5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2       5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2       5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff      5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2               5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2               5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff      5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff       5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff           5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff       5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff       5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff           5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff               6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff               6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff               6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff        6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff        7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff                7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff                7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff                7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2      7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2      7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2                7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                   7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2                7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                   7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                   7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2                7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff                 9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                    9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                    9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                   10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff      10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2           10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff      10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2           10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2           10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2      11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2      12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2      12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2          12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2          13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2          13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff            13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff            13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff            13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff           16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff       16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff       16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff       16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff           16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff           16.99 kB
../holdspeak/static/_built/assets/rainy-masonry-DIBtQ-m6.webp                            17.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2         21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2         21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                  23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                  24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                  24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff          27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff          28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                   30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                   31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                   31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2              35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2              36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2              36.26 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-77YHD8bZ.woff               47.56 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-BxGbmqWO.woff               48.49 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-CIVaiw4L.woff               48.67 kB
../holdspeak/static/_built/assets/wet-concrete-B8Jlfxi3.webp                             61.50 kB
../holdspeak/static/_built/assets/wet-asphalt-nQmNY0GR.webp                              65.97 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-cE2vkmv2.css                  0.50 kB │ gzip:   0.23 kB
../holdspeak/static/_built/assets/CadenceCore-BcDWJsh4.css                                0.63 kB │ gzip:   0.34 kB
../holdspeak/static/_built/assets/RepoWindow-Dmvmdom7.css                                 1.59 kB │ gzip:   0.64 kB
../holdspeak/static/_built/assets/SettingsCore-BVsDobrN.css                               2.51 kB │ gzip:   0.68 kB
../holdspeak/static/_built/assets/XtermPane-DDGTF8rc.css                                  3.62 kB │ gzip:   0.99 kB
../holdspeak/static/_built/assets/RoadmapWindow-BpQxUh51.css                              3.81 kB │ gzip:   1.07 kB
../holdspeak/static/_built/assets/PeopleCore-DawtcWHJ.css                                 4.94 kB │ gzip:   1.29 kB
../holdspeak/static/_built/assets/DoorCore-CASx1vIJ.css                                   5.56 kB │ gzip:   1.45 kB
../holdspeak/static/_built/assets/ConciergeCore-B7BZbZ8k.css                              8.77 kB │ gzip:   1.79 kB
../holdspeak/static/_built/assets/DictationCore-DMwTh7Sg.css                             13.08 kB │ gzip:   2.39 kB
../holdspeak/static/_built/assets/WorkbenchWindow-Bbq47XG1.css                           13.47 kB │ gzip:   2.50 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-oz-meLoZ.css                         22.75 kB │ gzip:   4.41 kB
../holdspeak/static/_built/assets/index-B77rbR73.css                                     91.91 kB │ gzip:  31.03 kB
../holdspeak/static/_built/assets/desk-BB4mjvrk.css                                     317.77 kB │ gzip:  47.39 kB
../holdspeak/static/_built/assets/atmosphereLighting-D2uEdGO0.js                          0.14 kB │ gzip:   0.14 kB
../holdspeak/static/_built/assets/WelcomePage-BMmkVkUM.js                                 0.38 kB │ gzip:   0.27 kB
../holdspeak/static/_built/assets/core-layout-Di0kxsFQ.js                                 0.44 kB │ gzip:   0.26 kB
../holdspeak/static/_built/assets/PresencePage-CyuTDwSs.js                                0.56 kB │ gzip:   0.38 kB
../holdspeak/static/_built/assets/core-hooks-BAknnnD7.js                                  0.57 kB │ gzip:   0.37 kB
../holdspeak/static/_built/assets/atmosphereControls-nB4jNh-k.js                          0.77 kB │ gzip:   0.41 kB
../holdspeak/static/_built/assets/Filter-CG0zrvgb.js                                      0.91 kB │ gzip:   0.48 kB
../holdspeak/static/_built/assets/ChangePlacesCore-Dl_Q3ySI.js                            0.92 kB │ gzip:   0.49 kB
../holdspeak/static/_built/assets/useUndoReceipt-WsAK8cti.js                              1.63 kB │ gzip:   0.74 kB
../holdspeak/static/_built/assets/SetupCore-BZ-Ul-UG.js                                   2.07 kB │ gzip:   1.02 kB
../holdspeak/static/_built/assets/api-D9Zm--RI.js                                         2.11 kB │ gzip:   0.70 kB
../holdspeak/static/_built/assets/greenhouseScene-CbiPReIQ.js                             2.48 kB │ gzip:   1.34 kB
../holdspeak/static/_built/assets/midnightArchiveScene-Cks10AbM.js                        2.49 kB │ gzip:   1.36 kB
../holdspeak/static/_built/assets/deepSeaScene-Kph6_2or.js                                2.81 kB │ gzip:   1.52 kB
../holdspeak/static/_built/assets/nightTrainScene-DxGfS3yD.js                             2.90 kB │ gzip:   1.57 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-B7nY4OY0.js                   2.99 kB │ gzip:   1.32 kB
../holdspeak/static/_built/assets/CompanionCore-Dw777k5s.js                               3.00 kB │ gzip:   1.35 kB
../holdspeak/static/_built/assets/WorkbenchesHomeCore-Bql-GTOe.js                         3.04 kB │ gzip:   1.41 kB
../holdspeak/static/_built/assets/laundromatScene-BNGSS1T1.js                             3.05 kB │ gzip:   1.58 kB
../holdspeak/static/_built/assets/radioStationScene-s-EUOSVI.js                           3.20 kB │ gzip:   1.61 kB
../holdspeak/static/_built/assets/ActivityCore-BOnWPm5W.js                                3.24 kB │ gzip:   1.44 kB
../holdspeak/static/_built/assets/RoadmapWindow-DhpEUEIS.js                               3.62 kB │ gzip:   1.43 kB
../holdspeak/static/_built/assets/settingsWallpaper-CDDf3aF6.js                           3.62 kB │ gzip:   1.64 kB
../holdspeak/static/_built/assets/CommandsCore-klP9GO9d.js                                4.00 kB │ gzip:   1.70 kB
../holdspeak/static/_built/assets/CalendarSnapshotReviewCore-Bf71JJ95.js                  4.06 kB │ gzip:   1.68 kB
../holdspeak/static/_built/assets/helpers-M5flVTQa.js                                     4.24 kB │ gzip:   1.59 kB
../holdspeak/static/_built/assets/api-DHnx4rDB.js                                         5.27 kB │ gzip:   1.73 kB
../holdspeak/static/_built/assets/Atmosphere-CAv7lJn3.js                                  5.32 kB │ gzip:   2.23 kB
../holdspeak/static/_built/assets/RepoWindow-COaw6lFU.js                                  5.79 kB │ gzip:   2.43 kB
../holdspeak/static/_built/assets/usePrimitiveDetail-BAxZCpJx.js                          8.53 kB │ gzip:   3.16 kB
../holdspeak/static/_built/assets/ProcessCore-Cu3pvNqp.js                                 9.42 kB │ gzip:   3.60 kB
../holdspeak/static/_built/assets/ComponentsCore-CZ_W1nGb.js                              9.97 kB │ gzip:   3.74 kB
../holdspeak/static/_built/assets/LiveCore-BApZwyBF.js                                   10.22 kB │ gzip:   4.01 kB
../holdspeak/static/_built/assets/BufferResource-vz7AKVUi.js                             10.62 kB │ gzip:   2.80 kB
../holdspeak/static/_built/assets/CadenceCore-BbZ4Qig9.js                                10.78 kB │ gzip:   3.67 kB
../holdspeak/static/_built/assets/BitmapFont-B5vs-2FZ.js                                 12.87 kB │ gzip:   4.71 kB
../holdspeak/static/_built/assets/webworkerAll-FcBhowEo.js                               15.48 kB │ gzip:   4.91 kB
../holdspeak/static/_built/assets/sceneKit-DiGkm6FV.js                                   16.55 kB │ gzip:   6.13 kB
../holdspeak/static/_built/assets/DoorCore-Ci01OEw_.js                                   17.50 kB │ gzip:   5.26 kB
../holdspeak/static/_built/assets/CanvasRenderer-CMIr0n_j.js                             17.54 kB │ gzip:   5.88 kB
../holdspeak/static/_built/assets/lanternGardenScene-xeGn5N5B.js                         18.98 kB │ gzip:   7.14 kB
../holdspeak/static/_built/assets/ConciergeCore-Dqw0Dc2r.js                              22.94 kB │ gzip:   6.90 kB
../holdspeak/static/_built/assets/rainyCityScene-P7sWSGGp.js                             28.01 kB │ gzip:   9.68 kB
../holdspeak/static/_built/assets/PeopleCore-D3xCD1aS.js                                 28.21 kB │ gzip:   7.67 kB
../holdspeak/static/_built/assets/WebGPURenderer-GAijBhLF.js                             38.99 kB │ gzip:  10.90 kB
../holdspeak/static/_built/assets/WorkbenchWindow-CAHEk2NH.js                            41.92 kB │ gzip:  13.72 kB
../holdspeak/static/_built/assets/browserAll-C312mDlS.js                                 43.12 kB │ gzip:  11.33 kB
../holdspeak/static/_built/assets/DictationCore-DNqt_Dit.js                              46.37 kB │ gzip:  14.81 kB
../holdspeak/static/_built/assets/RenderTargetSystem-e9VugnBt.js                         46.38 kB │ gzip:  12.73 kB
../holdspeak/static/_built/assets/SettingsCore-DgkWJSBQ.js                               46.86 kB │ gzip:  14.27 kB
../holdspeak/static/_built/assets/HistoryCore-ShUZcHPH.js                                47.99 kB │ gzip:  14.68 kB
../holdspeak/static/_built/assets/react-SZyUX699.js                                      48.46 kB │ gzip:  17.18 kB
../holdspeak/static/_built/assets/WebGLRenderer-Bh3BD5Wy.js                              68.80 kB │ gzip:  18.90 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-y0TIxck5.js                         161.21 kB │ gzip:  44.27 kB
../holdspeak/static/_built/assets/index-CT6RwACn.js                                     219.35 kB │ gzip:  69.02 kB
../holdspeak/static/_built/assets/WorldStage-ti6txedt.js                                338.64 kB │ gzip: 107.27 kB
../holdspeak/static/_built/assets/XtermPane-C6o2sTDy.js                                 364.14 kB │ gzip:  93.99 kB
../holdspeak/static/_built/assets/UnrealBloomPass-COc2GKT4.js                           558.38 kB │ gzip: 141.32 kB
../holdspeak/static/_built/assets/desk-BG1UHnoK.js                                    1,319.31 kB │ gzip: 421.62 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.36s

> holdspeak-web@0.0.1 bundle:gate
> node scripts/check-bundle.mjs

bundle gate passed (Desk JS 1319310 B; Desk CSS 317774 B; source maps 0)
```

### Captured run — 2026-09-23T16:23:29Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j5.meeting_open.planned_host_disclosed --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58196 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-79os71ym/.local/share/holdspeak/holdspeak.db engine=real
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162329Z-case.j5.meeting_open.planned_host_disclosed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162329Z-case.j5.meeting_open.planned_host_disclosed-astra-393/after.png']
NOTE: predicate: '192.168.1.43 · LAN' in observe_at text
```

### Captured run — 2026-09-23T16:24:12Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j7.hub_restart.intel_retained --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58249 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hj8gb7ca/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162412Z-case.j7.hub_restart.intel_retained-astra-1440/after.png']
NOTE: placeholder(s) ['before_summary'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /intel/summary is non-empty
```

### Captured run — 2026-09-23T16:25:02Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.retrying --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58363 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ymvbmd53/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162502Z-case.j6.run_summary.retrying-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162502Z-case.j6.run_summary.retrying-astra-393/after.png']
NOTE: predicate: 'RETRYING' in observe_at text
```

### Captured run — 2026-09-23T16:25:51Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.intel_failed --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58431 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-bb26n3fb/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162552Z-case.j6.run_summary.intel_failed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162552Z-case.j6.run_summary.intel_failed-astra-393/after.png']
NOTE: predicate: 'LAST ERROR' in observe_at text
```

### Captured run — 2026-09-23T16:27:47Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.j6.run_summary.intel_failed --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58543 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-0rz42daw/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162747Z-case.j6.run_summary.intel_failed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162747Z-case.j6.run_summary.intel_failed-astra-393/after.png']
NOTE: predicate: 'FAILED\nLAST ATTEMPT' in observe_at text
```

### Captured run — 2026-09-23T16:28:37Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_retry --viewport 393 --engine replayed`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58631 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1nv6arax/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162837Z-case.j6.run_summary.intel_retry-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162837Z-case.j6.run_summary.intel_retry-astra-393/after.png']
NOTE: predicate: POST /api/intel/retry/9996265f answered 200, wanted 200 (body sha256 f1ea07a1e51a); response body contains the declared admission facts
```

### Captured run — 2026-09-23T16:29:11Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_running --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58717 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-7e2hhncp/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162911Z-case.j6.run_summary.intel_running-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162911Z-case.j6.run_summary.intel_running-astra-1440/after.png']
NOTE: predicate: /jobs/0/status equals the declared value
```

### Captured run — 2026-09-23T16:29:40Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.no_engine_no_verb --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58792 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-gqryhe92/.local/share/holdspeak/holdspeak.db engine=none
JOB: j5
VERDICT: blocked terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162940Z-case.j5.meeting_open.no_engine_no_verb-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T162940Z-case.j5.meeting_open.no_engine_no_verb-astra-393/after.png']
NOTE: predicate: BLOCKED: observe_at not present ('[data-testid=arrival-run-intel]'); an absence inside a scope that does not exist proves nothing
NOTE: BLOCKED, not failed: the rig gathered the whole run (setup, before, trigger, wait, after) but no verdict is earned from it.
```

### Captured run — 2026-09-23T16:30:50Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.no_engine_no_verb --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58911 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hzj0yguy/.local/share/holdspeak/holdspeak.db engine=none
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163050Z-case.j5.meeting_open.no_engine_no_verb-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163050Z-case.j5.meeting_open.no_engine_no_verb-astra-393/after.png']
NOTE: predicate: 'Run summary' absent at observe_at
```

### Captured run — 2026-09-23T16:31:45Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.summary_text --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:58957 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-8o0je9kf/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163145Z-case.j6.run_summary.summary_text-astra-393/after.png']
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T16:32:55Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.summary_text --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59025 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zptnkn99/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163255Z-case.j6.run_summary.summary_text-astra-1440/after.png']
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T16:33:31Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.arrival_load.reload_persisted --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59086 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-qbqyleeo/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163331Z-case.j7.arrival_load.reload_persisted-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163331Z-case.j7.arrival_load.reload_persisted-astra-393/after.png']
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T16:34:47Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.arrival_load.reload_persisted --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59200 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zmck1z2n/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163447Z-case.j7.arrival_load.reload_persisted-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163447Z-case.j7.arrival_load.reload_persisted-astra-393/after.png']
NOTE: predicate: observe_at text is 'The meeting covered three decisions: Mayyachan will write a migration plan by Friday, Leo Martinez will test hub restart retrieval on Tuesday, and Priya Shah is assigned to use recorded provider replies for isolated rig tests.', wanted 'The meeting covered three decisions: Mayyachan will write a migration plan by Friday, Leo Martinez will test hub restart retrieval on Tuesday, and Priya Shah is assigned to use recorded provider replies for isolated rig tests.'
```

### Captured run — 2026-09-23T16:37:06Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.arrival_load.reload_persisted --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59284 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-7ys_00v0/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163706Z-case.j7.arrival_load.reload_persisted-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163706Z-case.j7.arrival_load.reload_persisted-astra-393/after.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The meeting covered three decisions: using SQ for the local ledger, keeping summary retrieval after a hub restart, and using recorded provider replies for isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, and Leo Martinez will test restart retrieval on Tuesday.', wanted 'The meeting covered three decisions: using SQ for the local ledger, keeping summary retrieval after a hub restart, and using recorded provider replies for isolated rig tests. Mayyachan is tasked with writing the migration plan by Friday, and Leo Martinez will test restart retrieval on Tuesday.'
```

### Captured run — 2026-09-23T16:38:02Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.arrival_load.reload_persisted --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59354 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-a876cxys/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163802Z-case.j7.arrival_load.reload_persisted-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163802Z-case.j7.arrival_load.reload_persisted-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163802Z-case.j7.arrival_load.reload_persisted-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The Synthetic Architect Meeting established three decisions: using SQ for the local meeting ledger, keeping summary retrieval on the local desk after a hub restart, and using a recorded provider reply for isolated rig tests. Action items were assigned to Mayyachan for the migration plan by Friday and Leo Martinez for testing restart retrieval by Tuesday.', wanted 'The Synthetic Architect Meeting established three decisions: using SQ for the local meeting ledger, keeping summary retrieval on the local desk after a hub restart, and using a recorded provider reply for isolated rig tests. Action items were assigned to Mayyachan for the migration plan by Friday and Leo Martinez for testing restart retrieval by Tuesday.'
```

### Captured run — 2026-09-23T16:38:44Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.hub_restart.intel_retained --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59417 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-a3aii21u/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163844Z-case.j7.hub_restart.intel_retained-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163844Z-case.j7.hub_restart.intel_retained-astra-393/after.png']
NOTE: placeholder(s) ['before_summary'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /intel/summary is non-empty
```

### Captured run — 2026-09-23T16:39:37Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.record_start.capture_recording --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59514 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-tvl9tl6t/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163937Z-case.j4.record_start.capture_recording-astra-1440/blocked.png']
NOTE: BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without substituting microphone ownership.') is not implemented; a label alone substitutes nothing. The one implemented substitution is 'engine_reply'.
```

### Captured run — 2026-09-23T16:39:59Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.record_start.capture_recording --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59605 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-k_yla3k2/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T163959Z-case.j4.record_start.capture_recording-astra-393/blocked.png']
NOTE: BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without substituting microphone ownership.') is not implemented; a label alone substitutes nothing. The one implemented substitution is 'engine_reply'.
```

### Captured run — 2026-09-23T16:40:28Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.meeting_stop.capture_finalized --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59629 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-axbstd68/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164028Z-case.j4.meeting_stop.capture_finalized-astra-1440/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, wanted True
```

### Captured run — 2026-09-23T16:40:58Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.meeting_stop.capture_finalized --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59738 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hddcepku/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164058Z-case.j4.meeting_stop.capture_finalized-astra-393/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, wanted True
```

### Captured run — 2026-09-23T16:41:27Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.meeting_stop.transcription_absent --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59781 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-t7hekznr/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164127Z-case.j4.meeting_stop.transcription_absent-astra-1440/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, wanted True
```

### Captured run — 2026-09-23T16:41:54Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.meeting_stop.transcription_absent --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59822 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-vpzr_of8/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164154Z-case.j4.meeting_stop.transcription_absent-astra-393/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, wanted True
```

### Captured run — 2026-09-23T16:42:24Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.record_only.no_speech_head --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59865 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-nibd16nh/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164224Z-case.j4.record_only.no_speech_head-astra-1440/blocked.png']
NOTE: BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without substituting microphone ownership.') is not implemented; a label alone substitutes nothing. The one implemented substitution is 'engine_reply'.
```

### Captured run — 2026-09-23T16:42:50Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.record_only.no_speech_head --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59888 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-76p4yvwv/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164250Z-case.j4.record_only.no_speech_head-astra-393/blocked.png']
NOTE: BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without substituting microphone ownership.') is not implemented; a label alone substitutes nothing. The one implemented substitution is 'engine_reply'.
```

### Captured run — 2026-09-23T16:43:21Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.route_intelligence_run.refusal --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59915 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-a6n_m53n/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164321Z-case.j6.route_intelligence_run.refusal-astra-1440/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/segments', 'value': []} at 'protocol: GET /api/meetings/1f8ccabd' — /segments = [{'text': 'Hold Speaksynthetic Architect Meeting. Decision 1. Use SQ like for the local meeting ledger. Owner, Mayyachan. Action. Mayyachan will write the Migration Plan by Friday. Decision 2. Keep summary retrieval on the local desk after a hub restart. Owner, Leo Martinez. Action. Leo Martinez will test restart retrieval on Tuesday. Decision 3. Use a recorded provider reply for isolated rig tests. Owner, Priya Shah. Action. creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating creating', 'speaker': 'Recording', 'speaker_id': None, 'start_time': 0.0, 'end_time': 30.0, 'is_bookmarked': False, 'device_id': None}, {'text': 'named failure offense before ship, Marker, hold speaks synthetic arquitect 3.', 'speaker': 'Recording', 'speaker_id': None, 'start_time': 30.0, 'end_time': 34.67525, 'is_bookmarked': False, 'device_id': None}], wanted []
```

### Captured run — 2026-09-23T16:43:53Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.route_intelligence_run.refusal --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2a8882eed1d6b0559226d4c899c9dd6e0f58797f

```text
PASS: live
BRAIN: astra
SOURCE: aac7544eae3c1f30a5928c95825a8cb654c582cc dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CT6RwACn.js'] hub=http://127.0.0.1:59968 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-bcozl66f/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T164353Z-case.j6.route_intelligence_run.refusal-astra-393/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/segments', 'value': []} at 'protocol: GET /api/meetings/150e6ad4' — /segments = [{'text': 'Hold Speaksynthetic Architect Meeting. Decision 1. Use SQ like for the local meeting ledger. Owner, Mayyachan. Action. Mayyachan will write the Migration Plan by Friday. Decision 2. Keep summary retrieval on the local desk after a hub restart. Owner, Leo Martinez. Action. Leo Martinez will test restart retrieval on Tuesday. Decision 3. Use a recorded provider reply for isolated rig tests. Owner, Priya Shah. Action. Olga Shah will add a near-', 'speaker': 'Recording', 'speaker_id': None, 'start_time': 0.0, 'end_time': 30.0, 'is_bookmarked': False, 'device_id': None}, {'text': 'named failure offense before ship, Marker, hold speaks synthetic arquitect 3.', 'speaker': 'Recording', 'speaker_id': None, 'start_time': 30.0, 'end_time': 34.67525, 'is_bookmarked': False, 'device_id': None}], wanted []
```

### Captured run — 2026-09-23T16:49:18Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build && npm run bundle:gate


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (11 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (826 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-3-02/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28249:12) undefined

 Test Files  306 passed (306)
      Tests  2806 passed (2806)
   Start at  10:49:30
   Duration  97.49s (transform 5.13s, setup 13.17s, import 35.43s, tests 62.52s, environment 60.65s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1690 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/api.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store/compositorSlice.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/SpeakFace.tsx but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/App.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/PreparePosture.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/recall/RecallFace.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ImportSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/MeetingReview.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InterviewPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/NewWorkbenchChooser.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ScheduleCreateWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ThreadComposer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/RoomActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/windowCommands.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/atmosphereActivity.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/infoContract.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/keymap.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/newThought.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/ThreadsSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/DecisionsView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/useDeskChangedRefresh.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/ChangePlacesCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/threads.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/callLoopWiring.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/CallChip.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/hooks/useChatImport.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/ThreadsSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                     0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2      4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2          4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2          4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2      4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2      4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2              4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2              5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2              5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2               5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2       5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2       5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff      5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2               5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2               5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff      5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff       5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff           5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff       5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff       5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff           5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff               6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff               6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff               6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff        6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff        7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff                7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff                7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff                7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2      7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2      7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2                7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                   7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2                7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                   7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                   7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2                7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff                 9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                    9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                    9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                   10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff      10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2           10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff      10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2           10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2           10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2      11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2      12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2      12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2          12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2          13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2          13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff            13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff            13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff            13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff           16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff       16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff       16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff       16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff           16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff           16.99 kB
../holdspeak/static/_built/assets/rainy-masonry-DIBtQ-m6.webp                            17.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2         21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2         21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                  23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                  24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                  24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff          27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff          28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                   30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                   31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                   31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2              35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2              36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2              36.26 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-77YHD8bZ.woff               47.56 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-BxGbmqWO.woff               48.49 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-CIVaiw4L.woff               48.67 kB
../holdspeak/static/_built/assets/wet-concrete-B8Jlfxi3.webp                             61.50 kB
../holdspeak/static/_built/assets/wet-asphalt-nQmNY0GR.webp                              65.97 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-cE2vkmv2.css                  0.50 kB │ gzip:   0.23 kB
../holdspeak/static/_built/assets/CadenceCore-BcDWJsh4.css                                0.63 kB │ gzip:   0.34 kB
../holdspeak/static/_built/assets/RepoWindow-Dmvmdom7.css                                 1.59 kB │ gzip:   0.64 kB
../holdspeak/static/_built/assets/SettingsCore-BVsDobrN.css                               2.51 kB │ gzip:   0.68 kB
../holdspeak/static/_built/assets/XtermPane-DDGTF8rc.css                                  3.62 kB │ gzip:   0.99 kB
../holdspeak/static/_built/assets/RoadmapWindow-BpQxUh51.css                              3.81 kB │ gzip:   1.07 kB
../holdspeak/static/_built/assets/PeopleCore-DawtcWHJ.css                                 4.94 kB │ gzip:   1.29 kB
../holdspeak/static/_built/assets/DoorCore-CASx1vIJ.css                                   5.56 kB │ gzip:   1.45 kB
../holdspeak/static/_built/assets/ConciergeCore-B7BZbZ8k.css                              8.77 kB │ gzip:   1.79 kB
../holdspeak/static/_built/assets/DictationCore-DMwTh7Sg.css                             13.08 kB │ gzip:   2.39 kB
../holdspeak/static/_built/assets/WorkbenchWindow-Bbq47XG1.css                           13.47 kB │ gzip:   2.50 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-oz-meLoZ.css                         22.75 kB │ gzip:   4.41 kB
../holdspeak/static/_built/assets/index-B77rbR73.css                                     91.91 kB │ gzip:  31.03 kB
../holdspeak/static/_built/assets/desk-C_h0bGUY.css                                     319.05 kB │ gzip:  47.58 kB
../holdspeak/static/_built/assets/atmosphereLighting-D2uEdGO0.js                          0.14 kB │ gzip:   0.14 kB
../holdspeak/static/_built/assets/WelcomePage-CaYVuohs.js                                 0.38 kB │ gzip:   0.27 kB
../holdspeak/static/_built/assets/core-layout-Dz7e88BB.js                                 0.44 kB │ gzip:   0.26 kB
../holdspeak/static/_built/assets/PresencePage-DOP4KALw.js                                0.56 kB │ gzip:   0.37 kB
../holdspeak/static/_built/assets/core-hooks-DTJSznWU.js                                  0.57 kB │ gzip:   0.37 kB
../holdspeak/static/_built/assets/atmosphereControls-nB4jNh-k.js                          0.77 kB │ gzip:   0.41 kB
../holdspeak/static/_built/assets/Filter-DykoKdgm.js                                      0.91 kB │ gzip:   0.48 kB
../holdspeak/static/_built/assets/ChangePlacesCore-hBXmfkjX.js                            0.92 kB │ gzip:   0.49 kB
../holdspeak/static/_built/assets/useUndoReceipt-WsAK8cti.js                              1.63 kB │ gzip:   0.74 kB
../holdspeak/static/_built/assets/SetupCore-CcA4GiAW.js                                   2.07 kB │ gzip:   1.02 kB
../holdspeak/static/_built/assets/api-P3eVP7Dx.js                                         2.11 kB │ gzip:   0.70 kB
../holdspeak/static/_built/assets/greenhouseScene-CbiPReIQ.js                             2.48 kB │ gzip:   1.34 kB
../holdspeak/static/_built/assets/midnightArchiveScene-Cks10AbM.js                        2.49 kB │ gzip:   1.36 kB
../holdspeak/static/_built/assets/deepSeaScene-Kph6_2or.js                                2.81 kB │ gzip:   1.52 kB
../holdspeak/static/_built/assets/nightTrainScene-DxGfS3yD.js                             2.90 kB │ gzip:   1.57 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-CCcvpvq4.js                   2.99 kB │ gzip:   1.32 kB
../holdspeak/static/_built/assets/CompanionCore-CIl4kaDc.js                               3.00 kB │ gzip:   1.35 kB
../holdspeak/static/_built/assets/WorkbenchesHomeCore-DxdFiqyn.js                         3.04 kB │ gzip:   1.41 kB
../holdspeak/static/_built/assets/laundromatScene-BNGSS1T1.js                             3.05 kB │ gzip:   1.58 kB
../holdspeak/static/_built/assets/radioStationScene-s-EUOSVI.js                           3.20 kB │ gzip:   1.61 kB
../holdspeak/static/_built/assets/ActivityCore-DZ-MzE0J.js                                3.24 kB │ gzip:   1.44 kB
../holdspeak/static/_built/assets/RoadmapWindow-paW5xTYk.js                               3.62 kB │ gzip:   1.43 kB
../holdspeak/static/_built/assets/settingsWallpaper-C91xbh_Z.js                           3.62 kB │ gzip:   1.64 kB
../holdspeak/static/_built/assets/CommandsCore-wOhT6KIw.js                                4.00 kB │ gzip:   1.70 kB
../holdspeak/static/_built/assets/CalendarSnapshotReviewCore-CfSgti9f.js                  4.06 kB │ gzip:   1.68 kB
../holdspeak/static/_built/assets/helpers-M5flVTQa.js                                     4.24 kB │ gzip:   1.59 kB
../holdspeak/static/_built/assets/api-C6Hau47u.js                                         5.27 kB │ gzip:   1.73 kB
../holdspeak/static/_built/assets/Atmosphere-Cj6WjBTH.js                                  5.32 kB │ gzip:   2.23 kB
../holdspeak/static/_built/assets/RepoWindow-CjVGDN1g.js                                  5.79 kB │ gzip:   2.43 kB
../holdspeak/static/_built/assets/usePrimitiveDetail-CpcQaKD7.js                          8.53 kB │ gzip:   3.16 kB
../holdspeak/static/_built/assets/ProcessCore-fnL8uQOk.js                                 9.42 kB │ gzip:   3.60 kB
../holdspeak/static/_built/assets/ComponentsCore-IyBOEeRo.js                              9.97 kB │ gzip:   3.74 kB
../holdspeak/static/_built/assets/LiveCore-yNyzpqae.js                                   10.22 kB │ gzip:   4.01 kB
../holdspeak/static/_built/assets/BufferResource-ormXD_eL.js                             10.62 kB │ gzip:   2.80 kB
../holdspeak/static/_built/assets/CadenceCore-agsoQGfi.js                                10.78 kB │ gzip:   3.67 kB
../holdspeak/static/_built/assets/BitmapFont-BHCO1YiC.js                                 12.87 kB │ gzip:   4.71 kB
../holdspeak/static/_built/assets/webworkerAll-BIqZBt6F.js                               15.48 kB │ gzip:   4.91 kB
../holdspeak/static/_built/assets/sceneKit-DiGkm6FV.js                                   16.55 kB │ gzip:   6.13 kB
../holdspeak/static/_built/assets/DoorCore-CHIELbJm.js                                   17.50 kB │ gzip:   5.26 kB
../holdspeak/static/_built/assets/CanvasRenderer-B0P16QBG.js                             17.54 kB │ gzip:   5.88 kB
../holdspeak/static/_built/assets/lanternGardenScene-xeGn5N5B.js                         18.98 kB │ gzip:   7.14 kB
../holdspeak/static/_built/assets/ConciergeCore-CEoAc8kw.js                              22.94 kB │ gzip:   6.90 kB
../holdspeak/static/_built/assets/rainyCityScene-P7sWSGGp.js                             28.01 kB │ gzip:   9.68 kB
../holdspeak/static/_built/assets/PeopleCore-ISykJBP0.js                                 28.21 kB │ gzip:   7.67 kB
../holdspeak/static/_built/assets/WebGPURenderer-CDH2kXcX.js                             38.99 kB │ gzip:  10.91 kB
../holdspeak/static/_built/assets/WorkbenchWindow-C9vnjlXC.js                            41.92 kB │ gzip:  13.72 kB
../holdspeak/static/_built/assets/browserAll-DOvycZdb.js                                 43.12 kB │ gzip:  11.33 kB
../holdspeak/static/_built/assets/DictationCore-Bt36hqW3.js                              46.37 kB │ gzip:  14.82 kB
../holdspeak/static/_built/assets/RenderTargetSystem-SztNYqvF.js                         46.38 kB │ gzip:  12.73 kB
../holdspeak/static/_built/assets/SettingsCore-RAqQsuTD.js                               46.86 kB │ gzip:  14.28 kB
../holdspeak/static/_built/assets/HistoryCore-DymhHEol.js                                47.99 kB │ gzip:  14.68 kB
../holdspeak/static/_built/assets/react-SZyUX699.js                                      48.46 kB │ gzip:  17.18 kB
../holdspeak/static/_built/assets/WebGLRenderer-CRybbopf.js                              68.80 kB │ gzip:  18.91 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-DY8s_-Oj.js                         161.21 kB │ gzip:  44.27 kB
../holdspeak/static/_built/assets/index-EPIMRzZ0.js                                     219.35 kB │ gzip:  69.01 kB
../holdspeak/static/_built/assets/WorldStage-DJGAxGpX.js                                338.64 kB │ gzip: 107.27 kB
../holdspeak/static/_built/assets/XtermPane-B-H6MkzJ.js                                 364.14 kB │ gzip:  93.99 kB
../holdspeak/static/_built/assets/UnrealBloomPass-COc2GKT4.js                           558.38 kB │ gzip: 141.32 kB
../holdspeak/static/_built/assets/desk-DaRb6wah.js                                    1,320.31 kB │ gzip: 422.02 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.85s

> holdspeak-web@0.0.1 bundle:gate
> node scripts/check-bundle.mjs

bundle gate passed (Desk JS 1320308 B; Desk CSS 319048 B; source maps 0)
```

### Captured run — 2026-09-23T16:52:03Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.meetings_import.imported --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:60614 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-yo8ro8np/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165203Z-case.j4.meetings_import.imported-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165203Z-case.j4.meetings_import.imported-astra-1440/after.png']
NOTE: placeholder(s) ['meeting_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /meetings/0/id equals the declared value
```

### Captured run — 2026-09-23T16:52:29Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j4.meetings_import.imported --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:60705 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-y8lst9th/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165230Z-case.j4.meetings_import.imported-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165230Z-case.j4.meetings_import.imported-astra-393/after.png']
NOTE: placeholder(s) ['meeting_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /meetings/0/id equals the declared value
```

### Captured run — 2026-09-23T16:52:52Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.route_disclosed --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:60750 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ap7abpp_/.local/share/holdspeak/holdspeak.db engine=real
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165252Z-case.j5.meeting_open.route_disclosed-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165252Z-case.j5.meeting_open.route_disclosed-astra-1440/after.png']
NOTE: predicate: '192.168.1.43 · LAN' in observe_at text
```

### Captured run — 2026-09-23T16:53:35Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.route_disclosed --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:60839 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-_gngo__e/.local/share/holdspeak/holdspeak.db engine=real
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165335Z-case.j5.meeting_open.route_disclosed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165335Z-case.j5.meeting_open.route_disclosed-astra-393/after.png']
NOTE: predicate: '192.168.1.43 · LAN' in observe_at text
```

### Captured run — 2026-09-23T16:54:07Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.planned_host_disclosed --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:60901 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-0ob9jtxr/.local/share/holdspeak/holdspeak.db engine=real
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165407Z-case.j5.meeting_open.planned_host_disclosed-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165407Z-case.j5.meeting_open.planned_host_disclosed-astra-1440/after.png']
NOTE: predicate: '192.168.1.43 · LAN' in observe_at text
```

### Captured run — 2026-09-23T16:54:48Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.planned_host_disclosed --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:60998 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rqazpavo/.local/share/holdspeak/holdspeak.db engine=real
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165448Z-case.j5.meeting_open.planned_host_disclosed-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165448Z-case.j5.meeting_open.planned_host_disclosed-astra-393/after.png']
NOTE: predicate: '192.168.1.43 · LAN' in observe_at text
```

### Captured run — 2026-09-23T16:55:15Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j5.meeting_open.no_engine_no_verb --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:61087 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-n_xd80i1/.local/share/holdspeak/holdspeak.db engine=none
JOB: j5
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165515Z-case.j5.meeting_open.no_engine_no_verb-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165515Z-case.j5.meeting_open.no_engine_no_verb-astra-1440/after.png']
NOTE: predicate: 'Run summary' absent at observe_at
```

### Captured run — 2026-09-23T16:55:39Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_queued --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:61174 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-48p6_kkk/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165539Z-case.j6.run_summary.intel_queued-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165539Z-case.j6.run_summary.intel_queued-astra-1440/after.png']
NOTE: predicate: POST /api/meetings/b0fc9b63/intelligence/run answered 200, wanted 200 (body sha256 8c2501cf494d); response body contains the declared admission facts
```

### Captured run — 2026-09-23T16:56:10Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_queued --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:61297 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-09exbvfb/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165610Z-case.j6.run_summary.intel_queued-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165610Z-case.j6.run_summary.intel_queued-astra-393/after.png']
NOTE: predicate: POST /api/meetings/417d1882/intelligence/run answered 200, wanted 200 (body sha256 005358692d0b); response body contains the declared admission facts
```

### Captured run — 2026-09-23T16:56:43Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_running --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:61366 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-u5w4l78q/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165643Z-case.j6.run_summary.intel_running-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T165643Z-case.j6.run_summary.intel_running-astra-393/after.png']
NOTE: predicate: /jobs/0/status equals the declared value
```

### Captured run — 2026-09-23T16:57:13Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_ready --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 143
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
(no output)
```

### Captured run — 2026-09-23T17:02:19Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_ready --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62302 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-99z88c6f/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170219Z-case.j6.run_summary.intel_ready-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170219Z-case.j6.run_summary.intel_ready-astra-1440/after.png']
NOTE: predicate: /intel_job/status equals the declared value
```

### Captured run — 2026-09-23T17:03:12Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_ready --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62402 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-_tgp47as/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170312Z-case.j6.run_summary.intel_ready-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170312Z-case.j6.run_summary.intel_ready-astra-393/after.png']
NOTE: predicate: /intel_job/status equals the declared value
```

### Captured run — 2026-09-23T17:03:52Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.host_named --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62487 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1ctvlznf/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170352Z-case.j6.run_summary.host_named-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170352Z-case.j6.run_summary.host_named-astra-1440/after.png']
NOTE: predicate: /run_receipt/attempts/0/host equals the declared value
```

### Captured run — 2026-09-23T17:04:31Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.host_named --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62565 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-0mup6vc3/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170431Z-case.j6.run_summary.host_named-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170431Z-case.j6.run_summary.host_named-astra-393/after.png']
NOTE: predicate: /run_receipt/attempts/0/host equals the declared value
```

### Captured run — 2026-09-23T17:05:07Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_failed --viewport 1440 --engine replayed`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62630 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-bfvzoyi9/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170507Z-case.j6.run_summary.intel_failed-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170507Z-case.j6.run_summary.intel_failed-astra-1440/after.png']
NOTE: predicate: 'FAILED\nLAST ATTEMPT' in observe_at text
```

### Captured run — 2026-09-23T17:05:39Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.intel_retry --viewport 1440 --engine replayed`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62703 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-evpfo_86/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170539Z-case.j6.run_summary.intel_retry-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170539Z-case.j6.run_summary.intel_retry-astra-1440/after.png']
NOTE: predicate: POST /api/intel/retry/4b4db058 answered 200, wanted 200 (body sha256 f1ea07a1e51a); response body contains the declared admission facts
```

### Captured run — 2026-09-23T17:06:18Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.retrying --viewport 1440 --engine replayed`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62776 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-0_mk0wnq/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170618Z-case.j6.run_summary.retrying-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170618Z-case.j6.run_summary.retrying-astra-1440/after.png']
NOTE: predicate: 'RETRYING' in observe_at text
```

### Captured run — 2026-09-23T17:06:48Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.retrying --viewport 393 --engine replayed`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62851 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ukg5nztv/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170648Z-case.j6.run_summary.retrying-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170648Z-case.j6.run_summary.retrying-astra-393/after.png']
NOTE: predicate: 'RETRYING' in observe_at text
```

### Captured run — 2026-09-23T17:07:19Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.route_intelligence_run.no_assignment --viewport 1440 --engine none`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62909 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-vh432g_x/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170719Z-case.j6.route_intelligence_run.no_assignment-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170719Z-case.j6.route_intelligence_run.no_assignment-astra-1440/after.png']
NOTE: predicate: POST /api/meetings/2d869ea4/intelligence/run answered 409, wanted 409 (body sha256 ba6ed5c078fa); response body contains the declared admission facts
```

### Captured run — 2026-09-23T17:07:56Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.route_intelligence_run.no_assignment --viewport 393 --engine none`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62955 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kcz2k2t7/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170756Z-case.j6.route_intelligence_run.no_assignment-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170756Z-case.j6.route_intelligence_run.no_assignment-astra-393/after.png']
NOTE: predicate: POST /api/meetings/152f971a/intelligence/run answered 409, wanted 409 (body sha256 502af3598200); response body contains the declared admission facts
```

### Captured run — 2026-09-23T17:08:32Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.summary_text --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:62998 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-r83fnl2c/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170832Z-case.j6.run_summary.summary_text-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170832Z-case.j6.run_summary.summary_text-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170832Z-case.j6.run_summary.summary_text-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T17:09:13Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.summary_text --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:63074 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-9g6ukxbk/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170913Z-case.j6.run_summary.summary_text-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170913Z-case.j6.run_summary.summary_text-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170913Z-case.j6.run_summary.summary_text-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T17:09:59Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.arrival_load.reload_persisted --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:63169 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-pftlt8tt/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170959Z-case.j7.arrival_load.reload_persisted-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170959Z-case.j7.arrival_load.reload_persisted-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T170959Z-case.j7.arrival_load.reload_persisted-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is 'The team decided to use SQ like for the local meeting ledger, keep summary retrieval on the local desk after a hub restart, and use a recorded provider reply for isolated rig tests. Action items were assigned to Mayyachan and Leo Martinez.', wanted 'The team decided to use SQ like for the local meeting ledger, keep summary retrieval on the local desk after a hub restart, and use a recorded provider reply for isolated rig tests. Action items were assigned to Mayyachan and Leo Martinez.'
```

### Captured run — 2026-09-23T17:14:16Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.hub_restart.intel_retained --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:63250 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-55gim1i2/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T171417Z-case.j7.hub_restart.intel_retained-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T171417Z-case.j7.hub_restart.intel_retained-astra-1440/after.png']
NOTE: placeholder(s) ['before_summary'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /intel/summary is non-empty
```

### Captured run — 2026-09-23T17:15:09Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j7.hub_restart.intel_retained --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-EPIMRzZ0.js'] hub=http://127.0.0.1:63343 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ur5a1nlk/.local/share/holdspeak/holdspeak.db engine=real
JOB: j7
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T171510Z-case.j7.hub_restart.intel_retained-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T171510Z-case.j7.hub_restart.intel_retained-astra-393/after.png']
NOTE: placeholder(s) ['before_summary'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: /intel/summary is non-empty
```

### Captured run — 2026-09-23T17:16:06Z

- **Command:** `/bin/zsh -c set -o pipefail; uv run --no-sync pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee docs/internal/philo/phase-3/summary/integration/full-python.raw.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
...........ssssssssssssssssssssss.........ssssss............s..s........ [  0%]
..................ssssssssssss....sssssssss......................ssss... [  1%]
.ssssss........................F........................................ [  1%]
........................................................................ [  2%]
......................F..................xxxx.......F..........F........ [  3%]
...........FF....FF...F......................FF......................... [  3%]
ssssssssss.s............................................................ [  4%]
........................................................................ [  4%]
.....................s...............sss................................ [  5%]
........................................................................ [  6%]
........................................................................ [  6%]
........................................................................ [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
....................................ss....................ss............ [  9%]
..........................................................s............. [  9%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 11%]
........................................................................ [ 12%]
........................................................................ [ 12%]
........................................................................ [ 13%]
........................................................................ [ 14%]
........................................................................ [ 14%]
......ss..........s..................................................... [ 15%]
........................................................................ [ 16%]
........................................................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 19%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 24%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 27%]
............................................................s........... [ 28%]
........................................................................ [ 29%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 30%]
........................................................s............... [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
....................................s........ss...ss.................... [ 33%]
......s......sssss...................................................... [ 33%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 37%]
........................................................................ [ 38%]
..................ss.................................................... [ 38%]
.....E.................EEEEEE.EE.......F..EE............................ [ 39%]
........................................................................ [ 40%]
......................s................................................. [ 40%]
........................................................................ [ 41%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 56%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 62%]
........................................................................ [ 63%]
..............................................s..sss.....F.............. [ 64%]
........................................................................ [ 64%]
........................................................................ [ 65%]
....................................F................................... [ 66%]
........................................................................ [ 66%]
........................................................................ [ 67%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................F............... [ 74%]
........................................................................ [ 75%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 77%]
........................................................................ [ 78%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................s............................... [ 80%]
........................................................................ [ 80%]
.....................................s.................................. [ 81%]
........................................................................ [ 82%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 93%]
........................................................................ [ 94%]
........................................................................ [ 95%]
.................................s...................................... [ 95%]
........................................................................ [ 96%]
........................................................................ [ 96%]
........................................................................ [ 97%]
........................................................................ [ 98%]
........................................................................ [ 98%]
..............................s......................................... [ 99%]
........................................................................ [ 99%]
....                                                                     [100%]
==================================== ERRORS ====================================
_ ERROR at setup of test_a_captured_value_drives_a_later_step_and_the_predicate _

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
_______ ERROR at setup of test_every_new_predicate_kind_gets_its_verdict _______

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
_ ERROR at setup of test_a_refusal_status_is_read_from_the_triggers_own_response _

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
________ ERROR at setup of test_a_row_gone_is_named_never_merely_fewer _________

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
_________ ERROR at setup of test_protocol_field_reads_one_named_field __________

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
_____ ERROR at setup of test_input_value_reads_the_field_not_the_dom_text ______

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
__ ERROR at setup of test_a_restart_is_a_real_restart_and_the_value_survives ___

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
__________ ERROR at setup of test_a_refusal_must_name_what_is_missing __________

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
___ ERROR at setup of test_an_asserted_absence_is_earned_by_the_named_bound ____

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
_ ERROR at setup of test_a_clicked_verb_reads_its_identity_from_its_own_response _

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
__ ERROR at setup of test_a_clicked_verb_status_is_read_by_its_declared_route __

tmp_path_factory = TempPathFactory(_given_basetemp=None, _trace=<pluggy._tracing.TagTracerSub object at 0x109bd5350>, _basetemp=PosixPath.../folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357'), _retention_count=3, _retention_policy='all')

    @pytest.fixture(scope="module")
    def predicate_calibration(tmp_path_factory):
        """All four new kinds, on the calibration page and its protocol surface,
        through the same engine a real case uses."""
        out = tmp_path_factory.mktemp("graph-walk-predicates")
>       records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:668: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'action': 'restart_hub', 'adapter': 'process', 'kind': 'cli'}
page = <Page url='http://127.0.0.1:53191/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x1769c7950>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...ers/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/graph-walk-predicates0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['cal:l'], 'expected': {'observe_at': 'protocol: GET /state', 'predicate': {'kind': 'protocol_field', 'path': 'note', 'value': 'the summary'}}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
            status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
            record = {"kind": "fixture", "path": step["path"], "route": route,
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
            want_status = step.get("expect_status")
            if want_status is not None and status != want_status:
                raise Blocked(
                    f"{route['method']} {route['path']} answered {status}, "
                    f"wanted {want_status}: {record['response']}"[:500])
            if status >= 400:
                raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                # the import route answers 202 {"meeting_id": …, "status": "importing"}
                # (holdspeak/services/meeting_service.py:226), so an import case
                # declares `capture_path: "meeting_id"`.
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of the input boundary {route['method']} {route['path']} "
                        f"(it answered {record['response']})"[:500])
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            if step.get("wait_for"):
                record["completion_wait"] = wait_for_fixture_completion(
                    hub, step["wait_for"], variables)
            return record
        if kind == "cli":
            action = step.get("action")
            if action != "restart_hub":
                raise Blocked(
                    f"cli command {(step.get('command') or action)!r} is not "
                    "implemented in this rig; the case is blocked, not claimed. The "
                    "one implemented command is action 'restart_hub'.")
            if hub is None or not hasattr(hub, "restart"):
                raise Blocked("a restart_hub step needs the rig's own hub process")
            resolved_case = substitute(case or {}, variables)
            before_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record = {"kind": "cli", "action": "restart_hub",
                      "adapter": step.get("adapter", "process"), **hub.restart()}
            after_restart = snapshot(page, resolved_case, hub) if page is not None else None
            record["hub_identity"] = {
>               "url": hub.url,
                       ^^^^^^^
                "port": hub.port,
                "db_path": hub.db_path,
                "stopped_pid": record.get("stopped_pid"),
                "started_pid": record.get("started_pid"),
            }
E           AttributeError: 'CalibrationServer' object has no attribute 'url'

scripts/graph_walk.py:2505: AttributeError
=================================== FAILURES ===================================
_____________________ TestMeetingsGlass.test_meetings_face _____________________

self = <tests.e2e.test_hs170_meetings_glass.TestMeetingsGlass object at 0x10b1ece10>

    def test_meetings_face(self) -> None:
        from playwright.sync_api import sync_playwright, expect
    
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
    
            for width in (1440, 393):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.on("pageerror", lambda err: errors.append(str(err)))
    
                # Navigate with auth token
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed", token=TOKEN)
                _api(page, "PUT", "/api/setup/onboarding",
                     {"disposition": "completed"}, token=TOKEN)
                _normal_chair(page)
    
                # Open the meetings surface
                _open_surface(page, "review-meetings")
                found = _wait_for_surface_window(page, timeout=12000)
                assert found, f"Meetings surface window did not open at {width}"
    
                # Wait for data to render (headline is the signal)
                headline = page.locator("[data-testid='meetings-headline']")
                headline.wait_for(timeout=8_000)
                _settle(page)
    
                # ── Assert: headline ──
                headline_text = headline.text_content() or ""
                assert "1" in headline_text and "summary" in headline_text.lower(), (
                    f"Headline at {width}: expected '1 ... summary', got '{headline_text}'"
                )
    
                # ── Assert: Run summary on OFF-with-words row ──
                run_btns = page.locator("[data-testid='run-intelligence-btn']")
                expect(run_btns.first).to_be_visible(timeout=5_000)
                assert run_btns.count() == 1, (
                    f"Expected exactly 1 'Run summary' at {width}, got {run_btns.count()}"
                )
    
                # ── Assert: NO TRANSCRIPT renders ──
                no_transcript = page.locator("[data-testid='no-transcript-token']")
                expect(no_transcript.first).to_be_visible(timeout=3_000)
    
                # ── Assert: 0 SEG never appears ──
                win = page.locator(".desk-surface-window")
                page_text = win.text_content() or ""
                assert "0 SEG" not in page_text, (
                    f"'0 SEG' found in page at {width}"
                )
    
                # ── Assert: INTERRUPTED renders for dead capture, REC never does ──
                assert "INTERRUPTED" in page_text, (
                    f"'INTERRUPTED' not found at {width} for dead capture"
                )
                state_tokens_text = page.evaluate("""() => {
                    const body = document.querySelector('.desk-surface-body');
                    if (!body) return '';
                    const tokens = body.querySelectorAll('[data-testid="state-token"]');
                    return Array.from(tokens).map(t => t.textContent).join('|');
                }""")
                assert "REC" not in state_tokens_text.split("|"), (
                    f"'REC' state token found at {width}: {state_tokens_text}"
                )
    
                # ── Assert: no raw <button> in the face body ──
                raw_buttons = page.evaluate("""() => {
                    const body = document.querySelector('.desk-surface-body');
                    if (!body) return [];
                    const all = body.querySelectorAll('button');
                    const raw = [];
                    for (const b of all) {
                        // .btn = library Button; .desk-mic = library MicButton
                        if (!b.classList.contains('btn') && !b.classList.contains('btn--chrome') && !b.classList.contains('desk-mic')) {
                            raw.push((b.textContent || '').trim().slice(0, 40));
                        }
                    }
                    return raw;
                }""")
                assert len(raw_buttons) == 0, (
                    f"Raw buttons at {width}: {raw_buttons}"
                )
    
                # ── Assert: HS-170-04 restored doors ──
                if width == 1440:
                    # Search StringGadget with mic in the list head
                    search_input = page.locator(".meetings-search .gadget-string input")
                    expect(search_input).to_be_visible(timeout=3_000)
    
                    # Facet token toggles on the caption row
                    facet_area = page.locator("[data-testid='meetings-facets']")
>                   expect(facet_area).to_be_visible(timeout=3_000)
E                   AssertionError: Locator expected to be visible
E                   Actual value: None
E                   Error: element(s) not found 
E                   Call log:
E                     - Expect "to_be_visible" with timeout 3000ms
E                     - waiting for locator("[data-testid='meetings-facets']")

tests/e2e/test_hs170_meetings_glass.py:318: AssertionError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____________________ TestAttentionGlass.test_long_row_393 _____________________

self = <tests.e2e.test_hs200_attention_glass.TestAttentionGlass object at 0x10b5f1e10>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_long_row_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1463c1860>

    def test_long_row_393(self, tmp_path, monkeypatch) -> None:
>       _run_long_row(tmp_path, monkeypatch, 393)

tests/e2e/test_hs200_attention_glass.py:733: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_long_row_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1463c1860>
width = 393

    def _run_long_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
        """Counsel P0-2: nothing extends past the viewport; one primary on the
        whole face; the sources disclosure opens with an Open per projection."""
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        errors: list[str] = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": 1100})
                page.on("pageerror", lambda e: errors.append(str(e)))
                _arrive(page, url)
                _seed_long_row(page)
                _reload_arrival(page)
                wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
                first = wire["items"][0]
                assert first["title"].startswith("KAN-7") and first["dedupCount"] == 2, first
                page.reload(wait_until="load")
                _normal_chair(page)
                page.get_by_test_id("arrival-needs-you").wait_for(timeout=15000)
                _settle(page)
                page.mouse.move(2, 2)
    
                row = page.locator("[data-testid='arrival-needs-you-row']").first
                assert LONG_TITLE in (row.text_content() or "")
                project = row.locator(".surface-project-button")
                assert project.count() == 1
                assert (project.get_attribute("aria-label") or "") == f"Open the Project: {LONG_PROJECT}"
                _no_horizontal_scroll(page, width)
                # The verb sits on the SAME line as the meta, at its right.
                boxes = page.evaluate("""() => {
                    const row = document.querySelector('[data-testid="arrival-needs-you-row"]');
                    const meta = row.querySelector('.arrival-needs-you-meta').getBoundingClientRect();
                    const verb = row.querySelector('.surface-ledger-trailing .btn').getBoundingClientRect();
                    const name = row.querySelector('.surface-ledger-primary').getBoundingClientRect();
                    return {metaTop: meta.top, metaBottom: meta.bottom, verbTop: verb.top, verbBottom: verb.bottom,
                            verbRight: verb.right, nameBottom: name.bottom, rowRight: row.getBoundingClientRect().right};
                }""")
                assert boxes["verbRight"] <= width + 0.5, boxes
                if width <= 480:
                    assert boxes["verbTop"] >= boxes["nameBottom"] - 1, f"the verb is under the name at 393: {boxes}"
                    assert boxes["verbTop"] < boxes["metaBottom"] and boxes["verbBottom"] > boxes["metaTop"], \
                        f"the verb shares the meta line at 393: {boxes}"
                assert len(_primaries(page)) == 1, _primaries(page)
    
                _shot(page, "long-row", width)
    
                trigger = row.locator(".surface-disclosure-trigger").first
                trigger.click()
                _settle(page)
                opens = page.get_by_test_id("arrival-source-open")
                assert opens.count() == 2, "every projection keeps its own Open"
                titles = [t.text_content() for t in page.locator(".arrival-source-title").all()]
                assert titles == [f"KAN-7 {LONG_TITLE}", LONG_TITLE], titles
                _no_horizontal_scroll(page, width)
                assert len(_primaries(page)) == 1, _primaries(page)
                _shot(page, "long-row-sources", width)
    
                # The selected filter token is never the filled primary.
                page.get_by_role("group", name="Ranking").get_by_role("button", name="OVERDUE").click()
                _settle(page)
                assert len(_primaries(page)) == 1, _primaries(page)
    
                if width <= 480:
                    # Counsel P1-8: scrolled to the end, the last section clears the
                    # capture bar.
                    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                    page.wait_for_timeout(200)
                    _settle(page)
                    clear = page.evaluate("""() => {
                        const bar = document.querySelector('.arrival-capture-bar').getBoundingClientRect();
                        const sections = [...document.querySelectorAll('.chair > [data-testid^="arrival-"]')]
                            .filter(el => !el.classList.contains('arrival-capture-bar'));
                        const last = sections[sections.length - 1].getBoundingClientRect();
                        return {barTop: bar.top, lastBottom: last.bottom, lastId: sections[sections.length - 1].getAttribute('data-testid')};
                    }""")
>                   assert clear["lastBottom"] <= clear["barTop"] + 0.5, clear
E                   AssertionError: {'barTop': 821, 'lastBottom': 1004.296875, 'lastId': 'arrival-meetings'}
E                   assert 1004.296875 <= (821 + 0.5)

tests/e2e/test_hs200_attention_glass.py:659: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ test_running_then_kept_brief_with_claims_and_not_read[393] __________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_running_then_kept_brief_w1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1414426d0>
width = 393

    @pytest.mark.timeout(300)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_running_then_kept_brief_with_claims_and_not_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
    ) -> None:
        """P3Brief / P3BriefPhone over a REAL dispatch to the fake server: the
        document, `CLAIMS` on three axes with typed unknowns, `NO SOURCE` +
        `Find support`, `SUPERSEDED 1` with its successor (P1-2), `NOT INCLUDED
        2` (P1-3), `NOT READ 2` carrying the state chip and the repair, the
        LAN egress and receipt from the wire, `Keep` -- then the kept brief
        re-read by id with its manifest (AC2, AC3, AC4)."""
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        llm = FakeLLM()
        llm.reply = _board_reply
        llm.delay_s = 6.0
        errors: list[str] = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": 900 if width >= 1440 else 852})
                page.on("pageerror", lambda e: errors.append(str(e)))
                _init_desk(page, url)
                project_id = _seed_project_room(page, f"hs200-11-brief-{width}")
                _define_route(tmp_path / "home", llm.endpoint, "probe-llm", 1)
                _open_room(page, project_id)
                _enter_prepare(page)
                _purpose(page).fill(PURPOSE)
                page.get_by_test_id("prepare-verb").click()
    
                # The run: a real plan with `Stop` kept, the egress beside it.
                page.get_by_test_id("prepare-running").wait_for(timeout=10000)
                assert page.get_by_role("button", name="Stop", exact=True).count() == 1
                _shot_room(page, f"prepare-running-{width}")
    
                page.get_by_test_id("prepare-document").wait_for(timeout=60000)
                _settle(page)
                assert len(llm.posts) == 1, llm.requests
                assert "read replica" in llm.posts[0]["body"], "the decision travelled in the prompt"
                assert page.get_by_test_id("prepare-head-name").inner_text().strip() == "Brief ready"
                assert _chip_words(page.get_by_test_id("prepare-lifecycle")) == "DRAFT"
                assert page.get_by_test_id("prepare-manifest-token").inner_text().strip() == "MANIFEST · REV 1"
                assert _chip_words(page.get_by_test_id("prepare-coverage")) == "COVERAGE · 2 OF 4"
                assert page.get_by_test_id("prepare-prepared").inner_text().strip().startswith("PREPARED ")
    
                # The document is the bounded outline, in caption-step headings;
                # the superseded decision is NOT a line of it (P1-2).
                doc = page.get_by_test_id("prepare-document").inner_text()
                assert "DECIDE TODAY" in doc and "ASK THEM" in doc, doc
                assert "Sprint velocity improved" in doc
                assert "full freeze" not in doc, doc
                assert "Extra priority" not in doc, doc
    
                captions = _section_captions(page)
                assert "CLAIMS 5" in captions and "SUPERSEDED 1" in captions and "NOT READ 2" in captions, captions
    
                # The carried decision keeps its axes; the model's own prose is
                # LINKED at best; the uncited sentence is UNSUPPORTED (C2).
                kinds = _texts(page, "prepare-claim-kind")
                assert kinds == ["DECISION", "INFERENCE", "INFERENCE", "INFERENCE", "INFERENCE"], kinds
                support = [_chip_words(el) for el in page.get_by_test_id("prepare-claim-support").all()]
                assert support == ["SUPPORTED", "LINKED", "LINKED", "LINKED", "UNSUPPORTED"], support
                acceptance = [_chip_words(el) for el in page.get_by_test_id("prepare-claim-acceptance").all()]
                assert acceptance == ["ACCEPTED", "UNREVIEWED", "UNREVIEWED", "UNREVIEWED", "UNREVIEWED"], acceptance
                unknowns = [_chip_words(el) for el in page.get_by_test_id("prepare-claim-unknown").all()]
                assert "DEADLINE 2026-12-31 · NO SOURCE" in unknowns, unknowns
                assert "NUMBER 95% · NO SOURCE" in unknowns, unknowns
                # The NAME rule: no known person on this desk, no false NAME chip.
                assert not [u for u in unknowns if u.startswith("NAME ")], unknowns
                # No raw id on the face (162's law): the ref chip names the source.
                ref_chips = _texts(page, "prepare-claim-ref")
                assert ref_chips[0].startswith("DEC "), ref_chips
                assert ref_chips[1].lower() == "karolswdev/holdspeak", ref_chips
                assert not any("decrec" in r.lower() or "w_gh" in r.lower() for r in ref_chips), ref_chips
                # No source, no source chip: `NO SOURCE` + `Find support`, and no
                # `Open source` that opens nothing.
                assert page.get_by_test_id("prepare-claim-no-source").count() == 1
                assert page.get_by_test_id("prepare-claim-find").count() == 1
                assert page.get_by_test_id("prepare-claim-open").count() == 4
                assert page.get_by_role("button", name="Write it myself").count() == 0
    
                # P1-2: the superseded citation, its successor linked.
                assert page.get_by_test_id("prepare-superseded-row").count() == 1
                assert _chip_words(page.get_by_test_id("prepare-superseded-chip")).startswith("SUPERSEDED BY DEC ")
                assert page.get_by_test_id("prepare-superseded-open").count() == 1
    
                # P1-3: what the bound left out is named, with why.
                page.get_by_role("button", name="NOT INCLUDED 2").click()
>               page.get_by_test_id("prepare-not-included").wait_for(timeout=5000)

tests/e2e/test_hs200_preparation_brief_glass.py:706: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x1432d5d50>
cb = <function Channel.send.<locals>.<lambda> at 0x14e823a60>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 5000ms exceeded.
E           Call log:
E             - waiting for get_by_test_id("prepare-not-included") to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
____________ test_saved_ask_draws_the_ratified_unfinished_row[393] _____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_saved_ask_draws_the_ratif1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x14796ce50>
width = 393

    @pytest.mark.timeout(300)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_saved_ask_draws_the_ratified_unfinished_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
    ) -> None:
        """`UNFINISHED 1`: purpose, `SAVED HH:MM`, custody, one `Resume`."""
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        errors: list[str] = []
        purpose = "Whether the Q4 platform migration can land before the freeze"
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(
                    viewport={"width": width, "height": 900 if width >= 1440 else 852}
                )
                page.on("pageerror", lambda e: errors.append(str(e)))
    
                _init_desk(page, url)
                project_id = _create_project(page, "Q4 platform", "hs200-41-saved")
                task = _save_ask(page, project_id, purpose)
                assert task["state"] == "saved", task
                assert task["purpose"] == purpose
    
                _open_room(page, project_id)
                page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
                assert _rows(page).count() == 1, "expected exactly one unfinished row"
    
                # The caption carries the count the design ratified. F5 moved it:
                # the list is a Room SECTION now, so the count rides the section
                # label rather than a caption inside the composer's sticky foot.
                section = _rows(page).first.locator(
                    "xpath=ancestor::section[contains(@class,'surface-section')][1]"
                )
                caption = section.locator(".surface-section-head h3").first.inner_text().strip()
                assert caption == "UNFINISHED 1", caption
                # F5: and it is NOT inside the sticky ask container.
                assert page.evaluate(
                    """() => !document.querySelector('.room-ask-container')
                       .contains(document.querySelector('[data-testid="room-unfinished"]'))"""
                ), "the unfinished list must live in the Room body, not the sticky foot"
    
                # F5 tail — AT THE ROOM'S OPENING SCROLL POSITION, not only at
                # full scroll. Filed as the trailing section, UNFINISHED was the
                # one the sticky foot reached: the Room opened with the single row
                # he came back for sitting under the composer, its verb hidden.
                # It is placed directly after NEEDS YOU now, so the foot never
                # reaches it at rest.
                order = page.evaluate(
                    """() => Array.from(document.querySelectorAll(
                         '.room-body .surface-section-head h3')).map(el => el.textContent.trim())"""
                )
                print(f"[hs200-41] section order at rest: {order}")
                unfinished_at = [i for i, name in enumerate(order)
                                 if name.startswith("UNFINISHED")]
                assert unfinished_at, order
                if "NEEDS YOU" in order:
                    assert unfinished_at[0] == order.index("NEEDS YOU") + 1, (
                        f"UNFINISHED belongs directly after NEEDS YOU: {order}"
                    )
                if "SOURCES" in order:
                    assert unfinished_at[0] < order.index("SOURCES"), order
                clear = page.evaluate(
                    """() => {
                        const body = document.querySelector('.desk-surface-body');
                        const top = body ? body.scrollTop : 0;
                        const well = document.querySelector('.room-ask-container')
                          .getBoundingClientRect();
                        const rows = Array.from(document.querySelectorAll(
                          '[data-testid="room-unfinished"] .surface-task-resume'));
                        const covered = rows.filter(row => {
                          const r = row.getBoundingClientRect();
                          return r.bottom > well.top + 1 && r.top < well.bottom - 1;
                        }).length;
                        // The row's ONE verb must be whole, not a sliver above
                        // the composer's edge.
                        const verb = document.querySelector(
                          '[data-testid="room-unfinished"] .surface-task-resume-verbs button');
                        const v = verb.getBoundingClientRect();
                        return {scrollTop: top, covered,
                                verbClear: Math.round(well.top - v.bottom)};
                    }"""
                )
                print(f"[hs200-41] at rest: {json.dumps(clear)}")
                assert clear["scrollTop"] == 0, "this is meant to measure the RESTING Room"
>               assert clear["covered"] == 0, (
                    f"the row he came back for opens under the composer: {clear}"
                )
E               AssertionError: the row he came back for opens under the composer: {'scrollTop': 0, 'covered': 1, 'verbClear': -101}
E               assert 1 == 0

tests/e2e/test_hs200_task_resume_glass.py:288: AssertionError
----------------------------- Captured stdout call -----------------------------
[hs200-41] section order at rest: ['NEEDS YOU', 'UNFINISHED 1', 'SOURCES', 'RECEIPTS 4', 'SINCE CREATED']
[hs200-41] at rest: {"scrollTop": 0, "covered": 1, "verbClear": -101}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________________ test_thought_note_is_one_clean_note[1440] ___________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_thought_note_is_one_clean0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x14fde7e70>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_thought_note_is_one_clean_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        server, url, provider, engine = _boot(tmp_path, monkeypatch)
        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        console_errors: list[str] = []
        responses: list[tuple[str, int]] = []
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                page.on("response", lambda response: responses.append((response.url, response.status)) if "/api/thoughts/" in response.url else None)
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
                thought = _seed(page, OWNER_TITLE, OWNER_BODY)
                note_id = thought["working_note"]["id"]
                page.goto(f"{url}/?token={TOKEN}&open=note%3A{note_id}", wait_until="load")
    
                workspace = page.get_by_role("region", name="Thought", exact=True)
                workspace.wait_for(timeout=15000)
                band = page.get_by_role("region", name="One question", exact=True)
                band.wait_for(timeout=15000)
    
                # ── Band 3 is folded to one row; nothing else is on the screen ──
                assert band.get_by_role("button", name="Ask", exact=True).is_visible()
                assert page.get_by_role("textbox", name="Your answer").count() == 0
                assert workspace.get_by_role("toolbar", name="Markdown formatting").count() == 0
                assert workspace.get_by_role("button", name="Info", exact=True).count() == 0
                assert workspace.get_by_role("button", name="Add tag", exact=True).count() == 0
                assert workspace.get_by_role("region", name="Interview", exact=True).count() == 0
                assert page.get_by_text("Filed", exact=True).count() == 0
                assert page.get_by_text("Saved", exact=True).count() == 0
                _no_empty_heading(page)
                _no_horizontal_escape(page)
                # Every verb is a library species: btn (Button), or a library
                # control's own element (the desk mic, the in-place editor).
                assert workspace.evaluate(
                    "el => [...el.querySelectorAll('button')].filter(node => "
                    "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
                ) == 0
                assert workspace.locator(".btn--primary:visible").count() == 1
                assert workspace.locator(".btn--primary:visible").inner_text().strip() == "Finish"
    
                # The title wraps: every character of it is drawn, never clipped.
                title = workspace.locator(".thought-note-title")
                assert title.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
                assert title.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                assert OWNER_TITLE[-12:] in title.inner_text()
    
                # The context fact is said ONCE, in the Reads line of the foot.
                reads = workspace.locator(".thought-note-reads")
                assert reads.count() == 1
                assert page.get_by_text("Attached", exact=False).count() == 0
                page.screenshot(path=str(SHOTS / f"after-{width}.png"), full_page=False)
    
                # ── Change: an in-window well, and the Reads line is the receipt ──
                change = workspace.get_by_role("button", name="Change", exact=True)
                change.click()
                well = page.get_by_role("region", name="What the AI reads")
                well.wait_for(timeout=10000)
                assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
                assert well.evaluate(
                    "el => [...el.querySelectorAll('button')].filter(node => "
                    "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
                ) == 0
                token = well.get_by_role("checkbox").first
                token.wait_for(timeout=10000)
                chosen = token.get_attribute("aria-label")
                assert chosen, "the well drew a control with no name"
                # The token variant's own face takes the click (the input is its
                # state, not its target) — the owner presses the named token.
                well.locator("label.gadget-check-token").first.click()
                page.wait_for_function(
                    "name => document.querySelector('.thought-note-reads')?.textContent?.includes(name)",
                    arg=chosen,
                    timeout=10000,
                )
                # The receipt is said ONCE, and it is never clipped at either width.
                assert workspace.locator(".thought-note-reads").count() == 1
                assert workspace.locator(".thought-note-reads").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                # …and the kept state keeps its own place beside it (the foot
                # stacks at 393 rather than pushing a fact off the glass).
                kept = workspace.locator(".thought-note-foot .surface-footer-receipt-line")
>               assert kept.inner_text().strip() == "KEPT"
                       ^^^^^^^^^^^^^^^^^

tests/e2e/test_hs201_12_thought_note_glass.py:233: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:17093: in inner_text
    self._sync(self._impl_obj.inner_text(timeout=timeout))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:476: in inner_text
    return await self._frame.inner_text(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:712: in inner_text
    return await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x1414f0d50>
cb = <function Channel.send.<locals>.<lambda> at 0x14fe85440>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.inner_text: Error: strict mode violation: get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line") resolved to 2 elements:
E               1) <span role="status" class="surface-footer-receipt-line">KEPT · 12:02 PM</span> aka get_by_text("KEPT · 12:02 PM")
E               2) <span data-line="filing" class="surface-footer-receipt-line">IN INBOX</span> aka get_by_text("IN INBOX")
E           
E           Call log:
E             - waiting for get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line")

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___________________ test_thought_note_is_one_clean_note[393] ___________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_thought_note_is_one_clean1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x14fde7e00>
width = 393

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_thought_note_is_one_clean_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        server, url, provider, engine = _boot(tmp_path, monkeypatch)
        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        console_errors: list[str] = []
        responses: list[tuple[str, int]] = []
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                page.on("response", lambda response: responses.append((response.url, response.status)) if "/api/thoughts/" in response.url else None)
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
                thought = _seed(page, OWNER_TITLE, OWNER_BODY)
                note_id = thought["working_note"]["id"]
                page.goto(f"{url}/?token={TOKEN}&open=note%3A{note_id}", wait_until="load")
    
                workspace = page.get_by_role("region", name="Thought", exact=True)
                workspace.wait_for(timeout=15000)
                band = page.get_by_role("region", name="One question", exact=True)
                band.wait_for(timeout=15000)
    
                # ── Band 3 is folded to one row; nothing else is on the screen ──
                assert band.get_by_role("button", name="Ask", exact=True).is_visible()
                assert page.get_by_role("textbox", name="Your answer").count() == 0
                assert workspace.get_by_role("toolbar", name="Markdown formatting").count() == 0
                assert workspace.get_by_role("button", name="Info", exact=True).count() == 0
                assert workspace.get_by_role("button", name="Add tag", exact=True).count() == 0
                assert workspace.get_by_role("region", name="Interview", exact=True).count() == 0
                assert page.get_by_text("Filed", exact=True).count() == 0
                assert page.get_by_text("Saved", exact=True).count() == 0
                _no_empty_heading(page)
                _no_horizontal_escape(page)
                # Every verb is a library species: btn (Button), or a library
                # control's own element (the desk mic, the in-place editor).
                assert workspace.evaluate(
                    "el => [...el.querySelectorAll('button')].filter(node => "
                    "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
                ) == 0
                assert workspace.locator(".btn--primary:visible").count() == 1
                assert workspace.locator(".btn--primary:visible").inner_text().strip() == "Finish"
    
                # The title wraps: every character of it is drawn, never clipped.
                title = workspace.locator(".thought-note-title")
                assert title.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
                assert title.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                assert OWNER_TITLE[-12:] in title.inner_text()
    
                # The context fact is said ONCE, in the Reads line of the foot.
                reads = workspace.locator(".thought-note-reads")
                assert reads.count() == 1
                assert page.get_by_text("Attached", exact=False).count() == 0
                page.screenshot(path=str(SHOTS / f"after-{width}.png"), full_page=False)
    
                # ── Change: an in-window well, and the Reads line is the receipt ──
                change = workspace.get_by_role("button", name="Change", exact=True)
                change.click()
                well = page.get_by_role("region", name="What the AI reads")
                well.wait_for(timeout=10000)
                assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
                assert well.evaluate(
                    "el => [...el.querySelectorAll('button')].filter(node => "
                    "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
                ) == 0
                token = well.get_by_role("checkbox").first
                token.wait_for(timeout=10000)
                chosen = token.get_attribute("aria-label")
                assert chosen, "the well drew a control with no name"
                # The token variant's own face takes the click (the input is its
                # state, not its target) — the owner presses the named token.
                well.locator("label.gadget-check-token").first.click()
                page.wait_for_function(
                    "name => document.querySelector('.thought-note-reads')?.textContent?.includes(name)",
                    arg=chosen,
                    timeout=10000,
                )
                # The receipt is said ONCE, and it is never clipped at either width.
                assert workspace.locator(".thought-note-reads").count() == 1
                assert workspace.locator(".thought-note-reads").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                # …and the kept state keeps its own place beside it (the foot
                # stacks at 393 rather than pushing a fact off the glass).
                kept = workspace.locator(".thought-note-foot .surface-footer-receipt-line")
>               assert kept.inner_text().strip() == "KEPT"
                       ^^^^^^^^^^^^^^^^^

tests/e2e/test_hs201_12_thought_note_glass.py:233: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:17093: in inner_text
    self._sync(self._impl_obj.inner_text(timeout=timeout))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:476: in inner_text
    return await self._frame.inner_text(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:712: in inner_text
    return await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x1414f2550>
cb = <function Channel.send.<locals>.<lambda> at 0x144bc4360>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.inner_text: Error: strict mode violation: get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line") resolved to 2 elements:
E               1) <span role="status" class="surface-footer-receipt-line">KEPT · 12:02 PM</span> aka get_by_text("KEPT · 12:02 PM")
E               2) <span data-line="filing" class="surface-footer-receipt-line">IN INBOX</span> aka get_by_text("IN INBOX")
E           
E           Call log:
E             - waiting for get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line")

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________ test_thought_note_long_context_and_open_well_never_clip[1440] _________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_thought_note_long_context0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x149a323c0>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_thought_note_long_context_and_open_well_never_clip(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
    ) -> None:
        """Astra finding 5: a long context name pushed Finish off the window."""
        from playwright.sync_api import sync_playwright
    
        server, url, _provider, _engine = _boot(tmp_path, monkeypatch)
        SHOTS.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
                _api(page, "POST", "/api/notes", {"title": LONG_CONTEXT, "body_markdown": "The freeze holds.", "tags": []})
                thought = _seed(page, OWNER_TITLE, OWNER_BODY)
                page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")
    
                workspace = page.get_by_role("region", name="Thought", exact=True)
                workspace.wait_for(timeout=15000)
                workspace.get_by_role("button", name="Change", exact=True).click()
                well = page.get_by_role("region", name="What the AI reads")
                well.wait_for(timeout=10000)
    
                # The well SEARCHES the desk, not just six recent notes.
                find = well.get_by_role("textbox", name="Find a note")
                find.fill("standing decisions")
                token = well.locator("label.gadget-check-token", has_text="standing decisions")
                token.first.wait_for(timeout=10000)
                token.first.click()
                page.wait_for_function(
                    "name => document.querySelector('.thought-note-reads')?.title?.includes(name)",
                    arg="standing decisions",
                    timeout=10000,
                )
    
                window_box = workspace.bounding_box()
                assert window_box
                # Nothing the owner must press leaves the window…
                for name in ("Change", "Finish"):
                    box = workspace.get_by_role("button", name=name, exact=True).bounding_box()
                    assert box, name
                    assert box["x"] + box["width"] <= window_box["x"] + window_box["width"] + 1, (name, box, window_box)
                    _in_frame(box, window_box, name)
                # …the kept state keeps its width…
                kept = workspace.locator(".thought-note-foot .surface-footer-receipt-line")
>               kept_box = kept.bounding_box()
                           ^^^^^^^^^^^^^^^^^^^

tests/e2e/test_hs201_12_thought_note_glass.py:524: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:15485: in bounding_box
    self._sync(self._impl_obj.bounding_box(timeout=timeout))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:132: in bounding_box
    return await self._with_element(
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:113: in _with_element
    handle = await self.element_handle(timeout=timeout)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:319: in element_handle
    handle = await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x14740c550>
cb = <function Channel.send.<locals>.<lambda> at 0x147185ee0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.bounding_box: Error: strict mode violation: get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line") resolved to 2 elements:
E               1) <span role="status" class="surface-footer-receipt-line">KEPT · 12:02 PM</span> aka get_by_text("KEPT · 12:02 PM")
E               2) <span data-line="filing" class="surface-footer-receipt-line">IN INBOX</span> aka get_by_text("IN INBOX")
E           
E           Call log:
E             - waiting for get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line")

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_________ test_thought_note_long_context_and_open_well_never_clip[393] _________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_thought_note_long_context1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x150a2cd00>
width = 393

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_thought_note_long_context_and_open_well_never_clip(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
    ) -> None:
        """Astra finding 5: a long context name pushed Finish off the window."""
        from playwright.sync_api import sync_playwright
    
        server, url, _provider, _engine = _boot(tmp_path, monkeypatch)
        SHOTS.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
                _api(page, "POST", "/api/notes", {"title": LONG_CONTEXT, "body_markdown": "The freeze holds.", "tags": []})
                thought = _seed(page, OWNER_TITLE, OWNER_BODY)
                page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")
    
                workspace = page.get_by_role("region", name="Thought", exact=True)
                workspace.wait_for(timeout=15000)
                workspace.get_by_role("button", name="Change", exact=True).click()
                well = page.get_by_role("region", name="What the AI reads")
                well.wait_for(timeout=10000)
    
                # The well SEARCHES the desk, not just six recent notes.
                find = well.get_by_role("textbox", name="Find a note")
                find.fill("standing decisions")
                token = well.locator("label.gadget-check-token", has_text="standing decisions")
                token.first.wait_for(timeout=10000)
                token.first.click()
                page.wait_for_function(
                    "name => document.querySelector('.thought-note-reads')?.title?.includes(name)",
                    arg="standing decisions",
                    timeout=10000,
                )
    
                window_box = workspace.bounding_box()
                assert window_box
                # Nothing the owner must press leaves the window…
                for name in ("Change", "Finish"):
                    box = workspace.get_by_role("button", name=name, exact=True).bounding_box()
                    assert box, name
                    assert box["x"] + box["width"] <= window_box["x"] + window_box["width"] + 1, (name, box, window_box)
                    _in_frame(box, window_box, name)
                # …the kept state keeps its width…
                kept = workspace.locator(".thought-note-foot .surface-footer-receipt-line")
>               kept_box = kept.bounding_box()
                           ^^^^^^^^^^^^^^^^^^^

tests/e2e/test_hs201_12_thought_note_glass.py:524: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:15485: in bounding_box
    self._sync(self._impl_obj.bounding_box(timeout=timeout))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:132: in bounding_box
    return await self._with_element(
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:113: in _with_element
    handle = await self.element_handle(timeout=timeout)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:319: in element_handle
    handle = await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x14740f750>
cb = <function Channel.send.<locals>.<lambda> at 0x13f70eac0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.bounding_box: Error: strict mode violation: get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line") resolved to 2 elements:
E               1) <span role="status" class="surface-footer-receipt-line">KEPT · 12:02 PM</span> aka get_by_text("KEPT · 12:02 PM")
E               2) <span data-line="filing" class="surface-footer-receipt-line">IN INBOX</span> aka get_by_text("IN INBOX")
E           
E           Call log:
E             - waiting for get_by_role("region", name="Thought", exact=True).locator(".thought-note-foot .surface-footer-receipt-line")

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
______ test_summary_and_receipt_survive_real_hub_restart_on_both_glasses _______

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_summary_and_receipt_survi0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x147181940>

    def test_summary_and_receipt_survive_real_hub_restart_on_both_glasses(tmp_path, monkeypatch):
        from holdspeak.db import get_database
        from playwright.sync_api import sync_playwright
    
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json"))
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        db = get_database()
        _configure(db)
        engine = FakeIntel()
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
        monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(()))
        monkeypatch.setattr("holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(()))
        _profile(db, "lane-a-summary", claims=("language", _result_claim("meeting.deferred_analysis")))
        now = datetime.now()
        meeting = MeetingState(
            id="lane-a-fixture", title="Lane A fixture meeting",
            started_at=now - timedelta(minutes=1), ended_at=now,
            capture_status="finalized", transcription_status="final",
            segments=[TranscriptSegment("We agreed to send the budget report.", "Me", 0.0, 2.0)],
        )
        db.meetings.save_meeting(meeting)
        SHOTS.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed", token=TOKEN)
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                selected = _api(page, "POST", "/api/concierge/summary-selection", {
                    "commandId": "lane-a-glass-selection", "expectedAssignmentRevision": 0,
                    "profileId": "lane-a-summary", "profileRevision": 1,
                }, token=TOKEN)
                assert selected["status"] == "succeeded"
                before = _api(page, "GET", f"/api/meetings/{meeting.id}", token=TOKEN)
                planned = before["planned_route"]
                assert planned["status"] == "ready" and len(planned["legs"]) == 1
                queued = _api(page, "POST", f"/api/meetings/{meeting.id}/intelligence/run", {
                    "expected_selection_hash": planned["selection_hash"],
                }, token=TOKEN)
                assert queued["state"] == "queued", queued
                for _ in range(100):
                    if db.meetings.get_meeting(meeting.id).intel is not None:
                        break
                    process_next_intel_job()
                    time.sleep(0.05)
                saved = db.meetings.get_meeting(meeting.id)
                assert saved is not None and saved.intel is not None
                assert saved.intel.summary == engine.result.summary
                after = _api(page, "GET", f"/api/meetings/{meeting.id}/intel-recovery", token=TOKEN)
                receipt = after["run_receipt"]
                assert receipt["outcome"] == "succeeded"
                assert receipt["selection_hash"] == planned["selection_hash"]
                assert receipt["attempts"] and receipt["attempts"][0]["host"] == planned["legs"][0]["host"]
    
                server.stop()
                url = server.start()
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                reopened = _api(page, "GET", f"/api/meetings/{meeting.id}/intel-recovery", token=TOKEN)
                assert reopened["run_receipt"] == receipt
                assert db.meetings.get_meeting(meeting.id).intel.summary == engine.result.summary
                print(f"SUMMARY meeting={meeting.id} text={engine.result.summary!r}")
                print(f"RECEIPT after hub restart={receipt!r}")
    
                for width in (1440, 393):
                    page.set_viewport_size({"width": width, "height": 900 if width == 1440 else 852})
                    _normal_chair(page)
                    page.evaluate("""() => {
                        localStorage.removeItem('hs.desk.workspace.v1');
                        sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key:'review-meetings'}));
                    }""")
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    row = page.get_by_test_id(f"meeting-row-{meeting.id}")
                    row.locator(".meetings-stream-row-body").click()
>                   page.get_by_text("We agreed to send the budget report.", exact=True).wait_for()

tests/e2e/test_hs201_lane_a_glass.py:104: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x14120c050>
cb = <function Channel.send.<locals>.<lambda> at 0x14bb3f600>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.wait_for: Error: strict mode violation: get_by_text("We agreed to send the budget report.", exact=True) resolved to 2 elements:
E               1) <p>We agreed to send the budget report.</p> aka get_by_test_id("arrival-meetings").get_by_text("We agreed to send the budget")
E               2) <p>We agreed to send the budget report.</p> aka locator("#surface-meetings").get_by_text("We agreed to send the budget")
E           
E           Call log:
E             - waiting for get_by_text("We agreed to send the budget report.", exact=True) to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
----------------------------- Captured stdout call -----------------------------
SUMMARY meeting=lane-a-fixture text='The team reviewed the budget.'
RECEIPT after hub restart={'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_4c00f701d3d642559c3506c7ee47b61f', 'outcome': 'succeeded'}], 'job_id': 'ij_37841f1bac9437923830aba62536c8c24e9669a4430f0ffaaf9b2656457696b1', 'meeting_id': 'lane-a-fixture', 'outcome': 'succeeded', 'receipt_id': 'rr_0816f32b1f655d8b86ca8cbc95606862', 'selection_hash': 'sha256:82b212ceea98582976e519a83736e1e8bfea0aed4a8a7166efec56bc52142d51'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___________ test_the_summary_is_asked_for_disclosed_and_found_again ____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_the_summary_is_asked_for_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x156227310>

    def test_the_summary_is_asked_for_disclosed_and_found_again(tmp_path, monkeypatch):
        from holdspeak.db import get_database
        from playwright.sync_api import sync_playwright
    
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json"))
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        db = get_database()
        _configure(db)
        engine = FakeIntel()
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
        monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
        monkeypatch.setattr(
            "holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(())
        )
        monkeypatch.setattr(
            "holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(())
        )
        # Both halves of the meeting path on one local profile: speech becomes
        # text, and text becomes a summary (glass_infra.seed_meeting_engines).
        seed_meeting_engines()
    
        # Astra's counsel round 2: TWO summary-ready meetings, so the canon
        # probe measures a rail that can draw more than one run verb. Only the
        # lead row may wear the filled species.
        spare_id = _record_fixture_meeting(monkeypatch)
        first_id = _record_fixture_meeting(monkeypatch)
        saved = db.meetings.get_meeting(first_id)
        assert saved is not None and saved.segments, "the fixture WAV produced no transcript"
        assert saved.intel is None, "recording must not run a summary"
        print(f"RECORDED meeting={first_id} spare={spare_id} segments={len(saved.segments)}")
    
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                errors: list[str] = []
                requests: list[dict] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on(
                    "request",
                    lambda request: requests.append(
                        {
                            "path": request.url.split("?")[0].replace(url, ""),
                            "body": request.post_data or "",
                        }
                    )
                    if request.method == "POST"
                    else None,
                )
    
                def open_meetings(meeting_id: str | None = None) -> None:
                    """The Meetings window, with one record open when asked."""
                    page.evaluate(
                        """() => {
                            localStorage.removeItem('hs.desk.workspace.v1');
                            sessionStorage.setItem('hs.desk.staged-surface-open',
                                JSON.stringify({key:'review-meetings'}));
                        }"""
                    )
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    if meeting_id is None:
                        page.locator(".meetings-stream-rows").wait_for(timeout=15_000)
                        return
                    row = page.get_by_test_id(f"meeting-row-{meeting_id}")
                    row.wait_for(timeout=15_000)
                    print(f"ROW {meeting_id} {row.text_content()}")
                    row.locator(".meetings-stream-row-body").click()
                    page.locator(".meetings-detail-head").wait_for(timeout=15_000)
    
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    
                # ── the disclosed route, read before any click ──
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                detail = _api(page, "GET", f"/api/meetings/{first_id}", token=TOKEN)
                planned = detail["planned_route"]
                assert planned["status"] == "ready", planned
                assert planned["legs"], planned
                host = planned["legs"][0]["host"]
                print(f"PLANNED host={host} hash={planned['selection_hash']}")
    
                # ── station 1: the record BEFORE the run ──
                open_meetings(first_id)
                route_chip = page.get_by_test_id("detail-route")
                route_chip.wait_for(timeout=15_000)
                assert _chip_label(host) in (route_chip.text_content() or ""), (
                    route_chip.text_content()
                )
                page.get_by_test_id("detail-run-intelligence-btn").wait_for()
                _assert_canon(page)
                _shot(page, "record-before-run")
    
                # ── station 2: the first summary, from the verb, with the hash ──
                requests.clear()
                page.get_by_test_id("detail-run-intelligence-btn").click()
                page.wait_for_timeout(600)
                run_post = _run_posts(requests)[-1]
                assert run_post["path"] == f"/api/meetings/{first_id}/intelligence/run"
                assert json.loads(run_post["body"])["expected_selection_hash"] == (
                    planned["selection_hash"]
                ), run_post
                print(f"RUN POST {run_post}")
    
                _drain(db, first_id)
                produced = db.meetings.get_meeting(first_id)
                assert produced.intel is not None, "no summary was produced"
                assert produced.intel.summary == engine.result.summary
                receipt = _api(
                    page, "GET", f"/api/meetings/{first_id}/intel-recovery", token=TOKEN
                )["run_receipt"]
                assert receipt["outcome"] == "succeeded", receipt
                assert receipt["attempts"], receipt
                assert receipt["selection_hash"] == planned["selection_hash"], receipt
                print(f"RECEIPT {receipt}")
    
                # ── station 3: the record AFTER the run: the text and the hosts ──
                open_meetings(first_id)
                summary_text = page.get_by_test_id("meeting-summary-text")
>               summary_text.wait_for(timeout=15_000)

tests/e2e/test_hs201_summary_face_glass.py:250: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x15770cd50>
cb = <function Channel.send.<locals>.<lambda> at 0x15a1f2980>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.wait_for: Error: strict mode violation: get_by_test_id("meeting-summary-text") resolved to 2 elements:
E               1) <p class="summary-text" data-testid="meeting-summary-text">The team reviewed the budget.</p> aka get_by_test_id("arrival-meetings").get_by_test_id("meeting-summary-text")
E               2) <p class="summary-text" data-testid="meeting-summary-text">The team reviewed the budget.</p> aka get_by_role("region", name="Meetings").get_by_test_id("meeting-summary-text")
E           
E           Call log:
E             - waiting for get_by_test_id("meeting-summary-text") to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
----------------------------- Captured stdout call -----------------------------
RECORDED meeting=f3b5ff14 spare=ebaef426 segments=1
PLANNED host=same_device hash=sha256:29ae26badc6223abccae25c6e928bd163d140997dae72667b47d0b2ea87aa4ba
ROW f3b5ff14 MeetingSEP 23 · OFFSEP 23·1 S·3 WORDS·OFFTHIS DEVICERun summary
CANON primaries=['Run summary'] zeros=[] run_verbs_in_rail=['Run summary', 'Run summary']
SHOT /Users/karol/dev/tools/wt-philo-3-02/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-before-run-1440.png
SHOT /Users/karol/dev/tools/wt-philo-3-02/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-before-run-393.png
RUN POST {'path': '/api/meetings/f3b5ff14/intelligence/run', 'body': '{"expected_selection_hash":"sha256:29ae26badc6223abccae25c6e928bd163d140997dae72667b47d0b2ea87aa4ba"}'}
RECEIPT {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_e1f0acb7015e481a9a5f336e0a20c7c5', 'outcome': 'succeeded'}], 'job_id': 'ij_ddb77de061e7ce17ba0ff5fb9a12a4b00d2ac94f5dad0d46cd1f65c7112808b4', 'meeting_id': 'f3b5ff14', 'outcome': 'succeeded', 'receipt_id': 'rr_518cba218ecd6f7a0d53f09bff41677b', 'selection_hash': 'sha256:29ae26badc6223abccae25c6e928bd163d140997dae72667b47d0b2ea87aa4ba'}
ROW f3b5ff14 MeetingSEP 23 · RANSEP 23·1 S·3 WORDS·RANTHIS DEVICEOpen
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_______ test_import_transcribes_and_stops_then_the_summary_is_asked_for ________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_import_transcribes_and_st0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x159e96dd0>

    def test_import_transcribes_and_stops_then_the_summary_is_asked_for(
        tmp_path, monkeypatch
    ):
        from holdspeak.db import get_database
        from holdspeak.web.routes import meeting_import as import_route
        from playwright.sync_api import sync_playwright
    
        monkeypatch.setenv(
            "HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json")
        )
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=IMPORT_TOKEN)
        db = get_database()
        _configure(db)
        engine = FakeIntel()
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
        monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
        monkeypatch.setattr(
            "holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(())
        )
        monkeypatch.setattr(
            "holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(())
        )
        # No Whisper on this walk: the subject is what the import DOES, not what
        # it hears. The engine that would write the summary is the real seam and
        # it is watched (`engine.analyzed`).
        monkeypatch.setattr(
            import_route, "_transcriber_factory", lambda cfg: _FixtureImportTranscriber()
        )
        seed_meeting_engines()
    
        # The file the rehearsal imported, with a mtime months in the past —
        # the exact shape that dated the meeting JUN 03 (defect 10).
        source = tmp_path / "core_path_smoke_16k.wav"
        source.write_bytes(FIXTURE_WAV.read_bytes())
        old = (datetime.now() - timedelta(days=108)).timestamp()
        os.utime(source, (old, old))
        with wave.open(str(source), "rb") as wav_file:
            seconds = wav_file.getnframes() / float(wav_file.getframerate())
        assert 2.0 < seconds < 3.0, seconds
        print(f"FIXTURE {source.name} {seconds:.2f}s mtime={datetime.fromtimestamp(old)}")
    
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                errors: list[str] = []
                requests: list[dict] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on(
                    "request",
                    lambda request: requests.append(
                        {
                            "path": request.url.split("?")[0].replace(url, ""),
                            "body": request.post_data or "",
                        }
                    )
                    if request.method == "POST"
                    else None,
                )
    
                def open_meetings(expect_rows: bool = True) -> None:
                    page.evaluate(
                        """() => {
                            localStorage.removeItem('hs.desk.workspace.v1');
                            sessionStorage.setItem('hs.desk.staged-surface-open',
                                JSON.stringify({key:'review-meetings'}));
                        }"""
                    )
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    # A cold desk draws the Meetings face with no stream at all,
                    # so the face's own head verbs are what a first visit waits
                    # for (the headline span is empty while the list loads).
                    page.locator(".meetings-head-verbs").wait_for(timeout=15_000)
                    if expect_rows:
                        page.locator(".meetings-stream-rows").wait_for(timeout=15_000)
    
                page.goto(f"{url}/?token={IMPORT_TOKEN}", wait_until="load")
                _api(
                    page, "PUT", "/api/setup/onboarding", {"disposition": "completed"},
                    token=IMPORT_TOKEN,
                )
                open_meetings(expect_rows=False)
    
                # ── station 1: the Import door, and the real gesture ──
                page.locator(".meetings-head-verbs").get_by_role(
                    "button", name="Import", exact=True
                ).click()
                file_input = page.locator(".surface-dropwell input[type=file]")
                # The dropwell hides its input behind the label's own species.
                file_input.wait_for(timeout=15_000, state="attached")
                file_input.set_input_files(str(source))
                page.get_by_role("textbox", name="Title").fill("Imported standup")
                requests.clear()
                page.locator(".surface-actions").get_by_role(
                    "button", name="Import", exact=True
                ).click()
    
                import_post = None
                for _ in range(120):
                    posts = [r for r in requests if r["path"] == "/api/meetings/import"]
                    if posts:
                        import_post = posts[-1]
                        break
                    page.wait_for_timeout(100)
                assert import_post is not None, requests
                # Defect 10 at its source: the gesture sends no file mtime.
                assert "started_at_ms" not in import_post["body"], import_post
                print(f"IMPORT POST {import_post['path']} (no started_at_ms)")
    
                imported = None
                for _ in range(150):
                    rows = db.meetings.list_meetings()
                    done = [
                        row for row in rows
                        if row.id and db.meetings.get_meeting(row.id).segments
                    ]
                    if done:
                        imported = db.meetings.get_meeting(done[0].id)
                        break
                    page.wait_for_timeout(100)
                assert imported is not None, "the import never produced a transcript"
                print(f"IMPORTED {imported.id} segments={len(imported.segments)}")
    
                # ── the fence: it transcribed, and it stopped ──
                assert db.intel.list_intel_jobs() == [], db.intel.list_intel_jobs()
                assert db.intel.get_latest_intel_job(imported.id) is None
                assert engine.analyzed == [], engine.analyzed
                assert imported.intel is None
                assert imported.intel_status == "disabled", imported.intel_status
                # Defects 10 and 11: dated the import moment, transcript final.
                assert imported.started_at > datetime.now() - timedelta(minutes=10)
                assert imported.transcription_status == "complete", (
                    imported.transcription_status
                )
                print(
                    f"AFTER IMPORT jobs={db.intel.list_intel_jobs()} "
                    f"analyzed={engine.analyzed} intel_status={imported.intel_status} "
                    f"started_at={imported.started_at} "
                    f"transcription_status={imported.transcription_status}"
                )
    
                # ── station 2: the row tells the truth about its length ──
                open_meetings()
                row = page.get_by_test_id(f"meeting-row-{imported.id}")
                row.wait_for(timeout=15_000)
                row_words = row.text_content() or ""
                print(f"ROW {row_words}")
                assert "3 S" in row_words, row_words
                assert "1 MIN" not in row_words, row_words
                today = _ledger_date(datetime.now())
                assert today in row_words, (today, row_words)
                run_verb = row.get_by_test_id("run-intelligence-btn")
                run_verb.wait_for(timeout=15_000)
                detail = _api(
                    page, "GET", f"/api/meetings/{imported.id}", token=IMPORT_TOKEN
                )
                planned = detail["planned_route"]
                assert planned["status"] == "ready", planned
                host = planned["legs"][0]["host"]
                assert _chip_label(host) in (
                    row.get_by_test_id("row-route").text_content() or ""
                )
                assert detail.get("run_receipt") is None, detail.get("run_receipt")
                print(f"PLANNED host={host} hash={planned['selection_hash']}")
                _shot_10(page, "import-row-length")
    
                # ── station 3: the record, with the verb and the planned host ──
                row.locator(".meetings-stream-row-body").click()
                page.locator(".meetings-detail-head").wait_for(timeout=15_000)
                route_chip = page.get_by_test_id("detail-route")
                route_chip.wait_for(timeout=15_000)
                assert _chip_label(host) in (route_chip.text_content() or "")
                page.get_by_test_id("detail-run-intelligence-btn").wait_for(timeout=15_000)
                head = page.locator(".meetings-detail-head").text_content() or ""
                print(f"DETAIL HEAD {head}")
                assert "3 S" in head, head
                assert "1 MIN" not in head, head
                _shot_10(page, "import-done")
    
                # ── station 4: ask for it, and read the receipt ──
                requests.clear()
                page.get_by_test_id("detail-run-intelligence-btn").click()
                page.wait_for_timeout(600)
                run_post = [r for r in requests if r["path"].endswith("/intelligence/run")][-1]
                assert run_post["path"] == f"/api/meetings/{imported.id}/intelligence/run"
                assert json.loads(run_post["body"])["expected_selection_hash"] == (
                    planned["selection_hash"]
                ), run_post
                print(f"RUN POST {run_post}")
    
                _drain(db, imported.id)
                produced = db.meetings.get_meeting(imported.id)
                assert produced.intel is not None, "no summary was produced"
                assert produced.intel.summary == engine.result.summary
                assert engine.analyzed, "the provider was never contacted by the gesture"
                receipt = _api(
                    page, "GET", f"/api/meetings/{imported.id}/intel-recovery",
                    token=IMPORT_TOKEN,
                )["run_receipt"]
                assert receipt["outcome"] == "succeeded", receipt
                assert receipt["attempts"], receipt
                assert receipt["selection_hash"] == planned["selection_hash"], receipt
                assert receipt["attempts"][0]["host"] == host, receipt
                print(f"RECEIPT {receipt}")
    
                open_meetings()
                page.get_by_test_id(f"meeting-row-{imported.id}").locator(
                    ".meetings-stream-row-body"
                ).click()
                summary_text = page.get_by_test_id("meeting-summary-text")
                summary_text.wait_for(timeout=15_000)
>               assert (summary_text.text_content() or "").strip() == engine.result.summary
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_hs201_summary_face_glass.py:792: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:17839: in text_content
    self._sync(self._impl_obj.text_content(timeout=timeout))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:647: in text_content
    return await self._frame.text_content(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:705: in text_content
    return await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x15770d250>
cb = <function Channel.send.<locals>.<lambda> at 0x15bbfea20>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: Locator.text_content: Error: strict mode violation: get_by_test_id("meeting-summary-text") resolved to 2 elements:
E               1) <p class="summary-text" data-testid="meeting-summary-text">The team reviewed the budget.</p> aka get_by_test_id("arrival-meetings").get_by_test_id("meeting-summary-text")
E               2) <p class="summary-text" data-testid="meeting-summary-text">The team reviewed the budget.</p> aka get_by_role("region", name="Meetings").get_by_test_id("meeting-summary-text")
E           
E           Call log:
E             - waiting for get_by_test_id("meeting-summary-text")

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
----------------------------- Captured stdout call -----------------------------
FIXTURE core_path_smoke_16k.wav 2.79s mtime=2026-06-07 12:05:14.252429
IMPORT POST /api/meetings/import (no started_at_ms)
IMPORTED 99f006a9 segments=1
AFTER IMPORT jobs=[] analyzed=[] intel_status=disabled started_at=2026-09-23 12:05:17.353098 transcription_status=complete
ROW Imported standupSEP 23 · OFFSEP 23·3 S·9 WORDS·OFFTHIS DEVICERun summary
PLANNED host=same_device hash=sha256:11e044c071a798beb4a0fd6a60efc42fbc53807798275a2e99647835a38cc978
SHOT /Users/karol/dev/tools/wt-philo-3-02/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-row-length-1440.png
SHOT /Users/karol/dev/tools/wt-philo-3-02/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-row-length-393.png
DETAIL HEAD Imported standupSEP 23·3 S·SUMMARY OFF
SHOT /Users/karol/dev/tools/wt-philo-3-02/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-done-1440.png
SHOT /Users/karol/dev/tools/wt-philo-3-02/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-done-393.png
RUN POST {'path': '/api/meetings/99f006a9/intelligence/run', 'body': '{"expected_selection_hash":"sha256:11e044c071a798beb4a0fd6a60efc42fbc53807798275a2e99647835a38cc978"}'}
RECEIPT {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_557ed369f7a344bda1ce00f0e43e58ce', 'outcome': 'succeeded'}], 'job_id': 'ij_4d99d8f6e7a3670cc68c084041e4562c5e13c15a8d421a84412ee38c979c82fa', 'meeting_id': '99f006a9', 'outcome': 'succeeded', 'receipt_id': 'rr_c39030fffe826abd92366b6777fbadfe', 'selection_hash': 'sha256:11e044c071a798beb4a0fd6a60efc42fbc53807798275a2e99647835a38cc978'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
____ test_the_real_j4_import_case_fires_the_upload_and_binds_the_meeting_id ____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_the_real_j4_import_case_f0')

    def test_the_real_j4_import_case_fires_the_upload_and_binds_the_meeting_id(tmp_path):
        """Finding 2: the ACTUAL atlas case, through a synthetic import boundary
        that answers like the real route (202 {"meeting_id", "status"}). Before
        the fix: BLOCKED "unresolved placeholder … meeting_id", zero uploads."""
        case = _atlas_case(J4_IMPORT)
        assert case["trigger"]["capture_as"] == "meeting_id", "the atlas case changed"
>       record = calibrate(tmp_path, cases=[case])[0]
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_calibration.py:961: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
scripts/graph_walk.py:3400: in calibrate
    exercise(page, case, recorder=recorder, hub=fixture,
scripts/graph_walk.py:3083: in exercise
    trigger_record = run_step(trigger, page, hub, provenance, pre_case,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

step = {'adapter': 'http-route', 'capture_as': 'meeting_id', 'capture_path': 'meeting_id', 'expect_status': 202, ...}
page = <Page url='http://127.0.0.1:53249/'>
hub = <scripts.graph_walk.CalibrationServer object at 0x15b32e9e0>
provenance = {'boundary_substitutions': [], 'brief_sha256': 'ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800', 'cl...zz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_the_real_j4_import_case_f0/calibration-state.json', ...}
case = {'applicability': 'applicable', 'completion_bound_s': 300, 'edge_ids': ['edge.route.meetings_import'], 'expected': {'o...summary) [the audit\'s stated observation location: protocol: GET /api/meetings; protocol: GET /api/intel/jobs]'}, ...}

    def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
                 provenance: dict[str, Any], case: dict[str, Any] | None = None,
                 *, allow_error: bool = False,
                 variables: dict[str, str] | None = None) -> dict[str, Any]:
        """One setup step or the trigger, by kind. Records the adapter it drove."""
        kind = step.get("kind")
        if kind not in STEP_KINDS:
            raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                          f"{sorted(STEP_KINDS)}; nothing was fired")
        variables = variables if variables is not None else {}
        step = substitute(step, variables)
        missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
        if missing:
            raise Blocked(
                f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
                "step; nothing was sent. A `{name}` is filled by an earlier step's "
                "`capture_as`, never sent literally.")
    
        if kind == "check":
            # The same evaluator a verdict uses, at the point it stands. It is
            # given a bounded wait: a face that is still loading has not yet
            # refused the precondition.
            probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                       "predicate": step.get("predicate")}}
            deadline = time.monotonic() + float(step.get("timeout_s", 5))
            waited = 0.0
            while True:
                snap = snapshot(page, probe_case, hub)
                ok, why = check_predicate(step.get("predicate"), snap, snap)
                if ok or time.monotonic() >= deadline:
                    break
                if page is not None:
                    page.wait_for_timeout(300)
                waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
            record = {"kind": "check", "observe_at": step.get("observe_at"),
                      "predicate": step.get("predicate"),
                      "adapter": step.get("adapter", "observation"),
                      "waited_s": waited, "holds": ok, "reading": why}
            if not ok:
                raise Blocked(
                    f"precondition not met: {step.get('predicate')} at "
                    f"{step.get('observe_at')!r} — {why}")
            return record
    
        if kind == "ui":
            return _ui_step(page, step, hub)
        if kind == "api":
            if hub is None:
                raise Blocked("an api step needs a hub; this pass has none")
            status, payload = hub.api(step["method"], step["path"], step.get("body"))
            record = {"kind": "api", "method": step["method"], "path": step["path"],
                      "adapter": step.get("adapter", "http-route"), "status": status,
                      "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                      "response_sha256": hashlib.sha256(
                          json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
            want = step.get("expect_status")
            if want is not None and status != want:
                raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
            # A SETUP step that errors means the preconditions were never reached,
            # so the case is blocked. A TRIGGER's error status is the observation
            # itself (an intelligible refusal is a promised result), so it is
            # recorded and the predicate decides.
            if want is None and status >= 400 and not allow_error:
                raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
            name = step.get("capture_as")
            if name:
                where = step.get("capture_path", "id")
                found, value = _json_path(payload, where)
                if not found or value is None:
                    raise Blocked(
                        f"capture_as {name!r}: no value at {where!r} in the response "
                        f"of {step['method']} {step['path']}")
                variables[name] = str(value)
                record["captured"] = {"name": name, "path": where, "value": str(value)}
            return record
        if kind == "fixture":
            if hub is None:
                raise Blocked("a fixture step needs a hub; this pass has none")
            wav = REPO / step["path"]
            if not wav.exists():
                raise Blocked(f"fixture {wav} does not exist")
            provenance["fixture_hashes"][step["path"]] = _sha256(wav)
            route = step.get("route")
            if not route:
                raise Blocked(
                    f"no documented input boundary declared for {step['path']}; "
                    "the rig never opens a microphone")
>           status, payload = hub.upload(
                route["method"], route["path"], wav, step.get("field", "file"),
                form=step.get("form"))
E           TypeError: CalibrationServer.upload() got an unexpected keyword argument 'form'

scripts/graph_walk.py:2459: TypeError
_______ test_private_backend_route_and_recovery_decisions_are_classified _______

    def test_private_backend_route_and_recovery_decisions_are_classified() -> None:
        """A new private selector/retry/fallback helper fails closed until reviewed."""
        found = _private_decisions()
>       assert found == set(BACKEND_PRIVATE_DECISIONS), (
            "Unclassified private route/recovery decision(s): "
            f"{sorted(found - set(BACKEND_PRIVATE_DECISIONS))}; stale classifications: "
            f"{sorted(set(BACKEND_PRIVATE_DECISIONS) - found)}"
        )
E       AssertionError: Unclassified private route/recovery decision(s): [('holdspeak/services/meeting_intel_service.py', '_is_scheduled_retry')]; stale classifications: []
E       assert {('holdspeak/...resent'), ...} == {('holdspeak/...resent'), ...}
E         
E         Extra items in the left set:
E         ('holdspeak/services/meeting_intel_service.py', '_is_scheduled_retry')
E         Use -v to get more diff

tests/unit/test_phase143_surface_fallback_census.py:208: AssertionError
______________ test_the_last_known_observation_survives_a_restart ______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-357/test_the_last_known_observatio0')

    def test_the_last_known_observation_survives_a_restart(tmp_path: Path) -> None:
        """HS-200-15 left `LastKnownStore` process-local; a failed source after a
        restart replayed nothing.  With the durable store a fresh process still
        carries the last observation, marked as such."""
        db = _db(tmp_path)
        _seed_room(db)
        observed = "2026-09-07T08:41:00"
        items = [{"id": "p-q4:commitment:x", "projectId": "p-q4", "title": "Priya confirms the freeze window",
                  "source": "commitment", "why": "DUE TODAY", "severity": "warning", "since": observed}]
        LastKnownStore(db_factory=lambda: db).remember("project:p-q4", items=items, observed_at=observed,
                                                       label="Q4 Platform", project_id="p-q4")
    
        fresh = LastKnownStore(db_factory=lambda: Database(tmp_path / "continuity.db"))
        recalled = fresh.recall("project:p-q4")
>       assert recalled is not None and recalled["observed_at"] == observed
E       assert (None is not None)

tests/unit/test_phase200_continuity.py:423: AssertionError
____________ test_primary_copy_has_no_prohibited_operational_drift _____________

    def test_primary_copy_has_no_prohibited_operational_drift() -> None:
        recorded = _recorded_copy_debt()
        problems = [
            item
            for item in violations(inventory(REPO))
            if (str(item.path), item.rule_id, item.text) not in recorded
        ]
>       assert not problems, "Primary product-copy drift:\n  " + "\n  ".join(
            f"{item.path}:{item.line}: {item.rule_id}: {item.text}"
            for item in problems
        )
E       AssertionError: Primary product-copy drift:
E           web/src/desk/chair/ChairHome.tsx:1988: failure-missing-facts: DETAIL READ FAILED · {value
E       assert not [CopyViolation(rule_id='failure-missing-facts', path='web/src/desk/chair/ChairHome.tsx', line=1988, text='DETAIL READ ...iled, retained work, the next valid action, and the destination when relevant (missing: retained_work, next_action).')]

tests/unit/test_product_copy.py:74: AssertionError
=============================== warnings summary ===============================
tests/e2e/test_hs202_05_first_use_type_floor.py:283
  /Users/karol/dev/tools/wt-philo-3-02/tests/e2e/test_hs202_05_first_use_type_floor.py:283: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/e2e/test_hs202_05_first_use_type_floor.py:462
  /Users/karol/dev/tools/wt-philo-3-02/tests/e2e/test_hs202_05_first_use_type_floor.py:462: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:17: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:181: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:160: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:552: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:618: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:171: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:232: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:281: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:149: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:396: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:461: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:554: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:270: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:521: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:673: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:921: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1090: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:327: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1636: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:318: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:281: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:367: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-philo-3-02/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.fTmlfISJEP/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.fTmlfISJEP/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.fTmlfISJEP/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:84: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:139: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:169: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:207: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_web_runtime.py:269: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
ERROR tests/unit/test_graph_walk_calibration.py::test_a_captured_value_drives_a_later_step_and_the_predicate
ERROR tests/unit/test_graph_walk_calibration.py::test_every_new_predicate_kind_gets_its_verdict
ERROR tests/unit/test_graph_walk_calibration.py::test_a_refusal_status_is_read_from_the_triggers_own_response
ERROR tests/unit/test_graph_walk_calibration.py::test_a_row_gone_is_named_never_merely_fewer
ERROR tests/unit/test_graph_walk_calibration.py::test_protocol_field_reads_one_named_field
ERROR tests/unit/test_graph_walk_calibration.py::test_input_value_reads_the_field_not_the_dom_text
ERROR tests/unit/test_graph_walk_calibration.py::test_a_restart_is_a_real_restart_and_the_value_survives
ERROR tests/unit/test_graph_walk_calibration.py::test_a_refusal_must_name_what_is_missing
ERROR tests/unit/test_graph_walk_calibration.py::test_an_asserted_absence_is_earned_by_the_named_bound
ERROR tests/unit/test_graph_walk_calibration.py::test_a_clicked_verb_reads_its_identity_from_its_own_response
ERROR tests/unit/test_graph_walk_calibration.py::test_a_clicked_verb_status_is_read_by_its_declared_route
FAILED tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face
FAILED tests/e2e/test_hs200_attention_glass.py::TestAttentionGlass::test_long_row_393
FAILED tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read[393]
FAILED tests/e2e/test_hs200_task_resume_glass.py::test_saved_ask_draws_the_ratified_unfinished_row[393]
FAILED tests/e2e/test_hs201_12_thought_note_glass.py::test_thought_note_is_one_clean_note[1440]
FAILED tests/e2e/test_hs201_12_thought_note_glass.py::test_thought_note_is_one_clean_note[393]
FAILED tests/e2e/test_hs201_12_thought_note_glass.py::test_thought_note_long_context_and_open_well_never_clip[1440]
FAILED tests/e2e/test_hs201_12_thought_note_glass.py::test_thought_note_long_context_and_open_well_never_clip[393]
FAILED tests/e2e/test_hs201_lane_a_glass.py::test_summary_and_receipt_survive_real_hub_restart_on_both_glasses
FAILED tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again
FAILED tests/e2e/test_hs201_summary_face_glass.py::test_import_transcribes_and_stops_then_the_summary_is_asked_for
FAILED tests/unit/test_graph_walk_calibration.py::test_the_real_j4_import_case_fires_the_upload_and_binds_the_meeting_id
FAILED tests/unit/test_phase143_surface_fallback_census.py::test_private_backend_route_and_recovery_decisions_are_classified
FAILED tests/unit/test_phase200_continuity.py::test_the_last_known_observation_survives_a_restart
FAILED tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift
15 failed, 11530 passed, 116 skipped, 4 xfailed, 2 warnings, 11 errors in 5687.30s (1:34:47)
```

### Captured run — 2026-09-23T19:06:26Z

- **Command:** `/bin/zsh -c set -o pipefail; uv run --no-sync pytest -q tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_product_copy.py tests/e2e/test_hs201_lane_a_glass.py tests/e2e/test_hs201_summary_face_glass.py 2>&1 | tee docs/internal/philo/phase-3/summary/integration/summary-fallout.fixed.raw.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
...................                                                      [100%]
19 passed in 45.92s
```

### Captured run — 2026-09-23T19:07:34Z

- **Command:** `/bin/zsh -c set -o pipefail; npm --prefix web run check 2>&1 | tee docs/internal/philo/phase-3/summary/integration/full-web-final.raw.log`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build && npm run bundle:gate


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (11 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (826 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit

src/desk/chair/arrivalSummaryCompletion.test.tsx(148,9): error TS2769: No overload matches this call.
  Overload 1 of 2, '(role: ByRoleMatcher, options?: ByRoleOptions | undefined): HTMLElement', gave the following error.
    Object literal may only specify known properties, and 'exact' does not exist in type 'ByRoleOptions'.
  Overload 2 of 2, '(role: ByRoleMatcher, options?: ByRoleOptions | undefined): HTMLElement', gave the following error.
    Object literal may only specify known properties, and 'exact' does not exist in type 'ByRoleOptions'.
src/desk/chair/arrivalSummaryCompletion.test.tsx(277,74): error TS2769: No overload matches this call.
  Overload 1 of 2, '(role: ByRoleMatcher, options?: ByRoleOptions | undefined): HTMLElement', gave the following error.
    Object literal may only specify known properties, and 'exact' does not exist in type 'ByRoleOptions'.
  Overload 2 of 2, '(role: ByRoleMatcher, options?: ByRoleOptions | undefined): HTMLElement', gave the following error.
    Object literal may only specify known properties, and 'exact' does not exist in type 'ByRoleOptions'.
src/desk/chair/arrivalSummaryCompletion.test.tsx(344,9): error TS2769: No overload matches this call.
  Overload 1 of 2, '(role: ByRoleMatcher, options?: ByRoleOptions | undefined): HTMLElement', gave the following error.
    Object literal may only specify known properties, and 'exact' does not exist in type 'ByRoleOptions'.
  Overload 2 of 2, '(role: ByRoleMatcher, options?: ByRoleOptions | undefined): HTMLElement', gave the following error.
    Object literal may only specify known properties, and 'exact' does not exist in type 'ByRoleOptions'.
```

### Captured run — 2026-09-23T19:08:27Z

- **Command:** `/bin/zsh -c set -o pipefail; npm --prefix web run check 2>&1 | tee docs/internal/philo/phase-3/summary/integration/full-web-final.raw.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build && npm run bundle:gate


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (11 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (826 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-3-02/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-philo-3-02/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/wt-philo-3-02/web/node_modules/axe-core/axe.js:28249:12) undefined

 Test Files  306 passed (306)
      Tests  2806 passed (2806)
   Start at  13:08:36
   Duration  89.60s (transform 4.69s, setup 11.94s, import 31.98s, tests 61.26s, environment 52.44s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1690 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/api.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store/compositorSlice.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/usePrepareController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/SpeakFace.tsx but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/App.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/prepare/PreparePosture.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/recall/RecallFace.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/useProjectRoomController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/ImportSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/history/MeetingReview.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/concierge/useConciergeController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/InterviewPanel.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/NewWorkbenchChooser.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ScheduleCreateWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ThreadComposer.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/RoomActions.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/windowCommands.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/atmosphereActivity.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/infoContract.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/keymap.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/newThought.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/ThreadsSection.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/views/DecisionsView.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/useDeskChangedRefresh.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/ChangePlacesCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/threads.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/verbRegistry.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/callLoopWiring.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/CallChip.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/hooks/useChatImport.ts, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/shared/ThreadsSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-3-02/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                     0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2      4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2          4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2          4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2      4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2      4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2              4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2              5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2              5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2               5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2       5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2       5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff      5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2               5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2               5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff      5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff       5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff           5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff       5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff       5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff           5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff               6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff               6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff               6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff        6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff        7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff                7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff                7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff                7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2      7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2      7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2                7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                   7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2                7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                   7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                   7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2                7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff                 9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                    9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                    9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                   10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff      10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2           10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff      10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2           10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2           10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2      11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2      12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2      12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2          12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2          13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2          13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff            13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff            13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff            13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff           16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff       16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff       16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff       16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff           16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff           16.99 kB
../holdspeak/static/_built/assets/rainy-masonry-DIBtQ-m6.webp                            17.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2         21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2         21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                  23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                  24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                  24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff          27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff          28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                   30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                   31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                   31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2              35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2              36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2              36.26 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-77YHD8bZ.woff               47.56 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-BxGbmqWO.woff               48.49 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-CIVaiw4L.woff               48.67 kB
../holdspeak/static/_built/assets/wet-concrete-B8Jlfxi3.webp                             61.50 kB
../holdspeak/static/_built/assets/wet-asphalt-nQmNY0GR.webp                              65.97 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-cE2vkmv2.css                  0.50 kB │ gzip:   0.23 kB
../holdspeak/static/_built/assets/CadenceCore-BcDWJsh4.css                                0.63 kB │ gzip:   0.34 kB
../holdspeak/static/_built/assets/RepoWindow-Dmvmdom7.css                                 1.59 kB │ gzip:   0.64 kB
../holdspeak/static/_built/assets/SettingsCore-BVsDobrN.css                               2.51 kB │ gzip:   0.68 kB
../holdspeak/static/_built/assets/XtermPane-DDGTF8rc.css                                  3.62 kB │ gzip:   0.99 kB
../holdspeak/static/_built/assets/RoadmapWindow-BpQxUh51.css                              3.81 kB │ gzip:   1.07 kB
../holdspeak/static/_built/assets/PeopleCore-DawtcWHJ.css                                 4.94 kB │ gzip:   1.29 kB
../holdspeak/static/_built/assets/DoorCore-CASx1vIJ.css                                   5.56 kB │ gzip:   1.45 kB
../holdspeak/static/_built/assets/ConciergeCore-B7BZbZ8k.css                              8.77 kB │ gzip:   1.79 kB
../holdspeak/static/_built/assets/DictationCore-DMwTh7Sg.css                             13.08 kB │ gzip:   2.39 kB
../holdspeak/static/_built/assets/WorkbenchWindow-Bbq47XG1.css                           13.47 kB │ gzip:   2.50 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-oz-meLoZ.css                         22.75 kB │ gzip:   4.41 kB
../holdspeak/static/_built/assets/index-B77rbR73.css                                     91.91 kB │ gzip:  31.03 kB
../holdspeak/static/_built/assets/desk-C_h0bGUY.css                                     319.05 kB │ gzip:  47.58 kB
../holdspeak/static/_built/assets/atmosphereLighting-D2uEdGO0.js                          0.14 kB │ gzip:   0.14 kB
../holdspeak/static/_built/assets/WelcomePage-CyxSIprL.js                                 0.38 kB │ gzip:   0.27 kB
../holdspeak/static/_built/assets/core-layout-DwW2BQw8.js                                 0.44 kB │ gzip:   0.26 kB
../holdspeak/static/_built/assets/PresencePage-ClHKehZq.js                                0.56 kB │ gzip:   0.37 kB
../holdspeak/static/_built/assets/core-hooks-6QzhdsZM.js                                  0.57 kB │ gzip:   0.37 kB
../holdspeak/static/_built/assets/atmosphereControls-nB4jNh-k.js                          0.77 kB │ gzip:   0.41 kB
../holdspeak/static/_built/assets/Filter-CdpLmmfL.js                                      0.91 kB │ gzip:   0.48 kB
../holdspeak/static/_built/assets/ChangePlacesCore-DUkIvje5.js                            0.92 kB │ gzip:   0.49 kB
../holdspeak/static/_built/assets/useUndoReceipt-WsAK8cti.js                              1.63 kB │ gzip:   0.74 kB
../holdspeak/static/_built/assets/SetupCore--IBCYQbY.js                                   2.07 kB │ gzip:   1.02 kB
../holdspeak/static/_built/assets/api--17wQf3k.js                                         2.11 kB │ gzip:   0.70 kB
../holdspeak/static/_built/assets/greenhouseScene-CbiPReIQ.js                             2.48 kB │ gzip:   1.34 kB
../holdspeak/static/_built/assets/midnightArchiveScene-Cks10AbM.js                        2.49 kB │ gzip:   1.36 kB
../holdspeak/static/_built/assets/deepSeaScene-Kph6_2or.js                                2.81 kB │ gzip:   1.52 kB
../holdspeak/static/_built/assets/nightTrainScene-DxGfS3yD.js                             2.90 kB │ gzip:   1.57 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-DabD1chB.js                   2.99 kB │ gzip:   1.32 kB
../holdspeak/static/_built/assets/CompanionCore-D0102lyM.js                               3.00 kB │ gzip:   1.35 kB
../holdspeak/static/_built/assets/WorkbenchesHomeCore-5S9ccMZl.js                         3.04 kB │ gzip:   1.41 kB
../holdspeak/static/_built/assets/laundromatScene-BNGSS1T1.js                             3.05 kB │ gzip:   1.58 kB
../holdspeak/static/_built/assets/radioStationScene-s-EUOSVI.js                           3.20 kB │ gzip:   1.61 kB
../holdspeak/static/_built/assets/ActivityCore-D9019qA1.js                                3.24 kB │ gzip:   1.44 kB
../holdspeak/static/_built/assets/RoadmapWindow-CDXmMt5n.js                               3.62 kB │ gzip:   1.43 kB
../holdspeak/static/_built/assets/settingsWallpaper-Cobb1Up5.js                           3.62 kB │ gzip:   1.64 kB
../holdspeak/static/_built/assets/CommandsCore-CNcCvJoE.js                                4.00 kB │ gzip:   1.70 kB
../holdspeak/static/_built/assets/CalendarSnapshotReviewCore-CZhl4tQL.js                  4.06 kB │ gzip:   1.68 kB
../holdspeak/static/_built/assets/helpers-M5flVTQa.js                                     4.24 kB │ gzip:   1.59 kB
../holdspeak/static/_built/assets/api-zFCQnUGT.js                                         5.27 kB │ gzip:   1.73 kB
../holdspeak/static/_built/assets/Atmosphere-C8tbdz7d.js                                  5.32 kB │ gzip:   2.23 kB
../holdspeak/static/_built/assets/RepoWindow-CtSqsrOU.js                                  5.79 kB │ gzip:   2.43 kB
../holdspeak/static/_built/assets/usePrimitiveDetail-obyElAMt.js                          8.53 kB │ gzip:   3.16 kB
../holdspeak/static/_built/assets/ProcessCore-DIoLd8Hs.js                                 9.42 kB │ gzip:   3.60 kB
../holdspeak/static/_built/assets/ComponentsCore-DnKpQXup.js                              9.97 kB │ gzip:   3.74 kB
../holdspeak/static/_built/assets/LiveCore-C8umlqK_.js                                   10.22 kB │ gzip:   4.01 kB
../holdspeak/static/_built/assets/BufferResource-C4LK1JH2.js                             10.62 kB │ gzip:   2.80 kB
../holdspeak/static/_built/assets/CadenceCore-Bx1ltNIj.js                                10.78 kB │ gzip:   3.67 kB
../holdspeak/static/_built/assets/BitmapFont-7LjJlH5F.js                                 12.87 kB │ gzip:   4.71 kB
../holdspeak/static/_built/assets/webworkerAll-DV8tBX8s.js                               15.48 kB │ gzip:   4.91 kB
../holdspeak/static/_built/assets/sceneKit-DiGkm6FV.js                                   16.55 kB │ gzip:   6.13 kB
../holdspeak/static/_built/assets/DoorCore-BN2eGpom.js                                   17.50 kB │ gzip:   5.26 kB
../holdspeak/static/_built/assets/CanvasRenderer-CINaBUth.js                             17.54 kB │ gzip:   5.88 kB
../holdspeak/static/_built/assets/lanternGardenScene-xeGn5N5B.js                         18.98 kB │ gzip:   7.14 kB
../holdspeak/static/_built/assets/ConciergeCore-BS1Q3fwg.js                              22.94 kB │ gzip:   6.90 kB
../holdspeak/static/_built/assets/rainyCityScene-P7sWSGGp.js                             28.01 kB │ gzip:   9.68 kB
../holdspeak/static/_built/assets/PeopleCore-BhUh1532.js                                 28.21 kB │ gzip:   7.67 kB
../holdspeak/static/_built/assets/WebGPURenderer-DscjYNG2.js                             38.99 kB │ gzip:  10.91 kB
../holdspeak/static/_built/assets/WorkbenchWindow-BZ1Ii9TQ.js                            41.92 kB │ gzip:  13.72 kB
../holdspeak/static/_built/assets/browserAll-Bc0GFbyM.js                                 43.12 kB │ gzip:  11.33 kB
../holdspeak/static/_built/assets/DictationCore-DwtJcB5g.js                              46.37 kB │ gzip:  14.82 kB
../holdspeak/static/_built/assets/RenderTargetSystem-fZd_cpB-.js                         46.38 kB │ gzip:  12.73 kB
../holdspeak/static/_built/assets/SettingsCore-C5XhHWHW.js                               46.86 kB │ gzip:  14.27 kB
../holdspeak/static/_built/assets/HistoryCore-DTkqVASr.js                                47.99 kB │ gzip:  14.68 kB
../holdspeak/static/_built/assets/react-SZyUX699.js                                      48.46 kB │ gzip:  17.18 kB
../holdspeak/static/_built/assets/WebGLRenderer-5BHvq09u.js                              68.80 kB │ gzip:  18.91 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-BMeBZ5CD.js                         161.21 kB │ gzip:  44.27 kB
../holdspeak/static/_built/assets/index-CHOl_t-i.js                                     219.35 kB │ gzip:  69.02 kB
../holdspeak/static/_built/assets/WorldStage-BN7r78dv.js                                338.64 kB │ gzip: 107.28 kB
../holdspeak/static/_built/assets/XtermPane-DSPKOtY_.js                                 364.14 kB │ gzip:  93.99 kB
../holdspeak/static/_built/assets/UnrealBloomPass-COc2GKT4.js                           558.38 kB │ gzip: 141.32 kB
../holdspeak/static/_built/assets/desk-DbhWYbVw.js                                    1,320.40 kB │ gzip: 422.01 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.38s

> holdspeak-web@0.0.1 bundle:gate
> node scripts/check-bundle.mjs

bundle gate passed (Desk JS 1320404 B; Desk CSS 319048 B; source maps 0)
```

### Captured run — 2026-09-23T19:10:42Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.summary_text --viewport 1440 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CHOl_t-i.js'] hub=http://127.0.0.1:55358 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3ny5zb3b/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T191042Z-case.j6.run_summary.summary_text-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T191042Z-case.j6.run_summary.summary_text-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T191042Z-case.j6.run_summary.summary_text-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T19:11:50Z

- **Command:** `uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --brain astra --no-build --out pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final --case case.j6.run_summary.summary_text --viewport 393 --engine real`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
PASS: live
BRAIN: astra
SOURCE: 0ad59c0488ba100b516e3b1763d93a9a81f486ac dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-CHOl_t-i.js'] hub=http://127.0.0.1:55438 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-4cmejxvu/.local/share/holdspeak/holdspeak.db engine=real
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T191150Z-case.j6.run_summary.summary_text-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T191150Z-case.j6.run_summary.summary_text-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/final/20260923T191150Z-case.j6.run_summary.summary_text-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: observe_at text is present
```

### Captured run — 2026-09-23T19:15:47Z

- **Command:** `uv run --no-sync python .tmp/philo3-closure-verify.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
case.j6.run_summary.summary_text 1440 6.691 seconds; real engine; raw summary visible
case.j6.run_summary.summary_text 393 6.223 seconds; real engine; raw summary visible
60 retained observations; 40 actual case-width pairs; 30 pass; 10 blocked; no missing pairs; all linked shots present
Both restart identity records verified; synthetic WAV hash verified. Technical completion is separate from partial usefulness.
```

### Captured run — 2026-09-23T19:17:10Z

- **Command:** `uv run --no-sync python docs/internal/philo/phase-3/summary/verify_observations.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cfb65703d85e05bc98c8eac426817ff42f7a4342

```text
case.j6.run_summary.summary_text 1440 6.691 seconds; real engine; raw summary visible
case.j6.run_summary.summary_text 393 6.223 seconds; real engine; raw summary visible
60 retained observations; 40 actual case-width pairs; 30 pass; 10 blocked; no missing pairs; all linked shots present
Both restart identity records verified; synthetic WAV hash verified. Technical completion is separate from partial usefulness.
```
