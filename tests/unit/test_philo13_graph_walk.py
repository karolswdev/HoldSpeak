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
