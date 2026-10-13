"""PHILO-8-02 -- one delete on the desk, fenced AS RENDERED through the real hub.

Re-homed by PHILO-17 (owner 2026-10-10, "Yes, everything must become one
desk"): the Floor and its list are parked; these fences enter from the
Screen (a decision's icon and its object menu) and from Search (a
Workbench). The assertions are unchanged: Undo keeps the object (200 on the
hub, the icon back on the desk); the receipt is readable after the desk
scrolls at 393; a Workbench item's refused Park frees it, and the next Park
offers a visible Restore that keeps the item. The Floor-only fences are
parked: tests/e2e/_parked/test_philo8_one_delete_glass.py.
"""
from __future__ import annotations

import time
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
STILL_FLOOR = "reduce"  # reduced motion, as the parked file ran


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


def _wait_deleted(page: Any, *decision_ids: str) -> None:
    """Wait until the hub answers 404 for each id, at most the old fixed wait.

    These cases assert a 404 after the undo window. The fixed 12 s wait is the
    limit, not the wait: the read returns when the hub has the delete (about
    8 s). A case that asserts a 200 keeps the full fixed wait.
    """
    deadline = time.monotonic() + WINDOW_WAIT_MS / 1000
    while time.monotonic() < deadline:
        if all(_status(page, decision_id) == 404 for decision_id in decision_ids):
            return
        page.wait_for_timeout(250)


def _palette(page: Any, query: str, option_id: str) -> None:
    """Run one palette entry (the shelf opens the palette at both widths)."""
    field = page.locator("[aria-controls=desk-palette-listbox]")
    if not field.is_visible():
        page.locator("[aria-controls=desk-tool-shelf]").click()
    field.fill(query)
    page.locator(f"[id='desk-palette-option-{option_id}']").click()


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
        const text = [...document.querySelectorAll('.undo-receipt, .write-receipt, .park-receipt')].map((e) => e.innerText).join(' | ');
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
        page = browser.new_page(viewport={"width": width, "height": 852 if width <= 720 else 900},
                                reduced_motion=STILL_FLOOR)
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

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_undo_on_the_desk_keeps_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Undo desk decision"])
            try:
                _icon_menu_delete(page, decision_id)
                _readable_receipt(page, "Removed", 5_000)
                page.locator(".undo-receipt-btn").click()
                _readable_receipt(page, "Restored", 5_000)
                page.screenshot(path=str(SHOTS / f"desk-3-restored-{width}.png"))
                page.wait_for_timeout(WINDOW_WAIT_MS)
                assert _status(page, decision_id) == 200
                assert _icon(page, decision_id).is_visible()
                assert not self.deletes, self.deletes
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_the_receipt_is_readable_on_a_long_desk_at_393(self) -> None:
        from playwright.sync_api import sync_playwright

        titles = [f"Long desk decision {n:02d}" for n in range(1, 41)]
        with sync_playwright() as pw:
            browser, page, ids, errors = self._open(pw, 393, titles)
            try:
                # The end of the desk: the last icon, the Screen scrolled to its foot.
                _icon(page, ids[-1]).wait_for(timeout=15_000)
                page.evaluate("() => { const s = document.querySelector('.desk-screen'); s.scrollTop = s.scrollHeight; }")
                page.wait_for_timeout(200)
                scroll = page.evaluate(
                    "() => { const s = document.querySelector('.desk-screen');"
                    " return {top: s.scrollTop, h: s.scrollHeight, vh: s.clientHeight}; }"
                )
                assert scroll["h"] > scroll["vh"] and scroll["top"] > 0, f"the desk does not scroll: {scroll}"
                _icon_menu_delete(page, ids[-1])
                _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / "desk-long-end-393.png"))
                _readable_receipt(page, "Removal committed", 15_000)
                assert _status(page, ids[-1]) == 404
                # The top of the same desk.
                page.evaluate("() => { document.querySelector('.desk-screen').scrollTop = 0; }")
                page.wait_for_timeout(200)
                _icon_menu_delete(page, ids[0])
                _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / "desk-long-top-393.png"))
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_workbench_park_works_again_after_a_refusal(self, width: int) -> None:
        """Round four item 2, rehomed by PHILO-13-02: a refused Park (403)
        frees the item: the next Park sends a DELETE (the hub's park); the
        window never says PARKED before the refusal."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, width, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "Refused WB"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Refused item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _palette(page, "Refused WB", f"workbench:{wb}")  # PHILO-17: Search is the workbench's door
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
                window.get_by_role("button", name="Park", exact=True).click()
                window.locator(".write-receipt").wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.unroute(url, refuse)
                before = len(self.deletes)
                window.get_by_role("button", name="Park", exact=True).click()
                page.wait_for_function(
                    "() => (document.querySelector('.desk-workbench-window .park-receipt')?.innerText || '').startsWith('PARKED')",
                    timeout=5_000,
                )
                _readable_in_view(page, ".desk-workbench-window .park-receipt button")
                history = page.evaluate("() => window.__receipts")
                items = _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]
                parked = _api(page, "GET", f"/api/workbenches/{wb}?parked=true", token=TOKEN)["workbench"]["items"]
                sent = len(self.deletes) - before
                print(f"workbench refusal {width}: DELETE after refusal {sent}; items {len(items)}; parked {len(parked)};"
                      f" history {[h['text'] for h in history]}")
                assert sent == 1 and not items and [i["id"] for i in parked] == [item], (sent, items, parked)
                first_failure = next(i for i, h in enumerate(history) if "PARK ITEM" in h["text"])
                before_failure = [h["text"] for h in history[:first_failure + 1]]
                assert not any("PARKED" in t for t in before_failure), before_failure
                self._clean(errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_workbench_park_after_a_refusal_offers_restore(self, width: int) -> None:
        """Round five P1, rehomed by PHILO-13-02: refusal, then an ordinary
        Park: its Restore is visible (the old refusal never hides it) and
        Restore keeps the item."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, width, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "Undo WB"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Undo item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _palette(page, "Undo WB", f"workbench:{wb}")  # PHILO-17: Search is the workbench's door
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
                window.get_by_role("button", name="Park", exact=True).click()
                window.locator(".write-receipt").wait_for(timeout=WINDOW_WAIT_MS + 6_000)
                page.unroute(url, refuse)
                window.get_by_role("button", name="Park", exact=True).click()
                page.wait_for_function(
                    "() => !!document.querySelector('.desk-workbench-window .park-receipt button')", timeout=5_000,
                )
                box = _readable_in_view(page, ".desk-workbench-window .park-receipt button")
                footer = page.evaluate("() => document.querySelector('.desk-workbench-window .park-receipt')?.innerText || ''")
                page.screenshot(path=str(SHOTS / f"workbench-restore-after-refusal-{width}.png"))
                page.evaluate("() => document.querySelector('.desk-workbench-window .park-receipt button').click()")
                page.wait_for_timeout(WINDOW_WAIT_MS)
                items = _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]
                print(f"workbench restore after refusal {width}: Restore at {box}; receipt {footer!r}; kept {len(items)}")
                assert footer.startswith("PARKED") and "Restore" in footer, footer
                assert [i["id"] for i in items] == [item], items
                self._clean(errors)
            finally:
                browser.close()
