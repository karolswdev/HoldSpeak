# PHILO-8-01 half A — the proof so far (not the story's evidence file)

The gate refuses `evidence-story-01.md` while the story is in progress (`dw check`: "evidence exists but matching story is not done"). These are the runs captured by `.githooks/dw evidence capture` for half A, moved here; the story's evidence file is written when the list face is built and the story closes.

- **Story:** PHILO-8-01 - The zone name and the rename where he is (canvas first)
- **Status:** in-progress (half A built; the list's in-row field waits on the owner's canvas word)
- **Date:** 2026-09-26

## Red on main (the fences before the repair)

Method: the six changed product files (`DeskApp.tsx`, `DeskMenuBar.tsx`, `DeskToolShelf.tsx`, `WorldStage.tsx`, `store/dataSlice.ts`, `verbRegistry.ts`) were written from `git show HEAD:<path>` (main 267f692a), the bundle rebuilt (`npm run build`, exit 0), and the SAME fence file run through the real hub on an isolated HOME; then the branch files were restored and rebuilt. 10 of 12 glass cases red; the 2 green are the `floor-chair-floor` guard leg (green on main: leaving the Floor blurs the open field and the blur commits it; kept as a guard for the face-change rule).

```text
E               AssertionError: stale rename field: list-to-spatial
E               AssertionError: 409s in the network log: [201, 409]
E               AssertionError: [201, 201, 409]
E               AssertionError: 409s in the network log: [201, 409]
E               AssertionError: [201, 201, 409]
E               AssertionError: 409s in the network log: [201, 409]
E               AssertionError: stale rename field: list-to-spatial
E               AssertionError: 409s in the network log: [201, 409]
PASSED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[393-floor-chair-floor]
PASSED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[1440-floor-chair-floor]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_the_chair_does_not_offer_new_zone[1440]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_the_chair_does_not_offer_new_zone[393]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[393-list-to-spatial]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-spatial]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_a_name_the_owner_chose_is_skipped_not_renamed[1440]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[393-spatial]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_a_name_the_owner_chose_is_skipped_not_renamed[393]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[393-list]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[1440-list-to-spatial]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-list]
10 failed, 2 passed in 75.23s (0:01:15)
```

Unit fences on main source: `zoneFreeName.test.ts`, `philo801ZoneVerbs.test.ts`, `DeskApp.test.tsx` → `8 failed | 17 passed (25)`; the 8 failures are every PHILO-8-01 behaviour case (next free name, two quick presses, the face change during the create, Retry refreshes first, the Chair withholds New Zone, only New Zone withheld, F2 on a zone on the Chair, the face change clears the rename). The `nextFreeZoneName` pure cases and "never replaces a passed name" pass on main by construction (main never replaced a name).

## C1 (the Astra-role check r1): the list-to-spatial fence waits for the create to land

The fence waited a fixed 600 ms, so on main under load it could pass. It now waits for the new zone's row (`New zone zone`, present only after the post-create refresh, which is the same turn that starts the rename on main) and for `.desk-world`, then checks the field is absent. Red on TRUE main under load: a `git archive` of origin/main 26f7b005 with this fence file laid in, real `npm ci --ignore-scripts && npm run build`, run in parallel with two other glass files (`-n 8`: this file + `test_philo7_delete_receipt_glass.py` + `test_philo8_04_empty_decision_heads_glass.py`, 16 cases):

```text
E               AssertionError: stale rename field: list-to-spatial
E               AssertionError: stale rename field: list-to-spatial
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[393-list-to-spatial]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[1440-list-to-spatial]
11 failed, 5 passed in 94.40s (0:01:34)
```

The same loaded run on the branch: `1 failed, 15 passed in 85.93s`; the one failure is `test_philo7_delete_receipt_glass.py::...[1440]` (`'Removal committed': not in the viewport`), which fails the same way on main under this load (story 02's area, not this story's). The zone file alone on the branch: `12 passed in 77.02s`. The fence's waits were raised to 15 s (one 5 s `.chair` wait timed out on the branch under load).

## Proof

### Captured run — 2026-09-26T16:27:39Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.cII3kUQTMg PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -n 6 tests/e2e/test_philo8_01_zone_name_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c98dff8d1f5c1da7d93e530e580789a9ef54bf5b

```text
bringing up nodes...
bringing up nodes...

............                                                             [100%]
12 passed in 74.95s (0:01:14)
```

### Captured run — 2026-09-26T16:29:00Z

- **Command:** `sh -c cd web && npx vitest run src/desk/store/__tests__/zoneFreeName.test.ts src/desk/__tests__/philo801ZoneVerbs.test.ts src/desk/DeskApp.test.tsx src/desk/__tests__/verbRegistry.test.ts src/desk/__tests__/commandDeck.test.tsx src/desk/__tests__/phoneDoors.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c98dff8d1f5c1da7d93e530e580789a9ef54bf5b

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-8-01/web


 Test Files  6 passed (6)
      Tests  51 passed (51)
   Start at  10:29:00
   Duration  1.51s (transform 1.49s, setup 543ms, import 2.45s, tests 872ms, environment 1.56s)
```
