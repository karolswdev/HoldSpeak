"""Object titles, folding verbs and bounded reading/editing on the isolated Desk."""
from __future__ import annotations
import re
from pathlib import Path
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_decisions_os_grammar_glass import _seed, TOKEN
from .test_desk_sweep import _seed_automation
from .type_floor_rig import _MEASURE, _FAINT_JS

SHOTS = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/os-grammar"

def verb(page, win, label):
    button=win.get_by_role("button",name=label,exact=True)
    if button.count() and button.is_visible(): button.click()
    else:
        win.get_by_role("button",name="Actions ▾",exact=True).click()
        page.get_by_role("menu").last.get_by_role("menuitem",name=label,exact=True).click()

@pytest.mark.e2e
@pytest.mark.timeout(240)
@pytest.mark.parametrize("width",[1440,393])
def test_object_windows_fit_and_keep_their_actions(tmp_path,monkeypatch,width):
    from playwright.sync_api import expect,sync_playwright
    _ensure_build()
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    SHOTS.mkdir(parents=True,exist_ok=True)
    try:
        seeds=_seed(base);wb=_seed_automation("missing-note")
        from datetime import datetime, timezone
        from holdspeak.db import get_database
        from holdspeak.meeting_session import MeetingState,TranscriptSegment
        from holdspeak.principals import derive_owner
        from holdspeak.services.decision_record_service import DecisionRecordService
        db=get_database()
        quote="The shared runners keep one build path. " * 35
        db.meetings.save_meeting(MeetingState(id="reader-source",title="Runner review",started_at=datetime.now(timezone.utc),segments=[TranscriptSegment(text=quote,speaker="Mira",start_time=1.0,end_time=5.0)],intel_status="disabled"))
        with db._connection() as conn:
            segment_id=conn.execute("SELECT id FROM segments WHERE meeting_id = ?",("reader-source",)).fetchone()["id"]
        records=DecisionRecordService(db);owner=derive_owner(TOKEN,TOKEN)
        records.add_source(owner,seeds[0]["record"]["id"],"segment",segment_id)
        records.update_record(owner,seeds[0]["record"]["id"],{"review_date":"2026-12-01"})
        from holdspeak import workbench_memory
        monkeypatch.setattr(workbench_memory,"WORKBENCH_DIR",tmp_path/"workbench-memory")
        workbench_memory.append_memory(wb,"seeded-run","lesson","Keep the update under ten lines.")
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
            def open_window(wid,ref=None):
                clear_hub_windows_http(base,TOKEN)
                page.goto(f"{base}/?token={TOKEN}",wait_until="load")
                _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
                _api(page,"POST",f"/api/desk/windows/{wid}/open",{"object_ref":ref} if ref else {},token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win=page.locator(f'[id="{wid}"]');expect(win).to_be_visible()
                if width==1440:
                    _api(page,"POST",f"/api/desk/windows/{wid}/set_geometry",{"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}},token=TOKEN)
                return win
            def shot(win,app,state,settle=True):
                if settle:_settle(page)
                assert win.evaluate("""el => {
                  const body=el.querySelector('.desk-surface-body');
                  const pane=el.querySelector('[data-testid="decision-reader"],[data-testid="automation-window"]');
                  return body.scrollHeight<=body.clientHeight+1 && body.scrollWidth<=body.clientWidth+1
                    && pane.scrollHeight<=pane.clientHeight+1 && pane.scrollWidth<=pane.clientWidth+1;
                }"""),state
                assert win.locator(".surface-mast:not(.surface-mast--framed),.decisions-plate,.automation-plate,.surface-spine").count()==0
                assert win.locator(".surface-mast--framed").count()==1
                if app == "decision-reader" and width == 1440 and state not in ["edit","save-failed","send"]:
                    gaps=win.evaluate("""el => {
                      const pane=el.querySelector('[data-testid="decision-reader"]').getBoundingClientRect();
                      return [...el.querySelectorAll('.reading-document, .surface-inspector-facts, [data-testid="decision-filing-well"]')]
                        .map(content => {const well=content.closest('.surface-pane-inspector, .surface-tab-panel') || content;const r=well.getBoundingClientRect();return {left:r.left-pane.left,right:pane.right-r.right};});
                    }""")
                    assert gaps,state
                    assert all(-1 <= gap[side] <= 24 for gap in gaps for side in ["left","right"]),(state,gaps)
                    measure=win.locator(".reading-document").evaluate_all("""documents => documents.map(document => {
                      const style=getComputedStyle(document), context=document.ownerDocument.createElement('canvas').getContext('2d');
                      context.font=[style.fontStyle,style.fontWeight,style.fontSize,style.fontFamily].join(' ');
                      return {width:document.getBoundingClientRect().width,measure:68*context.measureText('0').width};
                    })""")
                    assert all(reading["width"] <= reading["measure"]+2 for reading in measure),(state,measure)
                page.screenshot(path=str(SHOTS/f'{app}-{state}-{"900x600" if width==1440 else "393"}-after.png'))
            def gutter(win,reading=False):
                return win.evaluate("""(el,reading) => {
                  const panel=el.querySelector('[role="tabpanel"]');
                  const content=panel.querySelector(reading ? '.reading-document,.surface-inspector-rows' : '.surface-inspector-rows,.object-list');
                  return content.getBoundingClientRect().left-panel.getBoundingClientRect().left;
                }""",reading)
            def reading_stays(win):
                words=win.get_by_test_id("decision-words")
                expect(words).to_be_visible()
                expect(words).to_contain_text(seeds[0]["record"]["decision_text"])
                box=words.bounding_box();question=win.get_by_test_id("decision-reader-question").bounding_box()
                assert box and question and box["height"] > 0 and box["y"] < question["y"],(box,question)
            for seed,state in zip(seeds,["decided","proposed","retired","committed","disputed","superseded"]):
                win=open_window("surface-decisions","record:"+seed["record"]["id"])
                expect(win.get_by_test_id("decision-words")).to_be_visible()
                expect(win.get_by_role("heading", name=seed["record"]["title"], exact=True)).to_be_visible()
                decision_gutter=gutter(win,reading=True)
                shot(win,"decision-reader",state)
                if state=="decided":
                    for tab in ["Facts","History"]:
                        win.get_by_role("tab",name=tab,exact=True).click()
                        assert abs(gutter(win,reading=True)-decision_gutter) <= 1,(tab,gutter(win,reading=True),decision_gutter)
                        shot(win,"decision-reader",tab.lower())
                    win.get_by_role("tab",name="Evidence",exact=True).click()
                    source=win.get_by_role("row").filter(has_text="The shared runners keep one build path.").first
                    source.click()
                    expect(win.locator(".surface-list-pane-preview")).to_contain_text(quote.strip())
                    assert abs(gutter(win,reading=True)-decision_gutter) <= 1
                    shot(win,"decision-reader","evidence")
                    source.click(button="right")
                    expect(page.get_by_role("menu").last.get_by_role("menuitem",name=re.compile("^Open source"))).to_be_enabled()
                    shot(win,"decision-reader","evidence-menu")
                    page.keyboard.press("Escape")
                    folded=win.get_by_role("button",name="Actions ▾",exact=True).is_visible()
                    verb(page,win,"Retire")
                    question=win.get_by_test_id("decision-reader-question")
                    expect(question.get_by_role("button",name="Cancel")).to_be_focused()
                    reading_stays(win)
                    assert win.get_by_role("button",name="Actions ▾",exact=True).is_visible() == folded
                    if width == 1440:
                        expect(win.get_by_test_id("decision-reader-edit")).to_be_visible()
                        expect(win.get_by_test_id("decision-reader-edit")).to_be_disabled()
                        expect(win.get_by_test_id("decision-reader-retire")).to_be_visible()
                    shot(win,"decision-reader","retire-question")
                    question.get_by_role("button",name="Cancel").click()
                    verb(page,win,"Delete");reading_stays(win);shot(win,"decision-reader","delete-question")
                    win.get_by_test_id("decision-reader-question").get_by_role("button",name="Cancel").click()
                    verb(page,win,"Edit")
                    field=win.get_by_role("textbox",name="Decision",exact=True)
                    field.fill("Keep this draft")
                    shot(win,"decision-reader","edit")
                    path="**/api/decisions/"+seed["decision"]["id"]
                    page.route(path,lambda route:route.fulfill(status=503,json={"detail":"Decision not saved"}))
                    win.get_by_role("button",name="Save",exact=True).click()
                    expect(win.get_by_role("alert")).to_contain_text("Save failed")
                    expect(field).to_have_value("Keep this draft");shot(win,"decision-reader","save-failed")
                    page.unroute(path)
                    win.get_by_role("button",name="Cancel",exact=True).click()
                    verb(page,win,"File");shot(win,"decision-reader","filing")
                    verb(page,win,"File")
                    verb(page,win,"Send…");win.get_by_test_id("send-sheet").wait_for();shot(win,"decision-reader","send")
            win=open_window("workbench:"+wb)
            expect(win.get_by_test_id("automation-summary")).to_be_visible()
            expect(win.get_by_test_id("automation-summary")).to_contain_text("Source missing")
            expect(win.get_by_test_id("automation-summary")).not_to_contain_text("Choose Edit")
            expect(win.get_by_test_id("automation-summary").get_by_text("Source missing",exact=True)).to_be_visible()
            shot(win,"automation-window","about")
            pane_gutter=gutter(win)
            win.get_by_role("tab",name="Learned",exact=True).click()
            assert abs(gutter(win)-pane_gutter) <= 1
            shot(win,"automation-window","learned")
            win.get_by_role("row",name="Keep the update under ten lines.",exact=True).click()
            win.get_by_role("button",name="Forget",exact=True).click()
            question=win.get_by_role("region",name="Forget this lesson?",exact=True)
            expect(question.get_by_role("button",name="Cancel")).to_be_focused()
            expect(win.get_by_role("row",name="Keep the update under ten lines.",exact=True)).to_be_visible()
            shot(win,"automation-window","forget-question")
            question.get_by_role("button",name="Cancel").click()
            win.get_by_role("button",name="Forget",exact=True).click()
            win.get_by_role("region",name="Forget this lesson?",exact=True).get_by_role("button",name="Forget",exact=True).click()
            expect(win.get_by_role("tab",name="About",exact=True)).to_have_attribute("aria-selected","true")
            shot(win,"automation-window","forgot")

            for tab in ["Runs","Results"]:
                win.get_by_role("tab",name=tab,exact=True).click()
                assert abs(gutter(win)-pane_gutter) <= 1,(tab,gutter(win),pane_gutter)
                shot(win,"automation-window",tab.lower())
            win.get_by_role("tab",name="Runs",exact=True).click()
            failed=win.get_by_role("row").filter(has_text="Failed")
            failed.dblclick()
            expect(win.get_by_role("alert")).to_contain_text("did not answer")
            shot(win,"automation-window","failed")
            page.route("**/api/workbenches/"+wb+"/run",lambda route:route.fulfill(status=503,json={"detail":"Run not started"}))
            verb(page,win,"Run again")
            expect(win.get_by_test_id("automation-failure")).to_contain_text("Run not started")
            shot(win,"automation-window","run-refused")
            page.unroute("**/api/workbenches/"+wb+"/run")
            held=[]
            page.route("**/api/workbenches/"+wb+"/run",lambda route:held.append(route))
            verb(page,win,"Run again")
            running = win.get_by_role("region",name="Automation",exact=True).locator(".surface-object-running")
            expect(running.locator('.surface-lamp[data-state="working"]')).to_be_visible()
            expect(running).to_contain_text("Working")
            shot(win,"automation-window","working",settle=False)
            held[0].fulfill(status=503,json={"detail":"Run not started"})
            expect(win.get_by_test_id("automation-failure")).to_contain_text("Run not started")
            page.unroute("**/api/workbenches/"+wb+"/run")
            verb(page,win,"Edit")
            for tab in ["Do","When","About","With","Put it in"]:
                win.get_by_role("tab",name=tab,exact=True).click()
                if tab == "About":expect(win.get_by_role("checkbox",name=re.compile("note",re.I))).to_be_visible()
                shot(win,"automation-window","edit-"+tab.lower().replace(" ","-"))
            win.get_by_role("tab",name="Do",exact=True).click()
            field=win.get_by_role("textbox",name="What it does",exact=True)
            field.fill("Keep my automation draft")
            page.route("**/api/workbenches/"+wb,lambda route:route.fulfill(status=503,json={"detail":"Automation not saved"}) if route.request.method=="PUT" else route.continue_())
            win.get_by_role("button",name="Save",exact=True).click()
            expect(win.get_by_role("alert")).to_contain_text("Not saved")
            expect(field).to_have_value("Keep my automation draft");shot(win,"automation-window","save-failed")
            page.unroute("**/api/workbenches/"+wb)
            win.get_by_role("button",name="Cancel",exact=True).click()
            verb(page,win,"Edit")
            field=win.get_by_role("textbox",name="What it does",exact=True)
            field.press("Escape")
            expect(win.get_by_test_id("automation-setup")).to_have_count(0)
            expect(win).to_be_visible()
            expect(win.get_by_role("tab",name="Results",exact=True)).to_have_attribute("aria-selected","true")
            shot(win,"automation-window","escape")
            if width == 393:
                verb(page,win,"Edit")
                back=win.get_by_test_id("automation-inspector-back")
                def back_ink():
                    expect(back).to_have_text("‹ Back")
                    assert back.evaluate("""button => {
                      const word=button.querySelector('span'), face=getComputedStyle(button,'::before');
                      return Number(getComputedStyle(word).zIndex) > Number(face.zIndex);
                    }""")
                    contrast = page.evaluate(_MEASURE, page.evaluate(_FAINT_JS))["contrast"]
                    assert not [fault for fault in contrast if "‹ Back" in fault["text"]], contrast
                back.focus();page.keyboard.press("ArrowLeft")
                assert back.evaluate("el => el.matches(':focus-visible')")
                back_ink();shot(win,"automation-window","back-focus")
                back.hover();back_ink();shot(win,"automation-window","back-hover")
                page.mouse.down();back_ink();shot(win,"automation-window","back-pressed",settle=False)
                page.mouse.up()
                expect(win).to_be_visible()
                expect(win.get_by_role("tab",name="Results",exact=True)).to_have_attribute("aria-selected","true")
                shot(win,"automation-window","back")
            assert errors==[],errors
            browser.close()
    finally:server.stop()
