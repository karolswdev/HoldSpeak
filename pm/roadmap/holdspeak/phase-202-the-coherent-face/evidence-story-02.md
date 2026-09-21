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
