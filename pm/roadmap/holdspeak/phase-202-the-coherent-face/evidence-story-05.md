# Evidence - HS-202-05

- **Story:** HS-202-05 - The type-scale ruling, then the tokens
- **Status:** done
- **Date:** 2026-09-21

## Proof

### Captured run — 2026-09-21T16:13:36Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HS202_05_CSS_DIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/css-head uv run pytest -q tests/e2e/test_hs202_05_button_hit_ownership.py::test_button_owns_44px_at_393 tests/e2e/test_hs202_05_disabled_stays_distinct.py -p no:randomly 2>&1 | tail -30`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
                    "disabled state and proves nothing about the others"
                )
    
            if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.locator(".pair").first.screenshot(
                    path=str(SHOTS / f"disabled-pair-{width}.png")
                )
            browser.close()
    
>       assert not failures, (
            f"the disabled Button is not distinct at {width}:\n  " + "\n  ".join(failures)
        )
E       AssertionError: the disabled Button is not distinct at 1440:
E           off-btn: the bevel survived (rgba(255, 255, 255, 0.07) 0px 1px 0px 0px inset); the disabled treatment is flat
E           off-btn: only ['cursor'] channel(s) separate it from on-btn; gray alone never states the disabled position
E           off-btn: the disabled label reads 4.21:1 on its own ground, under the ruling's 4.5:1
E           off-primary: the bevel survived (rgba(255, 255, 255, 0.22) 0px 1px 0px 0px inset, rgba(0, 0, 0, 0.3) 0px 1px 2px 0px); the disabled treatment is flat
E           off-primary: the disabled label reads 4.38:1 on its own ground, under the ruling's 4.5:1
E           off-sm: the bevel survived (rgba(255, 255, 255, 0.07) 0px 1px 0px 0px inset); the disabled treatment is flat
E           off-sm: only ['cursor'] channel(s) separate it from on-sm; gray alone never states the disabled position
E           off-sm: the disabled label reads 4.21:1 on its own ground, under the ruling's 4.5:1
E       assert not ['off-btn: the bevel survived (rgba(255, 255, 255, 0.07) 0px 1px 0px 0px inset); the disabled treatment is flat', "off...", 'off-sm: the bevel survived (rgba(255, 255, 255, 0.07) 0px 1px 0px 0px inset); the disabled treatment is flat', ...]

tests/e2e/test_hs202_05_disabled_stays_distinct.py:176: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_05_button_hit_ownership.py::test_button_owns_44px_at_393
FAILED tests/e2e/test_hs202_05_disabled_stays_distinct.py::test_disabled_button_stays_distinct[393]
FAILED tests/e2e/test_hs202_05_disabled_stays_distinct.py::test_disabled_button_stays_distinct[1440]
3 failed in 1.41s
```

### Captured run — 2026-09-21T16:13:45Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HS202_05_EXPORT_SHOTS=1 uv run pytest -q tests/e2e/test_hs202_05_button_hit_ownership.py tests/e2e/test_hs202_05_disabled_stays_distinct.py tests/e2e/test_hs202_05_first_use_type_floor.py -p no:randomly 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
......                                                                   [100%]
6 passed in 29.79s
```

### Captured run — 2026-09-21T16:14:25Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HS202_05_FAINT_OVERRIDE=#767e8d uv run pytest -q tests/e2e/test_hs202_05_first_use_type_floor.py -p no:randomly 2>&1 | grep -E "M8 [0-9]|failed|passed" | head -8`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
E           models@393 M8 4.38:1 < 4.5 at 11px on rgb(21, 23, 29): 'CHECKED 3:41 AM' (div#surface-concierge > div.desk-surface-body > div.concierge-root > div > div.concierge-hardware-row > span.concierge-checked-at)
E           models@393 M8 4.38:1 < 4.5 at 12px on rgb(21, 23, 29): 'Use these' (div#surface-concierge > footer.desk-surface-foot.surface-footer > div.surface-footer-layout.concierge-footer > div.surface-footer-verbs > button.btn.btn--secondary)
E       assert not ["models@393 M8 4.38:1 < 4.5 at 11px on rgb(21, 23, 29): 'CHECKED 3:41 AM' (div#surface-concierge > div.desk-surface-b...t.surface-footer > div.surface-footer-layout.concierge-footer > div.surface-footer-verbs > button.btn.btn--secondary)"]
E           models@1440 M8 4.38:1 < 4.5 at 11px on rgb(21, 23, 29): 'CHECKED 3:41 AM' (div#surface-concierge > div.desk-surface-body > div.concierge-root > div > div.concierge-hardware-row > span.concierge-checked-at)
E           models@1440 M8 4.38:1 < 4.5 at 12px on rgb(21, 23, 29): 'Use these' (div#surface-concierge > footer.desk-surface-foot.surface-footer > div.surface-footer-layout.concierge-footer > div.surface-footer-verbs > button.btn.btn--secondary)
E       assert not ["models@1440 M8 4.38:1 < 4.5 at 11px on rgb(21, 23, 29): 'CHECKED 3:41 AM' (div#surface-concierge > div.desk-surface-...t.surface-footer > div.surface-footer-layout.concierge-footer > div.surface-footer-verbs > button.btn.btn--secondary)"]
2 failed in 27.29s
```

### Captured run — 2026-09-21T16:14:59Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs202_02_first_use_glass.py -p no:randomly 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
...........................                                              [100%]
27 passed in 191.75s (0:03:11)
```

### Captured run — 2026-09-21T16:18:37Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_first_use_smoke.py -p no:randomly 2>&1 | grep -cE "^FAIL:" ; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_first_use_smoke.py -p no:randomly 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
0
..                                                                       [100%]
2 passed in 50.85s
```

### Captured run — 2026-09-21T16:20:30Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05/web && npm run check 2>&1 | grep -E "tokens.css and|token gate|architecture guard|Test Files|Tests |bundle gate|error TS" | head -10`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (808 source files; zero framework residue).
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯
 Test Files  1 failed | 289 passed (290)
      Tests  1 failed | 2721 passed (2722)
```

### Captured run — 2026-09-21T16:23:58Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05/web && npm run check 2>&1 | grep -E "tokens.css and|token gate|architecture guard|Test Files|Tests  |bundle gate|error TS|FAIL "`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (808 source files; zero framework residue).
 Test Files  290 passed (290)
      Tests  2722 passed (2722)
bundle gate passed (Desk JS 1310819 B; Desk CSS 316103 B; source maps 0)
```

### Captured run — 2026-09-21T16:28:30Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run python scripts/surface_census_walk.py --desk cold --widths 1440,393 --no-shots --out /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/census-cold2 --only app-chair --only app-meetings --only wing-meetings-review --only state-meetings-queued --only state-thought --only win-thought-workspace --only app-models --only app-settings --only settings-settings 2>&1 | tail -22`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
  hub pid=1547 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-cold-0c4t3nx0 port=56713

== cold desk @1440 ==
  MEASURED  app-chair                    M10, M7, M8, U1
  MEASURED  app-meetings                 U1
  MEASURED  app-settings                 U1
  MEASURED  app-models                   U1
  MEASURED  settings-settings            U1
  MEASURED  wing-meetings-review         M7, U1

== cold desk @393 ==
  MEASURED  app-chair                    M10, M7, M8, U1
  MEASURED  app-meetings                 M7, U1
  MEASURED  app-settings                 M7, U1
  MEASURED  app-models                   M7, U1
  MEASURED  settings-settings            M7, U1
  MEASURED  wing-meetings-review         M7, U1

report   /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/census-cold2/01-measured-walk.md
census   /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/a656696c-d9eb-491f-8d02-7b5a6518db89/scratchpad/census-cold2/census.json
shots    0
measured 12/12 legs
```

### Captured run — 2026-09-21T16:31:08Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs202_05_button_hit_ownership.py tests/e2e/test_hs202_05_disabled_stays_distinct.py tests/e2e/test_hs202_05_first_use_type_floor.py -p no:randomly 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 54f85b6195099cfaccbbf915a02c6e72c9877f34

```text
......                                                                   [100%]
6 passed in 29.55s
```
