# Evidence - HS-129-11

- **Story:** HS-129-11 - The walk
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T22:24:24Z

- **Command:** `npm --prefix web run test:web`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a8f549559ee8305bb660fc77946678717d9e8029

```text

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
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:188:7) undefined

 Test Files  109 passed (109)
      Tests  778 passed (778)
   Start at  16:24:24
   Duration  26.38s (transform 1.96s, setup 3.11s, import 9.97s, tests 10.88s, environment 20.37s)
```

### Captured run — 2026-08-08T22:24:55Z

- **Command:** `npm --prefix web run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a8f549559ee8305bb660fc77946678717d9e8029

```text

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```

## Failure classification — suite repair half

| Test | Verdict | Why | Fix |
|---|---|---|---|
| `ask` — hub error | Product bug | Structured hub refusals were discarded for a generic status message. | Preserve `error` and `unknown_ids` in `runAsk`. |
| `chat` — empty grounding refusal | Product bug | `runChatTurn` likewise discarded the hub's refusal receipt. | Preserve `error` and `unknown_ids` in `runChatTurn`. |
| `grounding` — unknown id refusal | Product bug | Same `runAsk` receipt loss; unknown IDs must be named. | Covered by the `runAsk` fix. |
| `commandDeck` — Enter top hit | Test-stale | HS-124 made the search an ARIA combobox and rows listbox options. | Query the current semantic roles. |
| `commandDeck` — ArrowDown/Enter | Test-stale | Current ranking may move to a program before an object. | Assert selection movement and the shared recents receipt. |
| `commandDeck` — MEETINGS band | Test-stale | HS-124 listbox semantics replaced button roles. | Query the meeting option. |
| `commandDeck` — Escape ladder | Test-stale | HS-124 search is a combobox. | Query the combobox. |
| `commandDeck` — cold launcher | Test-stale | HS-124 rows are options, not buttons. | Query program options. |
| `floorMenu` — Open | Test-stale | HS-129-08 correctly carries an optional editor/window origin through the open path. | Expect the explicit `undefined` origin. |
| `verbRegistry` — closed menu scope | Test-stale | Phase 128/129 adds the valid Window menu face. | Include `window`. |
| `verbRegistry` — bound keys | Test-stale | Current registry correctly declares rename, delete, and reverse-cycle bindings. | Assert the expanded registered set. |
| `DeskArrival` — advanced shelf | Test-stale | HS-124 changed shelf rows to listbox options. | Query options. |
| `DeskArrival` — object lookup | Test-stale | HS-124 changed the field to a combobox and results to options. | Query current roles. |
| `DeskArrival` — resource discovery | Test-stale | The current cold deck deliberately caps SETTINGS; queries remain discoverable. | Search each resource through the combobox. |
| `DeskArrival` — ready action | Test-stale | HS-124 contextual rows are options. | Query the contextual option. |
| `DeskListView` — unrendered-page search | Test-stale | HS-124 result rows are options. | Query the result option. |
| `DeskListView` — chrome toggle | Test-stale | Phase 124 made DeskChrome require its RuntimeBus context. | Mock the bus at this unit boundary. |

The full-suite pass also found two unrelated stale assertions: `storeSplit` now
correctly keeps an editor in its open pullout (HS-129-08), and
`ContextualPullout` correctly uses concise `REPLY FAILED · RETRY` and
`DRAFT RECOVERED` states (HS-129-09). Their tests now assert those current
behaviors.

### Captured run — 2026-08-08T22:55:31Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe8b5c89cea4846d3e04d683ea3d47b34b33cbb6

```text
FAIL Intelligence: default: horizontal overflow
FAIL Intelligence: scroll-top: horizontal overflow
FAIL Intelligence: scroll-mid: horizontal overflow
FAIL Intelligence: scroll-bottom: horizontal overflow
FAIL Intelligence: resized-small: horizontal overflow
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | FAIL
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
WALK Desk memory | default (non-window) | PASS
WALK Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Panes | default (non-window) | PASS
FAIL Intelligence Brief: default: horizontal overflow
FAIL Intelligence Brief: scroll-top: horizontal overflow
FAIL Intelligence Brief: scroll-mid: horizontal overflow
FAIL Intelligence Brief: scroll-bottom: horizontal overflow
FAIL Intelligence Brief: resized-small: horizontal overflow
WALK Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | FAIL
WALK Intelligence Follow-through | default, resized-small, maximized | PASS
FAIL Intelligence Receipts: default: horizontal overflow
FAIL Intelligence Receipts: resized-small: horizontal overflow
WALK Intelligence Receipts | default, resized-small, maximized | FAIL
FAIL HARNESS: locator.click: Timeout 30000ms exceeded.
Call log:
[2m  - waiting for locator('.meeting-row, .surface-ledger-line, [data-meeting-id], button:has-text(\'Untitled meeting\')').first()[22m
[2m    - locator resolved to <button type="button" data-kind="meeting" aria-label="Untitled meeting" data-obj-id="meeting:2b1df22c">Untitled meeting</button>[22m
[2m  - attempting click action[22m
[2m    2 × waiting for element to be visible, enabled and stable[22m
[2m      - element is visible, enabled and stable[22m
[2m      - scrolling into view if needed[22m
[2m      - done scrolling[22m
[2m      - <div class="desk-menubar">…</div> intercepts pointer events[22m
[2m    - retrying click action[22m
[2m    - waiting 20ms[22m
[2m    2 × waiting for element to be visible, enabled and stable[22m
[2m      - element is visible, enabled and stable[22m
[2m      - scrolling into view if needed[22m
[2m      - done scrolling[22m
[2m      - <div class="desk-menubar">…</div> intercepts pointer events[22m
[2m    - retrying click action[22m
[2m      - waiting 100ms[22m
[2m    47 × waiting for element to be visible, enabled and stable[22m
[2m       - element is visible, enabled and stable[22m
[2m       - scrolling into view if needed[22m
[2m       - done scrolling[22m
[2m       - <div class="desk-menubar">…</div> intercepts pointer events[22m
[2m     - retrying click action[22m
[2m       - waiting 500ms[22m

    at /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:233:38

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | FAIL |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Desk memory | default (non-window) | footer/head/overflow/height | PASS |
| Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Panes | default (non-window) | footer/head/overflow/height | PASS |
| Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | FAIL |
| Intelligence Follow-through | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Receipts | default, resized-small, maximized | footer/head/overflow/height | FAIL |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 11 surfaces; 13 violations; 0 console errors.
```

### Captured run — 2026-08-08T22:57:34Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe8b5c89cea4846d3e04d683ea3d47b34b33cbb6

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens drifted from design-tokens.json — run: node scripts/generate-tokens.cjs
```

### Captured run — 2026-08-08T22:58:12Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe8b5c89cea4846d3e04d683ea3d47b34b33cbb6

```text
FAIL Intelligence: default: horizontal overflow
FAIL Intelligence: scroll-top: horizontal overflow
FAIL Intelligence: scroll-mid: horizontal overflow
FAIL Intelligence: scroll-bottom: horizontal overflow
FAIL Intelligence: resized-small: horizontal overflow
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | FAIL
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
WALK Desk memory | default (non-window) | PASS
WALK Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Panes | default (non-window) | PASS
FAIL Intelligence Brief: default: horizontal overflow
FAIL Intelligence Brief: scroll-top: horizontal overflow
FAIL Intelligence Brief: scroll-mid: horizontal overflow
FAIL Intelligence Brief: scroll-bottom: horizontal overflow
FAIL Intelligence Brief: resized-small: horizontal overflow
WALK Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | FAIL
WALK Intelligence Follow-through | default, resized-small, maximized | PASS
FAIL Intelligence Receipts: default: horizontal overflow
FAIL Intelligence Receipts: resized-small: horizontal overflow
WALK Intelligence Receipts | default, resized-small, maximized | FAIL
WALK Meetings detail | default, resized-small, maximized | PASS
WALK Settings Transcription | default, resized-small, maximized | PASS
WALK Settings Guide | default, resized-small, maximized | PASS
GO ENTRIES: Speak | Ask AI | Meetings | Settings | Workbenches | Agents and coder sessions | Runs on | Integrations | Commands | Cadence | Context | Activity | Processes
WALK Go Speak | default, resized-small, maximized | PASS
WALK Go Ask AI | default, resized-small, maximized | PASS
WALK Go Meetings | default, resized-small, maximized | PASS
WALK Go Settings | default, resized-small, maximized | PASS
WALK Go Workbenches | default, resized-small, maximized | PASS
WALK Go Agents and coder sessions | default, resized-small, maximized | PASS
WALK Go Runs on | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Go Integrations | default, resized-small, maximized | PASS
WALK Go Commands | default, resized-small, maximized | PASS
WALK Go Cadence | default, resized-small, maximized | PASS
WALK Go Context | default, resized-small, maximized | PASS
WALK Go Activity | default, resized-small, maximized | PASS
WALK Go Processes | default, resized-small, maximized | PASS
FAIL Object zone: No reachable zone body
WALK Object zone | unreachable | FAIL
FAIL Object meeting: meeting: absent from this live desk
WALK Object meeting | unreachable | FAIL
FAIL Object artifact: artifact: absent from this live desk
WALK Object artifact | unreachable | FAIL
FAIL Object workbench: workbench: absent from this live desk
WALK Object workbench | unreachable | FAIL
WALK Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Design components | default, resized-small, maximized | PASS
WALK New Note editor | default (non-window) | PASS
WALK Speak mobile | default | PASS
WALK Settings mobile | default | PASS
WALK Meetings mobile | default | PASS
WALK Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | PASS

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | FAIL |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Desk memory | default (non-window) | footer/head/overflow/height | PASS |
| Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Panes | default (non-window) | footer/head/overflow/height | PASS |
| Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | FAIL |
| Intelligence Follow-through | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Receipts | default, resized-small, maximized | footer/head/overflow/height | FAIL |
| Meetings detail | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings Transcription | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings Guide | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Ask AI | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Workbenches | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Agents and coder sessions | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Runs on | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Integrations | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Commands | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Cadence | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Context | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Activity | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Processes | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object zone | unreachable | footer/head/overflow/height | FAIL |
| Object meeting | unreachable | footer/head/overflow/height | FAIL |
| Object artifact | unreachable | footer/head/overflow/height | FAIL |
| Object workbench | unreachable | footer/head/overflow/height | FAIL |
| Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Design components | default, resized-small, maximized | footer/head/overflow/height | PASS |
| New Note editor | default (non-window) | footer/head/overflow/height | PASS |
| Speak mobile | default | footer/head/overflow/height | PASS |
| Settings mobile | default | footer/head/overflow/height | PASS |
| Meetings mobile | default | footer/head/overflow/height | PASS |
| Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | footer/head/overflow/height | PASS |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 38 surfaces; 16 violations; 0 console errors.
```

### Captured run — 2026-08-08T23:10:15Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
FAIL HARNESS: locator.focus: Timeout 30000ms exceeded.
Call log:
[2m  - waiting for getByRole('button', { name: 'Desk memory', exact: true }).last()[22m

    at openDock (/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:159:18)
    at async file:///private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:217:5

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 5 surfaces; 1 violations; 0 console errors.
```

### Captured run — 2026-08-08T23:11:52Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text
FAIL HARNESS: TypeError: button.wait is not a function
    at openDock (file:///private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:155:16)
    at file:///private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:218:11

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 0 surfaces; 1 violations; 0 console errors.
```

### Captured run — 2026-08-08T23:12:11Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
FAIL HARNESS: locator.waitFor: Timeout 10000ms exceeded.
Call log:
[2m  - waiting for locator('.desk-dock button[aria-label="Desk memory"]').last() to be visible[22m

    at openDock (/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:155:16)
    at /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs:218:11

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 5 surfaces; 1 violations; 0 console errors.
```

### Captured run — 2026-08-08T23:13:32Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
WALK Desk memory | default (non-window) | PASS
WALK Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Panes | default (non-window) | PASS
WALK Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Intelligence Follow-through | default, resized-small, maximized | PASS
WALK Intelligence Receipts | default, resized-small, maximized | PASS
WALK Meetings detail | default, resized-small, maximized | PASS
FAIL Settings Transcription: face not present
FAIL Settings Guide: face not present
GO ENTRIES: Speak | Ask AI | Meetings | Settings | Workbenches | Agents and coder sessions | Runs on | Integrations | Commands | Cadence | Context | Activity | Processes
WALK Go Speak | default, resized-small, maximized | PASS
WALK Go Ask AI | default, resized-small, maximized | PASS
WALK Go Meetings | default, resized-small, maximized | PASS
WALK Go Settings | default, resized-small, maximized | PASS
WALK Go Workbenches | default, resized-small, maximized | PASS
WALK Go Agents and coder sessions | default, resized-small, maximized | PASS
WALK Go Runs on | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Go Integrations | default, resized-small, maximized | PASS
WALK Go Commands | default, resized-small, maximized | PASS
WALK Go Cadence | default, resized-small, maximized | PASS
WALK Go Context | default, resized-small, maximized | PASS
WALK Go Activity | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Go Processes | default, resized-small, maximized | PASS
WALK Object zone | default, resized-small, maximized | PASS
WALK Object meeting | default, resized-small, maximized | PASS
FAIL Object artifact: page.goto: Timeout 30000ms exceeded.
Call log:
[2m  - navigating to "http://127.0.0.1:61308/?token=uMcN-J7wwRrQRTWcac5Ucc_2Wf9kv6wf", waiting until "networkidle"[22m

WALK Object artifact | unreachable | FAIL
WALK Object workbench | default, resized-small, maximized | PASS
WALK Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Design components | default, resized-small, maximized | PASS
WALK New Note editor | default (non-window) | PASS
WALK Speak mobile | default | PASS
WALK Settings mobile | default | PASS
WALK Meetings mobile | default | PASS
WALK Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | PASS
FAIL Console: Failed to load resource: the server responded with a status of 500 (Internal Server Error)

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Desk memory | default (non-window) | footer/head/overflow/height | PASS |
| Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Panes | default (non-window) | footer/head/overflow/height | PASS |
| Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Follow-through | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Receipts | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings detail | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Ask AI | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Workbenches | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Agents and coder sessions | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Runs on | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Integrations | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Commands | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Cadence | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Context | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Activity | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Processes | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object zone | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object meeting | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object artifact | unreachable | footer/head/overflow/height | FAIL |
| Object workbench | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Design components | default, resized-small, maximized | footer/head/overflow/height | PASS |
| New Note editor | default (non-window) | footer/head/overflow/height | PASS |
| Speak mobile | default | footer/head/overflow/height | PASS |
| Settings mobile | default | footer/head/overflow/height | PASS |
| Meetings mobile | default | footer/head/overflow/height | PASS |
| Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | footer/head/overflow/height | PASS |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 36 surfaces; 4 violations; 1 console errors.
```

### Captured run — 2026-08-08T23:19:08Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
WALK Desk memory | default (non-window) | PASS
WALK Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Panes | default (non-window) | PASS
WALK Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Intelligence Follow-through | default, resized-small, maximized | PASS
WALK Intelligence Receipts | default, resized-small, maximized | PASS
WALK Meetings detail | default, resized-small, maximized | PASS
WALK Settings Transcription | default, resized-small, maximized | PASS
WALK Settings Guide | default, resized-small, maximized | PASS
GO ENTRIES: Speak | Ask AI | Meetings | Settings | Workbenches | Agents and coder sessions | Runs on | Integrations | Commands | Cadence | Context | Activity | Processes
WALK Go Speak | default, resized-small, maximized | PASS
WALK Go Ask AI | default, resized-small, maximized | PASS
WALK Go Meetings | default, resized-small, maximized | PASS
WALK Go Settings | default, resized-small, maximized | PASS
WALK Go Workbenches | default, resized-small, maximized | PASS
WALK Go Agents and coder sessions | default, resized-small, maximized | PASS
WALK Go Runs on | default, resized-small, maximized | PASS
WALK Go Integrations | default, resized-small, maximized | PASS
WALK Go Commands | default, resized-small, maximized | PASS
WALK Go Cadence | default, resized-small, maximized | PASS
WALK Go Context | default, resized-small, maximized | PASS
WALK Go Activity | default, resized-small, maximized | PASS
WALK Go Processes | default, resized-small, maximized | PASS
FAIL Object zone: No reachable zone body
WALK Object zone | unreachable | FAIL
FAIL Object meeting: meeting: absent from this live desk
WALK Object meeting | unreachable | FAIL
FAIL Object artifact: artifact: absent from this live desk
WALK Object artifact | unreachable | FAIL
FAIL Object workbench: workbench: absent from this live desk
WALK Object workbench | unreachable | FAIL
WALK Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Design components | default, resized-small, maximized | PASS
WALK New Note editor | default (non-window) | PASS
WALK Speak mobile | default | PASS
WALK Settings mobile | default | PASS
WALK Meetings mobile | default | PASS
WALK Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | PASS

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Desk memory | default (non-window) | footer/head/overflow/height | PASS |
| Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Panes | default (non-window) | footer/head/overflow/height | PASS |
| Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Follow-through | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Receipts | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings detail | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings Transcription | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings Guide | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Ask AI | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Workbenches | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Agents and coder sessions | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Runs on | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Integrations | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Commands | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Cadence | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Context | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Activity | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Processes | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object zone | unreachable | footer/head/overflow/height | FAIL |
| Object meeting | unreachable | footer/head/overflow/height | FAIL |
| Object artifact | unreachable | footer/head/overflow/height | FAIL |
| Object workbench | unreachable | footer/head/overflow/height | FAIL |
| Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Design components | default, resized-small, maximized | footer/head/overflow/height | PASS |
| New Note editor | default (non-window) | footer/head/overflow/height | PASS |
| Speak mobile | default | footer/head/overflow/height | PASS |
| Settings mobile | default | footer/head/overflow/height | PASS |
| Meetings mobile | default | footer/head/overflow/height | PASS |
| Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | footer/head/overflow/height | PASS |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 38 surfaces; 4 violations; 0 console errors.
```

### Captured run — 2026-08-08T23:23:49Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9339d6fd-826a-46b0-b0f2-1e240cda6a4d/scratchpad/walk-129.mjs`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text
WALK Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Speak | default, resized-small, maximized | PASS
WALK Meetings | default, resized-small, maximized | PASS
WALK Agents | default, resized-small, maximized | PASS
WALK Settings | default, resized-small, maximized | PASS
WALK Desk memory | default (non-window) | PASS
WALK Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Panes | default (non-window) | PASS
WALK Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Intelligence Follow-through | default, resized-small, maximized | PASS
WALK Intelligence Receipts | default, resized-small, maximized | PASS
WALK Meetings detail | default, resized-small, maximized | PASS
WALK Settings Transcription | default, resized-small, maximized | PASS
WALK Settings Guide | default, resized-small, maximized | PASS
GO ENTRIES: Speak | Ask AI | Meetings | Settings | Workbenches | Agents and coder sessions | Runs on | Integrations | Commands | Cadence | Context | Activity | Processes
WALK Go Speak | default, resized-small, maximized | PASS
WALK Go Ask AI | default, resized-small, maximized | PASS
WALK Go Meetings | default, resized-small, maximized | PASS
WALK Go Settings | default, resized-small, maximized | PASS
WALK Go Workbenches | default, resized-small, maximized | PASS
WALK Go Agents and coder sessions | default, resized-small, maximized | PASS
WALK Go Runs on | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Go Integrations | default, resized-small, maximized | PASS
WALK Go Commands | default, resized-small, maximized | PASS
WALK Go Cadence | default, resized-small, maximized | PASS
WALK Go Context | default, resized-small, maximized | PASS
WALK Go Activity | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Go Processes | default, resized-small, maximized | PASS
WALK Object zone | default, resized-small, maximized | PASS
WALK Object meeting | default, resized-small, maximized | PASS
WALK Object artifact | default, resized-small, maximized | PASS
WALK Object workbench | default, resized-small, maximized | PASS
WALK Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | PASS
WALK Design components | default, resized-small, maximized | PASS
WALK New Note editor | default (non-window) | PASS
WALK Speak mobile | default | PASS
WALK Settings mobile | default | PASS
WALK Meetings mobile | default | PASS
WALK Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | PASS

=== HS-129-11 WALK REPORT ===
| Surface | States walked | Assertions | Verdict |
|---|---|---|---|
| Intelligence | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Agents | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Desk memory | default (non-window) | footer/head/overflow/height | PASS |
| Delivery | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Panes | default (non-window) | footer/head/overflow/height | PASS |
| Intelligence Brief | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Follow-through | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Intelligence Receipts | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Meetings detail | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings Transcription | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Settings Guide | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Speak | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Ask AI | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Meetings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Settings | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Workbenches | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Agents and coder sessions | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Runs on | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Integrations | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Commands | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Cadence | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Context | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Activity | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Go Processes | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object zone | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object meeting | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object artifact | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Object workbench | default, resized-small, maximized | footer/head/overflow/height | PASS |
| Trust egress | default, scroll-top, scroll-mid, scroll-bottom, resized-small, maximized | footer/head/overflow/height | PASS |
| Design components | default, resized-small, maximized | footer/head/overflow/height | PASS |
| New Note editor | default (non-window) | footer/head/overflow/height | PASS |
| Speak mobile | default | footer/head/overflow/height | PASS |
| Settings mobile | default | footer/head/overflow/height | PASS |
| Meetings mobile | default | footer/head/overflow/height | PASS |
| Intelligence mobile | default, scroll-top, scroll-mid, scroll-bottom | footer/head/overflow/height | PASS |
PIXl/WEBGL WARNINGS (non-failing): 0
SUMMARY: 38 surfaces; 0 violations; 0 console errors.
```

### Captured run — 2026-08-08T23:28:16Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3bda09a1cf022cf6a9fd9198f7c80bdcb3084d16

```text

> holdspeak-web@0.0.1 check
> npm run tokens:check && npm run tokens:gate && npm run guard:architecture && npm run typecheck && npm run test:web && npm run build


> holdspeak-web@0.0.1 tokens:check
> node scripts/generate-tokens.cjs --check

tokens.css and tokens.gen.ts match design-tokens.json

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (12 allow-listed exceptions, all in use)

> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (386 source files; zero framework residue).

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
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts:188:7) undefined

 Test Files  109 passed (109)
      Tests  779 passed (779)
   Start at  17:28:22
   Duration  25.67s (transform 1.55s, setup 3.06s, import 9.07s, tests 10.71s, environment 20.18s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1450 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EditorAIBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/voice/intentRouter.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/store/compositorSlice.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/App.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RunsOnPicker.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/UtteranceWell.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/ImportSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EditorAIBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/infoContract.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/keymap.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/ReceiptsView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

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
../holdspeak/static/_built/asset
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

## Backend verdict — 2026-08-08

Commit `48802f23` records the backend triage. Of 98 failures, 96 reproduce on
pre-129 main and are the inherited ledger; the one 129-caused delivery collector
failure is fixed (21 delivery tests green), and the mesh case is flaky/environmental.
See [`backend-suite-branch.log`](assets/hs-129-11/backend-suite-branch.log) and
[`backend-triage-on-main.log`](assets/hs-129-11/backend-triage-on-main.log).
The story criterion amendment is recorded in the story and phase decision log; the
owner may overrule it at the sitting.
