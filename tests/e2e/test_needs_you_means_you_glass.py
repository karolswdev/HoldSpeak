"""``Needs you`` means the owner, AS RENDERED (owner rulings 2026-10-04).

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch). The oracle week is minted through the real producers
(``scripts/philo13_needs_you_fixture.py``): A3 names another owner (Priya)
and is due later; one Desk decision waits for review.

  * The Chair head, the bell and the Dock say 6. A3 is not in that number.
  * The drawer's rows are the members: one row per member, and no row for A3.
  * ``Waiting · N`` lists A3 (``WAITING ON PRIYA``); the head still says 6.

PHILO-14 A5: the Needs-you window body is the smart drawer. Its stable
testids: ``needs-drawer``, ``needs-list`` (the rows), ``needs-row`` (a
member), ``needs-source-row``, ``needs-row-verb`` (``data-verb`` names it),
``needs-filter`` (Phase 16: the FilterBar; its ``Waiting`` and ``Muted``
tokens open ``needs-waiting`` / ``needs-muted``), ``needs-next``.
  * The decision row has a Review verb; Review opens the decision's window.
  * Name an owner on A4 (the Door card's delegate verb): the head says 5 and
    WAITING lists A3 and A4.
  * Accept the decision: the head says 4 and the decision row is gone.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the needs-you glass needs Playwright")

TOKEN = "needs-you-means-you"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/needs-you-means-you-shots")
SIZES = {1440: 900, 393: 852}
A3_TASK = "A3 wait for Priya's review"
A4_TASK = "A4 assign the owner"

NUMBERS = r"""() => {
  const num = (s) => { const e = document.querySelector(s); const m = ((e && e.innerText) || '').match(/\d+/); return m ? Number(m[0]) : null; };
  return { head: num('[data-testid=arrival-display]'), bell: num('.desk-bell strong'),
           dock: num('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge') };
}"""


class TestNeedsYouMeansYou:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        from scripts.philo13_needs_you_fixture import seed_week

        server, _ = _boot(tmp_path, monkeypatch, token=TOKEN)
        try:
            self.week = seed_week(tmp_path / "holdspeak.db", home=tmp_path)
        finally:
            server.stop()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

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
        page.reload(wait_until="load")
        _normal_chair(page)
        return browser, page, errors

    @staticmethod
    def _agree_on(page: Any, n: int) -> dict[str, Any]:
        page.wait_for_function(
            """(n) => {
              const r = (s) => { const e = document.querySelector(s); const m = ((e && e.innerText) || '').match(/\\d+/); return m ? Number(m[0]) : null; };
              // PHILO-17 (needsyou): the head and the bell; the Dock's
              // Intelligence tile carries no copy of the number.
              return r('[data-testid=arrival-display]') === n && r('.desk-bell strong') === n
                && r('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge') === null;
            }""",
            arg=n, timeout=20_000,
        )
        return page.evaluate(NUMBERS)

    @staticmethod
    def _filter(page: Any, label: str) -> None:
        """Phase 16: WAITING is the FilterBar's `Waiting` token (its list is
        `Waiting · N`); RANKED is its `Ranked` token. The pressed token is
        asserted. At 393 a strip that does not fit is one menu Button."""
        word = "Waiting" if label == "WAITING" else "Ranked"
        bar = page.locator("[data-testid='needs-filter']")
        bar.wait_for(timeout=15_000)
        menu = bar.locator("[data-testid='surface-strip-menu']")
        if menu.count():
            menu.click()
            page.locator(".desk-head-menu").get_by_text(word, exact=True).click()
            _settle(page)
            assert (menu.get_attribute("aria-label") or "").endswith(f": {word}"), menu.get_attribute("aria-label")
            return
        token = bar.get_by_role("button", name=word, exact=True)
        token.click()
        _settle(page)
        assert token.get_attribute("aria-pressed") == "true", word

    @staticmethod
    def _rows(page: Any) -> list[str]:
        """The rows on view: the waiting list when it is open, else the members."""
        waiting = page.locator("[data-testid='needs-waiting']")
        scope = waiting if waiting.count() else page.locator("[data-testid='needs-list'] ul.needs-list")
        return [" ".join(text.split()) for text in scope.locator("[data-testid='needs-row']").all_inner_texts()]

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_head_counts_what_needs_him_and_waiting_lists_the_rest(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        ids = self.week["ids"]
        decision_ref = next(ref for ref in self.week["expectedRefs"] if ref.startswith("decision:"))
        decision_id = decision_ref.removeprefix("decision:")
        record: dict[str, Any] = {"width": width, "expectedRefs": self.week["expectedRefs"],
                                  "expectedWaitingRefs": self.week["expectedWaitingRefs"]}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # ── the head, the bell and the Dock: 6, without A3 ──
                record["before"] = self._agree_on(page, 6)
                wire = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
                record["wire"] = {"count": wire["count"], "waitingCount": wire["waitingCount"]}
                assert wire["count"] == 6 and wire["waitingCount"] == 1, record["wire"]
                _settle(page)
                page.screenshot(path=str(SHOTS / f"chair-headline-{width}.png"))

                # ── the drawer lists what the head counts: one row per member
                #    (the attention rows, the SETUP rows, the failed summaries),
                #    and no waiting row ──
                ranked = self._rows(page)
                record["ranked_rows"] = ranked
                assert len(ranked) == len(wire["members"]) == record["before"]["head"] == 6, ranked
                assert not any(A3_TASK in row or "WAITING ON" in row for row in ranked), ranked

                # ── the WAITING filter lists A3; the head does not move ──
                self._filter(page, "WAITING")
                waiting = self._rows(page)
                record["waiting_rows"] = waiting
                assert any(A3_TASK in row and "WAITING ON PRIYA" in row for row in waiting), waiting
                assert not any(A4_TASK in row for row in waiting), waiting
                assert page.evaluate(NUMBERS)["head"] == 6
                page.screenshot(path=str(SHOTS / f"chair-waiting-{width}.png"))

                # ── name an owner on A4: 5, and WAITING lists A3 and A4 ──
                _api(page, "POST", "/api/follow-through/complete",
                     {"card_id": ids["A4"], "verb": "delegate", "payload": {"to": "Dana"}}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                record["after_owner"] = self._agree_on(page, 5)
                self._filter(page, "WAITING")
                waiting = self._rows(page)
                record["waiting_rows_after_owner"] = waiting
                assert any(A3_TASK in row for row in waiting), waiting
                assert any(A4_TASK in row and "WAITING ON DANA" in row for row in waiting), waiting
                page.screenshot(path=str(SHOTS / f"chair-waiting-after-owner-{width}.png"))
                self._filter(page, "RANKED")

                # ── the decision row: Review opens the decision ──
                row = page.locator("[data-testid='needs-row']",
                                   has_text="R1 adopt the release checklist").first
                row.scroll_into_view_if_needed()
                review = row.get_by_role("button", name="Review: R1 adopt the release checklist")
                assert review.count() == 1
                review.click()
                opened = page.locator(".desk-window", has_text="R1 adopt the release checklist").first
                opened.wait_for(timeout=15_000)
                _settle(page)
                record["decision_window"] = opened.get_attribute("aria-label")
                page.screenshot(path=str(SHOTS / f"decision-review-open-{width}.png"))

                # ── accept the decision: 4, and its row is gone (a fresh page:
                #    the open decision window covers the Chair at 393) ──
                _api(page, "PUT", f"/api/decisions/{decision_id}/status", {"status": "accepted"}, token=TOKEN)
                wire = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
                assert wire["count"] == 4 and wire["waitingCount"] == 2, wire["count"]
                browser.close()
                browser, page, errors_after = self._page(pw, width)
                record["after_decision"] = self._agree_on(page, 4)
                assert not any("R1 adopt the release checklist" in row for row in self._rows(page))
                errors.extend(errors_after)

                record["page_errors"] = errors
                assert not errors, errors
            finally:
                (SHOTS / f"glass-{width}.json").write_text(json.dumps(record, indent=2, default=str))
                browser.close()
