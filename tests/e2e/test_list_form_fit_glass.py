"""A list yields before its open form; the form opens at its first row."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _settle, clear_hub_windows_http
from .test_desk_sweep import _seed_automation
from .test_people_os_grammar_glass import TOKEN, _open


@pytest.mark.parametrize("width", [1440, 393])
def test_open_list_forms_keep_their_first_row_and_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.intel.models import ActionItem
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.meeting_service import MeetingService

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists11/form-fit"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        person = open_rig._seed(tmp_path / "home", base)["priya"]
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/projects/p-ledger", {})
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/owed", {"body": "Send the API migration estimate"})
        open_rig._http(base, "POST", f"/api/people/relationships/{person}/owner-aliases", {"alias": "Priya S."})
        db = get_database()
        now = datetime.now(timezone.utc)
        event = open_rig._http(base, "GET", f"/api/people/relationships/{person}/brief")["brief"]["next_one_on_one"]
        db.meetings.save_meeting(MeetingState(id="form-fit-history", title="1:1 Priya / Karol", calendar_event_id=event["id"], started_at=now-timedelta(days=2), ended_at=now-timedelta(days=2)+timedelta(minutes=30), intel=IntelSnapshot(timestamp=30, summary="Priya owns the follow-up.", action_items=[ActionItem(id="form-fit-action",task="Send the overdue report",owner="Priya S.",due="2026-01-01")]), intel_status="completed"))
        for item in db.meetings.list_action_items(meeting_id="form-fit-history"):
            MeetingService(db).review_action_item(Principal(PrincipalKind.OWNER, "form-fit"), item.id, {"review_state":"accepted"})
        automation = _seed_automation("form-fit-note")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            clear_hub_windows_http(base, TOKEN)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            suffix = "900x600" if width == 1440 else "393"
            _open(page, base)

            def geometry(window, wid):
                if width == 1440:
                    _api(page, "POST", f"/api/desk/windows/{wid}/set_geometry", {"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}}, token=TOKEN)
                _settle(page)

            def first_row(form):
                _settle(page)
                bounds = form.evaluate("""form => {
                  const fields=form.querySelector(':scope > .surface-inspector-fields');
                  const first=fields.querySelector('.gadget-row');
                  const inspector=form.closest('.surface-pane-inspector');
                  const head=inspector.querySelector(':scope > .surface-pane-inspector-head').getBoundingClientRect();
                  const actions=form.querySelector(':scope > .surface-inspector-actions').getBoundingClientRect();
                  const row=first.getBoundingClientRect(), well=fields.getBoundingClientRect(), pane=inspector.getBoundingClientRect();
                  const list=form.closest('.surface-list-pane').querySelector(':scope > .surface-list-pane-list .object-list');
                  const listWell=list.querySelector('.object-list-rows').getBoundingClientRect();
                  const completeRow=[...list.querySelectorAll('.object-list-row')].some(el=>{const r=el.getBoundingClientRect();return r.top>=listWell.top-1 && r.bottom<=listWell.bottom+1;});
                  const heading=list.querySelector('.object-list-head')?.getBoundingClientRect();
                  return {scroll:fields.scrollTop, rowTop:row.top,rowBottom:row.bottom,wellTop:well.top,wellBottom:well.bottom,headBottom:head.bottom,actTop:actions.top,actBottom:actions.bottom,paneBottom:pane.bottom,completeRow,listHeadingFits:!heading || heading.bottom<=listWell.top+1};
                }""")
                assert bounds["scroll"] <= 1, bounds
                assert bounds["rowTop"] >= max(bounds["wellTop"], bounds["headBottom"]) - 1, bounds
                assert bounds["rowBottom"] <= bounds["wellBottom"] + 1, bounds
                assert bounds["wellBottom"] <= bounds["actTop"] + 1, bounds
                assert bounds["actBottom"] <= bounds["paneBottom"] + 1, bounds
                assert bounds["completeRow"] and bounds["listHeadingFits"], bounds

            def shot(name):
                page.screenshot(path=str(shots / f"{name}-{suffix}.png"))

            roster = page.locator("#surface-people")
            geometry(roster, "surface-people")
            roster.get_by_role("row", name="Priya Nair", exact=False).click()
            roster.get_by_role("button", name="Add person", exact=True).click()
            first_row(roster.get_by_test_id("people-add-row"))
            shot("people-add")
            roster.get_by_test_id("people-add-row").get_by_role("button", name="Cancel", exact=True).click()
            roster.locator(f'[data-object-id="{person}"]').press("Enter")
            window = page.locator(f'[id="pullout:people:{person}"]')
            window.get_by_test_id("people-composer").wait_for()
            geometry(window, f"pullout:people:{person}")
            first_row(window.get_by_test_id("people-composer"))
            shot("person-ledger")
            window.get_by_role("combobox", name="Add to this person", exact=True).select_option("note")
            composer = window.get_by_test_id("people-composer")
            first_row(composer)
            visibility = composer.get_by_role("combobox", name="Visibility", exact=True)
            field = composer.locator(":scope > .surface-inspector-fields")
            v, f = visibility.bounding_box(), field.bounding_box()
            assert v and f and v["y"] >= f["y"] - 1 and v["y"] + v["height"] <= f["y"] + f["height"] + 1, (v, f)
            shot("person-add-note")
            _api(page, "POST", f"/api/desk/windows/pullout:people:{person}/close", {}, token=TOKEN)
            page.get_by_role("button", name="Go", exact=True).first.click()
            page.locator("nav[aria-label='Go menu']").get_by_role("menuitem", name="Automations", exact=True).evaluate("el=>el.click()")
            auto = page.locator("#surface-workbenches")
            auto.locator(f'[data-object-id="{automation}"]').click()
            auto.get_by_role("button", name="Edit", exact=True).click()
            setup = auto.get_by_test_id("automation-setup")
            setup.wait_for()
            geometry(auto, "surface-workbenches")
            first_row(setup)
            shot("automations-edit-do")
            # A larger form still starts at its first row; its own well scrolls.
            auto.get_by_role("combobox", name="Do kind", exact=True).select_option("run_program")
            first_row(setup)
            fields = setup.locator(":scope > .surface-inspector-fields")
            fields.evaluate("el=>{el.scrollTop=el.scrollHeight;}")
            actions = setup.locator(":scope > .surface-inspector-actions")
            expect(actions.get_by_role("button", name="Save", exact=True)).to_be_visible()
            assert fields.evaluate("el=>el.scrollTop>0"), "The longer program form must scroll in its own well"
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
