"""PHILO-13 B0 fences for the graph rig's opt-in native touch adapter."""
from __future__ import annotations

import pytest

from scripts import graph_walk as gw


def _ui_case(*steps: dict) -> dict:
    return {
        "setup": [],
        "trigger": {
            "kind": "ui",
            "action": "click",
            "selector": "#trigger",
            "adapter": "ui-pointer",
            "then": list(steps),
        },
    }


def test_ui_by_viewport_declares_touch_when_nested_trigger_then_uses_it() -> None:
    case = _ui_case({
        "kind": "ui",
        "action": "click_role",
        "role": "button",
        "name": "Continue",
        "adapter": "ui-by-viewport",
    })

    assert gw.case_uses_ui_by_viewport(case)
    assert gw.case_uses_ui_by_viewport({
        "setup": [],
        "trigger": {"kind": "api", "method": "GET", "path": "/state"},
    }) is False


class _TapPage:
    viewport_size = {"width": 393}

    def __init__(self) -> None:
        self.calls: list[str] = []

    def locator(self, _selector: str):
        page = self

        class Locator:
            first = None

            def tap(self, *, timeout: float) -> None:
                page.calls.append(f"tap:{timeout}")

            def click(self, *, timeout: float, button: str = "left") -> None:
                page.calls.append(f"click:{timeout}:{button}")

        locator = Locator()
        locator.first = locator
        return locator

    def get_by_role(self, _role: str, *, name: str, exact: bool):
        return self.locator(f"role={_role}:{name}:{exact}")


class _ZoneProbePage:
    viewport_size = {"width": 1440}

    def __init__(self, record: dict) -> None:
        self.record = record
        self.probe = {
            "id": "zone-1",
            "x": 120,
            "y": 200,
            "width": 260,
            "height": 96,
        }
        self.hit_args: list[dict] = []
        self.dispatch_snapshot: dict | None = None
        self.calls: list[tuple[float, float, str]] = []

        page = self

        class Mouse:
            def click(self, x: float, y: float, *, button: str) -> None:
                # The native event is the last operation. The evidence fields
                # must already be present if dispatch or a later step fails.
                page.dispatch_snapshot = dict(page.record)
                page.calls.append((x, y, button))

        self.mouse = Mouse()

    def locator(self, _selector: str):
        class Locator:
            first = None

            def wait_for(self, *, state: str, timeout: float) -> None:
                assert state == "visible"

            def bounding_box(self) -> dict[str, float]:
                return {"x": 0, "y": 0, "width": 400, "height": 300}

        locator = Locator()
        locator.first = locator
        return locator

    def evaluate(self, script: str, argument: dict) -> dict:
        if "__hsWorldZoneProbe" in script:
            return dict(self.probe)
        assert "__hsWorldHitProbe" in script
        self.hit_args.append(dict(argument))
        if argument["y"] == self.probe["y"] + 6:
            return {"type": "zone", "id": self.probe["id"]}
        return {"type": "background"}


def test_zone_context_menu_records_body_point_and_hit_before_native_dispatch() -> None:
    record: dict = {}
    page = _ZoneProbePage(record)

    result = gw._world_context_menu(
        page,
        {
            "kind": "ui",
            "action": "world_context_menu",
            "selector": ".desk-world-canvas",
            "world_ref": "zone-1",
            "world_target": "zone",
        },
        "ui-pointer",
        10_000.0,
        record,
    )

    assert page.hit_args == [{"x": 120.0, "y": 206.0, "ref": "zone-1", "target": "zone"}]
    assert page.calls == [(120.0, 206.0, "right")]
    assert page.dispatch_snapshot == {
        "world_ref": "zone-1",
        "world_target": "zone",
        "world_probe": page.probe,
        "point": {"x": 120.0, "y": 206.0},
        "world_hit_probe": {"type": "zone", "id": "zone-1"},
    }
    assert result["done"] is True


def test_trigger_then_flushes_completed_steps_before_a_later_timeout(tmp_path, monkeypatch) -> None:
    recorder = gw.Recorder(tmp_path / "observation.json", {})
    trigger = {
        "kind": "ui",
        "action": "click",
        "selector": "#trigger",
        "then": [
            {"kind": "ui", "action": "wait_for", "selector": "#open"},
            {"kind": "ui", "action": "wait_for", "selector": "#never"},
        ],
    }
    seen: list[str] = []

    def fake_run_step(step, page, hub, provenance, case=None, *, variables=None, **_kwargs):
        seen.append(step["selector"])
        if step["selector"] == "#never":
            raise gw.Blocked("later step timed out")
        return {"kind": "ui", "selector": step["selector"], "done": True}

    monkeypatch.setattr(gw, "run_step", fake_run_step)
    with pytest.raises(gw.Blocked, match="later step timed out"):
        gw._run_trigger_sequence(
            trigger,
            page=object(),
            hub=None,
            provenance={},
            case={},
            variables={},
            recorder=recorder,
        )

    assert seen == ["#trigger", "#open", "#never"]
    assert recorder.record["trigger"]["selector"] == "#trigger"
    assert recorder.record["trigger"]["then"] == [
        {"kind": "ui", "selector": "#open", "done": True},
    ]


def test_trigger_lifecycle_error_is_recorded_as_fail(tmp_path) -> None:
    """A real trigger response mismatch is a lifecycle failure, not setup block."""
    case = {
        "id": "philo13-trigger-lifecycle-failure",
        "applicability": "applicable",
        "setup": [],
        "trigger": {
            "kind": "api",
            "method": "POST",
            "path": "/missing-trigger-route",
            "body": {},
            "expect_status": 200,
            "adapter": "http-route",
        },
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_field", "path": "counts.unseen", "value": 1},
        },
        "completion_bound_s": 5,
        "viewports": [],
    }

    record = gw.calibrate(tmp_path, cases=[case], headless=True)[0]

    assert record["verdict"] == "fail"
    assert record["trigger_error"]["lifecycle"] == "fail"
    assert record["trigger_error"]["step"]["path"] == "/missing-trigger-route"
    assert "wanted 200" in record["trigger_error"]["error"]


def test_hit_test_probes_use_interior_points_for_rounded_sheet() -> None:
    """Both hit-test probes must sample the painted area of a 393px sheet."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 393, "height": 393})
        page = context.new_page()
        try:
            page.set_content(
                """
                <style>
                  html, body { margin: 0; width: 393px; height: 393px; }
                  #sheet {
                    width: 393px;
                    height: 393px;
                    border-radius: 32px;
                    overflow: hidden;
                    background: #d8e4ff;
                  }
                  #sheet > .surface {
                    width: 100%;
                    height: 100%;
                    background: #d8e4ff;
                  }
                </style>
                <div id="sheet"><div class="surface"></div></div>
                """
            )

            snapshot = page.evaluate(gw._SNAPSHOT_JS, ["#sheet", None, None])
            placement = page.evaluate(
                gw._PLACEMENT_ARM_JS, ["#sheet", [], None, None]
            )

            for hit in (snapshot["hit_test"], placement["card"]["hit_test"]):
                assert hit["all_owned"] is True
                assert len(hit["samples"]) == 9
                assert all(
                    0 < sample["x"] < 393 and 0 < sample["y"] < 393
                    for sample in hit["samples"]
                )
                assert all(sample["owned"] is True for sample in hit["samples"])
        finally:
            context.close()
            browser.close()


def test_ui_by_viewport_records_pointer_adapter_at_desktop_width() -> None:
    page = _TapPage()
    page.viewport_size = {"width": 1440}

    record = gw._ui_step(page, {
        "kind": "ui",
        "action": "click_role",
        "role": "button",
        "name": "Continue",
        "adapter": "ui-by-viewport",
    })

    assert page.calls == ["click:10000.0:left"]
    assert record["adapter"] == "ui-pointer"
    assert record["adapter_requested"] == "ui-by-viewport"


def test_ui_by_viewport_records_touch_adapter_and_uses_native_tap() -> None:
    page = _TapPage()

    record = gw._ui_step(page, {
        "kind": "ui",
        "action": "click",
        "selector": "#trigger",
        "adapter": "ui-by-viewport",
        "timeout_s": 2.5,
    })

    assert page.calls == ["tap:2500.0"]
    assert record["adapter"] == "ui-touch"
    assert record["adapter_requested"] == "ui-by-viewport"
    assert record["done"] is True


def test_ui_by_viewport_guarded_touch_blocks_before_synthetic_delivery() -> None:
    page = _TapPage()

    with pytest.raises(gw.Blocked, match="guarded synthetic delivery cannot claim touch"):
        gw._ui_step(page, {
            "kind": "ui",
            "action": "click",
            "selector": "#trigger",
            "adapter": "ui-by-viewport",
            "requires": {"visible": "#guard"},
        })

    assert page.calls == []


def test_world_context_menu_rejects_a_hold_shorter_than_product_long_press() -> None:
    page = _TapPage()

    with pytest.raises(gw.Blocked, match="500 ms long-press bound"):
        gw._ui_step(page, {
            "kind": "ui",
            "action": "world_context_menu",
            "selector": ".desk-world-canvas",
            "world_ref": "chain:c1",
            "adapter": "ui-by-viewport",
            "hold_ms": 499,
        })


def test_world_context_menu_uses_the_real_probe_and_native_touch_long_press() -> None:
    """The spatial door is a canvas gesture, so prove CDP touch events reach it."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 393, "height": 852},
            has_touch=True,
        )
        page = context.new_page()
        page.set_content(
            """
            <canvas id="world" class="desk-world-canvas" width="393" height="852"
                    style="display:block;width:393px;height:852px"></canvas>
            <script>
                  window.events = [];
                  window.__hsWorldProbe = () => [{ref: 'chain:c1', x: 120, y: 220}];
                  window.__hsWorldHitProbe = (x, y) => ({type: 'object', ref: 'chain:c1'});
                  const canvas = document.querySelector('#world');
              canvas.addEventListener('pointerdown', event => {
                window.events.push({name: 'down', pointerType: event.pointerType});
                setTimeout(() => { canvas.dataset.menu = 'open'; }, 500);
              });
              canvas.addEventListener('pointerup', event =>
                window.events.push({name: 'up', pointerType: event.pointerType}));
            </script>
            """
        )

        record = gw._ui_step(page, {
            "kind": "ui",
            "action": "world_context_menu",
            "selector": ".desk-world-canvas",
            "world_ref": "chain:c1",
            "adapter": "ui-by-viewport",
            "hold_ms": 550,
        })

        assert record["adapter"] == "ui-touch"
        assert record["gesture"] == "touch-long-press"
        assert record["world_ref"] == "chain:c1"
        assert record["point"] == {"x": 120.0, "y": 220.0}
        assert page.locator("#world").get_attribute("data-menu") == "open"
        events = page.evaluate("window.events")
        assert {event["name"] for event in events} == {"down", "up"}
        assert all(event["pointerType"] == "touch" for event in events)
        context.close()
        browser.close()


def test_world_context_menu_uses_the_real_probe_and_native_mouse_context_menu() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            has_touch=False,
        )
        page = context.new_page()
        page.set_content(
            """
            <canvas id="world" class="desk-world-canvas" width="1440" height="900"
                    style="display:block;width:1440px;height:900px"></canvas>
            <script>
              window.__hsWorldProbe = () => [{ref: 'chain:c1', x: 820, y: 240}];
              window.__hsWorldHitProbe = (x, y) => ({type: 'object', ref: 'chain:c1'});
              document.querySelector('#world').addEventListener('contextmenu', event => {
                event.preventDefault();
                document.querySelector('#world').dataset.menu = 'open';
              });
            </script>
            """
        )

        record = gw._ui_step(page, {
            "kind": "ui",
            "action": "world_context_menu",
            "selector": ".desk-world-canvas",
            "world_ref": "chain:c1",
            "adapter": "ui-by-viewport",
        })

        assert record["adapter"] == "ui-pointer"
        assert record["gesture"] == "mouse-right-click"
        assert page.locator("#world").get_attribute("data-menu") == "open"
        context.close()
        browser.close()


def test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events() -> None:
    """The adapter proof observes Chromium events, not a locator double."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 393, "height": 852},
            has_touch=True,
        )
        page = context.new_page()
        page.set_content(
            """
            <button id="trigger">Continue</button>
            <script>
              window.events = [];
              const button = document.querySelector('#trigger');
              for (const name of ['pointerdown', 'touchstart', 'pointerup', 'touchend', 'click']) {
                button.addEventListener(name, event => window.events.push({
                  name, pointerType: event.pointerType || null
                }));
              }
            </script>
            """
        )

        record = gw._ui_step(page, {
            "kind": "ui",
            "action": "click",
            "selector": "#trigger",
            "adapter": "ui-by-viewport",
        })

        events = page.evaluate("window.events")
        assert record["adapter"] == "ui-touch"
        assert {event["name"] for event in events} >= {
            "pointerdown", "pointerup", "click",
        }
        assert all(
            event["pointerType"] == "touch"
            for event in events
            if event["name"].startswith("pointer")
        )
        assert any(event["name"] == "touchstart" for event in events)
        assert any(event["name"] == "touchend" for event in events)
        context.close()
        browser.close()


def test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            has_touch=False,
        )
        page = context.new_page()
        page.set_content(
            """
            <button id="trigger">Continue</button>
            <script>
              window.events = [];
              const button = document.querySelector('#trigger');
              for (const name of ['pointerdown', 'pointerup', 'click']) {
                button.addEventListener(name, event => window.events.push({
                  name, pointerType: event.pointerType || null
                }));
              }
            </script>
            """
        )

        record = gw._ui_step(page, {
            "kind": "ui",
            "action": "click",
            "selector": "#trigger",
            "adapter": "ui-by-viewport",
        })

        events = page.evaluate("window.events")
        assert record["adapter"] == "ui-pointer"
        assert {event["name"] for event in events} >= {
            "pointerdown", "pointerup", "click",
        }
        assert all(
            event["pointerType"] == "mouse"
            for event in events
            if event["name"].startswith("pointer")
        )
        context.close()
        browser.close()
