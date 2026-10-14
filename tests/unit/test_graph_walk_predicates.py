"""The graph-walk rig (scripts/graph_walk.py): the protocol_reads and all_of
predicates, the right-click, `then` steps and the guarded click and press.

Moved from tests/unit/test_philo8_atlas.py by the fast diet (2026-10-12); the
Phase 8 atlas-case pins are parked in tests/_parked/unit/test_philo8_atlas.py,
and the general atlas fences hold for every atlas file in
tests/unit/test_graph_atlas.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts import graph_walk as gw

REPO = Path(__file__).resolve().parents[2]

#: The face cases this story names (story file "Scope" + the lane's brief).
#: Face predicate kinds that read what the owner sees without text
#: containment: readable text, a control's own geometry, a field's value, an
#: attribute. Protocol kinds read the hub. ``text_absent`` is allowed only as
#: a part beside a readable one (an absence has no readable form).


# ─────────────────────────── protocol_reads ──────────────────────────────

def _reads(*statuses: int, payload: Any = None) -> dict[str, Any]:
    return {"api_reads": [{"method": "GET", "path": f"/api/decisions/d{i}", "status": s,
                           "payload": payload} for i, s in enumerate(statuses)]}


def test_protocol_reads_passes_on_every_declared_status() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}, {"status": 404}]},
                                 {}, _reads(404, 404))
    assert ok, why


def test_protocol_reads_fails_when_one_object_is_still_on_the_hub() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}, {"status": 404}]},
                                 {}, _reads(404, 200))
    assert not ok and "answered 200, wanted 404" in why


def test_protocol_reads_fails_on_a_read_never_sent() -> None:
    after = {"api_reads": [{"method": "GET", "path": "/api/decisions/{x}", "skipped": "unresolved"}]}
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}]}, {}, after)
    assert not ok and "not sent" in why


def test_protocol_reads_fails_on_a_missing_read() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}]}, {}, {})
    assert not ok and "0 read(s) observed" in why


def test_protocol_reads_without_expectations_is_blocked() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": []}, {}, _reads(200))
    assert not ok and why.startswith("BLOCKED")


def test_protocol_reads_row_needs_exactly_one_match() -> None:
    row = {"path": "directories", "match": {"name": "New zone 2"}}
    one = {"directories": [{"name": "New zone"}, {"name": "New zone 2"}]}
    two = {"directories": [{"name": "New zone 2"}, {"name": "New zone 2"}]}
    none = {"directories": [{"name": "New zone"}]}
    pred = {"kind": "protocol_reads", "expect": [{"status": 200, "row": row}]}
    assert gw.check_predicate(pred, {}, _reads(200, payload=one))[0]
    assert not gw.check_predicate(pred, {}, _reads(200, payload=two))[0]
    assert not gw.check_predicate(pred, {}, _reads(200, payload=none))[0]


def test_protocol_reads_is_decidable_headless() -> None:
    ok, _ = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}]},
                               {}, {"headless": True, **_reads(404)})
    assert ok


# ─────────────────────────────── all_of ──────────────────────────────────

def _readable(text: str) -> dict[str, Any]:
    return {"target_present": True, "visible": True, "text": text,
            "hit_test": {"in_viewport": True, "all_owned": True, "rect": {"w": 10, "h": 10}}}


def test_all_of_needs_every_part() -> None:
    pred = {"kind": "all_of", "predicates": [
        {"kind": "readable_text", "value": "Removal committed"},
        {"kind": "protocol_reads", "expect": [{"status": 404}]}]}
    assert gw.check_predicate(pred, {}, {**_readable("Removal committed"), **_reads(404)})[0]
    ok, why = gw.check_predicate(pred, {}, {**_readable("Removal committed"), **_reads(200)})
    assert not ok and "protocol_reads" in why
    ok, why = gw.check_predicate(pred, {}, {**_readable("Removed A"), **_reads(404)})
    assert not ok and "readable_text" in why


@pytest.mark.parametrize("parts", [
    [],
    [{"kind": "readable_text", "value": "x"}],
    [{"kind": "readable_text", "value": "x"}, {"kind": "all_of", "predicates": []}],
    [{"kind": "readable_text", "value": "x"}, {"kind": "unchanged"}],
    [{"kind": "readable_text", "value": "x"}, "prose"],
])
def test_all_of_refuses_a_shape_it_cannot_decide(parts) -> None:
    ok, why = gw.check_predicate({"kind": "all_of", "predicates": parts}, {}, _readable("x"))
    assert not ok and why.startswith("BLOCKED")


def test_all_of_hands_its_input_value_selector_to_the_snapshot() -> None:
    pred = {"kind": "all_of", "predicates": [
        {"kind": "protocol_status", "status": 201},
        {"kind": "input_value", "selector": "input.desk-zone-rename", "equals": "New zone 2"}]}
    assert gw._value_selector(pred) == "input.desk-zone-rename"
    assert gw._value_selector({"kind": "input_value", "selector": "input.x"}) == "input.x"
    mixed = {"kind": "all_of", "predicates": [
        {"kind": "selector_presence", "selector": "button.record", "present": True},
        {"kind": "input_value", "selector": "input.agenda", "equals": "Keep this draft"},
    ]}
    assert gw._value_selector(mixed) == "input.agenda"
    assert gw._value_selector({"kind": "all_of", "predicates": [mixed["predicates"][0]]}) is None


# ──────────────────────────── the right-click ────────────────────────────

class _Locator:
    def __init__(self, log: list) -> None:
        self.log = log
        self.first = self

    def click(self, timeout: float, button: str = "left") -> None:
        self.log.append(button)


class _Page:
    viewport_size = {"width": 1440}

    def __init__(self) -> None:
        self.log: list[str] = []

    def locator(self, _selector: str) -> _Locator:
        return _Locator(self.log)

    def get_by_role(self, _role: str, name: str, exact: bool) -> _Locator:
        return _Locator(self.log)


def test_a_right_click_reaches_the_page_as_a_right_click() -> None:
    page = _Page()
    record = gw._ui_step(page, {"kind": "ui", "action": "click_role", "role": "button",
                                "name": "Atlas list delete", "button": "right"})
    assert page.log == ["right"] and record["button"] == "right" and record["done"]
    gw._ui_step(page, {"kind": "ui", "action": "click", "selector": ".desk-x"})
    assert page.log == ["right", "left"]


@pytest.mark.parametrize("step", [
    {"kind": "ui", "action": "click", "selector": ".desk-x", "button": "middle"},
    {"kind": "ui", "action": "press", "key": "Delete", "button": "right"},
])
def test_a_button_the_rig_cannot_press_is_blocked(step) -> None:
    with pytest.raises(gw.Blocked):
        gw._ui_step(_Page(), step)


@pytest.mark.parametrize("then", [[{"kind": "api", "method": "DELETE", "path": "/x"}], "press Delete", [None]])
def test_then_takes_ui_steps_only(then) -> None:
    with pytest.raises(gw.Blocked):
        gw.trigger_then({"kind": "ui", "action": "press", "key": "Delete", "then": then})
    assert gw.trigger_then({"kind": "ui", "action": "press", "key": "Delete"}) == []


class _GuardLocator(_Locator):
    def wait_for(self, state: str, timeout: float) -> None:
        self.log.append(f"wait:{state}")

    def element_handle(self, timeout: float) -> str:
        return "handle"


class _GuardPage(_Page):
    """The atomic path: the page's ONE evaluate decides and delivers."""

    def __init__(self, delivered: bool, reasons: list[str] | None = None) -> None:
        super().__init__()
        self.result = {"delivered": delivered, "reasons": reasons or [],
                       "seen": {"text": "Removed A Undo 05s", "seconds": 5}}
        self.evaluated: list = []

    def locator(self, _selector: str) -> _GuardLocator:
        return _GuardLocator(self.log)

    def evaluate(self, _js: str, args: Any) -> dict:
        self.evaluated.append(args)
        return self.result


_IN_WINDOW = {"visible": ".undo-receipt.is-pending", "text": "Undo",
              "seconds_left": {"selector": ".undo-receipt-time", "min": 2}}


def test_a_guarded_click_is_one_page_task_and_never_a_playwright_click() -> None:
    """Codex Astra r2: no actionability wait between the guard and the event."""
    page = _GuardPage(delivered=True)
    record = gw._ui_step(page, {"kind": "ui", "action": "click", "selector": ".desk-x", "requires": _IN_WINDOW})
    assert page.log == ["wait:visible"], page.log  # resolved, NOT clicked by Playwright
    assert page.evaluated == [["handle", _IN_WINDOW, None]]
    assert record["done"] and record["guard"]["atomic"] and record["guard"]["holds"]


def test_a_guarded_press_goes_to_the_focused_element_in_the_same_task() -> None:
    page = _GuardPage(delivered=True)
    gw._ui_step(page, {"kind": "ui", "action": "press", "key": "Delete", "requires": _IN_WINDOW})
    assert page.log == [] and page.evaluated == [[None, _IN_WINDOW, "Delete"]]


@pytest.mark.parametrize("reasons", [["'.undo-receipt.is-pending' is not visible"],
                                     ["'.undo-receipt-time' reads '01s', wanted >= 2s"],
                                     ["the target is disabled"], ["the target is covered at its centre"]])
@pytest.mark.parametrize("optional", [False, True])
def test_a_guard_or_target_that_fails_at_delivery_blocks(reasons, optional) -> None:
    page = _GuardPage(delivered=False, reasons=reasons)
    with pytest.raises(gw.Blocked, match="did not hold at delivery"):
        gw._ui_step(page, {"kind": "ui", "action": "click", "selector": ".desk-x",
                           "requires": _IN_WINDOW, "optional": optional})
    assert "left" not in page.log


def test_only_click_and_press_are_guarded() -> None:
    with pytest.raises(gw.Blocked, match="only click"):
        gw._ui_step(_GuardPage(delivered=True), {"kind": "ui", "action": "fill", "selector": "input.desk-x",
                                                 "value": "x", "requires": _IN_WINDOW})
