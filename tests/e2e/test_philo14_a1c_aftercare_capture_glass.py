"""PHILO-14 A1c -- the MEETING READY card in Capture's slot at 1440, AS RENDERED.

Muad'Dib's ruling 2026-10-07: a card that lands opens a closed Capture and
sits in Capture's slot; nothing floats over another window. Astra r1 (#954)
asked for rendered geometry, not presence:

  default   Capture closed -> the card opens it; the eyebrow, the title and
            Dismiss are whole in Capture's body; Capture does not cover
            Needs you; Dismiss -> Capture returns to its seat.
  moved     Capture moved by its title bar (arranged) -> its rect does not
            change through card -> Dismiss; the eyebrow is whole at
            scrollTop 0; the title and Dismiss are whole once scrolled to.
  resized   Capture sized by its grip (arranged) -> the same.
  meetings  Capture open, Meetings in front -> the card lands in Meetings;
            Capture's rect does not change through card -> Dismiss.

The frame is the hub's own (``build_aftercare_ready_event`` over a seeded
meeting with open items, sent with ``MeetingWebServer.broadcast``).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_17_phone_desk_glass import CARD_MEETING, _seed_card_meeting
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the aftercare glass needs Playwright")

TOKEN = "philo14-a1c-card"
SHOTS = evidence_dir("docs/internal/philo/phase-14/a1c-shots")
CAPTURE = "[id='chair:capture']"

GEOMETRY = r"""() => {
  const rect = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; };
  const capture = document.getElementById('chair:capture');
  const needs = document.getElementById('chair:needs');
  const card = document.querySelector('.ambient-aftercare');
  const host = card ? card.closest('.desk-window-shell') : null;
  return { capture: rect(capture), needs: rect(needs), card: rect(card),
           host: host ? host.getAttribute('aria-label') : null,
           fixed: !!document.querySelector('.ambient-aftercare-fixed') };
}"""

# Whole = the element's box lies inside every clipping ancestor and the
# viewport, and the point at its centre hits it (nothing covers it).
WHOLE = r"""(el) => {
  const r = el.getBoundingClientRect();
  let t = r.top, l = r.left, b = r.bottom, ri = r.right;
  for (let a = el.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowX + cs.overflowY)) {
      const ar = a.getBoundingClientRect();
      t = Math.max(t, ar.top); l = Math.max(l, ar.left); b = Math.min(b, ar.bottom); ri = Math.min(ri, ar.right);
    }
  }
  t = Math.max(t, 0); l = Math.max(l, 0); b = Math.min(b, innerHeight); ri = Math.min(ri, innerWidth);
  const full = Math.abs(ri - l - r.width) < 1.5 && Math.abs(b - t - r.height) < 1.5;
  const h = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2);
  return { full, hit: !!h && (h === el || el.contains(h)), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}"""


def _same(a: dict | None, b: dict | None) -> bool:
    return bool(a and b) and all(abs(a[k] - b[k]) <= 1 for k in ("x", "y", "w", "h"))


class TestTheCardInCapture1440:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed_card_meeting()
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the hands ────────────────────────────────────────────────────────

    def _page(self, pw: Any) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1).new_page()
        page.set_default_timeout(20_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(800)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _open_chair(page: Any, name: str) -> None:
        page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
        page.locator(".desk-verbbar-menu [role='menuitem']").filter(has_text="Chair").click()
        page.locator(".desk-menu-list [role='menuitemcheckbox']").filter(has_text=name).click()
        page.locator(f".desk-window-shell.chair-window[aria-label='{name}']").wait_for()
        page.wait_for_timeout(400)

    def _send_card(self, page: Any) -> None:
        from holdspeak.db import get_database
        from holdspeak.meeting_aftercare import build_aftercare_ready_event

        event = build_aftercare_ready_event(get_database(), CARD_MEETING)
        assert event, "the seeded meeting has no aftercare (the event is quiet)"
        self.server.broadcast("aftercare_ready", event)
        page.locator(".ambient-aftercare").wait_for()
        page.wait_for_timeout(700)
        _settle(page)

    @staticmethod
    def _dismiss(page: Any) -> None:
        button = page.locator(".ambient-aftercare").get_by_role("button", name="Dismiss")
        button.scroll_into_view_if_needed()
        button.click()
        page.locator(".ambient-aftercare").wait_for(state="detached")
        page.wait_for_timeout(500)

    @staticmethod
    def _readable(page: Any, fails: list[str], name: str) -> dict[str, Any]:
        """The receipt is reachable by scrolling Capture's body: at scrollTop 0
        the eyebrow is whole; scrolled to them, the title and Dismiss are whole."""
        body = page.locator(f"{CAPTURE} .chair-window-body")
        body.evaluate("(el) => { el.scrollTop = 0; }")
        page.wait_for_timeout(150)
        card = page.locator(f"{CAPTURE} [data-aftercare-slot] .ambient-aftercare")
        # At scrollTop 0 the card's first line is whole: nothing is stranded
        # above the scroll origin. Each later part is whole once scrolled to.
        out = {"eyebrow": card.locator(".signal-eyebrow").evaluate(WHOLE)}
        for part, loc in (("title", card.locator("strong")),
                          ("dismiss", card.get_by_role("button", name="Dismiss"))):
            loc.evaluate("(el) => el.scrollIntoView({ block: 'nearest' })")
            page.wait_for_timeout(150)
            out[part] = loc.evaluate(WHOLE)
        out["scroll"] = body.evaluate("(el) => ({ top: el.scrollTop, height: el.scrollHeight, client: el.clientHeight })")
        for part in ("eyebrow", "title", "dismiss"):
            if not (out[part]["full"] and out[part]["hit"]):
                fails.append(f"{name}: the card's {part} is not whole {out[part]}")
        return out

    def _arranged(self, how: str) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._open_chair(page, "Needs you")
                self._open_chair(page, "Capture")
                if how == "moved":
                    head = page.locator(f"{CAPTURE} .desk-pullout-head").bounding_box()
                    x, y = head["x"] + 180, head["y"] + head["height"] / 2
                    page.mouse.move(x, y)
                    page.mouse.down()
                    page.mouse.move(x + 20, y - 30, steps=10)
                    page.mouse.up()
                else:
                    grip = page.locator(f"{CAPTURE} .desk-window-grip").bounding_box()
                    x, y = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                    page.mouse.move(x, y)
                    page.mouse.down()
                    page.mouse.move(x - 218, y + 32, steps=12)
                    page.mouse.up()
                page.wait_for_timeout(500)
                before = page.evaluate(GEOMETRY)
                facts["before"] = before
                self._send_card(page)
                with_card = page.evaluate(GEOMETRY)
                facts["with_card"] = with_card
                page.screenshot(path=str(SHOTS / f"A1c-r2-{how}-1440-card.png"))
                if with_card["host"] != "Capture":
                    fails.append(f"{how}: the card is in {with_card['host']}, not Capture")
                if with_card["fixed"]:
                    fails.append(f"{how}: a fixed card floats")
                if not _same(before["capture"], with_card["capture"]):
                    fails.append(f"{how}: Capture moved with the card {before['capture']} -> {with_card['capture']}")
                facts["readable"] = self._readable(page, fails, how)
                page.screenshot(path=str(SHOTS / f"A1c-r2-{how}-1440-scrolled.png"))
                self._dismiss(page)
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                if not _same(before["capture"], after["capture"]):
                    fails.append(f"{how}: Dismiss did not keep Capture {before['capture']} -> {after['capture']}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / f"A1c-r2-{how}-facts.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1))
                browser.close()
        assert not fails, fails

    # ── the fences ───────────────────────────────────────────────────────

    def test_closed_capture_opens_and_holds_the_whole_card(self) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._open_chair(page, "Needs you")
                if page.locator(f".desk-window-shell{CAPTURE}").count():
                    fails.append("Capture is open before the card")
                self._send_card(page)
                g = page.evaluate(GEOMETRY)
                facts["with_card"] = g
                page.screenshot(path=str(SHOTS / "A1c-r2-default-1440-card.png"))
                if g["host"] != "Capture":
                    fails.append(f"default: the card is in {g['host']}, not Capture")
                if g["fixed"]:
                    fails.append("default: a fixed card floats")
                cap, needs = g["capture"], g["needs"]
                if cap and needs and cap["y"] < needs["y"] + needs["h"] - 1 and cap["x"] < needs["x"] + needs["w"]:
                    fails.append(f"default: Capture {cap} covers Needs you {needs}")
                facts["readable"] = self._readable(page, fails, "default")
                scroll = facts["readable"]["scroll"]
                if scroll["height"] > scroll["client"] + 1:
                    fails.append(f"default: the grown Capture still scrolls {scroll}")
                self._dismiss(page)
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                if not after["capture"] or after["capture"]["h"] >= cap["h"] - 50:
                    fails.append(f"default: Capture did not return to its seat {cap} -> {after['capture']}")
                if after["capture"] and abs(after["capture"]["y"] + after["capture"]["h"] - cap["y"] - cap["h"]) > 2:
                    fails.append(f"default: Capture's foot moved {cap} -> {after['capture']}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / "A1c-r2-default-facts.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1))
                browser.close()
        assert not fails, fails

    def test_moved_capture_keeps_its_rect_and_the_card_scrolls_whole(self) -> None:
        self._arranged("moved")

    def test_resized_capture_keeps_its_rect_and_the_card_scrolls_whole(self) -> None:
        self._arranged("resized")

    def test_card_in_meetings_does_not_move_capture(self) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._open_chair(page, "Needs you")
                self._open_chair(page, "Capture")
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                page.locator(".desk-verbbar-menu").get_by_role("menuitem", name=re.compile(r"^Meetings")).click()
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                meetings.locator("[data-aftercare-window-slot]").first.wait_for(state="attached")
                page.wait_for_timeout(600)
                before = page.evaluate(GEOMETRY)
                facts["before"] = before
                self._send_card(page)
                with_card = page.evaluate(GEOMETRY)
                facts["with_card"] = with_card
                page.screenshot(path=str(SHOTS / "A1c-r2-meetings-1440-card.png"))
                if with_card["host"] != "Meetings":
                    fails.append(f"meetings: the card is in {with_card['host']}, not Meetings")
                if not _same(before["capture"], with_card["capture"]):
                    fails.append(f"meetings: Capture moved {before['capture']} -> {with_card['capture']}")
                self._dismiss(page)
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                if not _same(before["capture"], after["capture"]):
                    fails.append(f"meetings: Capture moved after Dismiss {before['capture']} -> {after['capture']}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / "A1c-r2-meetings-facts.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1))
                browser.close()
        assert not fails, fails
