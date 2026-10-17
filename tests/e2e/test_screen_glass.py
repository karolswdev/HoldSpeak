"""The desk's Screen, rendered: a delete's receipt, read where the owner reads
it. What jsdom cannot read: the Delete key on a selected icon, the receipt's
box in the viewport (9 of 9 ``elementFromPoint`` samples on it, no pixel
shared with the ask bar or the Dock), the 6 s linger of "Removal committed",
and the same with the phone's current Go desk and a scrolled drawer at 393.

The delete's logic (Undo keeps the object, a second delete commits the
first, the seat) is vitest: ``web/src/desk/__tests__/deleteReceipt.test.tsx``.

Moved from test_philo7_delete_receipt_glass.py and
test_philo8_one_delete_glass.py (push 2 of the test diet, 2026-10-12; both
parked in tests/e2e/_parked/, the second as
test_philo8_one_delete_screen_glass.py).

PHILO-7-03 red on main: the wrapper carried the ``.desk-next`` root class,
whose ``min-height: 100vh`` made the fixed box one viewport tall, so the
receipt was drawn at y = -12 (3 of 9 samples off-screen), and the committed
phase cleared after 1.2 s.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Screen glass needs Playwright")

TOKEN = "screen-glass"
SHOTS = evidence_dir(".tmp/screen-glass-shots")
STILL_FLOOR = "reduce"  # reduced motion, as the one-delete rig ran


_PROBE_JS = """(el) => {
  const r = el.getBoundingClientRect();
  const vw = window.innerWidth, vh = window.innerHeight;
  const style = getComputedStyle(el);
  const xs = [r.left + 2, r.left + r.width / 2, r.right - 2];
  const ys = [r.top + 2, r.top + r.height / 2, r.bottom - 2];
  const samples = [];
  for (const x of xs) for (const y of ys) {
    const hit = document.elementFromPoint(x, y);
    samples.push({x, y, owned: !!hit && (hit === el || el.contains(hit))});
  }
  return {
    text: el.innerText,
    rect: {x: r.left, y: r.top, w: r.width, h: r.height},
    visible: style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0,
    inViewport: r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh && r.width > 0 && r.height > 0,
    samples,
  };
}"""


_OVERLAP_JS = """() => {
  const r = document.querySelector('.undo-receipt').getBoundingClientRect();
  const hits = [];
  for (const sel of ['.desk-askbar', '.desk-dock']) {
    for (const el of document.querySelectorAll(sel)) {
      const o = el.getBoundingClientRect();
      if (o.width && o.height && r.left < o.right && o.left < r.right && r.top < o.bottom && o.top < r.bottom)
        hits.push({sel, rect: {x: o.left, y: o.top, w: o.width, h: o.height}});
    }
  }
  return hits;
}"""


def _readable_receipt(page: Any, want: str, timeout_ms: int) -> dict[str, Any]:
    """Wait until the receipt reads ``want``; then it must be readable and uncovered."""
    page.wait_for_function(
        "(w) => (document.querySelector('.undo-receipt')?.innerText || '').includes(w)",
        arg=want,
        timeout=timeout_ms,
    )
    # The receipt animates in from opacity 0. Read it after that motion, as the
    # owner reads it (the PHILO-8-02 rig does the same). On the GPU the probe
    # is otherwise faster than the first painted frame.
    _settle(page)
    probe = page.locator(".undo-receipt").first.evaluate(_PROBE_JS)
    assert want in probe["text"], probe
    assert probe["visible"] and probe["inViewport"], f"{want!r}: not in the viewport: {probe['rect']}"
    owned = [s for s in probe["samples"] if s["owned"]]
    assert len(owned) == 9, f"{want!r}: {len(owned)}/9 samples on the receipt: {probe}"
    # Never covers: the receipt shares no pixel with the selection bar or the dock.
    overlaps = page.evaluate(_OVERLAP_JS)
    assert overlaps == [], f"{want!r}: the receipt overlaps {overlaps}"
    return probe


def _readable_settled(page: Any, want: str, timeout_ms: int) -> dict[str, Any]:
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
    return _readable_receipt(page, want, timeout_ms)


def _decision(page: Any, title: str) -> str:
    created = _api(page, "POST", "/api/decisions", {"title": title, "status": "accepted"}, token=TOKEN)
    return created["decision"]["id"]


def _status(page: Any, decision_id: str) -> int:
    status, _payload = _api_allow_error(page, "GET", f"/api/decisions/{decision_id}", token=TOKEN)
    return status


def _icon(page: Any, decision_id: str) -> Any:
    return page.locator(f".desk-screen [data-object-id='decision:{decision_id}']").first


def _icon_menu_delete(page: Any, decision_id: str) -> None:
    """Right-click the decision's desk icon; press the object menu's Delete."""
    icon = _icon(page, decision_id)
    icon.wait_for(timeout=15_000)
    icon.scroll_into_view_if_needed()
    icon.click(button="right")
    item = page.locator(".desk-world-menu [role=menuitem]", has_text="Delete").last
    item.wait_for(timeout=5_000)
    if item.get_attribute("aria-disabled") == "true":
        raise AssertionError("Delete greyed: " + repr(page.locator(".desk-world-menu").last.inner_text()))
    item.click()


def _phone_open_decision(page: Any, decision_id: str, title: str) -> Any:
    """Open the exact record through Search, as the phone's Go desk does."""
    field = page.locator('[aria-controls=desk-palette-listbox]')
    if not field.is_visible():
        page.locator('[aria-controls=desk-tool-shelf]:visible').tap()
    field.fill(title)
    page.locator(f'[id="desk-palette-option-decision:{decision_id}"]').tap()
    window = page.locator(f'[id="pullout:decision:{decision_id}"]')
    window.wait_for()
    return window


def _phone_window_delete(page: Any, window: Any) -> None:
    """Long-press the real window head, then Object > Delete."""
    box = window.locator(':scope > .desk-pullout-head').bounding_box()
    assert box
    x, y = box['x'] + box['width'] * .65, box['y'] + box['height'] / 2
    cdp = page.context.new_cdp_session(page)
    try:
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
        page.wait_for_timeout(800)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    finally:
        cdp.detach()
    menu = page.locator('.desk-head-menu[role=menu]')
    menu.wait_for()
    menu.get_by_role('menuitem').filter(
        has=page.locator('.desk-menu-label', has_text=re.compile(r'^Object$'))).tap()
    delete = page.get_by_role('menu', name='Object submenu', exact=True).get_by_role('menuitem').filter(
        has=page.locator('.desk-menu-label', has_text=re.compile(r'^Delete$')))
    assert delete.get_attribute('aria-disabled') != 'true'
    delete.tap()
    window.wait_for(state='detached')


def _undo_phone_delete(page: Any, decision_id: str) -> None:
    _readable_settled(page, 'Removed', 5_000)
    page.locator('.undo-receipt-btn').tap()
    _readable_settled(page, 'Restored', 5_000)
    page.wait_for_timeout(10_000)  # past the pending removal's 8 s deadline
    assert _status(page, decision_id) == 200



class TestScreenDeleteGlass:
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
        page = browser.new_page(viewport={"width": width, "height": 852 if width <= 720 else 900},
                                reduced_motion=STILL_FLOOR, has_touch=width <= 720)
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("request", lambda req: self.deletes.append(req.url) if req.method == "DELETE" else None)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        ids = [_decision(page, title) for title in titles]
        page.reload(wait_until="load")
        _normal_chair(page)
        return browser, page, ids, errors

    def _clean(self, errors: list[str]) -> None:
        real = [e for e in errors if "ResizeObserver" not in e]
        assert not real, real

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_delete_receipt_is_readable_in_the_viewport(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900},
                                        has_touch=width <= 720, reduced_motion=STILL_FLOOR)
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                created = _api(page, "POST", "/api/decisions",
                               {"title": "Glass withdrawn decision", "status": "accepted"}, token=TOKEN)
                decision_id = created["decision"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)

                if width <= 720:
                    window = _phone_open_decision(page, decision_id, "Glass withdrawn decision")
                    _phone_window_delete(page, window)
                    _undo_phone_delete(page, decision_id)
                    window = _phone_open_decision(page, decision_id, "Glass withdrawn decision")
                else:
                    # Desktop retains the real selected-icon Delete key proof.
                    icon = _icon(page, decision_id)
                    icon.wait_for(timeout=15_000)
                    icon.scroll_into_view_if_needed()
                    icon.click()
                    assert icon.get_attribute("aria-pressed") == "true"
                # An in-page clock: when 'Removal committed' first shows and when it goes.
                page.evaluate("""() => {
                  window.__committedFirst = null; window.__committedGone = null;
                  const iv = setInterval(() => {
                    const text = document.querySelector('.undo-receipt')?.innerText || '';
                    const now = performance.now();
                    if (text.includes('Removal committed') && window.__committedFirst === null) window.__committedFirst = now;
                    if (!text && window.__committedFirst !== null) { window.__committedGone = now; clearInterval(iv); }
                  }, 50);
                }""")
                if width <= 720:
                    _phone_window_delete(page, window)
                else:
                    page.keyboard.press("Delete")

                pending = _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / f"1-pending-{width}.png"))
                committed = _readable_receipt(page, "Removal committed", 15_000)
                page.screenshot(path=str(SHOTS / f"2-committed-{width}.png"))

                # The committed receipt stays long enough to read (the desk's outcome
                # linger, OUTCOME_LINGER_MS = 6000 in web/src/desk/linger.ts; main: 1.2 s).
                page.wait_for_function("() => window.__committedGone !== null", timeout=20_000)
                shown_ms = page.evaluate("() => window.__committedGone - window.__committedFirst")
                assert shown_ms >= 5_000, f"'Removal committed' shows for {shown_ms} ms only"

                status, payload = _api_allow_error(page, "GET", f"/api/decisions/{decision_id}", token=TOKEN)
                assert status == 404, payload
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
                print(f"{width}: pending {pending['rect']} committed {committed['rect']} shown {shown_ms:.0f} ms")
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_the_receipt_is_readable_on_a_long_desk_at_393(self) -> None:
        from playwright.sync_api import sync_playwright

        titles = [f"Long desk decision {n:02d}" for n in range(1, 41)]
        with sync_playwright() as pw:
            browser, page, ids, errors = self._open(pw, 393, titles)
            try:
                # At 393 Go is the desk. Open an actual drawer whose contents
                # exceed its viewport, then delete the record at its foot.
                created = _api(page, "POST", "/api/directories", {"name": "Receipt decisions"}, token=TOKEN)
                directory_id = (created.get("directory") or created)["id"]
                for decision_id in ids:
                    _api(page, "PUT", f"/api/directories/{directory_id}/members/decision:{decision_id}", {}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                door = page.locator(f'.desk-go-home [data-object-id="zone:{directory_id}"]')
                door.scroll_into_view_if_needed()
                door.tap()
                drawer = page.locator(f'[id="pullout:zone:{directory_id}"]')
                drawer.wait_for()
                body = drawer.locator('.desk-pullout-body')
                body.evaluate("s => { s.scrollTop = s.scrollHeight; }")
                page.wait_for_timeout(200)
                scroll = body.evaluate("s => ({top:s.scrollTop, h:s.scrollHeight, vh:s.clientHeight})")
                assert scroll["h"] > scroll["vh"] and scroll["top"] > 0, f"the drawer does not scroll: {scroll}"
                last = drawer.locator('.surface-row-open').filter(has=page.locator(f'[data-member-ref="decision:{ids[-1]}"]'))
                last.tap()
                window = page.locator(f'[id="pullout:decision:{ids[-1]}"]')
                window.wait_for()
                _phone_window_delete(page, window)
                _readable_settled(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / "desk-long-end-393.png"))
                _readable_settled(page, "Removal committed", 15_000)
                assert _status(page, ids[-1]) == 404
                # The top of the same drawer, and an Undo that survives the
                # original removal deadline while that scrolled host stays open.
                body.evaluate("s => { s.scrollTop = 0; }")
                page.wait_for_timeout(200)
                first = drawer.locator('.surface-row-open').filter(has=page.locator(f'[data-member-ref="decision:{ids[0]}"]'))
                first.tap()
                window = page.locator(f'[id="pullout:decision:{ids[0]}"]')
                window.wait_for()
                _phone_window_delete(page, window)
                _readable_settled(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / "desk-long-top-393.png"))
                _undo_phone_delete(page, ids[0])
                self._clean(errors)
            finally:
                browser.close()
