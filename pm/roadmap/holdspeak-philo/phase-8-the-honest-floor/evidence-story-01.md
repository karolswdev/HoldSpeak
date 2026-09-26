# Evidence - PHILO-8-01

- **Story:** PHILO-8-01 - The zone name and the rename where he is (canvas first)
- **Status:** done
- **Date:** 2026-09-26

## Red on main 808a9c30 (half B fences, before the build)

The branch was cut from main 808a9c30 and the new glass file run BEFORE any product change (real `npm run build`, real hub, isolated HOME): 14 of 14 red. The list draws no field (10 cases wait for `input.desk-zone-rename` in vain), the Floor shows the sentence and no chip (2), no write receipt after a late refusal (2). The 4 failed-save cases are red through the missing list field, not through a separate Floor run.

```text
  10 E             - waiting for locator("input.desk-zone-rename") to be visible
   2 E             - waiting for locator("[data-testid=zone-name-refused]") to be visible
   2 E             - waiting for locator(".write-receipt").filter(has_text="RENAME ZONE").first to be visible
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_the_list_field_opens_writes_and_keeps[393]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_the_list_field_opens_writes_and_keeps[1440]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_f2_on_a_focused_zone_row_opens_the_field[393]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_f2_on_a_focused_zone_row_opens_the_field[1440]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_list[393]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_list[1440]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[393]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[393]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-network]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-422]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-network]
   1 FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-422]
   1 14 failed in 143.70s (0:02:23)
```

Unit fences on main source (`dataSlice.ts`, `DeskApp.tsx`, `store/types.ts`, `store/index.ts` written from `git show HEAD:`; restored after): `zoneRenameRefusal.test.ts` + `DeskApp.test.tsx` → `6 failed | 12 passed (18)` — every refusal case (409, 422, network, 500, the late refusal, the face change with a standing refusal); the 200 case passes on main by construction.

The first capture below (exit 1) ran both zone glass files at `-n 6` and had two failures of different kinds (corrected on the Astra-role check r1 on PR #673, C1): (1) a LOAD timeout on a POST response wait (`test_two_new_zone_presses_make_two_zones[1440-spatial]`; green serially); (2) a DETERMINISTIC failure of the half-A list-to-spatial leg, which waited for the row's name BUTTON that half B replaces with the field, so it could not pass on half B at any load. The leg now waits for the button or the field; the files were rerun at `-n 4`: 26 passed.

## Proof

### Captured run — 2026-09-26T19:05:41Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.joLQDZ9rWp PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q -n 6 -p no:cacheprovider tests/e2e/test_philo8_01_list_rename_glass.py tests/e2e/test_philo8_01_zone_name_glass.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** bd7ac95e4a866e0b283c5e2534b15ea2dcc3f061

```text
bringing up nodes...
bringing up nodes...

.........F..............F.                                               [100%]
=================================== FAILURES ===================================
___ TestZoneNameGlass.test_two_new_zone_presses_make_two_zones[1440-spatial] ___
[gw4] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-01/.venv/bin/python

self = <tests.e2e.test_philo8_01_zone_name_glass.TestZoneNameGlass object at 0x10a689f90>
width = 1440, face = 'spatial'

    @pytest.mark.e2e
    @pytest.mark.parametrize("face", ["spatial", "list"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_two_new_zone_presses_make_two_zones(self, width: int, face: str) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, statuses, errors = self._open(pw, width)
            try:
                page.locator("[data-testid=chair-floor-toggle]").click()
                _ensure_view(page, face)
                first = _new_zone(page)
>               second = _new_zone(page)
                         ^^^^^^^^^^^^^^^

tests/e2e/test_philo8_01_zone_name_glass.py:124: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_01_zone_name_glass.py:73: in _new_zone
    with page.expect_response(
.venv/lib/python3.14/site-packages/playwright/_impl/_sync_base.py:85: in __exit__
    self._event.value
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._sync_base.EventInfo object at 0x115cc02b0>

    @property
    def value(self) -> T:
        while not self._future.done():
            self._sync_base._dispatcher_fiber.switch()
        asyncio._set_running_loop(self._sync_base._loop)
        exception = self._future.exception()
        if exception:
>           raise exception
E           playwright._impl._errors.TimeoutError: Timeout 15000ms exceeded while waiting for event "response"

.venv/lib/python3.14/site-packages/playwright/_impl/_sync_base.py:59: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestZoneNameGlass.test_no_stale_rename_field_after_a_face_change[393-list-to-spatial] _
[gw2] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-01/.venv/bin/python

self = <tests.e2e.test_philo8_01_zone_name_glass.TestZoneNameGlass object at 0x10a335310>
width = 393, leg = 'list-to-spatial'

    @pytest.mark.e2e
    @pytest.mark.parametrize("leg", ["list-to-spatial", "floor-chair-floor"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_no_stale_rename_field_after_a_face_change(self, width: int, leg: str) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, statuses, errors = self._open(pw, width)
            try:
                page.locator("[data-testid=chair-floor-toggle]").click()
                if leg == "list-to-spatial":
                    # FINDING Finding 1: the list, then Spatial view.
                    _ensure_view(page, "list")
                    assert _new_zone(page) == 201
                    # C1 (Astra-role check r1): wait for the create to LAND before the
                    # face change. The new zone's row appears only after the post-create
                    # refresh, and createPrimitive starts the rename in the same turn
                    # (dataSlice.ts createPrimitive), so on main the stale state is set
                    # by now and the Floor draws it at mount. A fixed sleep let a slow
                    # refresh hide the defect (green on main under load).
>                   page.get_by_role("button", name="New zone zone", exact=True).wait_for(timeout=30_000)

tests/e2e/test_philo8_01_zone_name_glass.py:213: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.14/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.14/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x11ac596a0>
cb = <function Channel.send.<locals>.<lambda> at 0x11affde80>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
E           Call log:
E             - waiting for get_by_role("button", name="New zone zone", exact=True) to be visible

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-spatial]
FAILED tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[393-list-to-spatial]
2 failed, 24 passed in 229.63s (0:03:49)
```

### Captured run — 2026-09-26T19:11:20Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HuBMsMG02L PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q -n 4 -p no:cacheprovider tests/e2e/test_philo8_01_list_rename_glass.py tests/e2e/test_philo8_01_zone_name_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bd7ac95e4a866e0b283c5e2534b15ea2dcc3f061

```text
bringing up nodes...
bringing up nodes...

..........................                                               [100%]
26 passed in 263.89s (0:04:23)
```

### Captured run — 2026-09-26T19:15:51Z

- **Command:** `sh -c cd web && npx vitest run src/desk/store/__tests__/zoneRenameRefusal.test.ts src/desk/store/__tests__/zoneFreeName.test.ts src/desk/__tests__/philo801ZoneVerbs.test.ts src/desk/DeskApp.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bd7ac95e4a866e0b283c5e2534b15ea2dcc3f061

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-8-01/web


 Test Files  4 passed (4)
      Tests  32 passed (32)
   Start at  13:15:51
   Duration  872ms (transform 840ms, setup 326ms, import 1.11s, tests 342ms, environment 1.02s)
```

### Captured run — 2026-09-26T19:15:52Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.VcDUFfPcoI uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bd7ac95e4a866e0b283c5e2534b15ea2dcc3f061

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2898 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-26T19:54:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.5vmMsr1JD6 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q -n 4 -p no:cacheprovider tests/e2e/test_philo8_01_list_rename_glass.py tests/e2e/test_philo8_01_zone_name_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0ecd076d1d633738bd5926c901a72047afe47622

```text
bringing up nodes...
bringing up nodes...

..............................                                           [100%]
30 passed in 309.45s (0:05:09)
```
