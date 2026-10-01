"""Focused fences for the graph-walk native select action.

The locator test checks command wiring only: it proves the exact selector and
option value reach Playwright's native ``select_option`` call. It does not
claim that a page field changed; that belongs to a live walk.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import graph_walk as gw


REPO = Path(__file__).resolve().parents[2]
ATLAS_SCHEMA = REPO / "docs/internal/philo/graph/atlas.schema.json"


class _SelectLocator:
    def __init__(self, calls: list[tuple[str, float]]) -> None:
        self.first = self
        self._calls = calls

    def select_option(self, value: str, *, timeout: float) -> None:
        self._calls.append((value, timeout))


class _SelectPage:
    viewport_size = {"width": 1440}

    def __init__(self) -> None:
        self.selectors: list[str] = []
        self.option_calls: list[tuple[str, float]] = []

    def locator(self, selector: str) -> _SelectLocator:
        self.selectors.append(selector)
        return _SelectLocator(self.option_calls)


class _PressLocator:
    def __init__(self, calls: list[tuple[str, float]]) -> None:
        self.first = self
        self._calls = calls

    def press(self, key: str, *, timeout: float) -> None:
        self._calls.append((key, timeout))


class _PressPage:
    viewport_size = {"width": 1440}

    def __init__(self) -> None:
        self.selectors: list[str] = []
        self.press_calls: list[tuple[str, float]] = []
        self.keyboard_calls: list[str] = []
        self.keyboard = self

    def locator(self, selector: str) -> _PressLocator:
        self.selectors.append(selector)
        return _PressLocator(self.press_calls)

    def press(self, key: str) -> None:
        self.keyboard_calls.append(key)


def test_select_option_sends_exact_selector_and_value_to_native_locator() -> None:
    page = _SelectPage()
    selector = "select[data-testid='slack-destination']"
    value = "destination-slack-7"

    record = gw._ui_step(page, {
        "kind": "ui",
        "action": "select_option",
        "selector": selector,
        "value": value,
        "timeout_s": 2.5,
    })

    assert page.selectors == [selector]
    assert page.option_calls == [(value, 2500.0)]
    assert record["selector"] == selector
    assert record["value"] == value
    assert record["done"] is True


def test_press_with_a_selector_delivers_the_key_to_that_control() -> None:
    page = _PressPage()
    selector = "[data-testid=dest-key-row] input"

    record = gw._ui_step(page, {
        "kind": "ui",
        "action": "press",
        "selector": selector,
        "key": "Enter",
        "timeout_s": 2.5,
    })

    assert page.selectors == [selector]
    assert page.press_calls == [("Enter", 2500.0)]
    assert page.keyboard_calls == []
    assert record["selector"] == selector
    assert record["key"] == "Enter"
    assert record["done"] is True


@pytest.mark.parametrize("selector,value", [
    ("", "destination-slack-7"),
    ("select[data-testid='slack-destination']", ""),
    ("   ", "destination-slack-7"),
    ("select[data-testid='slack-destination']", "   "),
])
def test_select_option_refuses_an_empty_target_or_value_before_page_access(
    selector: str, value: str,
) -> None:
    page = _SelectPage()

    with pytest.raises(gw.Blocked, match="nonempty selector and value"):
        gw._ui_step(page, {
            "kind": "ui",
            "action": "select_option",
            "selector": selector,
            "value": value,
        })

    assert page.selectors == []
    assert page.option_calls == []


def test_atlas_schema_accepts_select_option_and_requires_nonempty_fields() -> None:
    schema = json.loads(ATLAS_SCHEMA.read_text())
    ui = next(
        branch for branch in schema["$defs"]["step"]["oneOf"]
        if branch.get("properties", {}).get("kind", {}).get("const") == "ui"
    )
    validator = Draft202012Validator({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": schema["$defs"],
        **ui,
    })

    valid = {
        "kind": "ui",
        "action": "select_option",
        "selector": "select[data-testid='slack-destination']",
        "value": "destination-slack-7",
    }
    assert not list(validator.iter_errors(valid))
    assert list(validator.iter_errors({**valid, "selector": ""}))
    assert list(validator.iter_errors({**valid, "value": ""}))
