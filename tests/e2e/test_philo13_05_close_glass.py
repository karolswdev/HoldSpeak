"""PHILO-13-05 (A4) -- close means gone, fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch: every press a tap). Each object window opens through its REAL opener,
closes through its own Close gadget, and the fence reads what the browser
renders: the card leaves the DOM, and ``elementFromPoint`` at the window's old
centre hits the Desk (no window), so the next tap reaches what is under it.

Openers (the store keeps the id each one passes):
  * the palette ``decision:<id>``   (qualified; the Chair's card mount)
  * the Dock ``intelligence:desk``  (qualified; the J1 window)
  * ``Write a thought`` ``note:<id>`` (qualified; the Thought window)
  * the Floor's object button ``<id>`` (bare; the Floor's card mount, 1440)
  * a list row ``note:<id>`` (qualified; the list's card mount, 393)
  * the list row's menu -> Open ``<id>`` (bare; object.open, 393)
And the J1 recovery leg: the closed Intelligence window must not swallow the
Chair's brief ``Retry``.

Red on main 27b91553 (the card closed with the bare id; the store kept the
qualified one; the faded card stayed at opacity 0 and caught every tap).
Every record is minted by a real route (POST /api/decisions, /api/notes,
/api/brief/generate).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the close glass needs Playwright")

TOKEN = "philo13-05-close"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-05-shots")
SIZES = {1440: 900, 393: 852}
DECISION = "Freeze the old ledger on Nov 5"
NOTE = "Arch review prep"

HIT_JS = """([x, y]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  const w = e.closest('.desk-window, .desk-pullout');
  const t = e.closest('[data-testid]');
  return {tag: e.tagName.toLowerCase(), cls: String(e.className || '').slice(0, 80),
          testid: t ? t.dataset.testid : null, window: w ? (w.id || String(w.className).slice(0, 60)) : null,
          desk: Boolean(e.closest('.desk-next'))};
}"""

OPEN_WINDOWS_JS = """() => [...document.querySelectorAll('.desk-window, .desk-pullout')]
  .filter(w => w.getBoundingClientRect().width > 0 && getComputedStyle(w).display !== 'none')
  .map(w => { const r = w.getBoundingClientRect(); const cs = getComputedStyle(w);
    return {id: w.id, label: w.getAttribute('aria-label'), op: cs.opacity, pe: cs.pointerEvents,
            rect: [r.x, r.y, r.width, r.height]}; })"""


class TestCloseMeansGone:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        _api(page, "POST", "/api/decisions", {"title": DECISION, "status": "proposed",
                                              "decision_markdown": "Freeze writes on Nov 5."}, token=TOKEN)
        _api(page, "POST", "/api/notes", {"title": NOTE, "body_markdown": "- Ledger cutover risks\n"}, token=TOKEN)
        _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        """A click at 1440; a real touch tap at the element's centre at 393."""
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _open(page: Any) -> list[dict[str, Any]]:
        return page.evaluate(OPEN_WINDOWS_JS)

    def _close_and_prove(self, page: Any, width: int, label: str, name: str) -> dict[str, Any]:
        """Close the one open window ``label`` by its Close gadget; prove it is gone."""
        page.wait_for_timeout(600)
        _settle(page)
        wins = [w for w in self._open(page) if w["label"] == label]
        assert len(wins) == 1, (label, self._open(page))
        win = wins[0]
        x, y, w, h = win["rect"]
        cx, cy = x + w / 2, y + h / 2
        assert page.evaluate(HIT_JS, [cx, cy])["window"] == win["id"], "the open window is not on top"
        page.screenshot(path=str(SHOTS / f"{name}-before-{width}.png"))
        self._press(page, page.locator(f"[id='{win['id']}'] [aria-label='Close {label}']"), width)
        page.wait_for_timeout(900)
        _settle(page)
        hit = page.evaluate(HIT_JS, [cx, cy])
        left = [o for o in self._open(page) if o["id"] == win["id"]]
        page.screenshot(path=str(SHOTS / f"{name}-after-{width}.png"))
        proof = {"window": win["id"], "centre": [round(cx), round(cy)], "hit": hit, "left_in_dom": left}
        (SHOTS / f"{name}-{width}.txt").write_text(f"{proof}\n")
        assert not left, f"the closed window stays in the DOM: {left}"
        assert hit is not None and hit["window"] is None and hit["desk"], f"the old centre hits {hit}"
        return proof

    # ── the fences ───────────────────────────────────────────────────────

    @pytest.mark.parametrize("width", list(SIZES))
    def test_every_opener_closes_to_the_desk(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # 1. the palette: `decision:<id>` (DeskToolShelf → qualifiedRef).
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill("freeze")
                option = page.locator("[id^='desk-palette-option-decision:']").first
                option.wait_for()
                self._press(page, option, width)
                page.locator(f".desk-gadget-close[aria-label='Close {DECISION}']").wait_for()
                self._close_and_prove(page, width, DECISION, "palette-decision")

                # 2. the Dock: `intelligence:desk`.
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Intelligence']"), width)
                page.locator(".desk-gadget-close[aria-label='Close Intelligence']").wait_for()
                self._close_and_prove(page, width, "Intelligence", "dock-intelligence")

                # 3. Write a thought: `note:<id>` (newThought.ts) → the Thought window.
                self._press(page, page.get_by_test_id("arrival-develop-thought"), width)
                page.locator(".desk-gadget-close[aria-label='Close Thought']").wait_for()
                self._close_and_prove(page, width, "Thought", "write-a-thought")

                self._press(page, page.get_by_test_id("chair-floor-toggle"), width)
                page.wait_for_timeout(2500)  # the Floor (1440) or the list (393) mounts
                if width >= 720:
                    # 4. a bare id: the Floor stage's object button (WorldStage → openPullout(o.id)).
                    obj = page.locator(f"[data-obj-id][aria-label^='{NOTE}']").first
                    obj.wait_for(state="attached")
                    obj.focus()
                    page.keyboard.press("Enter")
                    page.locator(f".desk-gadget-close[aria-label='Close {NOTE}']").wait_for()
                    self._close_and_prove(page, width, NOTE, "floor-bare-note")
                else:
                    # 4. the list mount at 393: a row tap passes `note:<id>` (qualifiedRef).
                    self._press(page, page.locator(f".desk-list-name-cell[aria-label='{NOTE}']"), width)
                    page.locator(f".desk-gadget-close[aria-label='Close {NOTE}']").wait_for()
                    self._close_and_prove(page, width, NOTE, "list-row-note")
                    # 5. a bare id at 393: the row's menu → Open (object.open → openPullout(o.id)).
                    page.locator(f".desk-list-name-cell[aria-label='{DECISION}']").focus()
                    page.keyboard.press("Shift+F10")
                    item = page.get_by_role("menuitem", name="Open", exact=True)
                    item.wait_for()
                    self._press(page, item, width)
                    page.locator(f".desk-gadget-close[aria-label='Close {DECISION}']").wait_for()
                    self._close_and_prove(page, width, DECISION, "row-menu-bare-decision")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_closed_intelligence_window_does_not_swallow_retry(self, width: int) -> None:
        """J1's recovery leg: the brief read fails, Intelligence opens and closes,
        and the Chair's Retry (under the old window at 393) works with no reload."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.route("**/api/brief/latest*", lambda r: r.fulfill(
                    status=500, body='{"detail":"injected"}', content_type="application/json"))
                page.reload(wait_until="load")
                _normal_chair(page)
                retry = page.get_by_test_id("arrival-brief-retry")
                retry.wait_for()
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Intelligence']"), width)
                page.locator(".desk-gadget-close[aria-label='Close Intelligence']").wait_for()
                page.unroute("**/api/brief/latest*")
                proof = self._close_and_prove(page, width, "Intelligence", "j1-retry")
                self._press(page, retry, width)
                page.get_by_test_id("arrival-brief-retry").wait_for(state="detached", timeout=10_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"j1-retry-reached-{width}.png"))
                (SHOTS / f"j1-retry-{width}.txt").write_text(
                    f"{proof}\nafter Retry: {page.get_by_test_id('arrival-brief').first.inner_text()[:200]!r}\n")
                assert not [e for e in errors if "injected" not in e], errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_meeting_resolved_as_deleted_closes_its_card(self, width: int) -> None:
        """Round three (Astra counsel r2): the meeting card's own close caller,
        through the REAL producer. A tombstone conflict is recorded through the
        meeting repository (as tests/integration/test_meeting_conflict_recovery.py
        does); the card opens as `meeting:<id>`; the real MeetingConflictRecovery
        resolves with Use incoming; the real route answers deleted:true; the card
        leaves the DOM and its old centre hits the Desk."""
        from playwright.sync_api import sync_playwright
        from datetime import datetime, timedelta

        from holdspeak.db import get_database
        from holdspeak.meeting_session import MeetingState, TranscriptSegment

        db = get_database()
        started = datetime.now() - timedelta(hours=2)
        title = "Tombstone sync review"
        local = MeetingState(
            id="p13-tombstone", started_at=started, ended_at=started + timedelta(minutes=12),
            title=title, tags=["delivery"],
            segments=[TranscriptSegment(text="Retained until the owner decides.", speaker="Karol",
                                        start_time=4.0, end_time=9.0)],
        )
        db.meetings.save_meeting(local)
        db.meetings.record_sync_conflict(local.id, local_value=local.to_dict(),
                                         incoming_value={"deleted": True})

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill("Tombstone")
                option = page.locator("[id='desk-palette-option-meeting:p13-tombstone']")
                option.wait_for()
                self._press(page, option, width)
                card = page.locator(f".desk-pullout[aria-label='{title}']")
                card.wait_for()
                incoming = card.get_by_role("button", name="Use incoming")
                incoming.wait_for()
                page.wait_for_timeout(600)
                _settle(page)
                box = card.bounding_box()
                assert box
                cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                win_id = card.get_attribute("id")
                page.screenshot(path=str(SHOTS / f"meeting-tombstone-before-{width}.png"))
                answers: list[dict] = []
                page.on("response", lambda r: answers.append({"status": r.status, "url": r.url})
                        if "/sync-conflicts/" in r.url and r.url.endswith("/resolve") else None)
                self._press(page, incoming, width)
                page.wait_for_timeout(1500)
                _settle(page)
                hit = page.evaluate(HIT_JS, [cx, cy])
                left = [o for o in self._open(page) if o["id"] == win_id]
                page.screenshot(path=str(SHOTS / f"meeting-tombstone-after-{width}.png"))
                proof = {"window": win_id, "centre": [round(cx), round(cy)], "resolve": answers,
                         "hit": hit, "left_in_dom": left}
                (SHOTS / f"meeting-tombstone-{width}.txt").write_text(f"{proof}\n")
                assert answers and answers[0]["status"] == 200, answers
                assert db.meetings.get_meeting(local.id) is None
                assert not left, f"the closed card stays in the DOM: {left}"
                assert hit is not None and hit["window"] is None and hit["desk"], f"the old centre hits {hit}"
                assert not errors, errors
            finally:
                browser.close()
