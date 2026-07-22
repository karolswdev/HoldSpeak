# Evidence - HS-102-03

- **Story:** HS-102-03 - Ask AI — the composer refit
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Captured run — 2026-07-22T20:57:23Z

- **Command:** `sh -c cd web && npx vitest run --no-color && npx tsc --noEmit -p . && npm run tokens:gate --silent && cd .. && uv run pytest -q tests/unit/test_interior_canon_guard.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 623b192bf759c366c742b1c77c5558796b8eb8a7

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
   Start at  14:57:23
   Duration  6.76s (transform 3.64s, setup 4.97s, import 14.06s, tests 12.11s, environment 32.13s)

token gate: clean (61 allow-listed exceptions, all in use)
..........                                                               [100%]
10 passed in 0.13s
```

## The hands-first ledger (headed, staged instance, BEFORE code)

`AskPanel.tsx` mounted `MicButton` and the question `<textarea>` as
one block, then `RunsOnPicker` / `GroundingSection` / `RailsPicker`
each as their own separate mounted blocks below it, and a floating
"Ask" button lived in the footer — a stack of sections around a
question box, not one well. The printed answer rendered as
`<pre className="desk-pullout-md">{result.output}</pre>` — raw
markdown source in a box (round 7's naming, confirmed still present).

## The fix

- The composer is now ONE well (`.desk-chat-well` /
  `.desk-chat-composer`): `MicButton` + question `<textarea>` + the
  `Ask` verb inline, side by side — the SAME class family
  `PersonaChat.tsx` and `Pullout.tsx`'s capability-card composer
  already use (round 2/8's convergence), not a fourth variant.
- `RunsOnPicker`, `GroundingSection`, and `RailsPicker` moved into
  `.desk-chat-well-foot`. `GroundingSection`/`RailsPicker` already
  render as a single collapsed caption row (`.desk-ground-head`) with
  their list folding open on click — a new scoped CSS rule
  (`.desk-chat-well-foot .desk-ground`) strips their bordered-card
  chrome so they read as captions in the foot, without touching how
  they render elsewhere (PersonaChat's own composer, where the
  bordered look is still correct).
- The footer's separate "Ask" button is gone (it now lives in the
  well); compose-phase footer is just "Cancel".
- `desk-pullout-md` is gone; the printed answer renders through
  `Material` (`desk/surface/Material.tsx` — the same renderer HS-101
  round 8 built for Blocks/Journal, not a second implementation). The
  run receipt stays a quiet caption line below it; "Keep"/"Bin" stay
  the footer's two verbs, unchanged.
- The ask wire (`/api/ask`, `buildGrounding`) is untouched.

## Driven live, after (headed, staged instance, both viewports)

A real note (`Q3 planning`) was created via `/api/notes` and selected
on the desk to reach Ask AI through the real selection-bar → panel
handoff (one gesture, unchanged).

- `assets/hs-102-03-after-composer-empty.png` (1440) — one bordered
  well (mic/textarea/Ask), the caption line "This device · sends
  Instruction, Selected context, Grounding," and the collapsed
  "Ground this ask" row beneath it.
- `assets/hs-102-03-after-grounding-open.png` — the grounding
  disclosure opened in place: "Desk objects and collections" lists
  the selected note, pickable, still reading as part of the well's
  foot rather than a separate section.
- `assets/hs-102-03-after-failure-state.png` / `-mobile-failure.png`
  (1440 + 393) — asking with no model configured on this staged
  instance refuses HONESTLY, by name, inline in the well: "⚠ No
  language model on this hub. Pick one in Settings under
  Intelligence." Nothing prints silently.
- `assets/hs-102-03-after-mobile-393.png` — the same composer at
  393px: single column, well-foot wraps cleanly, no overflow.

### Correction (2026-07-22, same day): the real grounded answer, proven live

The first pass of this evidence file wrongly claimed the LAN model at
`192.168.1.43:8080` was unreachable from this sandbox and deferred the
answered-state proof to HS-102-07. That was wrong — the owner caught
it; `curl http://192.168.1.43:8080/v1/models` answers directly from
this shell. Re-run with the real model, through the real wire, no
shortcuts:

- Registered `.43` as a real `Runs on` destination via
  `POST /api/profiles` (`kind: openAICompatible`,
  `base_url: http://192.168.1.43:8080`,
  `model: Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf`) — the exact wire
  HS-102-01 shipped, byte-identical, no shortcut route.
- `assets/hs-102-03-after-destination-picked.png` — the well-foot's
  `RunsOnPicker` set to the LAN destination, inline in the same
  composer.
- `assets/hs-102-03-after-real-answer.png` — asked "In one sentence,
  what is the biggest risk mentioned?" against a real note ("Q3
  planning," body naming mesh-worker deadlocking as the risk). The
  model answered correctly and the printed card is `Material` —
  clean prose, no markdown box — with the receipt as a quiet caption
  ("Ran on LAN llama.cpp (.43) · cloud · Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf
  · private_network") and the egress badge honestly reading
  "→ Leaves device · 192.168.1.43 · Qwythos-9B-Clau…".
- `assets/hs-102-03-after-keep-materialized.png` — "Keep" minted a
  real artifact ("Summarize") on the desk wearing the NEW beat, same
  as every other run-born output.

The acceptance criterion ("select an object → Ask → grounded answer →
keep → the artifact materializes") is now fully proven live, not
deferred. HS-102-07's added bullet about this gap is stale and is
removed in the same commit as this correction.

## Guard added

`tests/unit/test_interior_canon_guard.py::
test_ask_panel_never_regresses_to_a_pre_box_or_section_stack` —
refuses `desk-pullout-md` anywhere in `AskPanel.tsx` and requires
`desk-chat-well` to be present (pins the one-well composition).
