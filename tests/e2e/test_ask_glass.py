"""The Ask window, AS RENDERED: what only a real browser proves (the test diet).

Betterment Q6 (docs/internal/betterment/asking/RECIPE.md): a desk object
dropped on the Ask window becomes an About chip. The drop is a real HTML drag
from the Screen's note icon (the hand's drag: `hand/drag.ts`) onto the window,
through the real hub on an isolated HOME at 1440 x 900. The phone (393) has no
loose Screen icons to drag; its About is the picker
(web/src/desk/components/about/__tests__/about.app.test.tsx).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair

pytest.importorskip("playwright.sync_api", reason="the Ask glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "ask-glass"
T = 20_000
NOTE_ID, NOTE = "n-mira", "1:1 with Mira"
ICON = f".desk-screen [data-object-id='note:{NOTE_ID}']"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    PrimitiveService(get_database()).create_note(
        Principal(PrincipalKind.OWNER, "karol"), note_id=NOTE_ID, title=NOTE,
        body_markdown="Feedback on her cutover design doc is due Friday.", tags=[])
    try:
        yield base
    finally:
        server.stop()


def test_1440_a_screen_note_dropped_on_ask_becomes_an_about_chip(hub: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                                   reduced_motion="reduce").new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        try:
            page.goto(f"{hub}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            page.locator(ICON).wait_for(timeout=T)
            page.keyboard.press("Control+KeyI")
            body = page.get_by_test_id("ask-body")
            body.wait_for(timeout=T)
            about = page.get_by_test_id("ask-context")
            assert "My whole desk" in about.inner_text()
            # The window opens over the Screen's icons: move it by its title
            # strip until the note's icon is clear.
            icon_box = page.locator(ICON).bounding_box()
            frame = page.locator("[id='ask']")
            box = frame.bounding_box()
            assert icon_box and box
            grab = (box["x"] + 120, box["y"] + 12)
            shift = max(0.0, icon_box["y"] + icon_box["height"] + 24 - box["y"])
            page.mouse.move(*grab)
            page.mouse.down()
            page.mouse.move(grab[0], grab[1] + shift / 2, steps=6)
            page.mouse.move(grab[0], grab[1] + shift, steps=6)
            page.mouse.up()
            moved = frame.bounding_box()
            assert moved and moved["y"] > icon_box["y"] + icon_box["height"], (icon_box, moved)
            page.locator(ICON).drag_to(body)
            about.get_by_test_id("ask-about-chip").filter(has_text=NOTE).wait_for(timeout=T)
            assert "My whole desk" not in about.inner_text()
            assert not errors, errors
        finally:
            browser.close()
