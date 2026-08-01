# Evidence - HS-111-01

- **Story:** HS-111-01 - Settings
- **Status:** done
- **Date:** 2026-08-01

## Proof

### Captured run — 2026-08-01T17:59:55Z

- **Command:** `bash -c cd web && npm run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5dd76af6d8e295da8b56c69f7bdb6004c30b6563

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (53 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (193 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


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
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:206:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:206:7) undefined

 Test Files  65 passed (65)
      Tests  380 passed (380)
   Start at  12:00:00
   Duration  12.73s (transform 838ms, setup 1.67s, import 4.21s, tests 3.92s, environment 10.99s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1287 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/store.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/App.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/DictationCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/WorkbenchCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/settingsBespoke.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskCreateMenu.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/infoContract.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, dynamic import will not move module into another chunk.

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
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2         21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2         21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                  23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                  24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                  24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff          27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff          28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                   30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                   31.26 kB
../holdspeak/static/_built/assets/inter-la
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

Full run (untruncated): exit 0 — tokens match, token gate clean
(53 allow-listed exceptions, all in use), architecture guard passed
(193 files, zero framework residue), typecheck clean, **65 test files
/ 380 tests passed**, production build succeeded.

## What shipped

The Settings program rethought as the OS's own Prefs program
(Workbench 2.0 Prefs-drawer structure, dark Signal Workbench render),
per the audited rethink (agent audit + owner-ratified phase canon):

- **Gadget kit** — new reusable surface primitives in
  `web/src/desk/surface/gadgets.tsx` + `gadgets.css`: CheckGadget
  (replaces the sliding switch species GLOBALLY — DictationCore,
  ProfilesCore, ActivityCore, CommandsCore, ComponentsCore inherit),
  CycleGadget, MxRadio with indented dependent gadgets, StringGadget
  with in-well MicButton, StepperGadget, PropGadget, GadgetTable,
  SecretRow, EgressChip, GadgetGroup/GadgetRow (two-column sheet,
  26px rows, container-query stack under 420px).
- **Prefs drawer face** — `web/src/pages/cores/settingsPrefs.tsx`:
  authored 13-module registry (12 designed modules + System, the only
  place the generic walker survives; the wire can never mint a pane
  again), icon-grid tiles, filter string gadget with mic and
  deep-setting matches, POSTURE line with the precedence fact chain,
  footer status bar `« PREFS | USING · WRITTEN hh:mm:ss | DEFAULTS`
  (refusals land here; the whisper and InlineMessage banner are dead).
- **SettingsCore.tsx rewritten** (~70%) — kept the resource +
  debounced-save plumbing, secret calls, control-mode call, scope
  alias. Enums are cycle gadgets with option sets derived from
  `holdspeak/config.py`; the Runtime bays became an mx-radio column
  promoted to the Models module; the keycap is inverted-video with a
  block cursor (no glow); Credentials became SecretRows with the one
  etched LOCAL badge — all row-description prose deleted.
- Deleted species: settings rail, settings-bay cards, glow keycap,
  select gradient wash, sliding switch track, legacy search styles.

## Live proof (real hub, :8765)

Before/after shots in [assets/hs-111-01/](./assets/hs-111-01/):
`before-desktop-arrival.png` (sidebar + macOS rows + orange slider +
posture prose) vs `desktop-00-drawer-face.png`,
`desktop-06-models.png` (mx-radio + dependents),
`desktop-07-integrations.png` (SET/— chips, LOCAL badge, no prose),
`mobile-00-drawer-face.png` (same model at 393px, 3-column grid).
Full 21-shot set at both viewports reviewed during the walk
(`.tmp/hs-111-01-after/`).

## Honest notes

- Meetings device fields stay string gadgets — no audio-device-list
  endpoint exists yet (only mesh `/api/devices/health`); named for a
  follow-up.
- Delivery module ships the fact body ("CONFIG LIVES IN DELIVERY" +
  Open Delivery) — no delivery keys under `/api/settings`, verified
  live.
- DEFAULTS verb renders disabled (`defaults source pending`) — needs
  a per-section defaults source server-side.
- Two pre-existing red items in the shared working tree were repaired
  (DictationPage tests aligned to the already-modified `FINAL_TEXT:`
  receipt rendering; token allowlist reconciled 6 added / 14 stale
  removed) — the gate was red before this story started.
