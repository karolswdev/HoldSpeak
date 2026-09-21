# Evidence - HS-202-04

- **Story:** HS-202-04 - Names and repeats on the touched flows
- **Status:** done
- **Date:** 2026-09-21

## Proof

### Captured run — 2026-09-21T15:54:59Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/pages/cores/__tests__/summaryName202.test.tsx src/pages/cores/__tests__/settingsSummaryName202.test.tsx src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx src/desk/components/__tests__/zeroCounters202.test.tsx src/desk/pullouts/__tests__/sequenceVerb202.test.tsx src/features/project-room/__tests__/provenanceWords202.test.ts src/pages/cores/dictation/__tests__/readinessZero202.test.tsx --maxWorkers=2 2>&1 | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
    at Function.from (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-202-04/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-202-04/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-202-04/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-202-04/web/src/desk/gl/engine.ts:188:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/wt-202-04/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/wt-202-04/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/wt-202-04/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/wt-202-04/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/wt-202-04/web/src/desk/gl/engine.ts:188:7) undefined

 Test Files  7 passed (7)
      Tests  23 passed (23)
   Start at  09:54:59
   Duration  2.93s (transform 1.12s, setup 398ms, import 2.49s, tests 639ms, environment 1.49s)
```

### Captured run — 2026-09-21T15:55:13Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/pages src/desk src/features src/lib --maxWorkers=2 2>&1 | grep -E "Test Files|Tests |FAIL" | tail -10`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
 Test Files  285 passed (285)
      Tests  2691 passed (2691)
```

### Captured run — 2026-09-21T15:56:46Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) npm_config_cache=$HOME_REAL/.npm uv run python scripts/check_web_baseline.py --run 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2745 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T15:57:33Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_phase200_doc_claims.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_claim_support.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py tests/unit/test_interior_canon_guard.py tests/unit/test_doc_drift_guard.py 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
........................................................................ [ 40%]
........................................................................ [ 81%]
.................................                                        [100%]
177 passed in 11.24s
```

### Captured run — 2026-09-21T15:57:59Z

- **Command:** `bash -c set -o pipefail; python3 -c "
import json, sys
p = \"pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/walk-facts.json\"
d = json.load(open(p))
ok = True
for w in (\"1440\", \"393\"):
    live = d[\"live\"][w]
    print(w, \"live sections\", live[\"section_labels\"], \"door\", live[\"door_labels\"])
    print(w, \"live facts\", repr(live[\"facts_line\"]), \"receipt\", repr(live[\"footer_receipt\"]), \"SEG?\", live[\"body_has_SEG\"])
    ok &= \"SUMMARY\" in live[\"section_labels\"] and not live[\"body_has_SEG\"]
    me = d[\"meetings_empty\"][w]
    print(w, \"meetings headline\", repr(me[\"headline\"]), \"empty\", me[\"empty_lines\"], \"said-twice\", me[\"no_meetings_yet_count\"])
    ok &= me[\"no_meetings_yet_count\"] == 1 and me[\"empty_lines\"] == [\"○ Record or import a meeting\"]
    sh = d[\"settings_hub\"][w]
    print(w, \"settings chips\", sh[\"chips\"], \"INTELLIGENCE?\", sh[\"body_has_INTELLIGENCE\"], \"first row\", sh[\"meetings_module_rows\"][0])
    ok &= not sh[\"body_has_INTELLIGENCE\"] and sh[\"meetings_module_rows\"][0] == \"Summary\"
    print(w, \"ask head\", repr(d[\"ask\"][w][\"session_head\"]))
    ok &= d[\"ask\"][w][\"session_head\"] == \"SESSION\"
    sd = d[\"speak_door\"][w]
    print(w, \"speak runs row?\", sd[\"has_runs_row\"], \"RAW READINESS?\", sd[\"has_raw_readiness\"])
    ok &= not sd[\"has_runs_row\"] and sd[\"has_raw_readiness\"]
    sq = d[\"sequence\"][w]
    print(w, \"Edit Sequence?\", sq[\"has_edit_sequence\"], \"Edit chain?\", sq[\"has_edit_chain\"])
    ok &= sq[\"has_edit_sequence\"] and not sq[\"has_edit_chain\"]
    fz = d[\"floor_zone\"][w]
    print(w, \"zone names\", fz[\"zone_aria_names\"], \"zero names\", fz[\"zero_item_names\"], \"zero cells\", fz[\"zero_item_cells\"])
    ok &= fz[\"zero_item_names\"] == [] and fz[\"zero_item_cells\"] == []
print(\"page_errors\", d.get(\"page_errors\"), \"console_errors\", d.get(\"console_errors\"), \"bad_responses\", d.get(\"bad_responses\"), \"step_errors\", d.get(\"step_errors\"))
ok &= not d.get(\"page_errors\") and not d.get(\"console_errors\") and not d.get(\"bad_responses\") and not d.get(\"step_errors\")
print(\"LIST FACE AT 393:\", d[\"list_view_opened\"][\"393\"], \"(the Desk menu is dead at 393 - a DOOR defect, not a label; recorded, not claimed)\")
print(\"VERDICT\", \"PASS\" if ok else \"FAIL\")
sys.exit(0 if ok else 1)
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
1440 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
1440 live facts 'connected · recording' receipt 'REC 00:00' SEG? False
1440 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
1440 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Summary
1440 ask head 'SESSION'
1440 speak runs row? False RAW READINESS? True
1440 Edit Sequence? True Edit chain? False
1440 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item'] zero names [] zero cells []
393 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
393 live facts 'connected · recording' receipt 'REC 00:00' SEG? False
393 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
393 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Summary
393 ask head 'SESSION'
393 speak runs row? False RAW READINESS? True
393 Edit Sequence? True Edit chain? False
393 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item'] zero names [] zero cells []
page_errors None console_errors None bad_responses None step_errors None
LIST FACE AT 393: False (the Desk menu is dead at 393 - a DOOR defect, not a label; recorded, not claimed)
VERDICT PASS
```

### Captured run — 2026-09-21T15:58:26Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/shoot.py 2>&1 | grep -E "shot |hub pid|!!|==" | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
  == 1440x900 ==
  hub pid=79566 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-04-1440-xbjbg7iy port=55085
    shot live-summary-1440.png
    shot live-door-summary-1440.png
    shot settings-hub-1440.png
    shot settings-meetings-1440.png
    shot ask-session-1440.png
    shot speak-door-1440.png
    shot sequence-pullout-1440.png
    shot floor-list-zone-1440.png
    shot meetings-empty-1440.png
  == 393x852 ==
  hub pid=81093 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-04-393-9jklxuex port=55238
    shot live-summary-393.png
    shot live-door-summary-393.png
    shot settings-hub-393.png
    shot settings-meetings-393.png
    shot ask-session-393.png
    shot speak-door-393.png
    shot sequence-pullout-393.png
    shot floor-list-zone-393.png
    shot meetings-empty-393.png
```

### Captured run — 2026-09-21T16:03:01Z

- **Command:** `bash -c set -o pipefail; cd web && npm run tokens:check 2>&1 | tail -2 && npm run guard:architecture 2>&1 | tail -2 && npx tsc --noEmit && echo "TYPECHECK CLEAN"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text

tokens.css and tokens.gen.ts match design-tokens.json

React architecture guard passed (815 source files; zero framework residue).
TYPECHECK CLEAN
```

### Captured run — 2026-09-21T16:03:40Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src --maxWorkers=2 2>&1 | grep -E "Test Files|Tests |FAIL" | tail -10`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
 Test Files  297 passed (297)
      Tests  2745 passed (2745)
```
