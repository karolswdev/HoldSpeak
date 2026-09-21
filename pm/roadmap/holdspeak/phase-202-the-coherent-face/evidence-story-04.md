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

## Counsel round

Astra's counsel on PR #599 returned **DO-NOT-RATIFY** with four conditions
and one integration finding. What each condition asked, and what closed it:

1. **"The touched Live flow is incomplete."** `live-door-summary-393.png`
   showed six counters of zero in the gear door's queue section, the
   Summary could still print `0 action items`, and the facts row repeated
   the footer receipt's state word (`ready` beside `READY`). All three are
   closed at `web/src/pages/cores/LiveCore.tsx`; a fourth defect the fix
   exposed — the idle wire's `next_retry_at: null` counted as a fact, so
   the section drew a header with a lone verb (M5) — is closed with it.
   The first round's fence could not have caught any of them: it rendered
   `LiveCore` with no `WingSlotContext`, so the gear door was unreachable.
   The fence now hosts the wing slot and presses the door.
2. **"Eighteen-row closure is not demonstrated."** The dated after-maps are
   `docs/internal/surface-inventory-2026-09-20/02-verbs-after-2026-09-21.csv`
   (20 rows, each with its rule, its before and after names, its site
   before and after, its anchor text, its fence and its shot) and
   `02-nouns-after-2026-09-21.csv` (the checked-collision table, with what
   is closed on the touched faces and what is ledgered and why).
   **"…and red-first capture"**: several rows carried only a green tail.
   `assets/story-04-shots/red-first.py` now makes the red reproducible —
   it writes the OLD text back one row at a time, requires that row's
   fence to FAIL, restores the file and verifies the bytes by SHA-256. A
   row whose fence stays green with the old text back is a harness
   failure, and that is exactly how the missing door-label fence was
   found (row 02 went green in the first run).
3. **"The existing Settings glass test still selects `Intelligence`."**
   Re-pointed at `tests/e2e/test_hs172_settings_meetings_glass.py:100`,
   selector only; the NO-MODEL assertions are unchanged and a new
   `count() >= 1` guard stops the rig from passing against a row it can no
   longer find.
4. **"Observe the list at 393 through the correct door."** The rig only
   knew the `desk` menu, which does not render at 393 — since HS-202-02
   the Desk/Object/Window entries are folded into `Go`
   (`web/src/desk/__tests__/phoneDoors.test.tsx:104`). The rig now walks
   the fold; the list face is OBSERVED at 393 and its zone cells read
   `EMPTY`.
5. **Integration finding: stale boundary-census records.** Confirmed: my
   edits moved three recorded line numbers (`AskPanel.tsx`,
   `productLanguage.ts`, `LiveCore.tsx` ×2). All seven Philo inventories
   regenerated together and every `--check` re-run.

Not closed, and recorded rather than claimed: the filled-primary pairs
(reported with `file:line` below and in the report; neither sibling lane
owns them yet) and the Sequence pullout's two raw footer controls
(`web/src/desk/pullouts/ChainPullout.tsx:63`, `:70`) — species work that
belongs to story 03's census, which this names lane must not certify.

### Captured run — 2026-09-21T18:59:42Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/red-first.py 2>&1 | tail -45`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
  RED 14 floor list zone cell (U3 text)
      fence: src/desk/components/__tests__/zeroCounters202.test.tsx
      × does not print 0 ITEMS in the zone row's own cell 28ms
      AssertionError: expected [ '0 ITEMS' ] to deeply equal []
  RED 15 spatial floor zone accessible name (U3 aria)
      fence: src/desk/components/__tests__/zeroCounters202.test.tsx
      × names an empty zone without a count 20ms
      AssertionError: expected [ 'Launch zone, 0 items' ] to include 'Launch zone'
  RED 16 ask session head (U3)
      fence: src/desk/components/__tests__/zeroCounters202.test.tsx
      × heads a fresh session with SESSION, not SESSION · 0 TURNS 15ms
      AssertionError: expected 'SESSION · 0 TURNS' to be 'SESSION' // Object.is equality
  RED 17 speak door Runs fact (U3)
      fence: src/pages/cores/dictation/__tests__/readinessZero202.test.tsx
      × withholds the row when the pipeline has never run 24ms
      AssertionError: expected [ …(4) ] to not include 'Runs'
  RED 18 speak door raw fold
      fence: src/pages/cores/dictation/__tests__/readinessZero202.test.tsx
      × keeps the readiness wire behind a fold that says it is raw 1008ms
      TestingLibraryElementError: Unable to find an element with the text: RAW · READINESS. This could be because the text is broken up by multiple elements. In this case, you can provide a function for you
  RED 19 registry: the Segment term
      fence: src/lib/productLanguage.test.ts
      × matches the versioned registry exactly 6ms
      AssertionError: expected { …(22) } to deeply equal { …(23) }
  RED 20 registry: the seg/mtg aliases
      fence: src/lib/productLanguage.test.ts
      × matches the versioned registry exactly 5ms
      AssertionError: expected { agent: 'persona', …(10) } to deeply equal { agent: 'persona', …(12) }

  -- restore check --
  ok  web/src/pages/cores/LiveCore.tsx  abd61da4c0e2
  ok  web/src/pages/cores/history/DoorSection.tsx  f649b49108c6
  ok  web/src/pages/cores/history/CatalogRail.tsx  6cd52b9f35d1
  ok  web/src/desk/pullouts/ChainPullout.tsx  dbec7376f54f
  ok  web/src/features/project-room/RoomPeopleSection.tsx  057d906867c1
  ok  web/src/pages/cores/settingsPrefs.tsx  e47f57a69aea
  ok  web/src/pages/cores/SettingsCore.tsx  f769f99d72bc
  ok  web/src/desk/components/DeskListView.tsx  5ff354b39138
  ok  web/src/desk/gl/WorldStage.tsx  f312528691f1
  ok  web/src/desk/components/AskPanel.tsx  87f4668e00a1
  ok  web/src/pages/cores/dictation/Readiness.tsx  a8cdc6d166cd
  ok  web/src/lib/productLanguage.ts  da698fe18279

  rows: 21  failures: 0
VERDICT PASS — every row proved red first
```

### Captured run — 2026-09-21T19:00:34Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/shoot.py 2>&1 | grep -E "shot |hub pid|!!|==" | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
  == 1440x900 ==
  hub pid=74447 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-04-1440-zl09r2wt port=61469
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
  hub pid=76186 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-04-393-xfqpe62_ port=61635
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

### Captured run — 2026-09-21T19:04:09Z

- **Command:** `bash -c set -o pipefail; python3 /tmp/hs20404_assert.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
1440 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
1440 live facts 'Link · connected' receipt 'REC 00:00' SEG? False
1440 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
1440 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Intelligence
1440 ask head 'SESSION'
1440 speak runs row? False RAW READINESS? True Wire details? False
1440 Edit Sequence? True Edit chain? False
1440 list face opened? True door used {'List view': 'desk', 'Spatial view': 'desk'}
1440 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item']
1440 zero names [] zero cells [] EMPTY cells ['EMPTY', 'EMPTY']
393 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
393 live facts 'Link · connected' receipt 'REC 00:00' SEG? False
393 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
393 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Intelligence
393 ask head 'SESSION'
393 speak runs row? False RAW READINESS? True Wire details? False
393 Edit Sequence? True Edit chain? False
393 list face opened? True door used {'Spatial view': 'go'}
393 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item']
393 zero names [] zero cells [] EMPTY cells ['EMPTY', 'EMPTY']
page_errors None console_errors None bad_responses None step_errors None
VERDICT FAIL
```

### Captured run — 2026-09-21T19:04:42Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/red-first.py 2>&1 | tail -25`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
      AssertionError: expected { …(22) } to deeply equal { …(23) }
  RED 20 registry: the seg/mtg aliases
      fence: src/lib/productLanguage.test.ts
      × matches the versioned registry exactly 5ms
      AssertionError: expected { agent: 'persona', …(10) } to deeply equal { agent: 'persona', …(12) }

  -- rebuilding the web bundle (a fence rebuilt it from reverted source) --
  build exit=0

  -- restore check --
  ok  web/src/pages/cores/LiveCore.tsx  abd61da4c0e2
  ok  web/src/pages/cores/history/DoorSection.tsx  f649b49108c6
  ok  web/src/pages/cores/history/CatalogRail.tsx  6cd52b9f35d1
  ok  web/src/desk/pullouts/ChainPullout.tsx  dbec7376f54f
  ok  web/src/features/project-room/RoomPeopleSection.tsx  057d906867c1
  ok  web/src/pages/cores/settingsPrefs.tsx  e47f57a69aea
  ok  web/src/pages/cores/SettingsCore.tsx  f769f99d72bc
  ok  web/src/desk/components/DeskListView.tsx  5ff354b39138
  ok  web/src/desk/gl/WorldStage.tsx  f312528691f1
  ok  web/src/desk/components/AskPanel.tsx  87f4668e00a1
  ok  web/src/pages/cores/dictation/Readiness.tsx  a8cdc6d166cd
  ok  web/src/lib/productLanguage.ts  da698fe18279

  rows: 21  failures: 0
VERDICT PASS — every row proved red first
```

### Captured run — 2026-09-21T19:05:34Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/shoot.py 2>&1 | grep -E "shot |hub pid|!!|==" | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
  == 1440x900 ==
  hub pid=79317 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-04-1440-778jwnpo port=61906
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
  hub pid=80699 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-04-393-j_u7zom3 port=62175
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

### Captured run — 2026-09-21T19:08:56Z

- **Command:** `bash -c set -o pipefail; python3 /tmp/hs20404_assert.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
1440 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
1440 live facts 'Link · connected' receipt 'REC 00:00' SEG? False
1440 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
1440 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Summary
1440 ask head 'SESSION'
1440 speak runs row? False RAW READINESS? True Wire details? False
1440 Edit Sequence? True Edit chain? False
1440 list face opened? True door used {'List view': 'desk', 'Spatial view': 'desk'}
1440 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item']
1440 zero names [] zero cells [] EMPTY cells ['EMPTY', 'EMPTY']
393 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
393 live facts 'Link · connected' receipt 'REC 00:00' SEG? False
393 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
393 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Summary
393 ask head 'SESSION'
393 speak runs row? False RAW READINESS? True Wire details? False
393 Edit Sequence? True Edit chain? False
393 list face opened? True door used {'Spatial view': 'go'}
393 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item']
393 zero names [] zero cells [] EMPTY cells ['EMPTY', 'EMPTY']
page_errors None console_errors None bad_responses None step_errors None
VERDICT PASS
```

### Captured run — 2026-09-21T19:09:11Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/pages/cores/__tests__/summaryName202.test.tsx src/pages/cores/__tests__/settingsSummaryName202.test.tsx src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx src/desk/components/__tests__/zeroCounters202.test.tsx src/desk/pullouts/__tests__/sequenceVerb202.test.tsx src/features/project-room/__tests__/provenanceWords202.test.ts src/pages/cores/dictation/__tests__/readinessZero202.test.tsx --maxWorkers=2 --reporter=verbose 2>&1 | grep -E "✓|×|Test Files|Tests " | tail -40`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
 ✓ src/pages/cores/dictation/__tests__/readinessZero202.test.tsx > the gear door's Runs fact (A.8) > withholds the row when the pipeline has never run 23ms
 ✓ src/pages/cores/dictation/__tests__/readinessZero202.test.tsx > the gear door's Runs fact (A.8) > draws the row once there is a run to count 7ms
 ✓ src/pages/cores/dictation/__tests__/readinessZero202.test.tsx > the gear door's Runs fact (A.8) > keeps the readiness wire behind a fold that says it is raw 6ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > Live calls the meeting result a Summary (F06) > labels the result section Summary 26ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > Live calls the meeting result a Summary (F06) > never says Intelligence on the Live face 10ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > the Live gear door counts nothing to zero (A.8) > names its run-state section Summary, never Intelligence 97ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > the Live gear door counts nothing to zero (A.8) > says the true thing instead of six zeros on an idle queue 22ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > the Live gear door counts nothing to zero (A.8) > says it on the REAL idle wire, which carries a null next retry 20ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > the Live gear door counts nothing to zero (A.8) > still counts the jobs that exist 17ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > the Summary never counts its action items to zero (A.8) > omits the line when a final Summary has nothing to do 9ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > the Summary never counts its action items to zero (A.8) > counts the action items that exist 8ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > Live's row and its receipt hold different facts (M6) > never says the same state word twice 7ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > Live spells its words and states each fact once (F21, M6) > never renders the undefined abbreviation SEG 10ms
 ✓ src/pages/cores/__tests__/summaryName202.test.tsx > Live spells its words and states each fact once (F21, M6) > states the segment count exactly once 9ms
 ✓ src/desk/components/__tests__/zeroCounters202.test.tsx > an empty zone never counts to a screen reader (A.8) > does not announce '0 items' in the row's accessible name 162ms
 ✓ src/desk/components/__tests__/zeroCounters202.test.tsx > an empty zone never counts to a screen reader (A.8) > announces a filled zone in plain lowercase words 40ms
 ✓ src/desk/components/__tests__/zeroCounters202.test.tsx > an empty zone never counts to a screen reader (A.8) > does not print 0 ITEMS in the zone row's own cell 24ms
 ✓ src/desk/components/__tests__/zeroCounters202.test.tsx > the spatial Floor announces no zero either (A.8) > names an empty zone without a count 19ms
 ✓ src/desk/components/__tests__/zeroCounters202.test.tsx > the spatial Floor announces no zero either (A.8) > counts a filled zone in plain lowercase words 22ms
 ✓ src/desk/components/__tests__/zeroCounters202.test.tsx > Ask AI opens without counting its turns to zero (A.8) > heads a fresh session with SESSION, not SESSION · 0 TURNS 15ms
 ✓ src/desk/pullouts/__tests__/sequenceVerb202.test.tsx > the Sequence pullout names its own object (F08) > offers Edit Sequence, never Edit chain 115ms
 ✓ src/pages/cores/__tests__/settingsSummaryName202.test.tsx > the Settings hub's Meetings row (F06) > says SUMMARY ON, never INTELLIGENCE ON 21ms
 ✓ src/pages/cores/__tests__/settingsSummaryName202.test.tsx > the Settings hub's Meetings row (F06) > says SUMMARY OFF, never INTELLIGENCE OFF 7ms
 ✓ src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx > the failed Summary offers one Retry (F07) > names the queue's summary recovery Retry, never Retry intelligence 101ms
 ✓ src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx > the failed Summary offers one Retry (F07) > keeps the deferred plugin job's own verb — a different object 14ms
 ✓ src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx > the cold Meetings face says its all-clear once (M6) > does not repeat the headline's words in the rail's empty state 2ms
 ✓ src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx > the cold Meetings face says its all-clear once (M6) > states the next move instead 1ms
 ✓ src/features/project-room/__tests__/provenanceWords202.test.ts > a commitment's source line (F21) > names the meeting and the segment in words 1ms
 ✓ src/features/project-room/__tests__/provenanceWords202.test.ts > a commitment's source line (F21) > omits the segment when the wire has none 0ms
 ✓ src/features/project-room/__tests__/provenanceWords202.test.ts > a commitment's source line (F21) > never renders the undefined abbreviations 0ms
 Test Files  7 passed (7)
      Tests  30 passed (30)
```

### Captured run — 2026-09-21T19:09:27Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs172_settings_meetings_glass.py 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
....                                                                     [100%]
4 passed in 16.52s
```

### Captured run — 2026-09-21T19:09:46Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run bash -c "
set -e
python -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -2
python scripts/check_docs.py | tail -1
python scripts/philo_repository_census.py --check
python scripts/philo_api_reference.py --check
python scripts/philo_boundary_census.py --check
python scripts/philo_doctor_reference.py --check
python scripts/philo_config_reference.py --check
python scripts/philo_openapi_reference.py --check
python scripts/validate_architecture.py | tail -1
python scripts/generate_capability_docs.py --check
python scripts/check_doc_coverage.py --check | tail -1
echo ALL_PHILO_CHECKS_GREEN
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text

OK
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference checked
Boundary candidate census checked
Doctor reference: 41 check functions
Configuration declaration reference is current
OpenAPI: 569 paths
Architecture metadata validation passed.
Architecture documentation checked (10 outputs).
Documentation coverage checked.
ALL_PHILO_CHECKS_GREEN
```

### Captured run — 2026-09-21T19:10:10Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src --maxWorkers=2 2>&1 | grep -E "Test Files|Tests |FAIL" | tail -10`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
 Test Files  297 passed (297)
      Tests  2752 passed (2752)
```

### Captured run — 2026-09-21T19:11:38Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) npm_config_cache=$HOME_REAL/.npm uv run python scripts/check_web_baseline.py --run 2>&1 | tail -10`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2752 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T19:12:21Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_phase200_doc_claims.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_claim_support.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py tests/unit/test_interior_canon_guard.py tests/unit/test_doc_drift_guard.py 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
........................................................................ [ 40%]
........................................................................ [ 81%]
.................................                                        [100%]
177 passed in 10.45s
```

### Captured run — 2026-09-21T19:12:32Z

- **Command:** `bash -c set -o pipefail; cd web && npm run tokens:check 2>&1 | tail -1 && npm run guard:architecture 2>&1 | tail -1 && npx tsc --noEmit && echo "TYPECHECK CLEAN"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
tokens.css and tokens.gen.ts match design-tokens.json
React architecture guard passed (815 source files; zero framework residue).
TYPECHECK CLEAN
```

### Captured run — 2026-09-21T19:12:57Z

- **Command:** `bash -c set -o pipefail; python3 /tmp/hs20404_aftermap.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
after-map rows: 20
  01   OK  a meeting result (Live, the result section)    Summary | Intelligence       -> Summary
  02   OK  a meeting result (Live gear door run state)    Summary | Intelligence       -> Summary
  03   OK  the capture state (Live row vs footer receipt) connected · ready + READY    -> Link · connected + READY
  04   OK  the segment count (Live footer receipt)        N SEG                        -> (withheld; the stream head cou
  05   OK  action items on a Summary with none            0 action items               -> (withheld)
  06   OK  the deferred queue on an idle desk             total/queued/running/failed/ -> No jobs waiting
  06b  OK  the deferred queue section on the real idle wi header + a lone verb (next_r -> No jobs waiting
  07   OK  recover a failed meeting Summary               Retry | Retry intelligence   -> Retry
  08   OK  the cold Meetings all-clear                    No meetings yet (twice)      -> No meetings yet + Record or im
  09   OK  edit a saved Sequence                          Edit chain                   -> Edit Sequence
  10   OK  a commitment's provenance line                 MTG · X · SEG 4              -> Meeting · X · Segment 4
  11   OK  a meeting result (Settings hub Meetings row)   INTELLIGENCE ON/OFF          -> SUMMARY ON/OFF
  12   OK  a meeting result (Settings meetings module)    Intelligence / Auto-run inte -> Summary / Auto-run the summary
  12b  BAD a meeting result (Settings advanced sheet)     Intelligence                 -> Summary
       !! no red-first row
  13   OK  an empty zone (list face)                      <name> zone, 0 items         -> <name> zone
  14   OK  an empty zone cell (list face)                 0 ITEMS                      -> EMPTY
  15   OK  an empty zone (spatial Floor)                  <name> zone, 0 items         -> <name> zone
  16   OK  a fresh Ask session                            SESSION · 0 TURNS            -> SESSION
  17   OK  the Speak gear door's run count                Runs 0                       -> (row withheld)
  18   OK  the Speak gear door's wire fold                Wire details                 -> RAW · READINESS

noun collisions: 7
  closed-on-touched-faces    Meeting result
  closed-on-touched-faces    Saved sequence
  closed-on-touched-faces    Transcript segment
  closed-on-touched-faces    Meeting (provenance token)
  not-this-story             Primary operating surface
  not-this-story             Named service connection
  not-this-story             The Project Room

collapsed on the touched faces: 4 of 7; the rest carry a recorded reason
VERDICT FAIL
```

### Captured run — 2026-09-21T19:13:50Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/red-first.py 2>&1 | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
      × keeps the readiness wire behind a fold that says it is raw 1011ms
      TestingLibraryElementError: Unable to find an element with the text: RAW · READINESS. This could be because the text is broken up by multiple elements. In this case, you can provide a function for you
  RED 19 registry: the Segment term
      fence: src/lib/productLanguage.test.ts
      × matches the versioned registry exactly 5ms
      AssertionError: expected { …(22) } to deeply equal { …(23) }
  RED 20 registry: the seg/mtg aliases
      fence: src/lib/productLanguage.test.ts
      × matches the versioned registry exactly 5ms
      AssertionError: expected { agent: 'persona', …(10) } to deeply equal { agent: 'persona', …(12) }

  -- rebuilding the web bundle (a fence rebuilt it from reverted source) --
  build exit=0

  -- restore check --
  ok  web/src/pages/cores/LiveCore.tsx  abd61da4c0e2
  ok  web/src/pages/cores/history/DoorSection.tsx  f649b49108c6
  ok  web/src/pages/cores/history/CatalogRail.tsx  6cd52b9f35d1
  ok  web/src/desk/pullouts/ChainPullout.tsx  dbec7376f54f
  ok  web/src/features/project-room/RoomPeopleSection.tsx  057d906867c1
  ok  web/src/pages/cores/settingsPrefs.tsx  e47f57a69aea
  ok  web/src/pages/cores/SettingsCore.tsx  f769f99d72bc
  ok  web/src/desk/components/DeskListView.tsx  5ff354b39138
  ok  web/src/desk/gl/WorldStage.tsx  f312528691f1
  ok  web/src/desk/components/AskPanel.tsx  87f4668e00a1
  ok  web/src/pages/cores/dictation/Readiness.tsx  a8cdc6d166cd
  ok  web/src/lib/productLanguage.ts  da698fe18279

  rows: 22  failures: 0
VERDICT PASS — every row proved red first
```

### Captured run — 2026-09-21T19:14:53Z

- **Command:** `bash -c set -o pipefail; python3 /tmp/hs20404_aftermap.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
after-map rows: 20
  01   OK  a meeting result (Live, the result section)    Summary | Intelligence       -> Summary
  02   OK  a meeting result (Live gear door run state)    Summary | Intelligence       -> Summary
  03   OK  the capture state (Live row vs footer receipt) connected · ready + READY    -> Link · connected + READY
  04   OK  the segment count (Live footer receipt)        N SEG                        -> (withheld; the stream head cou
  05   OK  action items on a Summary with none            0 action items               -> (withheld)
  06   OK  the deferred queue on an idle desk             total/queued/running/failed/ -> No jobs waiting
  06b  OK  the deferred queue section on the real idle wi header + a lone verb (next_r -> No jobs waiting
  07   OK  recover a failed meeting Summary               Retry | Retry intelligence   -> Retry
  08   OK  the cold Meetings all-clear                    No meetings yet (twice)      -> No meetings yet + Record or im
  09   OK  edit a saved Sequence                          Edit chain                   -> Edit Sequence
  10   OK  a commitment's provenance line                 MTG · X · SEG 4              -> Meeting · X · Segment 4
  11   OK  a meeting result (Settings hub Meetings row)   INTELLIGENCE ON/OFF          -> SUMMARY ON/OFF
  12   OK  a meeting result (Settings meetings module)    Intelligence / Auto-run inte -> Summary / Auto-run the summary
  12b  OK  a meeting result (Settings advanced sheet)     Intelligence                 -> Summary
  13   OK  an empty zone (list face)                      <name> zone, 0 items         -> <name> zone
  14   OK  an empty zone cell (list face)                 0 ITEMS                      -> EMPTY
  15   OK  an empty zone (spatial Floor)                  <name> zone, 0 items         -> <name> zone
  16   OK  a fresh Ask session                            SESSION · 0 TURNS            -> SESSION
  17   OK  the Speak gear door's run count                Runs 0                       -> (row withheld)
  18   OK  the Speak gear door's wire fold                Wire details                 -> RAW · READINESS

noun collisions: 7
  closed-on-touched-faces    Meeting result
  closed-on-touched-faces    Saved sequence
  closed-on-touched-faces    Transcript segment
  closed-on-touched-faces    Meeting (provenance token)
  not-this-story             Primary operating surface
  not-this-story             Named service connection
  not-this-story             The Project Room

collapsed on the touched faces: 4 of 7; the rest carry a recorded reason
VERDICT PASS
```

### Captured run — 2026-09-21T19:15:19Z

- **Command:** `bash -c set -o pipefail; python3 /tmp/hs20404_pairs.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text

FILLED-PRIMARY PAIRS on the touched screens (U4)
  OK  web/src/desk/chair/ChairHome.tsx:1777
        Chair / arrival — Continue (Thoughts, first row)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/desk/chair/ChairHome.tsx:1983
        Chair / arrival — Run summary (lead meeting)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/desk/chair/ChairHome.tsx:2069
        Chair / arrival — Answer (blocked coder session)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/pages/cores/history/ImportSection.tsx:63
        Meetings Record wing — Record meeting
        owner: story 05 — one filled primary per window
  OK  web/src/pages/cores/history/ImportSection.tsx:125
        Meetings Record wing — Import (filled even while disabled)
        owner: story 05 — one filled primary per window
  OK  web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:493
        Thought window — Resume / Finish (note footer)
        owner: story 05 — pairs with the restart banner below
  OK  web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:540
        Thought window — Reload Thought (restart banner)
        owner: story 05 — pairs with the note footer above

RAW CONTROLS this lane touched a LABEL on but did not migrate (U1)
  BAD web/src/desk/pullouts/ChainPullout.tsx:63
        Sequence pullout footer — Dictate about this
        owner: story 03 — the raw-control census
        !! expected 'className="desk-chip quiet"', found '<SurfaceFooter verbs={<> <button'
  BAD web/src/desk/pullouts/ChainPullout.tsx:70
        Sequence pullout footer — Edit
        owner: story 03 — the raw-control census
        !! expected 'className="desk-chip is-primary"', found 'Dictate about this'

Neither pair is fixed here: this is the NAMES lane, and a filled/ghost arbitration is a species decision. Every entry above is a line-checked record, not a promise.
VERDICT FAIL
```

### Captured run — 2026-09-21T19:15:30Z

- **Command:** `bash -c set -o pipefail; python3 /tmp/hs20404_pairs.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text

FILLED-PRIMARY PAIRS on the touched screens (U4)
  OK  web/src/desk/chair/ChairHome.tsx:1777
        Chair / arrival — Continue (Thoughts, first row)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/desk/chair/ChairHome.tsx:1983
        Chair / arrival — Run summary (lead meeting)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/desk/chair/ChairHome.tsx:2069
        Chair / arrival — Answer (blocked coder session)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/pages/cores/history/ImportSection.tsx:63
        Meetings Record wing — Record meeting
        owner: story 05 — one filled primary per window
  OK  web/src/pages/cores/history/ImportSection.tsx:125
        Meetings Record wing — Import (filled even while disabled)
        owner: story 05 — one filled primary per window
  OK  web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:493
        Thought window — Resume / Finish (note footer)
        owner: story 05 — pairs with the restart banner below
  OK  web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:540
        Thought window — Reload Thought (restart banner)
        owner: story 05 — pairs with the note footer above

RAW CONTROLS this lane touched a LABEL on but did not migrate (U1)
  OK  web/src/desk/pullouts/ChainPullout.tsx:65
        Sequence pullout footer — Dictate about this
        owner: story 03 — the raw-control census
  OK  web/src/desk/pullouts/ChainPullout.tsx:74
        Sequence pullout footer — Edit
        owner: story 03 — the raw-control census

Neither pair is fixed here: this is the NAMES lane, and a filled/ghost arbitration is a species decision. Every entry above is a line-checked record, not a promise.
VERDICT PASS
```

### Captured run — 2026-09-21T19:15:51Z

- **Command:** `bash -c set -o pipefail; python3 pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/assert-walk-facts.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
1440 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
1440 live facts 'Link · connected' receipt 'REC 00:00' SEG? False
1440 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
1440 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Summary
1440 ask head 'SESSION'
1440 speak runs row? False RAW READINESS? True Wire details? False
1440 Edit Sequence? True Edit chain? False
1440 list face opened? True door used {'List view': 'desk', 'Spatial view': 'desk'}
1440 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item']
1440 zero names [] zero cells [] EMPTY cells ['EMPTY', 'EMPTY']
393 live sections ['SUMMARY', 'TRANSCRIPT'] door ['INTENT ROUTING', 'SUMMARY', 'DEFERRED PLUGIN JOBS', 'DEVICES']
393 live facts 'Link · connected' receipt 'REC 00:00' SEG? False
393 meetings headline 'No meetings yet' empty ['○ Record or import a meeting'] said-twice 1
393 settings chips ['⚠\nNO DEFAULT', '✓\nLIVE', '✓\nSUMMARY ON · AFTER ROOM MEETINGS', '✓\nON'] INTELLIGENCE? False first row Summary
393 ask head 'SESSION'
393 speak runs row? False RAW READINESS? True Wire details? False
393 Edit Sequence? True Edit chain? False
393 list face opened? True door used {'Spatial view': 'go'}
393 zone names ['Decisions zone', 'Inbox zone, 1 item', 'Launch zone', 'Meetings zone, 1 item', 'Personal zone, 2 items', 'Reference zone, 1 item', 'Work zone, 1 item']
393 zero names [] zero cells [] EMPTY cells ['EMPTY', 'EMPTY']
page_errors None console_errors None bad_responses None step_errors None
VERDICT PASS
```

### Captured run — 2026-09-21T19:15:51Z

- **Command:** `bash -c set -o pipefail; python3 pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/check-after-map.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
after-map rows: 20
  01   OK  a meeting result (Live, the result section)    Summary | Intelligence       -> Summary
  02   OK  a meeting result (Live gear door run state)    Summary | Intelligence       -> Summary
  03   OK  the capture state (Live row vs footer receipt) connected · ready + READY    -> Link · connected + READY
  04   OK  the segment count (Live footer receipt)        N SEG                        -> (withheld; the stream head cou
  05   OK  action items on a Summary with none            0 action items               -> (withheld)
  06   OK  the deferred queue on an idle desk             total/queued/running/failed/ -> No jobs waiting
  06b  OK  the deferred queue section on the real idle wi header + a lone verb (next_r -> No jobs waiting
  07   OK  recover a failed meeting Summary               Retry | Retry intelligence   -> Retry
  08   OK  the cold Meetings all-clear                    No meetings yet (twice)      -> No meetings yet + Record or im
  09   OK  edit a saved Sequence                          Edit chain                   -> Edit Sequence
  10   OK  a commitment's provenance line                 MTG · X · SEG 4              -> Meeting · X · Segment 4
  11   OK  a meeting result (Settings hub Meetings row)   INTELLIGENCE ON/OFF          -> SUMMARY ON/OFF
  12   OK  a meeting result (Settings meetings module)    Intelligence / Auto-run inte -> Summary / Auto-run the summary
  12b  OK  a meeting result (Settings advanced sheet)     Intelligence                 -> Summary
  13   OK  an empty zone (list face)                      <name> zone, 0 items         -> <name> zone
  14   OK  an empty zone cell (list face)                 0 ITEMS                      -> EMPTY
  15   OK  an empty zone (spatial Floor)                  <name> zone, 0 items         -> <name> zone
  16   OK  a fresh Ask session                            SESSION · 0 TURNS            -> SESSION
  17   OK  the Speak gear door's run count                Runs 0                       -> (row withheld)
  18   OK  the Speak gear door's wire fold                Wire details                 -> RAW · READINESS

noun collisions: 7
  closed-on-touched-faces    Meeting result
  closed-on-touched-faces    Saved sequence
  closed-on-touched-faces    Transcript segment
  closed-on-touched-faces    Meeting (provenance token)
  not-this-story             Primary operating surface
  not-this-story             Named service connection
  not-this-story             The Project Room

collapsed on the touched faces: 4 of 7; the rest carry a recorded reason
VERDICT PASS
```

### Captured run — 2026-09-21T19:15:51Z

- **Command:** `bash -c set -o pipefail; python3 pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/record-primary-pairs.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text

FILLED-PRIMARY PAIRS on the touched screens (U4)
  OK  web/src/desk/chair/ChairHome.tsx:1777
        Chair / arrival — Continue (Thoughts, first row)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/desk/chair/ChairHome.tsx:1983
        Chair / arrival — Run summary (lead meeting)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/desk/chair/ChairHome.tsx:2069
        Chair / arrival — Answer (blocked coder session)
        owner: story 05 — the primary arbitration on the arrival
  OK  web/src/pages/cores/history/ImportSection.tsx:63
        Meetings Record wing — Record meeting
        owner: story 05 — one filled primary per window
  OK  web/src/pages/cores/history/ImportSection.tsx:125
        Meetings Record wing — Import (filled even while disabled)
        owner: story 05 — one filled primary per window
  OK  web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:493
        Thought window — Resume / Finish (note footer)
        owner: story 05 — pairs with the restart banner below
  OK  web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:540
        Thought window — Reload Thought (restart banner)
        owner: story 05 — pairs with the note footer above

RAW CONTROLS this lane touched a LABEL on but did not migrate (U1)
  OK  web/src/desk/pullouts/ChainPullout.tsx:65
        Sequence pullout footer — Dictate about this
        owner: story 03 — the raw-control census
  OK  web/src/desk/pullouts/ChainPullout.tsx:74
        Sequence pullout footer — Edit
        owner: story 03 — the raw-control census

Neither pair is fixed here: this is the NAMES lane, and a filled/ghost arbitration is a species decision. Every entry above is a line-checked record, not a promise.
VERDICT PASS
```

### Captured run — 2026-09-21T19:16:28Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs172_settings_meetings_glass.py 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
....                                                                     [100%]
4 passed in 15.24s
```

### Captured run — 2026-09-21T19:16:51Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src --maxWorkers=2 2>&1 | grep -E "Test Files|Tests |FAIL" | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 718b16257f8718bb9109d0c9a88bb08d4f32e1ca

```text
 Test Files  297 passed (297)
      Tests  2752 passed (2752)
```

### Counsel round two — RATIFY-WITH-CONDITIONS, evidence only

1. **"The after-map's `site_after` anchors are inaccurate."** Correct, and
   worse than stale: row 01 pointed at
   `web/src/pages/cores/LiveCore.tsx:375`, which is a COMMENT inside the
   deferred-queue filter, while claiming to anchor the Summary section
   label. Seven anchors had drifted under the counsel-round edits (01, 02,
   04, 05, 06, 06b, 10). Every anchor is now the exact line of its changed
   string, verified against the tree before it was written, and each row
   carries a new `anchor_text` column holding that string.
   `site_before` is deliberately NOT anchored to this tree: it names the
   PRE-change census at `93f9524f`, where no line of this file survives.
2. **"The claim says 21 rows while the CSV holds 20."** Corrected above.
   The counts that are genuinely different, so no one has to reconcile
   them: the verb after-map holds **20** face rows; `red-first.py` proves
   **22**, because it also proves the two registry rows (the `Segment`
   term and the `seg`/`mtg` aliases), which are registry entries rather
   than faces and belong to the noun map instead.
3. **"Make the checker REJECT an incorrect consumer reference."** Done:
   `check-after-map.py` now requires `anchor_text` to be present ON the
   anchored line and prints what it found instead. In-range was never a
   reference — it is exactly what let row 01 pass. The rejection is proved
   rather than asserted: `prove-anchor-check.py` puts the stale anchor
   back, requires the checker to fail AND to name the mismatch, restores
   the file (SHA-256 verified) and requires green.

### Captured run — 2026-09-21T19:38:46Z

- **Command:** `bash -c set -o pipefail; python3 pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/prove-anchor-check.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15cd9bbb3bb902200e46b275844e288485dbfd24

```text
  the stale anchor web/src/pages/cores/LiveCore.tsx:375 points at:
      looking non-empty and the shot showed a header with a lone verb
  the true anchor  web/src/pages/cores/LiveCore.tsx:401 points at:
      label="Summary"

  -- with the stale anchor back --
    01   BAD a meeting result (Live, the result section)    Summary | Intelligence       -> Summary
         !! site_after does NOT carry its string: web/src/pages/cores/LiveCore.tsx:375
              wanted: label="Summary"
              found:  looking non-empty and the shot showed a header with a lone verb
  VERDICT FAIL

  -- restored: docs/internal/surface-inventory-2026-09-20/02-verbs-after-2026-09-21.csv 1aab36323c82 (identical) --
  -- with the true anchor --
  VERDICT PASS
VERDICT PASS — a wrong reference is rejected, a right one passes
```

### Captured run — 2026-09-21T19:38:46Z

- **Command:** `bash -c set -o pipefail; python3 pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-04-shots/check-after-map.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15cd9bbb3bb902200e46b275844e288485dbfd24

```text
after-map rows: 20
  01   OK  a meeting result (Live, the result section)    Summary | Intelligence       -> Summary
  02   OK  a meeting result (Live gear door run state)    Summary | Intelligence       -> Summary
  03   OK  the capture state (Live row vs footer receipt) connected · ready + READY    -> Link · connected + READY
  04   OK  the segment count (Live footer receipt)        N SEG                        -> (withheld; the stream head cou
  05   OK  action items on a Summary with none            0 action items               -> (withheld)
  06   OK  the deferred queue on an idle desk             total/queued/running/failed/ -> No jobs waiting
  06b  OK  the deferred queue section on the real idle wi header + a lone verb (next_r -> No jobs waiting
  07   OK  recover a failed meeting Summary               Retry | Retry intelligence   -> Retry
  08   OK  the cold Meetings all-clear                    No meetings yet (twice)      -> No meetings yet + Record or im
  09   OK  edit a saved Sequence                          Edit chain                   -> Edit Sequence
  10   OK  a commitment's provenance line                 MTG · X · SEG 4              -> Meeting · X · Segment 4
  11   OK  a meeting result (Settings hub Meetings row)   INTELLIGENCE ON/OFF          -> SUMMARY ON/OFF
  12   OK  a meeting result (Settings meetings module)    Intelligence / Auto-run inte -> Summary / Auto-run the summary
  12b  OK  a meeting result (Settings advanced sheet)     Intelligence                 -> Summary
  13   OK  an empty zone (list face)                      <name> zone, 0 items         -> <name> zone
  14   OK  an empty zone cell (list face)                 0 ITEMS                      -> EMPTY
  15   OK  an empty zone (spatial Floor)                  <name> zone, 0 items         -> <name> zone
  16   OK  a fresh Ask session                            SESSION · 0 TURNS            -> SESSION
  17   OK  the Speak gear door's run count                Runs 0                       -> (row withheld)
  18   OK  the Speak gear door's wire fold                Wire details                 -> RAW · READINESS

noun collisions: 7
  closed-on-touched-faces    Meeting result
  closed-on-touched-faces    Saved sequence
  closed-on-touched-faces    Transcript segment
  closed-on-touched-faces    Meeting (provenance token)
  not-this-story             Primary operating surface
  not-this-story             Named service connection
  not-this-story             The Project Room

collapsed on the touched faces: 4 of 7; the rest carry a recorded reason
VERDICT PASS
```
