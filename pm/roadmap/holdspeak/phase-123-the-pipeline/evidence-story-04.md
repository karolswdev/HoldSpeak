# Evidence - HS-123-04

- **Story:** HS-123-04 - Ask and decisions
- **Status:** done
- **Date:** 2026-08-06

## Proof

### Captured run — 2026-08-07T01:52:03Z

- **Command:** `uv run pytest -q`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 5031425ff6622cef5c93be348b9a5ad86491d9a0

```text
ssssssssssssssssssssssFFFssssssssss..ssssssssssssssss..............EEEEE [  1%]
EEEEEEEEE....F.............................................F...FF....... [  3%]
.............................................F..s......F............FFFF [  4%]
F........FFF..FFF.F.FF.................................................. [  6%]
.........FF.....F............F...........ssFFF.FF.FFFFFFF............... [  7%]
...............F.F.............F......................................F. [  9%]
F.........FFF..F..FFFFFFFFFFFF.FFFF..FF.F.F...F.......................FF [ 10%]
...........FFFFFF.FF..F..........F......FFFF...FFFFFF.FF...F.FFFFFFFFFFF [ 12%]
FFFFFFFFFFFFFFFF.FFFFFF.FF.F.F..FFFFFFFFFF.....F.....FFF.FF............. [ 13%]
........................................................F............... [ 15%]
............F..............................F...FFFFFF.F..F....FF.F.FF..F [ 17%]
...........F.FFF............FFFFFFFFF.FFFFFFF.........F.F............... [ 18%]
..............................F......FF..F.......F...........F.......... [ 20%]
...............................................................F.F...... [ 21%]
........................................................................ [ 23%]
........................................................................ [ 24%]
........................................................................ [ 26%]
........................................................................ [ 27%]
.....................F...............................FF................. [ 29%]
...........................................F............................ [ 30%]
....................................................................F... [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 40%]
..................................F..................................... [ 41%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 46%]
.............................................................F...F..F... [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 55%]
...............................F..........F............................. [ 57%]
........................................................................ [ 58%]
...................................F.................................... [ 60%]
...............................................................FFFF..... [ 61%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 68%]
..................F..................................................... [ 69%]
..........F...F..F.............F........................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 74%]
..........................FF..................F......................... [ 75%]
...........................................FF........................... [ 77%]
........................................................................ [ 78%]
.................................................FF..FF.F............... [ 80%]
....F............F...................................................... [ 82%]
.............................................F..FFF..................... [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 92%]
......F.............................F..F.FFFFF..FF...................... [ 94%]
........................................................................ [ 95%]
.........................................................FF............. [ 97%]
.............................................F.....FF................... [ 99%]
...........................................                              [100%]
==================================== ERRORS ====================================
_ ERROR at setup of TestWorkbenchWalk.test_desk_with_workbench_objects[desktop] _

request = <SubRequest 'walk_page' for <Function test_desk_with_workbench_objects[desktop]>>

    @pytest.fixture(params=VIEWPORTS, ids=lambda v: v["name"])
    def walk_page(request):
        """A Playwright page at the requested viewport, pointed at the hub."""
        from playwright.sync_api import sync_playwright
    
        viewport = request.param
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=2,
            )
            page = context.new_page()
>           page.goto(HUB_URL, wait_until="networkidle")

tests/e2e/test_workbench_walk.py:47: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:9050: in goto
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:552: in goto
    return await self._main_frame.goto(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:153: in goto
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x120458550>
cb = <function Channel.send.<locals>.<lambda> at 0x11f891440>
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
E           playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8778/
E           Call log:
E             - navigating to "http://localhost:8778/", waiting until "networkidle"

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
_ ERROR at setup of TestWorkbenchWalk.test_desk_with_workbench_objects[mobile] _

request = <SubRequest 'walk_page' for <Function test_desk_with_workbench_objects[mobile]>>

    @pytest.fixture(params=VIEWPORTS, ids=lambda v: v["name"])
    def walk_page(request):
        """A Playwright page at the requested viewport, pointed at the hub."""
        from playwright.sync_api import sync_playwright
    
        viewport = request.param
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=2,
            )
            page = context.new_page()
>           page.goto(HUB_URL, wait_until="networkidle")

tests/e2e/test_workbench_walk.py:47: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:9050: in goto
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:552: in goto
    return await self._main_frame.goto(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:153: in goto
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x120496060>
cb = <function Channel.send.<locals>.<lambda> at 0x120473920>
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
E           playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8778/
E           Call log:
E             - navigating to "http://localhost:8778/", waiting until "networkidle"

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
______ ERROR at setup of TestWorkbenchWalk.test_workbenches_home[desktop] ______

request = <SubRequest 'walk_page' for <Function test_workbenches_home[desktop]>>

    @pytest.fixture(params=VIEWPORTS, ids=lambda v: v["name"])
    def walk_page(request):
        """A Playwright page at the requested viewport, pointed at the hub."""
        from playwright.sync_api import sync_playwright
    
        viewport = request.param
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=2,
            )
            page = context.new_page()
>           page.goto(HUB_URL, wait_until="networkidle")

tests/e2e/test_workbench_walk.py:47: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:9050: in goto
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:552: in goto
    return await self._main_frame.goto(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:153: in goto
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x11f8090f0>
cb = <function Channel.send.<locals>.<lambda> at 0x11feb6a20>
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
E           playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8778/
E           Call log:
E             - navigating to "http://localhost:8778/", waiting until "networkidle"

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
______ ERROR at setup of TestWorkbenchWalk.test_workbenches_home[mobile] _______

request = <SubRequest 'walk_page' for <Function test_workbenches_home[mobile]>>

    @pytest.fixture(params=VIEWPORTS, ids=lambda v: v["name"])
    def walk_page(request):
        """A Playwright page at the requested viewport, pointed at the hub."""
        from playwright.sync_api import sync_playwright
    
        viewport = request.param
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=2,
            )
            page = context.new_page()
>           page.goto(HUB_URL, wait_until="networkidle")

tests/e2e/test_workbench_walk.py:47: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:9050: in goto
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:552: in goto
    return await self._main_frame.goto(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:153: in goto
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x12043d7f0>
cb = <function Channel.send.<locals>.<lambda> at 0x11f840540>
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
E           playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8778/
E           Call log:
E             - navigating to "http://localhost:8778/", waiting until "networkidle"

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
______ ERROR at setup of TestWorkbenchWalk.test_template_picker[desktop] _______

request = <SubRequest 'walk_page' for <Function test_template_picker[desktop]>>

    @pytest.fixture(params=VIEWPORTS, ids=lambda v: v["name"])
    def walk_page(request):
        """A Playwright page at the requested viewport, pointed at the hub."""
        from playwright.sync_api import sync_playwright
    
        viewport = request.param
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=2,
            )
            page = context.new_page()
>           page.goto(HUB_URL, wait_until="networkidle")

tests/e2e/test_workbench_walk.py:47: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:9050: in goto
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:552: in goto
    return await self._main_frame.goto(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:153: in goto
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x12048f9b0>
cb = <function Channel.send.<locals>.<lambda> at 0x120447b00>
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
E           playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8778/
E           Call log:
E             - navigating to "http://localhost:8778/", waiting until "networkidle"

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: Error
_______ ERROR at setup of TestWorkbenchWalk.test_template_picker[mobile] _______

request = <SubRequest 'walk_page' for <Function test_template_picker[mobile]>>

    @pytest.fixture(params=VIEWPORTS, ids=lambda v: v["name"])
    def walk_page(request):
        """A Playwright page at the requested viewport, pointed at the hub."""
        from playwright.sync_api import sync_playwright
    
        viewport = request.param
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=2,
            )
            page = context.new_page()
>           page.goto(HUB_URL, wait_until="networkidle")

tests/e2e/test_workbench_walk.py:47: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:9050: in goto
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:552: in goto
    return await self._main_frame.goto(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:153: in goto
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_a
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-07T02:06:52Z

- **Command:** `zsh -c uv run python -m py_compile holdspeak/services/ask_service.py holdspeak/services/decision_lifecycle_service.py holdspeak/web/routes/primitives/ask.py holdspeak/web/routes/decisions.py && rg -n "class (AskService|DecisionLifecycleService)|def (list_models|resolve_grounding|ask|keep|list_decisions|get_decision|get_moment|transition|supersede|promote|draft_promoted_with_model)" holdspeak/services && ! rg -n "get_database\(|ctx\.get_database" holdspeak/web/routes/primitives/ask.py holdspeak/web/routes/decisions.py && ! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/ask_service.py holdspeak/services/decision_lifecycle_service.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5031425ff6622cef5c93be348b9a5ad86491d9a0

```text
holdspeak/services/recipe_service.py:298:    def keep(
holdspeak/services/primitive_service.py:83:    def list_decisions(self, principal: Principal) -> list[dict[str, Any]]:
holdspeak/services/primitive_service.py:86:    def get_decision(self, principal: Principal, decision_id: str) -> dict[str, Any]:
holdspeak/services/primitive_service.py:142:    def supersede_decision(
holdspeak/services/decision_lifecycle_service.py:11:class DecisionLifecycleService:
holdspeak/services/decision_lifecycle_service.py:14:    def list_decisions(self, principal: Principal, *, project_id: str | None = None, project_key: str | None = None, meeting_id: str | None = None, lifecycle: str | None = None, limit: int = 200, offset: int = 0) -> dict[str, Any]:
holdspeak/services/decision_lifecycle_service.py:20:    def get_decision(self, principal: Principal, decision_id: str) -> dict[str, Any]:
holdspeak/services/decision_lifecycle_service.py:27:    def get_moment(self, principal: Principal, decision_id: str) -> dict[str, Any]:
holdspeak/services/decision_lifecycle_service.py:34:    def transition(self, principal: Principal, decision_id: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
holdspeak/services/decision_lifecycle_service.py:46:    def supersede(self, principal: Principal, decision_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
holdspeak/services/decision_lifecycle_service.py:53:    def promote(self, principal: Principal, decision_id: str, artifact_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
holdspeak/services/decision_lifecycle_service.py:58:    async def draft_promoted_with_model(self, principal: Principal, decision_id: str, artifact_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
holdspeak/services/ask_service.py:21:class AskService:
holdspeak/services/ask_service.py:27:    def list_models(self, principal: Principal) -> list[dict[str, Any]]:
holdspeak/services/ask_service.py:46:    def resolve_grounding(self, principal: Principal, refs: list[str]) -> dict[str, Any]:
holdspeak/services/ask_service.py:56:    async def ask(self, principal: Principal, question: str, grounding: Any = None, *, lens: str = "Ask", context: list[dict[str, Any]] | None = None, model: str | None = None, inference_target_id: str | None = None, profile_id: str | None = None, max_tokens: Any = None, temperature: Any = None) -> dict[str, Any]:
holdspeak/services/ask_service.py:104:    def keep(self, principal: Principal, output: str, sources: list[dict[str, Any]], *, lens: str = "Ask", prompt: str = "", grounding: Any = None) -> dict[str, Any]:
holdspeak/services/workbench_service.py:263:    def promote_memory(self, principal: Principal, workbench_id: str, index: int) -> dict[str, Any]:
```
