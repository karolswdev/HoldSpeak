"""PHILO-17 U08: a thought is sendable -- fenced AS RENDERED.

The fault (usability inventory, U08): he wrote a thought to send, and the
Thought window had only Change and Finish. Finish kept it; there was no Send
and no Copy. A note was not a sendable kind.

Through the real hub on an isolated HOME, at 1440x900 and 393x852: Desk >
Write a thought, the words typed, then the foot's Send opens the SEND well on
the working note. The built-in HoldSpeak folder is the one destination of a
fresh desk, so it is picked and its preview shows where the note goes. His
press of Send saves the file; the receipt says SAVED with the path. Nothing
leaves the machine.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .chair_windows import go_group
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the thought glass needs Playwright")

TOKEN = "philo17-thought-send"
SHOTS = evidence_dir("tests/e2e/shots/philo17-thought-send")
SIZES = {1440: 900, 393: 852}
THOUGHT = ".desk-window.thought-workspace-window"
WORDS = "Pilot plan: we start on Monday and Avery owns the rollout"
T = 20_000


class TestTheThoughtSends:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _menu_thought(self, page: Any, width: int) -> None:
        menu = "desk" if width >= 720 else "go"
        page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
        if width < 720:
            go_group(page, "New", lambda loc: loc.click())
        label = "Write a thought" if width >= 720 else "Thought"
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first
        item.wait_for()
        item.click()

    @staticmethod
    def _tap(page: Any, loc: Any) -> None:
        """A real pointer press at the verb's place (an inert well takes no press)."""
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        assert box, "the well's Send is not on the glass"
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_write_a_thought_then_send_it_to_a_folder(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
            ctx.grant_permissions(["clipboard-read", "clipboard-write"])
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)

                self._menu_thought(page, width)
                win = page.locator(THOUGHT)
                win.wait_for()
                page.keyboard.type(WORDS)  # no wait: Send saves the note first

                foot = win.locator(".thought-note-foot")
                verbs = [" ".join(t.split()) for t in foot.locator(".btn").all_inner_texts()]
                assert verbs[-4:] == ["Change", "Copy", "Send", "Finish"], verbs

                # Copy copies the working text.
                foot.get_by_role("button", name="Copy").click()
                foot.get_by_text("COPIED").wait_for(timeout=T)
                assert WORDS in page.evaluate("navigator.clipboard.readText()")

                # Send opens the SEND well on the working note; nothing is sent yet.
                foot.get_by_role("button", name="Send").click()
                well = win.locator("[data-testid=send-well][data-doc^='note:']")
                well.wait_for(timeout=T)
                note_ref = well.get_attribute("data-doc")
                opened = well.locator("[data-testid=send-open][data-destination='HoldSpeak folder']")
                opened.locator("[data-testid=send-preview]").wait_for(timeout=T)
                preview = " ".join(opened.locator("[data-testid=send-preview]").inner_text().split())
                assert "Monday" in preview, preview
                assert not _api(page, "GET", f"/api/channels/sends?document_ref={note_ref}", token=TOKEN)["sends"]
                page.screenshot(path=str(SHOTS / f"thought-send-picked-{width}.png"))

                # Astra r1 MUST: an edit after the well opened, its save held. The
                # well waits (inert, a plain word); a press on it sends nothing.
                held: list[Any] = []
                mode = {"saves": "hold"}

                def saves(route: Any) -> None:
                    if mode["saves"] == "hold":
                        held.append(route)
                    elif mode["saves"] == "fail":
                        route.abort()
                    else:
                        route.continue_()

                page.route("**/api/thoughts/*/working", saves)
                note = win.locator(".thought-note-body .cm-content").first
                note.click()
                page.keyboard.press("End")
                page.keyboard.type(" REVISED")
                verb = opened.locator("[data-testid=send-verb]")
                self._tap(page, verb)
                for _ in range(100):  # the writer's held save reaches the route
                    if held:
                        break
                    page.wait_for_timeout(50)
                assert held, "the edit was never saved"
                assert not _api(page, "GET", f"/api/channels/sends?document_ref={note_ref}", token=TOKEN)["sends"], \
                    "the well sent while the edit was not saved"
                assert win.locator(".thought-send-body[inert]").count() == 1
                win.get_by_text("SAVING… · SEND WAITS").wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"thought-send-waits-{width}.png"))
                mode["saves"] = "pass"
                for route in held:
                    route.continue_()
                # The save lands: the well opens again on a preview of the revised words.
                win.locator(".thought-send-body:not([inert])").wait_for(timeout=T)
                page.wait_for_function(
                    "(sel) => (document.querySelector(sel)?.innerText || '').includes('REVISED')",
                    arg=f"{THOUGHT} [data-testid=send-open][data-destination='HoldSpeak folder'] [data-testid=send-preview]",
                    timeout=T)

                # His press: the file is saved, the receipt names the path.
                page.wait_for_function("(e) => e && !e.disabled", arg=verb.element_handle(), timeout=T)
                verb.click()
                receipt = opened.locator("[data-receipt=latest][data-state=sent]")
                receipt.wait_for(timeout=T)
                sends = _api(page, "GET", f"/api/channels/sends?document_ref={note_ref}", token=TOKEN)["sends"]
                sent = [s for s in sends if s["state"] == "sent"]
                assert len(sent) == 1, sends
                path = Path(sent[0]["proof"]["path"])
                assert path.is_file() and f"{WORDS} REVISED" in path.read_text(), path
                text = " ".join(receipt.inner_text().split())
                # The built-in folder names its path from HOME (~).
                assert text == f"✓ SAVED ~/Documents/HoldSpeak/Sent/{path.name}", text
                receipt.scroll_into_view_if_needed()
                page.screenshot(path=str(SHOTS / f"thought-send-saved-{width}.png"))

                # A failed save: the well stays held with a plain word; nothing more is sent.
                mode["saves"] = "fail"
                note.click()
                page.keyboard.press("End")
                page.keyboard.type(" LOST")
                win.get_by_text("NOT SAVED · SEND WAITS").wait_for(timeout=T)
                assert win.locator(".thought-send-body[inert]").count() == 1
                self._tap(page, opened.locator("[data-testid=send-verb]"))
                page.wait_for_timeout(600)
                after = _api(page, "GET", f"/api/channels/sends?document_ref={note_ref}", token=TOKEN)["sends"]
                assert len(after) == 1, after
                mode["saves"] = "pass"

                assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "page scrolls sideways"
                assert not errors, errors
            finally:
                browser.close()
