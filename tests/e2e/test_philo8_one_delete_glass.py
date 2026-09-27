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
    # A greyed Delete names its reason; fail on it, never wait out a click.
    if item.get_attribute("aria-disabled") == "true":
        raise AssertionError("Delete greyed: " + repr(page.locator(".desk-world-menu").last.inner_text()))
    box = item.evaluate(
        "(el) => { const r = el.getBoundingClientRect();"
        " return {top: r.top, bottom: r.bottom, vh: window.innerHeight}; }"
    )
    item.click()
    return box


_OPTION_PROBE_JS = """(el) => {
  const r = el.getBoundingClientRect();
  return {text: el.innerText, inViewport: r.top >= 0 && r.left >= 0 &&
    r.bottom <= window.innerHeight && r.right <= window.innerWidth && r.width > 0};
}"""


_ROW_MENU_DELETE_JS = """async (title) => {
  const row = [...document.querySelectorAll('.desk-list-name-cell')].find((e) => e.innerText.includes(title));
  if (!row) return 'no row';
  const r = row.getBoundingClientRect();
  row.dispatchEvent(new MouseEvent('contextmenu', {bubbles: true, cancelable: true,
    clientX: r.x + r.width / 2, clientY: r.y + r.height / 2, button: 2}));
  for (let i = 0; i < 60; i++) {
    await new Promise((done) => requestAnimationFrame(done));
    const items = [...document.querySelectorAll('.desk-world-menu [role=menuitem]')].filter((e) => e.innerText.includes('Delete'));
    const item = items[items.length - 1];
    if (item) {
      if (item.getAttribute('aria-disabled') === 'true') return 'greyed: ' + item.innerText;
      item.click();
      return 'pressed';
    }
  }
  return 'no menu';
}"""


_IN_VIEW_JS = """(sel) => [...document.querySelectorAll(sel)].map((e) => {
  const r = e.getBoundingClientRect();
  const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  return {top: r.top, bottom: r.bottom, left: r.left, right: r.right,
          inViewport: r.width > 0 && r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth,
          own: !!hit && (hit === e || e.contains(hit))};
})"""


def _readable_in_view(page: Any, selector: str) -> dict[str, Any]:
    """Read BEFORE any click (a Playwright click scrolls): one match of the
    selector is inside the viewport and owns the point at its centre."""
    boxes = page.evaluate(_IN_VIEW_JS, selector)
    seen = [b for b in boxes if b["inViewport"] and b["own"]]
    assert seen, f"{selector} is not readable in the viewport: {boxes}"
    return seen[0]


def _observe_receipts(page: Any) -> None:
    """Record every change of the receipt texts from now on (the transition)."""
    page.evaluate("""() => {
      window.__receipts = []; let last = null;
      const read = () => {
        const text = [...document.querySelectorAll('.undo-receipt, .write-receipt')].map((e) => e.innerText).join(' | ');
        if (text !== last) { window.__receipts.push({t: performance.now(), text}); last = text; }
      };
      new MutationObserver(read).observe(document.body, {subtree: true, childList: true, characterData: true});
      read();
    }""")


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

    def _open(self, pw: Any, width: int, titles: list[str], engine: str = "chromium") -> tuple[Any, Any, list[str], list[str]]:
        browser = getattr(pw, engine).launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 852 if width <= 720 else 900})
        errors: list[str] = []
        page.on("pageerror", lambda err: (errors.append(str(err)), print(f"PAGEERROR {err.stack}")))
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

    # -- the Chair with a selection left from the Floor (round two: withheld)

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_chair_withholds_delete_with_its_reason(self, width: int) -> None:
        """The keymap is global: a selection left from the Floor reaches the Chair.

        The Chair shows no delete receipt, so it withholds the verb (Muad'Dib's
        ruling, PHILO-8-02 round two; UX-CANON A.11). The Delete key does
        nothing there, and the palette shows Delete greyed with its reason.
        Main: the request reached no listener (200). Round one: the one
        listener committed it at once with no receipt (404).
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
                receipt = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                print(f"chair {width}: {status}; DELETE {len(self.deletes)}; receipt {receipt!r}")
                assert (status, self.deletes) == (200, []), (status, self.deletes)
                # The verb, greyed with its reason, as the palette renders it.
                field = page.locator("[aria-controls=desk-palette-listbox]")
                if not field.is_visible():
                    page.locator("[aria-controls=desk-tool-shelf]").click()
                field.fill("Delete")
                option = page.locator("[id='desk-palette-option-object.delete']")
                option.wait_for(timeout=5_000)
                assert option.get_attribute("aria-disabled") == "true"
                probe = option.evaluate(_OPTION_PROBE_JS)
                assert "Open the Floor or the list" in probe["text"], probe
                assert probe["inViewport"], probe
                page.screenshot(path=str(SHOTS / f"chair-delete-withheld-{width}.png"))
                option.click(force=True)
                page.wait_for_timeout(1_000)
                assert _status(page, decision_id) == 200
                assert not self.deletes, self.deletes
                self._clean(errors)
            finally:
                browser.close()

    # -- round three (Codex Astra's check on PR #672, checks/story-02-built-astra-r1.md)

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("face", ["list", "floor"])
    def test_a_repeated_delete_never_offers_a_false_undo(self, face: str, width: int) -> None:
        """P1-a: Delete the same object twice, then Undo. Never "Restored" with 404."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Repeat me"])
            try:
                _to_face(page, face, width)
                if face == "list":
                    # Scroll once: a later right-click must not spend the window scrolling.
                    _name_button(page, "Repeat me").scroll_into_view_if_needed()
                for turn in range(2):
                    if turn:
                        # A probe only inside the first window: still pending.
                        now = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                        assert "Removed Repeat me" in now, f"the second Delete came after the window: {now!r}"
                    if face == "list" and turn:
                        # The second press in one page call: real DOM events on the
                        # row (contextmenu, then the menu's Delete), no round trips.
                        pressed = page.evaluate(_ROW_MENU_DELETE_JS, "Repeat me")
                        assert pressed == "pressed", pressed
                    elif face == "list":
                        _row_menu_delete(page, "Repeat me")
                    else:
                        if not _askbar_count(page):
                            _select(page, face, decision_id, "Repeat me")
                        page.keyboard.press("Delete")
                    page.wait_for_function(
                        "() => (document.querySelector('.undo-receipt')?.innerText || '').includes('Removed Repeat me')",
                        timeout=5_000,
                    )
                # Undo in one page call (the window is 8 s; each Playwright round
                # trip under load costs about a second).
                clicked = page.evaluate(
                    "() => { const b = document.querySelector('.undo-receipt-btn'); if (b) b.click(); return !!b; }"
                )
                assert clicked, "the window ended before Undo"
                _readable_receipt(page, "Restored Repeat me", 5_000)
                page.wait_for_timeout(WINDOW_WAIT_MS)
                status = _status(page, decision_id)
                print(f"repeat {face} {width}: {status}; DELETE {len(self.deletes)}")
                assert (status, self.deletes) == (200, []), (status, self.deletes)
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_a_repeated_workbench_remove_never_offers_a_false_undo(self) -> None:
        """P1-a, the Workbench window (the same hook)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, 1440, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "WB Probe"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Repeat WB item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _to_face(page, "list", 1440)
                _name_button(page, "WB Probe").click()
                window = page.locator(".desk-workbench-window")
                window.wait_for(timeout=10_000)
                window.get_by_text("Repeat WB item", exact=True).click()
                for _ in range(2):
                    window.get_by_role("button", name="Remove", exact=True).click()
                    page.wait_for_function(
                        "() => (document.querySelector('.desk-workbench-window .undo-receipt')?.innerText || '').includes('Removed')",
                        timeout=5_000,
                    )
                window.locator(".undo-receipt-btn").click()
                page.wait_for_timeout(WINDOW_WAIT_MS)
                receipt = page.evaluate("() => document.querySelector('.desk-workbench-window .undo-receipt')?.innerText || ''")
                items = _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]
                kept = any(i["id"] == item for i in items)
                print(f"workbench repeat: kept {kept}; receipt {receipt!r}; DELETE {len(self.deletes)}")
                assert kept and not self.deletes, (kept, receipt, self.deletes)
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_failed_refresh_keeps_the_pending_delete_and_its_undo(self, width: int) -> None:
        """P1-b: the setup read fails (503) while "Undo" shows. The desk shows
        its failure screen; the pending delete must NOT commit early (no DELETE
        before the 8 s window ends), and after Retry the receipt is back."""
        import time
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Refresh pending"])
            try:
                _to_face(page, "list", width)
                stamps: list[float] = []
                page.on("request", lambda req: stamps.append(time.monotonic()) if req.method == "DELETE" else None)
                _name_button(page, "Refresh pending").scroll_into_view_if_needed()
                t0 = time.monotonic()
                _row_menu_delete(page, "Refresh pending")
                fail = lambda route: route.fulfill(status=503, content_type="application/json", body="{}")
                page.route("**/api/setup/status", fail)
                _palette(page, "Refresh from hub", "desk.refresh")
                page.locator("[role=alert]").wait_for(timeout=10_000)
                shown = time.monotonic() - t0
                status_during = _status(page, decision_id) if shown < 7.0 else None
                page.unroute("**/api/setup/status", fail)
                page.locator("[role=alert]").get_by_role("button", name="Retry").click()
                page.locator(".desk-listmode").wait_for(timeout=10_000)
                recovered = time.monotonic() - t0
                receipt = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                early = [round(t - t0, 2) for t in stamps if t - t0 < 7.5]
                print(f"refresh {width}: failure shown at {shown:.1f}s; status during {status_during};"
                      f" DELETE at {[round(t - t0, 2) for t in stamps]}; receipt after Retry {receipt!r}")
                assert status_during in (None, 200), status_during
                assert not early, f"the delete committed early, at {early} s"
                # Back inside the window (or its 6 s linger) the receipt is back.
                if recovered < 12.0:
                    assert "Remov" in receipt, (recovered, receipt)
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_foot_never_covers_the_last_rows(self, width: int) -> None:
        """P2: with the receipt and the selection bar in the foot, the end of a
        long list scrolls clear of the foot; the last rows own their centres."""
        from playwright.sync_api import sync_playwright

        titles = [f"Last row {n:02d}" for n in range(1, 21)]
        with sync_playwright() as pw:
            browser, page, ids, errors = self._open(pw, width, titles)
            try:
                _to_face(page, "list", width)
                page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
                _select(page, "list", ids[-2], titles[-2])
                _row_menu_delete(page, titles[-1])
                _readable_receipt(page, "Removed", 5_000)
                page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
                page.wait_for_timeout(300)
                probe = page.evaluate("""() => {
                  const foot = document.querySelector('.desk-listmode > .desk-world-foot').getBoundingClientRect();
                  const rows = [...document.querySelectorAll('.desk-list-name-cell')]
                    .filter((e) => e.innerText.includes('Last row')).slice(-3).map((e) => {
                      const r = e.getBoundingClientRect();
                      const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                      return {text: e.innerText.replace(/\\n/g, ' '), top: r.top, bottom: r.bottom,
                              own: !!hit && (hit === e || e.contains(hit))};
                    });
                  return {footTop: foot.top, footBottom: foot.bottom, rows};
                }""")
                page.screenshot(path=str(SHOTS / f"list-foot-clear-{width}.png"))
                print(f"foot {width}: {probe}")
                assert all(r["own"] and r["bottom"] <= probe["footTop"] for r in probe["rows"]), probe
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("face", ["list", "floor"])
    def test_a_refused_delete_says_so_with_retry(self, face: str, width: int) -> None:
        """MISSED 1 (round three) + round four item 4: the hub refuses the DELETE
        (403, one second late). From the press to the failure the face never
        says "Removal committed"; it names the failure with Retry and the
        hub's own words in the chip's title; the object stays; Retry deletes."""
        import time
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Refuse me"])
            try:
                _to_face(page, face, width)
                _observe_receipts(page)

                def refuse(route: Any) -> None:
                    if route.request.method == "DELETE":
                        time.sleep(1)
                        route.fulfill(status=403, content_type="application/json",
                                      body='{"detail":"Delete refused by the glass"}')
                    else:
                        route.continue_()

                page.route(f"**/api/decisions/{decision_id}", refuse)
                if face == "list":
                    _row_menu_delete(page, "Refuse me")
                else:
                    _select(page, face, decision_id, "Refuse me")
                    page.keyboard.press("Delete")
                page.locator(".write-receipt").first.wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.wait_for_timeout(300)
                # Round five (P2): the failure and its Retry are where the owner's
                # eyes are, without scrolling (read before any click).
                failure_box = _readable_in_view(page, ".write-receipt")
                retry_box = _readable_in_view(page, ".write-receipt-retry")
                print(f"refused {face} {width}: failure at {failure_box}; Retry at {retry_box}")
                history = page.evaluate("() => window.__receipts")
                failure = page.locator(".write-receipt").first.inner_text()
                title = page.locator(".write-receipt-label").first.get_attribute("title") or ""
                status = _status(page, decision_id)
                page.screenshot(path=str(SHOTS / f"{face}-delete-refused-{width}.png"))
                print(f"refused {face} {width}: {status}; failure {failure!r}; title {title!r};"
                      f" history {[h['text'] for h in history]}")
                assert status == 200
                assert not any("Removal committed" in h["text"] for h in history), history
                assert "DELETE" in failure and "Retry" in failure, failure
                assert "Delete refused by the glass" in title, title
                page.unroute(f"**/api/decisions/{decision_id}", refuse)
                page.locator(".write-receipt-retry").first.click()
                page.wait_for_timeout(2_000)
                assert _status(page, decision_id) == 404
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_workbench_remove_works_again_after_a_refusal(self, width: int) -> None:
        """Round four item 2: a refused Remove (403) frees the item: the next
        Remove sends a DELETE; the window never says "Removal committed"."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, width, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "Refused WB"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Refused item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _to_face(page, "list", width)
                _name_button(page, "Refused WB").click()
                window = page.locator(".desk-workbench-window")
                window.wait_for(timeout=10_000)
                window.get_by_text("Refused item", exact=True).click()
                _observe_receipts(page)
                url = f"**/api/workbenches/{wb}/items/{item}"

                def refuse(route: Any) -> None:
                    if route.request.method == "DELETE":
                        route.fulfill(status=403, content_type="application/json", body='{"detail":"Item locked by the glass"}')
                    else:
                        route.continue_()

                page.route(url, refuse)
                window.get_by_role("button", name="Remove", exact=True).click()
                window.locator(".write-receipt").wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.unroute(url, refuse)
                before = len(self.deletes)
                window.get_by_role("button", name="Remove", exact=True).click()
                # Round five (MISSED 1): the renewed window shows its Undo.
                page.wait_for_function(
                    "() => (document.querySelector('.desk-workbench-window .undo-receipt')?.innerText || '').includes('Removed Refused item')",
                    timeout=5_000,
                )
                _readable_in_view(page, ".desk-workbench-window .undo-receipt-btn")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                history = page.evaluate("() => window.__receipts")
                items = _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]
                sent = len(self.deletes) - before
                print(f"workbench refusal {width}: DELETE after refusal {sent}; items {len(items)};"
                      f" history {[h['text'] for h in history]}")
                assert sent == 1 and not items, (sent, items)
                first_failure = next(i for i, h in enumerate(history) if "REMOVE ITEM" in h["text"])
                before_failure = [h["text"] for h in history[:first_failure + 1]]
                assert not any("Removal committed" in t for t in before_failure), before_failure
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_workbench_remove_after_a_refusal_offers_undo(self, width: int) -> None:
        """Round five P1: refusal, then an ordinary Remove: its Undo is visible
        (the old refusal never hides it) and Undo keeps the item."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, width, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "Undo WB"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Undo item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _to_face(page, "list", width)
                _name_button(page, "Undo WB").click()
                window = page.locator(".desk-workbench-window")
                window.wait_for(timeout=10_000)
                window.get_by_text("Undo item", exact=True).click()
                url = f"**/api/workbenches/{wb}/items/{item}"

                def refuse(route: Any) -> None:
                    if route.request.method == "DELETE":
                        route.fulfill(status=403, content_type="application/json", body='{"detail":"Item locked by the glass"}')
                    else:
                        route.continue_()

                page.route(url, refuse)
                window.get_by_role("button", name="Remove", exact=True).click()
                window.locator(".write-receipt").wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.unroute(url, refuse)
                before = len(self.deletes)
                window.get_by_role("button", name="Remove", exact=True).click()
                page.wait_for_function(
                    "() => !!document.querySelector('.desk-workbench-window .undo-receipt-btn')", timeout=5_000,
                )
                box = _readable_in_view(page, ".desk-workbench-window .undo-receipt-btn")
                footer = page.evaluate("() => document.querySelector('.desk-workbench-window .undo-receipt')?.innerText || ''")
                page.screenshot(path=str(SHOTS / f"workbench-undo-after-refusal-{width}.png"))
                page.evaluate("() => document.querySelector('.desk-workbench-window .undo-receipt-btn').click()")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                items = _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]
                sent = len(self.deletes) - before
                print(f"workbench undo after refusal {width}: Undo at {box}; receipt {footer!r}; kept {len(items)}; DELETE {sent}")
                assert "Removed Undo item" in footer, footer
                assert [i["id"] for i in items] == [item] and sent == 0, (items, sent)
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_workbench_success_keeps_another_items_refusal(self, width: int) -> None:
        """Round six (the Workbench's local channel): A's Remove is refused; B is
        removed and commits; A's failure and Retry still show; Retry removes A."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, width, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "Two items WB"}, token=TOKEN)["workbench"]["id"]
                a = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Item A"}, token=TOKEN)["item"]["id"]
                b = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Item B"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _to_face(page, "list", width)
                _name_button(page, "Two items WB").click()
                window = page.locator(".desk-workbench-window")
                window.wait_for(timeout=10_000)
                url = f"**/api/workbenches/{wb}/items/{a}"

                def refuse(route: Any) -> None:
                    if route.request.method == "DELETE":
                        route.fulfill(status=403, content_type="application/json", body='{"detail":"Item A locked"}')
                    else:
                        route.continue_()

                page.route(url, refuse)
                window.get_by_text("Item A", exact=True).click()
                window.get_by_role("button", name="Remove", exact=True).click()
                window.locator(".write-receipt").wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.unroute(url, refuse)
                window.get_by_text("Item B", exact=True).click()
                window.get_by_role("button", name="Remove", exact=True).click()
                page.wait_for_timeout(WINDOW_WAIT_MS + 1_000)
                items = [i["id"] for i in _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]]
                assert items == [a], items  # B committed, A kept
                page.wait_for_timeout(7_000)  # past B's "Removal committed" linger
                standing = page.evaluate(
                    "() => [...document.querySelectorAll('.desk-workbench-window .write-receipt')].map((e) => e.innerText)"
                )
                print(f"workbench two items {width}: standing {standing}")
                assert standing and "REMOVE ITEM" in standing[0], standing
                _readable_in_view(page, ".desk-workbench-window .write-receipt-retry")
                page.locator(".desk-workbench-window .write-receipt-retry").click()
                page.wait_for_timeout(2_000)
                items = _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]
                assert items == [], items
                self._clean(errors)
            finally:
                browser.close()

    def _refuse_then(self, width: int, other_write: str) -> None:
        """Round seven: A's delete is refused; then another desk write lands
        (a New Zone create, or a rename update); A's failure and a reachable
        Retry remain; Retry deletes A."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Refused A"])
            try:
                note = _api(page, "POST", "/api/notes", {"title": "Rename me"}, token=TOKEN)["note"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _to_face(page, "list", width)

                def refuse(route: Any) -> None:
                    if route.request.method == "DELETE":
                        route.fulfill(status=403, content_type="application/json", body='{"detail":"A is locked"}')
                    else:
                        route.continue_()

                page.route(f"**/api/decisions/{decision_id}", refuse)
                _row_menu_delete(page, "Refused A")
                page.locator(".write-receipt", has_text="DELETE").first.wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.unroute(f"**/api/decisions/{decision_id}", refuse)
                if other_write == "create":
                    _palette(page, "New Zone", "desk.new-zone")
                    page.locator("input.desk-zone-rename").wait_for(timeout=10_000)
                    page.keyboard.press("Escape")
                    landed = lambda: len(_api(page, "GET", "/api/directories", token=TOKEN)["directories"]) >= 1
                else:
                    # An update: edit the note's body in its editor (the
                    # debounced save, updatePrimitive).
                    _name_button(page, "Rename me").click(button="right")
                    page.locator(".desk-world-menu [role=menuitem]", has_text="Edit").last.click()
                    body = page.locator(".desk-editor-window .cm-content").first
                    body.wait_for(timeout=10_000)
                    body.click()
                    page.keyboard.type(" edited by the glass")
                    import json as _json
                    landed = lambda: "edited by the glass" in _json.dumps(
                        _api(page, "GET", f"/api/notes/{note}", token=TOKEN))
                page.wait_for_timeout(2_000)
                assert landed(), f"the {other_write} did not land"
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                standing = [t for t in page.locator(".write-receipt").all_inner_texts() if "DELETE" in t]
                print(f"{other_write} {width}: A {_status(page, decision_id)}; standing {standing}")
                assert standing, "A's failure was erased"
                _readable_in_view(page, ".write-receipt-retry")
                page.screenshot(path=str(SHOTS / f"list-delete-failure-kept-after-{other_write}-{width}.png"))
                page.locator(".write-receipt", has_text="DELETE").locator(".write-receipt-retry").first.click()
                page.wait_for_timeout(2_000)
                assert _status(page, decision_id) == 404
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_create_keeps_an_unrelated_delete_failure(self, width: int) -> None:
        self._refuse_then(width, "create")

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_an_update_keeps_an_unrelated_delete_failure(self, width: int) -> None:
        self._refuse_then(width, "update")

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("engine", ["chromium", "webkit"])
    def test_a_delete_keeps_an_unrelated_rename_failure(self, engine: str, width: int) -> None:
        """Round four item 1, round eight: a rename refusal is SEATED on the
        chip (NAME TAKEN); a face change moves it to the desk receipt; a
        successful delete of another object must not clear it (its failure and
        a reachable Retry remain). Chromium and WebKit (Astra reproduced in
        WebKit)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Unrelated decision"], engine)
            try:
                _to_face(page, "list", width)
                _palette(page, "New Zone", "desk.new-zone")
                field = page.locator("input.desk-zone-rename")
                field.wait_for(timeout=10_000)
                field.fill("Inbox")
                field.press("Enter")
                # The refusal is seated on the chip BEFORE the face changes.
                page.locator("[data-testid=zone-name-refused]").first.wait_for(timeout=10_000)
                page.locator("[data-testid=chair-floor-toggle]").click()
                page.locator(".chair").wait_for(timeout=10_000)
                rename = page.locator(".write-receipt").filter(has_text="RENAME ZONE")
                rename.first.wait_for(timeout=10_000)
                page.locator("[data-testid=chair-floor-toggle]").click()
                page.locator(".desk-listmode").wait_for(timeout=10_000)
                _row_menu_delete(page, "Unrelated decision")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                status = _status(page, decision_id)
                standing = [t for t in page.locator(".write-receipt").all_inner_texts() if "RENAME ZONE" in t]
                page.screenshot(path=str(SHOTS / f"list-rename-failure-kept-{engine}-{width}.png"))
                print(f"unrelated {engine} {width}: {status}; standing {standing}")
                assert status == 404
                assert standing and "Retry" in standing[0], standing
                _readable_in_view(page, ".write-receipt-retry")
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_a_recreated_object_can_be_deleted_again(self) -> None:
        """Round four item 3: delete A; the hub re-creates A with the same id;
        after a refresh, Delete on it sends a DELETE and it is gone."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, 1440, ["First incarnation"])
            try:
                _to_face(page, "list", 1440)
                _row_menu_delete(page, "First incarnation")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                assert _status(page, decision_id) == 404
                made = _api(page, "POST", "/api/decisions",
                            {"id": decision_id, "title": "Second incarnation", "status": "accepted"}, token=TOKEN)
                assert made["decision"]["id"] == decision_id, made
                _palette(page, "Refresh from hub", "desk.refresh")
                _name_button(page, "Second incarnation").wait_for(timeout=10_000)
                before = len(self.deletes)
                _row_menu_delete(page, "Second incarnation")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                status = _status(page, decision_id)
                sent = len(self.deletes) - before
                print(f"recreated: {status}; DELETE {sent}")
                assert (status, sent) == (404, 1), (status, sent)
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_a_resize_that_changes_the_face_commits(self) -> None:
        """MISSED 2: the face is the one the owner SEES. 393 opens the list;
        widening to 1440 resolves the spatial Floor: the pending delete commits."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, 393, ["Resize me"])
            try:
                _to_face(page, "list", 393)
                _row_menu_delete(page, "Resize me")
                _readable_receipt(page, "Removed Resize me", 5_000)
                # Round five (MISSED 3): the DELETE must start with the face
                # change, well before the window could end on its own.
                page.evaluate("""() => { window.__deleteAt = null; const f = window.fetch;
                  window.fetch = (input, init) => { if ((init?.method || '').toUpperCase() === 'DELETE' && window.__deleteAt === null)
                    window.__deleteAt = performance.now(); return f(input, init); }; }""")
                left = page.evaluate("() => (document.querySelector('.undo-receipt-time')?.innerText || '')")
                resized_at = page.evaluate("() => performance.now()")
                page.set_viewport_size({"width": 1440, "height": 900})
                page.locator(".desk-world-a11y").wait_for(state="attached", timeout=10_000)
                page.wait_for_timeout(500)
                # Read at once: the commit is the face change's, not the window's end.
                receipt = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                page.wait_for_timeout(1_000)
                status = _status(page, decision_id)
                delete_at = page.evaluate("() => window.__deleteAt")
                lag = None if delete_at is None else delete_at - resized_at
                print(f"resize: {status}; receipt {receipt!r}; window left {left!r}; DELETE {lag} ms after the resize")
                assert lag is not None and lag < 1_000, (lag, left)
                # The face change started the commit: no Undo is offered any more
                # (round four: "Removed …" while in flight, then "Removal committed").
                assert "Undo" not in receipt and receipt, (status, receipt)
                assert status == 404, (status, receipt)
                self._clean(errors)
            finally:
                browser.close()
