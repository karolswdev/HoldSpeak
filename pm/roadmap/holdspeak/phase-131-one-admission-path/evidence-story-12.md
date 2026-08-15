# Evidence - HS-131-12

- **Story:** HS-131-12 - The walk
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T17:00:45Z

- **Command:** `npm --prefix web run test:web`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

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

 Test Files  116 passed (116)
      Tests  811 passed (811)
   Start at  11:00:46
   Duration  32.32s (transform 3.55s, setup 3.55s, import 16.50s, tests 11.75s, environment 23.59s)
```

### Captured run — 2026-08-15T17:02:39Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-e2e-evidence-home XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-e2e-evidence-home/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-e2e-evidence-home/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-e2e-evidence-home/tmp PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_live_bus.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

```text
...                                                                      [100%]
3 passed in 28.37s
```

### Captured run — 2026-08-15T17:03:31Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-focused-evidence-home XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-focused-evidence-home/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-focused-evidence-home/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-focused-evidence-home/tmp uv run pytest -q tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay tests/integration/test_primitive_framework_sync.py::test_ipad_synced_graph_workflow_runs_on_the_hub tests/integration/test_web_companion_slack.py::test_source_identity_must_be_a_known_qualified_kind tests/unit/test_primitive_contract.py::TestHubEmissionsValidate::test_pull_body_validates_against_changeset_envelope tests/unit/test_primitive_contract.py::TestKindSetCannotDrift::test_schemas_cover_exactly_sync_kinds tests/unit/test_primitive_contract.py::TestKindSetCannotDrift::test_python_web_sync_contract_is_complete tests/unit/test_web_routes_sync.py::test_pull_serializes_meetings_and_artifacts tests/unit/test_web_routes_sync.py::test_push_live_merges_meeting_and_keeps_audit_inbox`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

```text
........                                                                 [100%]
8 passed in 6.54s
```

### Captured run — 2026-08-15T17:04:05Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-walk-evidence-home XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-walk-evidence-home/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-walk-evidence-home/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-walk-evidence-home/tmp HS_WALK_LAN=http://192.168.1.43:8080/v1 uv run python scripts/walk_one_admission_path.py --work-dir /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-walk-evidence-work --summary-json /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs13112-walk-evidence-summary.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

```text
LIVE endpoint ready: http://192.168.1.43:8080/v1; model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf; model_count=1
  PASS  runner: runner revision/cancellation; rc=0; duration_ms=6149; operations=7; receipts=7; stdout_bytes=160; stderr_bytes=0; output=sha256:29a47d980b5f5aafb3e01dad35bd4e0b2f5480b6dd398347e836f7222cf371ea
  PASS  ask-agent: Ask and saved Agent; rc=0; duration_ms=4433; operations=6; receipts=6; stdout_bytes=890; stderr_bytes=0; output=sha256:eb03c36666898c00a1de9b314dfcd39e385a50cde71dd46c350d7925276ba0fc
  PASS  sequence-workflow: Sequence and Workflow; rc=0; duration_ms=5541; operations=14; receipts=14; stdout_bytes=552; stderr_bytes=0; output=sha256:10687c5aba8eb6576c1b6afeae4dfc0dfb1d7133a8528bb8df37aa914b795e29
  PASS  workbench: Workbench item and memory; rc=0; duration_ms=9199; operations=16; receipts=16; stdout_bytes=635; stderr_bytes=0; output=sha256:dea0ccf0ad2bbe48620b570aec6de5b8f4f85baf3bf2cb0ba665aad236c51f21
  PASS  schedule: bounded scheduled Workbench; rc=0; duration_ms=8669; operations=16; receipts=16; stdout_bytes=1001; stderr_bytes=0; output=sha256:5ab30e93e9b4d8b3d5efa42288785d3c42120712ea9196e208f25200740a4d3b
  PASS  services: finite service callers; rc=0; duration_ms=5859; operations=15; receipts=15; stdout_bytes=861; stderr_bytes=135; output=sha256:42151e2ae9bff430be6a3873eff70d31af3724551756cca029c1702af6a26e1a
  PASS  meeting: meeting session and deferred intelligence; rc=0; duration_ms=12798; operations=13; receipts=13; stdout_bytes=784; stderr_bytes=68; output=sha256:748697fc7344269f231387d96cb48a80cedf9e9fb9b345a9e8552d56118ab5c6
  PASS  dictation: dictation sessions; rc=0; duration_ms=4914; operations=6; receipts=5; stdout_bytes=754; stderr_bytes=0; output=sha256:a72b004f293b99abe6d49a6916a87bea828035e91bc661dfb0ee39c912efb506
  PASS  controlled-contracts: fallback, indeterminate, sessions, hygiene, sync, restart; rc=0; duration_ms=4819; operations=0; receipts=0; stdout_bytes=99; stderr_bytes=0; output=sha256:d699d4b5909f4f1d8d4227968f21442919b063722f67423d9eb277858c178e67
  PASS  one-path-fence: literal spine, context, cardinality, provenance, mutation fence; rc=0; duration_ms=65736; operations=0; receipts=0; stdout_bytes=191; stderr_bytes=0; output=sha256:94db0e848cf073ac450cf269b03644f04d83c301ce9fac02996b2399eb8505fb
SUMMARY: 10 passed, 0 failed
```

### Captured run — 2026-08-15T17:13:22Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h4 XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h4/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h4/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/t4 uv run pytest -q tests/unit/test_inference_kernel.py::test_tool_effect_is_causally_linked_child_with_own_receipt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

```text
.                                                                        [100%]
1 passed in 1.30s
```

### Captured run — 2026-08-15T17:20:36Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h5 XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h5/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h5/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/t5 HS_WALK_LAN=http://192.168.1.43:8080/v1 uv run python scripts/walk_one_admission_path.py --work-dir /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/w5 --summary-json /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/w5-summary.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

```text
LIVE endpoint ready: http://192.168.1.43:8080/v1; model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf; model_count=1
  PASS  runner: runner revision/cancellation; rc=0; duration_ms=3924; operations=7; receipts=7; stdout_bytes=160; stderr_bytes=0; output=sha256:29a47d980b5f5aafb3e01dad35bd4e0b2f5480b6dd398347e836f7222cf371ea
  PASS  ask-agent: Ask and saved Agent; rc=0; duration_ms=4098; operations=6; receipts=6; stdout_bytes=890; stderr_bytes=0; output=sha256:c4cf3363a838f10e916b0ad801c3629681f2a97e8e2846e80adb0ee0df1ca5b3
  PASS  sequence-workflow: Sequence and Workflow; rc=0; duration_ms=5517; operations=14; receipts=14; stdout_bytes=552; stderr_bytes=0; output=sha256:0a21b8345f8906e0ec049982661057699e829f3bac95dee66a43a88c568bae81
  PASS  workbench: Workbench item and memory; rc=0; duration_ms=9634; operations=16; receipts=16; stdout_bytes=635; stderr_bytes=0; output=sha256:4eed5ebf9723b3bd6a3579b4cbfc927a1b1f596aac10ad8201a0e01f4a3731a9
  PASS  schedule: bounded scheduled Workbench; rc=0; duration_ms=8054; operations=16; receipts=16; stdout_bytes=1001; stderr_bytes=0; output=sha256:a97d5ca35b7e41a346f79fbded7edb4a49be85f4f93312b2575323d76f9d533a
  PASS  services: finite service callers; rc=0; duration_ms=5007; operations=15; receipts=15; stdout_bytes=861; stderr_bytes=135; output=sha256:df4a50d580519e63055bbafccd96ac726b14a355090965e01a3c8745cad9ff20
  PASS  meeting: meeting session and deferred intelligence; rc=0; duration_ms=10779; operations=13; receipts=13; stdout_bytes=784; stderr_bytes=68; output=sha256:578572c25e68a3412a098972cb4af66805eb4b9e8673afff22b1c469ca9add5e
  PASS  dictation: dictation sessions; rc=0; duration_ms=3751; operations=6; receipts=5; stdout_bytes=754; stderr_bytes=0; output=sha256:ebee6e3b4762e03eb14893b9f4dda76c74e969b61899409a2e256c30011611f0
  PASS  controlled-contracts: fallback, indeterminate, sessions, hygiene, sync, restart; rc=0; duration_ms=2826; operations=0; receipts=0; stdout_bytes=99; stderr_bytes=0; output=sha256:3e7f4557bfbdc599b3edbed2e2d7f12f6db7fdb56eaec880249ae99a5ed18128
  PASS  one-path-fence: literal spine, context, cardinality, provenance, mutation fence; rc=0; duration_ms=68091; operations=0; receipts=0; stdout_bytes=191; stderr_bytes=0; output=sha256:aaa7e30a4b10f05798f4b1b2d24aa8381691b182cf67814c26ed709179967b9b
SUMMARY: 10 passed, 0 failed
```

### Captured run — 2026-08-15T17:12:28Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h3 XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h3/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h3/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/t3 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q --tb=no --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** unknown

```text
ssssssssssssssssssssss...ssssssssss................EEEEEEEEEEEEEEss....F [  1%]
.....FF......................................F...FF..................... [  2%]
..................................s...............sss..FFFF........FFF.. [  3%]
FFF.F.FF...........................F.................................... [  5%]
...................ssFss................................................ [  6%]
........................................................................ [  7%]
.FF........F..F.FF.F..F.....F.F......................................... [  8%]
.FFFFFF.FF.............F......FF......FF................................ [ 10%]
.....F................F....................FFF.FF....................... [ 11%]
..............................................F......................... [ 12%]
..F..............................F...FFFFFF.F..F.........FF.F........... [ 13%]
........................................................................ [ 15%]
...........................FF..........F................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 62%]
.................................F...................................... [ 63%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 78%]
............................................................FE.......... [ 79%]
...................................................................F.... [ 81%]
.......................................................FFFEEEE.......... [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 97%]
.........................................F..................FEEEEEEEEEEE [ 98%]
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/cacheprovider.py:475
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/cacheprovider.py:475: PytestCacheWarning: cache could not write path /Users/karol/dev/tools/HoldSpeak/.pytest_cache/v/cache/nodeids: [Errno 28] No space left on device: '/Users/karol/dev/tools/HoldSpeak/.pytest_cache/v/cache/nodeids'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

.venv/lib/python3.13/site-packages/_pytest/cacheprovider.py:429
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/cacheprovider.py:429: PytestCacheWarning: cache could not write path /Users/karol/dev/tools/HoldSpeak/.pytest_cache/v/cache/lastfailed: [Errno 28] No space left on device: '/Users/karol/dev/tools/HoldSpeak/.pytest_cache/v/cache/lastfailed'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_workbench_walk.py:122: requires the production app fixture and deployment-adapter fake
SKIPPED [1] tests/e2e/test_workbench_walk.py:131: requires the production app fixture and deployment-adapter fake
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h3/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h3/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h3/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_desk_with_workbench_objects[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_desk_with_workbench_objects[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbenches_home[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbenches_home[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_template_picker[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_template_picker[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbench_window_configured[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbench_window_configured[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_config_panel_expanded[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_config_panel_expanded[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_constitutional_context_editor[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_constitutional_context_editor[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_composer_with_body[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_composer_with_body[mobile]
ERROR tests/unit/test_plugin_queue.py::test_process_next_plugin_run_job_terminal_failure_marks_failed
ERROR tests/unit/test_recipe_runner_migration.py::test_recipe_run_and_root_chat_use_exact_saved_revision_and_stages
ERROR tests/unit/test_recipe_runner_migration.py::test_recipe_profile_revision_is_committed_before_runner_claim
ERROR tests/unit/test_recipe_runner_migration.py::test_recipe_service_ast_fence_and_forged_materializer_permit
ERROR tests/unit/test_release_gate_script.py::test_release_gate_passes_when_all_items_checked
ERROR tests/unit/test_workbench_runner_migration.py::test_manual_attempt_creates_one_authenticated_workbench_parent
ERROR tests/unit/test_workbench_runner_migration.py::test_replay_returns_the_original_terminal_attempt_and_receipt
ERROR tests/unit/test_workbench_runner_migration.py::test_each_item_provider_call_has_one_admitted_child_and_receipt
ERROR tests/unit/test_workbench_runner_migration.py::test_memory_writeback_is_a_distinct_child_linked_to_its_item_child
ERROR tests/unit/test_workbench_runner_migration.py::test_memory_disabled_admits_no_memory_child
ERROR tests/unit/test_workbench_runner_migration.py::test_item_and_memory_children_freeze_provenance_and_per_child_placement
ERROR tests/unit/test_workbench_runner_migration.py::test_item_memory_artifact_and_attempt_history_are_receipt_gated
ERROR tests/unit/test_workbench_runner_migration.py::test_cancel_before_item_checkpoint_leaves_no_item_or_memory_write
ERROR tests/unit/test_workbench_runner_migration.py::test_cancel_after_item_preserves_item_and_fences_memory_late_write
ERROR tests/unit/test_workbench_runner_migration.py::test_repeated_or_foreign_parent_cancel_cannot_cross_workbenches_or_mutate_receipts
ERROR tests/unit/test_workbench_runner_migration.py::test_manual_workbench_uses_only_trusted_runner_children
ERROR tests/unit/test_workbench_runner_migration.py::test_memory_service_contract_hashes_the_exact_submitted_payload
ERROR tests/unit/test_workbench_runner_migration.py::test_workbench_deadline_expiry_fences_new_children_and_late_projections
ERROR tests/unit/test_workbench_runner_migration.py::test_cross_request_cancel_adopts_parent_receipt_and_preserves_child_receipt
ERROR tests/unit/test_workbench_runner_migration.py::test_checkpoint_that_did_not_advance_never_stages_workbench_success_aggregate
ERROR tests/unit/test_workbench_runner_migration.py::test_cancel_after_parent_result_stage_never_finalizes_completed_history
ERROR tests/unit/test_workbench_runner_migration.py::test_cancellation_before_claim_does_not_strand_item_and_next_run_processes_it
ERROR tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_valid_accept
ERROR tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_valid_reject
ERROR tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_valid_rework
ERROR tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_invalid_action
ERROR tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_missing_fields
ERROR tests/unit/test_workbench_triage.py::TestTriageAcceptDB::test_accept_changes_artifact_to_draft
ERROR tests/unit/test_workbench_triage.py::TestTriageAcceptDB::test_accepted_artifact_visible_in_run_list
ERROR tests/unit/test_workbench_triage.py::TestTriageRejectDB::test_reject_archives_artifact_and_dismisses_item
ERROR tests/unit/test_workbench_triage.py::TestTriageRejectDB::test_rejected_artifact_hidden_from_run_list
ERROR tests/unit/test_workbench_triage.py::TestTriageRejectDB::test_rejected_artifact_still_in_db
ERROR tests/unit/test_workbench_triage.py::TestTriageReworkDB::test_rework_resets_item_to_pending
ERROR tests/unit/test_workbench_triage.py::TestTriageReworkDB::test_rework_cycle_allows_new_triage
ERROR tests/unit/test_workbench_triage.py::TestDoubleTriage::test_double_accept_fails
ERROR tests/unit/test_workbench_triage.py::TestTriageWithoutArtifact::test_no_artifact_id
ERROR tests/unit/test_workbench_triage_kernel.py::test_workbench_triage_codec_registered
ERROR tests/unit/test_workbench_triage_kernel.py::test_triage_parse_accept - ...
ERROR tests/unit/test_workbench_triage_kernel.py::test_triage_parse_reject - ...
ERROR tests/unit/test_workbench_triage_kernel.py::test_triage_parse_rework - ...
ERROR tests/unit/test_workbench_triage_kernel.py::test_triage_parse_rejects_invalid_action
ERROR tests/unit/test_workbench_triage_kernel.py::test_triage_parse_rejects_missing_fields
ERROR tests/unit/test_workflow_graph.py::test_parse_graph_decodes_tagged_union_kinds
ERROR tests/unit/test_workflow_graph.py::test_parse_graph_rejects_non_graphs_and_dupes
ERROR tests/unit/test_workflow_graph.py::test_linearize_orders_a_single_chain
ERROR tests/unit/test_workflow_graph.py::test_linearize_chain_without_declared_entry
ERROR tests/unit/test_workflow_graph.py::test_linearize_refuses_branch - OSEr...
ERROR tests/unit/test_workflow_graph.py::test_linearize_refuses_for_each_and_while_and_sequence
ERROR tests/unit/test_workflow_graph.py::test_linearize_refuses_fan_out_even_with_linear_kinds
ERROR tests/unit/test_workflow_graph.py::test_linearize_refuses_fan_in_join
ERROR tests/unit/test_workflow_graph.py::test_linearize_refuses_dangling_edge_and_disconnected
ERROR tests/unit/test_workflow_graph.py::test_linearize_refuses_unknown_kind
ERROR tests/unit/test_workflow_graph.py::test_build_node_prompt_matches_swift_templates
ERROR tests/unit/test_workflow_graph.py::test_apply_pure_transform - OSError:...
ERROR tests/unit/test_workflow_graph.py::test_parse_graph_carries_failure_policy_and_runs_on
ERROR tests/unit/test_workflow_graph.py::test_parse_graph_preserves_the_desktop_pin
ERROR tests/unit/test_workflow_graph.py::test_parse_graph_unset_or_unknown_provenance_is_byte_identical_default
ERROR tests/unit/test_workflow_graph.py::test_resolved_failure_policy_falls_back_to_run_default
ERROR tests/unit/test_workflow_graph.py::test_on_node_error_honors_skip_and_fallback_but_surfaces_retry
ERROR tests/unit/test_workflow_graph.py::test_linearize_preserves_provenance_through_ordering
ERROR tests/unit/test_workroom_context.py::test_workroom_context_round_trips_only_identity_and_orientation
ERROR tests/unit/test_workroom_context.py::test_workroom_context_is_forward_tolerant_but_refuses_content
ERROR tests/unit/test_workroom_context.py::test_workroom_context_has_no_open_return_destination[https://example.com]
ERROR tests/unit/test_workroom_context.py::test_workroom_context_has_no_open_return_destination[/settings]
ERROR tests/unit/test_workroom_context.py::test_workroom_context_has_no_open_return_destination[]
ERROR tests/unit/test_workroom_context.py::test_integration_is_a_qualified_desk_subject
ERROR tests/unit/test_write_through_verbs.py::test_done_marks_action_loop_and_commitment_terminal
ERROR tests/unit/test_write_through_verbs.py::test_dismiss_marks_action_loop_and_commitment_terminal
ERROR tests/unit/test_write_through_verbs.py::test_snooze_preserves_action_and_snoozes_its_loop
ERROR tests/unit/test_write_through_verbs.py::test_delegate_updates_action_and_commitment_owner
ERROR tests/unit/test_write_through_verbs.py::test_reopen_after_done_restores_all_linked_records
ERROR tests/unit/test_write_through_verbs.py::test_board_reflects_verb_immediately
ERROR tests/unit/test_write_through_verbs.py::test_action_only_card_can_complete
FAILED tests/integration/test_actuator_presence_broadcasts.py::test_qlippy_events_mirror_the_dashboard_decision_exactly
FAILED tests/integration/test_cadence_agent.py::test_reply_delivers_into_pane_and_closes
FAILED tests/integration/test_cadence_agent.py::test_reply_rejects_empty_and_non_agent_and_missing_pane
FAILED tests/integration/test_decision_records.py::test_v32_migration_adds_decision_moment_columns
FAILED tests/integration/test_decision_records.py::test_model_promotion_admits_before_generation_and_leaves_receipt
FAILED tests/integration/test_decision_records.py::test_superseded_promotion_route_names_successor_without_model_call
FAILED tests/integration/test_history_slack_surfaces.py::test_history_buttons_are_gated_on_the_flag
FAILED tests/integration/test_history_slack_surfaces.py::test_proposal_rows_render_the_central_policy_and_refusal_truth
F
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-15T17:46:25Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h6 XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h6/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h6/.local/share TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/t6 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q --tb=no --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 63afda36c017a232efc42f39a9d6065fc25e42a0

```text
ssssssssssssssssssssssEEEssssssssss................EEEEEEEEEEEEEEss....F [  1%]
.....FF......................................F...FF..................... [  2%]
..................................s...............sss..FFFF........FFF.. [  3%]
FFF.F.FF...........................F.................................... [  5%]
...................ssFss................................................ [  6%]
........................................................................ [  7%]
.FF........F..F.FF.F..F.....F.F......................................... [  8%]
.FFFFFF.FF.............F......FF......FF................................ [ 10%]
.....F................F....................FFF.FF....................... [ 11%]
..............................................F......................... [ 12%]
..F..............................F...FFFFFF.F..F.........FF.F........... [ 13%]
........................................................................ [ 15%]
...........................FF..........F................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 62%]
.................................F...................................... [ 63%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 78%]
........................................................................ [ 79%]
...................................................................F.... [ 81%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 97%]
.........................................F.............................. [ 98%]
.........................................................                [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_workbench_walk.py:122: requires the production app fixture and deployment-adapter fake
SKIPPED [1] tests/e2e/test_workbench_walk.py:131: requires the production app fixture and deployment-adapter fake
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h6/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h6/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/h6/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
ERROR tests/e2e/test_live_bus.py::test_every_live_page_opens_exactly_one_runtime_socket
ERROR tests/e2e/test_live_bus.py::test_a_real_broadcast_reaches_the_presence_card_via_the_bus
ERROR tests/e2e/test_live_bus.py::test_the_bus_reconnects_after_a_server_restart
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_desk_with_workbench_objects[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_desk_with_workbench_objects[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbenches_home[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbenches_home[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_template_picker[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_template_picker[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbench_window_configured[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_workbench_window_configured[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_config_panel_expanded[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_config_panel_expanded[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_constitutional_context_editor[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_constitutional_context_editor[mobile]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_composer_with_body[desktop]
ERROR tests/e2e/test_workbench_walk.py::TestWorkbenchWalk::test_composer_with_body[mobile]
FAILED tests/integration/test_actuator_presence_broadcasts.py::test_qlippy_events_mirror_the_dashboard_decision_exactly
FAILED tests/integration/test_cadence_agent.py::test_reply_delivers_into_pane_and_closes
FAILED tests/integration/test_cadence_agent.py::test_reply_rejects_empty_and_non_agent_and_missing_pane
FAILED tests/integration/test_decision_records.py::test_v32_migration_adds_decision_moment_columns
FAILED tests/integration/test_decision_records.py::test_model_promotion_admits_before_generation_and_leaves_receipt
FAILED tests/integration/test_decision_records.py::test_superseded_promotion_route_names_successor_without_model_call
FAILED tests/integration/test_history_slack_surfaces.py::test_history_buttons_are_gated_on_the_flag
FAILED tests/integration/test_history_slack_surfaces.py::test_proposal_rows_render_the_central_policy_and_refusal_truth
FAILED tests/integration/test_history_slack_surfaces.py::test_history_app_wires_the_export_route
FAILED tests/integration/test_history_slack_surfaces.py::test_settings_field_ships_the_honest_copy
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_done
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_pending
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_dismissed
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_without_handler_returns_501
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_callback_error_returns_500
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_review_accepts
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_edit_auto_accepts
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_review_without_handler_returns_501
FAILED tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint::test_patch_action_item_edit_without_handler_returns_501
FAILED tests/integration/test_meeting_conflict_recovery.py::test_keep_current_resolves_without_changing_the_meeting
FAILED tests/integration/test_rails_observer_live.py::test_remote_flip_reaches_the_journal_node_named
FAILED tests/integration/test_web_companion_github.py::test_yolo_files_to_the_registered_repo_without_a_decision
FAILED tests/integration/test_web_companion_github.py::test_yolo_refuses_an_unregistered_repo_without_filing_or_prompting
FAILED tests/integration/test_web_companion_slack.py::test_source_identity_returns_the_receipt_to_the_desk_subject
FAILED tests/integration/test_web_companion_slack.py::test_a_proposed_send_never_posts
FAILED tests/integration/test_web_companion_slack.py::test_approval_posts_the_preview_byte_equal
FAILED tests/integration/test_web_companion_slack.py::test_yolo_executes_configured_slack_without_a_prompt_and_returns_receipt
FAILED tests/integration/test_web_companion_slack.py::test_url_removed_between_propose_and_approve_fails_honestly
FAILED tests/integration/test_web_companion_slack.py::test_the_wire_events_ride_for_qlippy
FAILED tests/integration/test_web_companion_webhook.py::test_yolo_executes_the_configured_webhook_without_a_decision
FAILED tests/integration/test_web_companion_webhook.py::test_url_removed_between_propose_and_approve_fails_honestly
FAILED tests/integration/test_web_dictation_cockpit.py::test_dictation_is_one_typed_section_graph
FAILED tests/integration/test_web_dictation_cockpit.py::test_dictation_preserves_primary_api_verbs
FAILED tests/integration/test_web_dictation_cockpit.py::test_dictation_keeps_device_local_project_scope
FAILED tests/integration/test_web_dictation_cockpit.py::test_dictation_lists_are_react_owned_and_focus_safe
FAILED tests/integration/test_web_dictation_correction_ritual.py::test_ritual_component_is_shipped
FAILED tests/integration/test_web_dictation_correction_ritual.py::test_ritual_is_wired_into_dry_run_result
FAILED tests/integration/test_web_dictation_correction_ritual.py::test_ritual_uses_shared_react_controls
FAILED tests/integration/test_web_dictation_correction_ritual.py::test_dry_run_moment_host_present
FAILED tests/integration/test_web_dictation_corrections_api.py::test_dictation_page_includes_memory_tab
FAILED tests/integration/test_web_dictation_journal.py::test_dictation_page_includes_journal_tab
FAILED tests/integration/test_web_dictation_journal.py::test_dictation_journal_premium_and_a11y_markers
FAILED tests/integration/test_web_dictation_learning_digest.py::test_dictation_page_includes_learning_digest
FAILED tests/integration/test_web_dictation_learning_digest.py::test_learning_digest_styles_are_global
FAILED tests/integration/test_web_dictation_settings_api.py::test_dictation_page_includes_runtime_section
FAILED tests/integration/test_web_dictation_trust_signals.py::test_trust_chip_css_is_global
FAILED tests/integration/test_web_history_archive.py::test_history_uses_bounded_archive_and_detail_sections
FAILED tests/integration/test_web_history_archive.py::test_history_keeps_approval_and_export_governance
FAILED tests/integration/test_web_history_import_ui.py::test_history_has_audio_and_transcript_import
FAILED tests/integration/test_web_history_import_ui.py::test_history_search_uses_backend_search_contract
FAILED tests/integration/test_web_history_import_ui.py::test_failed_import_and_queue_states_stay_visible
FAILED tests/integration/test_web_project_kb_api.py::test_dictation_page_includes_project_kb_section
FAILED tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_bootstrap_prefers_runtime_status_payload
FAILED tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_meeting_stop_prefers_on_meeting_stop_callback
FAILED tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_intent_timeline_endpoint
FAILED tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_plugin_runs_endpoint
FAILED tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_artifacts_endpoint
FAILED tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_export_endpoint_renders_handoff_formats
FAILED tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_legacy_meeting_without_mir_history_rows_remains_loadable
FAILED tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_cli_reroute_persistence_is_visible_in_timeline_api
FAILED tests/integration/test_web_server.py::TestMeetingMetadataEndpoints::test_meeting_patch_falls_back_to_title_and_tags_callbacks
FAILED tests/integration/test_web_server.py::TestHistoryUiSmoke::test_history_page_contains_control_plane_tabs_and_handlers
FAILED tests/integration/test_web_server.py::TestSpeakerApiEndpoints::test_speaker_endpoints
FAILED tests/integration/test_web_server.py::TestGlobalActionItemsApiEndpoints::test_action_item_endpoints_include_review_and_edit
FAILED tests/integration/test_web_server.py::TestIntelQueueApiEndpoints::test_intel_jobs_list_retry_and_process
FAILED tests/uat/test_induction_integration_43.py::test_meeting_recipe_yields_a_real_open_action
FAILED tests/uat/test_induction_integration_43.py::test_mesh_node_lifecycle
FAILED tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged
FAILED tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css
FAILED tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift
FAILED tests/unit/test_web_vocabulary_guard.py::test_web_copy_has_no_dash_in_prose
71 failed, 5543 passed, 44 skipped, 17 errors in 1468.06s (0:24:28)
```
