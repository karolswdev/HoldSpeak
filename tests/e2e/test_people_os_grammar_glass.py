"""People selection, keyboard/menu parity and bounded wells at the owner's sizes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = "people-os-grammar"


@pytest.mark.timeout(240)
def test_people_selection_grammar_and_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    root = Path(__file__).resolve().parents[2]
    shots = root / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    try:
        week = open_rig._seed(tmp_path / "home", base)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                _open(page, base)
                window = page.locator("#surface-people")
                roster = window.get_by_test_id("people-roster")
                _settle(page)
                suffix = "900x600" if width == 1440 else "393"

                def shoot(state: str) -> None:
                    _settle(page)
                    _bounded(window)
                    page.screenshot(path=str(shots / f"people-{state}-{suffix}-after.png"))

                shoot("list")
                rows = roster.locator('[role=row][data-object-id]')
                assert rows.count() > 0
                assert all(abs(row.bounding_box()["height"] - 26) < 1 if width == 1440 else row.bounding_box()["height"] >= 44 for row in rows.all())
                assert rows.locator("button").count() == 0
                expect(roster.get_by_role("button", name="Open", exact=True)).to_be_disabled()
                assert roster.locator(".surface-spine, .people-now, h1").count() == 0
                assert roster.get_by_text("Your name is not set", exact=True).count() == 0
                priya = roster.locator(f'[data-object-id="{week["priya"]}"]')
                priya.click()
                expect(priya).to_have_attribute("aria-selected", "true")
                expect(roster.get_by_test_id("people-summary")).to_contain_text(open_rig.COMMITMENT)
                assert page.locator('[data-testid=person-window]').count() == 0
                shoot("selected")
                priya.press("Home")
                expect(rows.first).to_be_focused()
                rows.first.press("End")
                expect(rows.last).to_be_focused()
                rows.last.press("ArrowUp")
                expect(rows.nth(rows.count() - 2)).to_be_focused()
                priya.click(button="right")
                menu = page.get_by_role("menu", name="People actions", exact=True)
                expect(menu.get_by_role("menuitem", name="Prep 1:1", exact=False)).to_be_visible()
                shoot("context-menu")
                page.keyboard.press("Escape")
                expect(priya).to_be_focused()
                switcher = page.get_by_test_id("desk-screen-switcher")
                if switcher.is_visible():
                    switcher.click()
                    page.get_by_role("menuitem", name="People", exact=True).click()
                    app_menu = page.get_by_role("menu").last
                else:
                    page.get_by_test_id("desk-screen-title").get_by_role("button", name="People", exact=True).click()
                    app_menu = page.get_by_role("menu", name="People menu", exact=True)
                expect(app_menu.get_by_role("menuitem", name="Prep 1:1", exact=False)).to_be_visible()
                shoot("app-menu")
                page.keyboard.press("Escape")
                priya.press("Enter")
                expect(page.get_by_test_id("person-window")).to_be_visible()
                # Open uses the existing own window. Close it and keep the roster's selection.
                _api(page, "POST", f"/api/desk/windows/pullout:people:{week['priya']}/close", {}, token=TOKEN)
                expect(page.get_by_test_id("person-window")).not_to_be_visible()
                _settle(page)
                roster.get_by_role("button", name="Add person", exact=True).click()
                shoot("add")
                name = roster.get_by_role("textbox", name="Add person", exact=True)
                name.fill(f"Keep these words {width}")
                # A failed owner write retains the entered name and the same inspector.
                page.route("**/api/people/relationships", lambda route: route.fulfill(status=503, json={"detail": "people_store_unavailable"}))
                with page.expect_response(lambda response: response.url.endswith("/api/people/relationships") and response.request.method == "POST") as saved:
                    roster.get_by_role("button", name="Add", exact=True).click()
                assert saved.value.status == 503
                expect(roster.get_by_test_id("people-failure")).to_be_visible()
                expect(name).to_have_value(f"Keep these words {width}")
                shoot("save-failed")
                page.unroute("**/api/people/relationships")
                roster.get_by_role("button", name="Try again", exact=True).click()
                expect(name).to_have_value("")
                expect(roster.get_by_role("row", name=f"Keep these words {width}", exact=False)).to_be_visible()
                name.fill(f"Keep these words {width}")
                roster.get_by_role("button", name="Add", exact=True).click()
                expect(roster.get_by_test_id("people-duplicate")).to_be_visible()
                shoot("duplicate")
                roster.get_by_role("region", name="New person", exact=True).get_by_role("button", name="Cancel", exact=True).click()
                roster.get_by_role("textbox", name="Find a person").fill("no such name")
                expect(roster.get_by_test_id("people-summary")).to_contain_text("No names match")
                shoot("no-match")
                assert errors == [], errors
                page.close()

                # Empty, suggestions and unavailable states use real recorded producer answers.
                wire = json.loads((root / "web/src/desk/__tests__/fixtures/daily-week/people-from-work.json").read_text())
                for state in ("empty", "suggestions", "read-failed", "locked", "recovery", "no-key-store"):
                    clear_hub_windows_http(base, TOKEN)
                    page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                    if state in ("empty", "suggestions"):
                        for endpoint in ("/api/people/readiness", "/api/people/relationships", "/api/people/suggestions"):
                            payload = wire["before"].get(endpoint, {"relationships": []})
                            if endpoint.endswith("suggestions") and state == "empty":
                                payload = {"suggestions": []}
                            page.route(f"**{endpoint}*", lambda route, _request, payload=payload: route.fulfill(json=payload))
                    else:
                        readiness = {"read-failed": "unavailable", "locked": "locked", "recovery": "key_unavailable", "no-key-store": "no_key_store"}[state]
                        page.route("**/api/people/readiness", lambda route, _request, readiness=readiness: route.fulfill(json={"readiness": readiness}))
                    _open(page, base)
                    page.get_by_test_id({"empty": "people-empty-roster", "suggestions": "people-suggestion", "read-failed": "people-read-failed", "locked": "people-read-failed", "recovery": "people-joy-state", "no-key-store": "people-not-here"}[state]).first.wait_for()
                    _settle(page)
                    if state == "suggestions":
                        page.get_by_test_id("people-suggestion").first.click()
                    page.screenshot(path=str(shots / f"people-{state}-{suffix}-after.png"))
                    page.close()
            browser.close()
    finally:
        server.stop()


def _open(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'open-people'}))")
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator("#surface-people").wait_for(timeout=10_000)
    if page.viewport_size["width"] == 1440:
        # The frame mounts before its asynchronous hub open is acknowledged.
        page.wait_for_function("""async token => {
          const response = await fetch('/api/desk/windows', {headers: {Authorization: `Bearer ${token}`}});
          const body = await response.json();
          return body.windows?.some(row => row.id === 'surface-people');
        }""", arg=TOKEN)
        _api(page, "POST", "/api/desk/windows/surface-people/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)


def _bounded(window: Any) -> None:
    assert window.evaluate("""el => {
      const body = el.querySelector('.desk-surface-body');
      const list = el.querySelector('.surface-list-pane');
      return body.scrollHeight <= body.clientHeight + 1 && body.scrollWidth <= body.clientWidth + 1
        && (!list || list.scrollHeight <= list.clientHeight + 1);
    }"""), window.bounding_box()


@pytest.mark.timeout(240)
def test_people_shared_list_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-shoot the two roster poses after adopting Meetings' shared ListPane."""
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        week = open_rig._seed(tmp_path / "home", base)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                _open(page, base)
                roster = page.get_by_test_id("people-roster")
                row = roster.locator(f'[data-object-id="{week["priya"]}"]')
                row.wait_for()
                page.get_by_test_id("people-next-reading").wait_for(state="detached")
                suffix = "900x600" if width == 1440 else "393"
                _settle(page)
                _bounded(page.locator("#surface-people"))
                page.screenshot(path=str(shots / f"people-list-{suffix}-after.png"))
                row.click()
                expect(roster.get_by_test_id("people-summary")).to_contain_text(open_rig.COMMITMENT)
                _settle(page)
                _bounded(page.locator("#surface-people"))
                page.screenshot(path=str(shots / f"people-selected-{suffix}-after.png"))
                page.close()
            browser.close()
    finally:
        server.stop()
