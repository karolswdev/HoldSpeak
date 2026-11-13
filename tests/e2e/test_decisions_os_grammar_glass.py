"""Decisions selection, keyboard, menus and bounded inspector over an isolated hub."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
import urllib.request

import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = "decisions-grammar"


def _seed(base: str) -> list[dict[str, Any]]:
    from holdspeak.db import get_database
    from holdspeak.principals import derive_owner
    from holdspeak.services.decision_record_service import DecisionRecordService

    def request(path: str, body: dict[str, Any], method: str = "POST") -> dict[str, Any]:
        req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req))

    get_database().projects.create_project(project_id="grammar-platform", name="Platform", description="", keywords=[])
    seeds = [request("/api/decision-records/from-desk", {"title": title, "status": status,
        "why": "The team can support this choice.",
        **({"project_id": "grammar-platform", "project_name": "Platform"} if title == "Use the shared runners" else {})}) for title, status in (
        ("Use the shared runners", "accepted"), ("Adopt OpenTelemetry", "proposed"),
        ("Keep the nightly export", "accepted"), ("Move the release to Friday", "accepted"),
        ("Review the storage choice", "accepted"), ("Keep the old worker", "accepted"),
    )]
    request(f"/api/decisions/{seeds[2]['decision']['id']}/status", {"status": "deprecated"}, "PUT")
    request(f"/api/decision-records/{seeds[3]['record']['id']}/commit", {"who": "Karol"})
    records = DecisionRecordService(get_database())
    owner = derive_owner(TOKEN, TOKEN)
    records.dispute(owner, seeds[4]["record"]["id"], reason="The storage plan changed.")
    records.supersede(owner, seeds[5]["record"]["id"], seeds[0]["record"]["id"])
    return seeds


def _verb(page: Any, window: Any, label: str) -> None:
    button = window.get_by_role("button", name=label, exact=True)
    if button.is_visible():
        button.click()
    else:
        window.get_by_role("button", name="Actions ▾", exact=True).click()
        page.get_by_role("menu", name="Decisions actions", exact=True).get_by_role("menuitem", name=label, exact=False).click()


def _app_menu(page: Any) -> Any:
    switcher = page.get_by_test_id("desk-screen-switcher")
    if switcher.is_visible():
        switcher.click()
        page.get_by_role("menuitem", name="Decisions", exact=True).click()
        return page.get_by_role("menu").last
    else:
        page.get_by_test_id("desk-screen-title").get_by_role("button", name="Decisions", exact=True).click()
        return page.get_by_role("menu", name="Decisions menu", exact=True)


@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_decisions_selection_and_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/kit10"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        seeds = _seed(base)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.evaluate("localStorage.setItem('hs:walk-voice','off'); sessionStorage.setItem('hs.desk.staged-surface-open',JSON.stringify({key:'open-decisions'}))")
                page.reload(wait_until="load")
                _normal_chair(page)
                window = page.locator("#surface-decisions")
                rows = window.get_by_test_id("decisions-row")
                rows.first.wait_for()
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-decisions/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                suffix = "900x600" if width == 1440 else "393"

                def shot(state: str) -> None:
                    _settle(page)
                    assert window.evaluate("""el => {
                      const body=el.querySelector('.desk-surface-body');
                      const pane=el.querySelector('.surface-list-pane');
                      return body.scrollHeight<=body.clientHeight+1 && body.scrollWidth<=body.clientWidth+1
                        && (!pane || pane.scrollHeight<=pane.clientHeight+1);
                    }"""), state
                    page.screenshot(path=str(shots / f"decisions-{state}-{suffix}-after.png"))

                expect(window.get_by_test_id("decisions-preview")).to_have_count(0)
                assert window.locator('[role="row"] button, .decisions-plate, .surface-spine').count() == 0
                assert all(abs(row.bounding_box()["height"] - (36 if width == 1440 else 44)) < 1 for row in rows.all())
                shot("list")
                for title, state in (("Adopt OpenTelemetry", "proposed"), ("Use the shared runners", "decided"),
                    ("Move the release to Friday", "committed"), ("Keep the nightly export", "retired"),
                    ("Review the storage choice", "disputed"), ("Keep the old worker", "superseded")):
                    row = rows.filter(has_text=title)
                    row.click()
                    if state == "decided" and width == 1440:
                        expect(row.locator('[data-col="project"]')).to_have_text("Platform")
                    expect(row).to_have_attribute("aria-selected", "true")
                    preview = window.get_by_test_id("decisions-preview")
                    expect(preview).to_contain_text("The team can support this choice.")
                    assert preview.locator("button").count() == 0
                    expect(preview).to_contain_text(title)
                    assert window.locator(".object-list-rows").evaluate("""el => {
                      const row=el.querySelector('[data-object-id]');
                      return row && el.clientHeight >= row.getBoundingClientRect().height*3-1;
                    }"""), "Three complete list rows must remain above the selected facts"
                    assert preview.evaluate("""(el, title) => {
                      const walk=document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                      for (let node=walk.nextNode(); node; node=walk.nextNode()) {
                        const start=node.textContent.indexOf(title);
                        if (start<0) continue;
                        const range=document.createRange();
                        range.setStart(node,start); range.setEnd(node,start+title.length);
                        const lines=[...range.getClientRects()]; const well=el.getBoundingClientRect();
                        return lines.length===1 && lines[0].left>=well.left && lines[0].right<=well.right;
                      }
                      return false;
                    }""", title), f"{title} must use the preview's reading width"
                    if state in ("decided", "committed", "retired"):
                        expect(row.locator('[data-col="state"]')).to_have_text(state.capitalize())
                    shot(state)
                record_path = f"**/api/decision-records/{seeds[0]['record']['id']}"
                page.route(record_path, lambda route: route.fulfill(status=503, json={"detail": "Record not read"}))
                rows.filter(has_text="Use the shared runners").click()
                preview = window.get_by_test_id("decisions-preview")
                expect(preview.get_by_role("alert")).to_contain_text("Record not read")
                expect(preview).to_contain_text("Use the shared runners")
                shot("preview-error")
                page.unroute(record_path)
                preview.get_by_role("button", name="Try again", exact=True).click()
                expect(preview.get_by_role("alert")).to_have_count(0)
                shot("preview-retry")
                row = rows.filter(has_text="Adopt OpenTelemetry")
                row.click(button="right")
                menu = page.get_by_role("menu", name="Decisions actions", exact=True)
                expect(menu.get_by_role("menuitem", name="Decide", exact=False)).to_be_enabled()
                expect(menu.get_by_role("menuitem", name="Retire", exact=False)).to_be_disabled()
                shot("context-menu")
                page.keyboard.press("Escape")
                app_menu = _app_menu(page)
                expect(app_menu.get_by_role("menuitem", name="Decide", exact=False)).to_be_enabled()
                shot("app-menu")
                page.keyboard.press("Escape")
                from .test_desk_sweep import _start_app_walk, _finish_app_walk
                _start_app_walk(page)
                expect(page.get_by_test_id("guide-ring")).to_be_visible()
                shot("walk")
                _finish_app_walk(page)
                row.focus()
                page.keyboard.press("Home")
                expect(rows.first).to_have_attribute("aria-selected", "true")
                page.keyboard.press("ArrowDown")
                expect(rows.nth(1)).to_have_attribute("aria-selected", "true")
                _verb(page, window, "New decision")
                form = window.get_by_test_id("new-decision")
                expect(form).to_be_visible()
                shot("new")
                form.get_by_role("textbox", name="Decision title").fill("Retained draft")
                form.get_by_role("textbox", name="Why", exact=True).fill("One writer")
                shot("draft")
                form.get_by_role("button", name="Record", exact=True).scroll_into_view_if_needed()
                shot("new-actions")
                page.route("**/api/decision-records/from-desk", lambda route: route.fulfill(status=503, json={"detail": "Decisions not saved"}))
                form.get_by_role("button", name="Record", exact=True).click()
                expect(form.get_by_role("textbox", name="Decision title")).to_have_value("Retained draft")
                expect(form).to_contain_text("Could not make the decision")
                shot("record-error")
                form.get_by_role("button", name="Record", exact=True).scroll_into_view_if_needed()
                shot("record-error-actions")
                page.unroute("**/api/decision-records/from-desk")
                form.get_by_role("button", name="Cancel", exact=True).click()
                expect(page.get_by_text("Could not make the decision", exact=True)).to_have_count(0)
                find = window.get_by_role("searchbox", name="Find a decision", exact=True)
                find.fill("zzzzz")
                expect(rows).to_have_count(0)
                expect(window.get_by_text("No decisions match this search", exact=True)).to_be_visible()
                shot("find-empty")
                with page.expect_response(lambda response: "/api/decisions/ledger" in response.url and "zzzzz" not in response.url):
                    find.fill("")
                expect(rows.first).to_be_visible()
                _settle(page)
                scope_row = window.locator('.object-list-find-row').first
                scope_row.evaluate("el => {el.style.width='210px';el.style.flex='none';}")
                expect(window.get_by_role("checkbox", name="Current only", exact=True)).to_have_count(0)
                window.get_by_role("button", name="Actions ▾", exact=True).click()
                folded_scope = page.get_by_role("menuitemcheckbox", name="Current only", exact=True)
                expect(folded_scope).to_have_attribute("aria-checked", "false")
                folded_scope.click()
                scope_row.evaluate("el => el.removeAttribute('style')")
                expect(window.get_by_role("checkbox", name="Current only", exact=True)).to_be_checked()
                expect(rows.filter(has_text="Keep the old worker")).to_have_count(0)
                shot("current")
                page.route("**/api/decisions/ledger?*", lambda route: route.fulfill(status=503, json={"detail": "Decisions not read"}))
                find.fill("unavailable")
                expect(preview.get_by_role("alert")).to_contain_text("Decisions not read")
                assert preview.get_by_role("alert").evaluate("""el => {
                    const well = el.closest('.surface-list-pane-preview').getBoundingClientRect();
                    const alert = el.getBoundingClientRect();
                    return alert.top >= well.top && alert.bottom <= well.bottom;
                }"""), "The read failure and retry must fit inside the preview"
                shot("read-error")
                page.unroute("**/api/decisions/ledger?*")
                page.route("**/api/decisions/ledger?*", lambda route: route.fulfill(json={"decisions": [], "page": {"total": 0}}))
                find.fill("")
                expect(rows).to_have_count(0)
                shot("no-current")
                window.locator("label").filter(has_text="Current only").click()
                expect(window.get_by_test_id("decisions-preview")).to_have_text("No decisions yet")
                shot("empty")
                page.unroute("**/api/decisions/ledger?*")
                find.fill("shared")
                expect(rows.filter(has_text="Use the shared runners")).to_be_visible()
                row = rows.filter(has_text="Use the shared runners")
                row.focus()
                page.keyboard.press("Enter")
                expect(window.locator(".desk-pullout-title")).to_have_text("Use the shared runners")
                shot("reader")
                _start_app_walk(page)
                expect(page.get_by_test_id("guide-ring")).to_be_visible()
                expect(window.get_by_test_id("decision-reader")).to_have_count(0)
                shot("walk-from-reader")
                assert errors == [], errors
                page.close()
            browser.close()
    finally:
        server.stop()
