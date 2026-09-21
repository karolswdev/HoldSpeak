# Evidence - HS-202-02

- **Story:** HS-202-02 - First-use doors and truthful state
- **Status:** done
- **Date:** 2026-09-20

## Proof

### Captured run — 2026-09-21T00:53:46Z

- **Command:** `bash -c cd web && npx vitest run 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text

 Test Files  288 passed (288)
      Tests  2695 passed (2695)
   Start at  18:53:47
   Duration  80.44s (transform 41.21s, setup 71.77s, import 206.02s, tests 237.56s, environment 291.46s)
```

### Captured run — 2026-09-21T00:55:17Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/integration/test_web_setup_route.py tests/unit/test_hs202_desk_memory_recent.py tests/unit/test_phase200_continuity.py 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
..............................                                           [100%]
30 passed in 24.09s
```

### Captured run — 2026-09-21T00:55:54Z

- **Command:** `bash -c HOME_REAL=$HOME HOME=$(mktemp -d) npm_config_cache=$HOME_REAL/.npm uv run python scripts/check_web_baseline.py --run 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2695 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T00:57:32Z

- **Command:** `bash -c cd web && npm run guard:architecture 2>&1 | tail -2 && npm run tokens:gate 2>&1 | tail -2 && npm run bundle:gate 2>&1 | tail -2 && npx tsc --noEmit && echo "typecheck clean"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text

React architecture guard passed (806 source files; zero framework residue).

token gate: clean (11 allow-listed exceptions, all in use)

bundle gate passed (Desk JS 1309442 B; Desk CSS 315792 B; source maps 0)
typecheck clean
```

### Captured run — 2026-09-21T00:58:09Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_09_connect_engine_glass.py tests/e2e/test_hs201_12_thought_note_glass.py 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
............................                                             [100%]
28 passed in 447.58s (0:07:27)
```

### Captured run — 2026-09-21T01:06:06Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-02-shots/shoot.py 2>&1 | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
      "Overdue: Land the write-receipt channel",
      "Unassigned: Decide the streaming-partials question",
      "Phase 132 desk review",
      "/Users/karol/dev/tools/wt-202-02",
      "Models",
      "Assignments",
      "Connections",
      "Voice",
      "Meetings",
      "Rhythm",
      "Sounds & Presence",
      "Wallpaper",
      "System"
    ]
  },
  "meeting_record": {
    "1440": {
      "route_disclosed": 0,
      "run_verb": 0
    },
    "393": {
      "route_disclosed": 0,
      "run_verb": 0
    }
  },
  "speak_footer_chips": {
    "1440": [],
    "393": []
  }
}
```

## Rulings

The coordinator's two rulings of 2026-09-20 (the microphone recovery verb, and
the honest name for the leaving verb), with the runs that prove them.

### Captured run — 2026-09-21T01:40:53Z

- **Command:** `bash -c cd web && npx vitest run src/desk/components/FirstWords.test.tsx src/lib/dictationRecovery.test.ts src/desk/__tests__/menuGlyphs.test.tsx 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
 Test Files  3 passed (3)
      Tests  56 passed (56)
   Start at  19:40:53
   Duration  1.54s (transform 533ms, setup 317ms, import 891ms, tests 796ms, environment 714ms)
```

### Captured run — 2026-09-21T01:41:00Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs202_first_value_failure_vocabulary.py tests/unit/test_hs202_desk_memory_recent.py tests/integration/test_web_setup_route.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
................                                                         [100%]
16 passed in 2.85s
```

### Captured run — 2026-09-21T01:41:04Z

- **Command:** `bash -c cd web && npx tsc --noEmit && echo "typecheck clean" && npx vitest run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
typecheck clean
      Tests  2700 passed (2700)
   Start at  19:41:14
   Duration  37.82s (transform 17.65s, setup 34.44s, import 103.56s, tests 110.39s, environment 123.61s)
```

### Captured run — 2026-09-21T01:41:58Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-02-shots/shoot.py 2>&1 | tail -34`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
      "Decide the streaming-partials question",
      "Photograph the placement dial states",
      "Thought",
      "Meeting recorded: Phase 132 desk review",
      "Overdue: Land the write-receipt channel",
      "Unassigned: Decide the streaming-partials question",
      "Phase 132 desk review",
      "/Users/karol/dev/tools/wt-202-02",
      "Models",
      "Assignments",
      "Connections",
      "Voice",
      "Meetings",
      "Rhythm",
      "Sounds & Presence",
      "Wallpaper",
      "System"
    ]
  },
  "meeting_record": {
    "1440": {
      "route_disclosed": 0,
      "run_verb": 0
    },
    "393": {
      "route_disclosed": 0,
      "run_verb": 0
    }
  },
  "speak_footer_chips": {
    "1440": [],
    "393": []
  }
}
```

### Captured run — 2026-09-21T01:45:54Z

- **Command:** `bash -c python3 -c "
import json
d = json.load(open(\"pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-02-shots/walk-facts.json\"))
for k in (\"mic_refusal\",\"bad_responses\",\"console_errors\",\"page_errors\",\"step_errors\"):
    print(k, json.dumps(d.get(k)))
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53ba7839dd65d61d9f223df298ca4a8623bce0e3

```text
mic_refusal {"1440": {"message": "\u26a0\ufe0e\nNo microphone was found on this device. Your draft remains editable. Connect a microphone, then retry.", "verbs": ["Click to retry", "", "Copy", "Keep as Note", "Check the microphone", "Continue later", "Skip for now"]}, "393": {"message": "\u26a0\ufe0e\nNo microphone was found on this device. Your draft remains editable. Connect a microphone, then retry.", "verbs": ["Click to retry", "", "Copy", "Keep as Note", "Check the microphone", "Continue later", "Skip for now"]}}
bad_responses null
console_errors null
page_errors null
step_errors null
```

## Counsel round (Astra, PR #595 DO-NOT-RATIFY)

Every run below is captured with `set -o pipefail`, so a tail never
certifies the pipe instead of the run. RED tails are captured beside the
green ones.

### Captured run — 2026-09-21T02:30:03Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
 Test Files  290 passed (290)
      Tests  2711 passed (2711)
   Start at  20:30:04
   Duration  43.71s (transform 23.87s, setup 42.76s, import 119.40s, tests 112.48s, environment 157.42s)
```

### Captured run — 2026-09-21T02:31:06Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/red.sh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
== reverted the five counsel fixes ==
 FAIL  src/pages/cores/__tests__/meetingRefresh202.test.tsx > a slow refresh never restores a record the owner left > drops a response for a record that is no longer selected
AssertionError: expected 'Imported meeting' to be 'The other meeting' // Object.is equality

Expected: "The other meeting"
Received: "Imported meeting"

 ❯ src/pages/cores/__tests__/meetingRefresh202.test.tsx:204:25
    202|     });
    203|
    204|     expect(openTitle()).toBe("The other meeting");
       |                         ^
    205|   });
    206| });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[8/8]⎯


 Test Files  4 failed (4)
      Tests  8 failed | 11 passed (19)
   Start at  20:31:07
   Duration  3.35s (transform 1.14s, setup 608ms, import 1.79s, tests 2.94s, environment 2.09s)

== restored; vitest exit while reverted was 1 (non-zero = RED, as required) ==
```

### Captured run — 2026-09-21T02:31:23Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs202_desk_memory_recent.py tests/unit/test_hs202_first_value_failure_vocabulary.py tests/integration/test_web_setup_route.py tests/unit/test_phase200_continuity.py 2>&1 | tail -4; echo "pytest exit: $?"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
.....................................                                    [100%]
37 passed in 8.31s
pytest exit: 0
```

### Captured run — 2026-09-21T02:31:39Z

- **Command:** `bash -c set -o pipefail; python3 -c "
import json
d = json.load(open(\"pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-02-shots/walk-facts.json\"))
for k in (\"mic_recovery_opens\",\"generate\",\"transcript_import\",\"meeting_record\",\"mic_refusal\",\"bad_responses\",\"console_errors\",\"page_errors\",\"step_errors\"):
    print(k, json.dumps(d.get(k)))
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
mic_recovery_opens {"1440": {"setup_window": 1, "new_project_window": 0, "readiness_face": 3}, "393": {"setup_window": 1, "new_project_window": 0, "readiness_face": 3}}
generate {"1440": {"verb_present": 1, "badge_before": "THIS DEVICE", "receipt_after": "Brief ready \u00b7 3 items \u00b7 8:25 PM"}, "393": {"verb_present": 1, "badge_before": "THIS DEVICE", "receipt_after": "Brief ready \u00b7 3 items \u00b7 8:27 PM"}}
transcript_import {"1440": 202, "393": 202}
meeting_record {"1440": {"title": "HS-202-02 transcript", "route_disclosed": 1, "run_verb": 0, "record_rereads_on_signal": 2}, "393": {"title": "HS-202-02 transcript", "route_disclosed": 1, "run_verb": 0, "record_rereads_on_signal": 2}}
mic_refusal {"1440": {"message": "\u26a0\ufe0e\nThe browser gave no microphone. Your draft remains editable. Check the microphone, then retry.", "verbs": ["Click to retry", "", "Copy", "Keep as Note", "Check the microphone", "Continue later", "Skip for now"]}, "393": {"message": "\u26a0\ufe0e\nThe browser gave no microphone. Your draft remains editable. Check the microphone, then retry.", "verbs": ["Click to retry", "", "Copy", "Keep as Note", "Check the microphone", "Continue later", "Skip for now"]}}
bad_responses null
console_errors null
page_errors null
step_errors null
```

## Counsel fix round 2 (Astra PR #595 + coordinator items 9-10)

All runs `set -o pipefail`.

### Captured run — 2026-09-21T03:55:33Z

- **Command:** `bash -c set -o pipefail; cd web && npx tsc --noEmit && echo "typecheck clean" && npm run guard:architecture 2>&1 | tail -2 && npx vitest run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
typecheck clean

React architecture guard passed (808 source files; zero framework residue).
     Errors  3 errors
   Start at  21:55:44
   Duration  38.89s (transform 22.51s, setup 37.26s, import 112.57s, tests 103.18s, environment 131.54s)
```

### Captured run — 2026-09-21T03:57:47Z

- **Command:** `bash -c set -o pipefail; cd web && npx tsc --noEmit && echo "typecheck clean" && npm run guard:architecture 2>&1 | tail -2 && npx vitest run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
typecheck clean

React architecture guard passed (808 source files; zero framework residue).
      Tests  2714 passed (2714)
   Start at  21:57:58
   Duration  43.60s (transform 23.66s, setup 41.61s, import 118.50s, tests 117.89s, environment 152.27s)
```

### Captured run — 2026-09-21T03:58:48Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs202_desk_memory_recent.py tests/unit/test_hs202_first_value_failure_vocabulary.py tests/unit/test_hs202_import_announces.py tests/integration/test_web_setup_route.py tests/unit/test_phase200_continuity.py tests/unit/test_api_surface.py tests/unit/test_backend_density_guard.py tests/unit/test_web_vocabulary_guard.py 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
...........................................................              [100%]
59 passed in 11.71s
```

### Captured run — 2026-09-21T03:59:07Z

- **Command:** `bash -c set -o pipefail; python3 -c "
import json
d = json.load(open(\"pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-02-shots/walk-facts.json\"))
for k in (\"mic_recovery_opens\",\"generate\",\"meeting_record\",\"dock_presses\",\"desk_memory\",\"note_keep_receipt\",\"mic_refusal\",\"bad_responses\",\"console_errors\",\"page_errors\",\"step_errors\"):
    print(k, json.dumps(d.get(k)))
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
mic_recovery_opens {"1440": {"setup_window": 1, "new_project_window": 0, "readiness_face": 3}, "393": {"setup_window": 1, "new_project_window": 0, "readiness_face": 3}}
generate {"1440": {"verb_present": 1, "badge_before": "THIS DEVICE", "receipt_after": "Brief ready \u00b7 3 items \u00b7 9:49 PM"}, "393": {"verb_present": 1, "badge_before": "THIS DEVICE", "receipt_after": "Brief ready \u00b7 3 items \u00b7 9:53 PM"}}
meeting_record {"1440": {"title": "HS-202-02 transcript", "route_disclosed": 1, "run_verb": 0, "record_rereads_on_signal": 1}, "393": {"title": "HS-202-02 transcript", "route_disclosed": 1, "run_verb": 0, "record_rereads_on_signal": 1}}
dock_presses {"1440": {"total": 9, "pressed": 9, "refused": []}, "393": {"total": 9, "pressed": 9, "refused": []}}
desk_memory {"1440": {"body": 1, "results_region": 1, "rows": 2, "aria": "Recent on this desk"}, "393": {"body": 1, "results_region": 1, "rows": 2, "aria": "Recent on this desk"}}
note_keep_receipt {"1440": "KEPT \u00b7 9:50 PM", "393": "KEPT \u00b7 9:53 PM"}
mic_refusal {"1440": {"message": "\u26a0\ufe0e\nThe browser gave no microphone. Your draft remains editable. Check the microphone, then retry.", "verbs": ["Click to retry", "", "Copy", "Keep as Note", "Check the microphone", "Continue later", "Skip for now"]}, "393": {"message": "\u26a0\ufe0e\nThe browser gave no microphone. Your draft remains editable. Check the microphone, then retry.", "verbs": ["Click to retry", "", "Copy", "Keep as Note", "Check the microphone", "Continue later", "Skip for now"]}}
bad_responses null
console_errors null
page_errors null
step_errors null
```

### Captured run — 2026-09-21T04:04:55Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs141_chair_geometry.py tests/e2e/test_hs170_speak_glass.py tests/e2e/test_hs170_settings_hub_glass.py tests/e2e/test_hs200_continuity_glass.py tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_12_thought_note_glass.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4eb1fd8a887166ceb2d5588417ab8deb99523e1f

```text
........................................                                 [100%]
40 passed in 278.14s (0:04:38)
```

## The import-refresh gap

The one red the counsel round left open: after an Import completed, the
meeting record showed the transcript but not `Run summary`, and only a
reopen brought the verb back (Astra's first-use smoke, `import-refresh`
leg, red at 1440 and 393).

**Cause.** `holdspeak/services/meeting_service.py:285` announces the desk
change the instant the import worker finishes — which is BEFORE the owner
clicks the row it just changed, so the announcement lands while nothing is
open. `web/src/pages/cores/HistoryCore.tsx` debounced that announcement by
300 ms inside an effect whose dependency list carried `refreshFace`;
opening a record changes `selectedId`, which changes `refreshFace`, which
re-ran the effect — and its cleanup `clearTimeout`-ed the pending refresh.
The ledger was therefore never re-read at all. The open record kept the
`intel_status: "importing"` snapshot the click had taken, `summaryIsOff`
(`history/helpers.ts:198`) read `SAVED` from it, and `HistoryCore.tsx:480`
withheld `onRunIntelligence` — so `NeedsYouTable` had no verb to draw.

**Fix.** One dependency: the subscription is now held for the life of the
face, and the debounce with it; a ref keeps `refreshFace` current without
making the subscription depend on it.

**Red then green**, one line apart (`}, [subscribeFrames, refreshFace]);`
vs `}, [subscribeFrames]);`), everything else identical:

| Fence | with the dependency | without it |
| --- | --- | --- |
| `meetingRefresh202.test.tsx` — the frame arrived before the click | 1 failed \| 5 passed | 6 passed |
| `test_hs202_02_first_use_glass.py` (the story's own) | `MISSING verb 0 route 0 needs-you 0 transcript 1` | PASS 1440 + PASS 393 |
| Astra's smoke, `import-refresh` leg | `FAIL: The imported transcript exposes Run summary without a reload` | `PASS: …` at both widths |

The unit fence needed one repair of its own before it could see any of
this: its `RuntimeBus` mock minted a fresh `subscribe` per render, while
the real bus hands out one for the life of the provider
(`runtime/RuntimeBus.tsx:31`). Every subscriber's effect therefore re-ran
on every render inside the mock, which hid exactly the defect above.

### Captured run — 2026-09-21T04:31:46Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx vitest run --maxWorkers=2 src/pages/cores/__tests__/meetingRefresh202.test.tsx src/pages/cores/__tests__/speakRoom.test.tsx src/desk/__tests__/counsel595.test.tsx src/desk/__tests__/phoneDoors.test.tsx src/desk/__tests__/menuGlyphs.test.tsx src/desk/__tests__/shelfTypedMatch.test.ts src/desk/components/FirstWords.test.tsx src/lib/dictationRecovery.test.ts 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.19.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.19.1
npm notice To update run: npm install -g npm@11.19.1
npm notice
```

### Captured run — 2026-09-21T04:31:54Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx tsc --noEmit && echo "tsc --noEmit: clean"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.19.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.19.1
npm notice To update run: npm install -g npm@11.19.1
npm notice
tsc --noEmit: clean
```

### Captured run — 2026-09-21T04:32:08Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs141_chair_geometry.py tests/e2e/test_hs170_speak_glass.py tests/e2e/test_hs170_settings_hub_glass.py tests/e2e/test_hs200_continuity_glass.py tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs202_02_first_use_glass.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text
.........................................                                [100%]
41 passed in 261.32s (0:04:21)
```

### Captured run — 2026-09-21T04:36:49Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx vitest run --maxWorkers=2 src/pages/cores/__tests__/meetingRefresh202.test.tsx src/pages/cores/__tests__/speakRoom.test.tsx src/desk/__tests__/counsel595.test.tsx src/desk/__tests__/phoneDoors.test.tsx src/desk/__tests__/menuGlyphs.test.tsx src/desk/__tests__/shelfTypedMatch.test.ts src/desk/components/FirstWords.test.tsx src/lib/dictationRecovery.test.ts 2>&1 | grep -v "npm notice" | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text

 Test Files  8 passed (8)
      Tests  101 passed (101)
   Start at  22:36:50
   Duration  3.84s (transform 777ms, setup 433ms, import 1.83s, tests 2.97s, environment 1.71s)
```

### Captured run — 2026-09-21T04:36:59Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs202_first_use_smoke.py 2>&1 | grep -E "import-refresh|Run summary|FAIL:|RECOVERY|passed|failed" | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text
PASS: The imported transcript exposes Run summary without a reload
PASS: The imported transcript exposes Run summary without a reload
2 passed in 57.10s
```

### Captured run — 2026-09-21T04:38:03Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-02-shots/shoot.py 2>&1 | grep -E "meeting_record|console_errors|page_errors|step_errors|bad_responses|SHOT" | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text
  "meeting_record": {
```

### The residual race, closed (coordinator's follow-up)

`refreshFace` merges only into a record that is ALREADY open. A list read
in flight at the moment of the click — or one the search box starts —
lands its fresh rows after `selected` was frozen, with no frame following
to reconcile them, so the open record wears a snapshot the ledger beside
it has already replaced.

`web/src/pages/cores/HistoryCore.tsx:226-247` makes the open record follow
the ledger on every rows change, guarded twice: by id (a row for a record
the owner left is dropped) and by content (an unchanged row keeps the same
object, so the record's own reads are not re-fetched on every reload).

Red first: with the merge disabled, `meetingRefresh202.test.tsx` fails with
`expected 'Still importing' to be 'The transcribed meeting'`
(`Tests 1 failed | 6 passed (7)`); with it, `Tests 7 passed (7)`.

### Captured run — 2026-09-21T04:46:39Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx vitest run src/pages/cores/__tests__/meetingRefresh202.test.tsx 2>&1 | grep -v "npm notice" | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text

 Test Files  1 passed (1)
      Tests  7 passed (7)
   Start at  22:46:39
   Duration  2.51s (transform 356ms, setup 104ms, import 500ms, tests 1.54s, environment 288ms)
```

### Captured run — 2026-09-21T04:46:47Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx tsc --noEmit && echo "tsc --noEmit: clean"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.19.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.19.1
npm notice To update run: npm install -g npm@11.19.1
npm notice
tsc --noEmit: clean
```

### Captured run — 2026-09-21T04:46:57Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs202_02_first_use_glass.py 2>&1 | grep -E "PASS |MISSING|passed|failed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d1383a0299529c6e9833928cd540f02ccb0d250

```text
PASS 1440: the imported record shows its transcript, Run summary and host same_device with no reload (meeting 890b042d)
PASS 393: the imported record shows its transcript, Run summary and host same_device with no reload (meeting 8dcc8362)
1 passed in 17.09s
```

## Round 2 residuals

Astra's round-two residuals (b), each fixed at its source and fenced
red-first.

**1 — deduplication hid the desk's own objects.**
`web/src/desk/components/DeskToolShelf.tsx:170` ran `oneDoorPerName` over
EVERY palette row (applied at `:493`), so three notes and a meeting all
titled "Thought" collapsed to one row and the other three were
unreachable from ⌘K. Deduplication is a rule about DOORS — two ways to one
job — so it now skips object sections (`OBJECTS`, `MEETINGS`, `PROJECTS`,
`SETTINGS`, `DeskToolShelf.tsx:154`), and the live-name set that drops a
ghost is read from doors alone, so a note titled "Open" can never withdraw
the `Open` verb. Red first (`web/src/desk/__tests__/counsel595.test.tsx`):

```text
× keeps every object that wears one title
  AssertionError: expected [ 'note:a' ] to deeply equal [ 'note:a', 'note:b', 'meeting:c' ]
× never lets an object's title withdraw a verb of the same name
  AssertionError: expected [ 'note:open' ] to deeply equal [ 'note:open', 'object.open' ]
```

The `Ask AI` fold is unchanged: the launcher and the object verb still
collapse to one door.

**2 — `microphone_unavailable` offered New Project as microphone
recovery.** Both microphone failures set `setup: true`
(`web/src/lib/dictationRecovery.ts:63`), but `FirstWords.tsx:474` selected
the doctor for `no_microphone` alone, so `NotReadableError` /
`TrackStartError` sent the owner to the one-screen Door. The routing
decision now lives with the contract — `needsMicrophoneDoctor()`,
`dictationRecovery.ts:155-173` — and the face reads it for BOTH the
surface and the verb text. Red first:

```text
× sends both microphone failures to the readiness face
  AssertionError: expected false to be true
× is the gate the face itself reads, for the route AND the verb
```

**3 — recall asked for `thread` and RECENT had no source for it.**
`holdspeak/services/recall_service.py:54` lists `thread` under `_ALSO_KINDS`;
neither `_RECENT_SPECS` nor `_ECOSYSTEM_SPECS` carried it, so
`db/memory.py:376` skipped the kind in silence and a desk whose only
memory is threads read as an empty desk. Added the thread recency spec
(`holdspeak/db/memory.py:185-213`) wearing the lexical pass's own custody
filters — deleted threads and messages, sensitive parts and drafts never
reach memory. Red first
(`tests/unit/test_hs202_desk_memory_recent.py`):

```text
FAILED test_a_desk_of_only_threads_is_not_empty
FAILED test_every_kind_recall_asks_for_has_a_recent_source
  AssertionError: ['thread']
2 failed, 9 passed
```

The third new case is a drift fence: no kind recall asks for may be
skipped in silence again.

**4 — ledger hygiene.** The story's Notes lost the stale `STILL RED`
import entry (paid — see `## The import-refresh gap`) and the "deferred
vocabulary" entry (paid in full, fenced in
`tests/unit/test_hs202_first_value_failure_vocabulary.py`). The inherited
failures are now listed as node IDs — five, not four — answering Astra's
round-2 UNKNOWN ("I could not find the four parallel-only failure IDs or
full Python tail"), with this measured correction: **none of them is
parallel-only.** All five reproduce in a plain serial run of their own
file, which the capture below shows (exit code 1, preserved).

### Captured run — 2026-09-21T05:03:56Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx vitest run --maxWorkers=2 src/desk/__tests__/counsel595.test.tsx src/desk/__tests__/phoneDoors.test.tsx src/desk/__tests__/menuGlyphs.test.tsx src/desk/__tests__/shelfTypedMatch.test.ts src/desk/components/FirstWords.test.tsx src/lib/dictationRecovery.test.ts src/pages/cores/__tests__/meetingRefresh202.test.tsx src/pages/cores/__tests__/speakRoom.test.tsx 2>&1 | grep -v "npm notice" | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa0dd18f486e80102955e0aed07d8af26e9e7723

```text

 Test Files  8 passed (8)
      Tests  108 passed (108)
   Start at  23:03:57
   Duration  3.92s (transform 799ms, setup 456ms, import 1.89s, tests 3.00s, environment 1.73s)
```

### Captured run — 2026-09-21T05:04:01Z

- **Command:** `bash -c set -o pipefail; cd web && HOME=$(mktemp -d) npx tsc --noEmit && echo "tsc --noEmit: clean"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa0dd18f486e80102955e0aed07d8af26e9e7723

```text
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.19.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.19.1
npm notice To update run: npm install -g npm@11.19.1
npm notice
tsc --noEmit: clean
```

### Captured run — 2026-09-21T05:04:15Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs202_desk_memory_recent.py tests/unit/test_hs202_import_announces.py tests/unit/test_hs202_first_value_failure_vocabulary.py -rf 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa0dd18f486e80102955e0aed07d8af26e9e7723

```text
................                                                         [100%]
16 passed in 3.07s
```

### Captured run — 2026-09-21T05:04:19Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs202_02_first_use_glass.py 2>&1 | grep -E "PASS |MISSING|passed|failed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa0dd18f486e80102955e0aed07d8af26e9e7723

```text
PASS 1440: the imported record shows its transcript, Run summary and host same_device with no reload (meeting 143840ba)
PASS 393: the imported record shows its transcript, Run summary and host same_device with no reload (meeting 4c99b0a0)
1 passed in 11.27s
```

### Captured run — 2026-09-21T05:04:38Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs202_first_use_smoke.py 2>&1 | grep -E "FAIL:|RECOVERY|Run summary|passed|failed" | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa0dd18f486e80102955e0aed07d8af26e9e7723

```text
PASS: The imported transcript exposes Run summary without a reload
PASS: The imported transcript exposes Run summary without a reload
2 passed in 57.23s
```

### Captured run — 2026-09-21T05:05:42Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q -p no:randomly tests/unit/test_doc_drift_guard.py tests/unit/test_hs175_calendar_sources.py tests/e2e/test_hs154_call_glass.py tests/e2e/test_hs170_meetings_glass.py -rf 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** aa0dd18f486e80102955e0aed07d8af26e9e7723

```text
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link
FAILED tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week
FAILED tests/e2e/test_hs154_call_glass.py::test_tts_api_404_law - assert True...
FAILED tests/e2e/test_hs154_call_glass.py::test_tts_settings_glass - Assertio...
FAILED tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face
5 failed, 53 passed in 70.03s (0:01:10)
```
