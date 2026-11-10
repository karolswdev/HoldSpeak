"""Projects uses the shared selection list and keeps its Room doors."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = "projects-os-grammar"


def _open(page: Any, base: str) -> Any:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key:'open-projects'}))")
    page.reload(wait_until="load")
    _normal_chair(page)
    window = page.locator("#surface-projects")
    window.wait_for(timeout=10_000)
    page.wait_for_function("""async token => (await (await fetch('/api/desk/windows',
      {headers:{Authorization:`Bearer ${token}`}})).json()).windows?.some(w => w.id === 'surface-projects')""", arg=TOKEN)
    if page.viewport_size["width"] == 1440:
        _api(page, "POST", "/api/desk/windows/surface-projects/set_geometry", {"rect": {
            "x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
    _settle(page)
    return window


@pytest.mark.timeout(240)
def test_projects_selection_and_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright, expect
    from .test_desk_sweep import LIST_GRAMMAR_JS, _start_app_walk, _finish_app_walk

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    root = Path(__file__).resolve().parents[2]
    wire = json.loads((root / "web/src/pages/cores/__tests__/fixtures/projects/recorded.json").read_text())
    shots = root / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    from holdspeak.db import get_database
    for project in wire["gets"]["/api/projects"]["projects"]:
        get_database().projects.create_project(project_id=project["id"], name=project["name"], description="", keywords=[])
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                for state in ("list", "selected", "read-failed", "loading", "empty"):
                    clear_hub_windows_http(base, TOKEN)
                    page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                    errors: list[str] = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.clock.set_fixed_time("2026-10-19T04:00:00Z")
                    gets = wire["gets"]
                    page.route("**/api/projects", lambda route: route.fulfill(json={"projects": []} if state == "empty" else gets["/api/projects"]))
                    held: list[Any] = []
                    for endpoint, payload in gets.items():
                        if not endpoint.endswith("/room"):
                            continue
                        def room(route: Any, _request: Any, payload: Any = payload) -> None:
                            if state == "loading":
                                held.append((route, payload))
                            elif state == "read-failed":
                                route.fulfill(status=503, json={"detail": "room_unavailable"})
                            else:
                                route.fulfill(json=payload)
                        page.route(f"**{endpoint}", room)
                    window = _open(page, base)
                    if state in ("list", "selected", "read-failed"):
                        window.get_by_test_id("projects-row").first.wait_for()
                    if state == "selected":
                        window.get_by_test_id("projects-row").last.click()
                    def shoot(pose: str) -> None:
                        _settle(page)
                        assert window.evaluate("""el => {
                          const body = el.querySelector('.desk-surface-body');
                          const pane = el.querySelector('.surface-preference-pane');
                          return body.scrollHeight <= body.clientHeight + 1 && body.scrollWidth <= body.clientWidth + 1
                            && pane.scrollHeight <= pane.clientHeight + 1;
                        }"""), window.bounding_box()
                        assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-projects")
                        page.screenshot(path=str(shots / f"projects-{pose}-{'900x600' if width == 1440 else '393'}-after.png"))

                    shoot(state)
                    if state == "list":
                        rows = window.get_by_test_id("projects-row")
                        assert rows.locator("button").count() == 0
                        assert window.locator("h1, h2, h3, .surface-spine, .projects-plate").count() == 0
                        expect(window.get_by_role("button", name="Open Room", exact=True)).to_be_disabled()
                        assert all(abs(row.bounding_box()["height"] - (26 if width == 1440 else 44)) < 1 for row in rows.all())
                        rows.first.click()
                        expect(rows.first).to_have_attribute("aria-selected", "true")
                        expect(window.get_by_test_id("projects-reason")).to_contain_text("1 milestone late")
                        expect(window.get_by_test_id("projects-update")).to_contain_text("Update drafted")
                        shoot("risk-selected")
                        expect(window.get_by_role("button", name="Done", exact=True)).to_have_count(0)
                        rows.first.click()
                        rows.first.press("End")
                        expect(rows.last).to_be_focused()
                        expect(rows.last).to_have_attribute("aria-selected", "true")
                        expect(window.get_by_test_id("projects-next")).to_have_text("No date set")
                        rows.last.press("ArrowUp")
                        expect(rows.first).to_be_focused()
                        rows.first.press("Home")
                        expect(rows.first).to_be_focused()
                        rows.first.click(button="right")
                        menu = page.get_by_role("menu", name="Projects actions", exact=True)
                        expect(menu.get_by_role("menuitem", name="Open Room", exact=False)).to_be_visible()
                        expect(menu.get_by_role("menuitem", name="New project", exact=False)).to_be_visible()
                        shoot("context-menu")
                        page.keyboard.press("Escape")
                        expect(rows.first).to_be_focused()
                        switcher = page.get_by_test_id("desk-screen-switcher")
                        if switcher.is_visible():
                            switcher.click()
                            page.get_by_role("menuitem", name="Projects", exact=True).click()
                            menu = page.get_by_role("menu").last
                        else:
                            page.get_by_test_id("desk-screen-title").get_by_role("button", name="Projects", exact=True).click()
                            menu = page.get_by_role("menu", name="Projects menu", exact=True)
                        expect(menu.get_by_role("menuitem", name="Open Room", exact=False)).to_be_visible()
                        expect(menu.get_by_role("menuitem", name="Show me", exact=True)).to_have_count(0)
                        shoot("app-menu")
                        page.keyboard.press("Escape")
                        # Both keyboard and double-click preserve the existing own-window door.
                        for activate in (lambda: rows.first.press("Enter"), lambda: rows.first.dblclick()):
                            activate()
                            room_window = page.locator("#surface-project-memory")
                            expect(room_window).to_be_visible()
                            page.wait_for_function("""async token => (await (await fetch('/api/desk/windows',
                              {headers:{Authorization:`Bearer ${token}`}})).json()).windows?.some(w => w.id === 'surface-project-memory')""", arg=TOKEN)
                            _api(page, "POST", "/api/desk/windows/surface-project-memory/close", {}, token=TOKEN)
                            expect(room_window).not_to_be_visible()
                            _settle(page)
                        find = window.get_by_role("textbox", name="Find a project", exact=True)
                        find.fill("VENDOR")
                        expect(rows).to_have_count(1)
                        expect(rows.first).to_contain_text("Vendor review")
                        expect(window.get_by_role("button", name="Open Room", exact=True)).to_be_disabled()
                        shoot("filtered")
                        find.fill("[no-match]")
                        expect(rows).to_have_count(0)
                        expect(window.get_by_test_id("projects-pane")).to_have_text("No projects match")
                        shoot("no-match")
                        find.fill("")
                        expect(rows).to_have_count(2)
                        rows.first.click()
                        page.evaluate("localStorage.setItem('hs:walk-voice', 'off')")
                        _start_app_walk(page)
                        _finish_app_walk(page)
                        window.get_by_role("button", name="New project", exact=True).click()
                        expect(page.locator("#surface-project-setup")).to_be_visible()
                    elif state == "read-failed":
                        row = window.get_by_test_id("projects-row").first
                        row.click()
                        expect(window.get_by_test_id("projects-next")).to_have_text("Not read")
                        expect(window.get_by_role("button", name="Retry", exact=True)).to_be_enabled()
                        shoot("read-failed-selected")
                        # The selected-object recovery stays in the same window.
                        for endpoint, payload in gets.items():
                            if endpoint.endswith("/room"):
                                page.unroute(f"**{endpoint}")
                                page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                        row.press("r")
                        expect(window.get_by_test_id("projects-next")).not_to_have_text("Not read")
                        expect(row).to_have_attribute("aria-selected", "true")
                        shoot("recovered")
                    assert errors == [], errors
                    for route, payload in held:
                        route.fulfill(json=payload)
                    page.close()
            browser.close()
    finally:
        server.stop()
