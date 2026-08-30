# Evidence - HS-151-05

- **Story:** HS-151-05 - The Thread on the Desk (primitive, verbs, ThreadPullout, streaming renderer)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T00:00:08Z

- **Command:** `npm --prefix web run test:desk`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1350df8cfbfb24cf9cafe827d85bc7f377de06a0

```text

> holdspeak-web@0.0.1 test:desk
> vitest run src/desk --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web

 ❯ src/desk/components/MicButton.test.tsx (17 tests | 1 failed) 1200ms
     × never claims retention the session cannot prove 1010ms
 ❯ src/desk/components/__tests__/workbenchAutomations.test.tsx (5 tests | 1 failed) 991ms
     × tests without delivering work, then enables and pauses the trigger 180ms
stderr | src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
An update to NotePullout inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act
An update to NotePullout inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act

 ❯ src/desk/components/InlineEditor.test.tsx (10 tests | 1 failed) 194ms
     × hosts note editing in its open pullout 16ms
 ❯ src/desk/__tests__/containerQueryLaw.test.ts (3 tests | 1 failed) 5ms
     × keeps viewport-width media limited to shell exceptions 2ms
 ❯ src/desk/__tests__/writeReceiptGuard.test.ts (7 tests | 1 failed) 11ms
     × keeps every desk write out of a bare catch 7ms
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/axe-core/axe.js:28249:12) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web/src/desk/gl/engine.ts:188:7) undefined

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 5 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
AssertionError: expected [ …(7) ] to include '/src/desk/chair/chair.css'
 ❯ src/desk/__tests__/containerQueryLaw.test.ts:61:45
     59|     for (const [path, css] of Object.entries(cssSources)) {
     60|       if (/@media\s*\(\s*(?:max|min)-width/.test(css)) {
     61|         expect(viewportWidthMediaAllowlist).toContain(path);
       |                                             ^
     62|       }
     63|     }

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/5]⎯

 FAIL  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
AssertionError: expected [ Array(1) ] to deeply equal []

- Expected
+ Received

- []
+ [
+   "/src/desk/chair/lanes/BriefLane.tsx: 1 swallowed (allowed 0) at 102",
+ ]

 ❯ src/desk/__tests__/writeReceiptGuard.test.ts:167:23
    165|       }
    166|     }
    167|     expect(offenders).toEqual([]);
       |                       ^
    168|   });
    169|

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/5]⎯

 FAIL  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Save"

Here are the accessible roles:

  contentinfo:

  Name "":
  [36m<footer[39m
    [33mclass[39m=[32m"surface-footer"[39m
  [36m/>[39m

  --------------------------------------------------

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"desk-pullout-body desk-surface-body desk-editor-body"[39m
    [36m>[39m
      [36m<div[39m
        [33mdata-testid[39m=[32m"editor-note"[39m
      [36m>[39m
        [0mEditor[0m
      [36m</div>[39m
    [36m</div>[39m
    [36m<footer[39m
      [33mclass[39m=[32m"surface-footer"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"surface-footer-layout"[39m
      [36m>[39m
        [36m<div[39m
          [33mclass[39m=[32m"surface-footer-egress"[39m
        [36m/>[39m
        [36m<div[39m
          [33mclass[39m=[32m"surface-footer-receipt"[39m
        [36m/>[39m
        [36m<div[39m
          [33mclass[39m=[32m"surface-footer-verbs"[39m
        [36m/>[39m
      [36m</div>[39m
    [36m</footer>[39m
  [36m</div>[39m
[36m</body>[39m
 ❯ Object.getElementError node_modules/@testing-library/dom/dist/config.js:37:19
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:76:38
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:52:17
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:95:19
 ❯ src/desk/components/InlineEditor.test.tsx:92:19
     90|
     91|     expect(screen.getByTestId(`editor-${kind}`)).toBeInTheDocument();
     92|     expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocu…
       |                   ^
     93|     expect(container.querySelector(".desk-vignette")).toBeNull();
     94|   });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[3/5]⎯

 FAIL  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
TestingLibraryElementError: Unable to find an element with the text: /Retry the capture/. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<button[39m
      [33maria-label[39m=[32m"Speak again"[39m
      [33mclass[39m=[32m"desk-mic is-failed"[39m
      [33mtitle[39m=[32m"TRANSCRIPTION FAILED · Transcription did not finish. Your draft remains editable. Retry or type below."[39m
      [33mtype[39m=[32m"button"[39m
    [36m>[39m
      [36m<span[39m
        [33maria-hidden[39m=[32m"true"[39m
      [36m>[39m
        [36m<img[39m
          [33malt[39m=[32m""[39m
          [33mclass[39m=[32m"desk-chrome-sprite"[39m
          [33mdraggable[39m=[32m"false"[39m
          [33mheight[39m=[32m"16"[39m
          [33msrc[39m=[32m"/desk/sprites/system/mic.png"[39m
          [33mwidth[39m=[32m"16"[39m
        [36m/>[39m
      [36m</span>[39m
    [36m</button>[39m
    [36m<span[39m
      [33mclass[39m=[32m"desk-mic-failure"[39m
      [33mrole[39m=[32m"status"[39m
    [36m>[39m
      [36m<b[39m
        [33mclass[39m=[32m"desk-mic-failure-code"[39m
      [36m>[39m
        [0mTRANSCRIPTION FAILED[0m
      [36m</b>[39m
      [0m [0m
      [0mTranscription did not finish. Your draft remains editable. Retry or type below.[0m
    [36m</span>[39m
  [36m</div>[39m
[36m</body>[39m

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div>[39m
      [36m<button[39m
        [33maria-label[39m=[32m"Speak again"[39m
        [33mclass[39m=[32m"desk-mic is-failed"[39m
        [33mtitle[39m=[32m"TRANSCRIPTION FAILED · Transcription did not finish. Your draft remains editable. Retry or type below."[39m
        [33mtype[39m=[32m"button"[39m
      [36m>[39m
        [36m<span[39m
          [33maria-hidden[39m=[32m"true"[39m
        [36m>[39m
          [36m<img[39m
            [33malt[39m=[32m""[39m
            [33mclass[39m=[32m"desk-chrome-sprite"[39m
            [33mdraggable[39m=[32m"false"[39m
            [33mheight[39m=[32m"16"[39m
            [33msrc[39m=[32m"/desk/sprites/system/mic.png"[39m
            [33mwidth[39m=[32m"16"[39m
          [36m/>[39m
        [36m</span>[39m
      [36m</button>[39m
      [36m<span[39m
        [33mclass[39m=[32m"desk-mic-failure"[39m
        [33mrole[39m=[32m"status"[39m
      [36m>[39m
        [36m<b[39m
          [33mclass[39m=[32m"desk-mic-failure-code"[39m
        [36m>[39m
          [0mTRANSCRIPTION FAILED[0m
        [36m</b>[39m
        [0m [0m
        [0mTranscription did not finish. Your draft remains editable. Retry or type below.[0m
      [36m</span>[39m
    [36m</div>[39m
  [36m</body>[39m
[36m</html>[39m...
 ❯ Proxy.waitForWrapper node_modules/@testing-library/dom/dist/wait-for.js:163:27
 ❯ src/desk/components/MicButton.test.tsx:399:11
    397|     await speakAndStop();
    398|
    399|     await waitFor(() =>
       |           ^
    400|       expect(screen.getByText(/Retry the capture/)).toBeVisible(),
    401|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/5]⎯

 FAIL  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger
TestingLibraryElementError: Found multiple elements with the role "status"

Here are the matching elements:

Ignored nodes: comments, script, style
[36m<p[39m
  [33mclass[39m=[32m"contextual-assignment-error"[39m
  [33mrole[39m=[32m"status"[39m
[36m>[39m
  [0mAssignment unavailable[0m
[36m</p>[39m

Ignored nodes: comments, script, style
[36m<p[39m
  [33mclass[39m=[32m"contextual-assignment-error"[39m
  [33mrole[39m=[32m"status"[39m
[36m>[39m
  [0mAssignment unavailable[0m
[36m</p>[39m

Ignored nodes: comments, script, style
[36m<p[39m
  [33mclass[39m=[32m"wb-automation-test"[39m
  [33mrole[39m=[32m"status"[39m
[36m>[39m
  [0mTEST ONLY · NO ITEMS ADDED · [0m
  [0m0[0m
  [0m MATCH[0m
  [0mES[0m
  [0m FROM [0m
  [0m1[0m
  [0m OBSERVED[0m
[36m</p>[39m

(If this is intentional, then use the `*AllBy*` variant of the query (like `queryAllByText`, `getAllByText`, or `findAllByText`)).

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33maria-label[39m=[32m"Review desk"[39m
      [33mclass[39m=[32m"desk-pullout desk-workbench-window desk-window desk-window-shell is-floating is-front"[39m
      [33mid[39m=[32m"workbench:wb1"[39m
      [33mrole[39m=[32m"region"[39m
      [33mstyle[39m=[32m"z-index: 42; opacity: 0.8563705815541459; transform: translateX(8.617765106751243px); top: 64px; left: 10px; width: 480px; right: auto; bottom: auto; height: 480px; max-height: none;"[39m
      [33mtabindex[39m=[32m"-1"[39m
    [36m>[39m
      [36m<header[39m
        [33mclass[39m=[32m"desk-pullout-head desk-window-handle has-wings"[39m
      [36m>[39m
        [36m<span[39m
          [33mclass[39m=[32m"desk-traffic"[39m
        [36m>[39m
          [36m<button[39m
            [33maria-label[39m=[32m"Close Review desk"[39m
            [33mclass[39m=[32m"desk-light desk-light-close"[39m
            [33mtype[39m=[32m"button"[39m
          [36m>[39m
            [36m<svg[39m
              [33maria-hidden[39m=[32m"true"[39m
              [33mfill[39m=[32m"none"[39m
              [33mstroke[39m=[32m"currentColor"[39m
              [33mstroke-linecap[39m=[32m"round"[39m
              [33mstroke-linejoin[39m=[32m"round"[39m
              [33mstroke-width[39m=[32m"1.3"[39m
              [33mviewBox[39m=[32m"0 0 14 14"[39m
            [36m>[39m
              [36m<path[39m
                [33md[39m=[32m"M3.6 3.6l6.8 6.8M10.4 3.6l-6.8 6.8"[39m
              [36m/>[39m
            [36m</svg>[39m
          [36m</button>[39m
          [36m<button[39m
            [33maria-label[39m=[32m"Minimize Review desk"[39m
            [33mclass[39m=[32m"desk-light desk-light-min"[39m
            [33mtype[39m=[32m"button"[39m
          [36m>[39m
            [36m<svg[3
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-30T00:01:09Z

- **Command:** `uv run python scripts/web_baseline_check.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1350df8cfbfb24cf9cafe827d85bc7f377de06a0

```text
Running vitest (output -> /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpaxupy3uv.json) ...

--- baseline check ---
Baseline entries:   5
Actual failures:    5
Matched (known):    5
New reds:           0
Fixed:              0

OK — no new regressions.
```

## Orchestrator triage (2026-08-30)

Read: the web baseline check — 5 actual failures, all 5 matched to
`tests/fixtures/web-inherited-baseline.txt`, zero new reds (the desk
suite is 1143 passed / 5 inherited). The pullout's own tests: 19
`threads.test.ts` (delta by seq, dedup, out-of-order drop, the crash
rule with epoch timestamps, reconcile on reconnect, mount-then-hydrate)
+ 7 `ThreadPullout.test.tsx`. Glass truth (story-08 rig, failures=0):
the crash `Cannot read properties of undefined (reading 'token_in')`
on `?open=thread:<id>` and three client/server contract mismatches
(flat GET shape, siblings as [position,total], epoch seconds, inline
parts) were found ONLY on real Chromium and fixed in-round; the
composer overflow and the zero-parts CRASHED row likewise. The
`window.prompt` fork placeholder was replaced by 06's inline editor
(Art. VII). Shots: assets/story-08-shots/ (both widths).


> Merge note (2026-08-30): the phase was RENUMBERED 150 → 151 (the sibling
> session shipped Phase 150 — Delegation + Monday — first) and this phase's
> web-baseline rider (`scripts/web_baseline_check.py`,
> `tests/fixtures/web-inherited-baseline.txt`) was folded into main's
> `scripts/check_web_baseline.py` + `tests/web-inherited-baseline.txt`. The
> captured output above predates both renames.
