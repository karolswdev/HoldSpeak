"""Selection grammar and every preference pane at the owner's window sizes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _settle, clear_hub_windows_http
from .test_settings_page_glass import TOKEN, _open_page


@pytest.mark.timeout(240)
def test_settings_selection_grammar_and_pane_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    root = Path(__file__).resolve().parents[2]
    fixtures = root / "web/src/desk/__tests__/fixtures"
    shots = root / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    chain = json.loads((root / "web/src/features/runson/__tests__/fixtures/settings-chain.recorded.json").read_text())
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                accounts = json.loads((fixtures / "connections-wire/connections-checked.json").read_text())
                for endpoint, recording in (
                    ("/api/connections", "connections-wire/connections-checked.json"),
                    ("/api/channels/destinations", "destinations-wire/list-two.json"),
                    ("/api/settings/hub", "settings-wire/hub.json"),
                ):
                    payload = json.loads((fixtures / recording).read_text())
                    payload = payload.get("wire", payload)
                    page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                for tool in accounts["tools"]:
                    page.route(f"**/api/connections/{tool['provider_id']}/recheck", lambda route, _request, tool=tool: route.fulfill(json=tool))
                for endpoint, payload in chain["gets"].items():
                    page.route(f"**{endpoint}", lambda route, _request, payload=payload: route.fulfill(json=payload))
                def editor(route: Any) -> None:
                    scope = route.request.post_data_json.get("scope", {})
                    key = "default" if scope.get("kind") == "global" else "summaries" if scope.get("capability_id") == "meeting.deferred_analysis" else None
                    if key:
                        route.fulfill(json=chain["steps"][0]["editors"][key])
                    else:
                        route.continue_()
                page.route("**/api/inference/assignments/editor", editor)
                settings = json.loads((fixtures / "settings-wire/settings.json").read_text())
                calendar = json.loads((fixtures / "settings-wire/calendar-sources-one.json").read_text())
                # Vary only identity fields of real recorded calendar sources.
                sources = [{**calendar["sources"][0], "id": f"feed-{i}", "label": name} for i, name in enumerate(("Home", "Woodward", "Work"))]
                calendar["sources"] = sources
                settings["calendar"]["sources"] = [{"id": source["id"], "label": source["label"], "url": f"eventkit:{source['id']}", "enabled": True} for source in sources]
                page.route("**/api/settings", lambda route: route.fulfill(json=settings) if route.request.method == "GET" else route.continue_())
                page.route("**/api/calendar/sources", lambda route: route.fulfill(json=calendar))
                _open_page(page, base)
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-settings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                _settle(page)
                window = page.locator("#surface-settings")
                rail = window.get_by_role("navigation", name="Settings sections")
                panes = rail.locator("[data-rail-id]").evaluate_all("els => els.map(el => el.dataset.railId)")
                for pane in panes:
                    if not rail.is_visible():
                        page.get_by_test_id("settings-back").click()
                    window.get_by_test_id(f"settings-index-{pane}").click()
                    section = window.locator(f"[data-settings-section='{pane}']")
                    section.wait_for(state="visible")
                    _settle(page)
                    if pane == "accounts":
                        for tab in ("Services", "Calendars", "Send to"):
                            section.get_by_role("tab", name=tab, exact=True).click()
                            _settle(page)
                            _bounded(window)
                            if width == 1440:
                                assert all(abs(row.bounding_box()["height"] - 26) < 1 for row in section.locator("[role=row][data-object-id]:visible").all())
                            else:
                                assert all(row.bounding_box()["height"] >= 44 for row in section.locator("[role=row][data-object-id]:visible").all())
                            assert section.locator('[role="row"] button').count() == 0
                            suffix = {"Services": "services", "Calendars": "calendars", "Send to": "send-to"}[tab]
                            page.screenshot(path=str(shots / f"accounts-{suffix}-{'900x600' if width == 1440 else '393'}-after.png"))
                        section.get_by_role("tab", name="Services", exact=True).click()
                        row = section.get_by_text("GitHub", exact=True)
                        row.click()
                        expect(section.get_by_role("button", name="Sign in…", exact=True)).to_be_enabled()
                        row.click(button="right")
                        menu = page.get_by_role("menu", name="Services actions", exact=True)
                        expect(menu.get_by_role("menuitem", name="Sign in…", exact=False)).to_be_visible()
                        page.keyboard.press("Escape")
                        # The app menu receives the same selection verbs.
                        switcher = page.get_by_test_id("desk-screen-switcher")
                        if switcher.is_visible():
                            switcher.click()
                            page.get_by_role("menuitem", name="Settings", exact=True).click()
                            app_menu = page.get_by_role("menu").last
                        else:
                            page.get_by_test_id("desk-screen-title").get_by_role("button", name="Settings", exact=True).click()
                            app_menu = page.get_by_role("menu", name="Settings menu", exact=True)
                        expect(app_menu.get_by_role("menuitem", name="Sign in…", exact=False)).to_be_visible()
                        expect(app_menu.get_by_role("menuitem", name="Show me", exact=True)).to_be_visible()
                        page.keyboard.press("Escape")
                    else:
                        page.screenshot(path=str(shots / f"{pane}-{'900x600' if width == 1440 else '393'}-after.png"))
                        if pane == "engines":
                            _bounded(window)
                            if width == 1440:
                                assert all(abs(row.bounding_box()["height"] - 26) < 1 for row in section.locator("[role=row][data-object-id]:visible").all())
                            else:
                                assert all(row.bounding_box()["height"] >= 44 for row in section.locator("[role=row][data-object-id]:visible").all())
                            assert section.locator('[role="row"] button').count() == 0
                            expect(section.get_by_role("combobox", name="Everything else engines", exact=True).locator("option:checked")).to_have_text("Codex, then Gemini CLI")
                            section.get_by_role("button", name="Model library", exact=True).click()
                            library = section.get_by_test_id("settings-engines-library")
                            for tab in ("Engines", "Speech", "Search"):
                                library.get_by_role("tab", name=tab, exact=True).click()
                                _settle(page)
                                page.screenshot(path=str(shots / f"engines-library-{tab.lower()}-{'900x600' if width == 1440 else '393'}-after.png"))
                            section.get_by_role("region", name="Model library", exact=True).get_by_role("button", name="Close", exact=True).first.click()
                    assert rail.locator(".surface-spine").count() == 0
                    assert all(not node.inner_text() for node in rail.locator(".surface-rail-state").all())
                assert errors == [], errors
                page.close()
            browser.close()
    finally:
        server.stop()


def _bounded(window: Any) -> None:
    assert window.evaluate("""el => {
      const pane = el.querySelector('.pref-pane');
      const body = el.querySelector('.desk-surface-body');
      return pane.scrollHeight <= pane.clientHeight + 1 && body.scrollHeight <= body.clientHeight + 1
        && body.scrollWidth <= body.clientWidth + 1;
    }"""), window.bounding_box()

