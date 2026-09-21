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
