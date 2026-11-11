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
    shots = root / ".tmp/evidence-shots/lists10"
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
                # Keep both the app menu and the whole window in the shot.
                for part in (app_menu, window):
                    box = part.bounding_box()
                    assert box and box["x"] >= 0 and box["y"] >= 0
                    assert box["x"] + box["width"] <= width + 1
                    assert box["y"] + box["height"] <= page.viewport_size["height"] + 1
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
                expect(roster.get_by_test_id("people-add-row").get_by_role("alert")).to_contain_text("Person could not be added; the name is kept.")
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
                for state in ("empty", "loading", "suggestions", "read-failed", "locked", "recovery", "no-key-store"):
                    clear_hub_windows_http(base, TOKEN)
                    page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                    if state in ("empty", "suggestions"):
                        for endpoint in ("/api/people/readiness", "/api/people/relationships", "/api/people/suggestions"):
                            payload = wire["before"].get(endpoint, {"relationships": []})
                            if endpoint.endswith("suggestions") and state == "empty":
                                payload = {"suggestions": []}
                            page.route(f"**{endpoint}*", lambda route, _request, payload=payload: route.fulfill(json=payload))
                    elif state == "loading":
                        page.route("**/api/people/readiness", lambda route: None)
                    else:
                        readiness = {"read-failed": "unavailable", "locked": "locked", "recovery": "key_unavailable", "no-key-store": "no_key_store"}[state]
                        page.route("**/api/people/readiness", lambda route, _request, readiness=readiness: route.fulfill(json={"readiness": readiness}))
                    _open(page, base)
                    target = (page.get_by_text("People you meet appear here.", exact=True) if state == "empty"
                              else page.locator('#surface-people .surface-state[data-kind="loading"]') if state == "loading"
                              else page.get_by_test_id({"suggestions": "people-suggestion", "read-failed": "people-read-failed", "locked": "people-read-failed", "recovery": "people-joy-state", "no-key-store": "people-not-here"}[state]))
                    target.first.wait_for()
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
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists10"
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


@pytest.mark.timeout(300)
def test_person_views_forms_and_questions_fit_one_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each records view keeps one list and one inset reading or writing seat."""
    import re
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists10"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        week = open_rig._seed(tmp_path / "home", base)
        person = week["priya"]
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/projects/p-ledger", {})
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/owed", {"body": "Send the API migration estimate", "due": "2026-01-01"})
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/notes", {"topic": "Rollout", "body": "Keep the rollback plan in view.", "visibility": "leader_private"})
        session = open_rig._http(base, "POST", f"/api/people/relationships/{person}/one-on-ones", {})["one_on_one"]
        open_rig._http(base, "POST", f"/api/people/one-on-ones/{session['id']}/agenda", {"body": "Pick the cutover date"})
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/owner-aliases", {"alias": "Priya S."})
        empty_person=open_rig._http(base, "POST", "/api/people/relationships", {"display_name":"Empty record","relationship_kind":"peer"})["relationship"]["id"]
        from holdspeak.db import get_database
        get_database().workbenches.upsert(workbench_id="person-grammar-automation", name="Prepare the rollout", instruction="Prepare the rollout plan.")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                _open(page, base)
                roster = page.get_by_test_id("people-roster")
                person_row=roster.locator(f'[data-object-id="{person}"]')
                person_row.click()
                person_row.press("Enter")
                _settle(page)
                win = page.locator(f'[id="pullout:people:{person}"]')
                win.wait_for()
                if width == 1440:
                    _api(page, "POST", f"/api/desk/windows/pullout:people:{person}/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                suffix = "900x600" if width == 1440 else "393"
                win.get_by_test_id("people-composer").wait_for()

                def shoot(state: str) -> None:
                    _settle(page)
                    _bounded(win)
                    assert win.locator('[role=row][data-object-id] button').count() == 0
                    assert win.locator('h1, .people-folds, .surface-disclosure').count() == 0
                    page.screenshot(path=str(shots / f"person-{state}-{suffix}-after.png"))

                def view(label: str) -> None:
                    win.get_by_role("button", name="Person view", exact=True).click()
                    menu = page.get_by_role("menu", name="Person view", exact=True)
                    menu.get_by_text(label, exact=True).click()

                def verb(label: str) -> None:
                    button = win.get_by_role("button", name=label, exact=True)
                    if button.is_visible():
                        button.click()
                    else:
                        win.get_by_role("button", name="Actions ▾", exact=True).click()
                        page.get_by_role("menu").last.get_by_role("menuitem", name=re.compile("^" + re.escape(label))).click()

                shoot("ledger")
                for kind, label in (("agenda", "Add to the agenda"), ("note", "Note"), ("they", "Priya owes me"), ("you", "I owe Priya")):
                    win.get_by_role("combobox", name="Add to this person").select_option(kind)
                    win.get_by_role("textbox", name=label, exact=True).fill("Keep these words for the next meeting.")
                    shoot("add-" + kind)
                page.route(f"**/api/people/relationships/{person}/requests", lambda route: route.abort())
                win.get_by_role("button", name="Add", exact=True).click()
                expect(win.get_by_test_id("people-owe-receipt")).to_have_attribute("data-phase", "creation_uncertain")
                shoot("owe-create-unknown")
                win.get_by_role("button", name="Start another promise", exact=True).click()
                page.unroute(f"**/api/people/relationships/{person}/requests")
                page.route("**/api/people/requests/*/accept", lambda route: route.fulfill(status=503, json={"detail":"people_store_unavailable"}))
                win.get_by_role("button", name="Add", exact=True).click()
                expect(win.get_by_test_id("people-owe-receipt")).to_have_attribute("data-phase", "acceptance_uncertain")
                shoot("owe-accept-failed")
                win.get_by_role("button", name="Check saved request", exact=True).click()
                expect(win.get_by_test_id("people-owe-receipt")).to_have_attribute("data-phase", "acceptance_uncertain")
                shoot("owe-checked")
                page.unroute("**/api/people/requests/*/accept")
                win.get_by_role("button", name="Accept saved request", exact=True).click()
                expect(win.get_by_test_id("people-owe-receipt")).to_have_attribute("data-phase", "saved")
                shoot("owe-saved")
                win.get_by_role("combobox", name="Add to this person").select_option("note")
                page.route(f"**/api/people/relationships/{person}/notes", lambda route: route.fulfill(status=503, json={"detail": "people_store_unavailable"}))
                win.get_by_role("button", name="Add", exact=True).click()
                win.get_by_role("alert").wait_for()
                shoot("note-failed")
                page.unroute(f"**/api/people/relationships/{person}/notes")
                win.get_by_role("button", name="Add", exact=True).click()
                expect(win.get_by_role("textbox", name="Note", exact=True)).to_have_value("")
                win.get_by_role("grid", name="Commitments", exact=True).get_by_role("row", name=re.compile(open_rig.COMMITMENT)).click()
                shoot("commitment-selected")
                verb("Open")
                inspector = win.get_by_test_id("people-commitment-inspector")
                inspector.get_by_role("combobox", name="Automation", exact=True).wait_for()
                shoot("commitment-send")
                inspector.get_by_role("combobox", name="Commitment action", exact=True).select_option("satisfy")
                inspector.get_by_role("textbox", name="Satisfaction note", exact=True).fill("The rollout plan was reviewed.")
                shoot("commitment-satisfy")
                inspector.get_by_role("button", name="Cancel", exact=True).click()
                view("Agenda")
                shoot("agenda")
                verb("Add…"); shoot("agenda-add")
                win.get_by_role("button", name="Cancel", exact=True).click()
                expect(win.get_by_role("textbox",name="Add to the agenda",exact=True)).not_to_be_visible()
                win.get_by_role("grid", name="Agenda", exact=True).get_by_role("row", name=re.compile("Pick the cutover date")).click()
                shoot("agenda-selected")
                verb("Remove")
                question = win.get_by_role("region", name="Remove Pick the cutover date?", exact=True)
                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                shoot("agenda-remove")
                question.get_by_role("button", name="Cancel", exact=True).click()
                view("1:1 brief")
                shoot("brief")
                note = win.get_by_role("grid", name="1:1 brief", exact=True).get_by_role("row", name=re.compile("Rollout"))
                note.click()
                shoot("brief-selected")
                view("Links")
                shoot("links")
                for label, state in (("Link project", "project-form"), ("Link calendar event", "calendar-form"), ("Add name", "alias-form")):
                    verb(label)
                    win.get_by_test_id({"project-form": "people-project-link", "calendar-form": "people-event-picker", "alias-form": "people-alias-add"}[state]).wait_for()
                    if state == "project-form":
                        win.get_by_role("combobox", name="Project", exact=True).select_option("p-obs")
                    if state == "alias-form":
                        win.get_by_role("textbox", name="Name in meeting notes", exact=True).fill("Priya in the rollout notes")
                    shoot(state)
                    win.get_by_role("button", name="Cancel", exact=True).click()
                for title, label, state in (("Payments ledger cutover", "Unlink", "project-unlink"), (open_rig.ONE_ON_ONE, "Unlink", "calendar-unlink"), ("Priya S.", "Remove", "alias-remove")):
                    win.get_by_role("grid", name="Person links", exact=True).get_by_role("row").filter(has_text=title).click()
                    verb(label)
                    question = win.get_by_role("region", name=f"{label} {title}?", exact=True)
                    expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                    shoot(state)
                    question.get_by_role("button", name="Cancel", exact=True).click()
                verb("Archive person")
                question = win.get_by_role("region", name="Archive Priya Nair?", exact=True)
                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                shoot("archive")
                question.get_by_role("button", name="Cancel", exact=True).click()
                _api(page, "POST", f"/api/desk/windows/pullout:people:{person}/close", {}, token=TOKEN)
                expect(win).not_to_be_visible()
                empty_row=roster.locator(f'[data-object-id="{empty_person}"]')
                empty_row.click(); empty_row.press("Enter")
                win=page.locator(f'[id="pullout:people:{empty_person}"]')
                win.get_by_test_id("people-composer").wait_for()
                if width == 1440:
                    _api(page, "POST", f"/api/desk/windows/pullout:people:{empty_person}/set_geometry", {"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}}, token=TOKEN)
                shoot("empty-ledger")
                for label,state in (("1:1 brief","empty-brief"),("Agenda","empty-agenda"),("Links","empty-links")):
                    view(label); shoot(state)
                held=[]
                view("Ledger")
                page.route("**/api/door", lambda route: held.append(route))
                view("Links"); verb("Link calendar event")
                win.get_by_test_id("people-event-picker").locator('.surface-state[data-kind="loading"]').wait_for()
                shoot("calendar-loading")
                for route in held: route.fulfill(status=503,json={"detail":"unavailable"})
                win.get_by_test_id("people-event-picker").get_by_role("alert").wait_for()
                shoot("calendar-failed")
                page.unroute("**/api/door")
                page.route("**/api/door", lambda route: route.fulfill(json={"upcoming":[]}))
                win.get_by_role("button",name="Try again",exact=True).click()
                win.get_by_text("No upcoming events",exact=True).wait_for()
                shoot("calendar-empty")
                page.unroute("**/api/door")
                _api(page, "POST", f"/api/desk/windows/pullout:people:{empty_person}/close", {}, token=TOKEN)
                expect(win).not_to_be_visible()
                held=[]
                page.route(f"**/api/people/relationships/{empty_person}/brief", lambda route: held.append(route))
                empty_row.click(); empty_row.press("Enter")
                win.locator('.surface-state[data-kind="loading"]').wait_for()
                shoot("loading")
                for route in held: route.fulfill(status=503,json={"detail":"people_store_unavailable"})
                win.get_by_role("alert").wait_for()
                shoot("read-failed")
                page.unroute(f"**/api/people/relationships/{empty_person}/brief")
                win.get_by_role("button",name="Try again",exact=True).click()
                win.get_by_test_id("people-composer").wait_for()
                assert errors == [], errors
                page.close()
            browser.close()
    finally:
        server.stop()
