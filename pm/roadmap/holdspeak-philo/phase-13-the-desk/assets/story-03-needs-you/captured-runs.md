> H-A2 partial delivery. The generated Status: done below is the capture template default, not a story certification. Story 03 remains in-progress until both halves merge. The original capture bytes follow this note unchanged.

# Evidence - PHILO-13-03

- **Story:** PHILO-13-03 - A2 — One meaning of "needs you"
- **Status:** done
- **Date:** 2026-10-01

## Proof

### Captured run — 2026-10-02T04:27:26Z

- **Command:** `python3 .tmp/philo-13-astra/a2-web-baseline.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
COMMAND uv run python scripts/check_web_baseline.py --run
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

BRANCH-NEW (1):
  BRANCH-NEW: src/features/project-room/steward/__tests__/StewardPosture.test.tsx > Scroll hint: data-scroll-hint is set on the posture root > sets data-scroll-hint on the steward posture element

Suite totals: 3028 passed, 1 failed, 0 skipped

VERDICT: BRANCH-NEW FAILURES: 1
```

### Captured run — 2026-10-02T04:30:52Z

- **Command:** `python3 .tmp/philo-13-astra/a2-web-baseline.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
COMMAND uv run python scripts/check_web_baseline.py --run
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 3029 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-10-02T04:32:33Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.dock.needs_you_week --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-03/dock-1440-old-build`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
PASS: live
BRAIN: astra
SOURCE: 65d55047f35017d1774486462797fc67c962c869 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:64400 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-k504vw4l/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-03/dock-1440-old-build/20261002T043233Z-case.p13.dock.needs_you_week-astra-1440/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'readable_text', 'value': '6'} at '.desk-dock-app[aria-label^="Intelligence"] .desk-dock-badge' — '6' NOT in observe_at text
```

### Captured run — 2026-10-02T04:33:15Z

- **Command:** `python3 .tmp/philo-13-astra/test-a2-python.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
COMMAND uv run pytest --collect-only -q tests/unit/test_philo13_needs_you_fixture.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_graph_walk.py
FULL OUTPUT .tmp/philo-13-astra/a2-python-collection.txt
.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_navigation_steps_carry_no_selector]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_desk_face_case_crosses_the_gate_first]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_captured_id_names_the_field_it_reads]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_ids_are_unique]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_validates_against_schema_and_openapi
tests/unit/test_philo13_astra_atlas.py::test_phase13_case_and_sibling_manifest_is_local
tests/unit/test_philo13_astra_atlas.py::test_needs_you_case_reads_six_before_real_mutation_and_five_after_reload
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_semantic_guards_show_red_then_green
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_operation_count_excludes_only_phase13_files
tests/unit/test_philo13_fixture_rig.py::test_repository_fixture_binds_scalars_and_restarts_the_owned_hub
tests/unit/test_philo13_fixture_rig.py::test_ingest_coder_fixture_uses_real_cli_and_records_question
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_dispatches_native_path_and_records_hash
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[1440-ui-pointer]
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[393-ui-touch]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[1440]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[393]
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_refuses_a_path_outside_owned_roots
tests/unit/test_philo13_fixture_rig.py::test_hub_environment_and_teardown_never_use_inherited_tmux_socket
tests/unit/test_philo13_fixture_rig.py::test_hub_tmux_teardown_does_not_mislabel_permission_error_as_no_server
tests/unit/test_philo13_fixture_rig.py::test_hub_tmux_teardown_records_success_and_bounded_stderr
tests/unit/test_philo13_fixture_rig.py::test_repository_router_passes_fixture_to_real_builder
tests/unit/test_philo13_fixture_rig.py::test_real_hub_reads_repository_and_coder_producers
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_declares_touch_when_nested_trigger_then_uses_it
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_pointer_adapter_at_desktop_width
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_touch_adapter_and_uses_native_tap
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_guarded_touch_blocks_before_synthetic_delivery
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events

146 tests collected in 0.35s

COMMAND uv run pytest -q tests/unit/test_philo13_needs_you_fixture.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_graph_walk.py
FULL OUTPUT .tmp/philo-13-astra/a2-python-run.txt
........................................................................ [ 49%]
............................................................FF.......... [ 98%]
FF                                                                       [100%]
=================================== FAILURES ===================================
__ test_real_browser_file_chooser_accepts_detached_input_at_both_widths[1440] __

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-141/test_real_browser_file_chooser0')
width = 1440

    @pytest.mark.parametrize("width", [1440, 393])
    def test_real_browser_file_chooser_accepts_detached_input_at_both_widths(
        tmp_path: Path, width: int,
    ) -> None:
        from playwright.sync_api import sync_playwright
    
        value = "tests/fixtures/philo13/calendar-input.png"
        with sync_playwright() as play:
>           browser = play.chromium.launch(headless=True)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo13_fixture_rig.py:243: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10ddbd010>
cb = <function Channel.send.<locals>.<lambda> at 0x10d788510>
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
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo13-a2-python-bsi202dw/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
__ test_real_browser_file_chooser_accepts_detached_input_at_both_widths[393] ___

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-141/test_real_browser_file_chooser1')
width = 393

    @pytest.mark.parametrize("width", [1440, 393])
    def test_real_browser_file_chooser_accepts_detached_input_at_both_widths(
        tmp_path: Path, width: int,
    ) -> None:
        from playwright.sync_api import sync_playwright
    
        value = "tests/fixtures/philo13/calendar-input.png"
        with sync_playwright() as play:
>           browser = play.chromium.launch(headless=True)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo13_fixture_rig.py:243: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10ddc2990>
cb = <function Channel.send.<locals>.<lambda> at 0x10d9962a0>
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
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo13-a2-python-bsi202dw/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
______ test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events ______

    def test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events() -> None:
        """The adapter proof observes Chromium events, not a locator double."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as play:
>           browser = play.chromium.launch(headless=True)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo13_graph_walk.py:118: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10e64d810>
cb = <function Channel.send.<locals>.<lambda> at 0x10e38d590>
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
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo13-a2-python-bsi202dw/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
_____ test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events _____

    def test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events() -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as play:
>           browser = play.chromium.launch(headless=True)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo13_graph_walk.py:166: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10e6c3230>
cb = <function Channel.send.<locals>.<lambda> at 0x10e3a45c0>
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
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo13-a2-python-bsi202dw/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
=========================== short test summary info ============================
FAILED tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[1440]
FAILED tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[393]
FAILED tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events
FAILED tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events
4 failed, 142 passed in 20.09s
```

### Captured run — 2026-10-02T04:34:49Z

- **Command:** `python3 .tmp/philo-13-astra/test-a2-python.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
COMMAND uv run pytest --collect-only -q tests/unit/test_philo13_needs_you_fixture.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_graph_walk.py
FULL OUTPUT .tmp/philo-13-astra/a2-python-collection.txt
.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_navigation_steps_carry_no_selector]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_desk_face_case_crosses_the_gate_first]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_captured_id_names_the_field_it_reads]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_ids_are_unique]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_validates_against_schema_and_openapi
tests/unit/test_philo13_astra_atlas.py::test_phase13_case_and_sibling_manifest_is_local
tests/unit/test_philo13_astra_atlas.py::test_needs_you_case_reads_six_before_real_mutation_and_five_after_reload
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_semantic_guards_show_red_then_green
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_operation_count_excludes_only_phase13_files
tests/unit/test_philo13_fixture_rig.py::test_repository_fixture_binds_scalars_and_restarts_the_owned_hub
tests/unit/test_philo13_fixture_rig.py::test_ingest_coder_fixture_uses_real_cli_and_records_question
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_dispatches_native_path_and_records_hash
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[1440-ui-pointer]
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[393-ui-touch]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[1440]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[393]
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_refuses_a_path_outside_owned_roots
tests/unit/test_philo13_fixture_rig.py::test_hub_environment_and_teardown_never_use_inherited_tmux_socket
tests/unit/test_philo13_fixture_rig.py::test_hub_tmux_teardown_does_not_mislabel_permission_error_as_no_server
tests/unit/test_philo13_fixture_rig.py::test_hub_tmux_teardown_records_success_and_bounded_stderr
tests/unit/test_philo13_fixture_rig.py::test_repository_router_passes_fixture_to_real_builder
tests/unit/test_philo13_fixture_rig.py::test_real_hub_reads_repository_and_coder_producers
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_declares_touch_when_nested_trigger_then_uses_it
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_pointer_adapter_at_desktop_width
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_touch_adapter_and_uses_native_tap
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_guarded_touch_blocks_before_synthetic_delivery
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events

146 tests collected in 0.29s

COMMAND uv run pytest -q tests/unit/test_philo13_needs_you_fixture.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_graph_walk.py
FULL OUTPUT .tmp/philo-13-astra/a2-python-run.txt
........................................................................ [ 49%]
........................................................................ [ 98%]
..                                                                       [100%]
146 passed in 17.29s
```

### Captured run — 2026-10-02T04:35:00Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.dock.needs_you_week --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-03/dock-1440-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
PASS: live
BRAIN: astra
SOURCE: 65d55047f35017d1774486462797fc67c962c869 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-zqpG_Lw0.js'] hub=http://127.0.0.1:49619 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-w23cyz6j/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-03/dock-1440-final/20261002T043501Z-case.p13.dock.needs_you_week-astra-1440/before.png', '.tmp/graph-walk/philo-13-03/dock-1440-final/20261002T043501Z-case.p13.dock.needs_you_week-astra-1440/after.png']
NOTE: predicate: '5' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 209, 'y': 862, 'w': 33, 'h': 27}
```

### Captured run — 2026-10-02T04:36:23Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.dock.needs_you_week --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-03/dock-393-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
PASS: live
BRAIN: astra
SOURCE: 65d55047f35017d1774486462797fc67c962c869 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-zqpG_Lw0.js'] hub=http://127.0.0.1:50398 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-469c_1hj/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-03/dock-393-final/20261002T043623Z-case.p13.dock.needs_you_week-astra-393/before.png', '.tmp/graph-walk/philo-13-03/dock-393-final/20261002T043623Z-case.p13.dock.needs_you_week-astra-393/after.png']
NOTE: predicate: '5' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 45, 'y': 741, 'w': 33, 'h': 27}
```

### Captured run — 2026-10-02T04:42:35Z

- **Command:** `python3 .tmp/philo-13-astra/test-a2-web.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 52c5bc5d778b5e1a0bedae23834ee66d3c22da0f

```text
COMMAND npx vitest run src/desk/needsYou.test.ts src/desk/attention.test.ts src/desk/chair/arrivalOneThing.test.tsx src/desk/chair/arrivalRefresh.test.tsx src/desk/chair/arrivalAttention.test.tsx src/desk/chair/arrivalQuietDesk.test.tsx src/desk/chair/arrivalCoverage.test.tsx --reporter=verbose

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-13-astra/web

 ✓ src/desk/attention.test.ts > ranking (AC2) > has the five classes in the ratified order and a cap of five 1ms
 ✓ src/desk/attention.test.ts > ranking (AC2) > ranks overdue, due today, not run, no due date, waiting — severity never reorders 1ms
 ✓ src/desk/attention.test.ts > ranking (AC2) > orders within each class by the ratified observable time 0ms
 ✓ src/desk/attention.test.ts > ranking (AC2) > tie-breaks on the stable id, deterministically 0ms
 ✓ src/desk/attention.test.ts > ranking (AC2) > trusts the wire's class when lawful and reads the facts otherwise 0ms
 ✓ src/desk/attention.test.ts > ranking (AC2) > sorts an unknown time last in its class 0ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > collapses three projections of one obligation into one traceable row 1ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > keeps the same title in two Projects as two obligations 0ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > joins a Door card to the one Project that names the same thing 0ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > counsel probe 1: distinct obligations with one title and one source never merge 0ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > the true cross-source case is one row whose sources each keep their title and way in 0ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > the shared fixture ranks and groups exactly as the Python side does 1ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > keeps the wire's own sources when merging a row that arrived merged 0ms
 ✓ src/desk/attention.test.ts > dedup (AC3) > normalises a leading ref, case and spacing 0ms
 ✓ src/desk/attention.test.ts > the tokens the face draws > reason token: the class, the source's detail, the observable age 0ms
 ✓ src/desk/attention.test.ts > the tokens the face draws > ages and observation stamps 0ms
 ✓ src/desk/attention.test.ts > the tokens the face draws > caption: the cap in the caption, never a zero 0ms
 ✓ src/desk/needsYou.test.ts > the one needs-you membership > counts a settled R1-R3 example once and preserves each ref 2ms
 ✓ src/desk/needsYou.test.ts > the one needs-you membership > keeps a retried job as RETRYING after its due time 1ms
 ✓ src/desk/needsYou.test.ts > the one needs-you membership > does not infer a missing engine from an absent roster row 0ms
 ✓ src/desk/needsYou.test.ts > the one needs-you membership > makes a failed assignment read unknown instead of clear 0ms
 ✓ src/desk/needsYou.test.ts > the shared needs-you read > paginates meetings by offset when the HTTP route omits next_cursor 61ms
 ✓ src/desk/needsYou.test.ts > the shared needs-you read > uses shared coverage semantics when complete is true over a failed row 55ms
 ✓ src/desk/needsYou.test.ts > the shared needs-you read > keeps the meeting-path blocker unknown when the roster read fails 55ms
 ✓ src/desk/chair/arrivalQuietDesk.test.tsx > HS-201-11 the head speaks one total > adds what asks outside the attention list 1ms
 ✓ src/desk/chair/arrivalQuietDesk.test.tsx > HS-201-11 the arrival head and its asking rows agree > counts the setup row, and the calendar offer beside it never moves it 27ms
 ✓ src/desk/chair/arrivalQuietDesk.test.tsx > HS-201-11 the arrival head and its asking rows agree > speaks the all-clear beside a calendar offer 6ms
 ✓ src/desk/chair/arrivalQuietDesk.test.tsx > HS-201-11 the arrival head and its asking rows agree > speaks the all-clear with the calendar connected too 6ms
 ✓ src/desk/chair/arrivalCoverage.test.tsx > Arrival coverage (HS-200-07 / C4) > says Nothing needs you only when the empty result is complete 21ms
 ✓ src/desk/chair/arrivalCoverage.test.tsx > Arrival coverage (HS-200-07 / C4) > never speaks the all-clear over an empty PARTIAL result 11ms
 ✓ src/desk/chair/arrivalCoverage.test.tsx > Arrival coverage (HS-200-07 / C4) > shows the coverage row beside healthy items and marks a remembered row 10ms
 ✓ src/desk/chair/arrivalCoverage.test.tsx > Arrival coverage (HS-200-07 / C4) > treats a read that never landed as a coverage gap, not as quiet 7ms
 ✓ src/desk/chair/arrivalCoverage.test.tsx > Arrival coverage (HS-200-07 / C4) > keeps the arrival honest at the narrow viewport rule (no prose row) 7ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 headline > never says the all-clear while something is pending 1ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > draws ONE row with ONE Button when no engine makes summaries 24ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > is gone once the summary capability is assigned 7ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > stays while only a global head exists (the queue cannot use it) 5ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > draws no setup row while the roster read is still in flight 5ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > names the unknown as its own row when the roster could not be read 9ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > draws a row when no engine transcribes speech 5ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > draws ONE row when neither engine is assigned 4ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 the Chair names the one thing > clears the speech row when the speech capability is assigned 4ms
 ✓ src/desk/chair/arrivalOneThing.test.tsx > HS-201-01 a microphone action never opens Models > draws no blocker row for a microphone primary_action 4ms
 ✓ src/desk/chair/arrivalRefresh.test.tsx > HS-201-01 the row clears on the OPEN desk > re-reads the roster when the window takes focus again 28ms
 ✓ src/desk/chair/arrivalRefresh.test.tsx > HS-201-01 the row clears on the OPEN desk > re-reads the roster on the product's settings-updated signal 12ms
 ✓ src/desk/chair/arrivalRefresh.test.tsx > HS-201-01 the row clears on the OPEN desk > re-reads the roster on the hub's desk_changed frame 314ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > headline: the true total; the Project clause only over several Projects 1ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > shows five rows with reason, source and one action; the caption carries the cap; the rest is reachable 434ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > draws the dedup disclosure naming every source of a merged row 95ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > draws exactly ONE filled primary on the whole face, and the selected filter is not it 51ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > states the ranking key on the face as a filter strip and filters by class 67ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > withholds the Project button over one Project and says `3 need you` 11ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > keeps coverage ABOVE the answer: each unreadable source with its reason, token, observation and verb 17ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > stamps a remembered row STILL TRUE with its observation, and never speaks the all-clear over a partial result 14ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > speaks the all-clear with the coverage chip only when complete 6ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > a Room commitment is one row with one lawful verb; the Door's card for it is not drawn twice 39ms
 ✓ src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) > Mark done is the verb only when owner and date are known, and it posts the explicit act 6ms
stdout | src/desk/needsYou.test.ts > the real producer membership oracle > matches before/after real wire and rejects controlled wrong projections
{"mutant":"count M1","rejection":"expected 7 to be 6 // Object.is equality","expectedCount":6,"actualCount":7,"expectedRefs":["philo13-a2-A1","A2 confirm the room commitment","philo13-a2-A3","philo13-a2-A4","blocker:engines","philo13-a2-failed-meeting"],"actualRefs":["A2 confirm the room commitment","M1 muted project attention","blocker:engines","philo13-a2-A1","philo13-a2-A3","philo13-a2-A4","philo13-a2-failed-meeting"]}
{"mutant":"retain A2 Door duplicate","rejection":"expected 7 to be 6 // Object.is equality","expectedCount":6,"actualCount":7,"expectedRefs":["philo13-a2-A1","A2 confirm the room commitment","philo13-a2-A3","philo13-a2-A4","blocker:engines","philo13-a2-failed-meeting"],"actualRefs":["A2 confirm the room commitment","action-0005000000000000","blocker:engines","philo13-a2-A1","philo13-a2-A3","philo13-a2-A4","philo13-a2-failed-meeting"]}
{"mutant":"drop R3 failed meeting","rejection":"expected 5 to be 6 // Object.is equality","expectedCount":6,"actualCount":5,"expectedRefs":["philo13-a2-A1","A2 confirm the room commitment","philo13-a2-A3","philo13-a2-A4","blocker:engines","philo13-a2-failed-meeting"],"actualRefs":["A2 confirm the room commitment","blocker:engines","philo13-a2-A1","philo13-a2-A3","philo13-a2-A4"]}

 ✓ src/desk/needsYou.test.ts > the shared needs-you read > retains the last Room rows after a later Room read fails 53ms
 ✓ src/desk/needsYou.test.ts > the shared needs-you read > shares one in-flight read between two mounted consumers 3ms
 ✓ src/desk/needsYou.test.ts > the real producer membership oracle > matches before/after real wire and rejects controlled wrong projections 3227ms

 Test Files  7 passed (7)
      Tests  60 passed (60)
   Start at  22:42:35
   Duration  4.37s (transform 2.23s, setup 1.02s, import 3.40s, tests 4.74s, environment 2.83s)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.21.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.21.0
npm notice To update run: npm install -g npm@11.21.0
npm notice

EXIT 0
COMMAND npx tsc --noEmit --pretty false
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.21.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.21.0
npm notice To update run: npm install -g npm@11.21.0
npm notice

EXIT 0
```
