"""PHILO-8-02 -- one delete everywhere, fenced AS RENDERED through the real hub.

Every case drives the real page at 1440 and 393 against a real
``MeetingWebServer`` on an isolated HOME, and reads the outcome on the hub
(``GET /api/decisions/{id}``: 404 = deleted, 200 = kept). No test double.

The four defects this file fences (red on main 267f692a, recorded in
``docs/internal/philo/phase-8/one-delete/``):

* The list's Delete (row menu, Delete key) sent no request: the only
  ``OBJECT_DELETE_REQUEST`` listener lived in ``WorldStage``, which never
  mounts with ``DeskListView`` (FINDING Finding 2).
* Cause 1: the deleted object stayed selected, so selecting B made two
  selected and Delete was ghosted without a word (A 404, B 200).
* Cause 2: a second ``remove()`` cleared the first one's timer, so the
  first delete never fired (A 200, B 404).
* Cause 3: the hook dropped a pending delete when ``WorldStage`` unmounted
  on a face change (A 200, zero DELETE requests).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from .test_philo7_delete_receipt_glass import _readable_receipt as _readable_now
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the one-delete glass needs Playwright")

TOKEN = "philo8-one-delete"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-02-shots")
WINDOW_WAIT_MS = 12_000  # the 8 s undo window plus the hub round trip


def _readable_receipt(page: Any, want: str, timeout_ms: int) -> dict[str, Any]:
    """The #665 probe, read once the receipt's entrance has settled.

    When the selection bar leaves (the deleted object leaves the selection),
    the receipt drops into its seat and animates in; the probe reads it after
    that motion, as the owner reads it.
    """
    page.wait_for_function(
        "(w) => (document.querySelector('.undo-receipt')?.innerText || '').includes(w)",
        arg=want,
        timeout=timeout_ms,
    )
    _settle(page)
    return _readable_now(page, want, timeout_ms)


def _decision(page: Any, title: str) -> str:
    created = _api(page, "POST", "/api/decisions", {"title": title, "status": "accepted"}, token=TOKEN)
    return created["decision"]["id"]


def _status(page: Any, decision_id: str) -> int:
    status, _payload = _api_allow_error(page, "GET", f"/api/decisions/{decision_id}", token=TOKEN)
    return status


def _palette(page: Any, query: str, option_id: str) -> None:
    """Run one palette entry (the shelf opens the palette at both widths)."""
    field = page.locator("[aria-controls=desk-palette-listbox]")
    if not field.is_visible():
        page.locator("[aria-controls=desk-tool-shelf]").click()
    field.fill(query)
    page.locator(f"[id='desk-palette-option-{option_id}']").click()


def _to_face(page: Any, face: str, width: int) -> None:
    """From the Chair to the Floor in the named view ('floor' or 'list')."""
    page.locator("[data-testid=chair-floor-toggle]").click()
    listed = width <= 720  # the Floor opens as the list at phone width
    if (face == "list") != listed:
        _palette(page, "Spatial view" if listed else "List view", "desk.toggle-view")
    if face == "list":
        page.locator(".desk-listmode").wait_for(timeout=15_000)
    else:
        page.locator(".desk-world-a11y").wait_for(state="attached", timeout=15_000)


def _name_button(page: Any, title: str) -> Any:
    return page.locator(".desk-list-name-cell", has_text=title).first


def _select(page: Any, face: str, decision_id: str, title: str) -> None:
    """Toggle one object into (or out of) the selection, as the owner does."""
    # Focus in one page call: over the GL world each Playwright round trip
    # costs about a second, and the two-delete probe must fit A's window.
    if face == "list":
        _name_button(page, title).wait_for(timeout=15_000)
        page.evaluate(
            "(t) => [...document.querySelectorAll('.desk-list-name-cell')]"
            ".find((el) => el.innerText.includes(t)).focus()",
            title,
        )
        page.keyboard.press(" ")
    else:
        selector = f"[data-obj-id='decision:{decision_id}']"
        page.locator(selector).wait_for(state="attached", timeout=15_000)
        page.evaluate("(s) => document.querySelector(s).focus()", selector)
        page.keyboard.press("Shift+Enter")


def _askbar_count(page: Any) -> str:
    # Read now, never wait: the bar leaves when the selection empties.
    return page.evaluate("() => document.querySelector('.desk-askbar-count')?.innerText || ''")


def _row_menu_delete(page: Any, title: str) -> dict[str, Any]:
    """Right-click the row, press the menu's Delete; return the Delete row's box."""
    _name_button(page, title).click(button="right")
    item = page.locator(".desk-world-menu [role=menuitem]", has_text="Delete").last
    item.wait_for(timeout=5_000)
    box = item.evaluate(
        "(el) => { const r = el.getBoundingClientRect();"
        " return {top: r.top, bottom: r.bottom, vh: window.innerHeight}; }"
    )
    item.click()
    return box


class TestOneDelete:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        self.deletes: list[str] = []
        try:
            yield
        finally:
            server.stop()

    def _open(self, pw: Any, width: int, titles: list[str]) -> tuple[Any, Any, list[str], list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 852 if width <= 720 else 900})
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("request", lambda req: self.deletes.append(req.url) if req.method == "DELETE" else None)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        ids = [_decision(page, title) for title in titles]
        page.reload(wait_until="load")
        _normal_chair(page)
        return browser, page, ids, errors

    def _clean(self, errors: list[str]) -> None:
        real = [e for e in errors if "ResizeObserver" not in e]
        assert not real, real

    # -- exit 3: the list's Delete does what it says -----------------------

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_row_menu_delete_removes_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["List delete decision"])
            try:
                _to_face(page, "list", width)
                box = _row_menu_delete(page, "List delete decision")
                print(f"{width}: the row menu's Delete row {box}")  # FINDING S2, measured
                _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / f"list-1-pending-{width}.png"))
                _readable_receipt(page, "Removal committed", 15_000)
                page.screenshot(path=str(SHOTS / f"list-2-committed-{width}.png"))
                assert _status(page, decision_id) == 404
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_delete_key_removes_the_selected_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Key delete decision"])
            try:
                _to_face(page, "list", width)
                _select(page, "list", decision_id, "Key delete decision")
                page.keyboard.press("Delete")
                _readable_receipt(page, "Removed", 5_000)
                _readable_receipt(page, "Removal committed", 15_000)
                assert _status(page, decision_id) == 404
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_palette_delete_removes_the_selected_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Palette delete decision"])
            try:
                _to_face(page, "list", width)
                _select(page, "list", decision_id, "Palette delete decision")
                _palette(page, "Delete", "object.delete")
                _readable_receipt(page, "Removed", 5_000)
                _readable_receipt(page, "Removal committed", 15_000)
                assert _status(page, decision_id) == 404
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_undo_on_the_list_keeps_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Undo list decision"])
            try:
                _to_face(page, "list", width)
                _row_menu_delete(page, "Undo list decision")
                _readable_receipt(page, "Removed", 5_000)
                page.locator(".undo-receipt-btn").click()
                _readable_receipt(page, "Restored", 5_000)
                page.screenshot(path=str(SHOTS / f"list-3-restored-{width}.png"))
                page.wait_for_timeout(WINDOW_WAIT_MS)
                assert _status(page, decision_id) == 200
                assert _name_button(page, "Undo list decision").is_visible()
                assert not self.deletes, self.deletes
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_the_receipt_is_readable_on_a_long_list_at_393(self) -> None:
        from playwright.sync_api import sync_playwright

        titles = [f"Long list decision {n:02d}" for n in range(1, 21)]
        with sync_playwright() as pw:
            browser, page, ids, errors = self._open(pw, 393, titles)
            try:
                _to_face(page, "list", 393)
                # The end of the list: the last row, scrolled into view.
                last = _name_button(page, titles[-1])
                last.scroll_into_view_if_needed()
                page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
                page.wait_for_timeout(200)
                scroll = page.evaluate(
                    "() => ({y: window.scrollY, h: document.documentElement.scrollHeight, vh: window.innerHeight})"
                )
                assert scroll["h"] > scroll["vh"], f"the list does not scroll: {scroll}"
                _row_menu_delete(page, titles[-1])
                _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / "list-long-end-393.png"))
                _readable_receipt(page, "Removal committed", 15_000)
                assert _status(page, ids[-1]) == 404
                # The top of the same list: the first row, the page at y = 0.
                page.evaluate("() => window.scrollTo(0, 0)")
                page.wait_for_timeout(200)
                _row_menu_delete(page, titles[0])
                _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / "list-long-top-393.png"))
                self._clean(errors)
            finally:
                browser.close()

    # -- exit 4: two deletes in one window both reach the hub --------------

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("order", ["a_left_selected", "a_taken_out"])
    @pytest.mark.parametrize("face", ["floor", "list"])
    def test_two_deletes_in_one_window_both_reach_the_hub(self, face: str, order: str, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (a_id, b_id), errors = self._open(pw, width, ["Probe A", "Probe B"])
            try:
                _to_face(page, face, width)
                _select(page, face, a_id, "Probe A")
                page.keyboard.press("Delete")
                page.wait_for_timeout(500)
                # The check's second order: A out of the selection before B,
                # when the face still holds it (main does; the repair already did).
                if order == "a_taken_out" and _askbar_count(page):
                    _select(page, face, a_id, "Probe A")
                selected_before_b = _askbar_count(page)
                _select(page, face, b_id, "Probe B")
                # The probe is only a probe inside A's window: A still pending.
                before_b = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                assert "Removed Probe A" in before_b, f"B came after A's window: {before_b!r}"
                page.keyboard.press("Delete")
                page.wait_for_timeout(300)
                receipt = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                result = {"A": _status(page, a_id), "B": _status(page, b_id)}
                print(f"{face} {order} {width}: selected before B {selected_before_b!r};"
                      f" receipt after B {receipt!r}; {result}; DELETE {len(self.deletes)}")
                assert result == {"A": 404, "B": 404}, (result, selected_before_b, receipt, self.deletes)
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_undo_keeps_only_the_pending_object(self, width: int) -> None:
        """A second delete commits the first at once; Undo restores the second only."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (a_id, b_id), errors = self._open(pw, width, ["Probe A", "Probe B"])
            try:
                _to_face(page, "floor", width)
                _select(page, "floor", a_id, "Probe A")
                page.keyboard.press("Delete")
                page.wait_for_timeout(1_000)
                _select(page, "floor", b_id, "Probe B")
                page.keyboard.press("Delete")
                _readable_receipt(page, "Removed Probe B", 5_000)
                page.locator(".undo-receipt-btn").click()
                _readable_receipt(page, "Restored Probe B", 5_000)
                page.wait_for_timeout(WINDOW_WAIT_MS)
                result = {"A": _status(page, a_id), "B": _status(page, b_id)}
                assert result == {"A": 404, "B": 200}, result
                self._clean(errors)
            finally:
                browser.close()

    # -- exit 4: a face change inside the window commits the delete --------

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("face", ["floor", "list"])
    def test_leaving_the_face_inside_the_window_commits_the_delete(self, face: str, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Leave face decision"])
            try:
                _to_face(page, face, width)
                _select(page, face, decision_id, "Leave face decision")
                page.keyboard.press("Delete")
                _readable_receipt(page, "Removed", 5_000)
                page.wait_for_timeout(1_500)
                page.locator("[data-testid=chair-floor-toggle]").click()  # to the Chair
                page.locator(".chair").wait_for(timeout=10_000)
                page.wait_for_timeout(WINDOW_WAIT_MS)
                status = _status(page, decision_id)
                print(f"{face} {width}: {status}; DELETE {len(self.deletes)}")
                assert status == 404, (status, self.deletes)
                self._clean(errors)
            finally:
                browser.close()

    # -- the Chair with a selection left from the Floor (story 02 Out, exercised)

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_delete_key_on_the_chair_with_a_floor_selection(self, width: int) -> None:
        """The keymap is global: a selection left from the Floor reaches the Chair.

        Main: the request reaches no listener (200, zero requests). The repair:
        the one listener takes it; no face seats a receipt on the Chair, so no
        Undo is in reach and the delete commits at once (404).
        """
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Chair stale decision"])
            try:
                _to_face(page, "floor", width)
                _select(page, "floor", decision_id, "Chair stale decision")
                page.locator("[data-testid=chair-floor-toggle]").click()  # to the Chair
                page.locator(".chair").wait_for(timeout=10_000)
                page.keyboard.press("Delete")
                page.wait_for_timeout(3_000)
                status = _status(page, decision_id)
                print(f"chair {width}: {status}; DELETE {len(self.deletes)}")
                assert status == 404, (status, self.deletes)
                self._clean(errors)
            finally:
                browser.close()
