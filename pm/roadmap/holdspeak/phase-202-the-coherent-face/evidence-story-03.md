# Evidence - HS-202-03

- **Story:** HS-202-03 - Shared controls on the first-use path become library species
- **Status:** done
- **Date:** 2026-09-21

## Proof

### Captured run — 2026-09-21T15:09:18Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/desk/__tests__/hs202ChromeSpecies.test.tsx --maxWorkers=2 2>&1 | tail -20`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
+   "<button",
+   "<button",
+ ]

 ❯ src/desk/__tests__/hs202ChromeSpecies.test.tsx:65:41
     63| describe("HS-202-03 — no raw control on the five jobs' shared screens"…
     64|   it.each(MIGRATED)("%s draws every verb with the library Button", (_n…
     65|     expect(src.match(RAW_BUTTON) ?? []).toEqual([]);
       |                                         ^
     66|   });
     67| });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[6/18]⎯


 Test Files  1 failed (1)
      Tests  18 failed | 7 passed (25)
   Start at  09:09:19
   Duration  773ms (transform 117ms, setup 97ms, import 200ms, tests 73ms, environment 284ms)
```

### Captured run — 2026-09-21T15:19:51Z

- **Command:** `bash -c set -o pipefail; SCR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/redproof; HOME=$(mktemp -d) uv run pytest -q $SCR/tests/unit/test_ux_canon_ratchet.py -p no:cacheprovider 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED ../../../../../private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/redproof/tests/unit/test_ux_canon_ratchet.py::test_ratchet
FAILED ../../../../../private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/redproof/tests/unit/test_ux_canon_ratchet.py::test_hard_zeros
2 failed, 2 passed, 4 warnings in 0.62s
```

### Captured run — 2026-09-21T15:19:52Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py -p no:cacheprovider 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout_method
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
38 passed, 4 warnings in 1.41s
```

### Captured run — 2026-09-21T15:20:55Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run python scripts/check_web_baseline.py --run 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

BRANCH-NEW (1):
  BRANCH-NEW: src/desk/pullouts/NotePullout.test.tsx > NotePullout adoption recovery > scrolls a successful Original reveal into the nearest visible pullout position

Suite totals: 2743 passed, 1 failed, 0 skipped

VERDICT: BRANCH-NEW FAILURES: 1
```

### Captured run — 2026-09-21T15:21:52Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run python scripts/check_web_baseline.py --run 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2744 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T15:25:27Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_first_use_smoke.py 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
..                                                                       [100%]
2 passed in 58.24s
```

### Captured run — 2026-09-21T15:26:35Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_09_connect_engine_glass.py tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs202_02_first_use_glass.py 2>&1 | tail -20`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
.............................                                            [100%]
29 passed in 228.67s (0:03:48)
```

### Captured run — 2026-09-21T15:48:34Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_03_species_glass.py 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
....                                                                     [100%]
4 passed in 27.58s
```

### Captured run — 2026-09-21T15:49:11Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/desk/__tests__/hs202ChromeSpecies.test.tsx src/components/signal/Signal.test.tsx src/desk/surface/__tests__/wings.test.tsx src/desk/__tests__/workMenu.test.tsx src/desk/components/DeskEditor.test.tsx --maxWorkers=2 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
 RUN  v4.1.9 /Users/karol/dev/tools/wt-202-03/web


 Test Files  5 passed (5)
      Tests  55 passed (55)
   Start at  09:49:11
   Duration  1.70s (transform 639ms, setup 290ms, import 1.20s, tests 421ms, environment 1.09s)
```

### Captured run — 2026-09-21T15:49:41Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run python scripts/check_web_baseline.py --run 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2745 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T15:50:38Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_09_connect_engine_glass.py tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs202_02_first_use_glass.py tests/e2e/test_hs202_first_use_smoke.py tests/e2e/test_hs202_03_species_glass.py 2>&1 | tail -10`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
...................................                                      [100%]
35 passed in 309.62s (0:05:09)
```

### Captured run — 2026-09-21T15:56:24Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 68e5fc43080fadc7972c23f0f951fb07b3a814b9

```text
......................................                                   [100%]
38 passed in 1.39s
```

## Counsel round

Astra's counsel on #598 returned **RATIFY-WITH-CONDITIONS**
(`.tmp/two-brains/20260921-123218-counsel-202-345-counsel/last.md`). The runs
below close its four conditions: the Philo inventories regenerated and
re-checked, the PAIRED reduced-motion reproduction against the base commit
73758ef3 (verdict INHERITED — zero controls ringless only on this branch),
and the re-runs of every fence and rig after the docstring/story corrections.
The overclaim corrections and the two ledger rows with owners are text, not
runs: see the story file and `current-phase-status.md`.

### Captured run — 2026-09-21T18:51:52Z

- **Command:** `bash -c set -o pipefail; for s in philo_repository_census philo_api_reference philo_boundary_census philo_doctor_reference philo_config_reference philo_openapi_reference; do printf "%-26s " "$s"; HOME=$(mktemp -d) uv run python scripts/$s.py --check 2>&1 | tail -1; done`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7ead226b9c7b7dd0d352384946bc9c7931180206

```text
philo_repository_census    Repository census: 5 outputs verified.
philo_api_reference        API reference checked
philo_boundary_census      Boundary candidate census checked
philo_doctor_reference     Doctor reference: 41 check functions
philo_config_reference     Configuration declaration reference is current
philo_openapi_reference    OpenAPI: 569 paths
```

### Captured run — 2026-09-21T18:52:10Z

- **Command:** `bash -c set -o pipefail; python3 -c "
import json
d=json.load(open(\"pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-03-shots/reduced-motion-paired-baseline.json\"))
print(\"PAIRED reduced-motion reproduction, base\", d[\"base_commit\"], \"vs\", d[\"branch\"])
for r in d[\"rounds\"]:
    print(\"  round %d: base %d/%d ringless | branch %d/%d ringless | ringless ONLY on branch: %s\" % (r[\"round\"], r[\"base_ringless_rows\"], r[\"stops\"], r[\"branch_ringless_rows\"], r[\"stops\"], r[\"ringless_only_on_branch\"] or \"none\"))
print(\"VERDICT:\", d[\"verdict\"].split(\".\")[0] + \".\")
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7ead226b9c7b7dd0d352384946bc9c7931180206

```text
PAIRED reduced-motion reproduction, base 73758ef3 vs feat/hs-202-03-species
  round 1: base 18/26 ringless | branch 17/26 ringless | ringless ONLY on branch: none
  round 2: base 18/26 ringless | branch 17/26 ringless | ringless ONLY on branch: none
  round 3: base 18/26 ringless | branch 18/26 ringless | ringless ONLY on branch: none
VERDICT: INHERITED.
```

### Captured run — 2026-09-21T18:52:23Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_03_species_glass.py tests/e2e/test_hs202_first_use_smoke.py tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_09_connect_engine_glass.py tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs202_02_first_use_glass.py 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7ead226b9c7b7dd0d352384946bc9c7931180206

```text
...................................                                      [100%]
35 passed in 299.39s (0:04:59)
```

### Captured run — 2026-09-21T18:57:41Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py -p no:cacheprovider 2>&1 | tail -2; HOME=$(mktemp -d) uv run python scripts/check_web_baseline.py --run 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7ead226b9c7b7dd0d352384946bc9c7931180206

```text
......................................                                   [100%]
38 passed in 1.14s
Suite totals: 2745 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T19:17:29Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_03_species_glass.py 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f5ece779f86701668836aa9df0ed52bb2d93eaf7

```text
....                                                                     [100%]
4 passed in 29.72s
```

### Captured run — 2026-09-21T19:18:29Z

- **Command:** `bash -c set -o pipefail; python3 -c "
import json
d=json.load(open(\"pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-03-shots/strip-touch-targets-393.json\"))
print(\"STRIP TOUCH TARGETS at 393 (dock + wing bar, bounding boxes off the glass)\")
print(\"  under 44px BEFORE:\", len(d[\"at_393\"][\"rows_under_44_before\"]))
for l,h in d[\"at_393\"][\"rows_under_44_before\"]: print(\"      %-26s %4.0f px\" % (l,h))
print(\"  under 44px AFTER :\", len(d[\"at_393\"][\"rows_under_44_after\"]) or \"none\")
print(\"  dock box height  : %d -> %d px\" % (d[\"at_393\"][\"dock_box_height\"][\"before\"], d[\"at_393\"][\"dock_box_height\"][\"after\"]))
print(\"AT 1440, paired bundle swap on the same page:\")
print(\"  rows compared %d, rows changed %d, dock box %d -> %d\" % (d[\"at_1440\"][\"rows_compared\"], len(d[\"at_1440\"][\"rows_changed\"]), d[\"at_1440\"][\"dock_box_height\"][\"before\"], d[\"at_1440\"][\"dock_box_height\"][\"after\"]))
print(\"  \", d[\"at_1440\"][\"verdict\"])
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f5ece779f86701668836aa9df0ed52bb2d93eaf7

```text
STRIP TOUCH TARGETS at 393 (dock + wing bar, bounding boxes off the glass)
  under 44px BEFORE: 10
      Artifacts                    23 px
      Change places                36 px
      Meeting plumbing             24 px
      Outcomes                     23 px
      Overview                     22 px
      Record                       23 px
      Record a meeting             40 px
      Reset layout                 22 px
      Review                       23 px
      ◌Hide the menus              36 px
  under 44px AFTER : none
  dock box height  : 127 -> 149 px
AT 1440, paired bundle swap on the same page:
  rows compared 19, rows changed 0, dock box 53 -> 53
   UNCHANGED — both rules live inside @media (max-width: 720px).
```

### Captured run — 2026-09-21T19:18:35Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_03_species_glass.py tests/e2e/test_hs202_first_use_smoke.py tests/e2e/test_hs202_02_first_use_glass.py tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_09_connect_engine_glass.py tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs141_chair_geometry.py 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f5ece779f86701668836aa9df0ed52bb2d93eaf7

```text
....................................                                     [100%]
36 passed in 302.36s (0:05:02)
```

### Captured run — 2026-09-21T19:23:59Z

- **Command:** `bash -c set -o pipefail; cd web && npm run tokens:gate 2>&1 | tail -1 && npx vitest run src/desk/__tests__/hs202ChromeSpecies.test.tsx src/desk/surface/__tests__/wings.test.tsx --maxWorkers=2 2>&1 | tail -4; cd .. && HOME=$(mktemp -d) uv run python scripts/check_web_baseline.py --run 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f5ece779f86701668836aa9df0ed52bb2d93eaf7

```text
token gate: clean (11 allow-listed exceptions, all in use)
      Tests  29 passed (29)
   Start at  13:24:00
   Duration  1.03s (transform 340ms, setup 258ms, import 541ms, tests 131ms, environment 726ms)

Suite totals: 2745 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T19:25:18Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f5ece779f86701668836aa9df0ed52bb2d93eaf7

```text
......................................                                   [100%]
38 passed in 1.06s
```
