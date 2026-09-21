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

### Captured run — 2026-09-21T19:02:38Z

- **Command:** `bash -c set -o pipefail; cd /Users/karol/dev/tools/wt-202-05 && echo "COUNSEL ROUND -- RED: the ember plate before the ink ramp (live first-use screens)"; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HS202_05_ACCENT_OVERRIDE=1 uv run pytest -q tests/e2e/test_hs202_05_first_use_type_floor.py -p no:randomly 2>&1 | grep -E "M8\[ember\]|failed|passed" | sed "s/ (div.*//;s/ (section.*//" | grep -v "f\\"" | head -16`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** e2173b16df804dee69083b14c0ef95afa96f0b98

```text
bash: -c: line 0: unexpected EOF while looking for matching `"'
bash: -c: line 1: syntax error: unexpected end of file
```

### Captured run — 2026-09-21T19:02:48Z

- **Command:** `./.tmp/hs202-05-red-ember.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e2173b16df804dee69083b14c0ef95afa96f0b98

```text
COUNSEL ROUND -- RED: the ember plate before the ink ramp, on the live first-use screens
E           arrival@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           meetings-ledger@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           meetings-record@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           thought@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           models@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           settings@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E       assert not ["arrival@393 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           arrival@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           meetings-ledger@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           meetings-record@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           thought@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           models@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E           settings@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
E       assert not ["arrival@1440 M8[ember] 3.79:1 < 4.5 at 9px rgb(242, 243, 245) on rgb(168, 110, 74): 'Talk'
2 failed in 28.91s
```

### Captured run — 2026-09-21T19:03:27Z

- **Command:** `./.tmp/hs202-05-green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e2173b16df804dee69083b14c0ef95afa96f0b98

```text
COUNSEL ROUND -- GREEN: contrast, floor, hit contract and chrome rows on the live first-use screens
....HIT CONTRACT 393: 42 reachable plated Button observations, every one owning its nine points at 44x44; 27 skipped as occluded by a window in front
HALO UNDER A LAYER IN FRONT (ledger, not a clip): meetings-ledger@393 'Generate' halo runs under the layer in front at (0,1)->desk-pullout-head desk-window-handle has-wings, (-1,1)->desk-pullout-head desk-window-handle has-wings, (1,1)->desk-pullout-head desk-window-handle has-wings
CHROME ROWS 393: dock chip x86 min 22px max 44px
CHROME ROWS 393: wing tab x10 min 23px max 23px
FLOOR LEDGER 393: 51 of 51 recorded consumers still under 12.0px; 0 healed
.FLOOR LEDGER 1440: 58 of 58 recorded consumers still under 12.0px; 0 healed
6 passed in 32.19s
```

### Captured run — 2026-09-21T19:04:10Z

- **Command:** `./.tmp/hs202-05-rigs.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e2173b16df804dee69083b14c0ef95afa96f0b98

```text
COUNSEL ROUND -- the four named rigs + HS-202-01's first-use smoke, on the ink ramp
.............................                                            [100%]
29 passed in 252.00s (0:04:12)
```

### Captured run — 2026-09-21T19:08:37Z

- **Command:** `./.tmp/hs202-05-check.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e2173b16df804dee69083b14c0ef95afa96f0b98

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (808 source files; zero framework residue).
 Test Files  290 passed (290)
      Tests  2722 passed (2722)
bundle gate passed (Desk JS 1310819 B; Desk CSS 316091 B; source maps 0)
```

### Captured run — 2026-09-21T19:10:29Z

- **Command:** `./.tmp/hs202-05-probe.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e2173b16df804dee69083b14c0ef95afa96f0b98

```text
COUNSEL ROUND finding 3 -- the three dead --font-sans shorthands, probed before/after
consumer                                         BEFORE (--font-sans undefined)               AFTER (alias -> --font-ui)
surface.css:2979 .model-library-row-copy strong  13px / 400 / Inter                           13px / 600 / Inter  CHANGED
surface.css:3016 .model-library-repair           13px / 400 / Inter                           12px / 500 / Inter  CHANGED
surface.css:2984 .model-library-row-copy small   12px / 500 / "JetBrains Mono"                12px / 500 / "JetBrains Mono"  same
surface.css:3109 .model-library-add-choices > button 13px / 400 / Inter                           13px / 600 / Inter  CHANGED
```

### Captured run — 2026-09-21T19:44:39Z

- **Command:** `./.tmp/r2-red-hit.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 935133c5a4e9ee571ca7b2c390de1038b48dab00

```text
ROUND 2 RED -- reintroduce BOTH instrument defects and watch the fences fail
both defects reintroduced
                        f"NEGATIVE CONTROL {control}: {why} appeared to own its whole "
                        f"NEGATIVE CONTROL {control}: {why} filed a lost point as "
                        f"NEGATIVE CONTROL: no control produced {branch!r} "
NEGATIVE CONTROL: no control produced 'miss:body' (saw ['miss:sibling']); that branch is unproven
NEGATIVE CONTROL: no control produced 'miss:ancestor' (saw ['miss:sibling']); that branch is unproven
assert not ["NEGATIVE CONTROL: no control produced 'miss:body' (saw ['miss:sibling']); that branch is unproven", "NEGATIVE CONTROL: no control produced 'miss:ancestor' (saw ['miss:sibling']); that branch is unproven"]
                                f"SELF-TEST {control}: a Button with no reachable halo "
                                f"SELF-TEST {control}: a lost point was filed as "
                            "SELF-TEST ink: a muted label on --accent-ink classified as "
                            f"SELF-TEST ink: the probe did not paint --accent-ink "
(repaired readers restored)
```

### Captured run — 2026-09-21T19:45:21Z

- **Command:** `./.tmp/r2-red-hit.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 935133c5a4e9ee571ca7b2c390de1038b48dab00

```text
ROUND 2 RED -- reintroduce BOTH instrument defects and watch the fences fail
both defects reintroduced
NEGATIVE CONTROL: no control produced 'miss:body' (saw ['miss:sibling']); that branch is unproven
NEGATIVE CONTROL: no control produced 'miss:ancestor' (saw ['miss:sibling']); that branch is unproven
assert not ["NEGATIVE CONTROL: no control produced 'miss:body' (saw ['miss:sibling']); that branch is unproven", "NEGATIVE CONTROL: no control produced 'miss:ancestor' (saw ['miss:sibling']); that bra
                    f"ancestor clip, same-layer neighbour): 0 — any would have failed."
SELF-TEST ink: a muted label on --accent-ink classified as 'other' at 2.27:1 (accent fills seen: ['#a86e4a', '#bc8058', '#936041', '#da9868']); the ember gate does not cover the new plate, so it canno
assert not ["SELF-TEST ink: a muted label on --accent-ink classified as 'other' at 2.27:1 (accent fills seen: ['#a86e4a', '#bc8058', '#936041', '#da9868']); the ember gate does not cover the new plate
HIT CONTRACT 393: 69 visible plated Button observations = 27 occluded (centre not owned, skipped) + 42 probed. Of the probed: 41 own ALL nine points of their 44x44 area, 1 own fewer because a layer in
                    f"ancestor clip, same-layer neighbour): 0 — any would have failed."
SELF-TEST ink: a muted label on --accent-ink classified as 'other' at 2.27:1 (accent fills seen: ['#a86e4a', '#bc8058', '#936041', '#da9868']); the ember gate does not cover the new plate, so it canno
assert not ["SELF-TEST ink: a muted label on --accent-ink classified as 'other' at 2.27:1 (accent fills seen: ['#a86e4a', '#bc8058', '#936041', '#da9868']); the ember gate does not cover the new plate
3 failed, 1 passed, 2 warnings in 29.71s
(repaired readers restored)
```

### Captured run — 2026-09-21T19:46:01Z

- **Command:** `./.tmp/r2-green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 935133c5a4e9ee571ca7b2c390de1038b48dab00

```text
ROUND 2 GREEN -- the six tests with the repaired readers and their self-tests
....SELF-TEST: hit probes lost their points as {'clipped': ['own', 'miss:ancestor'], 'bare': ['miss:ancestor']}; ember probe rgb(155, 162, 176) on rgb(138, 90, 61) classified ember at 2.27:1 (gate covers 7 accent fills)
HIT CONTRACT 393: 69 visible plated Button observations = 27 occluded (centre not owned, skipped) + 42 probed. Of the probed: 41 own ALL nine points of their 44x44 area, 1 own fewer because a layer in front covers the rest (ledgered below). Misses (body, ances
HALO UNDER A LAYER IN FRONT (ledger, not a clip): meetings-ledger@393 'Generate' halo runs under the layer in front at (0,1)[covered]->desk-pullout-head desk-window-handle has-wings, (-1,1)[covered]->desk-pullout-head desk-window-handle has-wings, (1,1)[covere
CHROME ROWS 393: dock chip x86 min 22px max 44px
CHROME ROWS 393: wing tab x10 min 23px max 23px
FLOOR LEDGER 393: 51 of 51 recorded consumers still under 12.0px; 0 healed
.SELF-TEST: hit probes lost their points as {'clipped': ['miss:sibling'], 'bare': ['miss:sibling']}; ember probe rgb(155, 162, 176) on rgb(138, 90, 61) classified ember at 2.27:1 (gate covers 7 accent fills)
FLOOR LEDGER 1440: 58 of 58 recorded consumers still under 12.0px; 0 healed
6 passed, 2 warnings in 30.51s
```

### Captured run — 2026-09-21T19:46:44Z

- **Command:** `./.tmp/r2-rigs.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 935133c5a4e9ee571ca7b2c390de1038b48dab00

```text
ROUND 2 -- the four named rigs + HS-202-01's first-use smoke, on the repaired revision
.............................                                            [100%]
29 passed in 246.55s (0:04:06)
(HS-202-01 fence removed again)
```

### Captured run — 2026-09-21T19:51:01Z

- **Command:** `./.tmp/r2-check.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 935133c5a4e9ee571ca7b2c390de1038b48dab00

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (808 source files; zero framework residue).
 Test Files  290 passed (290)
      Tests  2722 passed (2722)
bundle gate passed (Desk JS 1310819 B; Desk CSS 316091 B; source maps 0)
```
