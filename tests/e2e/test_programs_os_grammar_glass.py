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
 const answer=question?{box:box(question),whole:within(box(question),seat),verbs:[...question.querySelectorAll('.surface-inspector-actions button')].map(e=>({word:e.textContent,box:box(e),whole:within(box(e),seat)}))}:null;
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
            expect(win.get_by_text("This question changed. Read it again.", exact=True)).to_be_visible()
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
            current = win.locator('.surface-step-station[aria-current="step"]')
            assert current.get_attribute("data-step-id") == tape["running"]["steps"][0]["id"]
            ring = current.locator('.surface-step-dot').evaluate("e=>({ring:getComputedStyle(e).outlineColor,fill:getComputedStyle(e).backgroundColor})")
            assert ring["ring"] == ring["fill"], ring
            shot(win,"steps-selected")
            selected_facts = win.locator(".surface-inspector-facts[data-headerless]").first
            assert selected_facts.count(), win.inner_text()
            assert selected_facts.evaluate("""el => {
                const seat=el.closest('.surface-list-pane-preview').getBoundingClientRect();
                return [...el.querySelectorAll('.gadget-row')].every(row=>{
                    const box=row.getBoundingClientRect();
                    return box.top>=seat.top-1 && box.bottom<=seat.bottom+1;
                });
            }"""), selected_facts.inner_text()
            win.get_by_role("tab",name="Text",exact=True).click()
            expect(win.get_by_test_id("programs-text")).to_be_visible();shot(win,"text")
            win.get_by_role("tab",name="Ledger",exact=True).click()
            win.get_by_role("grid",name="Program ledger",exact=True).locator('[data-object-id]').first.click()
            shot(win,"ledger")
            verb(win,"Amend");expect(win.get_by_role("region",name="Amend program",exact=True)).to_be_visible();shot(win,"amend-form")
            verb(win,"New program");expect(win.get_by_role("region",name="New program",exact=True)).to_be_visible();shot(win,"new-program-form")
            win.get_by_role("tab",name="Work",exact=True).click()
            shot(win,"new-program-work-form")
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_programs_restored_seats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Every restored seat uses a complete master/detail pair from one real rig."""
    import base64
    from urllib.parse import urlparse
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    tape = json.loads((WIRES / "program.visual10.json").read_text())
    wires = tape["wires"]
    shape = wires["program.shape.json"]
    projects = json.loads((WIRES / "program.create_projects.json").read_text())["response"]["body"]
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    current: dict[str, Any] = {"program": None, "project_fail": False, "shape": None, "engine": None}
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce", permissions=["clipboard-read", "clipboard-write"])
            page = context.new_page()
            page.set_default_timeout(10000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def route_program(route: Any) -> None:
                path = urlparse(route.request.url).path
                program = current["program"]
                if path == "/api/programs":
                    route.fulfill(json=tape["lists"][f"{program['id']}:{program['revision']}"])
                elif path.endswith("/shape"):
                    route.fulfill(json=current["shape"] if route.request.method == "POST" else (current["engine"] or tape["engines"][program["id"]]))
                elif path.endswith("/plan/draft"):
                    route.fulfill(json=current["shape"])
                elif path.endswith("/text"):
                    route.fulfill(json=tape["texts"][program["id"]])
                elif path.endswith("/evidence") and any(row["evidence"].get("url") == path and row["evidence"].get("kind") == "shot" for step in wires["program.requirements.json"]["steps"] for row in step["requirements"]):
                    route.fulfill(body=base64.b64decode(tape["shot"]["base64"]), content_type=tape["shot"]["type"])
                elif path.endswith("/evidence"):
                    evidence = wires["program.requirements.evidence.json"]
                    route.fulfill(body=evidence.get("log", ""), content_type="text/plain")
                elif route.request.method == "GET":
                    route.fulfill(json=program)
                else:
                    raise AssertionError(f"Unrecorded press: {route.request.method} {path}")

            page.route("**/api/programs{,/**}", route_program)
            def project_read(route: Any) -> None:
                if current["project_fail"]:
                    route.abort()
                else:
                    route.fulfill(json=projects)
            page.route("**/api/projects", project_read)
            page.route("**/api/reach/packages", lambda route: route.fulfill(json=wires["briefing"]["made"]))
            page.route("**/api/reach/packages/*/revoke", lambda route: route.fulfill(json=wires["briefing"]["revoked"]))

            def open_program(program: dict) -> Any:
                current["program"] = program
                current["shape"] = None
                current["engine"] = shape["engine"] if program["id"] in {shape["normal"]["program"]["id"], shape["voice"]["program"]["id"], shape["yolo"]["program"]["id"]} else None
                clear_hub_windows_http(base, TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "POST", "/api/desk/windows/surface-programs/open", {"object_ref": f"program:{program['id']}"}, token=TOKEN)
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-programs/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win = page.locator("#surface-programs")
                if program.get("held_shape"):
                    expect(win.get_by_role("grid", name="Text changes", exact=True)).to_be_visible()
                else:
                    expect(win.get_by_role("tab", name="Now", exact=True)).to_be_visible()
                _settle(page)
                master = win.get_by_role("grid", name="Programs", exact=True, include_hidden=True)
                target = master.locator(f'[data-object-id="{program["id"]}"]')
                if target.get_attribute("aria-selected") != "true":
                    if not target.is_visible():
                        win.get_by_role("button", name="Back", exact=True).click()
                    target.click()
                    _settle(page)
                return win

            def tab(win: Any, word: str) -> None:
                target = win.get_by_role("tab", name=word, exact=True).last
                target.click()
                expect(target).to_have_attribute("aria-selected", "true")

            def verb(win: Any, word: str) -> None:
                button = win.get_by_role("button", name=word, exact=True)
                if button.count() and button.last.is_visible():
                    button.last.click()
                else:
                    win.get_by_role("button", name="Actions ▾", exact=True).last.click()
                    page.get_by_role("menu").last.get_by_role("menuitem", name=word, exact=True).click()

            def pick(win: Any, grid: str, row: str | None = None) -> None:
                rows = win.get_by_role("grid", name=grid, exact=True).locator("[data-object-id]")
                if row is None:
                    rows.first.click()
                else:
                    target = win.locator(f'[data-object-id="{row}"]').last
                    assert target.count(), win.inner_text()
                    target.click()

            def shot(win: Any, name: str) -> None:
                _settle(page)
                suffix = "900x600" if width == 1440 else "393"
                facts = win.evaluate(FACTS)
                facts.update(engine_mode="replayed", wire_mode="recorded")
                path = OUT / f"{name}-{suffix}-after"
                page.screenshot(path=str(path.with_suffix(".png")))
                path.with_suffix(".json").write_text(json.dumps(facts, indent=2))
                assert facts["status"]
                assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-programs")
                assert not page.evaluate(CLIPPED_JS, "#surface-programs")
                assert not errors, errors

            p = wires["program.requirements.json"]
            win = open_program(p)
            tab(win, "Steps"); pick(win, "Steps", p["steps"][0]["id"]); tab(win, "Requirements")
            pick(win, "Requirements"); shot(win, "requirements-facts")
            verb(win, "Add requirement"); shot(win, "requirement-form")
            tab(win, "Proof"); shot(win, "requirement-proof-form")
            win.get_by_role("button", name="Cancel", exact=True).click()
            image = next(row for step in p["steps"] for row in step["requirements"] if row["evidence"].get("kind") == "shot")
            pick(win, "Requirements", image["id"])
            expect(win.get_by_role("img", name=f"{image['label']} evidence")).to_be_visible()
            shot(win, "requirement-shot"); tab(win, "Facts"); shot(win, "requirement-shot-facts")

            edit = wires["editable_requirement"]
            win = open_program(edit["program"]); tab(win,"Steps"); tab(win,"Requirements"); pick(win,"Requirements",edit["requirement_id"]); verb(win,"Edit requirement"); shot(win,"requirement-edit")
            win = open_program(wires["race_choice"]["program"])
            tab(win, "Steps"); pick(win, "Steps"); tab(win, "Race"); pick(win, "Race contenders"); shot(win, "race-contender")
            p = wires["program.adjust.json"]
            win = open_program(p); tab(win, "Steps"); pick(win, "Steps", p["steps"][1]["id"]); verb(win, "Race");
            win.get_by_role("combobox", name="Race contenders", exact=True).select_option("3"); shot(win, "race-three-choice")
            win = open_program(wires["limited"]); tab(win, "Ledger"); tab(win, "Handoffs"); shot(win, "handoff-reader")
            win = open_program(wires["audit.board.json"]); tab(win, "Ledger"); tab(win, "Findings"); pick(win, "Program ledger"); shot(win, "findings-door")
            p = wires["briefing"]["program"]
            win = open_program(p); tab(win, "Ledger"); tab(win, "Context"); pick(win, "Context doors", f"question:{p['your_turn_items'][0]['id']}")
            shot(win, "context-briefing"); verb(win, "Copy page link"); expect(win.get_by_role("button", name="Revoke link", exact=True)).to_be_visible(); shot(win, "briefing-link")
            verb(win, "Revoke link"); shot(win, "briefing-revoke")
            win = open_program(shape["normal"]["program"]); tab(win, "Steps"); tab(win, "Agents"); shot(win, "bulk-agents")
            p = wires["action_unbound"]
            win = open_program(p); tab(win, "Steps"); verb(win, "Add step"); expect(win.get_by_role("checkbox",name="Carry the program action",exact=True)).to_be_visible(); shot(win, "carry-action")
            win = open_program(shape["normal"]["program"]); verb(win, "Edit program")
            for word in ("Program", "Agents", "Checks", "Limits", "Night"):
                tab(win, word); shot(win, f"edit-{word.lower()}")
            verb(win, "New program"); tab(win, "Checks"); win.get_by_role("textbox", name="Spending note in USD", exact=True).fill("$40"); shot(win, "new-spending")
            current["project_fail"] = True
            win.get_by_role("button", name="Cancel", exact=True).click()
            verb(win, "New program"); expect(win.get_by_role("button", name="Retry projects", exact=True)).to_be_visible(); shot(win, "new-project-retry")
            current["project_fail"] = False
            verb(win, "Retry projects"); expect(win.get_by_role("button", name="Retry projects", exact=True)).to_have_count(0)
            p = shape["normal"]["program"]
            win = open_program(p); verb(win, "Amend"); current["shape"] = shape["normal"]["shape"]
            win.get_by_role("textbox", name="Program change", exact=True).fill("Keep the microphone reason beside Stop.")
            verb(win, "Preview"); expect(win.get_by_role("grid", name="Text changes", exact=True)).to_be_visible(); shot(win, "amend-changes")
            tab(win, "Add a sentence"); shot(win, "amend-accumulated")
            win = open_program(shape["call_later"]["program"]); expect(win.get_by_role("grid", name="Text changes", exact=True)).to_be_visible(); shot(win, "amend-call-held")
            win = open_program(shape["yolo"]["program"]); verb(win, "Amend"); current["shape"] = shape["yolo"]["shape"]
            win.get_by_role("textbox", name="Program change", exact=True).fill("Keep the microphone reason beside Stop.")
            verb(win, "Preview"); tab(win, "Applied"); pick(win, "Applied changes"); shot(win, "amend-applied")
            no_engine = shape["no_engine"]["program"]
            win = open_program(no_engine); current["engine"] = shape["no_engine"]["engine"]; verb(win, "Amend")
            win.get_by_role("textbox", name="Program change", exact=True).fill("Keep the saved reason.")
            verb(win, "Preview"); expect(win.get_by_role("button", name="Open Engines", exact=True)).to_be_visible(); shot(win, "amend-repair")
            split = wires["program.plan_programs.json"]
            win = open_program(split["program"]); current["shape"] = split["draft"]; verb(win,"Amend")
            win.get_by_role("combobox",name="Change method",exact=True).select_option("plan")
            win.get_by_role("textbox",name="Program change",exact=True).fill(split["program"]["goal"])
            verb(win,"Preview"); expect(win.get_by_role("grid",name="Planned programs",exact=True)).to_be_visible(); pick(win,"Planned programs"); shot(win,"plan-several")
            big = wires["program.plan_draft.json"]["big_file"]
            win = open_program(big["program"]); current["shape"] = big["draft"]; verb(win,"Amend")
            win.get_by_role("combobox",name="Change method",exact=True).select_option("plan")
            win.get_by_role("textbox",name="Program change",exact=True).fill(big["program"]["goal"])
            verb(win,"Preview"); expect(win.get_by_role("grid",name="Text changes",exact=True)).to_be_visible()
            row = next(row for row in big["draft"]["changes"] if row.get("size",{}).get("code")=="step_too_big")
            pick(win,"Text changes",row["id"]); shot(win,"plan-split")
            browser.close()
    finally:
        server.stop()
