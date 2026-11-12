"""D material in the real frame, using the existing seeded People rig."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_people_os_grammar_glass import TOKEN, _open

OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/material12"


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(240)
def test_mast_selection_and_instrument_strip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        week = open_rig._seed(tmp_path / "home", base)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _open(page, base)
            win = page.locator("#surface-people")
            head = win.locator(":scope > .desk-pullout-head")
            expect(head.locator(".surface-mast-facts")).to_contain_text("4 people")
            owed = sum(row.get("you_owe_count", 0) for row in open_rig._http(base, "GET", "/api/people/relationships?counts=1")["relationships"])
            expect(head.locator('[data-tone="ask"] dd')).to_have_text(str(owed))
            expect(head).to_have_css("height", "58px" if width == 1440 else "52px")
            assert head.locator(".surface-mast-object img").count() == 1
            assert win.locator(".kit-statusbar-clock").count() == 1
            expect(win.locator(".kit-statusbar")).to_have_css("background-color", "rgb(16, 25, 43)")
            assert "31, 63, 128" in head.evaluate("el => getComputedStyle(el).backgroundImage")
            suffix = 900 if width == 1440 else 393

            def shot(app: str, state: str) -> None:
                _settle(page)
                page.screenshot(path=str(OUT / f"{app}-{state}-{suffix}.png"))

            shot("people", "list")
            row = win.locator(f'[data-object-id="{week["priya"]}"]')
            row.click()
            expect(row).to_have_attribute("aria-selected", "true")
            expect(row.locator(".surface-lamp")).to_have_attribute("data-state", "waiting")
            assert "inset" in row.evaluate("el => getComputedStyle(el).boxShadow")
            assert row.locator(".surface-lamp").evaluate("el => getComputedStyle(el).animationName") == "none"
            shot("people", "selected")
            page.emulate_media(reduced_motion="no-preference")
            assert row.locator(".surface-lamp").evaluate("el => getComputedStyle(el).animationName") != "none"
            page.emulate_media(reduced_motion="reduce")
            win.get_by_role("button", name="Add person", exact=True).click()
            expect(win.get_by_test_id("people-add-row")).to_be_visible()
            shot("people", "form")
            win.get_by_role("textbox", name="Add person", exact=True).fill("Alex Chen")
            page.route("**/api/people/relationships", lambda route: route.abort("failed") if route.request.method == "POST" else route.continue_())
            win.get_by_role("button", name="Add", exact=True).click()
            expect(win.get_by_role("button", name="Try again", exact=True)).to_be_visible()
            expect(win.get_by_role("textbox", name="Add person", exact=True)).to_have_value("Alex Chen")
            expect(win.locator('.kit-statusbar-item[data-required="true"]')).to_contain_text("Failed")
            shot("people", "failure")
            win.get_by_role("button", name="Cancel", exact=True).click()
            _api(page, "POST", "/api/desk/windows/surface-meetings/open", {}, token=TOKEN)
            meeting = page.locator("#surface-meetings")
            expect(meeting.locator(".surface-mast-title")).to_have_text("Meetings")
            shot("meetings", "list")
            _api(page, "POST", "/api/desk/windows/surface-meetings/open", {"object_ref": "meeting:m-standup"}, token=TOKEN)
            expect(meeting.get_by_test_id("meeting-record")).to_be_visible()
            expect(meeting.locator(".surface-mast-title")).to_have_text("Ledger cutover sync")
            expect(meeting.locator(".surface-mast-facts")).to_contain_text("Meeting")
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-meetings/set_geometry", {"rect": {"x": "-1/2 + 110", "y": "-1/2 + 100", "w": "900px", "h": "600px"}}, token=TOKEN)
            shot("meeting-reader", "summary")
            if width == 1440:
                # The same Desk holds three actual windows and two resting Masts.
                _api(page, "POST", "/api/desk/windows/surface-projects/open", {"geometry": {"x": "-1/2 + 500", "y": "-1/2 + 220", "w": 780, "h": 600}}, token=TOKEN)
                expect(page.locator("#surface-projects")).to_be_visible()
                shot("desk", "three-windows")
            assert not errors, errors
            context.close()
            browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_empty_collections_keep_their_mast_and_new_verb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            # The unseeded isolated hub is the producer of these empty answers.
            for app, seat, title, verb in (("programs", "surface-programs", "Programs", "New program"), ("automations", "surface-workbenches", "Automations", "New automation"), ("projects", "surface-projects", "Projects", "New project"), ("recordings", "surface-recordings", "Recordings", "New recording")):
                clear_hub_windows_http(base, TOKEN)
                _api(page, "POST", f"/api/desk/windows/{seat}/open", {}, token=TOKEN)
                if width == 1440:
                    _api(page, "POST", f"/api/desk/windows/{seat}/set_geometry", {"rect": {"x": "-1/2 + 110", "y": "-1/2 + 100", "w": "900px", "h": "600px"}}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win = page.locator(f"#{seat}")
                expect(win.get_by_role("button", name=verb, exact=True)).to_be_enabled()
                expect(win.locator(".surface-mast-title")).to_have_text(title)
                expect(win.locator(":scope > .desk-pullout-head")).to_have_css("height", "58px" if width == 1440 else "52px")
                _settle(page)
                assert win.locator(".object-list-row").count() == 0
                assert win.locator(".surface-mast-figures").count() == 0
                page.screenshot(path=str(OUT / f"{app}-empty-{900 if width == 1440 else 393}.png"))
            browser.close()
    finally:
        server.stop()
