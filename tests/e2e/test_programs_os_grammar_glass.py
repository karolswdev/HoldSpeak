"""The Programs live kit at the owner's two window sizes, on recorded hub wires."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_desk_sweep import CLIPPED_JS, LIST_GRAMMAR_JS

TOKEN = "programs-grammar10"
ROOT = Path(__file__).resolve().parents[2]
WIRES = ROOT / "web/src/desk/programs/__fixtures__"
OUT = ROOT / ".tmp/evidence-shots/programs10"

FACTS = r"""el => {
 const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};
 const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden';};
 const within=(a,b)=>a.x>=b.x-1&&a.y>=b.y-1&&a.right<=b.right+1&&a.bottom<=b.bottom+1;
 const root=box(el),pane=el.querySelector('[data-testid=programs-pane]'),seat=pane?box(pane):root;
 const question=el.querySelector('[data-testid=program-question]');
 const facts=[...el.querySelectorAll('.surface-live-content .gadget-row')].filter(visible).map(e=>({words:e.innerText,box:box(e),whole:within(box(e),seat)}));
 const controls=[...el.querySelectorAll('button,input,select,textarea')].filter(visible).filter(e=>!e.closest('.object-list-measure')).map(e=>({name:e.getAttribute('aria-label')||e.textContent,box:box(e),whole:within(box(e),root)}));
 const answer=question?{box:box(question),whole:within(box(question),seat),verbs:[...question.querySelectorAll('button')].map(e=>({word:e.textContent,box:box(e),whole:within(box(e),seat)}))}:null;
 return {window:root,pane:seat,facts,controls,question:answer,well:el.querySelector("[role=log]")?.textContent,status:[...el.querySelectorAll('.kit-statusbar')].map(e=>({words:e.innerText,box:box(e)})),animations:document.getAnimations().filter(a=>el.contains(a.effect?.target)).map(a=>a.animationName)};
}"""


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_programs_live_states_and_panes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    tape = json.loads((WIRES / "program.live10.json").read_text())
    dreaming = tape["tonight"]
    projects = json.loads((WIRES / "program.create_projects.json").read_text())["response"]["body"]
    OUT.mkdir(parents=True, exist_ok=True)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    current = {"program": tape["waiting"], "list": tape["waiting_list"], "stale": False}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width":width,"height":900 if width == 1440 else 852}, reduced_motion="reduce")
            page = context.new_page()
            page.set_default_timeout(15000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("**/api/programs", lambda route: route.fulfill(json=current["list"]) if route.request.method == "GET" else route.continue_())
            pid = tape["waiting"]["id"]
            page.route(f"**/api/programs/{pid}", lambda route: route.fulfill(json=current["program"]))
            page.route(f"**/api/programs/{pid}/text", lambda route: route.fulfill(json=tape["running_text"]) if route.request.method == "GET" else route.fulfill(json=tape["text_preview"]))
            page.route(f"**/api/programs/{pid}/shape", lambda route: route.fulfill(json=json.loads((WIRES / "program.shape.json").read_text())["engine"]))
            page.route("**/api/projects", lambda route: route.fulfill(json=projects))
            page.route(f"**/api/programs/{dreaming['id']}", lambda route: route.fulfill(json=dreaming))
            def decide(route: Any) -> None:
                if current["stale"]:
                    current["program"] = tape["stale_program"]
                    route.fulfill(status=409,json=tape["stale_answer"])
                else:
                    current["program"],current["list"] = tape["go_on"]["program"],tape["advanced_list"]
                    route.fulfill(json=tape["go_on"])
            page.route(f"**/api/programs/{pid}/steps/*/decide", decide)
            def open_state(name: str, state: str, listing: str | None = None) -> Any:
                current["program"] = tape[state]
                current["list"] = tape[listing or ("waiting_list" if state == "waiting" else "running_list")]
                clear_hub_windows_http(base,TOKEN)
                page.goto(f"{base}/?token={TOKEN}",wait_until="load")
                _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
                _api(page,"POST","/api/desk/windows/surface-programs/open",{"object_ref":f"program:{pid}"},token=TOKEN)
                if width == 1440:
                    _api(page,"POST","/api/desk/windows/surface-programs/set_geometry",{"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}},token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win=page.locator("#surface-programs")
                expect(win.get_by_role("tab",name="Now",exact=True)).to_be_visible()
                _settle(page)
                return win
            def shot(win: Any, name: str, *, question: bool = False) -> dict:
                _settle(page)
                suffix="900x600" if width == 1440 else "393"
                facts=win.evaluate(FACTS)
                facts["engine_mode"]="none"
                facts["wire_mode"]="recorded"
                path=OUT/f"{name}-{suffix}-after"
                page.screenshot(path=str(path.with_suffix(".png")))
                path.with_suffix(".json").write_text(json.dumps(facts,indent=2))
                assert facts["status"],facts
                assert not [row for row in facts["facts"] if not row["whole"]],facts["facts"]
                # Scroll wells own off-screen editor fields. The question and
                # all buttons in its completion row must be in the reading seat.
                if question:
                    assert facts["question"] and facts["question"]["whole"],facts
                    assert all(row["whole"] for row in facts["question"]["verbs"]),facts
                    assert [row["word"] for row in facts["question"]["verbs"]] == ["Park","Go on"]
                assert not page.evaluate(LIST_GRAMMAR_JS,"#surface-programs")
                assert not page.evaluate(CLIPPED_JS,"#surface-programs")
                assert not errors,errors
                return facts
            def verb(win: Any, word: str) -> None:
                button=win.get_by_role("button",name=word,exact=True)
                if button.is_visible():button.click()
                else:
                    win.get_by_role("button",name="Actions ▾",exact=True).first.click()
                    page.get_by_role("menu").last.get_by_role("menuitem",name=word,exact=True).click()
            win=open_state("waiting","waiting")
            shot(win,"waits-on-you",question=True)
            current["stale"]=True
            win.get_by_role("button",name="Go on",exact=True).click()
            expect(win.get_by_test_id("programs-failure")).to_contain_text("changed")
            shot(win,"stale-answer")
            current["stale"]=False
            win.get_by_role("button",name="Read the new question",exact=True).click()
            win.get_by_role("button",name="Go on",exact=True).click()
            expect(win.get_by_test_id("program-question")).to_have_count(0)
            current["program"] = tape["advanced"]
            server.broadcast("program_changed",tape["advanced_frame"])
            expect(win.get_by_role("region",name=f"Step 2 · {tape['advanced']['steps'][1]['title']}",exact=True)).to_be_visible()
            shot(win,"go-on")
            win=open_state("running","advanced","advanced_list")
            first=shot(win,"running-frame1")
            current["program"]=tape["advanced_next"]
            # Replay the real producer frame through the hub socket.
            server.broadcast("program_changed",tape["advanced_next_frame"])
            expect(win.get_by_role("log")).to_contain_text("Read the saved step reason")
            second=shot(win,"running-frame2")
            assert first["well"] != second["well"]
            assert first["animations"] == second["animations"] == []
            page.emulate_media(reduced_motion="no-preference")
            assert win.locator(".surface-lamp").count()
            page.wait_for_function("""() => document.getAnimations().some(a=>document.querySelector('#surface-programs').contains(a.effect?.target))""")
            shot(win,"running-motion")
            page.emulate_media(reduced_motion="reduce")
            page.wait_for_function("""() => !document.getAnimations().some(a=>document.querySelector('#surface-programs').contains(a.effect?.target))""")
            shot(win,"running-reduced")
            win=open_state("done","done","list");shot(win,"finished")
            win=open_state("parked","parked","parked_list");shot(win,"parked")
            current["program"],current["list"] = tape["tonight"],tape["list"]
            clear_hub_windows_http(base,TOKEN)
            _api(page,"POST","/api/desk/windows/surface-programs/open",{"object_ref":f"program:{dreaming['id']}"},token=TOKEN)
            if width == 1440:
                _api(page,"POST","/api/desk/windows/surface-programs/set_geometry",{"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}},token=TOKEN)
            page.reload(wait_until="load");_normal_chair(page)
            expect(win.get_by_role("tab",name="Now",exact=True)).to_be_visible();shot(win,"tonight")
            win=open_state("steps","running")
            win.get_by_role("tab",name="Steps",exact=True).click()
            win.get_by_role("grid",name="Steps",exact=True).locator('[data-object-id]').last.click()
            shot(win,"steps-selected")
            win.get_by_role("tab",name="Text",exact=True).click()
            expect(win.get_by_test_id("programs-text")).to_be_visible();shot(win,"text")
            win.get_by_role("tab",name="Ledger",exact=True).click()
            win.get_by_role("grid",name="Program ledger",exact=True).locator('[data-object-id]').first.click()
            shot(win,"ledger")
            verb(win,"Amend");expect(win.get_by_role("region",name="Amend program",exact=True)).to_be_visible();shot(win,"amend-form")
            verb(win,"New program");expect(win.get_by_role("region",name="New program",exact=True)).to_be_visible();shot(win,"new-program-form")
            browser.close()
    finally:
        server.stop()
