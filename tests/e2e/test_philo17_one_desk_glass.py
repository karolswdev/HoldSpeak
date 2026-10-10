"""PHILO-17 one desk -- the Screen is the one desk, fenced AS RENDERED.

Owner ruling 2026-10-10, verbatim: "Yes, everything must become one desk."
Through the real hub on an isolated HOME at 1440x900 (mouse) and 393x852
(touch):

* a workspace that stored ``screen: "floor"`` loads the Screen (no Floor face);
* the Dock has no Floor button;
* the Needs-you drawer icon is on the desk;
* nothing on the page carries ``data-zone-id`` (a zone with a member is seeded);
* Send from the desk: a decision opened from its desk icon, its window menu
  ``Send to ▸`` -> the FILE destination -> the preview -> Send writes the file
  and the hub records one send.

The Floor never drew destination icons: Phase 12's drag-to-send was folded
into ``Send to ▸`` (PHILO-13-15 C5, commit 7bfe756ac), and
``floorSendBinding.resolve`` stays live under ``windowSend.tsx``. So the send
leg proves the surviving path from the one desk, not a drag.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the one-desk glass needs Playwright")

TOKEN = "philo17-one-desk"
SHOTS = evidence_dir("p17-one-desk")
SIZES = {1440: 900, 393: 852}
T = 20_000
DECISION = "Freeze the old ledger on Nov 5"
WORKSPACE = "hs.desk.workspace.v1"


class TestOneDesk:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            server.stop()

    def _sends(self, ref: str) -> list[dict[str, Any]]:
        with self.db._connection() as conn:
            rows = conn.execute(
                "SELECT id, state FROM channel_sends WHERE document_ref = ?", (ref,)).fetchall()
        return [{"id": r[0], "state": r[1]} for r in rows]

    def _tap(self, page: Any, loc: Any, phone: bool, ms: int = 700) -> None:
        loc = loc.first
        loc.scroll_into_view_if_needed()
        if phone:
            b = loc.bounding_box()
            page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        else:
            loc.click()
        page.wait_for_timeout(ms)

    def _window_menu(self, page: Any, win: str, phone: bool) -> None:
        head = page.locator(f"[id='{win}'] > .desk-pullout-head")
        t = head.locator(".desk-pullout-title").first
        b = t.bounding_box() if t.count() and t.is_visible() else head.first.bounding_box()
        x, y = b["x"] + min(b["width"] - 4, max(8, b["width"] / 2)), b["y"] + b["height"] / 2
        if phone:
            cdp = page.context.new_cdp_session(page)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]})
            page.wait_for_timeout(750)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            cdp.detach()
            page.wait_for_timeout(500)
        else:
            page.mouse.click(x, y, button="right")
            page.wait_for_timeout(500)
        page.locator("[role=menu]").first.wait_for(timeout=10_000)

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_screen_is_the_one_desk(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        phone = width <= 720
        scratch = Path(tempfile.mkdtemp(prefix="p17od-", dir="/tmp"))
        folder = scratch / "Team updates"
        folder.mkdir()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                      has_touch=phone, reduced_motion="reduce")
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                made = _api(page, "POST", "/api/decisions",
                            {"title": DECISION, "status": "accepted",
                             "decision_markdown": "Freeze writes to the old ledger on Nov 5."}, token=TOKEN)
                decision_id = made["decision"]["id"]
                # A zone with a member: the zone data stays; no face draws it.
                zone = _api(page, "POST", "/api/directories", {"name": "Payments"}, token=TOKEN)
                zid = (zone.get("directory") or zone)["id"]
                note = _api(page, "POST", "/api/notes", {"title": "Cutover runbook", "body": "Steps"}, token=TOKEN)
                nid = (note.get("note") or note)["id"]
                _api(page, "PUT", f"/api/directories/{zid}/members/note:{nid}", {}, token=TOKEN)
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)

                # 1. A workspace that stored the Floor loads the Screen.
                page.evaluate("""(key) => { const raw = localStorage.getItem(key);
                    const doc = raw ? JSON.parse(raw) : { version: 1 };
                    doc.version = 1; doc.screen = 'floor';
                    localStorage.setItem(key, JSON.stringify(doc)); }""", WORKSPACE)
                page.reload(wait_until="load")
                _normal_chair(page)
                stored = page.evaluate("(key) => JSON.parse(localStorage.getItem(key) || '{}').screen", WORKSPACE)
                assert stored == "floor", stored  # the stored value is kept; it no longer decides the face
                page.locator("[data-testid=desk-screen]").wait_for(timeout=T)
                icon = page.locator(f".desk-screen [data-object-id='decision:{decision_id}']")
                icon.wait_for(timeout=T)
                assert page.locator(".desk-world-a11y, .desk-listmode").count() == 0, "a Floor face mounted"

                # 2. No Floor button on the Dock.
                page.locator(".desk-dock").first.wait_for(timeout=T)
                assert page.locator("[data-testid=chair-floor-toggle]").count() == 0
                assert page.locator(".desk-dock").get_by_role("button", name="Floor", exact=True).count() == 0

                # 3. The Needs-you drawer is on the desk.
                needs = page.locator(".desk-screen [data-object-id='drawer:needs']")
                needs.wait_for(state="attached", timeout=T)
                assert (needs.get_attribute("aria-label") or "").startswith("Needs you"), needs.get_attribute("aria-label")

                # 4. Nothing draws a zone.
                assert page.locator("[data-zone-id]").count() == 0
                _settle(page)
                page.screenshot(path=str(SHOTS / f"one-desk-{width}.png"))

                # 5. Send from the desk: the icon opens the decision's window; its
                #    window menu Send to ▸ -> the FILE destination -> preview -> Send.
                win = f"pullout:decision:{decision_id}"
                icon.scroll_into_view_if_needed()
                icon.focus()
                page.keyboard.press("Enter")
                page.locator(f"[id='{win}']").wait_for(timeout=T)
                page.wait_for_timeout(1200)
                self._window_menu(page, win, phone)
                first = page.locator("[role=menu] [role^=menuitem]").first.inner_text()
                assert first.startswith("Send to"), first
                sub = page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Send to')").first
                if phone:
                    self._tap(page, sub, phone)
                else:
                    sub.hover()
                    page.wait_for_timeout(700)
                self._tap(page, page.locator("[role=menu] [role^=menuitem]:has-text('Team updates')").last, phone, 900)
                ref = f"desk_decision:{decision_id}"
                well = page.locator(f"[id='{win}'] [data-testid=send-well][data-doc='{ref}']")
                well.locator("[data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
                assert self._sends(ref) == [], "the pick sent; only Send sends"
                _settle(page)
                page.screenshot(path=str(SHOTS / f"one-desk-send-preview-{width}.png"))
                self._tap(page, well.locator("[data-testid=send-open] [data-testid=send-verbs] .btn--primary"), phone, 1800)
                well.locator("[data-testid=send-open] [data-testid=send-sent]").wait_for(timeout=T)
                sends = self._sends(ref)
                assert len(sends) == 1 and sends[0]["state"] == "sent", sends
                written = [p for p in folder.rglob("*") if p.is_file()]
                assert written and "freeze" in written[0].read_text().lower(), written
                page.screenshot(path=str(SHOTS / f"one-desk-send-saved-{width}.png"))
                (SHOTS / f"one-desk-{width}.json").write_text(json.dumps(
                    {"written": [p.name for p in written], "sends": sends}, indent=2))
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()
                shutil.rmtree(scratch, ignore_errors=True)
