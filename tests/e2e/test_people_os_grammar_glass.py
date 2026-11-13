"""People selection, keyboard/menu parity and bounded wells at the owner's sizes."""
from __future__ import annotations

import os
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
    shots = root / ".tmp/evidence-shots/lists14"
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
                suffix = "900" if width == 1440 else "393"

                def shoot(state: str) -> None:
                    _settle(page)
                    _bounded(window)
                    page.screenshot(path=str(shots / f"people-{state}-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))

                shoot("list")
                rows = roster.locator('[role=row][data-object-id]')
                assert rows.count() > 0
                assert all(abs(row.bounding_box()["height"] - 36) < 1 if width == 1440 else row.bounding_box()["height"] >= 44 for row in rows.all())
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
                    expect(page.locator("#surface-people > .desk-surface-foot .kit-statusbar")).to_be_visible()
                    page.screenshot(path=str(shots / f"people-{state}-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
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
    facts = window.evaluate("""el => [...el.querySelectorAll('.desk-surface-body,.surface-list-pane,.surface-list-pane-list,.surface-list-pane-preview,.surface-pane-inspector,.surface-inspector-form,.surface-inspector-fields')].map(e=>({kind:e.className,height:e.clientHeight,scroll:e.scrollHeight,width:e.clientWidth,scrollWidth:e.scrollWidth,rect:e.getBoundingClientRect().toJSON(),style:e.getAttribute('style')}))""")
    bounded = window.evaluate("""el => {
      const body = el.querySelector('.desk-surface-body');
      const list = el.querySelector('.surface-list-pane');
      return body.scrollHeight <= body.clientHeight + 1 && body.scrollWidth <= body.clientWidth + 1
        && (!list || list.scrollHeight <= list.clientHeight + 1);
    }""")
    if not bounded:
        import json
        out = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/kit11"
        out.mkdir(parents=True, exist_ok=True)
        (out / "unbounded-person.json").write_text(json.dumps(facts, indent=2))
        window.page.screenshot(path=str(out / "unbounded-person.png"))
    assert bounded, facts
    gaps = window.evaluate("""el => [...el.querySelectorAll('.surface-list-pane-preview .surface-inspector-form[data-completion]')].flatMap(form => {
      const fields=form.querySelector(':scope > .surface-inspector-fields'), actions=form.querySelector(':scope > .surface-inspector-actions');
      const row=fields?.querySelector(':scope > .surface-inspector-rows')?.lastElementChild;
      if(!fields||!actions||!row||!form.checkVisibility()||fields.scrollHeight>fields.clientHeight+1)return [];
      const end=row.getBoundingClientRect(), next=(form.querySelector(':scope > .surface-inspector-notice')||actions).getBoundingClientRect();
      return end.height && next.top-end.bottom>20 ? [next.top-end.bottom] : [];
    })""")
    assert not gaps, gaps
    clipped = window.evaluate("""el => [...el.querySelectorAll('.surface-list-pane-preview .surface-inspector-form[data-completion]')].flatMap(form => {
      const fields=form.querySelector(':scope > .surface-inspector-fields'), rows=fields?.querySelector(':scope > .surface-inspector-rows'), first=rows?.firstElementChild;
      if(!fields||!first||fields.scrollTop||!form.checkVisibility())return [];
      const r=first.getBoundingClientRect(), f=fields.getBoundingClientRect();
      return r.top<f.top-1||r.bottom>f.bottom+1 ? [first.textContent] : [];
    })""")
    assert not clipped, clipped
    bands = window.evaluate("""el => [...el.querySelectorAll('.surface-inspector-control > .object-list--selection')].flatMap(list => {
      if(!list.checkVisibility())return [];
      const children=[...list.children].filter(child=>getComputedStyle(child).position!=="absolute");
      const content=children.reduce((sum,child)=>sum+child.getBoundingClientRect().height,0);
      return list.getBoundingClientRect().height-content>2 ? [list.getAttribute("aria-label")] : [];
    })""")
    assert not bands, bands
    lost = window.evaluate("""el=>[...el.querySelectorAll('.surface-list-pane-list .object-list-rows')].flatMap(well=>{
      if(well.scrollTop>1||!well.checkVisibility())return [];
      const b=well.getBoundingClientRect(),rows=[...well.querySelectorAll('.object-list-row')],visible=rows.filter(row=>{const r=row.getBoundingClientRect();return r.top<b.bottom-1&&r.bottom>b.top+1});
      const more=rows.some(row=>row.getBoundingClientRect().bottom>b.bottom+1);
      const cue=visible.at(-1)?.getBoundingClientRect();
      return more && (!cue || cue.bottom<=b.bottom+1 || well.scrollHeight<=well.clientHeight) ? [{text:well.textContent,box:b.toJSON(),scroll:well.scrollTop,height:well.clientHeight,full:well.scrollHeight,rows:rows.map(row=>({text:row.textContent,box:row.getBoundingClientRect().toJSON()})),minimum:well.closest(".surface-list-pane")?.style.cssText}] : [];
    })""")
    assert not lost, lost


@pytest.mark.timeout(240)
def test_people_shared_list_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-shoot the two roster poses after adopting Meetings' shared ListPane."""
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists14"
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
                suffix = "900" if width == 1440 else "393"
                _settle(page)
                _bounded(page.locator("#surface-people"))
                page.screenshot(path=str(shots / f"people-list-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
                row.click()
                expect(roster.get_by_test_id("people-summary")).to_contain_text(open_rig.COMMITMENT)
                _settle(page)
                _bounded(page.locator("#surface-people"))
                page.screenshot(path=str(shots / f"people-selected-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
                page.close()
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440,393])
def test_person_views_forms_and_questions_fit_one_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Each records view keeps one list and one inset reading or writing seat."""
    import re
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists14"
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
        empty_person=open_rig._http(base, "POST", "/api/people/relationships", {"display_name":"Empty record with a long person name for the next meeting","relationship_kind":"peer"})["relationship"]["id"]
        from holdspeak.db import get_database
        get_database().workbenches.upsert(workbench_id="person-grammar-automation", name="Prepare the rollout", instruction="Prepare the rollout plan.")
        from datetime import datetime, timedelta, timezone
        from holdspeak.meeting_session import IntelSnapshot, MeetingState
        from holdspeak.intel.models import ActionItem
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.meeting_service import MeetingService
        from holdspeak.services.workbench_service import WorkbenchService
        owner=Principal(PrincipalKind.OWNER,"people-grammar")
        now=datetime.now(timezone.utc)
        event=open_rig._http(base,"GET",f"/api/people/relationships/{person}/brief")["brief"]["next_one_on_one"]
        db=get_database()
        db.meetings.save_meeting(MeetingState(id="people-nudge-source",title="1:1 Priya / Karol",calendar_event_id=event["id"],started_at=now-timedelta(days=2),ended_at=now-timedelta(days=2)+timedelta(minutes=30),intel=IntelSnapshot(timestamp=30,summary="Priya owns the rollout follow-up.",action_items=[ActionItem(id="people-nudge-action",task="Send the overdue report",owner="Priya S.",due="2026-01-01")]),intel_status="completed"))
        for item in db.meetings.list_action_items(meeting_id="people-nudge-source"):
            MeetingService(db).review_action_item(owner,item.id,{"review_state":"accepted"})
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            clear_hub_windows_http(base, TOKEN)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _open(page, base)
            roster = page.get_by_test_id("people-roster")
            person_row=roster.locator(f'[data-object-id="{person}"]')
            person_row.click()
            expect(roster.get_by_test_id("people-summary")).to_contain_text("Keep the rollback plan in view.")
            counts=person_row.locator('[data-col="open"]')
            expect(counts).to_have_text(re.compile(r"You \d+ · Them \d+"))
            _settle(page)
            assert counts.evaluate("""cell=>{const b=cell.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(cell);return [...range.getClientRects()].every(r=>!r.width||r.left>=b.left-1&&r.right<=b.right+1)}""")
            page.screenshot(path=str(shots / f"people-both-sides-selected-{'900' if width==1440 else '393'}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
            person_row.press("Enter")
            _settle(page)
            win = page.locator(f'[id="pullout:people:{person}"]')
            win.wait_for()
            if width == 1440:
                _api(page, "POST", f"/api/desk/windows/pullout:people:{person}/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            suffix = "900" if width == 1440 else "393"
            win.get_by_test_id("people-composer").wait_for()

            def shoot(state: str) -> None:
                _settle(page)
                _bounded(win)
                picker=win.get_by_role("button",name="Person view",exact=True)
                if picker.is_visible():
                    facts_left=win.get_by_test_id("people-detail-head").locator('.gadget-row').first.bounding_box()["x"]
                    assert abs(picker.bounding_box()["x"]-facts_left) <= 1
                assert win.locator('[role=row][data-object-id] button').count() == 0
                page.screenshot(path=str(shots / f"person-{state}-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
                if state == "brief-last":
                    from .test_kit_polish_wave14_r2_glass import capture_state
                    capture_state(page, win, "people", state, width)
                assert win.locator('h1:not(.reading-heading), .people-folds, .people-section').count() == 0, win.locator('h1:not(.reading-heading), .people-folds, .people-section').evaluate_all("els=>els.map(el=>el.outerHTML.slice(0,1500))")
                page.screenshot(path=str(shots / f"person-{state}-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))

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
            expect(win.get_by_test_id("people-owe-receipt")).to_have_text("Save result unknown · Check the list")
            assert win.locator(".surface-action-notice-body").evaluate("el=>el.getBoundingClientRect().height <= parseFloat(getComputedStyle(el).lineHeight)+1")
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
            accept=win.get_by_test_id("people-owe-accept-saved")
            if accept.is_visible():accept.click()
            else:
                win.get_by_test_id("people-composer").get_by_role("button",name="Actions",exact=True).click()
                page.get_by_role("menuitem",name="Accept saved request",exact=True).click()
            expect(win.get_by_test_id("people-owe-receipt")).to_have_attribute("data-phase", "saved")
            shoot("owe-saved")
            win.get_by_role("combobox", name="Add to this person").select_option("note")
            page.route(f"**/api/people/relationships/{person}/notes", lambda route: route.fulfill(status=503, json={"detail": "people_store_unavailable"}))
            win.get_by_role("button", name="Add", exact=True).click()
            win.get_by_role("alert").wait_for()
            shoot("note-failed")
            form = win.get_by_test_id("people-composer")
            assert "Try again" not in form.get_by_role("alert").inner_text()
            assert form.locator(".surface-action-notice-body").evaluate("el=>el.getBoundingClientRect().height <= parseFloat(getComputedStyle(el).lineHeight)+1")
            (shots / f"note-bounds-{suffix}.json").write_text(json.dumps(form.evaluate("""form=>[...form.closest('.surface-list-pane').querySelectorAll('.surface-list-pane-list,.surface-list-pane-preview,.surface-pane-inspector,.surface-inspector-form,.surface-inspector-fields,.surface-inspector-rows,.gadget-row,.surface-inspector-notice,.surface-inspector-actions')].map(el=>({kind:el.className,text:el.classList.contains('gadget-row')?el.textContent:null,height:el.clientHeight,scroll:el.scrollHeight,rect:el.getBoundingClientRect().toJSON()}))"""),indent=2))
            assert form.locator('.surface-inspector-rows > .gadget-row').evaluate_all("""rows=>rows.every(row=>{const r=row.getBoundingClientRect(),well=row.closest('.surface-inspector-fields').getBoundingClientRect();return r.top>=well.top-1&&r.bottom<=well.bottom+1})""")
            page.unroute(f"**/api/people/relationships/{person}/notes")
            win.get_by_role("button", name="Try again", exact=True).click()
            expect(win.get_by_role("textbox", name="Note", exact=True)).to_have_value("")
            win.get_by_role("grid",name="Commitments",exact=True).get_by_role("row",name=re.compile("Send the overdue report")).click()
            verb("Nudge")
            win.locator('[data-seat="note"]').wait_for()
            expect(win.get_by_test_id("send-status")).to_contain_text("New")
            expect(win.get_by_test_id("person-status")).to_have_count(0)
            shoot("nudge")
            win.get_by_role("button",name="Cancel",exact=True).click()
            expect(win.get_by_role("grid",name="Commitments",exact=True)).to_be_visible()
            expect(win.get_by_test_id("person-status")).to_be_visible()
            win.get_by_role("grid", name="Commitments", exact=True).get_by_role("row", name=re.compile(open_rig.COMMITMENT)).click()
            shoot("commitment-selected")
            verb("Open")
            inspector = win.get_by_test_id("people-commitment-inspector")
            inspector.get_by_role("combobox", name="Automation", exact=True).wait_for()
            shoot("commitment-send")
            inspector.get_by_role("button", name="Send to automation", exact=True).click()
            expect(inspector.get_by_role("button",name="Open automation",exact=True)).to_be_visible()
            expect(inspector.get_by_role("button",name="Send to automation",exact=True)).not_to_be_visible()
            shoot("commitment-linked")
            inspector.get_by_role("button",name="Open automation",exact=True).click()
            automation=page.locator('[id="workbench:person-grammar-automation"]')
            automation.get_by_test_id("automation-summary").wait_for()
            automation.locator(".desk-gadget-close").click()
            expect(win).to_be_visible()
            relationship=open_rig._http(base,"GET",f"/api/people/relationships/{person}")
            commitment=next(row for row in relationship["relationship"]["commitments"] if row["body"]==open_rig.COMMITMENT)
            execution=open_rig._http(base,"GET",f"/api/people/commitments/{commitment['id']}/execution")
            item=execution["items"][0]
            WorkbenchService(db).update_item(owner,item["workbench_id"],item["id"],status="done",result="The rollout brief is ready.",completed_at=now.isoformat())
            inspector.get_by_role("button",name="Cancel",exact=True).click()
            verb("Open")
            expect(win.get_by_test_id("people-commitment-facts").get_by_text("The rollout brief is ready.",exact=True)).to_be_visible()
            shoot("commitment-result")
            wire={"relationship":relationship,"readiness":open_rig._http(base,"GET","/api/people/readiness"),"sessions":open_rig._http(base,"GET",f"/api/people/relationships/{person}/one-on-ones"),"brief":open_rig._http(base,"GET",f"/api/people/relationships/{person}/brief"),"execution":open_rig._http(base,"GET",f"/api/people/commitments/{commitment['id']}/execution"),"workbenches":open_rig._http(base,"GET","/api/workbenches"),"commitment_id":commitment["id"]}
            tape=Path(__file__).resolve().parents[2]/f".tmp/lists10/r2/people-execution-{width}.json"
            tape.parent.mkdir(parents=True,exist_ok=True);tape.write_text(json.dumps(wire,indent=2)+"\n")
            inspector.get_by_role("combobox", name="Commitment action", exact=True).select_option("satisfy")
            inspector.get_by_role("textbox", name="Satisfaction note", exact=True).fill("The rollout plan was reviewed.")
            shoot("commitment-satisfy")
            inspector.get_by_role("button",name="Mark satisfied",exact=True).click()
            expect(win.get_by_role("grid",name="Commitments",exact=True).get_by_role("rowgroup",name="Done",exact=True)).to_contain_text(open_rig.COMMITMENT)
            shoot("commitment-done")
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
            win.get_by_test_id("prep-last").click()
            shoot("brief-last")
            note = win.get_by_role("grid", name="1:1 brief", exact=True).get_by_role("row", name=re.compile("Rollout"))
            note.click()
            shoot("brief-selected")
            view("Links")
            shoot("links")
            assert win.get_by_role("grid",name="Person links",exact=True).locator('.object-list-rows').evaluate("""well=>{const b=well.getBoundingClientRect();return [...well.querySelectorAll('.object-list-row')].every(row=>{const r=row.getBoundingClientRect();return r.top>=b.top-1&&r.bottom<=b.bottom+1})}""")
            expect(win.get_by_role("region",name="Links",exact=True)).to_contain_text("Payments ledger cutover")
            win.get_by_role("grid",name="Person links",exact=True).get_by_role("row").filter(has_text="Payments ledger cutover").click()
            shoot("links-selected")
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
            title=win.locator('.desk-window-title')
            full=title.get_attribute('title')
            shown=title.inner_text()
            assert title.evaluate('el=>el.scrollWidth<=el.clientWidth+1')
            assert shown==full or shown.endswith('…') and full.startswith(shown[:-1].rstrip()+' '), (shown,full)
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


@pytest.mark.timeout(180)
@pytest.mark.parametrize("width", [1440, 393])
def test_person_editor_rows_are_whole(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """The Add list and stored Result end on complete rows, above their verbs."""
    from datetime import datetime, timedelta, timezone
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.intel.models import ActionItem
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.workbench_service import WorkbenchService
    from holdspeak.services.meeting_service import MeetingService

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists14"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        week = open_rig._seed(tmp_path / "home", base)
        person = week["priya"]
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/projects/p-ledger", {})
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/owed", {"body": "Send the API migration estimate"})
        db = get_database()
        now = datetime.now(timezone.utc)
        event = open_rig._http(base, "GET", f"/api/people/relationships/{person}/brief")["brief"]["next_one_on_one"]
        db.meetings.save_meeting(MeetingState(id="person-row-history", title="1:1 Priya / Karol", calendar_event_id=event["id"], started_at=now-timedelta(days=2), ended_at=now-timedelta(days=2)+timedelta(minutes=30), intel=IntelSnapshot(timestamp=30, summary="The rollout plan is ready.", action_items=[ActionItem(id="row-history-action",task="Review the rollback plan",owner="Priya Nair")]), intel_status="completed"))
        for item in db.meetings.list_action_items(meeting_id="person-row-history"):
            MeetingService(db).review_action_item(Principal(PrincipalKind.OWNER,"person-row-fit"),item.id,{"review_state":"accepted"})
        db.workbenches.upsert(workbench_id="person-row-fit", name="Prepare the rollout", instruction="Prepare the rollout plan.")
        detail = open_rig._http(base, "GET", f"/api/people/relationships/{person}")["relationship"]
        commitment = next(row for row in detail["commitments"] if row["body"] == open_rig.COMMITMENT)
        open_rig._http(base, "POST", f"/api/people/commitments/{commitment['id']}/workbench", {"workbench_id": "person-row-fit"})
        item = open_rig._http(base, "GET", f"/api/people/commitments/{commitment['id']}/execution")["items"][0]
        WorkbenchService(db).update_item(Principal(PrincipalKind.OWNER, "person-row-fit"), item["workbench_id"], item["id"], status="done", result="The rollout brief is ready.")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            clear_hub_windows_http(base, TOKEN)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            _open(page, base)
            roster = page.get_by_test_id("people-roster")
            person_row = roster.locator(f'[data-object-id="{person}"]')
            person_row.click()
            person_row.press("Enter")
            win = page.locator(f'[id="pullout:people:{person}"]')
            if width == 1440:
                _api(page, "POST", f"/api/desk/windows/pullout:people:{person}/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            win.get_by_test_id("people-composer").wait_for()
            suffix = "900" if width == 1440 else "393"
            observations = {}

            def measure(well, selector):
                return well.evaluate("""(well, selector) => {
                  const box = well.getBoundingClientRect();
                  return [...well.querySelectorAll(selector)].map(row => {
                    const r = row.getBoundingClientRect();
                    return {text:row.textContent,top:r.top,bottom:r.bottom,wellTop:box.top,wellBottom:box.bottom,scrollTop:well.scrollTop,scrollHeight:well.scrollHeight,height:well.clientHeight,
                      cut: r.bottom > box.top+1 && r.top < box.bottom-1 && (r.top < box.top-1 || r.bottom > box.bottom+1)};
                  });
                }""", selector)

            _settle(page)
            observations["add-sparse"] = measure(win.get_by_role("grid", name="Commitments").locator(".object-list-rows"), ".object-list-row")
            page.screenshot(path=str(shots / f"person-add-sparse-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
            for body in ("Send the rollout dates", "Review the next report"):
                open_rig._http(base, "POST", f"/api/people/relationships/{person}/owed", {"body": body})
            expect(win.get_by_role("grid", name="Commitments").get_by_role("row", name="Review the next report", exact=False)).to_have_count(1)
            _settle(page)
            observations["add"] = measure(win.get_by_role("grid", name="Commitments").locator(".object-list-rows"), ".object-list-row")
            words = win.get_by_test_id("people-composer").get_by_role("textbox", name="Add to the agenda", exact=True)
            expect(words).to_be_focused()
            well = words.locator('xpath=ancestor::*[contains(@class,"surface-inspector-fields")]')
            control_box, field_box = words.bounding_box(), well.bounding_box()
            assert control_box and field_box
            assert control_box["y"] >= field_box["y"] - 1
            assert control_box["y"] + control_box["height"] <= field_box["y"] + field_box["height"] + 1
            page.screenshot(path=str(shots / f"person-add-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
            row = win.get_by_role("grid", name="Commitments").get_by_role("row", name=open_rig.COMMITMENT, exact=False)
            row.click()
            row.press("Enter")
            form = win.get_by_test_id("people-commitment-inspector")
            facts = win.get_by_test_id("people-commitment-facts")
            expect(facts.get_by_text("The rollout brief is ready.", exact=True)).to_be_visible()
            _settle(page)
            observations["result-list"] = measure(win.get_by_role("grid", name="Commitments").locator(".object-list-rows"), ".object-list-row")
            fields = form.locator(":scope > .surface-inspector-fields")
            observations["result"] = measure(fields, ".gadget-row")
            action = form.get_by_role("combobox", name="Commitment action", exact=True)
            control_box, field_box = action.bounding_box(), fields.bounding_box()
            assert control_box and field_box
            assert control_box["y"] >= field_box["y"] - 1
            assert control_box["y"] + control_box["height"] <= field_box["y"] + field_box["height"] + 1
            page.screenshot(path=str(shots / f"person-result-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
            result = facts.locator('.gadget-row').filter(has_text="The rollout brief is ready.")
            assert result.bounding_box()["y"] + result.bounding_box()["height"] <= form.locator(".surface-inspector-actions").bounding_box()["y"] + 1
            result.scroll_into_view_if_needed()
            _settle(page)
            result_box, well_box = result.bounding_box(), fields.bounding_box()
            assert result_box and well_box
            assert result_box["y"] >= well_box["y"] - 1
            assert result_box["y"] + result_box["height"] <= well_box["y"] + well_box["height"] + 1
            page.screenshot(path=str(shots / f"person-result-read-{suffix}-{os.environ.get('LISTS14_PHASE', 'after')}.png"))
            (shots / f"person-rows-{suffix}.json").write_text(json.dumps(observations, indent=2) + "\n")
            assert not [row for row in observations["result"] if row["cut"]], observations
            for state in ("add-sparse", "add", "result-list"):
                rows = observations[state]
                visible = [row for row in rows if row["top"] < row["wellBottom"] - 1 and row["bottom"] > row["wellTop"] + 1]
                if not rows or rows[0]["scrollHeight"] <= rows[0]["height"] + 1:
                    assert not any(row["cut"] for row in visible), (state, rows)
                else:
                    # A partly visible edge row cues the retained scroll range.
                    assert visible and (visible[0]["cut"] or visible[-1]["cut"]), (state, rows)
            browser.close()
    finally:
        server.stop()
